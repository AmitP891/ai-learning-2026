"""Train Bit's own wake word, "hey bit", for openWakeWord. Runs on a Mac, no GPU.

    .venv/bin/python wakeword/train_hey_bit.py

How it works (same model shape as openWakeWord's official models, lighter data recipe):
  1. Positives: "hey bit" spoken by every English macOS `say` voice at several speeds,
     plus Amit's own recordings in wakeword/data/amit/*.wav if there are any.
  2. Negatives: sound-alike phrases ("hey Bill", "a bit", "habit"...), everyday sentences,
     noise, and ~11 h of openWakeWord's published speech/noise features.
  3. Augment: speed, loudness, room echo, background noise.
  4. Features: openWakeWord's frozen melspectrogram + embedding models (16 x 96 per window).
  5. Train a small network on them, test on voices and audio it never saw, export ONNX.
"""
import random
import re
import subprocess
import sys
import tempfile
import time
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE.parent / "models" / "hey_bit.onnx"
SR = 16000
CLIP = int(2.5 * SR)  # every training clip is 2.5 s; the model sees its last 16 frames
SEED = 7
random.seed(SEED)
np.random.seed(SEED)

POSITIVE = ["hey bit", "hey, bit", "hey bit!", "Hey Bit.", "hey bit?", "heyy bit"]
SOUNDALIKES = [
    "hey bill", "hey bud", "hey big", "hey ben", "hey brit", "hey bix", "hey kit", "hey pit",
    "hey fit", "hey it", "hey but", "hey bet", "hey bat", "hey bot", "hey bee", "hey boat",
    "hey mitt", "hey liz", "hey there", "hey buddy", "hey siri", "hey jarvis", "hey", "bit",
    "a bit", "a little bit", "habit", "rabbit", "orbit", "obit", "they bit", "eight bits",
    "hay bale", "say it", "okay bit", "hey you", "hey bitty", "hey, bear", "a bit later", "hey Pete",
]
SENTENCES = [
    "Can you open the window a little bit, it's warm in here.",
    "I think the habit tracker is broken again.",
    "Let's record the next video after lunch.",
    "The rabbit ran across the garden this morning.",
    "Hey, did you see the new requirements document?",
    "Just a bit more and the render is done.",
    "Okay so the plan for today is editing and posting.",
    "My code finally compiled after the third try.",
    "We should test the microphone before filming.",
    "Hey there, welcome back to the channel.",
    "It's been a bit of a long week to be honest.",
    "Put the coffee on the desk next to the robot.",
    "That orbit animation looks really smooth now.",
    "Can you check the calendar for tomorrow afternoon?",
    "I bet the thumbnail with pink text does better.",
    "Turn the music down a bit please.",
    "The speedrunner finished the level in under a minute.",
    "Hey, how was your weekend, did you go anywhere?",
    "Let me think about it for a bit and get back to you.",
    "Bits and bytes, that's all a computer really is.",
    "Every eight bits make a byte, remember that.",
    "I need to rehearse my talk before the meetup.",
    "Hey buddy, can you pass me the charger?",
    "The weather is supposed to be rainy all week.",
    "Write the script first, then shoot the B roll.",
    "Big ideas start as tiny experiments.",
    "Hey Siri, set a timer for ten minutes.",
    "This little robot is made entirely of code.",
    "Do you want tea or coffee, or a bit of both?",
    "Hey, it's me again, I forgot my keys.",
]
NOVELTY = {"Albert", "Bad News", "Bahh", "Bells", "Boing", "Bubbles", "Cellos", "Good News",
           "Jester", "Organ", "Superstar", "Trinoids", "Whisper", "Wobble", "Zarvox"}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---- 1. synthesis ---------------------------------------------------------
def english_voices():
    out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout
    voices = []
    for line in out.splitlines():
        m = re.match(r"^(.+?)\s+(en_[A-Z]{2})\s+#", line)
        if m and m.group(1).split(" (")[0] not in NOVELTY:
            voices.append(m.group(1))
    return voices


_bad_voices: set = set()


def say(text, voice, rate):
    if voice in _bad_voices:
        return None
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        try:  # some voices occasionally hang when writing to a file: give up on them
            r = subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", f.name, "--file-format=WAVE",
                                f"--data-format=LEI16@{SR}", text], capture_output=True, timeout=15)
        except subprocess.TimeoutExpired:
            _bad_voices.add(voice)
            log(f"  voice '{voice}' hung, skipping it from now on")
            return None
        if r.returncode != 0:
            return None
        with wave.open(f.name) as w:
            a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    a = trim(a)
    return a if len(a) > SR * 0.15 else None


def trim(a, thresh=0.01):
    idx = np.where(np.abs(a) > thresh)[0]
    return a[max(0, idx[0] - 400): idx[-1] + 400] if len(idx) else a[:0]


_CACHE_FILE = DATA / "say_cache.pkl"
_cache = None


def synth_all(jobs):
    """jobs: list of (text, voice, rate). Returns list of float32 arrays (Nones dropped).
    Clips are cached in wakeword/data/say_cache.pkl, so retraining skips this slow step."""
    import pickle
    global _cache
    if _cache is None:
        _cache = pickle.loads(_CACHE_FILE.read_bytes()) if _CACHE_FILE.exists() else {}
    todo = [j for j in jobs if j not in _cache]
    if todo:
        with ThreadPoolExecutor(8) as ex:
            for j, a in zip(todo, ex.map(lambda j: say(*j), todo)):
                _cache[j] = a
        _CACHE_FILE.write_bytes(pickle.dumps(_cache))
    return [_cache[j] for j in jobs if _cache[j] is not None]


def read_wav(path):
    with wave.open(str(path)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        if w.getframerate() != SR:
            from scipy.signal import resample_poly
            a = resample_poly(a, SR, w.getframerate()).astype(np.float32)
    return trim(a, 0.02)


# ---- 2. augmentation ------------------------------------------------------
def colored_noise(n, kind):
    white = np.random.randn(n).astype(np.float32)
    if kind == "white":
        return white
    spec = np.fft.rfft(white)
    f = np.maximum(np.arange(len(spec)), 1)
    spec /= np.sqrt(f) if kind == "pink" else f
    out = np.fft.irfft(spec, n).astype(np.float32)
    return out / (np.std(out) + 1e-9)


def reverb(a):
    rt60 = random.uniform(0.15, 0.7)
    n = int(rt60 * SR)
    t = np.arange(n) / SR
    rir = np.random.randn(n).astype(np.float32) * np.exp(-6.9 * t / rt60)
    rir[0] = 1.0
    wet = np.convolve(a, rir)[: len(a)]
    wet /= np.max(np.abs(wet)) + 1e-9
    mix = random.uniform(0.15, 0.5)
    return (1 - mix) * a / (np.max(np.abs(a)) + 1e-9) + mix * wet


def augment(a):
    from scipy.signal import resample
    if random.random() < 0.7:  # speed / pitch
        a = resample(a, int(len(a) / random.uniform(0.88, 1.12))).astype(np.float32)
    if random.random() < 0.5:
        a = reverb(a)
    return a / (np.max(np.abs(a)) + 1e-9) * random.uniform(0.08, 0.9)


def place(a, end_aligned):
    """Put `a` in a 2.5 s window over background noise. End-aligned clips finish just before the
    window ends: always for positives, and mostly for sound-alikes too, so the model must learn
    the WORD, not where it sits in the window (live, every phrase passes through that spot)."""
    a = a[-CLIP:]
    clip = np.zeros(CLIP, dtype=np.float32)
    if end_aligned:
        end = CLIP - int(random.uniform(0.04, 0.3) * SR)
        start = max(0, end - len(a))
        clip[start:start + len(a[-(end - start):])] = a[-(end - start):]
    else:
        start = random.randint(0, max(0, CLIP - len(a)))
        clip[start:start + len(a)] = a[: CLIP - start]
    if random.random() < 0.85:
        speech_rms = np.sqrt(np.mean(a ** 2)) + 1e-6
        snr_db = random.uniform(3, 30)
        noise = colored_noise(CLIP, random.choice(["white", "pink", "brown"]))
        clip += noise * speech_rms / (10 ** (snr_db / 20))
    return np.clip(clip, -1, 1)


def to_int16(clips):
    return (np.stack(clips) * 32767).astype(np.int16)


# ---- 3. features ----------------------------------------------------------
_feat = None


def features(clips):
    """(N, CLIP) int16 -> (N, 16, 96) openWakeWord embeddings of the last 1.28 s."""
    global _feat
    if _feat is None:
        from openwakeword.utils import AudioFeatures
        _feat = AudioFeatures(inference_framework="onnx")
    out = []
    for i in range(0, len(clips), 256):
        out.append(_feat.embed_clips(clips[i:i + 256], batch_size=64, ncpu=4)[:, -16:, :])
    return np.concatenate(out).astype(np.float32)


def make_set(sources, copies, positive, end_aligned_share=None):
    """end_aligned_share: fraction of clips placed like positives (default: 1 for positives, 0 otherwise)."""
    share = (1.0 if positive else 0.0) if end_aligned_share is None else end_aligned_share
    clips = [place(augment(a), random.random() < share) for a in sources for _ in range(copies)]
    random.shuffle(clips)
    return features(to_int16(clips))


def sentence_crops(sentences_audio, n_per):
    crops = []
    for a in sentences_audio:
        for _ in range(n_per):
            if len(a) > CLIP:
                s = random.randint(0, len(a) - CLIP)
                crops.append(a[s:s + CLIP])
            else:
                crops.append(a)
    return crops


# ---- 4. model -------------------------------------------------------------
def build_model():
    import torch.nn as nn
    return nn.Sequential(
        nn.Flatten(), nn.Linear(16 * 96, 64), nn.LayerNorm(64), nn.ReLU(),
        nn.Linear(64, 64), nn.LayerNorm(64), nn.ReLU(), nn.Linear(64, 1), nn.Sigmoid())


def detections_per_hour(scores, threshold, frame_s=0.08, cooldown_s=1.5):
    hits, last = 0, -1e9
    for i in np.where(scores >= threshold)[0]:
        if (i - last) * frame_s > cooldown_s:
            hits += 1
        last = i
    return hits / (len(scores) * frame_s / 3600)


def main():
    import torch
    torch.manual_seed(SEED)

    general = DATA / "validation_set_features.npy"
    if not general.exists():
        sys.exit(f"missing {general}: download it from huggingface.co/datasets/davidscripka/openwakeword_features")

    voices = english_voices()
    random.shuffle(voices)
    n_val = max(4, len(voices) // 5)
    val_voices, train_voices = voices[:n_val], voices[n_val:]
    log(f"{len(voices)} English voices: {len(train_voices)} train, {len(val_voices)} held out")

    def jobs(texts, vs, rates):
        return [(t, v, r) for t in texts for v in vs for r in rates]

    log("synthesising 'hey bit' and sound-alikes...")
    pos_tr = synth_all(jobs(POSITIVE, train_voices, [140, 175, 210, 250]))
    pos_va = synth_all(jobs(POSITIVE[:3], val_voices, [160, 220]))
    amit = sorted((DATA / "amit").glob("*.wav")) if (DATA / "amit").exists() else []
    amit_audio = [read_wav(p) for p in amit]
    random.shuffle(amit_audio)
    amit_va = amit_audio[: len(amit_audio) // 4]
    amit_tr = amit_audio[len(amit_audio) // 4:]
    adv_tr = synth_all(jobs(SOUNDALIKES, train_voices, [160, 230]))
    adv_va = synth_all(jobs(SOUNDALIKES, val_voices, [190]))
    adv_va_text = [j[0] for j in jobs(SOUNDALIKES, val_voices, [190]) if _cache[j] is not None]
    sen_tr = synth_all(jobs(SENTENCES, train_voices, [185]))
    log(f"clips: pos {len(pos_tr)} (+{len(amit_tr)} Amit), held-out pos {len(pos_va)} "
        f"(+{len(amit_va)} Amit), sound-alikes {len(adv_tr)}, held-out {len(adv_va)}, sentences {len(sen_tr)}")

    log("augmenting + extracting features (the slow part)...")
    Xp = make_set(pos_tr, 5, True)
    if amit_tr:
        Xp = np.concatenate([Xp, make_set(amit_tr, 40, True)])
    Xa = make_set(adv_tr, 4, False, end_aligned_share=0.75)
    Xs = make_set(sentence_crops(sen_tr, 2), 1, False)
    noise_only = [np.zeros(int(0.3 * SR), dtype=np.float32) for _ in range(800)]
    Xn = make_set(noise_only, 1, False)
    Xp_va = make_set(pos_va, 3, True)
    Xamit_va = make_set(amit_va, 10, True) if amit_va else None
    Xa_va = make_set(adv_va, 2, False, end_aligned_share=1.0)  # the hardest case, as live
    log(f"features: pos {Xp.shape}, sound-alike {Xa.shape}, sentences {Xs.shape}, noise {Xn.shape}")

    g = np.load(general, mmap_mode="r")
    log(f"general negatives file: shape {g.shape}")
    if g.ndim == 2:  # continuous frames -> sliding 16-frame windows
        g = np.lib.stride_tricks.sliding_window_view(g, (16, g.shape[1]))[:, 0]
    cut = int(len(g) * 0.8)
    g_tr = g[:cut]
    g_va = np.asarray(g[cut:], dtype=np.float32)
    hours_va = len(g_va) * 0.08 / 3600
    log(f"general negatives: {len(g_tr)} train windows, {len(g_va)} held-out windows (~{hours_va:.1f} h)")

    X_hard = np.concatenate([Xa, Xs, Xn])
    model = build_model()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    steps = 6000
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=2e-3, total_steps=steps)
    bce = torch.nn.BCELoss(reduction="none")

    def batch(n):
        ip = np.random.randint(0, len(Xp), n // 3)
        ih = np.random.randint(0, len(X_hard), n // 3)
        ig = np.sort(np.random.randint(0, len(g_tr), n - 2 * (n // 3)))
        x = np.concatenate([Xp[ip], X_hard[ih], np.asarray(g_tr[ig], dtype=np.float32)])
        y = np.concatenate([np.ones(len(ip)), np.zeros(len(ih) + len(ig))]).astype(np.float32)
        return torch.from_numpy(x), torch.from_numpy(y)

    log(f"training {steps} steps...")
    model.train()
    for step in range(1, steps + 1):
        x, y = batch(384)
        p = model(x).squeeze(1)
        # negatives get more weight as training goes on (fewer false triggers)
        w = torch.where(y > 0, torch.tensor(1.0), torch.tensor(1.0 + 9.0 * step / steps))
        loss = (bce(p, y) * w).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
        sched.step()
        if step % 1000 == 0:
            log(f"  step {step}: loss {loss.item():.4f}")

    model.eval()

    def score(X):
        with torch.no_grad():
            return np.concatenate([model(torch.from_numpy(np.asarray(X[i:i + 4096], dtype=np.float32)))
                                   .squeeze(1).numpy() for i in range(0, len(X), 4096)])

    s_pos, s_adv, s_gen = score(Xp_va), score(Xa_va), score(g_va)
    s_amit = score(Xamit_va) if Xamit_va is not None else None
    print("\nHeld-out results (voices and audio the model never trained on):")
    print(" threshold | 'hey bit' caught | Amit caught | sound-alikes firing | false triggers/hour")
    for th in (0.3, 0.5, 0.7, 0.85):
        amit_s = f"{(s_amit >= th).mean():10.1%}" if s_amit is not None else "       n/a"
        print(f"   {th:4.2f}    |     {(s_pos >= th).mean():6.1%}       | {amit_s}  |"
              f"       {(s_adv >= th).mean():6.1%}        |   {detections_per_hour(s_gen, th):6.2f}")

    OUT.parent.mkdir(exist_ok=True)
    torch.onnx.export(model, torch.zeros(1, 16, 96), str(OUT), input_names=["input"],
                      output_names=["hey_bit"], opset_version=13, dynamo=False)
    log(f"saved {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")

    # Streaming check: held-out clips through openWakeWord exactly as live audio (every alignment)
    from openwakeword.model import Model
    m = Model(wakeword_models=[str(OUT)], inference_framework="onnx")
    pad = np.zeros(SR, dtype=np.float32)

    def stream_max(a):
        m.reset()
        x = (np.clip(np.concatenate([pad, a / (np.max(np.abs(a)) + 1e-9) * 0.5, pad]), -1, 1) * 32767)
        return max(p["hey_bit"] for p in m.predict_clip(x.astype(np.int16)))

    sp = np.array([stream_max(a) for a in pos_va])
    sa = np.array([stream_max(a) for a in adv_va])
    print("\nStreaming test on held-out voices (as live):")
    for th in (0.5, 0.7, 0.85, 0.95):
        print(f"   {th:4.2f}: 'hey bit' caught {(sp >= th).mean():6.1%} | sound-alikes firing {(sa >= th).mean():6.1%}")
    worst = sorted(zip(sa, adv_va_text), reverse=True)[:8]
    print("   top sound-alike scores:", ", ".join(f"{t!r} {v:.2f}" for v, t in worst))


if __name__ == "__main__":
    main()
