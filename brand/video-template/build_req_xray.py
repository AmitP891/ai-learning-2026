"""REQ X-RAY Short: paper case file -> scan -> blueprint. Vague Requirement of the Week template. 1080x1920, 30 fps.
Change CASE for each week. Voiceover: vo.mp3 (one file, one line per beat, blank-line pauses) -> split into vo1..vo7.wav,
or leave them out to preview with default timings."""
import os, io, sys, math, wave, subprocess, numpy as np, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CASE = {
    "num": "002", "id": "REQ-014", "system": "FLIGHT LOGGER", "title": "THE SUNLIGHT TRAP",
    "quote": ["The display", "shall be", "readable in", "sunlight."],
    "icon": "sun", "unknown": "? lux", "unknown_tag": "no number found",
    "test": "Readable by who?\nHow bright?", "why": "No number.\nNo unit.\nNo condition.",
    "known": "≥1000 nits", "known_sub": "up to 100,000 lux",
    "rewrite": "Display luminance\n≥ 1000 cd/m² and\ncontrast ≥ 5:1 in\n≤ 100,000 lux.",
    "foot_bad": ("Passes every review.", "Fails every test."), "foot_good": ("No number = no test.", "Ask for one. Don't guess it."),
}
W, H = 1080, 1920; FPS = 30; SR = 44100; GAP = 0.35
DEFAULT = [3.2, 3.0, 2.0, 5.5, 3.2, 8.5, 8.0]  # per voiceover line, used when no vo files

def load(fn):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", fn, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768
vo = [load(f"vo{i}.wav") if os.path.exists(f"vo{i}.wav") else None for i in range(1, 8)]
T = []; t = 0.3
for i in range(7):
    T.append(t); t += (len(vo[i]) / SR if vo[i] is not None else DEFAULT[i]) + GAP
E = [T[i] + ((len(vo[i]) / SR) if vo[i] is not None else DEFAULT[i]) for i in range(7)]
DUR = E[-1] + 1.2; N = int(DUR * FPS)
voice = np.zeros(int(DUR * SR) + SR, np.float32)
for i in range(7):
    if vo[i] is not None: j = int(T[i] * SR); voice[j:j + len(vo[i])] += vo[i]
hop = SR // FPS
rms = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2)) for i in range(N)])
hi = np.percentile(rms[rms > 0.01], 90) if (rms > 0.01).any() else 1
env = np.clip((rms - 0.01) / (hi - 0.01), 0, 1)

FD = lambda s, w="DejaVuSans-Bold": ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{w}.ttf", s)
FI = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", s)
FB = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", s)
MB = lambda s: FD(s, "DejaVuSansMono-Bold"); MR = lambda s: FD(s, "DejaVuSansMono")
PAPER = (22, 24, 38); INK = (255, 255, 255); RED = (240, 53, 158); CY = (0, 240, 255); GR = (57, 255, 136); WH = (255, 255, 255); PK = (240, 53, 158)
BP = (8, 24, 34); BPL = (0, 240, 255); BPG = (12, 52, 64)
def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
rng = np.random.default_rng(1)
CX0, CY0, CX1, CY1 = 70, 330, 1010, 1500; CW, CH = CX1 - CX0, CY1 - CY0

def icon(d, cx, cy, kind, col, blueprint):
    if kind == "sun":
        r = 80; d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=10 if not blueprint else 5)
        for k in range(12):
            a = k * math.pi / 6; d.line((cx + 110 * math.cos(a), cy + 110 * math.sin(a), cx + 150 * math.cos(a), cy + 150 * math.sin(a)), fill=col, width=10 if not blueprint else 5)
        if blueprint:
            for rr in (40, 120): d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(0, 120, 140), width=2)
            d.line((cx - 170, cy, cx + 170, cy), fill=(0, 120, 140), width=2); d.line((cx, cy - 170, cx, cy + 170), fill=(0, 120, 140), width=2)

def paper_card():
    a = np.zeros((CH, CW, 3), np.float32) + np.array(PAPER); a += rng.normal(0, 2, (CH, CW, 1))
    c = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA"); d = ImageDraw.Draw(c)
    d.rectangle((0, 0, CW - 1, CH - 1), outline=(58, 63, 92), width=4); d.rectangle((30, 30, 200, 72), fill=RED); d.text((115, 51), CASE["id"], font=MB(28), fill=WH, anchor="mm")
    d.text((CW - 40, 40), "CASE · " + CASE["system"], font=MR(22), fill=(150, 155, 178), anchor="ra")
    d.text((40, 100), CASE["title"], font=FI(72), fill=INK)
    d.rounded_rectangle((40, 220, 460, 980), radius=46, outline=INK, width=10); d.rounded_rectangle((60, 240, 440, 960), radius=34, fill=(32, 34, 52))
    icon(d, 250, 540, CASE["icon"], INK, False)
    d.text((250, 760), CASE["unknown"], font=FI(84), fill=RED, anchor="mm")
    d.rounded_rectangle((90, 880, 410, 935), radius=10, fill=(58, 63, 92)); d.text((250, 907), CASE["unknown_tag"], font=MR(24), fill=WH, anchor="mm")
    d.text((500, 230), "“", font=FI(150), fill=RED)
    for i, l in enumerate(CASE["quote"]): d.text((500, 370 + i * 74), l, font=FI(64), fill=INK)
    d.rectangle((500, 720, CW - 40, 980), outline=(70, 74, 100), width=3)
    d.text((520, 745), "WHY IT FAILS", font=MB(24), fill=(150, 155, 178)); d.text((520, 790), "• X-RAY PENDING", font=MB(24), fill=RED)
    d.text((40, 1050), CASE["foot_bad"][0], font=FB(44), fill=INK); d.text((40, 1105), CASE["foot_bad"][1], font=FB(44), fill=RED)
    return c

def blue_card(reveal):
    """reveal: dict of 0..1 per element: test, why, known, rewrite, foot"""
    c = Image.new("RGBA", (CW, CH), BP + (255,)); d = ImageDraw.Draw(c)
    for x in range(0, CW, 40): d.line((x, 0, x, CH), fill=BPG)
    for y in range(0, CH, 40): d.line((0, y, CW, y), fill=BPG)
    d.rectangle((14, 14, CW - 14, CH - 14), outline=BPL, width=3)
    d.rectangle((30, 30, 260, 72), outline=BPL, width=3); d.text((145, 51), "X-RAY · " + CASE["id"], font=MB(24), fill=BPL, anchor="mm")
    d.text((40, 100), CASE["title"], font=FI(72), fill=WH)
    d.rounded_rectangle((40, 220, 460, 980), radius=46, outline=BPL, width=6)
    icon(d, 250, 540, CASE["icon"], BPL, True)
    def a(c_, k): return tuple(int(BP[i] + (c_[i] - BP[i]) * k) for i in range(3))
    k = reveal.get("known", 0)
    if k > 0:
        d.text((250, 760), CASE["known"], font=FI(76), fill=a(GR, k), anchor="mm"); d.text((250, 825), CASE["known_sub"], font=MR(26), fill=a(BPL, k), anchor="mm")
    y = 225
    for n, key, lab in (("1", "test", "WHAT YOU'D TEST"), ("2", "why", "WHY YOU CAN'T")):
        k = reveal.get(key, 0); txt = CASE[key]
        if k > 0:
            d.ellipse((500, y, 540, y + 40), outline=a(BPL, k), width=3); d.text((520, y + 20), n, font=MB(22), fill=a(BPL, k), anchor="mm")
            d.text((556, y + 6), lab, font=MB(24), fill=a(BPL, k)); d.multiline_text((556, y + 46), txt, font=FB(38), fill=a(WH, k), spacing=6)
        y += 46 + txt.count("\n") * 48 + 100
    k = reveal.get("rewrite", 0)
    if k > 0:
        d.rectangle((500, y, CW - 40, 980), fill=a((10, 70, 44), k)); d.text((520, y + 20), "TESTABLE REWRITE", font=MB(24), fill=a((200, 255, 220), k))
        d.multiline_text((520, y + 62), CASE["rewrite"], font=FB(32), fill=a(WH, k), spacing=6)
        d.text((520, 948), "[example values]", font=MR(20), fill=a((200, 255, 220), k))
    k = reveal.get("foot", 0)
    if k > 0:
        d.text((40, 1050), CASE["foot_good"][0], font=FB(44), fill=a(WH, k)); d.text((40, 1105), CASE["foot_good"][1], font=FB(44), fill=a(GR, k))
    return c

BOARD = Image.new("RGBA", (W, H), (13, 13, 20, 255)); _g = ImageDraw.Draw(BOARD)
for _y in range(0, H, 60): _g.line((0, _y, W, _y), fill=(20, 21, 32))
bd = ImageDraw.Draw(BOARD); bd.text((60, 90), "REQ X-RAY", font=MB(30), fill=(200, 200, 210)); bd.text((1020, 90), "// CASE " + CASE["num"], font=MB(30), fill=RED, anchor="ra")
SH = Image.new("RGBA", (W, H)); ImageDraw.Draw(SH).rectangle((CX0 + 12, CY0 + 18, CX1 + 12, CY1 + 18), fill=(0, 0, 0, 150)); SH = SH.filter(ImageFilter.GaussianBlur(14))
PAPERC = paper_card()

SVG = open("/home/claude/ai-learning-2026/brand/bit/bit.svg").read()
import re
svg = re.sub(r'<g id="eyes">.*?</g>', '', SVG, flags=re.S); svg = re.sub(r'<path id="mouth"[^>]*/>', '', svg)
BASE = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=600, output_height=700))).convert("RGBA")
def bitimg(f, mood="norm"):
    r = BASE.copy(); d = ImageDraw.Draw(r); av = env[min(f, N - 1)]
    for ex in (244, 356):
        cx, cy = ex, 199
        if mood == "happy": d.arc((cx - 24, cy - 14, cx + 24, cy + 30), 200, 340, fill=CY, width=10)
        elif (f % 95) in (0, 1, 2): d.rounded_rectangle((cx - 22, cy - 4, cx + 22, cy + 4), radius=3, fill=CY)
        else: d.rounded_rectangle((cx - 22, cy - 29, cx + 22, cy + 29), radius=12, fill=CY)
    if av > 0.08: h = 8 + 38 * av; d.rounded_rectangle((272, 262 - h / 2, 328, 262 + h / 2), radius=int(min(h, 56) / 2), fill=CY)
    else: d.arc((260, 222, 340, 274), 25, 155, fill=CY, width=9)
    return r.resize((240, 280), Image.LANCZOS)
src = open("/home/claude/ai-learning-2026/brand/video-template/build_mcp_video.py").read(); ns = {"Image": Image, "ImageDraw": ImageDraw, "ImageFont": ImageFont}
exec(src[src.index("def yt_icon"):src.index("YT=yt_icon")], ns); exec(src[src.index("def tt_icon"):src.index("TT=tt_icon")], ns)
ICONS = [ns["tt_icon"](84), ns["yt_icon"](84), ns["ig_icon"](84)]

# sfx
tt = np.arange(len(voice)) / SR; sfx = np.zeros_like(voice); noise = np.random.default_rng(5).standard_normal(len(tt)).astype(np.float32)
def tone(t0, fr, d=.15, dec=20, amp=.1):
    i = int(t0 * SR); n = int(d * SR); s = np.sin(2 * np.pi * fr * tt[:n]) * np.exp(-tt[:n] * dec) * amp; sfx[i:i + n] += s[:len(sfx) - i]
def thump(t0, amp=.25):
    i = int(t0 * SR); n = int(.2 * SR); s = noise[:n] * np.exp(-np.arange(n) / SR * 30) * amp * .4 + np.sin(2 * np.pi * 70 * tt[:n]) * np.exp(-tt[:n] * 18) * amp; sfx[i:i + n] += s
SCAN0 = T[2] + 0.3; SCAN1 = SCAN0 + 1.4
thump(T[0] + 0.15); thump(T[1] + 0.1, .15)
i0 = int(SCAN0 * SR); n = int(1.4 * SR); sw = np.sin(2 * np.pi * (300 + 900 * tt[:n] / 1.4) * tt[:n]) * 0.05; sfx[i0:i0 + n] += sw
tone(SCAN1, 1320, .3, 8, .1)
for k_, t0 in enumerate((T[3] + .3, T[4] + .2, T[5] + .3)): tone(t0, 700 + k_ * 150, .15, 15, .09)
tone(T[6] + .1, 660, .3, 6, .1); tone(T[6] + .22, 990, .45, 6, .1)
mix = np.clip(sfx + voice, -1, 1)[:int(DUR * SR)]
with wave.open("audio.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())

PREVIEW = [float(x) for x in sys.argv[1:]]
OUT = f"vague-req-{CASE['num']}.mp4"
ff = None if PREVIEW else subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "audio.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], stdin=subprocess.PIPE)
FOOT = ["Bit opens the case…", "Bit opens the case…", "Running the X-ray…", "X-ray: what you'd test", "X-ray: why you can't", "The testable rewrite", "Case closed ✓"]
for f in ([int(p * FPS) for p in PREVIEW] if PREVIEW else range(N)):
    t = f / FPS; li = max(i for i in range(7) if t >= T[i] - GAP / 2 or i == 0)
    im = BOARD.copy()
    reveal = {"test": ease((t - T[3] - .3) / .4), "why": ease((t - T[4] - .2) / .4), "known": ease((t - T[5] - .3) / .4),
              "rewrite": ease((t - T[5] - 1.0) / .5), "foot": ease((t - T[6]) / .4)}
    # card drop-in
    k = ease((t - 0.05) / .45); dy = int(-700 * (1 - k)); shake = int(8 * math.sin(t * 70) * max(0, 1 - (t - .5) / .3)) if t > .5 else 0
    if t < SCAN0: card = PAPERC
    elif t < SCAN1:
        sx = int(CW * (t - SCAN0) / (SCAN1 - SCAN0)); card = PAPERC.copy(); card.paste(blue_card(reveal).crop((0, 0, sx, CH)), (0, 0))
    else: card = blue_card(reveal)
    im.alpha_composite(SH, (0, dy)); im.alpha_composite(card, (CX0 + shake, CY0 + dy))
    d = ImageDraw.Draw(im)
    for x in (300, 780): d.rectangle((x, CY0 - 18 + dy, x + 60, CY0 + 14 + dy), fill=(70, 72, 82))
    if li == 1 and t < SCAN0:  # highlight the quote
        kk = ease((t - T[1]) / .4); hl = Image.new("RGBA", (W, H)); hd = ImageDraw.Draw(hl)
        hd.rounded_rectangle((CX0 + 488, CY0 + 360, CX1 - 30, CY0 + 370 + 74 * len(CASE["quote"])), radius=12, outline=(240, 53, 158, int(255 * kk)), width=6); im.alpha_composite(hl)
    if SCAN0 <= t < SCAN1:
        sx = CX0 + int(CW * (t - SCAN0) / (SCAN1 - SCAN0)); g = Image.new("RGBA", (W, H)); gd = ImageDraw.Draw(g)
        gd.rectangle((sx - 6, CY0 - 40, sx + 6, CY1 + 40), fill=CY + (255,)); im.alpha_composite(g.filter(ImageFilter.GaussianBlur(18))); im.alpha_composite(g)
        ImageDraw.Draw(im).text((min(sx + 20, 820), CY0 - 60), "SCANNING…", font=MB(28), fill=CY)
    if li == 0 and t > T[0] + .6:  # hook banner
        kk = ease((t - T[0] - .6) / .3); bn = Image.new("RGBA", (W, H)); bnd = ImageDraw.Draw(bn)
        bnd.rectangle((0, 170, W, 290), fill=(240, 53, 158, int(235 * kk))); bnd.text((W / 2, 230), "FAILS EVERY TEST", font=FI(72), fill=(255, 255, 255, int(255 * kk)), anchor="mm"); im.alpha_composite(bn)
    d = ImageDraw.Draw(im)
    if t < T[6] + 3.5:
        im.alpha_composite(bitimg(f, "happy" if li == 6 else "norm"), (60, 1580 + int(8 * math.sin(t * 3.8)))); d = ImageDraw.Draw(im)
        d.text((330, 1640), FOOT[li], font=FI(52), fill=[WH, WH, CY, BPL, BPL, GR, GR][li])
        d.text((330, 1715), f"Vague Requirement of the Week #{int(CASE['num'])}", font=MB(28), fill=(150, 150, 165))
    else:
        kk = ease((t - T[6] - 3.5) / .35); ov = Image.new("RGBA", (W, H), (13, 13, 20, int(250 * kk))); im.alpha_composite(ov); d = ImageDraw.Draw(im)
        pulse = 1 + 0.04 * math.sin(t * 8); bw, bh = int(520 * pulse), int(120 * pulse)
        d.text((W / 2, 520), "Got a vague requirement?", font=FI(60), fill=WH, anchor="mm"); d.text((W / 2, 600), "Drop it in the comments 👇" if False else "Drop it in the comments", font=FB(46), fill=(165, 170, 190), anchor="mm")
        d.rounded_rectangle((540 - bw / 2, 760 - bh / 2, 540 + bw / 2, 760 + bh / 2), radius=60, fill=(230, 30, 40)); d.text((540, 760), "SUBSCRIBE", font=FI(64), fill=WH, anchor="mm")
        for j, ic in enumerate(ICONS): im.alpha_composite(ic, (250 + j * 100, 870))
        d = ImageDraw.Draw(im); d.text((560, 912), "@vibewithamitai", font=FD(44), fill=PK, anchor="lm")
        d.text((W / 2, 1060), "Build it. Test it. Ship it.", font=FD(58), fill=CY, anchor="mm")
        im.alpha_composite(bitimg(f, "happy").resize((330, 385)), (W // 2 - 165, 1300 + int(10 * math.sin(t * 3.8))))
    if PREVIEW: im.convert("RGB").save(f"pv_{t:.1f}.png")
    else: ff.stdin.write(im.convert("RGB").tobytes())
if ff: ff.stdin.close(); ff.wait()
print("T", [round(x, 1) for x in T], "DUR", round(DUR, 1))
