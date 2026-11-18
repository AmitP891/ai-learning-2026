"""Bit: Bug Patrol, Ep 1 "The Breach" (9:16 Short, ~47 s).

Usage: python3 build_bug_patrol_ep1.py CLIPS_DIR VO.mp3 OUT.mp4
CLIPS_DIR holds the 8 Runway clips in panel order: 01.mp4 … 08.mp4.
VO is Bit's 7 lines in one take (ElevenLabs); line bounds below come from silencedetect.
"""
import os, sys, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.signal import lfilter, butter

CLIPS, VO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
HERE = os.path.dirname(os.path.abspath(__file__))
BANG = os.path.join(HERE, "..", "fonts", "Bangers-Regular.ttf")
B = lambda s: ImageFont.truetype(BANG, s)
W, H, FPS, SR = 1080, 1920, 30, 48000
TMP = tempfile.mkdtemp(prefix="bp1_")

# ---------------------------------------------------------------- timeline
# (clip, seconds on screen, layout, cream border L,R,T,B)
CLIPS_T = [
    ("01", 6.5, "full", 32, 30, 46, 43),   # neon city
    ("02", 5.0, "full", 12, 12, 19, 28),   # landing
    ("03", 5.0, "fit", 8, 8, 8, 8),        # billboard
    ("04", 5.0, "full", 8, 7, 19, 28),     # leap
    ("05", 5.0, "fit", 8, 8, 11, 13),      # ZAP
    ("06", 5.0, "full", 8, 7, 19, 29),     # bug escapes
    ("07", 5.0, "full", 8, 8, 8, 8),       # green eyes
    ("08", 6.5, "fit", 8, 7, 11, 12),      # dawn
]
END_LEN = 4.5
starts = np.cumsum([0] + [c[1] for c in CLIPS_T]).tolist()
END_AT = starts[-1]                 # 43.0
TOTAL = END_AT + END_LEN            # 47.5

# VO lines: (src start, src end, place at, gain target dBFS RMS)
LINES = [
    (0.00, 5.94, 0.5, -20),    # Neon City…
    (6.59, 8.68, 7.0, -20),    # Quiet night. Too quiet.
    (9.02, 11.71, 11.8, -20),  # …Spoke too soon.
    (12.03, 13.58, 16.9, -17), # Bug Patrol, deploying!
    (13.90, 17.03, 27.0, -20), # One got away.
    (17.49, 21.20, 31.9, -22), # Wait… (whisper)
    (21.59, 26.80, 37.0, -20), # Bug fixed… for now.
]
def at(src):  # map a time in the VO file to the timeline
    for s, e, p, _ in LINES:
        if s - 0.05 <= src <= e + 0.05:
            return p + (src - s)
    raise ValueError(src)

# captions: (src start, src end, text) -> narration box at the top
CAPS = [
    (0.00, 1.07, "NEON CITY."),
    (1.60, 5.94, "TWO MILLION LINES OF CODE… AND ONE ROBOT KEEPING IT BUG-FREE."),
    (6.59, 7.38, "QUIET NIGHT."),
    (7.90, 8.68, "TOO QUIET."),
    (9.02, 11.71, "…SPOKE TOO SOON. BUG SWARM, SECTOR SEVEN."),
    (13.90, 17.03, "ONE GOT AWAY. AND IT KNEW EXACTLY WHERE IT WAS GOING."),
    (17.49, 17.82, "WAIT…"),
    (18.16, 19.65, "THESE BUGS DIDN'T JUST APPEAR."),
    (20.10, 21.20, "SOMEONE SENT THEM."),
    (23.49, 25.06, "NEXT TIME: SWARM CITY."),
    (25.38, 26.80, "FOLLOW SO YOU DON'T MISS IT."),
]

# ---------------------------------------------------------------- graphics
def stroked(d, xy, text, font, fill, stroke=8, sc=(0, 0, 0), anchor="mm"):
    d.text(xy, text, font=font, fill=fill, stroke_width=stroke, stroke_fill=sc, anchor=anchor)

def wrap(text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.getlength(t) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur)
    return lines

def narration_png(text, path, y=210):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = B(68); lines = wrap(text, f, 820); lh = 74
    bw = max(f.getlength(l) for l in lines) + 70; bh = lh * len(lines) + 44
    x0 = (W - bw) / 2
    d.rectangle([x0 + 10, y + 10, x0 + bw + 10, y + bh + 10], fill=(0, 0, 0, 200))
    d.rectangle([x0, y, x0 + bw, y + bh], fill=(255, 225, 77, 255), outline=(0, 0, 0, 255), width=6)
    for i, l in enumerate(lines):
        d.text((W / 2, y + 26 + lh * i + lh / 2 - 4), l, font=f, fill=(17, 17, 17), anchor="mm")
    im.save(path)

def burst_png(text, path, cy=1300):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    n, pts = 22, []
    for k in range(n * 2):
        a = np.pi * k / n; r = (470 if k % 2 == 0 else 360) * (1 + 0.06 * np.sin(k * 2.3))
        pts.append((W / 2 + r * np.cos(a), cy + 0.55 * r * np.sin(a)))
    d.polygon([(x + 12, y + 12) for x, y in pts], fill=(0, 0, 0, 220))
    d.polygon(pts, fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=7)
    stroked(d, (W / 2, cy - 55), "BUG PATROL,", B(120), (255, 79, 163), 7)
    stroked(d, (W / 2, cy + 65), "DEPLOYING!", B(132), (0, 200, 255), 7)
    im.save(path)

def title_png(path):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for dy, col in ((14, (255, 225, 77)), (0, (255, 79, 163))):
        stroked(d, (W / 2 + dy * .6, 760 + dy), "BIT:", B(210), col, 12)
        stroked(d, (W / 2 + dy * .6, 950 + dy), "BUG PATROL", B(210), col, 12)
    stroked(d, (W / 2, 1120), "EP 1 · THE BREACH", B(96), (0, 230, 255), 8)
    im.save(path)

def fixed_png(path, with_for_now):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = Image.new("RGBA", (W, 600), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    stroked(d, (W / 2 + 10, 210 + 10), "BUG FIXED", B(200), (0, 0, 0), 10)
    stroked(d, (W / 2, 210), "BUG FIXED", B(200), (57, 255, 136), 10)
    if with_for_now:
        stroked(d, (W / 2 + 60, 390), "…FOR NOW", B(120), (255, 60, 90), 9)
    g = g.rotate(6, resample=Image.BICUBIC, center=(W / 2, 300))
    im.alpha_composite(g, (0, 1180)); im.save(path)

def endcard_png(path):
    fr = os.path.join(TMP, "end_bg.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "4.6", "-i", os.path.join(CLIPS, "07.mp4"),
                    "-frames:v", "1", fr], check=True)
    bg = Image.open(fr).convert("RGB")
    s = max(W / bg.width, H / bg.height); bg = bg.resize((int(bg.width * s) + 1, int(bg.height * s) + 1))
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = Image.blend(bg.filter(ImageFilter.GaussianBlur(6)), Image.new("RGB", (W, H), (5, 8, 20)), 0.72).convert("RGBA")
    d = ImageDraw.Draw(bg)
    stroked(d, (W / 2, 420), "NEXT TIME ON", B(92), (255, 225, 77), 8)
    stroked(d, (W / 2, 530), "BIT: BUG PATROL", B(110), (255, 79, 163), 9)
    for dx, col in ((-9, (0, 230, 255)), (9, (255, 79, 163)), (0, (57, 255, 136))):
        stroked(d, (W / 2 + dx, 820), "SWARM", B(270), col, 12 if dx == 0 else 0)
        stroked(d, (W / 2 + dx, 1060), "CITY", B(270), col, 12 if dx == 0 else 0)
    stroked(d, (W / 2, 1230), "EPISODE 2", B(90), (255, 255, 255), 7)
    # follow pill
    d.rounded_rectangle([170, 1340, 910, 1470], 65, fill=(255, 79, 163), outline=(0, 0, 0), width=7)
    d.text((W / 2, 1405), "FOLLOW SO YOU DON'T MISS IT", font=B(66), fill=(255, 255, 255), anchor="mm",
           stroke_width=4, stroke_fill=(0, 0, 0))
    bg.convert("RGB").save(path)

# ---------------------------------------------------------------- video
def video():
    title_png(f"{TMP}/title.png"); burst_png("", f"{TMP}/burst.png")
    fixed_png(f"{TMP}/fixed.png", False); fixed_png(f"{TMP}/fixed2.png", True)
    endcard_png(f"{TMP}/end.png")
    ins, fc, ov = [], [], []
    for i, (c, dur, mode, L, R, T, Bt) in enumerate(CLIPS_T):
        ins += ["-i", os.path.join(CLIPS, c + ".mp4")]
        k = dur / 5.04
        crop = f"crop=iw-{L + R + 16}:ih-{T + Bt + 16}:{L + 8}:{T + 8}"
        slow = f"setpts={k:.4f}*PTS," if k > 1.01 else ""
        interp = "minterpolate=fps=30:mi_mode=blend," if k > 1.01 else "fps=30,"
        if mode == "full":
            fc.append(f"[{i}:v]{crop},{slow}{interp}scale={W}:{H}:force_original_aspect_ratio=increase,"
                      f"crop={W}:{H},setsar=1,trim=duration={dur},setpts=PTS-STARTPTS[c{i}]")
        else:
            fc.append(f"[{i}:v]{crop},{slow}{interp}split[a{i}][b{i}];"
                      f"[a{i}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=28:2,"
                      f"eq=brightness=-0.12:saturation=1.2[bg{i}];"
                      f"[b{i}]scale={W}:-2[fg{i}];[bg{i}][fg{i}]overlay=0:(H-h)/2,setsar=1,"
                      f"trim=duration={dur},setpts=PTS-STARTPTS[c{i}]")
    n = len(CLIPS_T)
    ins += ["-loop", "1", "-t", str(END_LEN), "-i", f"{TMP}/end.png"]
    fc.append(f"[{n}:v]fps=30,scale={W}:{H},setsar=1,zoompan=z='1+0.0006*on':d=1:s={W}x{H}:fps=30,"
              f"trim=duration={END_LEN},fade=in:st=0:d=0.25[c{n}]")
    fc.append("".join(f"[c{i}]" for i in range(n + 1)) + f"concat=n={n + 1}:v=1:a=0[base]")
    # overlays
    items = [] if os.environ.get("NO_TITLE") else [(f"{TMP}/title.png", 0.0, 2.4, 0.35)]
    for j, (s, e, text) in enumerate(CAPS):
        p = f"{TMP}/cap{j}.png"; narration_png(text, p)
        t0 = at(s); nxt = at(CAPS[j + 1][0]) if j + 1 < len(CAPS) else 99
        items.append((p, t0, min(at(e) + 0.5, nxt - 0.03), 0))
    items.append((f"{TMP}/burst.png", at(12.03), at(13.58) + 0.5, 0))
    items.append((f"{TMP}/fixed.png", at(21.59), at(21.59) + 0.95, 0))
    items.append((f"{TMP}/fixed2.png", at(21.59) + 0.95, END_AT - 0.02, 0))
    last, k0 = "base", n + 1
    for j, (p, t0, t1, fade) in enumerate(items):
        ins += ["-loop", "1", "-t", f"{TOTAL}", "-i", p]
        src = f"[{k0 + j}:v]format=rgba"
        if fade: src += f",fade=out:st={t1 - fade:.2f}:d={fade}:alpha=1"
        fc.append(f"{src}[o{j}];[{last}][o{j}]overlay=0:0:enable='between(t,{t0:.2f},{t1:.2f})'[v{j}]")
        last = f"v{j}"
    fc.append(f"[{last}]trim=duration={TOTAL},format=yuv420p[vout]")
    out = f"{TMP}/video.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fc), "-map", "[vout]",
                    "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "18", out], check=True)
    return out

# ---------------------------------------------------------------- audio
def load(path, extra_af=None):
    cmd = ["ffmpeg", "-v", "error", "-i", path]
    if extra_af: cmd += ["-af", extra_af]
    cmd += ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).copy()

def lp(x, fc, order=2): b, a = butter(order, fc / (SR / 2)); return lfilter(b, a, x)
def hp(x, fc, order=2): b, a = butter(order, fc / (SR / 2), "high"); return lfilter(b, a, x)
def bp(x, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], "band"); return lfilter(b, a, x)
def env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)
def saw(f, n, ph=0): t = np.arange(n) / SR; return 2 * ((f * t + ph) % 1) - 1
def hz(m): return 440 * 2 ** ((m - 69) / 12)
rng = np.random.default_rng(7)
def noise(n): return rng.standard_normal(n).astype(np.float64)

def add(buf, x, t, g=1.0):
    i = int(t * SR); j = min(len(buf), i + len(x))
    if j > i: buf[i:j] += g * x[: j - i]

def mk_kick():
    n = int(.45 * SR); t = np.arange(n) / SR; f = 48 + 120 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
def mk_snare():
    n = int(.25 * SR); t = np.arange(n) / SR
    return (0.7 * bp(noise(n), 1500, 7000) + 0.4 * np.sin(2 * np.pi * 190 * t)) * np.exp(-t * 18)
def mk_hat(): n = int(.06 * SR); return hp(noise(n), 7000) * np.exp(-np.arange(n) / SR * 70)
def chord(notes, dur, cut=900, det=0.004):
    n = int(dur * SR); x = sum(saw(hz(m) * (1 + det), n) + saw(hz(m) * (1 - det), n, .3) for m in notes)
    x = lp(x, cut); a = np.minimum(1, np.arange(n) / (0.4 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.4 * SR))
    return x * a / len(notes)

def music():
    m = np.zeros(int((TOTAL + 1) * SR)); beat = 0.5
    K, S, Hh = mk_kick(), mk_snare(), mk_hat()
    # intro: dark pad + rain + thunder
    add(m, chord([45, 52, 57, 60], 6.6, 700), 0, 0.35)
    add(m, lp(hp(noise(int(6.8 * SR)), 2500), 9000) * 0.05, 0)
    # A-minor pulse from the landing; drums build
    prog = [(45, [57, 60, 64]), (41, [53, 57, 60]), (43, [55, 59, 62]), (40, [52, 55, 59])]
    for sec0, sec1, lvl in ((6.5, 16.5, 1), (16.5, 26.5, 2)):
        t = sec0
        while t < sec1 - 1e-6:
            bar = int((t - 6.5) / 2) % 4; root, ch = prog[bar]
            step = int(round((t - 6.5) / (beat / 2)))
            nb = int(beat / 2 * SR)
            b = lp(saw(hz(root - 12 + (12 if step % 4 == 2 else 0)), nb), 500 + 300 * lvl) * env(nb, .003, .12)
            add(m, b, t, 0.5)
            if step % 2 == 0: add(m, K, t, 0.75 if lvl == 2 or t > 11.5 else 0.45)
            if lvl == 2 and step % 4 == 2: add(m, S, t, 0.45)
            if t > 11.5: add(m, Hh, t + beat / 4, 0.12 if lvl == 1 else 0.18)
            if step % 8 == 0: add(m, chord(ch, 2.0, 1200 + 600 * lvl), t, 0.22 if lvl == 1 else 0.3)
            t += beat / 2
    # risers into the leap and the zap
    for r0, r1 in ((15.2, 16.5), (20.2, 21.5)):
        n = int((r1 - r0) * SR); x = bp(noise(n), 800, 6000) * np.linspace(0, 1, n) ** 2
        add(m, x, r0, 0.35)
    # tension: drone, slow tick
    add(m, chord([38, 45, 50], 10.2, 450), 26.5, 0.45)
    add(m, chord([62, 65], 10.2, 1400, .008), 26.5, 0.12)
    t = 26.5
    while t < 36.4: add(m, Hh, t, 0.1); add(m, K, t, 0.25) if int((t - 26.5) / beat) % 4 == 0 else None; t += beat
    # dawn: warm major
    add(m, chord([48, 55, 60, 64, 67], 3.4, 1800), 36.5, 0.35)
    add(m, chord([53, 57, 60, 65, 69], 3.4, 1800), 39.7, 0.35)
    for i, nn in enumerate([72, 76, 79, 84, 79, 76, 79, 84]):
        nb = int(0.9 * SR); add(m, np.sin(2 * np.pi * hz(nn) * np.arange(nb) / SR) * env(nb, .01, .5), 36.6 + i * 0.75, 0.08)
    # end card sting
    add(m, K, END_AT, 1.0); add(m, chord([45, 52, 57, 64], END_LEN, 1500), END_AT, 0.35)
    return m

def sfx():
    s = np.zeros(int((TOTAL + 1) * SR))
    def boom(t, g=1.0, f=45):
        n = int(1.6 * SR); tt = np.arange(n) / SR
        add(s, (np.sin(2 * np.pi * f * tt) + 0.5 * lp(noise(n), 200)) * np.exp(-tt * 3), t, g)
    def whoosh(t, d=0.7, g=0.5):
        n = int(d * SR); x = bp(noise(n), 500, 4000); add(s, x * np.sin(np.pi * np.arange(n) / n) ** 2, t, g)
    # thunder
    n = int(2.5 * SR); add(s, lp(noise(n), 160) * env(n, .25, .9), 0.15, 1.2)
    whoosh(6.0, 0.6); boom(6.55, 1.0)                       # landing
    n = int(.5 * SR); add(s, hp(noise(n), 2500) * env(n, .001, .09), 11.55, 0.5)   # glass crack
    for k in range(6):                                       # glitch bursts on the billboard
        n = int(.06 * SR); add(s, np.sign(saw(300 + 140 * k, n)) * 0.3, 11.7 + k * 0.11, 0.25)
    whoosh(16.4, 0.9, 0.7)                                   # leap
    # ZAP: electric chirp + boom
    n = int(1.1 * SR); tt = np.arange(n) / SR
    z = np.sin(2 * np.pi * np.cumsum(1800 * np.exp(-tt * 4) + 120 + 80 * noise(n)) / SR)
    add(s, (np.sign(z) * 0.5 + 0.5 * bp(noise(n), 2000, 9000)) * np.exp(-tt * 4), 21.65, 0.55); boom(21.65, 1.2, 40)
    # bug buzz
    n = int(5 * SR); tt = np.arange(n) / SR
    bz = np.sign(np.sin(2 * np.pi * (210 + 25 * np.sin(2 * np.pi * 3 * tt)) * tt)) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * tt))
    add(s, lp(bz, 2500) * np.minimum(1, tt / .5) * np.minimum(1, (5 - tt) / .5), 26.5, 0.07)
    # green eyes: hum + glitch
    n = int(5 * SR); tt = np.arange(n) / SR
    add(s, (np.sin(2 * np.pi * 55 * tt) + .3 * np.sin(2 * np.pi * 110 * tt)) * np.minimum(1, tt / .3) * np.minimum(1, (5 - tt) / .5), 31.5, 0.18)
    for k in range(4):
        n = int(.05 * SR); add(s, np.sign(saw(90 + 60 * k, n)) * 0.3, 31.55 + k * 0.08, 0.3)
    # end-card glitch
    for k in range(5):
        n = int(.05 * SR); add(s, np.sign(saw(200 + 90 * k, n)) * 0.3, END_AT + k * 0.06, 0.25)
    return s

def audio():
    raw = load(VO, "acompressor=threshold=-22dB:ratio=3:attack=5:release=120:makeup=2,"
                   "equalizer=f=140:t=q:w=1:g=3,equalizer=f=3500:t=q:w=1:g=2,"
                   "aecho=0.8:0.5:45:0.12")
    vo = np.zeros(int((TOTAL + 1) * SR)); duck = np.zeros_like(vo)
    for s, e, p, tgt in LINES:
        seg = raw[int(s * SR): int(e * SR)].astype(np.float64)
        rms = np.sqrt((seg ** 2).mean()) + 1e-9; seg *= 10 ** (tgt / 20) / rms
        f = int(0.01 * SR); seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        add(vo, seg, p); add(duck, np.ones(len(seg) + int(0.25 * SR)), p - 0.1)
    duck = np.clip(duck, 0, 1); k = int(0.12 * SR)
    duck = np.convolve(duck, np.ones(k) / k, "same")
    m = music() * (1 - 0.6 * duck); x = sfx() * (1 - 0.35 * duck)
    mix = vo + 0.55 * m + 0.6 * x
    mix = mix[: int(TOTAL * SR)]; mix /= max(1e-9, np.abs(mix).max()) / 0.9
    wav = f"{TMP}/mix.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-af", "loudnorm=I=-13:TP=-1:LRA=9", "-ar", str(SR), "-ac", "2", wav],
                   input=mix.astype(np.float32).tobytes(), check=True)
    return wav

if __name__ == "__main__":
    a = audio(); v = video()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-i", a, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
    print("wrote", OUT, "tmp", TMP)
