"""Unboxing Short template: D (printing) -> A (Bit reacts) -> B (Game HUD) -> CTA. 1080x1920, 30 fps.

Drop-in slots (any phone video; missing files use a placeholder):
  clip1.mov  box on the desk + opening      (section D)
  clip2.mov  lift out, 360 spin, close-ups  (section A)
  clip3.mov  real Bit next to on-screen Bit (section B)
Optional voiceover: vo.mp3 (one file, 4 lines) or vo1..vo4.wav.
Section length = the longer of its clip (trimmed to SECTION_MAX) and its voiceover line.
"""
import os, re, io, sys, math, wave, subprocess, numpy as np, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1080, 1920; FPS = 30; SR = 44100
SECTION_DEFAULT = [6.0, 8.0, 7.0, 4.5]; SECTION_MAX = [8.0, 10.0, 9.0, 8.0]
CLIP_START = {1: 0.0, 2: 0.0, 3: 0.0}  # trim: seconds into each clip to start from

def dur_of(fn):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", fn], capture_output=True, text=True).stdout or 0)
def load(fn):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", fn, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

vo = [load(f"vo{i}.wav") if os.path.exists(f"vo{i}.wav") else np.zeros(0, np.float32) for i in range(1, 5)]
L = []
for i in range(4):
    c = dur_of(f"clip{i+1}.mov") - CLIP_START.get(i + 1, 0) if i < 3 and os.path.exists(f"clip{i+1}.mov") else 0
    L.append(max(SECTION_DEFAULT[i] if not c else min(c, SECTION_MAX[i]), len(vo[i]) / SR + 0.6))
S = [0.0]
for l in L[:-1]: S.append(S[-1] + l)
DUR = sum(L); N = int(DUR * FPS)
voice = np.zeros(int(DUR * SR) + SR, np.float32)
for i in range(4):
    j = int((S[i] + 0.3) * SR); voice[j:j + len(vo[i])] += vo[i]
hop = SR // FPS
rms = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2)) for i in range(N)])
env = np.clip((rms - 0.01) / (max(1e-3, np.percentile(rms[rms > 0.01], 90) if (rms > 0.01).any() else 1) - 0.01), 0, 1)

CY = (0, 240, 255); PK = (240, 53, 158); GR = (57, 255, 136); YL = (255, 214, 0); WH = (255, 255, 255); GY = (165, 170, 190); BG = (13, 13, 20)
FD = lambda s, w="DejaVuSans-Bold": ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{w}.ttf", s)
FI = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", s)
MB = lambda s: FD(s, "DejaVuSansMono-Bold")
def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def fade(c, k): return tuple(int(BG[i] + (c[i] - BG[i]) * k) for i in range(3))
def ctext(d, y, s, f, c, t, t0, stroke=0):
    if t < t0: return
    k = ease((t - t0) / .3); d.text((W / 2, y + 20 * (1 - k)), s, font=f, fill=fade(c, k), anchor="ma", stroke_width=stroke, stroke_fill=(0, 0, 0))
grid = Image.new("RGBA", (W, H), BG + (255,)); gd = ImageDraw.Draw(grid)
for y in range(0, H, 60): gd.line((0, y, W, y), fill=(20, 21, 32))

SVG = open("/home/claude/ai-learning-2026/brand/bit/bit.svg").read()
svg = re.sub(r'<g id="eyes">.*?</g>', '', SVG, flags=re.S); svg = re.sub(r'<path id="mouth"[^>]*/>', '', svg)
BASE = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=600, output_height=700))).convert("RGBA")
def bitimg(f, mood="norm"):
    r = BASE.copy(); d = ImageDraw.Draw(r); a = env[min(f, N - 1)]
    for ex in (244, 356):
        cx, cy = ex, 199
        if mood == "happy": d.arc((cx - 24, cy - 14, cx + 24, cy + 30), 200, 340, fill=CY, width=10)
        elif mood == "shock": d.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), outline=CY, width=9)
        elif (f % 95) in (0, 1, 2): d.rounded_rectangle((cx - 22, cy - 4, cx + 22, cy + 4), radius=3, fill=CY)
        else: d.rounded_rectangle((cx - 22, cy - 29, cx + 22, cy + 29), radius=12, fill=CY)
    mx, my = 300, 262
    if a > 0.08: h = 8 + 38 * a; d.rounded_rectangle((mx - 28, my - h / 2, mx + 28, my + h / 2), radius=int(min(h, 56) / 2), fill=CY)
    elif mood == "shock": d.ellipse((mx - 22, my - 22, mx + 22, my + 22), outline=CY, width=8)
    else: d.arc((mx - 40, my - 40, mx + 40, my + 12), 25, 155, fill=CY, width=9)
    return r
src = open("/home/claude/ai-learning-2026/brand/video-template/build_mcp_video.py").read(); ns = {"Image": Image, "ImageDraw": ImageDraw, "ImageFont": ImageFont}
exec(src[src.index("def yt_icon"):src.index("YT=yt_icon")], ns); exec(src[src.index("def tt_icon"):src.index("TT=tt_icon")], ns)
ICONS = [ns["tt_icon"](84), ns["yt_icon"](84), ns["ig_icon"](84)]

# ---- clips
PREV = Image.open("/home/claude/ai-learning-2026/brand/bit/3d/preview.png").convert("RGB")
PH_VIEWS = [PREV.crop((20, 20, 430, 580)), PREV.crop((470, 20, 880, 580)), PREV.crop((20, 20, 430, 580))]
PH_LABEL = ["CLIP 1: box on desk, opening", "CLIP 2: lift out, 360°, close-ups", "CLIP 3: real Bit + screen Bit"]
class Slot:
    def __init__(self, i, w, h, n):
        self.i, self.w, self.h, self.n, self.k, self.last = i, w, h, n, 0, None
        fn = f"clip{i}.mov"; self.p = None
        if os.path.exists(fn):
            t0 = CLIP_START.get(i, 0)
            vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={FPS}"
            self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-threads", "2", "-ss", str(t0), "-i", fn, "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    def get(self):
        if self.p:
            b = self.p.stdout.read(self.w * self.h * 3)
            if len(b) == self.w * self.h * 3: self.last = Image.frombytes("RGB", (self.w, self.h), b)
            return self.last
        v = PH_VIEWS[self.i - 1]; z = 1 + 0.15 * self.k / max(1, self.n); self.k += 1
        r = max(self.w / v.width, self.h / v.height) * z; im = v.resize((int(v.width * r), int(v.height * r)))
        x = (im.width - self.w) // 2; y = (im.height - self.h) // 2; im = im.crop((x, y, x + self.w, y + self.h))
        d = ImageDraw.Draw(im); lab = PH_LABEL[self.i - 1]; d.rounded_rectangle((20, 20, 50 + d.textlength(lab, font=MB(28)), 70), radius=10, fill=(0, 0, 0)); d.text((35, 28), lab, font=MB(28), fill=YL)
        return im
    def close(self):
        if self.p: self.p.kill(); self.p.wait()
def rmask(w, h, r):
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255); return m

# ---- sfx
tt = np.arange(len(voice)) / SR; sfx = np.zeros_like(voice); rng = np.random.default_rng(4).standard_normal(len(tt)).astype(np.float32)
def tone(t0, fr, d=.15, dec=20, amp=.1):
    i = int(t0 * SR); n = int(d * SR); s = np.sin(2 * np.pi * fr * tt[:n]) * np.exp(-tt[:n] * dec) * amp; sfx[i:i + n] += s[:len(sfx) - i]
for k in range(16): tone(S[0] + 0.2 + k * 0.05, 1400, .02, 90, .03)          # typing
for k in range(10): tone(S[0] + 1.2 + k * (L[0] - 1.6) / 10, 500 + k * 70, .06, 30, .05)  # progress ticks
tone(S[0] + L[0] - .4, 1320, .3, 8, .1)                                       # 100%
tone(S[1] + L[1] * .55, 220, .25, 10, .14); tone(S[1] + L[1] * .55 + .08, 330, .25, 10, .1)  # "that's me?"
for k, fr in enumerate((523, 659, 784, 1047)): tone(S[2] + L[2] * .5 + k * .09, fr, .25, 8, .12)  # ITEM GET
tone(S[3] + .1, 660, .3, 6, .1); tone(S[3] + .22, 990, .4, 6, .1)
mix = np.clip(sfx + voice, -1, 1)[:int(DUR * SR)]
with wave.open("audio.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())

PREVIEW = [float(x) for x in sys.argv[1:]]
OUT = "bit-unboxing.mp4"
ff = None if PREVIEW else subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "audio.wav", "-c:v", "libx264", "-threads", "3", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], stdin=subprocess.PIPE)
slots = {}
def slot(i, w, h, n):
    if i not in slots: slots[i] = Slot(i, w, h, n)
    return slots[i].get()
SCAN = Image.new("RGBA", (960, 1180)); sdd = ImageDraw.Draw(SCAN)
for y in range(0, 1180, 6): sdd.line((0, y, 960, y), fill=(0, 0, 0, 40))

for f in ([int(p * FPS) for p in PREVIEW] if PREVIEW else range(N)):
    t = f / FPS; sec = max(i for i in range(4) if t >= S[i]); lt = t - S[sec]; p = lt / L[sec]
    for k in list(slots):
        if k != sec + 1: slots[k].close(); del slots[k]
    im = grid.copy(); d = ImageDraw.Draw(im)
    if sec == 0:  # D: printing
        cmd = "$ print bit.3mf"; n = int(min(len(cmd), lt / 0.05)); d.text((60, 120), cmd[:n] + ("_" if int(t * 3) % 2 else ""), font=MB(48), fill=GR)
        prog = min(1, max(0, (lt - 1.0) / (L[0] - 1.4)))
        d.text((60, 195), f"PRINTING… {int(prog * 100)}%", font=MB(46), fill=WH); d.rectangle((60, 265, 1020, 305), outline=GR, width=4)
        if prog > 0: d.rectangle((66, 271, 66 + 948 * prog, 299), fill=GR)
        fr = slot(1, 960, 1180, int(L[0] * FPS)); im.paste(fr, (60, 370), rmask(960, 1180, 20)); im.alpha_composite(SCAN, (60, 370)); d = ImageDraw.Draw(im)
        ctext(d, 1600, "I made a robot out of code.", FI(64), WH, t, S[0] + .3)
        ctext(d, 1690, "Then I printed him.", FI(64), CY, t, S[0] + 1.6)
    elif sec == 1:  # A: Bit reacts
        mood = "shock" if p > .55 else "norm"
        r = bitimg(f, mood).resize((300, 350), Image.LANCZOS); im.alpha_composite(r, (60, 140 + int(8 * math.sin(t * 4)))); d = ImageDraw.Draw(im)
        if p > .55:
            k = ease((p - .55) / .08); d.rounded_rectangle((390, 200, 1020, 400), radius=30, fill=fade(WH, k)); d.polygon([(390, 300), (350, 330), (410, 330)], fill=fade(WH, k))
            d.text((705, 300), "Wait… that's ME?", font=FI(56), fill=BG, anchor="mm")
        fr = slot(2, 960, 1080, int(L[1] * FPS)); im.paste(fr, (60, 560), rmask(960, 1080, 30)); d = ImageDraw.Draw(im); d.rounded_rectangle((57, 557, 1023, 1643), radius=30, outline=CY, width=6)
        ctext(d, 1690, "I 3D-printed my AI presenter", FD(48), WH, t, S[1] + .2)
    elif sec == 2:  # B: game HUD
        d.text((60, 120), "BIT", font=MB(48), fill=WH); [d.rectangle((60 + i * 42, 185, 95 + i * 42, 215), fill=CY) for i in range(10)]
        score = int(21943 + 978056 * ease(p)); d.text((1020, 120), "SCORE", font=MB(48), fill=WH, anchor="ra"); d.text((1020, 180), f"{score:06d}", font=MB(48), fill=YL, anchor="ra")
        ctext(d, 290, "LEVEL 2", FI(110), YL, t, S[2]); ctext(d, 410, "REAL LIFE", FI(80), PK, t, S[2] + .3)
        fr = slot(3, 900, 1000, int(L[2] * FPS)); im.paste(fr, (90, 560)); d = ImageDraw.Draw(im); d.rectangle((84, 554, 996, 1566), outline=CY, width=8)
        if p > .5:
            k = ease((p - .5) / .12); s = 1 + .4 * (1 - k)
            d.rounded_rectangle((240, 1610, 840, 1720), radius=14, fill=fade((36, 30, 8), k), outline=fade(YL, k), width=5); d.text((540, 1665), "ITEM GET! ✓", font=FI(int(64 * s)), fill=fade(YL, k), anchor="mm")
    else:  # CTA
        ctext(d, 280, "Follow for the next build", FI(66), WH, t, S[3])
        if lt > .3:
            k = ease((lt - .3) / .35); pulse = 1 + 0.04 * math.sin(lt * 8); bw, bh = int(520 * pulse), int(120 * pulse)
            d.rounded_rectangle((540 - bw / 2, 470 - bh / 2, 540 + bw / 2, 470 + bh / 2), radius=60, fill=fade((230, 30, 40), k)); d.text((540, 470), "SUBSCRIBE", font=FI(64), fill=fade(WH, k), anchor="mm")
            for j, ic in enumerate(ICONS):
                a = ic.copy(); a.putalpha(a.getchannel("A").point(lambda v: int(v * k))); im.alpha_composite(a, (250 + j * 100, 580))
            d = ImageDraw.Draw(im); d.text((560, 622), "@vibewithamitai", font=FD(44), fill=fade(PK, k), anchor="lm")
        ctext(d, 760, "Print files free on GitHub", FD(44), GY, t, S[3] + 1.0)
        ctext(d, 900, "Build it. Test it. Ship it.", FD(58), CY, t, S[3] + 2.0)
        r = bitimg(f, "happy").resize((330, 385), Image.LANCZOS); im.alpha_composite(r, (W // 2 - 165, H - 395 + int(10 * math.sin(t * 3.8))))
    if PREVIEW: im.convert("RGB").save(f"pv_{t:.1f}.png")
    else: ff.stdin.write(im.convert("RGB").tobytes())
for s_ in slots.values(): s_.close()
if ff: ff.stdin.close(); ff.wait()
print("sections", [round(x, 1) for x in S], "lengths", [round(x, 1) for x in L], "DUR", round(DUR, 1))
