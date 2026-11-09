"""Unboxing Short v2: timelapse unboxing -> reveal -> 'is that me?' -> CTA. 1080x1920, 30 fps.

    python3 build_unboxing_v2.py <work_dir>

<work_dir> holds f1/ and f2/ (JPEG frames of clip1 and clip2 at 1080x1920, 30 fps:
  ffmpeg -i clip1.mov -vf scale=1080:1920 -q:v 3 f1/%04d.jpg) and, optionally, Bit's voice lines
vo1.mp3 .. vo4.mp3 (ElevenLabs). Without them the draft shows the lines as captions only.
Speed ramps: clip1 plays at 5x (timelapse) until the face appears, then real time;
clip2 plays the turn at 2.5x, then the face close-up at real time."""
import io, math, os, re, subprocess, sys, wave
import numpy as np, cairosvg
from PIL import Image, ImageDraw, ImageFont

WD = sys.argv[1] if len(sys.argv) > 1 else "."
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
W, H, FPS, SR = 1080, 1920, 30, 44100
PK, CY, YL, WH, BG, GR = (240, 53, 158), (0, 240, 255), (255, 214, 0), (245, 244, 239), (13, 13, 20), (57, 255, 136)
TITLE = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", s)
MONO = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", s)

# ---- edit plan: (clip, src_start, src_end, speed) -> output segments ------------------------------
PLAN = [(1, 0.0, 29.0, 5.0), (1, 29.0, 31.4, 1.0),     # timelapse unbox, then the face appears
        (2, 0.0, 7.4, 2.5), (2, 7.4, 12.0, 1.0)]       # the turn, then the face close-up
CTA = 4.0
segs, t = [], 0.0
for c, a, b, sp in PLAN:
    d = (b - a) / sp; segs.append((t, t + d, c, a, sp)); t += d
T_CTA = t; DUR = t + CTA; N = int(round(DUR * FPS))
T_FACE1 = segs[1][0] + 1.0          # Bit's face shows in clip1
T_TURN = segs[3][0]                 # clip2 face turns to camera
nframes = {c: len(os.listdir(os.path.join(WD, f"f{c}"))) for c in (1, 2)}

# ---- Bit's lines (captions now, his cloned voice later) --------------------------------------------
LINES = [(0.4, "Ooh, a parcel. For me?"),
         (T_FACE1 - 0.2, "Wait… is that ME?!"),
         (T_TURN + 0.3, "Look at my little code screen."),
         (T_CTA + 0.2, "I'm REAL now. Subscribe!")]

def load_audio(fn):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", fn, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768
VO = [load_audio(os.path.join(WD, f"vo{i}.mp3")) if os.path.exists(os.path.join(WD, f"vo{i}.mp3")) else None for i in range(1, 5)]

# ---- music: light, bouncy, major key (C major, 112 BPM) --------------------------------------------
BPM = 112; BEAT = 60 / BPM
def note(f, d, kind="pluck", v=0.3):
    n = int(d * SR); tt = np.arange(n) / SR
    if kind == "pluck":   # soft square + sine, quick decay
        w = 0.55 * np.sign(np.sin(2 * np.pi * f * tt)) * 0.35 + 0.65 * np.sin(2 * np.pi * f * tt)
        env = np.exp(-tt * 7)
    elif kind == "bass":
        w = np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt); env = np.exp(-tt * 3)
    elif kind == "bell":
        w = np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 2.76 * tt); env = np.exp(-tt * 4)
    env[: min(n, 60)] *= np.linspace(0, 1, min(n, 60))
    return (w * env * v).astype(np.float32)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
def put(buf, t0, x, g=1.0):
    i = int(t0 * SR); j = min(len(buf), i + len(x))
    if i < len(buf): buf[i:j] += x[: j - i] * g

def music():
    buf = np.zeros(int((DUR + 2) * SR), np.float32)
    chords = [(48, [60, 64, 67]), (45, [57, 60, 64]), (41, [57, 60, 65]), (43, [59, 62, 67])]  # C Am F G
    mel = [72, 76, 79, 76, 77, 76, 74, 72, 69, 72, 76, 74, 72, 74, 76, 79]
    bar = 0; tb = 0.0
    while tb < DUR + 1:
        root, tri = chords[bar % 4]
        for b in range(4):
            t0 = tb + b * BEAT
            put(buf, t0, note(hz(root - 12 if b % 2 == 0 else root), BEAT * 0.9, "bass", 0.32))
            for k, m in enumerate(tri): put(buf, t0 + BEAT / 2, note(hz(m), BEAT * 0.4, "pluck", 0.07))
            # hat: tiny noise tick on the off-beat
            n = int(0.03 * SR); put(buf, t0 + BEAT / 2, (np.random.randn(n) * np.exp(-np.arange(n) / 300)).astype(np.float32), 0.05)
            if b in (1, 3):  # soft clap
                n = int(0.08 * SR); put(buf, t0, (np.random.randn(n) * np.exp(-np.arange(n) / 900)).astype(np.float32), 0.06)
        for k in range(4):
            put(buf, tb + k * BEAT, note(hz(mel[(bar * 4 + k) % 16]), BEAT * 0.8, "pluck", 0.16))
        bar += 1; tb += 4 * BEAT
    return buf

def sfx_whoosh(d=0.35):
    n = int(d * SR); x = np.random.randn(n).astype(np.float32)
    x = np.convolve(x, np.ones(40) / 40, "same"); return x * np.sin(np.linspace(0, np.pi, n)) * 0.6
def sfx_ding():
    return note(hz(88), 0.9, "bell", 0.35) + note(hz(95), 0.9, "bell", 0.2)

def mix():
    m = music()[: int(DUR * SR)]
    voice = np.zeros_like(m)
    for (t0, _), v in zip(LINES, VO):
        if v is not None: put(voice, t0, v)
    # duck the music under Bit's voice
    if np.abs(voice).max() > 0:
        env = np.convolve(np.abs(voice), np.ones(4000) / 4000, "same"); duck = 1 - 0.55 * np.clip(env / (env.max() + 1e-9) * 3, 0, 1)
        m = m * duck
    fx = np.zeros_like(m)
    put(fx, segs[1][0] - 0.2, sfx_whoosh()); put(fx, T_FACE1, sfx_ding())
    put(fx, segs[2][0], sfx_whoosh()); put(fx, T_TURN + 0.1, sfx_ding()); put(fx, T_CTA, sfx_whoosh())
    fade = np.ones_like(m); fo = int(0.6 * SR); fade[-fo:] = np.linspace(1, 0, fo)
    out = (m * 0.9 + fx * 0.6) * fade + voice * 1.0
    return out / (np.abs(out).max() / 0.5)   # peak -6 dB

# ---- pictures ---------------------------------------------------------------------------------------
def bit_png(h, mood="happy"):
    s = open(os.path.join(ROOT, "brand/bit/bit.svg")).read()
    if mood == "happy":
        s = re.sub(r'<g id="eyes">.*?</g>', '<g id="eyes"><path d="M222 214 Q244 186 266 214" stroke="#00F0FF" stroke-width="14" fill="none" stroke-linecap="round"/><path d="M334 214 Q356 186 378 214" stroke="#00F0FF" stroke-width="14" fill="none" stroke-linecap="round"/></g>', s, flags=re.S)
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=s.encode(), output_width=round(600 * h / 700), output_height=h))).convert("RGBA")
BIT_CTA = bit_png(760)

def src_frame(t):
    for a, b, c, s0, sp in segs:
        if a <= t < b:
            i = int((s0 + (t - a) * sp) * FPS) + 1
            return Image.open(os.path.join(WD, f"f{c}", f"{min(max(i, 1), nframes[c]):04d}.jpg")).convert("RGBA"), sp
    return None, 1

def text_box(im, s, y, size, fg, bg=(13, 13, 20, 215), pad=26, font=TITLE):
    d = ImageDraw.Draw(im); f = font(size)
    while d.textlength(s, font=f) > W - 140: size -= 4; f = font(size)
    w = d.textlength(s, font=f); x = (W - w) / 2
    d.rounded_rectangle((x - pad, y - pad * 0.6, x + w + pad, y + size * 1.05 + pad * 0.6), 22, fill=bg)
    d.text((W / 2, y), s, font=f, fill=fg, anchor="mt")

def pop(t, t0, d=0.18):
    u = (t - t0) / d
    return None if u < 0 else (1.0 if u >= 1 else u)

def frame(n):
    t = n / FPS
    if t < T_CTA:
        im, sp = src_frame(t)
        d = ImageDraw.Draw(im)
        if sp > 1.0:   # timelapse badge
            d.rounded_rectangle((W - 250, 150, W - 50, 226), 18, fill=(13, 13, 20, 200))
            d.text((W - 150, 188), f"{sp:g}x ▶▶", font=MONO(40), fill=CY, anchor="mm")
        if t < 2.2:    # hook
            text_box(im, "UNBOXING…", 300, 120, YL); text_box(im, "MYSELF?", 450, 150, PK)
        for k, (t0, line) in enumerate(LINES[:3]):
            end = LINES[k + 1][0] if k + 1 < len(LINES) else T_CTA
            cut = min([b for a, b, *_ in segs if b > t0 + 0.8] + [T_CTA])   # don't run over a hard cut
            if t0 <= t < min(end, t0 + 3.2, cut) and pop(t, t0) is not None:
                text_box(im, line, 1440, 76, WH)
        for tf in (T_FACE1, T_TURN):  # white flash on each reveal
            if tf <= t < tf + 0.12:
                a = int(200 * (1 - (t - tf) / 0.12)); im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, a)))
        return im.convert("RGB")
    # CTA card
    u = t - T_CTA
    im = Image.new("RGBA", (W, H), BG + (255,)); d = ImageDraw.Draw(im)
    for y in range(0, H, 60): d.line((0, y, W, y), fill=(22, 24, 38))
    for x in range(0, W, 60): d.line((x, 0, x, H), fill=(22, 24, 38))
    bob = int(10 * math.sin(u * 5))
    im.alpha_composite(BIT_CTA, ((W - BIT_CTA.width) // 2, 560 + bob))
    k = pop(t, T_CTA, 0.25) or 0
    text_box(im, "BIT IS REAL", 260, int(140 * (0.6 + 0.4 * k)), PK)
    if u > 0.6: text_box(im, LINES[3][1], 1400, 70, WH)
    if u > 1.2 and int(u * 3) % 2 == 0: text_box(im, "SUBSCRIBE", 1560, 96, YL)
    if u > 1.2: d.text((W / 2, 1720), "@vibewithamitai", font=MONO(48), fill=(215, 180, 255), anchor="mt")
    return im.convert("RGB")

def main():
    out = os.path.join(WD, "unboxing_draft.mp4"); wav = os.path.join(WD, "unbox_mix.wav")
    pcm = (np.clip(mix(), -1, 1) * 32767).astype(np.int16)
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.repeat(pcm, 2).tobytes())
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-t", f"{DUR:.3f}", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for n in range(N): ff.stdin.write(frame(n).tobytes())
    ff.stdin.close(); ff.wait(); os.remove(wav)
    print(out, f"{DUR:.1f}s", "lines at", [round(a, 2) for a, _ in LINES])

if __name__ == "__main__":
    main()
