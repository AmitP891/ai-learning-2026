"""Bit: Bug Patrol, Ep 2 "Swarm City" (9:16 Short, ~47 s). Cold open first.

Usage: python3 build_bug_patrol_ep2.py CLIPS_DIR BIT.mp3 MOTHERBUG.mp3 OUT.mp4
CLIPS_DIR holds the 8 Runway clips (gen-4 turbo, 720x1280) in panel order: 01.mp4 … 08.mp4.
Line bounds below come from silencedetect on the ElevenLabs takes.
"""
import os, sys, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.signal import lfilter, butter

CLIPS, VO_BIT, VO_MB, OUT = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
BANG = os.path.join(HERE, "..", "fonts", "Bangers-Regular.ttf")
B = lambda s: ImageFont.truetype(BANG, s)
W, H, FPS, SR = 1080, 1920, 30, 48000
TMP = tempfile.mkdtemp(prefix="bp2_")

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


SUBTITLE = "EP 2 · SWARM CITY"
BORDER = 22  # cream comic-paper edge on the 720x1280 clips, cropped off

# (clip, seconds on screen)
CLIPS_T = [("01", 5.0), ("02", 5.0), ("03", 5.0), ("04", 6.0), ("05", 5.0), ("06", 5.0), ("07", 5.0), ("08", 7.5)]
END_LEN = 4.0
starts = np.cumsum([0] + [c[1] for c in CLIPS_T]).tolist()
END_AT = starts[-1]
TOTAL = END_AT + END_LEN

# VO lines: (source, src start, src end, place at, dB RMS)
LINES = [
    ("bit", 0.00, 2.85, 0.15, -19),    # Okay… that's a LOT of bugs.
    ("bit", 3.40, 6.22, 6.0, -20),     # That bug left a trail. Let's see where it leads.
    ("bit", 6.70, 10.32, 10.3, -21),   # Swarm City. Where old code goes to rot.
    ("mb", 0.00, 3.68, 15.4, -18),     # (purr) Every bug is my baby.
    ("bit", 10.76, 11.51, 19.4, -20),  # …Gross.
    ("bit", 11.86, 14.17, 21.2, -18),  # For every one I zap, three more hatch!
    ("bit", 14.60, 16.39, 26.4, -20),  # Bugs love a bright screen…
    ("bit", 16.72, 17.22, 33.4, -17),  # DELETE.
    ("mb", 3.99, 5.62, 36.3, -17),     # You'll pay for this!
    ("bit", 17.72, 22.83, 38.3, -20),  # Swarm deleted… Next time: someone's cheating.
]
def at(src, s):
    for so, a, b, p, _ in LINES:
        if so == src and a - 0.05 <= s <= b + 0.05: return p + (s - a)
    raise ValueError((src, s))

# captions: (source, src start, src end, text, style)
CAPS = [
    ("bit", 0.00, 2.85, "OKAY… THAT'S A LOT OF BUGS.", "n"),
    ("bit", 3.40, 4.78, "THAT BUG LEFT A TRAIL.", "n"),
    ("bit", 5.15, 6.22, "LET'S SEE WHERE IT LEADS.", "n"),
    ("bit", 6.70, 8.02, "SWARM CITY.", "n"),
    ("bit", 8.40, 10.32, "WHERE OLD CODE GOES TO ROT.", "n"),
    ("mb", 1.09, 3.68, "EVERY BUG IS MY BABY.", "v"),
    ("bit", 10.76, 11.51, "…GROSS.", "n"),
    ("bit", 11.86, 14.17, "FOR EVERY ONE I ZAP, THREE MORE HATCH!", "n"),
    ("bit", 14.60, 16.39, "BUGS LOVE A BRIGHT SCREEN…", "n"),
    ("mb", 3.99, 5.62, "YOU'LL PAY FOR THIS!", "v"),
    ("bit", 17.72, 20.34, "SWARM DELETED… BUT SOMEONE'S STILL WATCHING.", "n"),
    ("bit", 20.86, 22.83, "NEXT TIME: SOMEONE'S CHEATING.", "n"),
]

def villain_png(text, path, y=210):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = B(70); lines = wrap(text, f, 820); lh = 76
    bw = max(f.getlength(l) for l in lines) + 70; bh = lh * len(lines) + 44; x0 = (W - bw) / 2
    d.rectangle([x0 + 10, y + 10, x0 + bw + 10, y + bh + 10], fill=(0, 0, 0, 200))
    d.rectangle([x0, y, x0 + bw, y + bh], fill=(57, 255, 136, 255), outline=(0, 0, 0, 255), width=6)
    d.text((x0 + 18, y - 22), "MOTHER BUG", font=B(40), fill=(120, 40, 160), stroke_width=4, stroke_fill=(255, 255, 255))
    for i, l in enumerate(lines):
        d.text((W / 2, y + 26 + lh * i + lh / 2 - 4), l, font=f, fill=(60, 10, 90), anchor="mm")
    im.save(path)

def stamp_png(path, text, sub=None, col=(0, 230, 255)):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = Image.new("RGBA", (W, 600), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    stroked(d, (W / 2 + 10, 230), text, B(230), (0, 0, 0), 10); stroked(d, (W / 2, 220), text, B(230), col, 10)
    if sub: stroked(d, (W / 2, 400), sub, B(90), (255, 225, 77), 8)
    g = g.rotate(-5, resample=Image.BICUBIC, center=(W / 2, 300)); im.alpha_composite(g, (0, 1150)); im.save(path)

def earlier_png(path):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([60, 1470, 600, 1570], fill=(255, 225, 77), outline=(0, 0, 0), width=6)
    d.text((330, 1520), "TWO HOURS EARLIER…", font=B(66), fill=(17, 17, 17), anchor="mm"); im.save(path)

def endcard_png(path):
    fr = f"{TMP}/end_bg.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "4.8", "-i", os.path.join(CLIPS, "08.mp4"), "-frames:v", "1", fr], check=True)
    bg = Image.open(fr).convert("RGB"); bg = bg.crop((BORDER, BORDER, bg.width - BORDER, bg.height - BORDER)).resize((W, H))
    bg = Image.blend(bg.filter(ImageFilter.GaussianBlur(7)), Image.new("RGB", (W, H), (5, 8, 20)), 0.72).convert("RGBA")
    d = ImageDraw.Draw(bg)
    stroked(d, (W / 2, 420), "NEXT TIME ON", B(92), (255, 225, 77), 8)
    stroked(d, (W / 2, 530), "BIT: BUG PATROL", B(110), (255, 79, 163), 9)
    for dx, col in ((-9, (0, 230, 255)), (9, (255, 79, 163)), (0, (255, 60, 80))):
        stroked(d, (W / 2 + dx, 800), "SOMEONE'S", B(220), col, 12 if dx == 0 else 0)
        stroked(d, (W / 2 + dx, 1010), "CHEATING", B(220), col, 12 if dx == 0 else 0)
    stroked(d, (W / 2, 1180), "EPISODE 3", B(90), (255, 255, 255), 7)
    d.rounded_rectangle([170, 1300, 910, 1430], 65, fill=(255, 79, 163), outline=(0, 0, 0), width=7)
    d.text((W / 2, 1365), "FOLLOW SO YOU DON'T MISS IT", font=B(66), fill=(255, 255, 255), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
    bg.convert("RGB").save(path)

def video():
    title_png(f"{TMP}/title.png"); earlier_png(f"{TMP}/earlier.png"); endcard_png(f"{TMP}/end.png")
    stamp_png(f"{TMP}/delete.png", "DELETE", "BIN EMPTIED")
    ins, fc = [], []
    for i, (c, dur) in enumerate(CLIPS_T):
        ins += ["-i", os.path.join(CLIPS, c + ".mp4")]
        k = dur / 5.04
        slow = f"setpts={k:.4f}*PTS,minterpolate=fps=30:mi_mode=blend," if k > 1.01 else "fps=30,"
        fc.append(f"[{i}:v]crop=iw-{2 * BORDER}:ih-{2 * BORDER}:{BORDER}:{BORDER},{slow}scale={W}:{H}:flags=lanczos,"
                  f"setsar=1,trim=duration={dur},setpts=PTS-STARTPTS[c{i}]")
    n = len(CLIPS_T)
    ins += ["-loop", "1", "-t", str(END_LEN), "-i", f"{TMP}/end.png"]
    fc.append(f"[{n}:v]fps=30,scale={W}:{H},setsar=1,trim=duration={END_LEN},fade=in:st=0:d=0.25[c{n}]")
    fc.append("".join(f"[c{i}]" for i in range(n + 1)) + f"concat=n={n + 1}:v=1:a=0[base]")
    items = [(f"{TMP}/title.png", 3.05, 5.0), (f"{TMP}/earlier.png", 5.0, 6.6)]
    for j, (src, s, e, text, sty) in enumerate(CAPS):
        p = f"{TMP}/cap{j}.png"; (narration_png if sty == "n" else villain_png)(text, p)
        t0 = at(src, s); nxt = at(CAPS[j + 1][0], CAPS[j + 1][1]) if j + 1 < len(CAPS) else 99
        items.append((p, t0, min(at(src, e) + 0.5, nxt - 0.03, END_AT - 0.02)))
    items.append((f"{TMP}/delete.png", at("bit", 16.72), at("bit", 16.72) + 2.3))
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
    am = [(45, [57, 60, 64]), (41, [53, 57, 60]), (43, [55, 59, 62]), (40, [52, 55, 59])]
    drive(0.0, 5.0, 2, am)                                    # cold open: full drive
    add(m, chord([45, 52, 57], 5.2, 600), 5.0, 0.35)          # rewind: quiet pad + rain-ish air
    add(m, lp(hp(noise(int(5.2 * SR)), 2500), 9000) * 0.035, 5.0)
    add(m, chord([38, 45, 50], 10.2, 450), 10.0, 0.45)        # Swarm City + Mother Bug: creepy drone
    add(m, chord([62, 65, 68], 10.2, 1300, .01), 10.0, 0.1)
    drive(21.0, 31.0, 2, [(38, [50, 53, 57]), (41, [53, 57, 60]), (36, [48, 52, 55]), (40, [52, 55, 59])])  # the fight
    n = int(1.6 * SR); add(m, bp(noise(n), 800, 6000) * np.linspace(0, 1, n) ** 2, 31.6, 0.35)          # riser to the slam
    add(m, chord([48, 55, 60, 64, 67], 4.2, 1800), END_AT - 7.0, 0.32)  # resolve
    add(m, chord([45, 52, 57, 60], 3.5, 900), END_AT - 3.2, 0.3)       # uneasy turn (eyes)
    add(m, K, END_AT, 1.0); add(m, chord([45, 52, 57, 64], END_LEN, 1500), END_AT, 0.35)
    return m

def sfx():
    s = np.zeros(int((TOTAL + 1) * SR))
    def boom(t, g=1.0, f=45):
        n = int(1.6 * SR); tt = np.arange(n) / SR
        add(s, (np.sin(2 * np.pi * f * tt) + 0.5 * lp(noise(n), 200)) * np.exp(-tt * 3), t, g)
    def buzz(t0, dur, g):
        n = int(dur * SR); tt = np.arange(n) / SR
        bz = np.sign(np.sin(2 * np.pi * (210 + 25 * np.sin(2 * np.pi * 3 * tt)) * tt)) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * tt))
        add(s, lp(bz, 2500) * np.minimum(1, tt / .3) * np.minimum(1, (dur - tt) / .4), t0, g)
    def zap(t, g=0.5):
        n = int(1.0 * SR); tt = np.arange(n) / SR
        z = np.sin(2 * np.pi * np.cumsum(1800 * np.exp(-tt * 4) + 120 + 80 * noise(n)) / SR)
        add(s, (np.sign(z) * 0.5 + 0.5 * bp(noise(n), 2000, 9000)) * np.exp(-tt * 4), t, g)
    n = int(5 * SR); add(s, bp(noise(n), 300, 3000) * 0.6, 0.0, 0.25); buzz(0.0, 5.0, 0.12)   # tornado roar
    add(s, lp(hp(noise(int(5 * SR)), 2500), 9000) * 0.05, 5.0)                                  # night air
    buzz(10.0, 5.0, 0.05)                                                                        # distant swarm
    for k in range(5):                                                                           # eggs hatch
        n2 = int(.08 * SR); add(s, bp(noise(n2), 900, 4000) * env(n2, .001, .03), 16.3 + k * 0.55, 0.6)
    zap(21.3); zap(23.6, 0.4); buzz(21.0, 5.0, 0.1); boom(21.3, 0.8, 50)
    n = int(1.6 * SR); tt = np.arange(n) / SR                                                     # power-up whine
    add(s, np.sin(2 * np.pi * np.cumsum(300 + 1400 * tt / 1.6) / SR) * np.minimum(1, tt / .2) * 0.4, 26.1)
    buzz(31.0, 2.5, 0.14); boom(33.35, 1.2, 40)                                                  # swarm in, lid slams
    n = int(.25 * SR); add(s, hp(noise(n), 1500) * env(n, .001, .06), 33.35, 0.7)
    n = int(2.0 * SR); tt = np.arange(n) / SR                                                     # escape screech
    add(s, np.sin(2 * np.pi * np.cumsum(1400 - 500 * tt) / SR) * np.exp(-tt * 2) * 0.25, 36.2)
    n = int(3 * SR); tt = np.arange(n) / SR; add(s, (np.sin(2 * np.pi * 55 * tt)) * np.minimum(1, tt / .5) * np.minimum(1, (3 - tt) / .5), END_AT - 3.4, 0.2)
    for k in range(5):
        n2 = int(.05 * SR); add(s, np.sign(saw(200 + 90 * k, n2)) * 0.3, END_AT + k * 0.06, 0.25)
    return s

def audio():
    proc = ("acompressor=threshold=-22dB:ratio=3:attack=5:release=120:makeup=2,"
            "equalizer=f=140:t=q:w=1:g=3,equalizer=f=3500:t=q:w=1:g=2,aecho=0.8:0.5:45:0.12")
    raw = {"bit": load(VO_BIT, proc), "mb": load(VO_MB, proc + ",aecho=0.8:0.4:90:0.15")}
    vo = np.zeros(int((TOTAL + 1) * SR)); duck = np.zeros_like(vo)
    for src, s, e, p, tgt in LINES:
        seg = raw[src][int(s * SR): int(e * SR)].astype(np.float64)
        seg *= 10 ** (tgt / 20) / (np.sqrt((seg ** 2).mean()) + 1e-9)
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
