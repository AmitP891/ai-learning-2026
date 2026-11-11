"""Ask Bit coming-soon teaser from the 3D studio, timed to the real voice lines.
Usage: python3 build_coming_soon.py VOICES_DIR OUT.mp4 [w h]
VOICES_DIR holds l1.mp3 (Glitch: 'Bit, what's this show?'), l2.mp3 (Bit: 'You ask. I explain. In three parts.'),
l3.mp3 (Glitch: '...Fine.')."""
import json, os, subprocess, sys, tempfile, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); FPS = 30

def pcm(path, sr=44100):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(float) / 32768

def envelope(x, sr=44100):
    hop = sr // FPS; n = len(x) // hop
    r = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) for i in range(n)])
    r = r / (r.max() + 1e-9); r = np.clip((r - 0.06) / 0.94, 0, 1) ** 0.7
    out = np.zeros_like(r); a = 0
    for i, v in enumerate(r): a = max(v, a * 0.6); out[i] = a           # fast attack, quick release
    return out

def main(vdir, out, w=1080, h=1920):
    L = [("glitch", "GLITCH", "Bit, what's this show?", "l1.mp3", 1.7), ("bit", "BIT", "You ask. I explain. In three parts.", "l2.mp3", 3.65),
         ("glitch", "GLITCH", "…Fine.", "l3.mp3", 7.85)]
    sr = 44100; voices = []
    for who, tag, text, f, start in L:
        x = pcm(os.path.join(vdir, f)); voices.append((who, tag, text, start, len(x) / sr, envelope(x), x))
    end_t = 9.35; DUR = end_t + 3.3; N = int(DUR * FPS)
    states = []
    for i in range(N):
        t = i / FPS; s = {"t": t, "bitLevel": 0, "glLevel": 0, "speaker": None, "glExpr": "smirk"}
        # shots
        if t < 1.4: s["shot"] = ["sign"]; s["drift"] = [0, -t * 6, -t * 10]
        elif t < 2.2: s["shot"] = ["sign", "wide", (t - 1.4) / 0.8]
        elif t < 3.55: s["shot"] = ["wide"]; s["drift"] = [0, 0, -(t - 2.2) * 14]
        elif t < 7.5: s["shot"] = ["bit"]; s["drift"] = [0, 0, -(t - 3.55) * 6]
        elif t < 9.2: s["shot"] = ["glitch"]; s["drift"] = [0, 0, -(t - 7.5) * 8]
        else: s["shot"] = ["wide"]; s["drift"] = [0, 0, -(t - 9.2) * 8]
        # neon flicker on
        s["sign"] = 0 if t < 0.25 else ([0.3, 0, 0.8, 0.2, 1, 0.5, 1][int((t - 0.25) * 8) % 7] if t < 1.1 else 1)
        if 7.5 <= t < 9.2: s["glExpr"] = "neutral"
        for who, tag, text, start, dur, env, _ in voices:
            k = int((t - start) * FPS)
            if 0 <= k < len(env): s[f"{'bit' if who == 'bit' else 'gl'}Level"] = float(env[k]); s["speaker"] = who
            if start - 0.1 <= t < start + dur + 0.25: s["caption"] = {"who": tag, "text": text, "o": 1}
        if t >= end_t: s["end"] = min(1, (t - end_t) / 0.35); s.pop("caption", None)
        states.append(s)
    tmp = tempfile.mkdtemp(); sj = os.path.join(tmp, "states.json"); json.dump(states, open(sj, "w"))
    vid = os.path.join(tmp, "v.mp4")
    subprocess.run(["node", os.path.join(HERE, "studio/render.js"), sj, vid, str(w), str(h)], check=True)
    # audio: voices + lo-fi bed + small sfx
    n = int(DUR * sr); t = np.arange(n) / sr; mix = np.zeros(n); rng = np.random.default_rng(7); noise = rng.uniform(-1, 1, n)
    def env(s0, d):
        e = np.zeros(n); i0 = int(s0 * sr)
        if i0 < n: e[i0:] = np.exp(-np.arange(n - i0) / sr / d)
        return e
    beat = 60 / 85; chords = [(220, 261.6, 329.6), (174.6, 220, 261.6), (196, 246.9, 293.7), (164.8, 207.7, 246.9)]
    bed = np.zeros(n)
    for k in range(int(DUR / (beat * 4)) + 1):
        for f in chords[k % 4]: bed += 0.06 * np.sin(2 * np.pi * f * t) * env(k * beat * 4, 2.5) * (t >= k * beat * 4)
    for k in range(int(DUR / beat)):
        s0 = k * beat
        if s0 < 1.2: continue
        f = 55 * 2 ** (-np.clip((t - s0) * 30, 0, 3)); bed += 0.25 * np.sin(2 * np.pi * np.cumsum(f) / sr) * env(s0, 0.08) * (t >= s0)
        bed += 0.05 * noise * env(s0 + beat / 2, 0.02) * (t >= s0 + beat / 2)
    duck = np.ones(n)
    for who, tag, text, start, dur, e, x in voices:
        i0 = int(start * sr); mix[i0:i0 + len(x)] += x[:max(0, min(len(x), n - i0))] * 0.9
        duck[max(0, i0 - 2000):i0 + len(x) + 4000] = 0.4
    duck = np.convolve(duck, np.ones(4000) / 4000, mode="same")
    mix += bed * duck
    for s0 in (0.25, 0.5, 0.75, 1.0): mix += 0.12 * noise * env(s0, 0.02) * (t >= s0)            # neon buzz
    for s0 in (3.55, 7.5, 9.2): mix += 0.08 * noise * env(s0, 0.12) * (t >= s0)                 # soft whooshes on cuts
    mix += 0.18 * (np.sin(2 * np.pi * 523.3 * t) + 0.6 * np.sin(2 * np.pi * 784 * t)) * env(end_t, 0.9) * (t >= end_t)
    mix = mix / np.max(np.abs(mix)) * 0.89
    wav = os.path.join(tmp, "a.wav")
    with wave.open(wav, "w") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes((mix * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print(out)

if __name__ == "__main__":
    a = sys.argv[1:]; main(a[0], a[1], *(int(v) for v in a[2:4]))
