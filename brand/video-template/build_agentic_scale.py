"""Short: I rated my AI builds on the agentic scale. 1080x1920, 30 fps."""
import re, io, sys, math, wave, subprocess, numpy as np, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1080, 1920; FPS = 30; SR = 44100; GAP = 0.35; START = 0.2

lines = []
for i in range(1, 10):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"l{i}.wav", "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    lines.append(np.frombuffer(raw, np.int16).astype(np.float32) / 32768)
T = []; t = START
for a in lines: T.append(t); t += len(a) / SR + GAP
E = [T[i] + len(lines[i]) / SR for i in range(9)]
DUR = E[-1] + 1.3; N = int(DUR * FPS); hop = SR // FPS
voice = np.zeros(int(DUR * SR) + SR, np.float32)
for s, a in zip(T, lines): i = int(s * SR); voice[i:i + len(a)] += a
rms = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2)) for i in range(N)])
env = np.clip((rms - 0.01) / (np.percentile(rms[rms > 0.01], 90) - 0.01), 0, 1); env = np.convolve(env, [.25, .5, .25], "same")

CY = (0, 240, 255); PK = (240, 53, 158); GR = (57, 255, 136); RD = (255, 70, 90); WH = (255, 255, 255); GY = (165, 170, 190); BG = (13, 13, 20); YL = (255, 214, 0); PANEL = (20, 22, 34)
FD = lambda s, w="DejaVuSans-Bold": ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{w}.ttf", s)
FI = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", s)
MONO = FD(30, "DejaVuSansMono"); MONOB = lambda s: FD(s, "DejaVuSansMono-Bold")
def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def fade(c, k): return tuple(int(BG[i] + (c[i] - BG[i]) * k) for i in range(3))
def txt(d, xy, s, font, c, t, t0, anchor="ma", dy=24):
    if t < t0: return
    k = ease((t - t0) / .35); d.text((xy[0], xy[1] + dy * (1 - k)), s, font=font, fill=fade(c, k), anchor=anchor)
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
        elif (f % 95) in (0, 1, 2): d.rounded_rectangle((cx - 22, cy - 4, cx + 22, cy + 4), radius=3, fill=CY)
        else: d.rounded_rectangle((cx - 22, cy - 29, cx + 22, cy + 29), radius=12, fill=CY)
    mx, my = 300, 262
    if a > 0.08: h = 8 + 38 * a; d.rounded_rectangle((mx - 28, my - h / 2, mx + 28, my + h / 2), radius=int(min(h, 56) / 2), fill=CY)
    else: d.arc((mx - 40, my - 40, mx + 40, my + 12), 25, 155, fill=CY, width=9)
    return r
src = open("/home/claude/ai-learning-2026/brand/video-template/build_mcp_video.py").read(); ns = {"Image": Image, "ImageDraw": ImageDraw, "ImageFont": ImageFont}
exec(src[src.index("def yt_icon"):src.index("YT=yt_icon")], ns); exec(src[src.index("def tt_icon"):src.index("TT=tt_icon")], ns)
ICONS = [ns["tt_icon"](84), ns["yt_icon"](84), ns["ig_icon"](84)]
BOSS = Image.open("boss.png").convert("RGB").crop((0, 560, 1080, 1460)).resize((126, 105), Image.LANCZOS)

# ---- the scale
SX0, SX1, SY = 90, 990, 1010
def sx(v): return SX0 + (SX1 - SX0) * v
BUILDS = [  # name, sub, level, x, card_y, line, rel time, colour, icon
    ("Checker script", "LOW", 0.18, 640, 2, 1.8, CY, "{ }"),
    ("Prompt eval", "LOW", 0.12, 440, 2, 3.4, CY, "6/6"),
    ("MCP server", "MEDIUM", 0.50, 640, 3, 1.5, YL, "MCP"),
    ("MCP v2", "MEDIUM", 0.50, 440, 4, 1.0, YL, "?"),
    ("Boss fight", "HIGH", 0.88, 640, 5, 1.6, PK, "boss"),
]
def bcard(im, d, b, t):
    name, lvl, v, cy, li, rel, col, icon = b; t0 = T[li] + rel
    if t < t0: return d
    k = ease((t - t0) / .45); x = sx(v) - 115; y = cy - 260 * (1 - k)
    x = max(30, min(W - 260, x))
    d.rounded_rectangle((x, y, x + 230, y + 170), radius=18, fill=PANEL, outline=col, width=4)
    if icon == "boss": im.paste(BOSS, (int(x + 52), int(y + 12))); d = ImageDraw.Draw(im)
    elif icon == "?":
        d.rounded_rectangle((x + 70, y + 18, x + 160, y + 92), radius=16, fill=col); d.polygon([(x + 95, y + 92), (x + 85, y + 112), (x + 118, y + 92)], fill=col); d.text((x + 115, y + 55), "?", font=FI(56), fill=BG, anchor="mm")
    else: d.text((x + 115, y + 60), icon, font=MONOB(54), fill=col, anchor="mm")
    d.text((x + 115, y + 140), name, font=FD(28), fill=WH, anchor="mm")
    if k > .9: d.line((sx(v), y + 170, sx(v), SY - 30), fill=col, width=3)
    return d
def draw_scale(im, d, t, t0, pointer=None):
    if t < t0: return d
    k = ease((t - t0) / .6)
    w = int((SX1 - SX0) * k)
    bar = np.zeros((40, max(1, w), 3), np.uint8); xx = np.linspace(0, 1, SX1 - SX0)[:w, None]
    bar[:] = (np.array(CY) * (1 - xx) * (xx < 2) + 0).astype(np.uint8)
    c = np.where(xx < .5, np.array(CY) * (1 - xx * 2) + np.array(YL) * (xx * 2), np.array(YL) * (1 - (xx - .5) * 2) + np.array(PK) * ((xx - .5) * 2))
    bar[:] = c[None, :, :].astype(np.uint8).reshape(1, w, 3)
    im.paste(Image.fromarray(np.repeat(bar[:1], 40, axis=0)), (SX0, SY - 20)); d = ImageDraw.Draw(im)
    for v, lab, col in ((0.0, "LOW", CY), (0.5, "MEDIUM", YL), (1.0, "HIGH", PK)):
        txt(d, (sx(v) if v not in (0.0, 1.0) else (SX0 + 40 if v == 0 else SX1 - 40), SY + 40), lab, FD(40), col, t, t0 + .3 + v * .4)
    if pointer is not None:
        d.polygon([(sx(pointer) - 22, SY + 110), (sx(pointer) + 22, SY + 110), (sx(pointer), SY + 28)], fill=WH)
    return d

tt = np.arange(len(voice)) / SR; sfx = np.zeros_like(voice)
def tone(t0, fr, d=.15, dec=20, amp=.1):
    i = int(t0 * SR); n = int(d * SR); s = np.sin(2 * np.pi * fr * tt[:n]) * np.exp(-tt[:n] * dec) * amp; sfx[i:i + n] += s[:len(sfx) - i]
for b in BUILDS: t0 = T[b[4]] + b[5]; tone(t0 + .4, 330, .2, 12, .12); tone(t0 + .45, 660 if b[1] == "LOW" else (880 if b[1] == "MEDIUM" else 1320), .25, 10, .1)
tone(T[1] + .2, 520, .3, 8, .08); tone(T[6] + 2.2, 880, .3, 8, .1); tone(T[6] + 5.7, 140, .5, 5, .2)
tone(T[7] + .1, 660, .3, 6, .1); tone(T[7] + .22, 990, .4, 6, .1)
mix = np.clip(sfx + voice, -1, 1)
with wave.open("audio.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix[:int(DUR * SR)] * 32767).astype(np.int16).tobytes())

PREVIEW = [float(x) for x in sys.argv[1:]]
OUT = "agentic-scale.mp4"
ff = None if PREVIEW else subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "audio.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], stdin=subprocess.PIPE)
LAB = ["// agentic AI, module 1", "// the spectrum", "// build 1", "// build 2", "// build 3", "// build 4", "// why not all high?", "// the rule", "// build it. test it. ship it."]
for f in ([int(p * FPS) for p in PREVIEW] if PREVIEW else range(N)):
    t = f / FPS; li = max(i for i in range(9) if t >= T[i] - GAP / 2 or i == 0); lt = t - T[li]
    im = grid.copy(); d = ImageDraw.Draw(im); d.text((60, 80), LAB[li], font=MONO, fill=CY)
    mood = "norm"; show_bit = True
    if li == 0:
        txt(d, (W / 2, 330), "I RATED 5 OF MY", FI(84), WH, t, T[0] + .1)
        txt(d, (W / 2, 440), "AI BUILDS", FI(150), CY, t, T[0] + .5)
        txt(d, (W / 2, 620), "on the agentic AI scale", FD(52), GY, t, T[0] + 1.2)
        if lt > 5.0:
            k = ease((lt - 5.0) / .35); d.rounded_rectangle((70, 780, 1010, 1060), radius=24, fill=fade((36, 30, 8), k), outline=fade(YL, k), width=5)
            txt(d, (W / 2, 810), "The most autonomous", FI(66), WH, t, T[0] + 5.0); txt(d, (W / 2, 900), "≠", FI(70), YL, t, T[0] + 5.3)
            txt(d, (W / 2, 975), "the one I trust most", FI(66), YL, t, T[0] + 5.6)
    elif li <= 5:
        if li == 1:
            txt(d, (W / 2, 300), "Not yes or no.", FI(84), WH, t, T[1] + .2); txt(d, (W / 2, 410), "A spectrum.", FI(100), CY, t, T[1] + 1.4)
            if lt > 3.2:
                k = ease((lt - 3.2) / .35); d.rounded_rectangle((60, 1170, 500, 1330), radius=18, fill=PANEL, outline=fade(CY, k), width=4)
                txt(d, (280, 1200), "My code", FD(46), WH, t, T[1] + 3.2); txt(d, (280, 1260), "decides", FD(46), CY, t, T[1] + 3.2)
            if lt > 6.5:
                k = ease((lt - 6.5) / .35); d.rounded_rectangle((580, 1170, 1020, 1330), radius=18, fill=PANEL, outline=fade(PK, k), width=4)
                txt(d, (800, 1200), "The AI", FD(46), WH, t, T[1] + 6.5); txt(d, (800, 1260), "plans + checks", FD(46), PK, t, T[1] + 6.5)
        d = draw_scale(im, d, t, T[1] + .4, None)
        for b in BUILDS: d = bcard(im, d, b, t)
        cur = [b for b in BUILDS if b[4] == li]
        if cur:
            b = cur[-1] if lt > cur[-1][5] else cur[0]; t0 = T[li] + b[5]
            if t > t0:
                k = ease((t - t0) / .3); s = 1 + .5 * (1 - k)
                tl = Image.new("RGBA", (W, H)); td = ImageDraw.Draw(tl); td.text((W / 2, 1290), b[1], font=FI(int(140 * s)), fill=b[6] + (int(255 * k),), anchor="mm")
                im.alpha_composite(tl.filter(ImageFilter.GaussianBlur(14))); im.alpha_composite(tl); d = ImageDraw.Draw(im)
            if li == 4: txt(d, (W / 2, 1390), "on purpose: it asks me", FD(48), WH, t, T[4] + 2.0)
            if li == 5: txt(d, (W / 2, 1390), "self-scored 3 → 8 / 10", FD(48), WH, t, T[5] + 4.0)
            if li == 2: txt(d, (W / 2, 1390), "my code runs the loop", FD(48), WH, t, T[2] + 3.0)
            if li == 3: txt(d, (W / 2, 1390), "Claude picks tools + order", FD(48), WH, t, T[3] + 2.6)
    elif li == 6:
        txt(d, (W / 2, 300), "Why not make", FI(80), WH, t, T[6] + .1); txt(d, (W / 2, 400), "everything HIGH?", FI(90), PK, t, T[6] + .5)
        if lt > 2.2:
            k = ease((lt - 2.2) / .35); d.rounded_rectangle((60, 600, 1020, 820), radius=24, fill=fade((10, 30, 20), k), outline=fade(GR, k), width=5)
            txt(d, (W / 2, 630), "Bad boss fight", FD(50), WH, t, T[6] + 2.2); txt(d, (W / 2, 710), "10-second re-render", FI(70), GR, t, T[6] + 2.5)
        if lt > 5.7:
            k = ease((lt - 5.7) / .3); shake = int(12 * math.sin(lt * 80) * max(0, 1 - (lt - 5.7) / .5))
            d.rounded_rectangle((60 + shake, 880, 1020 + shake, 1100), radius=24, fill=fade((40, 8, 16), k), outline=fade(RD, k), width=5)
            txt(d, (W / 2 + shake, 910), "Bad requirement", FD(50), WH, t, T[6] + 5.7); txt(d, (W / 2 + shake, 990), "the whole project", FI(70), RD, t, T[6] + 5.9)
    elif li == 7:
        txt(d, (W / 2, 330), "MATCH THE", FI(110), WH, t, T[7] + .1)
        txt(d, (W / 2, 460), "AUTONOMY", FI(140), CY, t, T[7] + .4)
        txt(d, (W / 2, 620), "TO THE RISK", FI(110), YL, t, T[7] + .7)
        txt(d, (W / 2, 820), "a systems engineering decision,", FD(46), WH, t, T[7] + 2.4); txt(d, (W / 2, 885), "not an AI one", FD(46), WH, t, T[7] + 2.9)
        mood = "happy"
    else:
        t0 = T[8]
        txt(d, (W / 2, 280), "Follow for the next build", FI(66), WH, t, t0)
        if t >= t0 + .3:
            k = ease((t - t0 - .3) / .35); pulse = 1 + 0.04 * math.sin((t - t0) * 8); bw, bh = int(520 * pulse), int(120 * pulse)
            d.rounded_rectangle((540 - bw / 2, 470 - bh / 2, 540 + bw / 2, 470 + bh / 2), radius=60, fill=fade((230, 30, 40), k)); d.text((540, 470), "SUBSCRIBE", font=FI(64), fill=fade(WH, k), anchor="mm")
            for j, ic in enumerate(ICONS):
                a = ic.copy(); a.putalpha(a.getchannel("A").point(lambda v: int(v * k))); im.alpha_composite(a, (250 + j * 100, 580))
            d = ImageDraw.Draw(im); d.text((560, 622), "@vibewithamitai", font=FD(44), fill=fade(PK, k), anchor="lm")
        txt(d, (W / 2, 760), "Share with an engineer friend", FD(44), GY, t, t0 + 1.4)
        txt(d, (W / 2, 900), "Build it. Test it. Ship it.", FD(58), CY, t, t0 + 4.8)
        mood = "happy" if lt > 4.8 else "norm"
    r = bitimg(f, mood).resize((330, 385), Image.LANCZOS)
    bob = int(10 * math.sin(t * 2 * math.pi * .6))
    im.alpha_composite(r, (W // 2 - 165, H - 385 - 10 + bob))
    if PREVIEW: im.convert("RGB").save(f"pv_{t:.1f}.png")
    else: ff.stdin.write(im.convert("RGB").tobytes())
if ff: ff.stdin.close(); ff.wait()
print("T", [round(x, 2) for x in T], "DUR", round(DUR, 1))
