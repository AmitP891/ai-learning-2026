"""Long-form: How I make faceless YouTube videos with code. 1920x1080, 30 fps."""
import re, io, sys, math, wave, subprocess, numpy as np, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080; FPS = 30; SR = 44100; GAP = 0.35
REPO = "/home/claude/ai-learning-2026"
def load(fn, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", fn, "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768
lines = [load(f"l{i:02d}.wav") for i in range(1, 24)]
T = []; t = 0.0
for a in lines: T.append(t); t += len(a) / SR + GAP
E = [T[i] + len(lines[i]) / SR for i in range(23)]
DUR = E[-1] + 1.8; N = int(DUR * FPS); hop = SR // FPS
voice = np.zeros(int(DUR * SR) + SR, np.float32)
for s, a in zip(T, lines): i = int(s * SR); voice[i:i + len(a)] += a
rms = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2)) for i in range(N)])
env = np.clip((rms - 0.01) / (np.percentile(rms[rms > 0.01], 90) - 0.01), 0, 1); env = np.convolve(env, [.25, .5, .25], "same")

CY = (0, 240, 255); PK = (240, 53, 158); GR = (57, 255, 136); RD = (255, 70, 90); WH = (255, 255, 255); GY = (160, 165, 185); BG = (13, 13, 20); YL = (255, 214, 0); PANEL = (20, 22, 34)
FD = lambda s, w="DejaVuSans-Bold": ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{w}.ttf", s)
FI = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", s)
MONO = FD(30, "DejaVuSansMono"); MONOB = lambda s: FD(s, "DejaVuSansMono-Bold"); MONOR = lambda s: FD(s, "DejaVuSansMono")
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

SVG = open(f"{REPO}/brand/bit/bit.svg").read()
svg = re.sub(r'<g id="eyes">.*?</g>', '', SVG, flags=re.S); svg = re.sub(r'<path id="mouth"[^>]*/>', '', svg)
def png(s, w=600, h=700): return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=s.encode(), output_width=w, output_height=h))).convert("RGBA")
BASE = png(svg)
head, body = svg.split(">", 1); body = body.rsplit("</svg>", 1)[0]
elems = re.findall(r'(<g[^>]*>.*?</g>|<[a-z]+[^>]*/>|<text[^>]*>.*?</text>)', body, flags=re.S)
ASM = [png(head + ">" + "".join(elems[:k]) + "</svg>") for k in range(len(elems) + 1)]
CODE = [l.strip() for l in SVG.splitlines() if l.strip()]
BUILDSRC = [l.rstrip() for l in open(f"{REPO}/brand/motion/bit-level-1/build_longform.py").read().splitlines() if l.strip()][:400]
def bitimg(f, mood="norm", talk=True, a=None):
    r = BASE.copy(); d = ImageDraw.Draw(r); a = (env[min(f, N - 1)] if talk else 0) if a is None else a
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
    if a > 0.08: h = 8 + 38 * a; d.rounded_rectangle((mx - 28, my - h / 2, mx + 28, my + h / 2), radius=int(min(h, 56) / 2), fill=CY)
    else: d.arc((mx - 40, my - 40, mx + 40, my + 12), 25, 155, fill=CY, width=9)
    return r
def sc(im, s): return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
src = open(f"{REPO}/brand/video-template/build_mcp_video.py").read(); ns = {"Image": Image, "ImageDraw": ImageDraw, "ImageFont": ImageFont}
exec(src[src.index("def yt_icon"):src.index("YT=yt_icon")], ns); exec(src[src.index("def tt_icon"):src.index("TT=tt_icon")], ns)
ICONS = [ns["tt_icon"](84), ns["yt_icon"](84), ns["ig_icon"](84)]

class Clip:
    def __init__(self, fn, t0, t1, n, size):
        self.size = size; self.last = None
        vf = [f"setpts=(PTS-STARTPTS)*{n / FPS / max(0.01, t1 - t0):.6f}", f"fps={FPS}", f"scale={size[0]}:{size[1]}:flags=lanczos"]
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-threads", "2", "-ss", str(t0), "-t", str(t1 - t0), "-i", fn, "-vf", ",".join(vf), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    def get(self):
        b = self.p.stdout.read(self.size[0] * self.size[1] * 3)
        if len(b) == self.size[0] * self.size[1] * 3: self.last = Image.frombytes("RGB", self.size, b)
        return self.last if self.last else Image.new("RGB", self.size)
    def close(self): self.p.kill(); self.p.wait()
clips = {}; CLIP_LINE = {}
def clip(key, line, *a, **k):
    if key not in clips: clips[key] = Clip(*a, **k); CLIP_LINE[key] = line
    return clips[key].get()
def nfr(i): return max(2, int((E[i] - T[i] + GAP) * FPS) + 2)
def panel(im, img, x, y, k=1.0, border=CY, r=18):
    w, h = img.size; m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=int(255 * k))
    im.paste(img, (x, y), m); d = ImageDraw.Draw(im); d.rounded_rectangle((x - 3, y - 3, x + w + 2, y + h + 2), radius=r + 2, outline=fade(border, k), width=3)
    return d
def headline(d, t, t0, a, b=None, ca=WH, cb=CY):
    txt(d, (60, 92), a, FI(64), ca, t, t0)
    if b: txt(d, (60 + d.textlength(a + "  ", font=FI(64)), 92), b, FI(64), cb, t, t0 + .2)

V = f"{REPO}/content/videos"
MONTAGE = [(f"{V}/2026-10-22-meet-bit.mp4", 11), (f"{V}/2026-10-mcp-v2-crashed-on-camera.mp4", 0.5), (f"{V}/2026-11-08-vague-req-02-sunlight.mp4", 8), (f"{REPO}/brand/motion/bit-level-1/out/teaser_9x16.mp4", 13)]
TEASE16 = f"{REPO}/brand/motion/bit-level-1/out/teaser_16x9.mp4"
CHAPTERS = {3: (1, "The character"), 6: (2, "The voice"), 9: (3, "Lip-sync"), 11: (4, "The scenes"), 15: (5, "Where Claude comes in"), 18: (6, "Honest numbers")}
LABELS = ["// no camera", "// meet Bit", "// hi, I'm Amit", "", "// bit.svg", "// expressions", "", "// the voice", "// auto-split", "", "// lip-sync", "", "// frames", "// sound", "// render", "", "// the loop", "// critique", "", "// the numbers", "// pros & cons", "// try it", "// your turn"]
R1 = [("Hook", 3, 8), ("Readability", 6, 8), ("Beat sync", 8, 9), ("On-model", 7, 8), ("Game feel", 6, 8), ("Ending", 6, 8)]
# whole-file waveform for the auto-split scene
VO_ALL = load("vo.mp3", 8000); WAVE_N = 1400
wseg = np.array_split(np.abs(VO_ALL), WAVE_N); WAVE = np.array([s.max() if len(s) else 0 for s in wseg]); WAVE /= WAVE.max()
CUTS = __import__("json").load(open("cuts.json"))["cuts"]; VDUR = len(VO_ALL) / 8000

# sfx
tt = np.arange(len(voice)) / SR; sfx = np.zeros_like(voice)
def tone(t0, fr, d=.12, dec=25, amp=.06):
    i = int(t0 * SR); n = int(d * SR); s = np.sin(2 * np.pi * fr * tt[:n]) * np.exp(-tt[:n] * dec) * amp; sfx[i:i + n] += s[:len(sfx) - i]
for li in CHAPTERS: tone(T[li] + .05, 520, .25, 10, .08); tone(T[li] + .15, 780, .3, 10, .07)
for j in range(len(elems)): tone(T[4] + .5 + j * .3, 900 + j * 40, .05, 40, .04)
for j in range(22): tone(T[8] + .8 + j * (E[8] - T[8] - 1.2) / 22, 1200, .03, 60, .04)
tone(T[13] + .4, 880, 1.2, 1.5, .07)
for j in range(4): tone(T[16] + .4 + j * 1.6, 660 + j * 110, .15, 15, .06)
for j in range(6): tone(T[17] + .6 + j * .3, 880 + j * 80, .08, 30, .05)
tease = load(TEASE16); bi = int(T[0] * SR); bed = tease[int(13 * SR):int(13 * SR) + int((E[0] - T[0] + .3) * SR)] * .22; voice[bi:bi + len(bed)] += bed
mix = np.clip((voice + sfx) * 0.9, -1, 1)[:int(DUR * SR)]
with wave.open("audio.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())

PREVIEW = [float(x) for x in sys.argv[1:]]
OUT = "faceless-youtube-with-code.mp4"
ff = None if PREVIEW else subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "audio.wav", "-c:v", "libx264", "-threads", "3", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], stdin=subprocess.PIPE)
for f in ([int(p * FPS) for p in PREVIEW] if PREVIEW else range(N)):
    t = f / FPS; li = max(i for i in range(23) if t >= T[i] - GAP / 2 or i == 0); lt = t - T[li]; L = E[li] - T[li]; p = lt / L
    for k_ in list(clips):
        if CLIP_LINE[k_] != li: clips[k_].close(); del clips[k_]
    im = grid.copy(); d = ImageDraw.Draw(im); show_bit = True; mood = "norm"; bit_xy = None; bit_s = 0.55
    if li in CHAPTERS:
        n_, name = CHAPTERS[li]; show_bit = True
        k = ease(lt / .35)
        d.text((W / 2, 360 + 30 * (1 - k)), f"STEP {n_}", font=FI(70), fill=fade(PK, k), anchor="mm")
        d.text((W / 2, 500 + 30 * (1 - k)), name.upper(), font=FI(140), fill=fade(WH, k), anchor="mm")
        for j in range(6): d.rounded_rectangle((W / 2 - 170 + j * 60, 640, W / 2 - 130 + j * 60, 652), radius=6, fill=PK if j < n_ else (40, 42, 60))
    elif li == 0:
        show_bit = False
        txt(d, (W / 2, 70), "NO CAMERA · NO FACE · NO EDITOR", FI(72), WH, t, 0, anchor="ma")
        for j, (fn, s0) in enumerate(MONTAGE):
            fr = clip(f"m{j}", 0, fn, s0, s0 + 5.5, nfr(0), size=(360, 640)); panel(im, fr, 120 + j * 440, 200, 1, [PK, RD, CY, YL][j], 24)
        d = ImageDraw.Draw(im)
    elif li == 1:
        bit_s = 1.1; bit_xy = (W // 2 - 330, 230); mood = "happy" if p > .7 else "norm"
        if t > T[1] + .6:
            k = ease((t - T[1] - .6) / .25); s = 1 + .5 * (1 - k); st = Image.new("RGBA", (W, H)); sd = ImageDraw.Draw(st)
            sd.rounded_rectangle((1220, 250, 1780, 400), radius=20, outline=PK + (int(255 * k),), width=10); sd.text((1500, 325), "100% CODE", font=FI(int(80 * s)), fill=PK + (int(255 * k),), anchor="mm")
            im.alpha_composite(st.rotate(-8, center=(1500, 325))); d = ImageDraw.Draw(im)
        txt(d, (1500, 560), "2,000", FI(120), CY, t, T[1] + L * .65, anchor="ma"); txt(d, (1500, 700), "views in 2 weeks", FD(44), WH, t, T[1] + L * .7, anchor="ma")
    elif li == 2:
        bit_s = 1.0; bit_xy = (150, 330)
        if card(d, (820, 300, 1840, 760), PK, t, T[2] + .3):
            txt(d, (870, 340), "AMIT", FI(110), WH, t, T[2] + .3); txt(d, (870, 480), "Systems engineer", FD(48), CY, t, T[2] + 1.0)
            txt(d, (870, 545), "not a video editor", FD(48), CY, t, T[2] + 1.6); txt(d, (870, 650), "@vibewithamitai", FD(40), PK, t, T[2] + 2.2)
        txt(d, (870, 820), "The whole pipeline, built with Claude.", FD(44), YL, t, T[2] + L * .55)
    elif li == 4:
        show_bit = False; headline(d, t, T[4], "Bit is an", "SVG file")
        card(d, (60, 200, 1080, 1000), CY, t, T[4])
        n = int(min(len(CODE), lt * 5)); vis = CODE[max(0, n - 18):n]
        for j, l in enumerate(vis): d.text((90, 230 + j * 42), (l[:62] + "…") if len(l) > 63 else l, font=MONOR(26), fill=(200, 205, 220))
        k = int(min(len(elems), max(0, (lt - .5) / .3))); im.alpha_composite(sc(ASM[k] if k < len(elems) else bitimg(f, "happy", talk=False), 1.15), (1160, 190)); d = ImageDraw.Draw(im)
    elif li == 5:
        headline(d, t, T[5], "Eyes and mouth:", "drawn by code")
        moods = [("idle", "norm2"), ("blink", "blink"), ("happy", "happy"), ("shock", "shock"), ("determined", "det"), ("hit", "hit")]
        for j, (nm, md) in enumerate(moods):
            t0 = T[5] + .2 + j * .35; x = 60 + (j % 3) * 400; y = 220 + (j // 3) * 400
            if card(d, (x, y, x + 370, y + 370), CY, t, t0, w=3):
                b = sc(bitimg(f, "norm" if md == "norm2" else md, talk=False), .45); im.alpha_composite(b, (x + 50, y + 10)); d = ImageDraw.Draw(im)
                txt(d, (x + 185, y + 325), nm, FD(30), WH, t, t0, anchor="ma")
    elif li == 7:
        headline(d, t, T[7], "The voice:", "my own, cloned")
        if card(d, (60, 220, 620, 760), GY, t, T[7] + .2):
            txt(d, (90, 245), "script.txt", MONOB(30), YL, t, T[7] + .2)
            for j, l in enumerate(["Every video on this", "channel was made…", "", "This is Bit. He's a", "drawing made of code…", "", "I'm Amit. I'm a", "systems engineer…"]): txt(d, (90, 310 + j * 50), l, MONOR(30), (200, 205, 220), t, T[7] + .3 + j * .1)
        txt(d, (700, 470), "→", FI(100), WH, t, T[7] + L * .4)
        if card(d, (820, 220, 1840, 760), PK, t, T[7] + L * .45):
            txt(d, (850, 245), "my cloned voice", MONOB(30), PK, t, T[7] + L * .45)
            k = ease((lt - L * .45) / .8); i0 = int(T[7] * SR)
            seg = voice[i0:i0 + int(6 * SR)]; seg = seg[::max(1, len(seg) // 900)][:int(900 * k)]
            pts = [(880 + j, 500 - int(seg[j] * 700)) for j in range(len(seg))]
            if len(pts) > 1: d.line(pts, fill=PK, width=3)
    elif li == 8:
        headline(d, t, T[8], "Auto-split", "at the pauses")
        x0, x1, y0 = 80, 1840, 560
        for j in range(WAVE_N):
            x = x0 + (x1 - x0) * j / WAVE_N; h = WAVE[j] * 220; d.line((x, y0 - h, x, y0 + h), fill=(70, 74, 110))
        k = (lt - .8) / max(.1, L - 1.2)
        for j, c in enumerate(CUTS):
            if j / len(CUTS) <= k:
                x = x0 + (x1 - x0) * c / VDUR; d.line((x, y0 - 260, x, y0 + 260), fill=CY, width=3); d.polygon([(x - 10, y0 - 280), (x + 10, y0 - 280), (x, y0 - 260)], fill=CY)
        txt(d, (W / 2, 860), f"{int(min(23, max(0, k) * 23 + 1))} lines → {int(min(23, max(0, k) * 23 + 1))} scenes", FI(56), YL, t, T[8] + .8, anchor="ma")
        show_bit = False
    elif li == 10:
        headline(d, t, T[10], "No AI lip-sync.", "Just loudness.")
        b = sc(bitimg(f), 1.0); im.alpha_composite(b, (1200, 300)); d = ImageDraw.Draw(im); show_bit = False
        card(d, (60, 260, 1100, 900), CY, t, T[10])
        i0 = int(t * SR); seg = voice[max(0, i0 - int(1.5 * SR)):i0]
        if len(seg) > 10:
            seg = seg[::max(1, len(seg) // 960)][:960]; d.line([(100 + j, 500 - int(seg[j] * 600)) for j in range(len(seg))], fill=CY, width=3)
        lv = env[min(f, N - 1)]; d.rectangle((100, 760, 100 + int(960 * lv), 820), fill=PK); d.rectangle((100, 760, 1060, 820), outline=(60, 64, 90), width=3)
        d.text((100, 710), "loudness, 30× a second  →  mouth size", font=FD(32), fill=GY)
    elif li == 12:
        headline(d, t, T[12], "Every scene is", "Python drawing frames")
        card(d, (60, 200, 860, 1000), CY, t, T[12])
        n = int(min(len(BUILDSRC), lt * 9)); vis = BUILDSRC[max(0, n - 19):n]
        for j, l in enumerate(vis): d.text((85, 225 + j * 40), (l[:52] + "…") if len(l) > 53 else l, font=MONOR(24), fill=(200, 205, 220))
        fr = clip("bf", 12, TEASE16, 10, 17.5, nfr(12), size=(480, 270))
        for j in range(9):
            x = 920 + (j % 3) * 330; y = 200 + (j // 3) * 200
            if lt > j * .25: im.paste(fr.resize((310, 175)), (x, y))
        d = ImageDraw.Draw(im); cnt = min(2000, int(lt / L * 2000)); txt(d, (1400, 830), f"frame {cnt:,} / ~2,000", FI(56), PK, t, T[12] + .3, anchor="ma")
        show_bit = False
    elif li == 13:
        headline(d, t, T[13], "Even the sound", "is code")
        card(d, (60, 260, 1400, 760), CY, t, T[13]); ph = t * 6
        d.line([(100 + x, 510 - int(160 * math.sin(x / 40 + ph))) for x in range(0, 1260, 4)], fill=CY, width=6)
        txt(d, (730, 800), "beep = sin(2π · 880 · t)", MONOB(48), YL, t, T[13] + .6, anchor="ma")
    elif li == 14:
        headline(d, t, T[14], "ffmpeg:", "frames + voice → MP4")
        card(d, (60, 220, 1400, 820), GR, t, T[14], fill=(8, 14, 12))
        cmd = "$ ffmpeg -f rawvideo -i - -i voice.wav -c:v libx264 out.mp4"; n = int(min(len(cmd), lt / .03))
        d.text((90, 260), cmd[:n], font=MONOR(28), fill=GR)
        if lt > 2.2:
            k = min(1, (lt - 2.2) / max(.5, L - 3)); fr_ = int(k * 2000)
            d.text((90, 340), f"frame={fr_:5d} fps=120 size={int(k*48000):6d}kB time=00:01:{int(k*7):02d}", font=MONOR(28), fill=(200, 205, 220))
            d.rectangle((90, 420, 1370, 470), outline=GR, width=3); d.rectangle((96, 426, 96 + int(1268 * k), 464), fill=GR)
            if k >= 1: d.text((90, 520), "✓ out.mp4 written", font=MONOB(34), fill=GR)
        txt(d, (60, 880), "No timeline. No dragging clips around.", FD(46), YL, t, T[14] + L * .55)
    elif li == 16:
        headline(d, t, T[16], "The loop", "like a design review")
        steps = [("1", "I describe", "the video"), ("2", "Claude writes", "+ runs code"), ("3", "Render", "MP4"), ("4", "I review", "it")]
        for j, (n_, a, b) in enumerate(steps):
            t0 = T[16] + .3 + j * L * .18; x = 60 + j * 345
            if card(d, (x, 300, x + 305, 600), [CY, PK, YL, GR][j], t, t0):
                txt(d, (x + 152, 330), n_, FI(80), [CY, PK, YL, GR][j], t, t0, anchor="ma"); txt(d, (x + 152, 450), a, FD(36), WH, t, t0, anchor="ma"); txt(d, (x + 152, 500), b, FD(32), GY, t, t0, anchor="ma")
            if j < 3 and t > t0 + .3: d.text((x + 325, 450), "›", font=FI(70), fill=GY, anchor="mm")
        if t > T[16] + L * .75:
            k = ease((t - T[16] - L * .75) / .4); d.arc((420, 560, 1100, 820), 10, 170, fill=fade(RD, k), width=6)
            d.text((760, 830), "wrong? say what → it fixes it", font=FD(40), fill=fade(RD, k), anchor="ma")
    elif li == 17:
        headline(d, t, T[17], "Bigger pieces:", "a brief + self-scoring")
        for j, (nm, s1, s2) in enumerate(R1):
            y = 220 + j * 108; t0 = T[17] + .3 + j * .25
            if card(d, (60, y, 1240, y + 92), GR, t, t0, w=3):
                txt(d, (90, y + 20), nm, FD(44), WH, t, t0); txt(d, (820, y + 12), str(s1), FI(60), RD if s1 < 5 else YL, t, t0, anchor="ra")
                txt(d, (920, y + 12), "→", FI(60), GY, t, t0 + .2, anchor="ma"); k = ease((lt - .6 - j * .25) / .6); v = round(s1 + (s2 - s1) * k)
                txt(d, (1200, y + 12), str(v), FI(60), GR if v >= 8 else YL, t, t0 + .3, anchor="ra")
        mood = "happy" if p > .6 else "norm"
    elif li == 19:
        headline(d, t, T[19], "Two weeks in")
        for j, (big, small, col) in enumerate([("2,000", "views", CY), ("10", "subscribers", PK), ("2", "weeks", YL)]):
            t0 = T[19] + .2 + j * .5; x = 60 + j * 470
            if card(d, (x, 200, x + 430, 470), col, t, t0):
                txt(d, (x + 215, 230), big, FI(130), col, t, t0, anchor="ma"); txt(d, (x + 215, 400), small, FD(40), WH, t, t0, anchor="ma")
        t0 = T[19] + L * .55
        if card(d, (60, 520, 1400, 960), GY, t, t0):
            txt(d, (90, 545), "Average views per Short (as of 28 Oct)", FD(34), GY, t, t0)
            for j, (nm, v, col) in enumerate([("Bit presents", 343, PK), ("Plain screen recording", 160, GY)]):
                y = 640 + j * 150; k = ease((t - t0 - .3 - j * .3) / .6)
                d.text((90, y), nm, font=FD(36), fill=WH); d.rounded_rectangle((540, y - 6, 540 + int(780 * v / 343 * k), y + 60), radius=10, fill=col)
                if k > .9: d.text((550 + int(780 * v / 343), y + 2), str(v), font=FI(48), fill=WH)
    elif li == 20:
        headline(d, t, T[20], "The honest", "trade-off")
        pros = ["Never film", "Every video on-brand", "Changes = 10 s re-render"]; cons = ["Setup took real time", "Only as good as the script"]
        if card(d, (60, 210, 730, 840), GR, t, T[20]):
            txt(d, (90, 235), "UPSIDE", FI(50), GR, t, T[20])
            for j, s in enumerate(pros): txt(d, (90, 340 + j * 110), "✓  " + s, FD(36), WH, t, T[20] + .4 + j * L * .12)
        t0 = T[20] + L * .55
        if card(d, (770, 210, 1440, 840), RD, t, t0):
            txt(d, (800, 235), "DOWNSIDE", FI(50), RD, t, t0)
            for j, s in enumerate(cons): txt(d, (800, 340 + j * 110), "✗  " + s, FD(36), WH, t, t0 + .4 + j * L * .12)
    elif li == 21:
        headline(d, t, T[21], "Want to try it?")
        for j, (n_, s) in enumerate([("1", "Start with one character"), ("2", "Keep it simple"), ("3", "Let the voice carry it")]):
            y = 250 + j * 200; t0 = T[21] + L * (.15 + j * .25)
            if card(d, (60, y, 1400, y + 170), [CY, PK, GR][j], t, t0):
                txt(d, (110, y + 40), n_, FI(90), [CY, PK, GR][j], t, t0); txt(d, (230, y + 55), s, FD(54), WH, t, t0)
    else:
        t0 = T[22]
        txt(d, (W / 2 - 160, 140), "The pipeline is free", FI(84), GR, t, t0, anchor="ma")
        if card(d, (180, 270, 1440, 470), GR, t, t0 + .2, fill=(12, 26, 20), w=5):
            txt(d, (810, 300), "★  GitHub", FI(60), WH, t, t0 + .2, anchor="ma"); txt(d, (810, 390), "AmitP891/ai-learning-2026  ·  brand/", FD(40, "DejaVuSansMono-Bold"), GR, t, t0 + .2, anchor="ma")
        tS = t0 + L * .35
        if t >= tS:
            k = ease((t - tS) / .35); pulse = 1 + 0.04 * math.sin((t - tS) * 8); bw, bh = int(520 * pulse), int(120 * pulse)
            d.rounded_rectangle((810 - bw / 2, 600 - bh / 2, 810 + bw / 2, 600 + bh / 2), radius=60, fill=fade((230, 30, 40), k)); d.text((810, 600), "SUBSCRIBE", font=FI(64), fill=fade(WH, k), anchor="mm")
            for j, ic in enumerate(ICONS):
                a = ic.copy(); a.putalpha(a.getchannel("A").point(lambda v: int(v * k))); im.alpha_composite(a, (520 + j * 100, 700))
            d = ImageDraw.Draw(im); d.text((830, 742), "@vibewithamitai", font=FD(44), fill=fade(PK, k), anchor="lm")
        txt(d, (810, 860), "Share with someone who wants a faceless channel", FD(36), GY, t, t0 + L * .5, anchor="ma")
        txt(d, (810, 940), "Build it. Test it. Ship it.", FD(58), CY, t, t0 + L * .82, anchor="ma"); mood = "happy" if p > .8 else "norm"
    if li not in CHAPTERS and LABELS[li]:
        d.text((60, 30), LABELS[li], font=MONO, fill=CY)
    if li != 0: d.text((W - 60, 30), f"{int(t // 60)}:{int(t % 60):02d}", font=MONO, fill=(60, 64, 90), anchor="ra")
    if show_bit:
        r = sc(bitimg(f, mood), bit_s); bob = int(8 * math.sin(t * 2 * math.pi * .6))
        x, y = bit_xy if bit_xy else (W - r.width - 40, H - r.height + 10)
        im.alpha_composite(r, (x, y + bob))
    if PREVIEW: im.convert("RGB").save(f"pv_{t:.1f}.png")
    else: ff.stdin.write(im.convert("RGB").tobytes())
for c in clips.values(): c.close()
if ff: ff.stdin.close(); ff.wait()
print("T", [round(x, 1) for x in T], "DUR", round(DUR, 1))
