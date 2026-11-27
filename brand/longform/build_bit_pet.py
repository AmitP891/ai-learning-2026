"""Long-form: 'I Asked Claude to Turn My Robot Into a Pet. Then I Abandoned Him.' 1920x1080, 30 fps.
Narrator: Amit (ElevenLabs). Result first, setup under 15 s, verdict inside the payoff (79 Skills retention lesson).
Usage: python3 build_bit_pet.py WORK_DIR OUT.mp4
WORK_DIR holds: vo/amit_vo.mp3, vo/words.json, vo/lines.txt (from the pocketsphinx alignment), cap/*.mp4 (headless captures
of the fixed build), bitpet-24h.mov (Amit's real 24 h check-in), h1.png (Amit's real 1 h screenshot)."""
import os, re, json, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
W, H, FPS, SR = 1920, 1080, 30, 44100
F = "/usr/share/fonts/opentype/inter/"
BK = lambda s: ImageFont.truetype(F + "InterDisplay-Black.otf", s)
BI = lambda s: ImageFont.truetype(F + "InterDisplay-BlackItalic.otf", s)
BD = lambda s: ImageFont.truetype(F + "InterDisplay-Bold.otf", s)
MONO = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", s)
MONOR = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", s)
BANG = lambda s: ImageFont.truetype(os.path.join(ROOT, "brand/fonts/Bangers-Regular.ttf"), s)
PINK, LIME, CYAN, WHITE, RED, GOLD, INK, GREEN, LILAC, BLUE = (240, 53, 158), (57, 255, 136), (0, 240, 255), (255, 255, 255), (255, 70, 90), (255, 214, 80), (10, 11, 24), (40, 210, 110), (200, 150, 255), (150, 165, 255)
GREY = (170, 176, 200)
ease = lambda x: 1 - (1 - min(1, max(0, x))) ** 3
ENC = ["-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(FPS)]
def run(cmd): subprocess.run(cmd, check=True)

WORK, OUT = sys.argv[1], sys.argv[2]
VO = os.path.join(WORK, "vo/amit_vo.mp3"); REC = os.path.join(WORK, "bitpet-24h.mov"); CAP = os.path.join(WORK, "cap")
LINES = [l.strip() for l in open(os.path.join(WORK, "vo/lines.txt")) if l.strip()]
WORDS = json.load(open(os.path.join(WORK, "vo/words.json")))
VO_LEN = 168.12

# ---------- word timing ----------
NUM = {"twenty-four": "twenty four", "thirty-nine": "thirty nine", "ninety-three": "ninety three", "sixty-nine": "sixty nine", "ten-second": "ten second",
       "bug-catching": "bug catching", "one-line": "one line", "welcome-back": "welcome back"}
def norm(s):
    t = s.lower()
    for k, v in NUM.items(): t = t.replace(k, v)
    t = t.replace("p.m.", "p m").replace("a.m.", "a m").replace("usb", "u s b").replace("claude's", "claude").replace("maths", "math").replace("greyed", "grayed").replace("rebooted", "booted")
    return re.findall(r"[a-z']+", t)
OWN = []
for i, l in enumerate(LINES): OWN += [(i, w) for w in norm(l)]
LSTART = []
for i in range(len(LINES)):
    k = next(j for j, (o, _) in enumerate(OWN) if o == i); LSTART.append(WORDS[k][1] if k < len(WORDS) else 164.89)
LSTART[0] = 0.0
def wv(line, word, n=0):
    """VO time of the n-th occurrence of `word` in script line `line` (1-based)."""
    c = 0
    for j, (o, w) in enumerate(OWN):
        if o == line - 1 and w == word:
            if c == n: return WORDS[j][1] if j < len(WORDS) else LSTART[line - 1]
            c += 1
    raise KeyError((line, word, n))

# ---------- timeline: VO with a sting and two silent beats inserted ----------
STING, B2, B3, OUTRO = 3.0, 2.0, 5.0, 15.0
CUT1, CUT2, CUT3 = 15.45, 99.0, 109.75          # after line 4, after line 17, after line 19
def tl(v):
    if v < CUT1: return v
    if v < CUT2: return v + STING
    if v < CUT3: return v + STING + B2
    return v + STING + B2 + B3
END_VO = tl(VO_LEN); TOTAL = END_VO + OUTRO
def L(i): return tl(LSTART[i - 1])                         # video start of line i
def LE(i): return L(i + 1) if i < len(LINES) else END_VO   # video end of line i (next line's start)
def wt(line, word, n=0): return tl(wv(line, word, n)) - L(line)   # seconds into the line's scene

# scene list: (start, end, kind, source, ss)
SC = []
def add(a, b, kind, src=None, ss=0.0): SC.append((a, b, kind, src, ss))
add(0, L(2), "L1", "REC", 0.0)
add(L(2), L(3), "L2", "A_happy", 0.0)
add(L(3), L(4), "L3", "B_feed", 0.0)
add(L(4), CUT1, "L4", "A_happy", 1.0)
add(CUT1, CUT1 + STING, "STING")
add(CUT1 + STING, L(6), "L5", "A_happy", 0.0)
add(L(6), L(7), "L6", "H_start", 0.0)
add(L(7), L(8), "L7", "A_happy", 0.0)
add(L(8), L(9), "L8", None)
add(L(9), L(10), "L9", "B_feed", 0.3)
t10 = L(10); a10, b10 = t10 + wt(10, "sleep"), t10 + wt(10, "and", 0)
add(t10, a10, "L10a", "C_play", 0.4); add(a10, b10, "L10b", "E_sleep", 0.4); add(b10, L(11), "L10c", "D_bugs", 3.6)
add(L(11), L(12), "L11", "REC", 18.6)
add(L(12), L(13), "L12", "H_start", 0.0)
add(L(13), L(14), "L13", "H_start", 2.0)
add(L(14), L(15), "L14", None)
add(L(15), L(16), "L15", "H1")
add(L(16), L(17), "L16", None)
add(L(17), tl(CUT2 - 0.001) + 0.001, "L17", None)
add(tl(CUT2 - 0.001) + 0.001, L(18), "B2", "REC", 0.4)
add(L(18), L(19), "L18", "REC", 2.4)
add(L(19), tl(CUT3 - 0.001) + 0.001, "L19", "REC", 7.9)
add(tl(CUT3 - 0.001) + 0.001, L(20), "B3", "REC", 14.2)
add(L(20), L(21), "L20", "REC", 0.0)
add(L(21), L(22), "L21", None)
add(L(22), L(23), "L22", None)
add(L(23), L(24), "L23", "G_banner_wake", 0.8)
add(L(24), L(25), "L24", "A_happy", 0.0)
add(L(25), L(26), "L25", "B_feed", 0.3)
add(L(26), L(27), "L26", "C_play", 1.0)
add(L(27), END_VO, "L27", "A_happy", 0.0)
add(END_VO, TOTAL, "OUTRO")

# ---------- backgrounds ----------
CARD_X, CARD_Y, CARD_H = 1180, 40, 1000
def make_bg(path):
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H; d.line([(0, y), (W, y)], fill=(int(32 + 20 * t), int(18 + 6 * t), int(58 + 24 * t)))
    for x in range(0, W, 48):
        for y in range(0, H, 48): d.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(70, 50, 110))
    hz = 760
    for k in range(-14, 15): d.line([(W / 2 + k * 40, hz), (W / 2 + k * 260, H)], fill=(60, 50, 120), width=2)
    for j in range(8):
        y = hz + (H - hz) * (j / 8) ** 1.6; d.line([(0, y), (W, y)], fill=(60, 50, 120), width=2)
    glow = Image.new("RGB", (W, H)); ImageDraw.Draw(glow).ellipse((W - 900, -200, W + 200, 900), fill=(140, 40, 120))
    im = Image.blend(im, glow.filter(ImageFilter.GaussianBlur(160)), 0.25)
    im.save(path)

def card_frame(path):
    """Glow frame drawn behind the game card."""
    im = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(im)
    w = round(CARD_H * 692 / 1010); x0, y0 = CARD_X, CARD_Y
    d.rounded_rectangle((x0 - 10, y0 - 10, x0 + w + 10, y0 + CARD_H + 10), 34, fill=PINK + (150,))
    im = im.filter(ImageFilter.GaussianBlur(16)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((x0 - 6, y0 - 6, x0 + w + 6, y0 + CARD_H + 6), 30, outline=PINK + (255,), width=5)
    im.save(path)

def src_input(src, ss, dur):
    if src == "REC": return ["-ss", str(ss), "-t", str(dur + 1), "-i", REC], "crop=940:1372:1000:303,"
    if src == "H1": return ["-loop", "1", "-t", str(dur + 1), "-i", os.path.join(WORK, "h1.png")], "crop=940:1372:1000:300,"
    return ["-stream_loop", "-1", "-ss", str(ss), "-t", str(dur + 1), "-i", os.path.join(CAP, src + ".mp4")], ""

def scene(out, bg, frame, a, b, src, ss):
    dur = b - a
    if src is None:
        run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", str(dur), "-i", bg, *ENC, "-t", str(dur), out]); return
    ins, crop = src_input(src, ss, dur)
    fc = (f"[1:v]{crop}scale=-2:{CARD_H},setsar=1,fps={FPS},tpad=stop_mode=clone:stop_duration={dur + 1}[c];"
          f"[0:v][2:v]overlay=0:0[b];[b][c]overlay={CARD_X}:{CARD_Y}[v]")
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", str(dur), "-i", bg, *ins, "-loop", "1", "-t", str(dur), "-i", frame,
         "-filter_complex", fc, "-map", "[v]", "-an", "-t", str(dur), *ENC, out])

# ---------- drawing helpers ----------
def T(d, xy, s, f, fill, a=1.0, anchor="la", stroke=0, sf=INK):
    d.text(xy, s, font=f, fill=fill + (int(255 * a),), anchor=anchor, stroke_width=stroke, stroke_fill=sf + (int(255 * a),))
def pill(d, x, y, s, col, a, size=46, anchor="l", fg=INK):
    w = d.textlength(s, font=BD(size)) + 56; h = size + 30
    x0 = x if anchor == "l" else (x - w / 2 if anchor == "m" else x - w)
    d.rounded_rectangle((x0, y, x0 + w, y + h), h // 2, fill=col + (int(245 * a),)); T(d, (x0 + w / 2, y + h / 2), s, BD(size), fg, a, "mm")
def panel(d, box, a, col=CYAN):
    d.rounded_rectangle(box, 30, fill=(12, 10, 30, int(232 * a)), outline=col + (int(255 * a),), width=5)
def tick(d, cx, cy, r, a, col=GREEN):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col + (int(255 * a),))
    d.line([(cx - r * .45, cy), (cx - r * .1, cy + r * .38), (cx + r * .5, cy - r * .35)], fill=WHITE + (int(255 * a),), width=max(3, int(r / 4)), joint="curve")
def cross(d, cx, cy, r, a):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=RED + (int(255 * a),)); q = r * .4
    for s in (1, -1): d.line([(cx - q, cy - q * s), (cx + q, cy + q * s)], fill=WHITE + (int(255 * a),), width=max(3, int(r / 4)))
def title(d, xy, s, size, col, a, anchor="mm"):
    T(d, (xy[0] + 6, xy[1] + 8), s, BANG(size), (0, 0, 0), a * 0.55, anchor, 12, (0, 0, 0))
    T(d, xy, s, BANG(size), col, a, anchor, 12, (20, 10, 40))
def stamp(im, s, col, cx, cy, a, size=120, rot=-10):
    lay = Image.new("RGBA", (900, 300)); d = ImageDraw.Draw(lay)
    w = d.textlength(s, font=BK(size)); d.rounded_rectangle((450 - w / 2 - 30, 150 - size * .7, 450 + w / 2 + 30, 150 + size * .7), 20, outline=col + (int(255 * a),), width=12)
    T(d, (450, 150), s, BK(size), col, a, "mm"); lay = lay.rotate(rot, resample=Image.BICUBIC)
    im.alpha_composite(lay, (int(cx - 450), int(cy - 150)))

CODE_IMG = None
def code_strip():
    global CODE_IMG
    if CODE_IMG is None:
        src = open(os.path.join(ROOT, "builds/bit-pet/opus/index.html")).read().splitlines()
        f = MONOR(19); lh = 26; im = Image.new("RGBA", (1000, lh * len(src) + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for i, l in enumerate(src):
            s = l.replace("\t", "  ")[:80]; c = (200, 205, 230)
            if s.strip().startswith("//"): c = (120, 130, 160)
            elif re.search(r"\bfunction\b|\bconst\b|\blet\b|\breturn\b|\bif\b", s): c = (255, 150, 210)
            elif "<" in s and ">" in s: c = (120, 230, 255)
            d.text((60, 20 + i * lh), f"{i + 1:4d}", font=f, fill=(90, 90, 130)); d.text((130, 20 + i * lh), s, font=f, fill=c)
        CODE_IMG = im
    return CODE_IMG

TESTER = {k: Image.open(os.path.join(ROOT, f"builds/bit-pet/tester/{k}.png")).convert("RGB") for k in ("asleep", "lowpower", "mobile")}
CHECKS = ["Fresh load shows welcome banner", "FEED byte/cookie/usb: battery up", "FEED when full is refused", "PLAY starts mini-game", "PLAY raises fun",
          "SLEEP puts Bit to sleep", "Sleep need rises while asleep", "WAKE wakes Bit", "Glitch bugs appear when Clean low", "DEBUG: zap all bugs -> Clean 100",
          "24h gap: all needs 0 -> low power", "Feeding wakes Bit from low power", "7h gap wording", "State persists across reload", "Corrupt save recovers",
          "Mobile: touch on Bit pets him", "No console errors"]

# ---------- callouts ----------
def callouts(t):
    s = next((x for x in SC if x[0] <= t < x[1]), None)
    if s is None: return None
    a0, b0, kind = s[0], s[1], s[2]; u = t - a0; LL = b0 - a0
    k = lambda x, dur=0.35: ease((u - x) / dur)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if kind == "L1":
        title(d, (590, 300), "24 HOURS LATER", 150, GOLD, k(0.1))
        T(d, (590, 440), "I left him alone. On purpose.", BD(52), WHITE, k(wt(1, "after")), "mm", 6)
        if u > 0.6: pill(d, 590, 560, "BATTERY 0 · FUN 0 · SLEEP 0 · CLEAN 0", RED, k(0.6), 40, "m", WHITE)
    elif kind == "L2":
        im.paste((10, 6, 30, int(120 * (1 - ease(u / LL)))), (0, 0, W, H))
        for y in range(0, H, 6): d.line([(0, y), (W, y)], fill=(255, 255, 255, 18))
        T(d, (590, 470), "◀◀ REWIND", BK(120), WHITE, 1.0, "mm", 8)
        T(d, (590, 600), "WED 16:03", MONO(56), CYAN, 1.0, "mm")
    elif kind == "L3":
        for i, (w_, s_, c) in enumerate([("one", "1 PROMPT", CYAN), ("seven", "7 AI BOTS", LIME), ("thirteen", "13 MINUTES", GOLD)]):
            x = wt(3, w_)
            if u > x: pill(d, 90, 160 + i * 130, s_, c, k(x), 64)
        x = wt(3, "claude")
        if u > x: T(d, (90, 620), "Claude turned Bit into a", BD(54), WHITE, k(x)); title(d, (90, 720), "PET YOU CAN FEED", 120, PINK, k(x + 0.6), "lm")
    elif kind == "L4":
        T(d, (590, 430), "...and then I walked away.", BI(64), WHITE, k(0.2), "mm", 6)
        if u > wt(4, "to"): T(d, (590, 540), "Would he survive?", BD(56), GOLD, k(wt(4, "to")), "mm", 5)
        f = ease((u - (LL - 0.9)) / 0.8)
        if f > 0: im.paste((0, 0, 0, int(255 * f)), (0, 0, W, H)); T(d, (W / 2, H / 2), "TAB CLOSED", MONO(80), RED, f, "mm")
    elif kind == "STING":
        return None
    elif kind == "L5":
        a = k(0.2); panel(d, (60, 80, 1110, 1000), a, LIME); T(d, (100, 130), "THE PROMPT: A TEAM OF 7 BOTS", BD(40), LIME, a)
        roles = [("producer", "PRODUCER"), ("designer", "GAME DESIGNER"), ("artist", "ARTIST"), ("coder", "CODER"), ("sound", "SOUND DESIGNER"), ("tester", "TESTER"), ("hype", "HYPE BOT")]
        for i, (w_, r) in enumerate(roles):
            x = wt(5, w_); col = GOLD if r == "TESTER" else (PINK if r == "HYPE BOT" else LIME)
            if u > x:
                pill(d, 110, 210 + i * 102, f"{i + 1}. {r}", col, k(x), 44)
                if i < 6: T(d, (130 + d.textlength(f"{i + 1}. {r}", font=BD(44)) + 90, 248 + i * 102), "→", BK(44), WHITE, k(x), "lm")
        x = wt(5, "each")
        if u > x: T(d, (110, 945), "each one hands its work to the next", BI(40), CYAN, k(x), "lm")
    elif kind == "L6":
        cols = [("battery", "BATTERY", GOLD), ("fun", "FUN", LIME), ("sleep", "SLEEP", BLUE), ("clean", "CLEAN", LILAC)]
        T(d, (90, 150), "4 NEEDS", BK(90), WHITE, k(0.1), "la", 6)
        for i, (w_, s_, c) in enumerate(cols):
            x = wt(6, w_)
            if u > x: pill(d, 90 + (i % 2) * 430, 300 + (i // 2) * 130, s_, c, k(x), 60)
        x = wt(6, "they")
        if u > x: T(d, (90, 620), "Drain in real time…", BD(58), WHITE, k(x))
        x = wt(6, "even")
        if u > x: title(d, (90, 740), "EVEN WHEN THE TAB IS CLOSED", 84, RED, k(x), "lm")
        # arrow to the bars on the card
        if u > 0.5: d.line([(1110, 830), (1170, 830)], fill=GOLD + (int(255 * k(0.5)),), width=8); d.polygon([(1170, 815), (1195, 830), (1170, 845)], fill=GOLD + (int(255 * k(0.5)),))
    elif kind == "L7":
        a = k(0.1); panel(d, (60, 60, 1110, 1020), a, CYAN)
        c = code_strip(); off = int(u / LL * (c.height - 900))
        crop = c.crop((0, off, 1000, off + 900)); crop.putalpha(Image.eval(crop.getchannel("A"), lambda v: int(v * 0.55 * a)))
        im.alpha_composite(crop, (80, 90))
        for i, (w_, s_, c_) in enumerate([("no", "NO GAME ENGINE", RED), ("images", "NO IMAGES", RED), ("sound", "NO SOUND FILES", RED)]):
            x = wt(7, w_, 0 if w_ != "no" else 0)
            if w_ == "images": x = wt(7, "images")
            if u > x: pill(d, 100, 110 + i * 120, "✕  " + s_, c_, k(x), 54, fg=WHITE)
        x = wt(7, "every")
        if u > x: T(d, (100, 520), "Every pixel + every beep", BK(56), WHITE, k(x), "la", 5); T(d, (100, 590), "drawn in code", BK(56), CYAN, k(x + .3), "la", 5)
        x = wt(7, "one")
        if u > x:
            d.rounded_rectangle((100, 760, 1070, 960), 26, fill=(0, 0, 0, int(200 * k(x))), outline=GOLD + (int(255 * k(x)),), width=5)
            T(d, (585, 820), "index.html", MONO(60), GOLD, k(x), "mm")
            n = int(min(999, 999 * ease((u - wt(7, "nine")) / 1.6))) if u > wt(7, "nine") else 0
            T(d, (585, 905), f"{n} lines · 1 file", BK(56), WHITE, k(x), "mm")
    elif kind == "L8":
        a = k(0.1); panel(d, (60, 60, 940, 1020), a, GOLD); T(d, (100, 110), "TESTER BOT: 39 CHECKS", BD(42), GOLD, a)
        shown = int(len(CHECKS) * ease(u / (wt(8, "it") + 0.5)))
        for i, c in enumerate(CHECKS[:shown]):
            y = 180 + i * 46; tick(d, 115, y + 16, 15, 1.0); T(d, (145, y), c, BD(30), WHITE, 1.0)
        if u > wt(8, "found"):
            x = wt(8, "found"); pill(d, 1000, 110, "3 BUGS FOUND → FIXED", RED, k(x), 46, fg=WHITE)
        for i, key in enumerate(("asleep", "lowpower", "mobile")):
            if u > 0.6 + i * 0.4:
                p = TESTER[key]; s = 420 / p.height; p = p.resize((round(p.width * s), 420), Image.LANCZOS)
                x0 = 1000 + i * 290; d.rounded_rectangle((x0 - 6, 204, x0 + p.width + 6, 630), 16, fill=CYAN + (int(255 * k(0.6 + i * .4)),))
                im.paste(p, (x0, 210))
        x = wt(8, "retest")
        if u > x: T(d, (1400, 740), "39 / 39", BK(140), LIME, k(x), "mm", 8); tick(d, 1700, 740, 48, k(x))
        x = wt(8, "one", 0) if u > wt(8, "retest") else 999
        try: x = wt(8, "fix") - 0.2
        except KeyError: pass
        if u > x: pill(d, 1420, 830, "FIX ROUNDS: 1", GOLD, k(x), 50, "m")
        x = wt(8, "didn't")
        if u > x: pill(d, 1420, 940, "MY CORRECTIONS: 0", PINK, k(x), 50, "m", WHITE)
    elif kind == "L9":
        T(d, (90, 200), "FEED", BK(110), GOLD, k(0.1), "la", 6)
        for i, (w_, s_) in enumerate([("data", "DATA BYTE  +15"), ("cookie", "COOKIE  +25 · +FUN"), ("u", "USB STICK  +45")]):
            x = wt(9, w_)
            if u > x: pill(d, 90, 380 + i * 130, s_, GOLD, k(x), 56)
    elif kind in ("L10a", "L10b", "L10c"):
        lab = {"L10a": ("PLAY", "10-second bug-catching game", LIME), "L10b": ("SLEEP", "lights off", BLUE), "L10c": ("DEBUG", "zap the glitch bugs", LILAC)}[kind]
        T(d, (90, 380), lab[0], BK(140), lab[2], k(0.05, .25), "la", 7); T(d, (95, 560), lab[1], BD(54), WHITE, k(0.2, .25))
    elif kind == "L11":
        stamp(im, "BUG #1", RED, 1520, 150, k(wt(11, "they") + 0.3), 100, -8)
        T(d, (90, 380), "They crawl", BK(90), WHITE, k(0.1), "la", 6); T(d, (90, 490), "on his face.", BK(90), RED, k(0.4), "la", 6)
        x = wt(11, "that's")
        if u > x: T(d, (90, 660), "A bug about bugs.", BI(56), GOLD, k(x))
        x = wt(11, "we'll")
        if u > x: pill(d, 90, 780, "REMEMBER THIS ONE", WHITE, k(x), 44)
    elif kind == "L12":
        T(d, (90, 180), "THE TEST", BK(110), WHITE, k(0.1), "la", 7)
        x = wt(12, "four")
        if u > x: pill(d, 90, 360, "WED 16:03", CYAN, k(x), 60)
        x = wt(12, "filled")
        if u > x: pill(d, 90, 500, "BATTERY 100 · FUN 100", GOLD, k(x), 54)
        x = wt(12, "stopped")
        if u > x: title(d, (90, 720), "THEN: HANDS OFF", 110, RED, k(x), "lm")
    elif kind == "L13":
        a = k(0.1); panel(d, (60, 120, 1110, 960), a, GOLD); T(d, (100, 170), "DRAIN PER HOUR (from the code)", BD(42), GOLD, a)
        rows = [("battery", "BATTERY", "-10", GOLD), ("fun", "FUN", "-7", LIME), ("sleep", "SLEEP", "-5", BLUE), ("clean", "CLEAN", "-4", LILAC)]
        for i, (w_, n, v, c) in enumerate(rows):
            x = wt(13, w_, 0 if w_ != "battery" else 0)
            if w_ == "battery": x = wt(13, "battery")
            if u > x:
                y = 290 + i * 130; T(d, (120, y), n, BK(66), c, k(x)); T(d, (1040, y), v, BK(80), WHITE, k(x), "ra")
        x = wt(13, "so")
        if u > x: T(d, (585, 880), "→ we can predict his whole night", BI(46), CYAN, k(x), "mm")
    elif kind == "L14":
        a = k(0.1); title(d, (W / 2, 140), "THE FORECAST", 120, WHITE, a)
        d.line([(160, 560), (1760, 560)], fill=WHITE + (int(200 * a),), width=6)
        ev = [("glitch", "22:00", "GLITCH BUGS", LILAC, 380), ("battery", "02:00", "BATTERY EMPTY", GOLD, 900), ("low", "08:05", "LOW POWER MODE", RED, 1500)]
        for w_, tm, lab, c, x0 in ev:
            x = wt(14, w_)
            if u > x:
                b = k(x); d.ellipse((x0 - 26, 534, x0 + 26, 586), fill=c + (int(255 * b),))
                T(d, (x0, 470), tm, MONO(64), c, b, "mm"); pill(d, x0, 640, lab, c, b, 46, "m", INK if c != RED else WHITE)
        T(d, (160, 620), "WED 16:03", MONO(36), GREY, a, "la"); T(d, (1760, 620), "THU 16:16", MONO(36), GREY, a, "ra")
    elif kind == "L15":
        T(d, (90, 170), "1 HOUR LATER", BK(90), WHITE, k(0.1), "la", 6); T(d, (95, 280), "the real screenshot", BD(40), GREY, k(0.3))
        vals = [("ninety", "BATTERY", "100 → 90", "-10", GOLD), ("ninety", "FUN", "100 → 93", "-7", LIME), ("sixty", "SLEEP", "74 → 69", "-5", BLUE), ("sixty", "CLEAN", "64 → 60", "-4", LILAC)]
        wn = [wt(15, "ninety", 0), wt(15, "ninety", 1), wt(15, "sixty", 0), wt(15, "sixty", 1)]
        for i, (_, n, s_, dlt, c) in enumerate(vals):
            if u > wn[i]:
                y = 380 + i * 115; T(d, (100, y), n, BK(52), c, k(wn[i])); T(d, (420, y), s_, MONO(50), WHITE, k(wn[i])); tick(d, 900, y + 28, 30, k(wn[i] + 0.2))
        x = wt(15, "exactly")
        if u > x: title(d, (90, 900), "EXACTLY THE MATHS", 100, LIME, k(x), "lm")
    elif kind == "L16":
        f = ease(u / LL); im.paste((4, 3, 14, int(150 + 90 * f)), (0, 0, W, H))
        T(d, (W / 2, 420), "...nothing.", BI(90), WHITE, k(0.3), "mm")
        hh = (17 + int(u / LL * 14)) % 24
        T(d, (W / 2, 600), f"{hh:02d}:{int(u * 37) % 60:02d}", MONO(120), CYAN, k(0.1), "mm")
        T(d, (W / 2, 720), "all night", BD(44), GREY, k(1.0), "mm")
    elif kind == "L17":
        im.paste((0, 0, 0, 255), (0, 0, W, H))
        title(d, (W / 2, 470), "24 HOURS LATER", 190, GOLD, k(0.05))
        T(d, (W / 2, 640), "THU 16:16", MONO(70), CYAN, k(0.4), "mm")
    elif kind == "B2":
        pill(d, 90, 120, "MY REAL CHECK-IN", CYAN, k(0.1), 46)
        T(d, (90, 500), "...zz... sys... halt...", MONO(52), GREY, k(0.6), "lm")
    elif kind == "L18":
        pill(d, 90, 120, "MY REAL CHECK-IN", CYAN, 1.0, 46)
        for i, (w_, s_, c) in enumerate([("every", "EVERY BAR: 0", RED), ("grayed", "GREYED OUT", GREY)]):
            x = wt(18, w_)
            if u > x: pill(d, 90, 280 + i * 130, s_, c, k(x), 58, fg=WHITE if c == RED else INK)
        x = wt(18, "but")
        if u > x: T(d, (90, 620), "…but he never dies.", BK(64), WHITE, k(x), "la", 6)
        x = wt(18, "you")
        if u > x: title(d, (90, 800), "JUST FEED HIM", 110, GOLD, k(x), "lm")
    elif kind == "L19":
        pill(d, 90, 120, "MY REAL CHECK-IN", CYAN, 1.0, 46)
        title(d, (90, 430), "HE'S BACK", 150, LIME, k(0.1), "lm")
        x = wt(19, "still")
        if u > x: T(d, (95, 600), "…still a little sad about it.", BI(52), WHITE, k(x))
    elif kind == "B3":
        pill(d, 90, 120, "EVERY SNACK LINE: WRITTEN BY CLAUDE", PINK, k(0.1), 42, fg=WHITE)
        for i, (x, s_) in enumerate([(0.6, "“Yum! ...crumbs in my vents”"), (2.0, "“Crunchy bits! 01101!”"), (3.4, "“Mmm, 64 gigs of flavor!”")]):
            if u > x: T(d, (95, 330 + i * 120), s_, BI(56), WHITE, k(x), "la", 5)
    elif kind == "L20":
        a = k(0.1); panel(d, (60, 120, 1110, 900), a, RED); T(d, (100, 170), "THE PROMPT ASKED FOR:", BD(42), RED, a)
        T(d, (100, 280), "“Show how long you were away", MONO(38), WHITE, k(wt(20, "the"))); T(d, (100, 340), "when you come back", MONO(38), WHITE, k(wt(20, "the")))
        T(d, (100, 420), "(\"You were gone 7 hours…\")”", MONO(38), GOLD, k(wt(20, "welcome")))
        x = wt(20, "it")
        if u > x: cross(d, 220, 640, 70, k(x)); T(d, (330, 640), "NEVER SHOWED UP", BK(66), RED, k(x), "lm")
    elif kind == "L21":
        a = k(0.1); panel(d, (60, 60, 1860, 1020), a, CYAN); T(d, (100, 105), "SO I CHECKED THE CODE", BD(42), CYAN, a)
        code1 = ["// page loads fresh", "function adopt(save) {", "  const away = now - save.t;", "  simulate(save, away);", "  if (away >= 60000)", "    showBanner('You were gone…');", "}"]
        code2 = ["// tab left open: runs every second", "function tick() {", "  simulate(S, now - S.t);", "  S.t = now;", "  save();", "  // no banner here", "}"]
        x1, x2 = wt(21, "the", 0), wt(21, "i'd")
        for i, l in enumerate(code1): T(d, (110, 200 + i * 54), l, MONO(36), (120, 130, 160) if l.startswith("//") else WHITE, k(x1 + i * .15))
        if u > wt(21, "page"): tick(d, 860, 200 + 5 * 54 + 22, 30, k(wt(21, "page")))
        for i, l in enumerate(code2): T(d, (990, 200 + i * 54), l, MONO(36), (120, 130, 160) if l.startswith("//") else WHITE, k(x2 + i * .15))
        x = wt(21, "caught")
        if u > x: cross(d, 1700, 200 + 5 * 54 + 22, 30, k(x)); pill(d, 990, 640, "CAUGHT UP 24 H SILENTLY", GOLD, k(x), 40)
        x = wt(21, "message", 1)
        if u > x: T(d, (W / 2, 900), "The message never got its turn.", BK(64), RED, k(x), "mm", 6)
    elif kind == "L22":
        x = wt(22, "thirty")
        T(d, (W / 2, 220), "CLAUDE'S TESTS: ALWAYS RELOADED THE PAGE", BD(48), GREY, k(0.1), "mm")
        if u > x: T(d, (760, 450), "39 / 39", BK(200), LIME, k(x), "mm", 10); tick(d, 1260, 450, 80, k(x))
        x = wt(22, "real")
        if u > x: T(d, (760, 760), "REAL LIFE:  1", BK(140), RED, k(x), "mm", 8); cross(d, 1340, 760, 70, k(x))
        x = wt(22, "never")
        if u > x: T(d, (W / 2, 960), "the one case it never tried", BI(56), WHITE, k(x), "mm", 5)
    elif kind == "L23":
        stamp(im, "FIXED", LIME, 1520, 300, k(0.4), 130, -8)
        T(d, (90, 130), "A ONE-LINE FIX", BK(80), WHITE, k(0.1), "la", 6)
        items = [(0.3, "Banner when an open tab wakes up", LIME), (wt(23, "same"), "Bugs stay off his face", LIME), (wt(23, "math"), "The maths", CYAN),
                 (wt(23, "low"), "Low power", CYAN), (wt(23, "reboot"), "The reboot", CYAN), (wt(23, "every"), "Every snack line", CYAN)]
        ys = [300, 400, 590, 680, 770, 860]
        for i, (x, s_, c) in enumerate(items):
            if u > x: tick(d, 125, ys[i], 30, k(x), GREEN); T(d, (175, ys[i]), s_, BD(50), WHITE, k(x), "lm")
        if u > wt(23, "and"): T(d, (95, 500), "everything else worked:", BI(40), GREY, k(wt(23, "and")))
    elif kind == "L24":
        for i, (w_, s_, c) in enumerate([("thirteen", "13 MINUTES", GOLD), ("one", "1 PROMPT", CYAN), ("whole", "A WHOLE DAY ALONE", LIME)]):
            x = wt(24, w_)
            if u > x: pill(d, 90, 120 + i * 120, s_, c, k(x), 54)
        x = wt(24, "not", 0)
        if u > x: T(d, (90, 560), "not “does it run”…", BI(60), GREY, k(x), "la", 5)
        x = wt(24, "still")
        if u > x: title(d, (90, 700), "DOES IT STILL WORK", 100, WHITE, k(x), "lm"); title(d, (90, 820), "WHEN YOU'RE NOT LOOKING?", 100, GOLD, k(x + 0.3), "lm")
    elif kind == "L25":
        title(d, (90, 300), "ADOPT BIT", 150, PINK, k(0.1), "lm")
        x = wt(25, "link's")
        if u > x: pill(d, 90, 450, "LINK IN THE DESCRIPTION", CYAN, k(x), 54)
        x = wt(25, "full")
        if u > x: pill(d, 90, 580, "+ THE FULL PROMPT (FREE)", GOLD, k(x), 54)
    elif kind == "L26":
        T(d, (90, 300), "How long could YOU", BK(76), WHITE, k(0.1), "la", 6); T(d, (90, 400), "keep him alive?", BK(76), GOLD, k(0.3), "la", 6)
        x = wt(26, "be")
        if u > x: pill(d, 90, 560, "BE HONEST 👇", PINK, k(x), 54, fg=WHITE)
    elif kind == "L27":
        for i, (w_, s_, c) in enumerate([("build", "BUILD IT.", WHITE), ("test", "TEST IT.", CYAN), ("ship", "SHIP IT.", LIME), ("feed", "FEED IT.", PINK)]):
            x = wt(27, w_) if w_ != "feed" else wt(27, "and") + 0.25
            if u > x: title(d, (90, 230 + i * 170), s_, 140, c, k(x), "lm")
    else:
        return None
    return im

# ---------- outro (brand outro + watch-next card) ----------
def next_card(path):
    w, h = 819, 461; im = Image.new("RGB", (w, h)); d = ImageDraw.Draw(im)
    for y in range(h): d.line([(0, y), (w, y)], fill=(int(60 + 80 * y / h), 14, int(70 - 30 * y / h)))
    d.text((34, 40), "LAST WEEK", font=BD(40), fill=CYAN)
    d.text((34, 100), "79 GAME-DEV", font=BK(84), fill=WHITE, stroke_width=4, stroke_fill=INK)
    d.text((34, 200), "SKILLS", font=BK(84), fill=GOLD, stroke_width=4, stroke_fill=INK)
    d.text((36, 330), "Claude ignored them.", font=BD(40), fill=WHITE); d.text((36, 380), "So I made it use them.", font=BD(40), fill=PINK)
    im.save(path)

def sub_circle(path):
    D = 173; im = Image.new("RGBA", (D, D), (20, 20, 40, 255))
    p = Image.open(os.path.join(ROOT, "brand/photos/bit_painted_mockup.png")).convert("RGBA").crop((90, 30, 890, 830)).resize((D, D), Image.LANCZOS)
    im.alpha_composite(p); m = Image.new("L", (D * 4, D * 4), 0); ImageDraw.Draw(m).ellipse((0, 0, D * 4 - 1, D * 4 - 1), fill=255)
    im.putalpha(m.resize((D, D), Image.LANCZOS)); im.save(path)

def make_outro(tmp, out):
    card = os.path.join(tmp, "next.png"); next_card(card); circ = os.path.join(tmp, "circ.png"); sub_circle(circ)
    src = os.path.join(ROOT, "content/videos/brand-outro-15s.mp4"); cimg = Image.open(card).convert("RGB"); simg = Image.open(circ)
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *ENC, out], stdin=subprocess.PIPE)
    for i in range(int(OUTRO * FPS)):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        f = min(1.0, (i / FPS) / 0.4); fr = Image.frombuffer("RGB", (W, H), buf).copy()
        c = cimg if f >= 1 else Image.eval(cimg, lambda v: int(v * f))
        s = simg if f >= 1 else Image.merge("RGBA", [*Image.eval(simg.convert("RGB"), lambda v: int(v * f)).split(), simg.getchannel("A")])
        fr.paste(c, (116, 256)); fr.paste(s, (124, 774), s); enc.stdin.write(fr.tobytes())
    enc.stdin.close(); enc.wait(); dec.kill()

def main():
    tmp = tempfile.mkdtemp(); P = lambda n: os.path.join(tmp, n)
    bg = P("bg.png"); make_bg(bg); fr = P("frame.png"); card_frame(fr)
    parts = []
    for i, (a, b, kind, src, ss) in enumerate(SC):
        o = P(f"s{i:02d}.mp4")
        if kind == "STING": o = os.path.join(ROOT, "content/videos/brand-sting-3s.mp4")
        elif kind == "OUTRO": make_outro(tmp, o)
        else: scene(o, bg, fr, a, b, src, ss)
        parts.append((o, b - a))
    ins, fc = [], ""
    for i, (p, dur) in enumerate(parts):
        ins += ["-i", p]; fc += f"[{i}:v]scale={W}:{H},fps={FPS},format=yuv420p,setsar=1,trim=duration={dur:.4f},setpts=PTS-STARTPTS[v{i}];"
    base = P("base.mp4")
    run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc + "".join(f"[v{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0[v]", "-map", "[v]", *ENC, base])
    N = int(TOTAL * FPS); vid = P("v.mp4")
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium", vid], stdin=subprocess.PIPE)
    for i in range(N):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        c = callouts(i / FPS)
        if c is None: enc.stdin.write(buf); continue
        f_ = Image.frombuffer("RGB", (W, H), buf).convert("RGBA"); f_.alpha_composite(c); enc.stdin.write(f_.convert("RGB").tobytes())
    enc.stdin.close(); enc.wait(); dec.kill()
    # ---- audio: VO split at the three cuts, sting, synth bed, sfx, outro ----
    def pcm(p): return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout, np.int16).astype(float) / 32768
    n = int(TOTAL * SR); mix = np.zeros(n); v = pcm(VO)
    for a, b in [(0, CUT1), (CUT1, CUT2), (CUT2, CUT3), (CUT3, VO_LEN)]:
        seg = v[int(a * SR):int(b * SR)]; o = int(tl(a + 1e-6) * SR) if a else 0; mix[o:o + len(seg)] += seg[: n - o]
    st = pcm(os.path.join(ROOT, "content/videos/brand-sting-3s.mp4")); c1 = int(CUT1 * SR); mix[c1:c1 + len(st)] += st[: n - c1] * 0.8
    ou = pcm(os.path.join(ROOT, "content/videos/brand-outro-15s.mp4")); o0 = int(END_VO * SR); mix[o0:o0 + len(ou)] += ou[: n - o0] * 0.9
    tt = np.arange(n) / SR; beat = 60 / 100; bed = np.zeros(n)
    def env(s0, dd):
        e = np.zeros(n); i0 = int(s0 * SR)
        if 0 <= i0 < n: e[i0:] = np.exp(-np.arange(n - i0) / SR / dd)
        return e
    chords = [(261.6, 329.6, 392.0), (220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 246.9, 293.7)]
    for kk in range(int(TOTAL / (beat * 4)) + 1):
        for f in chords[kk % 4]: bed += 0.03 * np.sin(2 * np.pi * f * tt) * env(kk * beat * 4, 2.4)
    for kk in range(int(TOTAL / beat)):
        s0 = kk * beat
        if kk % 2 == 0: bed += 0.012 * np.sign(np.sin(2 * np.pi * [523.3, 659.3, 784.0, 659.3][(kk // 2) % 4] * tt)) * env(s0, .09)
        fr_ = 55 * 2 ** (-np.clip((tt - s0) * 30, 0, 3)); bed += 0.07 * np.sin(2 * np.pi * np.cumsum(fr_) / SR) * env(s0, .07) * (tt >= s0)
    gate = np.ones(n)
    def mute(a, b, lvl=0.0): gate[int(a * SR):int(b * SR)] = lvl
    mute(CUT1, CUT1 + STING); mute(L(16), L(18), 0.0); mute(L(18), L(19), 0.35); mute(END_VO, TOTAL)
    gate = np.convolve(gate, np.ones(9000) / 9000, mode="same"); mix += bed * gate
    noise = np.random.default_rng(7).uniform(-1, 1, n)
    for a, b, kind, *_ in SC:
        if kind not in ("STING", "OUTRO", "L10b", "L10c", "L18", "L19", "B3"): mix += 0.045 * noise * env(a, .11)
    def tone(t0, f0, f1, dur, vol):
        i0 = int(t0 * SR); m = int(dur * SR); x = np.arange(m) / SR; f = np.linspace(f0, f1, m)
        y = vol * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-x / (dur * 0.7)); mix[i0:i0 + m] += y[: n - i0]
    tone(L(2), 1200, 200, 0.9, 0.06)                     # rewind
    tone(tl(CUT2) + 0.3, 600, 90, 1.4, 0.07)            # power down
    tone(L(19) + 0.05, 220, 880, 0.5, 0.06); tone(L(19) + 0.55, 660, 1320, 0.35, 0.05)   # reboot chime
    for x in (0.6, 2.0, 3.4): tone(tl(CUT3) + 0.001 + x, 900, 500, 0.12, 0.05)          # snack blips
    mix = mix / np.max(np.abs(mix)) * 0.89; wav = P("a.wav")
    with wave.open(wav, "w") as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((mix * 32767).astype(np.int16).tobytes())
    run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", P("pre.mp4")])
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", P("pre.mp4"), "-af", "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    af = f"loudnorm=I=-14:TP=-1.0:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
    run(["ffmpeg", "-v", "error", "-y", "-i", P("pre.mp4"), "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", P("ln.mp4")])
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", P("ln.mp4"), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    gi = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]); gain = -14.0 - gi
    run(["ffmpeg", "-v", "error", "-y", "-i", P("ln.mp4"), "-c:v", "copy", "-af", f"volume={gain:.2f}dB,alimiter=limit=0.89", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", OUT])
    print(OUT, round(TOTAL, 2))

if __name__ == "__main__":
    main()
