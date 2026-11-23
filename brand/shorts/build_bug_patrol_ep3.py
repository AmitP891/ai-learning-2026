"""Bit: Bug Patrol, Ep 3 "Someone's Cheating" (9:16 Short, ~50 s). Cold open first.

Usage: python3 build_bug_patrol_ep3.py CLIPS_DIR BIT.mp3 WALLHACK.mp3 OUT.mp4
CLIPS_DIR holds the 8 Runway clips (gen-4 turbo, 720x1280) in panel order: 01.mp4 … 08.mp4.
Line bounds below come from silencedetect on the ElevenLabs takes.
"""
import os, sys, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.signal import lfilter, butter

CLIPS, VO_BIT, VO_WH, OUT = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
BANG = os.path.join(HERE, "..", "fonts", "Bangers-Regular.ttf")
B = lambda s: ImageFont.truetype(BANG, s)
W, H, FPS, SR = 1080, 1920, 30, 48000
TMP = tempfile.mkdtemp(prefix="bp3_")

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
    stroked(d, (W / 2, 1120), SUBTITLE, B(96), (0, 230, 255), 8)
    im.save(path)


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


SUBTITLE = "EP 3 · SOMEONE'S CHEATING"
BORDER = 22  # cream comic-paper edge on the 720x1280 clips, cropped off

def clip_len(c):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 os.path.join(CLIPS, c + ".mp4")], capture_output=True, text=True).stdout)

# (clip, seconds on screen)
CLIPS_T = [("01", 5.0), ("02", 5.0), ("03", 5.0), ("04", 6.0), ("05", 5.5), ("06", 5.0), ("07", 5.0), ("08", 9.0)]
END_LEN = 4.5
starts = np.cumsum([0] + [c[1] for c in CLIPS_T]).tolist()
END_AT = starts[-1]
TOTAL = END_AT + END_LEN
P = dict(zip([c[0] for c in CLIPS_T], starts))  # panel start times

# VO lines: (source, src start, src end, place at, dB RMS); bounds from silencedetect (-38 dB) on the two takes
LINES = [
    ("bit", 0.00, 1.80, 0.15, -18),            # He just walked through the WALL?!
    ("bit", 2.60, 6.30, P["02"] + 0.6, -20),   # Every high score in Neon City… gone overnight.
    ("bit", 7.28, 11.07, P["03"] + 0.3, -20),  # Nobody walks through walls. Nobody fair, anyway.
    ("wh", 0.00, 3.70, P["04"] + 0.3, -20),    # I see you, little robot. I see everything.
    ("bit", 11.87, 12.76, P["04"] + 4.4, -20), # …Creepy.
    ("bit", 13.41, 14.81, P["05"] + 0.4, -19), # Can't you win fair?
    ("wh", 3.85, 5.98, P["05"] + 2.1, -19),    # (snicker) Fair is for losers.
    ("bit", 15.57, 17.25, P["06"] + 0.8, -19), # Then it's time for a patch.
    ("bit", 17.76, 18.57, P["07"] + 1.1, -17), # Patched.
    ("wh", 6.25, 7.81, P["08"] + 0.4, -18),    # This isn't over!
    ("bit", 19.28, 28.00, P["08"] + 2.2, -20), # Scores restored… who's pulling the strings? Next time: everything… slows… down.
]
def at(src, s):
    for so, a, b, p, _ in LINES:
        if so == src and a - 0.05 <= s <= b + 0.05: return p + (s - a)
    raise ValueError((src, s))

# captions: (source, src start, src end, text, style)
CAPS = [
    ("bit", 0.00, 1.80, "HE JUST WALKED THROUGH THE WALL?!", "n"),
    ("bit", 2.70, 4.57, "EVERY HIGH SCORE IN NEON CITY…", "n"),
    ("bit", 5.07, 6.20, "GONE OVERNIGHT.", "n"),
    ("bit", 7.38, 9.16, "NOBODY WALKS THROUGH WALLS.", "n"),
    ("bit", 9.69, 10.97, "NOBODY FAIR, ANYWAY.", "n"),
    ("wh", 0.00, 1.80, "I SEE YOU, LITTLE ROBOT.", "v"),
    ("wh", 2.23, 3.64, "I SEE EVERYTHING.", "v"),
    ("bit", 11.97, 12.66, "…CREEPY.", "n"),
    ("bit", 13.51, 14.71, "CAN'T YOU WIN FAIR?", "n"),
    ("wh", 4.44, 5.91, "FAIR IS FOR LOSERS.", "v"),
    ("bit", 15.67, 17.15, "THEN IT'S TIME FOR A PATCH.", "n"),
    ("wh", 6.32, 7.48, "THIS ISN'T OVER!", "v"),
    ("bit", 19.38, 20.79, "SCORES RESTORED…", "n"),
    ("bit", 21.33, 23.15, "BUT WHO'S PULLING THE STRINGS?", "n"),
    ("bit", 23.99, 27.80, "NEXT TIME: EVERYTHING… SLOWS… DOWN.", "n"),
]
PATCH_AT = at("bit", 17.86)

def villain_png(text, path, y=210):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = B(70); lines = wrap(text, f, 820); lh = 76
    bw = max(f.getlength(l) for l in lines) + 70; bh = lh * len(lines) + 44; x0 = (W - bw) / 2
    d.rectangle([x0 + 10, y + 10, x0 + bw + 10, y + bh + 10], fill=(0, 0, 0, 200))
    d.rectangle([x0, y, x0 + bw, y + bh], fill=(255, 60, 80, 255), outline=(0, 0, 0, 255), width=6)
    d.text((x0 + 18, y - 22), "WALLHACK", font=B(40), fill=(20, 20, 30), stroke_width=4, stroke_fill=(0, 230, 255))
    for i, l in enumerate(lines):
        d.text((W / 2, y + 26 + lh * i + lh / 2 - 4), l, font=f, fill=(255, 255, 255), anchor="mm")
    im.save(path)

def stamp_png(path, text, sub=None, col=(0, 230, 255)):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = Image.new("RGBA", (W, 600), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    stroked(d, (W / 2 + 10, 230), text, B(230), (0, 0, 0), 10); stroked(d, (W / 2, 220), text, B(230), col, 10)
    if sub: stroked(d, (W / 2, 400), sub, B(90), (255, 225, 77), 8)
    g = g.rotate(-5, resample=Image.BICUBIC, center=(W / 2, 300)); im.alpha_composite(g, (0, 1150)); im.save(path)

def morning_png(path):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([60, 1470, 520, 1570], fill=(255, 225, 77), outline=(0, 0, 0), width=6)
    d.text((290, 1520), "THAT MORNING…", font=B(66), fill=(17, 17, 17), anchor="mm"); im.save(path)

def scores_png(path):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x0, y0 = 170, 560
    d.rectangle([x0 + 10, y0 + 10, W - x0 + 10, y0 + 430], fill=(0, 0, 0, 200))
    d.rectangle([x0, y0, W - x0, y0 + 420], fill=(12, 10, 30, 235), outline=(0, 230, 255), width=6)
    d.text((W / 2, y0 + 50), "HIGH SCORES", font=B(64), fill=(0, 230, 255), anchor="mm")
    for i in range(4):
        y = y0 + 130 + i * 72
        d.text((x0 + 50, y), f"{i + 1}.", font=B(58), fill=(255, 225, 77), anchor="lm")
        d.text((x0 + 130, y), "WALLHACK", font=B(58), fill=(255, 60, 80), anchor="lm")
        d.text((W - x0 - 50, y), "999999", font=B(58), fill=(255, 60, 80), anchor="rm")
    im.save(path)

def endcard_png(path):
    fr = f"{TMP}/end_bg.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.5", "-i", os.path.join(CLIPS, "08.mp4"), "-frames:v", "1", fr], check=True)
    bg = Image.open(fr).convert("RGB"); bg = bg.crop((BORDER, BORDER, bg.width - BORDER, bg.height - BORDER)).resize((W, H))
    bg = Image.blend(bg.filter(ImageFilter.GaussianBlur(7)), Image.new("RGB", (W, H), (5, 8, 20)), 0.72).convert("RGBA")
    d = ImageDraw.Draw(bg)
    stroked(d, (W / 2, 420), "NEXT TIME ON", B(92), (255, 225, 77), 8)
    stroked(d, (W / 2, 530), "BIT: BUG PATROL", B(110), (255, 79, 163), 9)
    for k, word in enumerate(["EVERYTHING…", "SLOWS…", "DOWN"]):
        for dx, col in ((-9, (0, 230, 255)), (9, (255, 79, 163)), (0, (255, 255, 255))):
            stroked(d, (W / 2 + dx + k * 40 - 40, 740 + k * 170), word, B(190 - k * 10), col, 11 if dx == 0 else 0)
    stroked(d, (W / 2, 1250), "EPISODE 4", B(90), (255, 225, 77), 7)
    d.rounded_rectangle([170, 1340, 910, 1470], 65, fill=(255, 79, 163), outline=(0, 0, 0), width=7)
    d.text((W / 2, 1405), "FOLLOW SO YOU DON'T MISS IT", font=B(66), fill=(255, 255, 255), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
    bg.convert("RGB").save(path)

def video():
    title_png(f"{TMP}/title.png"); morning_png(f"{TMP}/morning.png"); scores_png(f"{TMP}/scores.png"); endcard_png(f"{TMP}/end.png")
    stamp_png(f"{TMP}/patched.png", "PATCHED", "WALLS: SOLID")
    ins, fc = [], []
    for i, (c, dur) in enumerate(CLIPS_T):
        ins += ["-i", os.path.join(CLIPS, c + ".mp4")]
        k = dur / clip_len(c)
        slow = f"setpts={k:.4f}*PTS,minterpolate=fps=30:mi_mode=blend," if k > 1.01 else "fps=30,"
        fc.append(f"[{i}:v]crop=iw-{2 * BORDER}:ih-{2 * BORDER}:{BORDER}:{BORDER},{slow}scale={W}:{H}:flags=lanczos,"
                  f"setsar=1,trim=duration={dur},setpts=PTS-STARTPTS[c{i}]")
    n = len(CLIPS_T)
    ins += ["-loop", "1", "-t", str(END_LEN), "-i", f"{TMP}/end.png"]
    fc.append(f"[{n}:v]fps=30,scale={W}:{H},setsar=1,trim=duration={END_LEN},fade=in:st=0:d=0.25[c{n}]")
    fc.append("".join(f"[c{i}]" for i in range(n + 1)) + f"concat=n={n + 1}:v=1:a=0[base]")
    items = [(f"{TMP}/title.png", 2.1, P["02"]), (f"{TMP}/morning.png", P["02"], P["02"] + 1.6), (f"{TMP}/scores.png", P["02"] + 0.4, P["03"] - 0.1)]
    for j, (src, s, e, text, sty) in enumerate(CAPS):
        p = f"{TMP}/cap{j}.png"; (narration_png if sty == "n" else villain_png)(text, p)
        t0 = at(src, s); nxt = at(CAPS[j + 1][0], CAPS[j + 1][1]) if j + 1 < len(CAPS) else 99
        items.append((p, t0, min(at(src, e) + 0.5, nxt - 0.03, END_AT - 0.02)))
    items.append((f"{TMP}/patched.png", PATCH_AT, PATCH_AT + 2.4))
    last, k0 = "base", n + 1
    for j, (p, t0, t1) in enumerate(items):
        ins += ["-loop", "1", "-t", f"{TOTAL}", "-i", p]
        fc.append(f"[{k0 + j}:v]format=rgba[o{j}];[{last}][o{j}]overlay=0:0:enable='between(t,{t0:.2f},{t1:.2f})'[v{j}]")
        last = f"v{j}"
    fc.append(f"[{last}]trim=duration={TOTAL},format=yuv420p[vout]")
    out = f"{TMP}/video.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fc), "-map", "[vout]", "-r", "30",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19", out], check=True)
    return out

def music():
    m = np.zeros(int((TOTAL + 1) * SR)); K, S, Hh = mk_kick(), mk_snare(), mk_hat(); beat = 0.5
    def drive(t0, t1, lvl, prog):
        t = t0
        while t < t1 - 1e-6:
            step = int(round((t - t0) / (beat / 2))); root, ch = prog[int((t - t0) / 2) % len(prog)]; nb = int(beat / 2 * SR)
            add(m, lp(saw(hz(root - 12 + (12 if step % 4 == 2 else 0)), nb), 500 + 300 * lvl) * env(nb, .003, .12), t, 0.5)
            if step % 2 == 0: add(m, K, t, 0.8 if lvl == 2 else 0.5)
            if lvl == 2 and step % 4 == 2: add(m, S, t, 0.45)
            add(m, Hh, t + beat / 4, 0.17 if lvl == 2 else 0.1)
            if step % 8 == 0: add(m, chord(ch, 2.0, 1200 + 600 * lvl), t, 0.25)
            t += beat / 2
    em = [(40, [52, 55, 59]), (36, [48, 52, 55]), (38, [50, 53, 57]), (35, [47, 50, 54])]
    drive(0.0, P["02"], 2, em)                                          # cold open
    t = P["02"]                                                         # arcade chiptune blips under the score board
    while t < P["03"]:
        nb = int(0.125 * SR); add(m, np.sign(saw(hz(76 + [0, 3, 7, 12, 7, 3][int((t - P["02"]) * 8) % 6]), nb)) * env(nb, .002, .05), t, 0.07); t += 0.125
    add(m, chord([40, 47, 52], 5.2, 700), P["02"], 0.25)
    drive(P["03"], P["04"], 1, em)                                      # chase
    add(m, chord([38, 45, 50], 6.2, 450), P["04"], 0.45); add(m, chord([62, 65, 68], 6.2, 1300, .01), P["04"], 0.1)  # creepy X-ray
    drive(P["05"], P["06"], 2, [(38, [50, 53, 57]), (41, [53, 57, 60]), (36, [48, 52, 55]), (40, [52, 55, 59])])  # fight
    for k in range(8):                                                  # install arpeggio climbing to the bonk
        add(m, chord([60 + [0, 4, 7, 12][k % 4] + 12 * (k // 4)], 0.5, 2500), P["06"] + 0.6 * k, 0.22)
    n = int(1.4 * SR); add(m, bp(noise(n), 800, 6000) * np.linspace(0, 1, n) ** 2, P["07"] - 1.4, 0.3)
    add(m, chord([48, 55, 60, 64, 67], 4.0, 1800), P["07"] + 1.0, 0.3)  # resolve after PATCHED
    add(m, chord([45, 52, 57, 60], P["08"] + 9 - P["08"], 900), P["08"], 0.3)  # uneasy (green eyes)
    add(m, K, END_AT, 1.0); add(m, chord([45, 52, 57, 64], END_LEN, 1500), END_AT, 0.35)
    return m

def sfx():
    s = np.zeros(int((TOTAL + 1) * SR))
    def boom(t, g=1.0, f=45):
        n = int(1.6 * SR); tt = np.arange(n) / SR
        add(s, (np.sin(2 * np.pi * f * tt) + 0.5 * lp(noise(n), 200)) * np.exp(-tt * 3), t, g)
    def hum(t0, dur, g):                                                # wall-phase hum with glitch flutter
        n = int(dur * SR); tt = np.arange(n) / SR
        x = np.sin(2 * np.pi * 110 * tt) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 13 * tt))) + 0.3 * bp(noise(n), 2000, 6000)
        add(s, x * np.minimum(1, tt / .2) * np.minimum(1, (dur - tt) / .3), t0, g)
    def zap(t, g=0.5):
        n = int(1.0 * SR); tt = np.arange(n) / SR
        z = np.sin(2 * np.pi * np.cumsum(1800 * np.exp(-tt * 4) + 120 + 80 * noise(n)) / SR)
        add(s, (np.sign(z) * 0.5 + 0.5 * bp(noise(n), 2000, 9000)) * np.exp(-tt * 4), t, g)
    hum(0.0, P["02"], 0.25)
    for k in range(10):                                                 # score flips
        n2 = int(.04 * SR); add(s, np.sign(saw(900 + 60 * k, n2)) * env(n2, .001, .02), P["02"] + 0.7 + k * 0.33, 0.25)
    for k in range(14):                                                 # running footsteps
        n2 = int(.12 * SR); tt = np.arange(n2) / SR; add(s, np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 40), P["03"] + k * 0.32, 0.5)
    n = int(.7 * SR); add(s, bp(noise(n), 400, 5000) * np.sin(np.linspace(0, np.pi, n)), P["03"] + 2.3, 0.35)  # Ping whoosh
    n = int(1.2 * SR); tt = np.arange(n) / SR                           # X-ray scan beep sweep
    add(s, np.sin(2 * np.pi * np.cumsum(600 + 900 * tt) / SR) * (np.sin(2 * np.pi * 8 * tt) > 0) * np.exp(-tt * 1.5), P["04"] + 0.1, 0.18)
    zap(P["05"] + 0.2); boom(P["05"] + 0.25, 0.5, 60); hum(P["05"] + 1.4, 1.2, 0.2)
    for k in range(3):                                                  # snicker-ish blips under "fair is for losers"
        n2 = int(.05 * SR); add(s, bp(noise(n2), 1500, 4000) * env(n2, .001, .03), P["05"] + 1.9 + k * 0.09, 0.3)
    n = int(.6 * SR); tt = np.arange(n) / SR                            # BONK: cartoon boing + crack
    boom(P["07"] + 0.05, 1.2, 55); add(s, np.sin(2 * np.pi * np.cumsum(500 * np.exp(-tt * 3) + 120) / SR) * np.exp(-tt * 4), P["07"] + 0.05, 0.6)
    n = int(.3 * SR); add(s, hp(noise(n), 2500) * env(n, .001, .08), P["07"] + 0.1, 0.55)
    for k in range(9):                                                  # glitch-out
        n2 = int(.06 * SR); add(s, np.sign(bp(noise(n2), 300, 4000)) * 0.4, P["08"] + 0.2 + k * 0.11, 0.25)
    n = int(3 * SR); tt = np.arange(n) / SR; add(s, np.sin(2 * np.pi * 55 * tt) * np.minimum(1, tt / .5) * np.minimum(1, (3 - tt) / .5), END_AT - 3.4, 0.2)
    for k in range(5):
        n2 = int(.05 * SR); add(s, np.sign(saw(200 + 90 * k, n2)) * 0.3, END_AT + k * 0.06, 0.25)
    return s

def audio():
    proc = ("acompressor=threshold=-22dB:ratio=3:attack=5:release=120:makeup=2,"
            "equalizer=f=140:t=q:w=1:g=3,equalizer=f=3500:t=q:w=1:g=2,aecho=0.8:0.5:45:0.12")
    raw = {"bit": load(VO_BIT, proc), "wh": load(VO_WH, "highpass=f=300,lowpass=f=3600,acrusher=bits=10:mix=0.25," + proc)}  # Wallhack through his headset
    vo = np.zeros(int((TOTAL + 1) * SR)); duck = np.zeros_like(vo)
    for src, s, e, p, tgt in LINES:
        seg = raw[src][int(s * SR): int(e * SR)].astype(np.float64)
        seg *= 10 ** (tgt / 20) / (np.sqrt((seg ** 2).mean()) + 1e-9)
        if src == "wh" and s > 6.0:  # glitch stutter on "This isn't over!"
            st = seg[: int(0.09 * SR)]; seg = np.concatenate([st, st, seg])
        f = int(0.01 * SR); seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        add(vo, seg, p); add(duck, np.ones(len(seg) + int(0.25 * SR)), p - 0.1)
    k = int(0.12 * SR); duck = np.convolve(np.clip(duck, 0, 1), np.ones(k) / k, "same")
    mix = vo + 0.55 * music() * (1 - 0.6 * duck) + 0.6 * sfx() * (1 - 0.35 * duck)
    mix = mix[: int(TOTAL * SR)]; mix /= np.abs(mix).max() / 0.9
    wav = f"{TMP}/mix.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-af", "loudnorm=I=-13:TP=-1:LRA=9", "-ar", str(SR), "-ac", "2", wav], input=mix.astype(np.float32).tobytes(), check=True)
    return wav

if __name__ == "__main__":
    a = audio(); v = video()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-i", a, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
    print("wrote", OUT)
