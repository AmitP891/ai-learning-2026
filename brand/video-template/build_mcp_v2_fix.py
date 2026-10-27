"""Short: 'My MCP server crashed on camera. Here's how I fixed it.'
Screen recordings (stills) + Bit lip-synced to 7 voiceover lines. 1080x1920, 30 fps."""
import re, io, math, subprocess, wave, numpy as np, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1080, 1920; FPS = 30; SR = 44100; GAP = 0.35; START = 0.3

# ---- audio: 7 lines back to back
lines = []
for i in range(1, 8):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"vo{i}.mp3", "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    lines.append(np.frombuffer(raw, np.int16).astype(np.float32) / 32768)
T = []; t = START
for a in lines: T.append(t); t += len(a) / SR + GAP
E = [T[i] + len(lines[i]) / SR for i in range(7)]
DUR = E[-1] + 1.4; N = int(DUR * FPS); hop = SR // FPS
voice = np.zeros(int(DUR * SR), np.float32)
for s, a in zip(T, lines): i = int(s * SR); voice[i:i + len(a)] += a
rms = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2)) for i in range(N)])
env = np.clip((rms - 0.01) / (np.percentile(rms[rms > 0.01], 90) - 0.01), 0, 1); env = np.convolve(env, [.25, .5, .25], "same")

CY = (0, 240, 255); PK = (255, 43, 214); GR = (57, 255, 136); RD = (255, 70, 90); WH = (255, 255, 255); GY = (170, 175, 190); BG = (13, 13, 20); YL = (255, 214, 0)
FD = lambda s, w="DejaVuSans-Bold": ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{w}.ttf", s)
FI = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", s)
def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def fade(c, k): return tuple(int(BG[i] + (c[i] - BG[i]) * k) for i in range(3))
def txt(d, xy, s, font, c, t, t0, anchor="ma", dy=24):
    if t < t0: return
    k = ease((t - t0) / .35); d.text((xy[0], xy[1] + dy * (1 - k)), s, font=font, fill=fade(c, k), anchor=anchor)

# ---- Bit
SVG = open("/home/claude/ai-learning-2026/brand/bit/bit.svg").read()
svg = re.sub(r'<g id="eyes">.*?</g>', '', SVG, flags=re.S); svg = re.sub(r'<path id="mouth"[^>]*/>', '', svg)
def png(s, sc): return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=s.encode(), output_width=int(600 * sc), output_height=int(700 * sc)))).convert("RGBA")
BASE = png(svg, 1.0)
def bitimg(f, mood="norm"):
    r = BASE.copy(); d = ImageDraw.Draw(r); a = env[min(f, N - 1)]
    for ex in (244, 356):
        cx, cy = ex, 199
        if mood == "happy": d.arc((cx - 24, cy - 14, cx + 24, cy + 30), 200, 340, fill=CY, width=10)
        elif mood == "shock": d.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), outline=CY, width=9)
        elif (f % 95) in (0, 1, 2): d.rounded_rectangle((cx - 22, cy - 4, cx + 22, cy + 4), radius=3, fill=CY)
        else: d.rounded_rectangle((cx - 22, cy - 29, cx + 22, cy + 29), radius=12, fill=CY)
    mx, my = 300, 262
    if a > 0.08:
        h = 8 + 38 * a; w = 56; d.rounded_rectangle((mx - w / 2, my - h / 2, mx + w / 2, my + h / 2), radius=int(min(h, w) / 2), fill=CY)
    else: d.arc((mx - 40, my - 40, mx + 40, my + 12), 25, 155, fill=CY, width=9)
    return r

src = open("/home/claude/ai-learning-2026/brand/video-template/build_mcp_video.py").read(); ns = {"Image": Image, "ImageDraw": ImageDraw, "ImageFont": ImageFont}
exec(src[src.index("def yt_icon"):src.index("YT=yt_icon")], ns); exec(src[src.index("def tt_icon"):src.index("TT=tt_icon")], ns)
ICONS = [ns["tt_icon"](84), ns["yt_icon"](84), ns["ig_icon"](84)]

# ---- screen stills: (file, crop box, highlight box in crop coords or None)
SH = {
    "prompt":  ("st_r1_6.png",    (480, 560, 1440, 900), None),
    "fail":    ("st_r1_15.5.png", (480, 540, 1120, 700), (420, 100, 515, 138)),
    "fix":     ("st_r2_20.png",   (490, 320, 1290, 540), (20, 20, 770, 200)),
    "prog":    ("st_r3_10.5.png", (1280, 230, 1720, 350), (52, 80, 228, 108)),
    "table":   ("st_r4_30.png",   (994, 60, 1826, 560), None),
    "ask":     ("st_r4_50.png",   (994, 620, 1826, 900), (24, 56, 832, 127)),
    "answer":  ("st_r4_107.png",  (994, 820, 1826, 1040), (20, 158, 250, 198)),
    "rewrite": ("st_r4_125.png",  (994, 560, 1826, 900), (36, 170, 622, 214)),
}
SHOT = {}
for k, (fn, box, hl) in SH.items():
    im = Image.open(fn).convert("RGB").crop(box); sc = 1000 / im.width
    SHOT[k] = (im.resize((1000, int(im.height * sc)), Image.LANCZOS), [v * sc for v in hl] if hl else None)

def screen(im, key, t, t0, top=300, maxh=1060, zoom=0.04, hlc=YL, hl_t=0.6, label=None):
    """Card with a screen still, slow push-in, optional highlight box that draws on."""
    shot, hl = SHOT[key]; k = ease((t - t0) / .35)
    z = 1 + zoom * min(1, max(0, t - t0) / 4)
    s = shot.resize((int(shot.width * z), int(shot.height * z)))
    ch = min(s.height, maxh); ox = (s.width - 1000) // 2
    oy = 0 if hl is None else int(max(0, min(s.height - ch, hl[1] * z - ch * 0.5)))
    s = s.crop((ox, oy, ox + 1000, oy + ch))
    y = top + int(30 * (1 - k)); x = 40
    card = Image.new("RGBA", (1000, ch), (0, 0, 0, 0)); m = Image.new("L", (1000, ch), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, 999, ch - 1), radius=22, fill=int(255 * k)); card.paste(s, (0, 0), m)
    im.alpha_composite(card, (x, y)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((x - 3, y - 3, x + 1003, y + ch + 3), radius=24, outline=fade((60, 64, 90), k), width=3)
    if label: d.text((x + 6, y - 46), label, font=FD(30, "DejaVuSansMono"), fill=fade(GY, k))
    if hl and t > t0 + hl_t:
        kk = ease((t - t0 - hl_t) / .4); bx = [hl[0] * z - ox + x, hl[1] * z - oy + y, hl[2] * z - ox + x, hl[3] * z - oy + y]
        pad = 10 + 30 * (1 - kk); pulse = 0.5 + 0.5 * math.sin((t - t0) * 6)
        d.rounded_rectangle((bx[0] - pad, bx[1] - pad, bx[2] + pad, bx[3] + pad), radius=12, outline=hlc, width=int(5 + 2 * pulse))
    return y + ch

def caption(d, t, t0, a, b=None, ca=WH, cb=CY, y=1380):
    txt(d, (W / 2, y), a, FI(70), ca, t, t0)
    if b: txt(d, (W / 2, y + 88), b, FI(70), cb, t, t0 + .25)

grid = Image.new("RGBA", (W, H), BG + (255,)); gd = ImageDraw.Draw(grid)
for y in range(0, H, 60): gd.line((0, y, W, y), fill=(20, 21, 32))

# ---- sfx
tt = np.arange(int(DUR * SR)) / SR; sfx = np.zeros_like(tt, dtype=np.float32); noise = np.random.default_rng(3).standard_normal(len(tt)).astype(np.float32)
def tone(t0, fr, d=.15, dec=20, amp=.12):
    i = int(t0 * SR); n = int(d * SR); s = np.sin(2 * np.pi * fr * tt[:n]) * np.exp(-tt[:n] * dec) * amp; sfx[i:i + n] += s[:len(sfx) - i]
def zap(t0, amp=.22):
    i = int(t0 * SR); n = int(.25 * SR); sfx[i:i + n] += noise[:n] * amp * np.exp(-np.arange(n) / SR * 12)
T3fail = T[2]; ASK = T[5]; ANS = T[5] + 3.6; REW = T[5] + 5.6; PROG2 = T[4] + 2.9
zap(1.0); zap(1.25, .14); zap(T3fail + 0.05, .3); tone(T3fail + .1, 160, .4, 6, .2)
tone(T[3] + 0.2, 880, .2, 10); tone(T[4] + 0.2, 1100, .15, 15)
for k in range(8): tone(T[4] + 0.4 + k * 0.18, 900 + k * 60, .05, 40, .07)
tone(ANS, 1320, .12, 25, .1); tone(REW, 660, .3, 6, .14); tone(REW + .12, 880, .3, 6, .14); tone(REW + .24, 1320, .5, 5, .14)
tone(T[6] + 5.5, 660, .3, 6, .12); tone(T[6] + 5.62, 990, .4, 6, .12)
mix = np.clip(sfx + voice, -1, 1)
with wave.open("audio.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())

OUT = "mcp-v2-crashed-on-camera.mp4"
import sys
PREVIEW = [float(x) for x in sys.argv[1:]]
ff = None if PREVIEW else subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "audio.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], stdin=subprocess.PIPE)
mono = FD(30, "DejaVuSansMono")
frames = [int(p * FPS) for p in PREVIEW] if PREVIEW else range(N)
for f in frames:
    t = f / FPS; im = grid.copy(); d = ImageDraw.Draw(im)
    labels = ["// mcp server v2", "// requirements-checker-v2", "// run 1", "// the fix", "// run 2", "// fix_requirement", "// build it. test it. ship it."]
    li = max(i for i in range(7) if t >= T[i] - GAP / 2 or i == 0)
    d.text((60, 80), labels[li], font=mono, fill=CY)
    bit_y = 1920; bscale = 0.55; mood = "norm"; shake = 0
    if li == 0:
        # hook
        txt(d, (W / 2, 260), "MY MCP SERVER", FI(104), WH, t, 0.15)
        glitch = 0.8 < t < 1.6 and int(t * 20) % 2 == 0
        tl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); td = ImageDraw.Draw(tl)
        if t > 0.7:
            k = ease((t - 0.7) / .25); dx = 14 if glitch else 0
            td.text((W / 2 + dx, 470), "CRASHED", font=FI(190), fill=RD + (int(255 * k),), anchor="mm")
            if glitch: td.text((W / 2 - 10, 470), "CRASHED", font=FI(190), fill=CY + (90,), anchor="mm")
            im.alpha_composite(tl.filter(ImageFilter.GaussianBlur(16))); im.alpha_composite(tl); d = ImageDraw.Draw(im)
        txt(d, (W / 2, 600), "on camera.", FI(96), WH, t, 1.3)
        txt(d, (W / 2, 760), "Here's the fix ↓", FD(54), CY, t, 2.4)
        bscale = 1.0; mood = "shock" if 0.8 < t < 2.2 else "norm"
    elif li == 1:
        screen(im, "prompt", t, T[1] - .1, top=330, label="Claude, desktop app")
        d = ImageDraw.Draw(im)
        caption(d, t, T[1] + 1.0, "No number?", None, WH, y=1000)
        caption(d, t, T[1] + 4.4, "Ask me.", "Don't guess.", CY, PK, y=1100)
    elif li == 2:
        shake = int(10 * math.sin(t * 90) * max(0, 1 - (t - T[2]) / .5))
        screen(im, "fail", t + 0, T[2] - .1, top=500 + shake, zoom=0.08, hlc=RD, hl_t=0.15, label="fix_requirement")
        d = ImageDraw.Draw(im)
        tl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); td = ImageDraw.Draw(tl)
        k = ease((t - T[2] - .1) / .2); td.text((W / 2, 1000), "FAILED", font=FI(200), fill=RD + (int(255 * k),), anchor="mm")
        im.alpha_composite(tl.filter(ImageFilter.GaussianBlur(14))); im.alpha_composite(tl); d = ImageDraw.Draw(im)
        mood = "shock"
    elif li == 3:
        bottom = screen(im, "fix", t, T[3] - .1, top=260, maxh=900, zoom=0.03, hl_t=1.2, label="requirements_server_v2.py")
        d = ImageDraw.Draw(im)
        caption(d, t, T[3] + 4.0, "No forms?", "Ask in chat.", WH, CY, y=1200)
        txt(d, (W / 2, 1390), "Never invent a number.", FD(50), YL, t, T[3] + 7.3)
    elif li == 4:
        if t < PROG2:
            screen(im, "prog", t, T[4] - .1, top=420, zoom=0.05, hl_t=0.5, label="Claude Code, terminal")
            d = ImageDraw.Draw(im); caption(d, t, T[4] + .6, "Live progress", "7 / 8 checked", WH, CY, y=1050)
        else:
            screen(im, "table", t, PROG2, top=260, maxh=960, zoom=0.02, label="check_all result")
            d = ImageDraw.Draw(im); caption(d, t, PROG2 + .4, "6 need review", None, YL, y=1270)
    elif li == 5:
        if t < ANS:
            screen(im, "ask", t, ASK - .1, top=300, zoom=0.03, hl_t=0.8, label="fix REQ-002")
            d = ImageDraw.Draw(im); caption(d, t, ASK + 1.2, "Claude asks me", None, WH, y=1250)
        elif t < REW:
            screen(im, "answer", t, ANS, top=300, zoom=0.03, hl_t=0.2, hlc=GR, label="my answer")
            d = ImageDraw.Draw(im); caption(d, t, ANS + .2, "200 ms", None, GR, y=1250)
        else:
            screen(im, "rewrite", t, REW, top=280, zoom=0.04, hl_t=0.4, hlc=GR, label="the rewrite")
            d = ImageDraw.Draw(im); caption(d, t, REW + .8, "Testable ✓", None, GR, y=1300); mood = "happy"
    else:
        t0 = T[6]
        txt(d, (W / 2, 200), "The code is free", FI(84), GR, t, t0)
        if t > t0 + .2:
            k = ease((t - t0 - .2) / .35); d.rounded_rectangle((80, 330, 1000, 560), radius=24, fill=fade((12, 26, 20), k), outline=fade(GR, k), width=5)
            d.text((540, 395), "★  GitHub", font=FI(64), fill=fade(WH, k), anchor="mm")
            d.text((540, 480), "AmitP891/ai-learning-2026", font=FD(42, "DejaVuSansMono-Bold"), fill=fade(GR, k), anchor="mm")
            d.text((540, 530), "01-anthropic-academy/mcp · link in bio", font=FD(28), fill=fade(GY, k), anchor="mm")
        tS = t0 + 2.2
        if t >= tS:
            k = ease((t - tS) / .35); pulse = 1 + 0.04 * math.sin((t - tS) * 8); bw, bh = int(520 * pulse), int(120 * pulse)
            d.rounded_rectangle((540 - bw / 2, 680 - bh / 2, 540 + bw / 2, 680 + bh / 2), radius=60, fill=fade((230, 30, 40), k)); d.text((540, 680), "SUBSCRIBE", font=FI(64), fill=fade(WH, k), anchor="mm")
            for j, ic in enumerate(ICONS):
                a = ic.copy(); a.putalpha(a.getchannel("A").point(lambda v: int(v * k))); im.alpha_composite(a, (250 + j * 100, 790))
            d = ImageDraw.Draw(im); d.text((560, 832), "@vibewithamitai", font=FD(44), fill=fade(PK, k), anchor="lm")
        txt(d, (W / 2, 960), "Share with an engineer friend", FD(42), GY, t, t0 + 2.6)
        txt(d, (W / 2, 1060), "Build it. Test it. Ship it.", FD(58), CY, t, t0 + 5.4)
        bscale = 1.0; mood = "happy" if t > t0 + 5.4 else "norm"
    # Bit
    r = bitimg(f, mood)
    if bscale != 1.0: r = r.resize((int(r.width * bscale), int(r.height * bscale)), Image.LANCZOS)
    bob = int(10 * math.sin(t * 2 * math.pi * .6))
    im.alpha_composite(r, (W // 2 - r.width // 2 + shake, H - r.height + 20 + bob))
    if PREVIEW: im.convert("RGB").save(f"prev_{t:.1f}.png")
    else: ff.stdin.write(im.convert("RGB").tobytes())
if ff: ff.stdin.close(); ff.wait()
print("T", [round(x, 2) for x in T], "DUR", round(DUR, 1))
