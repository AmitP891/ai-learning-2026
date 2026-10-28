"""Long-form: Claude Code made a boss fight for my robot (3/10 -> 8/10). 1920x1080, 30 fps."""
import re, io, sys, json, math, wave, subprocess, numpy as np, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, "/home/claude/ai-learning-2026/brand/adventures")
from prof import professor

W, H = 1920, 1080; FPS = 30; SR = 44100; GAP = 0.35
OUTD = "/home/claude/ai-learning-2026/brand/motion/bit-level-1/out"
T16 = f"{OUTD}/teaser_16x9.mp4"; T9V1 = "/tmp/claude-0/-home-claude/21daa8ca-6e20-5e95-ae03-055ac8e41af7/scratchpad/lvl1/teaser.mp4"
ATT = "/mnt/user-data/attachments/21daa8ca-6e20-5e95-ae03-055ac8e41af7"
STYLE = [f"{ATT}/c949e770-image.png", f"{ATT}/489483ec-image.png", f"{ATT}/a1710026-image.png"]

# ---------------- audio
def load(fn, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", fn, "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768
lines = [load(f"l{i:02d}.wav") for i in range(1, 22)]
T = []; t = 0.0
for a in lines: T.append(t); t += len(a) / SR + GAP
E = [T[i] + len(lines[i]) / SR for i in range(21)]
DUR = E[-1] + 2.0; N = int(DUR * FPS); hop = SR // FPS
voice = np.zeros(int(DUR * SR) + SR, np.float32)
for s, a in zip(T, lines): i = int(s * SR); voice[i:i + len(a)] += a
rms = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2)) for i in range(N)])
env = np.clip((rms - 0.01) / (np.percentile(rms[rms > 0.01], 90) - 0.01), 0, 1); env = np.convolve(env, [.25, .5, .25], "same")
tease = load(T16)
bed = np.zeros_like(voice)
def put_bed(t0, src0, dur, g):
    a = tease[int(src0 * SR):int((src0 + dur) * SR)].copy(); n = len(a)
    f = np.ones(n); k = int(0.3 * SR); f[:k] = np.linspace(0, 1, k); f[-k:] = np.linspace(1, 0, k)
    i = int(t0 * SR); bed[i:i + n] += a * f * g
put_bed(0, 0, min(20, T[1]), 0.30)
put_bed(T[19], 17.0, 3.0, 0.30)
tt = np.arange(len(voice)) / SR; sfx = np.zeros_like(voice)
def tone(t0, fr, d=.12, dec=25, amp=.06):
    i = int(t0 * SR); n = int(d * SR); s = np.sin(2 * np.pi * fr * tt[:n]) * np.exp(-tt[:n] * dec) * amp; sfx[i:i + n] += s[:len(sfx) - i]

# ---------------- look
CY = (0, 240, 255); PK = (240, 53, 158); GR = (57, 255, 136); RD = (255, 70, 90); WH = (255, 255, 255); GY = (160, 165, 185); BG = (13, 13, 20); YL = (255, 214, 0); PU = (120, 56, 170); PANEL = (20, 22, 34)
FD = lambda s, w="DejaVuSans-Bold": ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{w}.ttf", s)
FI = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", s)
MONO = FD(30, "DejaVuSansMono"); MONOB = lambda s: FD(s, "DejaVuSansMono-Bold")
def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def fade(c, k): return tuple(int(BG[i] + (c[i] - BG[i]) * k) for i in range(3))
def txt(d, xy, s, font, c, t, t0, anchor="la", dy=20):
    if t < t0: return
    k = ease((t - t0) / .35); d.text((xy[0], xy[1] + dy * (1 - k)), s, font=font, fill=fade(c, k), anchor=anchor)
def card(d, box, c, t, t0, fill=PANEL, w=4, r=22):
    if t < t0: return 0
    k = ease((t - t0) / .35); y = int(16 * (1 - k))
    d.rounded_rectangle((box[0], box[1] + y, box[2], box[3] + y), radius=r, fill=fade(fill, k) if fill else None, outline=fade(c, k), width=w); return k
grid = Image.new("RGBA", (W, H), BG + (255,)); gd = ImageDraw.Draw(grid)
for y in range(0, H, 60): gd.line((0, y, W, y), fill=(20, 21, 32))
for x in range(0, W, 60): gd.line((x, 0, x, H), fill=(17, 18, 28))

# ---------------- Bit
SVG = open("/home/claude/ai-learning-2026/brand/bit/bit.svg").read()
svg = re.sub(r'<g id="eyes">.*?</g>', '', SVG, flags=re.S); svg = re.sub(r'<path id="mouth"[^>]*/>', '', svg)
BASE = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=600, output_height=700))).convert("RGBA")
def bitimg(f, mood="norm", talk=True):
    r = BASE.copy(); d = ImageDraw.Draw(r); a = env[min(f, N - 1)] if talk else 0
    for ex in (244, 356):
        cx, cy = ex, 199
        if mood == "happy": d.arc((cx - 24, cy - 14, cx + 24, cy + 30), 200, 340, fill=CY, width=10)
        elif mood == "shock": d.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), outline=CY, width=9)
        elif mood == "blink" or (mood == "norm" and (f % 95) in (0, 1, 2)): d.rounded_rectangle((cx - 22, cy - 4, cx + 22, cy + 4), radius=3, fill=CY)
        elif mood == "det": d.polygon([(cx - 22, cy - 12 + (8 if ex == 244 else 0)), (cx + 22, cy - 12 + (0 if ex == 244 else 8)), (cx + 22, cy + 26), (cx - 22, cy + 26)], fill=CY)
        elif mood == "hit":
            d.line((cx - 20, cy - 20, cx + 20, cy + 20), fill=CY, width=10); d.line((cx - 20, cy + 20, cx + 20, cy - 20), fill=CY, width=10)
        else: d.rounded_rectangle((cx - 22, cy - 29, cx + 22, cy + 29), radius=12, fill=CY)
    mx, my = 300, 262
    if a > 0.08:
        h = 8 + 38 * a; w = 56; d.rounded_rectangle((mx - w / 2, my - h / 2, mx + w / 2, my + h / 2), radius=int(min(h, w) / 2), fill=CY)
    else: d.arc((mx - 40, my - 40, mx + 40, my + 12), 25, 155, fill=CY, width=9)
    return r
def sc(im, s): return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)

src = open("/home/claude/ai-learning-2026/brand/video-template/build_mcp_video.py").read(); ns = {"Image": Image, "ImageDraw": ImageDraw, "ImageFont": ImageFont}
exec(src[src.index("def yt_icon"):src.index("YT=yt_icon")], ns); exec(src[src.index("def tt_icon"):src.index("TT=tt_icon")], ns)
ICONS = [ns["tt_icon"](84), ns["yt_icon"](84), ns["ig_icon"](84)]

# ---------------- video sources
PW, PH = 1400, 788; PX, PY = 60, 200
class Clip:
    """Sequential frame reader: source [t0,t1] mapped onto n output frames (speed-up/slow-down), cropped and scaled."""
    def __init__(self, fn, t0, t1, n, crop=None, size=(PW, PH)):
        self.size = size; self.n = n; self.last = None; self.i = 0
        vf = []
        if crop: vf.append(f"crop={crop[2]-crop[0]}:{crop[3]-crop[1]}:{crop[0]}:{crop[1]}")
        vf += [f"setpts=(PTS-STARTPTS)*{n / FPS / max(0.01, t1 - t0):.6f}", f"fps={FPS}", f"scale={size[0]}:{size[1]}:flags=lanczos"]
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-threads", "2", "-ss", str(t0), "-t", str(t1 - t0), "-i", fn, "-vf", ",".join(vf), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    def get(self):
        b = self.p.stdout.read(self.size[0] * self.size[1] * 3)
        if len(b) == self.size[0] * self.size[1] * 3: self.last = Image.frombytes("RGB", self.size, b)
        return self.last
def still(fn, t, crop, size=(PW, PH)):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", fn, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    return Image.open(io.BytesIO(raw)).convert("RGB").crop(crop).resize(size, Image.LANCZOS)
clips = {}
CLIP_LINE = {"t1": 0, "g1a": 8, "v1": 13, "t2": 15, "t3": 19}
def clip(key, *a, **k):
    if key not in clips: clips[key] = Clip(*a, **k)
    return clips[key].get()
def nfr(i, a=0.0, b=1.0): return max(2, int((E[i] - T[i] + GAP) * (b - a) * FPS) + 2)

S_G1END = still("g1.mov", 500, (100, 700, 1650, 1572))
S_G3 = still("g3.mov", 138, (90, 520, 1690, 1420))
S_G2 = still("g2.mov", 399, (100, 100, 1700, 1540), size=(PW, int(PW * 1440 / 1600)))
S_R1 = still("r1.mov", 17, (60, 560, 1660, 1460))
S_FIN = still("fin.mov", 258, (100, 700, 1740, 1622))
STYLES = [Image.open(p).convert("RGB") for p in STYLE]

def panel(im, img, x=PX, y=PY, k=1.0, border=CY):
    w, h = img.size; m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=18, fill=int(255 * k))
    im.paste(img, (x, y), m); d = ImageDraw.Draw(im); d.rounded_rectangle((x - 3, y - 3, x + w + 2, y + h + 2), radius=20, outline=fade(border, k), width=3)
    return d
def headline(d, t, t0, a, b=None, ca=WH, cb=CY):
    txt(d, (PX, 92), a, FI(64), ca, t, t0)
    if b: txt(d, (PX + d.textlength(a + "  ", font=FI(64)), 92), b, FI(64), cb, t, t0 + .2)

LABELS = ["// the result", "// first attempt", "// hi, I'm Bit", "// the trend", "// the theory", "// the brief", "// character bible", "// gates",
          "// gate 1", "// gate 1 review", "// gate 2", "// gate 3", "// critique loop", "// round 1", "// my notes", "// round 2", "// round 2",
          "// final check", "// lessons", "// level 2?", "// your turn"]
R1 = [("Hook", 3), ("Readability", 6), ("Beat sync", 8), ("On-model", 7), ("Game feel", 6), ("Ending", 6)]
R2 = [8, 8, 9, 8, 8, 8]
BRIEF = ["Film in one line", "Deliverables", "References", "Tools and keys", "Character bible", "Look", "Beat sheet", "Text on screen", "Sound", "Workflow gates", "Critique loop", "Gotchas"]

# sfx cues
for i in (1, 13): tone(T[i] + .1, 220, .3, 8, .08)
for j in range(12): tone(T[5] + 1.2 + j * 0.75, 900 + j * 30, .05, 40, .04)
for j in range(4): tone(T[7] + .3 + j * 1.8, 660 + j * 110, .15, 15, .06)
for j in range(6): tone(T[13] + .3 + j * .9, 700 if j else 330, .12, 20, .06)
for j in range(6): tone(T[16] + .5 + j * .25, 880 + j * 80, .08, 30, .05)
tone(T[16] + 2.2, 1320, .4, 6, .08)
mix = np.clip((voice + bed * 0.9 + sfx) * 0.85, -1, 1)[:int(DUR * SR)]
with wave.open("audio.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())

PREVIEW = [float(x) for x in sys.argv[1:]]
OUT = "claude-boss-fight-longform.mp4"
ff = None if PREVIEW else subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "audio.wav",
                                            "-c:v", "libx264", "-threads", "3", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], stdin=subprocess.PIPE)
frames = [int(p * FPS) for p in PREVIEW] if PREVIEW else range(N)

def line_at(t):
    return max(i for i in range(21) if t >= T[i] - GAP / 2 or i == 0)

for f in frames:
    t = f / FPS; li = line_at(t); lt = t - T[li]; L = E[li] - T[li]; p = lt / L
    im = grid.copy(); d = ImageDraw.Draw(im)
    show_bit = True; mood = "norm"; bit_s = 0.55; bit_xy = None
    if li == 0:
        fr = clip("t1", T16, 0, min(20, T[1]), int(min(20, T[1]) * FPS) + 2, size=(W, H))
        im.paste(fr, (0, 0)); d = ImageDraw.Draw(im); show_bit = False
        if t > 1.0:
            k = ease((t - 1.0) / .4); d.rounded_rectangle((40, 980, 860, 1050), radius=16, fill=(0, 0, 0)); d.text((64, 992), "100% code · no game engine · no editor", font=FD(34), fill=fade(YL, k))
    elif li == 1:
        txt(d, (W / 2 - 120, 230), "FIRST ATTEMPT", FI(80), WH, t, T[1], anchor="ma")
        if t > T[1] + .5:
            k = ease((t - T[1] - .5) / .25); s = 1 + 0.4 * (1 - k)
            tl = Image.new("RGBA", (W, H)); td = ImageDraw.Draw(tl); td.text((W / 2 - 120, 560), "3 / 10", font=FI(int(260 * s)), fill=RD + (int(255 * k),), anchor="mm")
            im.alpha_composite(tl.filter(ImageFilter.GaussianBlur(20))); im.alpha_composite(tl); d = ImageDraw.Draw(im)
        txt(d, (W / 2 - 120, 760), "...then it got to 8.", FD(56), GR, t, T[1] + 2.0, anchor="ma"); mood = "shock" if p < .6 else "norm"
    elif li == 2:
        bit_s = 1.0; bit_xy = (150, 330)
        if card(d, (820, 300, 1840, 760), PK, t, T[2] + .3):
            txt(d, (870, 340), "AMIT", FI(110), WH, t, T[2] + .3)
            txt(d, (870, 480), "Systems engineer", FD(48), CY, t, T[2] + 1.0)
            txt(d, (870, 545), "learning AI in public", FD(48), CY, t, T[2] + 1.6)
            txt(d, (870, 650), "@vibewithamitai", FD(40), PK, t, T[2] + 2.2)
        txt(d, (870, 820), "Everything here is made with code.", FD(44), YL, t, T[2] + L * .7)
    elif li == 3:
        if p < .55:
            headline(d, t, T[3], "Claude motion graphics", "is exploding")
            stats = [("claude video editing", "~1.46M", "searches / month"), ("claude motion", "+7,673%", "in a month"), ("claude motion graphics", "~1M", "searches / month")]
            for j, (a, b, c) in enumerate(stats):
                x = 60 + j * 470; t0 = T[3] + .4 + j * .6
                if card(d, (x, 300, x + 440, 700), CY, t, t0):
                    txt(d, (x + 30, 335), a, FD(30), GY, t, t0); txt(d, (x + 30, 420), b, FI(96), CY if j != 1 else GR, t, t0); txt(d, (x + 30, 560), c, FD(34), WH, t, t0)
            txt(d, (60, 760), "source: vidIQ keyword research, Oct 2026", FD(26), GY, t, T[3] + 2)
        else:
            t0 = T[3] + L * .55; headline(d, t, t0, "One prompt", "→ ?", WH, RD)
            if t > t0 + .2:
                k = ease((t - t0 - .2) / .4); g = Image.new("RGB", (900, 506))
                arr = np.zeros((506, 900, 3), np.uint8); xx = np.linspace(0, 1, 900)[None, :, None]
                arr[:] = (np.array([90, 60, 200]) * (1 - xx) + np.array([230, 90, 160]) * xx).astype(np.uint8); g = Image.fromarray(arr)
                gd2 = ImageDraw.Draw(g); gd2.text((450, 253), "My Product", font=FD(60), fill=WH, anchor="mm")
                panel(im, g, 100, 290, k, GY); d = ImageDraw.Draw(im)
            txt(d, (1060, 380), "gradient ✓", FD(44), GY, t, t0 + 1.0); txt(d, (1060, 450), "centred text ✓", FD(44), GY, t, t0 + 1.6); txt(d, (1060, 520), "anything else ✗", FD(44), RD, t, t0 + 2.4)
    elif li == 4:
        headline(d, t, T[4], "The real recipe")
        k = ease((t - T[4] - .4) / 1.2); x0, x1 = 60, 1460
        d.rounded_rectangle((x0, 360, x1, 520), radius=20, outline=GY, width=3)
        split = x0 + (x1 - x0) * 0.10
        if k > 0:
            d.rounded_rectangle((x0 + 6, 366, x0 + 6 + (split - x0 - 6) * min(1, k * 3), 514), radius=16, fill=PK)
            if k > .33: d.rounded_rectangle((split + 4, 366, split + 4 + (x1 - 6 - split - 4) * ((k - .33) / .67), 514), radius=16, fill=CY)
        txt(d, (x0, 560), "10%  prompt", FI(64), PK, t, T[4] + .8); txt(d, (x1, 560), "90%  setup", FI(64), CY, t, T[4] + 1.6, anchor="ra")
        txt(d, (60, 760), "So I tested it on my own robot.", FD(48), YL, t, T[4] + L * .72)
    elif li == 5:
        headline(d, t, T[5], "The director's brief", "1 page · 12 sections")
        for j, s in enumerate(BRIEF):
            col, row = j // 6, j % 6; x = 60 + col * 720; y = 250 + row * 118; t0 = T[5] + 1.0 + j * .75
            if card(d, (x, y, x + 680, y + 100), PK if s in ("Character bible", "Beat sheet", "Workflow gates", "Critique loop") else CY, t, t0, w=3):
                txt(d, (x + 26, y + 26), f"{j + 1:>2}", MONOB(40), YL, t, t0); txt(d, (x + 110, y + 26), s, FD(42), WH, t, t0)
        show_bit = True
    elif li == 6:
        headline(d, t, T[6], "Character bible")
        moods = [("idle", "norm2"), ("blink", "blink"), ("determined", "det"), ("hit", "hit"), ("happy", "happy")]
        for j, (nm, md) in enumerate(moods):
            t0 = T[6] + .5 + j * .5; x = 60 + j * 230
            if card(d, (x, 230, x + 210, 520), CY, t, t0, w=3):
                b = sc(bitimg(f, "norm" if md == "norm2" else md, talk=False), 0.3); im.alpha_composite(b, (x + 15, 250)); d = ImageDraw.Draw(im)
                txt(d, (x + 105, 470), nm, FD(28), WH, t, t0, anchor="ma")
        for j, (c, nm) in enumerate([((240, 53, 158), "#F0359E"), ((0, 240, 255), "#00F0FF"), ((23, 26, 43), "#171A2B"), ((58, 63, 92), "#3A3F5C")]):
            t0 = T[6] + 3.2 + j * .3
            if t > t0: x = 60 + j * 290; d.rounded_rectangle((x, 570, x + 60, 630), radius=10, fill=c, outline=WH, width=2); txt(d, (x + 76, 584), nm, MONOB(30), WH, t, t0)
        if t > T[6] + L * .45:
            k = ease((t - T[6] - L * .45) / .5); pr = sc(professor(0, t, "smug", 1.0), 0.42); a = pr.getchannel("A").point(lambda v: int(v * k)); pr.putalpha(a)
            im.alpha_composite(pr, (1230, 230)); d = ImageDraw.Draw(im)
        txt(d, (60, 700), "Same character in every shot.", FD(48), YL, t, T[6] + L * .6)
    elif li == 7:
        headline(d, t, T[7], "Gates", "= design reviews")
        names = ["Style frames", "Beat grid", "First render", "Critique loop"]
        for j, nm in enumerate(names):
            x = 60 + j * 360; t0 = T[7] + .3 + j * 1.8
            if card(d, (x, 300, x + 320, 560), CY, t, t0):
                txt(d, (x + 160, 330), f"GATE {j + 1}", FI(54), YL, t, t0, anchor="ma"); txt(d, (x + 160, 420), nm, FD(36), WH, t, t0, anchor="ma")
                if t > t0 + .6: d.rounded_rectangle((x + 40, 480, x + 280, 530), radius=10, fill=RD); d.text((x + 160, 505), "■ STOP & SHOW", font=FD(26), fill=WH, anchor="mm")
            if j < 3 and t > t0 + .3: d.text((x + 340, 430), "›", font=FI(70), fill=GY, anchor="mm")
        txt(d, (60, 700), "Don't wait until the end to find out it's wrong.", FD(46), YL, t, T[7] + L * .65)
    elif li == 8:
        if p < .62:
            fr = clip("g1a", "g1.mov", 30, 110, nfr(8, 0, .62), crop=(80, 60, 2240, 1275)); panel(im, fr); d = ImageDraw.Draw(im)
            d.rounded_rectangle((PX + PW - 300, PY + 20, PX + PW - 20, PY + 90), radius=14, fill=(0, 0, 0)); d.text((PX + PW - 160, PY + 55), "▶▶  ×12", font=MONOB(36), fill=YL, anchor="mm")
            headline(d, t, T[8], "It set up my Mac", "by itself")
        else:
            panel(im, S_G1END); d = ImageDraw.Draw(im); headline(d, t, T[8] + L * .62, "Gate 1:", "3 style frames", WH, YL)
    elif li == 9:
        headline(d, t, T[9], "Gate 1 review:", "4 problems", WH, RD)
        ims = [sc(s, 760 / 1920) for s in STYLES]
        for j, s in enumerate(ims):
            x = 60 + j * 470; t0 = T[9] + .2 + j * .25
            if t > t0: panel(im, s.convert("RGB"), x, 230, ease((t - t0) / .35), GY); d = ImageDraw.Draw(im)
        sc_ = 760 / 1920; marks = [(1, 540, 1720, "1"), (1, 440, 950, "2"), (2, 540, 830, "3"), (0, 540, 260, "4")]
        for j, (fi, mx, my, lab) in enumerate(marks):
            t0 = T[9] + L * (.28 + j * .17)
            if t > t0:
                k = ease((t - t0) / .3); cx = 60 + fi * 470 + mx * sc_; cy = 230 + my * sc_; r = 70 + 30 * (1 - k)
                d.ellipse((cx - r, cy - r * .6, cx + r, cy + r * .6), outline=RD, width=7); d.ellipse((cx + r - 30, cy - r * .6 - 30, cx + r + 20, cy - r * .6 + 20), fill=RD); d.text((cx + r - 5, cy - r * .6 - 5), lab, font=FD(30), fill=WH, anchor="mm")
        show_bit = False; bit_xy = None
    elif li == 10:
        oy = int((S_G2.height - PH) * ease(min(1, max(0, (p - .1) / .8)))); panel(im, S_G2.crop((0, oy, PW, oy + PH))); d = ImageDraw.Draw(im)
        headline(d, t, T[10], "Gate 2:", "the beat grid", WH, YL)
        beat = int((lt) * 2) % 40
        for j in range(40):
            x = PX + j * 35; d.rectangle((x, 1010, x + 28, 1040), fill=PK if j == beat else (40, 42, 60))
        d.text((PX + 1410, 1025), "120 BPM", font=MONOB(28), fill=PK, anchor="lm")
    elif li == 11:
        z = 1 + 0.05 * p; s = sc(S_G3, z).crop((0, 0, PW, PH)); panel(im, s); d = ImageDraw.Draw(im)
        headline(d, t, T[11], "Gate 3:", "first render", WH, YL)
        if card(d, (PX + 820, PY + 600, PX + 1380, PY + 760), GR, t, T[11] + L * .45, fill=(10, 30, 20)):
            txt(d, (PX + 1100, PY + 620), "600 frames", FI(52), GR, t, T[11] + L * .45, anchor="ma"); txt(d, (PX + 1100, PY + 690), "exactly 20.000 s", FD(36), WH, t, T[11] + L * .45, anchor="ma")
    elif li == 12:
        headline(d, t, T[12], "The critique loop", "score → fix → repeat")
        for j, (nm, _) in enumerate(R1):
            col, row = j % 2, j // 2; x = 60 + col * 720; y = 260 + row * 170; t0 = T[12] + L * .35 + j * .6
            if card(d, (x, y, x + 680, y + 140), CY, t, t0):
                txt(d, (x + 30, y + 40), f"{j + 1}", FI(64), YL, t, t0); txt(d, (x + 120, y + 48), nm, FD(48), WH, t, t0); txt(d, (x + 650, y + 52), "/10", FD(40), GY, t, t0, anchor="ra")
        txt(d, (60, 800), "1 frame per beat · 40 frames scored", FD(36), GY, t, T[12] + 1)
    elif li == 13:
        headline(d, t, T[13], "Round 1")
        order = [2, 1, 3, 4, 5, 0]
        for n_, j in enumerate(order):
            nm, s_ = R1[j]; y = 220 + n_ * 112; t0 = T[13] + .3 + n_ * .9
            if card(d, (60, y, 900, y + 96), RD if s_ < 5 else GY, t, t0, w=3):
                txt(d, (90, y + 22), nm, FD(44), WH, t, t0); txt(d, (870, y + 14), str(s_), FI(64), RD if s_ < 5 else (YL if s_ < 8 else GR), t, t0, anchor="ra")
        if t > T[13] + L * .6:
            fr = clip("v1", T9V1, 0, 2.0, 60, size=(360, 640)); f2 = fr if fr else Image.new("RGB", (360, 640))
            panel(im, f2, 1000, 230, ease((t - T[13] - L * .6) / .3), RD); d = ImageDraw.Draw(im)
            txt(d, (1180, 900), "first 2 s: black", FD(34), RD, t, T[13] + L * .6, anchor="ma")
        mood = "shock" if p > .4 else "norm"
    elif li == 14:
        panel(im, S_R1); d = ImageDraw.Draw(im); headline(d, t, T[14], "My notes", "as a viewer")
        for j, (a, b) in enumerate([(.3, (PX + 30, PY + 260, PX + 1380, PY + 420)), (.55, (PX + 30, PY + 470, PX + 1380, PY + 560)), (.78, (PX + 30, PY + 420, PX + 1380, PY + 470))]):
            if p > a: d.rounded_rectangle(b, radius=10, outline=YL, width=5)
    elif li == 15:
        fr = clip("t2", T16, 10.0, 17.2, nfr(15)); panel(im, fr); d = ImageDraw.Draw(im)
        d.rounded_rectangle((PX + PW - 250, PY + PH - 70, PX + PW - 20, PY + PH - 16), radius=12, fill=(0, 0, 0)); d.text((PX + PW - 135, PY + PH - 43), "SLOW-MO", font=MONOB(30), fill=YL, anchor="mm")
        headline(d, t, T[15], "Round 2:", "one word per beat", WH, YL)
        txt(d, (PX, 1010), "FAST → WITHIN 200 ms    TBD → 10 MB/s", MONOB(34), GR, t, T[15] + L * .6)
    elif li == 16:
        headline(d, t, T[16], "Round 1 → Round 2")
        for j, (nm, s1) in enumerate(R1):
            y = 230 + j * 108; t0 = T[16] + .2 + j * .25
            if card(d, (60, y, 1240, y + 92), GR, t, t0, w=3):
                txt(d, (90, y + 20), nm, FD(44), WH, t, t0); txt(d, (820, y + 12), str(s1), FI(60), RD if s1 < 5 else YL, t, t0, anchor="ra")
                txt(d, (920, y + 12), "→", FI(60), GY, t, t0 + .2, anchor="ma")
                k = ease((t - T[16] - .5 - j * .25) / .5); v = round(s1 + (R2[j] - s1) * k)
                txt(d, (1200, y + 12), str(v), FI(60), GR if v >= 8 else YL, t, t0 + .3, anchor="ra")
        if card(d, (60, 900, 1240, 990), GR, t, T[16] + L * .6, fill=(10, 30, 20)):
            txt(d, (650, 918), "All 8+ · stopped after 2 of 4 rounds", FD(42), GR, t, T[16] + L * .6, anchor="ma")
        mood = "happy" if p > .3 else "norm"
    elif li == 17:
        panel(im, S_FIN); d = ImageDraw.Draw(im); headline(d, t, T[17], "It caught", "its own bug", WH, RD)
        if p > .25:
            k = ease((t - T[17] - L * .25) / .3); d.rounded_rectangle((PX + 760, PY + 520, PX + 1380, PY + 760), radius=20, fill=(30, 8, 14), outline=fade(RD, k), width=5)
            d.text((PX + 1070, PY + 580), "sync error", font=FD(40), fill=fade(WH, k), anchor="mm"); d.text((PX + 1070, PY + 680), "3.1 → 11.8 ms", font=FI(72), fill=fade(RD, k), anchor="mm")
        if p > .62:
            k = ease((t - T[17] - L * .62) / .3); d.rounded_rectangle((PX + 760, PY + 780, PX + 1380, PY + 860), radius=16, fill=(10, 30, 20), outline=fade(GR, k), width=4)
            d.text((PX + 1070, PY + 820), "FIXED ✓  back to 3.1 ms", font=FD(36), fill=fade(GR, k), anchor="mm")
    elif li == 18:
        headline(d, t, T[18], "What I learned")
        ls = [("1", "Structure beats a long prompt"), ("2", "A character bible keeps it on-model"), ("3", "Gates + scores make it measurable")]
        for j, (n_, s_) in enumerate(ls):
            y = 260 + j * 200; t0 = T[18] + L * (.12 + j * .28)
            if card(d, (60, y, 1460, y + 170), [CY, PK, GR][j], t, t0):
                txt(d, (110, y + 40), n_, FI(90), [CY, PK, GR][j], t, t0); txt(d, (230, y + 55), s_, FD(54), WH, t, t0)
    elif li == 19:
        fr = clip("t3", T16, 17.0, 20.0, int(3 * FPS) + 2); panel(im, fr); d = ImageDraw.Draw(im)
        headline(d, t, T[19], "This was only", "Level 1", WH, YL)
        if p > .55:
            k = ease((t - T[19] - L * .55) / .35)
            ov = Image.new("RGBA", (PW, PH), (0, 0, 0, int(170 * k))); im.alpha_composite(ov, (PX, PY)); d = ImageDraw.Draw(im)
            d.rounded_rectangle((PX + 360, PY + 280, PX + 1040, PY + 500), radius=20, fill=(0, 0, 0), outline=fade(YL, k), width=6)
            d.text((PX + 700, PY + 345), "LEVEL 2 BOSS", font=FI(64), fill=fade(WH, k), anchor="mm"); d.text((PX + 700, PY + 440), "= ?  comment ↓", font=FI(56), fill=fade(YL, k), anchor="mm")
        mood = "happy"
    else:
        t0 = T[20]
        txt(d, (W / 2 - 160, 140), "The code is free", FI(84), GR, t, t0, anchor="ma")
        if card(d, (180, 270, 1440, 470), GR, t, t0 + .2, fill=(12, 26, 20), w=5):
            txt(d, (810, 300), "★  GitHub", FI(60), WH, t, t0 + .2, anchor="ma")
            txt(d, (810, 390), "AmitP891/ai-learning-2026  ·  brand/motion", FD(40, "DejaVuSansMono-Bold"), GR, t, t0 + .2, anchor="ma")
        tS = t0 + L * .4
        if t >= tS:
            k = ease((t - tS) / .35); pulse = 1 + 0.04 * math.sin((t - tS) * 8); bw, bh = int(520 * pulse), int(120 * pulse)
            d.rounded_rectangle((810 - bw / 2, 600 - bh / 2, 810 + bw / 2, 600 + bh / 2), radius=60, fill=fade((230, 30, 40), k)); d.text((810, 600), "SUBSCRIBE", font=FI(64), fill=fade(WH, k), anchor="mm")
            for j, ic in enumerate(ICONS):
                a = ic.copy(); a.putalpha(a.getchannel("A").point(lambda v: int(v * k))); im.alpha_composite(a, (520 + j * 100, 700))
            d = ImageDraw.Draw(im); d.text((830, 742), "@vibewithamitai", font=FD(44), fill=fade(PK, k), anchor="lm")
        txt(d, (810, 860), "Like · share with an engineer friend · subscribe", FD(38), GY, t, t0 + L * .55, anchor="ma")
        txt(d, (810, 940), "Build it. Test it. Ship it.", FD(58), CY, t, t0 + L * .82, anchor="ma")
        mood = "happy" if p > .8 else "norm"
    if li != 0:
        d.text((60, 30), LABELS[li], font=MONO, fill=CY)
        d.text((W - 60, 30), f"{int(t // 60)}:{int(t % 60):02d}", font=MONO, fill=(60, 64, 90), anchor="ra")
    if show_bit:
        r = bitimg(f, mood)
        r = sc(r, bit_s)
        bob = int(8 * math.sin(t * 2 * math.pi * .6))
        x, y = bit_xy if bit_xy else (W - r.width - 40, H - r.height + 10 + bob)
        im.alpha_composite(r, (x, y + (bob if bit_xy else 0)))
    if PREVIEW: im.convert("RGB").save(f"pv_{t:.1f}.png")
    else: ff.stdin.write(im.convert("RGB").tobytes())
    for k_, ln in list(CLIP_LINE.items()):
        if k_ in clips and li != ln:
            clips[k_].p.kill(); clips[k_].p.wait(); del clips[k_]
if ff: ff.stdin.close(); ff.wait()
json.dump({"T": T, "E": E, "DUR": DUR}, open("timeline.json", "w"))
print("T", [round(x, 1) for x in T], "DUR", round(DUR, 1))
