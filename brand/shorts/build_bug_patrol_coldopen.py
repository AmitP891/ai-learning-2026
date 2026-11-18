"""Bit: Bug Patrol, Ep 1 cold open (3.2 s), prepended to the episode for a 1-second hook.

Usage: python3 build_bug_patrol_coldopen.py CLIPS_DIR VO.mp3 OUT.mp4
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
TMP = tempfile.mkdtemp(prefix="bpc_")


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



SHOTS = [("05", 1.3, 1.6, "fit", 8, 8, 11, 13), ("04", 2.0, 1.6, "full", 8, 7, 19, 28)]
TOTAL = 3.2

def video():
    title_png(f"{TMP}/title.png"); narration_png("BUG PATROL, DEPLOYING!", f"{TMP}/cap.png")
    ins, fc = [], []
    for i, (c, ss, dur, mode, L, R, T, Bt) in enumerate(SHOTS):
        ins += ["-ss", str(ss), "-t", str(dur + 0.2), "-i", os.path.join(CLIPS, c + ".mp4")]
        crop = f"crop=iw-{L + R + 16}:ih-{T + Bt + 16}:{L + 8}:{T + 8},fps=30"
        if mode == "full":
            fc.append(f"[{i}:v]{crop},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
                      f"trim=duration={dur},setpts=PTS-STARTPTS[c{i}]")
        else:
            fc.append(f"[{i}:v]{crop},split[a{i}][b{i}];[a{i}]scale={W}:{H}:force_original_aspect_ratio=increase,"
                      f"crop={W}:{H},boxblur=28:2,eq=brightness=-0.12:saturation=1.2[bg{i}];[b{i}]scale={W}:-2[fg{i}];"
                      f"[bg{i}][fg{i}]overlay=0:(H-h)/2,setsar=1,trim=duration={dur},setpts=PTS-STARTPTS[c{i}]")
    fc.append("[c0][c1]concat=n=2:v=1:a=0[base]")
    ins += ["-loop", "1", "-t", "4", "-i", f"{TMP}/cap.png", "-loop", "1", "-t", "4", "-i", f"{TMP}/title.png"]
    fc.append("[2:v]format=rgba[o0];[base][o0]overlay=0:0:enable='between(t,0,1.6)'[v0]")
    fc.append("[3:v]format=rgba[o1];[v0][o1]overlay=0:0:enable='between(t,1.6,3.2)',trim=duration=3.2,format=yuv420p[vout]")
    out = f"{TMP}/video.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fc), "-map", "[vout]", "-r", "30",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", out], check=True)
    return out

def audio():
    raw = load(VO, "acompressor=threshold=-22dB:ratio=3:attack=5:release=120:makeup=2,"
                   "equalizer=f=140:t=q:w=1:g=3,equalizer=f=3500:t=q:w=1:g=2,aecho=0.8:0.5:45:0.12")
    n = int(TOTAL * SR); vo = np.zeros(n + SR); s = np.zeros(n + SR); m = np.zeros(n + SR)
    seg = raw[int(12.03 * SR): int(13.58 * SR)].astype(np.float64)
    seg *= 10 ** (-17 / 20) / (np.sqrt((seg ** 2).mean()) + 1e-9); add(vo, seg, 0.05)
    tt = np.arange(int(1.1 * SR)) / SR
    z = np.sin(2 * np.pi * np.cumsum(1800 * np.exp(-tt * 4) + 120 + 80 * noise(len(tt))) / SR)
    add(s, (np.sign(z) * 0.5 + 0.5 * bp(noise(len(tt)), 2000, 9000)) * np.exp(-tt * 4), 0.0, 0.45)
    tb = np.arange(int(1.6 * SR)) / SR
    add(s, (np.sin(2 * np.pi * 40 * tb) + 0.5 * lp(noise(len(tb)), 200)) * np.exp(-tb * 3), 0.0, 1.1)
    k = int(0.9 * SR); add(s, bp(noise(k), 500, 4000) * np.sin(np.pi * np.arange(k) / k) ** 2, 1.35, 0.6)
    K, S_, Hh = mk_kick(), mk_snare(), mk_hat()
    for i in range(int(TOTAL / 0.25)):
        t = i * 0.25; nb = int(0.25 * SR)
        add(m, lp(saw(hz(33 + (12 if i % 4 == 2 else 0)), nb), 1100) * env(nb, .003, .12), t, 0.5)
        if i % 2 == 0: add(m, K, t, 0.8)
        if i % 4 == 2: add(m, S_, t, 0.45)
        add(m, Hh, t + 0.125, 0.18)
    add(m, chord([57, 60, 64], 3.2, 2200), 0, 0.3)
    duck = np.zeros_like(vo); duck[int(0.0 * SR): int(1.7 * SR)] = 1
    mix = vo + 0.55 * m * (1 - 0.5 * duck) + 0.6 * s * (1 - 0.3 * duck)
    mix = mix[:n]; mix /= np.abs(mix).max() / 0.9
    wav = f"{TMP}/mix.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-af", "volume=-6dB", "-ar", str(SR), "-ac", "2", wav], input=mix.astype(np.float32).tobytes(), check=True)
    return wav

if __name__ == "__main__":
    a = audio(); v = video()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-i", a, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "pcm_s16le", "-shortest", OUT], check=True)
    print("wrote", OUT)
