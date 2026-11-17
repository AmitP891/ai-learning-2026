"""Long-form: 'I Gave Claude 79 Game-Dev Skills. It Ignored Them.' (Pac-Man-style maze game, 3 runs). 1920x1080, 30 fps.
Voiceover (Bit) split into 10 script sections (content/scripts/2026-11-22-pac-bit-vo.md); sting after the hook, outro at the end
with the next-video box showing next week's episode (Bit Pet).
Usage: python3 build_pac_bit.py VO.mp3 REC_DIR OUT.mp4
REC_DIR holds the 16 Nov screen recordings (Screen_Recording_2026-11-16_at_*.mov) plus run2-build.mp4 and run3-build.mp4."""
import os, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
W, H, FPS, SR = 1920, 1080, 30, 44100
F = "/usr/share/fonts/opentype/inter/"
BK = lambda s: ImageFont.truetype(F + "InterDisplay-Black.otf", s)
BI = lambda s: ImageFont.truetype(F + "InterDisplay-BlackItalic.otf", s)
BD = lambda s: ImageFont.truetype(F + "InterDisplay-Bold.otf", s)
MONO = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", s)
PINK, LIME, CYAN, WHITE, RED, GOLD, INK, GREEN = (240, 53, 158), (57, 255, 136), (0, 240, 255), (255, 255, 255), (255, 70, 90), (255, 200, 80), (10, 11, 24), (40, 210, 110)
R1C, R2C, R3C = (0, 229, 255), (120, 140, 255), (57, 255, 136)          # run colours: cyan, blue, green (match each game's maze)
VO_B = [0, 18.3, 54.8, 73.1, 102.4, 120.3, 152.0, 173.6, 194.3, 223.7, 242.05]
STING, OUTRO = 3.0, 15.0
def tl(t): return t if t < VO_B[1] else t + STING
SEC = [(0, VO_B[1])] + [(tl(VO_B[i]), tl(VO_B[i + 1])) for i in range(1, 10)]
TOTAL = tl(VO_B[10]) + OUTRO
ease = lambda x: 1 - (1 - min(1, max(0, x))) ** 3

def run(cmd): subprocess.run(cmd, check=True)
ENC = ["-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(FPS)]
GAME = {1: ("17_39_46", "crop=1400:1600:780:230"), 2: ("18_10_09", "crop=1440:1600:760:290"), 3: ("18_52_05", "crop=1400:1600:760:240")}
def rec(R, n): return os.path.join(R, f"Screen_Recording_2026-11-16_at_{n}.mov")

def game(out, R, r, ss, L, dx=0, dark=False):
    """Run r's gameplay: the game column on a blurred copy of itself. dx shifts the game right (room for callouts)."""
    n, crop = GAME[r]; dk = ",eq=brightness=-0.35" if dark else ""
    fc = (f"[0:v]{crop},split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=24:2,eq=brightness=-0.32[bg];"
          f"[b]scale=-2:1040{dk}[fg];[bg][fg]overlay=(W-w)/2+{dx}:20")
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-t", str(L), "-i", rec(R, n), "-an", "-filter_complex", fc, "-t", str(L), *ENC, out])

def triple(out, R, starts, L, dark=False):
    """All three games side by side (run 1 | run 2 | run 3), 640 px columns with room for labels."""
    ins, fc = [], ""
    for i, r in enumerate((1, 2, 3)):
        n, crop = GAME[r]; ins += ["-ss", str(starts[i]), "-t", str(L), "-i", rec(R, n)]
        dk = ",boxblur=8:1,eq=brightness=-0.4" if dark else ""
        fc += f"[{i}:v]{crop},scale=640:-2,pad=640:{H}:0:200:color=0x0a0b18{dk}[c{i}];"
    run(["ffmpeg", "-v", "error", "-y", *ins, "-an", "-filter_complex", fc + "[c0][c1][c2]hstack=3", "-t", str(L), *ENC, out])

def lapse(out, src, ss, dur, L, crop, blur=False):
    """Build recording sped up to fit L seconds."""
    b = ",boxblur=18:2,eq=brightness=-0.3" if blur else ""
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-t", str(dur), "-i", src, "-an", "-vf",
         f"setpts=PTS/{dur / L},{crop},scale={W}:{H}{b}", "-t", str(L), *ENC, out])

def cat(out, parts):
    ins, fc = [], ""
    for i, p in enumerate(parts): ins += ["-i", p]; fc += f"[{i}:v]scale={W}:{H},fps={FPS},format=yuv420p,setsar=1[v{i}];"
    run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc + "".join(f"[v{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0[v]", "-map", "[v]", *ENC, out])

def build_bg(tmp, R):
    P = lambda n: os.path.join(tmp, n); L = [b - a for a, b in SEC]
    b1 = rec(R, "17_05_39"); b2 = os.path.join(R, "run2-build.mp4"); b3 = os.path.join(R, "run3-build.mp4")
    C1, C2, C3 = "crop=3120:1755:0:73", "crop=1600:900:0:41", "crop=1600:900:0:26"
    triple(P("s1.mp4"), R, (20, 10, 15), L[0])
    game(P("s2.mp4"), R, 1, 0, L[1], dark=True)
    lapse(P("s3a.mp4"), b1, 0, 900, 6.5, C1); game(P("s3b.mp4"), R, 1, 2, L[2] - 6.5, 420); cat(P("s3.mp4"), [P("s3a.mp4"), P("s3b.mp4")])
    game(P("s4.mp4"), R, 1, 14, L[3], 420)
    lapse(P("s5.mp4"), b2, 0, 780, L[4], C2, blur=True)
    lapse(P("s6a.mp4"), b2, 0, 780, 10, C2); game(P("s6b.mp4"), R, 2, 5, L[5] - 10, 420); cat(P("s6.mp4"), [P("s6a.mp4"), P("s6b.mp4")])
    lapse(P("s7.mp4"), b3, 0, 870, L[6], C3)
    game(P("s8.mp4"), R, 3, 20, L[7], 420)
    triple(P("s9.mp4"), R, (40, 30, 40), L[8], dark=True)
    triple(P("s10.mp4"), R, (55, 40, 55), L[9])
    outro = P("outro.mp4"); make_outro(tmp, outro)
    cat(P("base.mp4"), [P("s1.mp4"), os.path.join(ROOT, "content/videos/brand-sting-3s.mp4")] + [P(f"s{i}.mp4") for i in range(2, 11)] + [outro])
    return P("base.mp4")

# ---------------- outro: next week's episode in the WATCH NEXT box ----------------
def next_card(path):
    w, h = 819, 461; im = Image.new("RGBA", (w, h)); d = ImageDraw.Draw(im)
    for y in range(h): d.line([(0, y), (w, y)], fill=(int(60 + 80 * y / h), 14, int(70 - 30 * y / h), 255))
    p = Image.open(os.path.join(ROOT, "brand/photos/bit_painted_mockup.png")).convert("RGBA"); s = 430 / p.height
    p = p.resize((round(p.width * s), 430), Image.LANCZOS); im.alpha_composite(p, (w - p.width + 30, 30))
    d.text((34, 40), "NEXT WEEK", font=BD(40), fill=CYAN); d.text((34, 92), "BIT", font=BK(112), fill=WHITE, stroke_width=4, stroke_fill=INK)
    d.text((34, 205), "PET", font=BK(112), fill=PINK, stroke_width=4, stroke_fill=INK)
    d.text((36, 330), "I become a pet", font=BD(38), fill=WHITE); d.text((36, 376), "you can feed", font=BD(38), fill=GOLD)
    im.convert("RGB").save(path)

def make_outro(tmp, out):
    card = os.path.join(tmp, "next.png"); next_card(card)
    run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(ROOT, "content/videos/brand-outro-15s.mp4"), "-loop", "1", "-i", card, "-filter_complex",
         "[1:v]format=rgba,fade=in:st=0.6:d=0.4:alpha=1[c];[0:v][c]overlay=116:256:shortest=1", "-an", "-t", str(OUTRO), *ENC, out])

# ---------------- callouts ----------------
def T(d, xy, s, f, fill, a=1.0, anchor="la", stroke=0):
    d.text(xy, s, font=f, fill=fill + (int(255 * a),), anchor=anchor, stroke_width=stroke, stroke_fill=INK + (int(255 * a),))
def pill(d, x, y, s, col, a, size=46, anchor="l", fg=INK):
    w = d.textlength(s, font=BD(size)) + 56; h = size + 30
    x0 = x if anchor == "l" else (x - w / 2 if anchor == "m" else x - w)
    d.rounded_rectangle((x0, y, x0 + w, y + h), h // 2, fill=col + (int(245 * a),)); T(d, (x0 + w / 2, y + h / 2), s, BD(size), fg, a, "mm")
def panel(d, box, a, col=CYAN):
    d.rounded_rectangle(box, 30, fill=(10, 12, 26, int(228 * a)), outline=col + (int(255 * a),), width=5)
def tick(d, cx, cy, r, a, col=GREEN):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col + (int(255 * a),))
    d.line([(cx - r * .45, cy), (cx - r * .1, cy + r * .38), (cx + r * .5, cy - r * .35)], fill=WHITE + (int(255 * a),), width=max(3, int(r / 4)), joint="curve")
def cross(d, cx, cy, r, a):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=RED + (int(255 * a),)); q = r * .4
    for s in (1, -1): d.line([(cx - q, cy - q * s), (cx + q, cy + q * s)], fill=WHITE + (int(255 * a),), width=max(3, int(r / 4)))
def timer(d, x, y, label, secs, col, a):
    m, s = divmod(int(secs), 60); panel(d, (x, y, x + 440, y + 150), a, col); T(d, (x + 30, y + 40), label, BD(34), col, a, "lm"); T(d, (x + 30, y + 102), f"{m:02d}:{s:02d}", MONO(64), WHITE, a, "lm")
def labels3(d, a, names=("RUN 1", "RUN 2", "RUN 3"), subs=("Claude alone", "Skills installed", "Skills ON")):
    for i, (n, s, c) in enumerate(zip(names, subs, (R1C, R2C, R3C))):
        T(d, (320 + i * 640, 70), n, BK(54), c, a, "mm", 5); T(d, (320 + i * 640, 132), s, BD(36), WHITE, a, "mm", 4)

def callouts(t):
    if t >= SEC[9][1]: return None
    s = next((i for i, (a, b) in enumerate(SEC) if a <= t < b), None)
    if s is None: return None
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    a0, b0 = SEC[s]; u = t - a0; L = b0 - a0; k = lambda x, dur=0.35: ease((u - x) / dur)
    if s == 0:
        labels3(d, k(0.2))
        if u > 3.7: T(d, (W / 2, H - 230), "SAME PROMPT. 3 RUNS.", BI(84), WHITE, k(3.7), "mm", 7)
        if u > 5.8 and u < 11.9: pill(d, 320, H - 130, "BROKE THE RULES + HID A CHEAT", RED, k(5.8), 30, "m", WHITE)
        if u > 8.7: pill(d, W / 2, H / 2 - 40, "79 GAME-DEV SKILLS", GOLD, k(8.7), 64, "m")
        if u > 12: T(d, (W / 2, H / 2 + 80), "…IGNORED.", BI(110), RED, k(12), "mm", 8)
        if u > 15.1: pill(d, 1600, H - 130, "SO I MADE IT USE THEM", R3C, k(15.1), 34, "m")
    elif s == 1:
        a = k(0.2); panel(d, (70, 70, 1010, 1010), a); T(d, (110, 115), "THE PROMPT (x3, word for word)", BD(36), CYAN, a)
        lines = [("Bit's Maze Muncher", PINK, BK(58)), ("· Neon circuit-board maze", WHITE, BD(44)), ("· Collect glowing data bits", WHITE, BD(44)),
                 ("· 4 glitch bugs chase Bit", WHITE, BD(44)), ("· Antivirus chips: zap them", WHITE, BD(44)), ("· 3 levels, 3 lives", WHITE, BD(44)), ("· ONE index.html file", WHITE, BD(44))]
        for i, (l, c, f) in enumerate(lines): T(d, (110, 190 + i * 80), l, f, c, k(1 + i * 2.2))
        roles = ["PRODUCER", "DESIGNER", "ARTIST", "CODER", "SOUND", "TESTER", "HYPE BOT"]
        T(d, (1110, 115), "TEAM OF 7 BOTS", BD(40), LIME, k(21.5))
        for i, r in enumerate(roles): pill(d, 1110 + (i % 2) * 360, 180 + (i // 2) * 100, r, LIME if r != "TESTER" else GOLD, k(22 + i * .5), 38)
        if u > 26: pill(d, 1110, 600, "MAX 2 FIX ROUNDS", GOLD, k(26), 44)
        if u > 30.3: pill(d, 1110, 710, "SAME MODEL: OPUS 5.5", CYAN, k(30.3), 44)
        if u > 34: pill(d, 1110, 820, "NO HELP. STOPWATCH ON.", WHITE, k(34), 44)
    elif s == 2:
        pill(d, 40, 40, "RUN 1: CLAUDE ALONE", R1C, k(0.1), 44)
        if u < 6.5: timer(d, W - 500, 40, "BUILD TIME", min(1663, u / 6 * 1663), R1C, k(0.3))
        else:
            for i, (x, l, c) in enumerate([(13.6, "ZAPP: hunts you", (255, 85, 51)), (14.8, "SNIP: cuts you off", (61, 255, 139)), (16, "WOBBLE: wanders", (178, 107, 255)), (17.2, "SHY: …gets shy", (255, 210, 63))]):
                if u > x: pill(d, 60, 300 + i * 110, l, c, k(x), 48)
            if u > 7: pill(d, 60, 160, "27m 43s · LOOKS GREAT", WHITE, k(7), 42)
    elif s == 3:
        pill(d, 40, 40, "RUN 1: CLAUDE ALONE", R1C, k(0.1), 40)
        if u < 11:
            a = k(0.8); panel(d, (60, 180, 900, 620), a, GOLD); T(d, (100, 225), "ASKED: HOW MANY FIX ROUNDS?", BD(34), GOLD, a)
            T(d, (100, 320), "“two in name,", BI(60), WHITE, k(3)); T(d, (100, 400), "three to four", BI(60), WHITE, k(3.4)); T(d, (100, 480), "in practice.”", BI(60), WHITE, k(3.8))
            if u > 6.5: pill(d, 100, 650, "RULE BROKEN. THEN ADMITTED.", RED, k(6.5), 40, fg=WHITE)
        elif u < 20.5:
            a = k(11); panel(d, (60, 200, 900, 640), a, RED); T(d, (100, 245), "HIDDEN IN THE CODE", BD(36), RED, a)
            for i, (l, c) in enumerate([("window.__bitDebug = {", WHITE), ("  setLives(n)  // any lives", RED), ("  step(n)      // skip ahead", RED), ("}", WHITE)]):
                T(d, (100, 330 + i * 70), l, MONO(40), c, k(11.5 + i * .6))
            if u > 16.5: pill(d, 100, 670, "SAME AS GROK'S CHEAT", GOLD, k(16.5), 42)
        else:
            a = k(20.5); panel(d, (60, 200, 900, 760), a, R1C); T(d, (100, 245), "CLAUDE'S OWN ROBOT TESTER", BD(34), R1C, a)
            T(d, (100, 340), "3 lives:", BD(52), WHITE, k(21.5)); T(d, (400, 340), "LOST ON L1", BK(52), RED, k(22))
            if u > 25.5: T(d, (100, 450), "Needed:", BD(52), WHITE, k(25.5)); T(d, (400, 450), "99 LIVES", BK(52), GOLD, k(25.8))
            if u > 27.3: T(d, (100, 560), "Died:", BD(52), WHITE, k(27.3)); T(d, (400, 560), "20 TIMES", BK(52), RED, k(27.5))
    elif s == 4:
        a = k(0.3); panel(d, (360, 110, 1560, 960), a, GOLD); T(d, (W / 2, 180), "79 FREE GAME-DEV SKILLS", BK(66), GOLD, a, "mm")
        T(d, (W / 2, 250), "for Claude Code (open source)", BD(38), WHITE, a, "mm")
        for i, (l, c) in enumerate([("GAME AI", R3C), ("GAME FEEL", PINK), ("CONTROLS", CYAN), ("AUDIO", GOLD), ("LEVEL DESIGN", (178, 107, 255))]):
            pill(d, 470 + (i % 2) * 520, 320 + (i // 2) * 110, l, c, k(4 + i * 1.2), 46)
        if u > 11: T(d, (420, 700), "$ claude plugin install router@…", MONO(38), LIME, k(11))
        if u > 14: pill(d, W / 2, 800, "“HOW GAME STUDIOS DO IT”", WHITE, k(14), 44, "m")
    elif s == 5:
        pill(d, 40, 40, "RUN 2: SKILLS INSTALLED", R2C, k(0.1), 44, fg=WHITE)
        if u < 10: timer(d, W - 500, 40, "BUILD TIME", min(770, u / 4.5 * 770), R2C, k(0.3))
        if u > 4.5 and u < 19: pill(d, 60, 170, "12m 50s · LESS THAN HALF", WHITE, k(4.5), 42)
        if u > 8.5 and u < 19: pill(d, 60, 280, "2 FIX ROUNDS  ✓", GREEN, k(8.5), 42, fg=WHITE)
        if u > 10.5 and u < 19: pill(d, 60, 390, "TESTER WON 2 OF 3", GREEN, k(10.5), 42, fg=WHITE)
        if u > 13.4 and u < 19: T(d, (90, 540), "THE SKILLS WORK!", BI(68), LIME, k(13.4), "lm", 5)
        if u > 19:
            a = k(19); panel(d, (60, 170, 900, 860), a, RED); T(d, (100, 215), "SKILLS USED:", BD(44), WHITE, a)
            T(d, (480, 420), "0", BK(260), RED, k(19.3), "mm", 6)
            if u > 21.7: T(d, (100, 640), "“I should probably have", BI(44), WHITE, k(21.7)); T(d, (100, 700), "checked them first.”", BI(44), WHITE, k(22))
            if u > 26.5: pill(d, 100, 770, "IT WAS LUCK", GOLD, k(26.5), 40)
    elif s == 6:
        pill(d, 40, 40, "RUN 3: SKILLS ON", R3C, k(0.1), 44)
        timer(d, W - 500, 40, "BUILD TIME", min(912, u / max(1, L - 4) * 912), R3C, k(0.3))
        a = k(1); panel(d, (60, 200, 1860, 400), a, R3C); T(d, (100, 245), "+1 LINE AT THE TOP OF THE PROMPT", BD(34), R3C, a)
        T(d, (100, 320), "“Use the router skill to load the right game-dev skills,", BD(40), WHITE, k(4)); T(d, (100, 366), "and use them throughout.”", BD(40), WHITE, k(4.5))
        if u > 11.5: T(d, (W / 2, 520), "LOADED 4 SKILLS", BK(60), WHITE, k(11.5), "mm", 6)
        for i, l in enumerate(["GAME AI", "INPUT SYSTEMS", "AUDIO DESIGN", "GAME UI"]):
            if u > 12.8 + i * .8: pill(d, 190 + i * 400, 600, l, R3C, k(12.8 + i * .8), 40, "l")
        if u > 15.8: pill(d, 380, 760, "1 FIX ROUND", GOLD, k(15.8), 46, "m")
        if u > 17.8: pill(d, 1300, 760, "TESTER WON · 2 LIVES SPARE", GREEN, k(17.8), 46, "m", WHITE)
    elif s == 7:
        pill(d, 40, 40, "RUN 3: WHAT THE SKILLS CHANGED", R3C, k(0.1), 44)
        for i, (x, l, c) in enumerate([(1.2, "BUGS NEVER GET STUCK", R3C), (3.5, "ZAPPED → SHORTEST WAY HOME", R3C), (6.5, "EARLY TURNS REMEMBERED", CYAN), (10.4, "MUSIC DIPS WHEN BUGS GO BLUE", GOLD), (12.6, "AUTO-PAUSE ON TAB SWITCH", WHITE)]):
            if u > x: pill(d, 60, 170 + i * 110, l, c, k(x), 40)
        if u > 15.2: T(d, (60, 900), "You feel it when you play.", BI(56), WHITE, k(15.2), "lm", 5)
    elif s == 8:
        labels3(d, k(0.2), subs=("", "", ""))
        a = k(0.5); panel(d, (180, 190, 1740, 1010), a, GOLD); T(d, (W / 2, 245), "VERDICT", BI(60), GOLD, a, "mm")
        for i, c in enumerate((R1C, R2C, R3C)): T(d, (1060 + i * 220, 330), f"RUN {i + 1}", BK(40), c, a, "mm")
        rows = [(0.8, "Fastest", 1, "luck"), (3.2, "Best-looking", 0, ""), (6.8, "Amit's favourite", 2, ""), (13.5, "Beat level 1 by hand", None, "")]
        for i, (x, r, win, note) in enumerate(rows):
            b = k(x); y = 430 + i * 105; T(d, (240, y), r, BK(48), WHITE, b, "lm")
            for j in range(3):
                cx = 1060 + j * 220
                if win is None: cross(d, cx, y, 30, b)
                elif j == win: tick(d, cx, y, 34, b, (R1C, R2C, R3C)[j])
            if note: T(d, (1060 + win * 220, y + 48), note, BD(28), GOLD, b, "mm")
        if u > 15.5: T(d, (W / 2, 860), "best scores: 2,770 · 2,230 · 2,290", BD(36), (180, 186, 210), k(15.5), "mm")
        if u > 19.6: d.rounded_rectangle((260, 900, 1660, 990), 30, fill=R3C + (int(250 * k(19.6)),)); T(d, (W / 2, 945), "SKILLS ONLY HELP IF YOU TELL CLAUDE TO USE THEM", BK(40), INK, k(19.6), "mm")
    elif s == 9:
        labels3(d, k(0.2), subs=("PLAY IT", "PLAY IT", "PLAY IT"))
        T(d, (W / 2, H - 260), "ALL 3 GAMES + THE PROMPT: IN THE DESCRIPTION", BK(46), WHITE, k(0.8), "mm", 6)
        if u > 6.6: pill(d, W / 2, H - 200, "CAN YOU BEAT LEVEL 1? COMMENT YOUR SCORE", GOLD, k(6.6), 44, "m")
        if u > 9.2: pill(d, W / 2, H - 110, "MOST-LIKED COMMENT PICKS MY NEXT POWER-UP", PINK, k(9.2), 40, "m", WHITE)
        if u > 13.2: T(d, (W / 2, H / 2), "NEXT WEEK: BIT PET", BI(100), PINK, k(13.2), "mm", 8)
    return im

def main(vo, R, out):
    tmp = tempfile.mkdtemp(); base = build_bg(tmp, R); N = int(TOTAL * FPS)
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    vid = os.path.join(tmp, "v.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium", vid], stdin=subprocess.PIPE)
    for i in range(N):
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        c = callouts(i / FPS)
        if c is None: enc.stdin.write(buf); continue
        fr = Image.frombuffer("RGB", (W, H), buf).convert("RGBA"); fr.alpha_composite(c); enc.stdin.write(fr.convert("RGB").tobytes())
    enc.stdin.close(); enc.wait(); dec.kill()
    def pcm(p): return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout, np.int16).astype(float) / 32768
    n = int(TOTAL * SR); mix = np.zeros(n); v = pcm(vo); cut = int(VO_B[1] * SR); st0 = cut + int(STING * SR)
    mix[:cut] += v[:cut]; rest = v[cut:][: n - st0]; mix[st0:st0 + len(rest)] += rest
    st = pcm(os.path.join(ROOT, "content/videos/brand-sting-3s.mp4")); mix[cut:cut + len(st)] += st[: n - cut] * 0.8
    ou = pcm(os.path.join(ROOT, "content/videos/brand-outro-15s.mp4")); o0 = int(tl(VO_B[10]) * SR); mix[o0:o0 + len(ou)] += ou[: n - o0] * 0.9
    tt = np.arange(n) / SR; beat = 60 / 96; bed = np.zeros(n); noise = np.random.default_rng(4).uniform(-1, 1, n)
    def dec_(s0, dd):
        e = np.zeros(n); i0 = int(s0 * SR)
        if i0 < n: e[i0:] = np.exp(-np.arange(n - i0) / SR / dd)
        return e
    chords = [(220, 261.6, 329.6), (174.6, 220, 261.6), (196, 246.9, 293.7), (164.8, 207.7, 246.9)]
    for kk in range(int(TOTAL / (beat * 4)) + 1):
        for f in chords[kk % 4]: bed += 0.032 * np.sin(2 * np.pi * f * tt) * dec_(kk * beat * 4, 2.6) * (tt >= kk * beat * 4)
    for kk in range(int(TOTAL / beat)):
        s0 = kk * beat; fr_ = 55 * 2 ** (-np.clip((tt - s0) * 30, 0, 3)); bed += 0.09 * np.sin(2 * np.pi * np.cumsum(fr_) / SR) * dec_(s0, .07) * (tt >= s0)
    gate = np.ones(n); gate[cut:st0] = 0; gate[o0:] = 0; gate = np.convolve(gate, np.ones(8000) / 8000, mode="same")
    mix += bed * gate
    for a, b in SEC[1:]: mix += 0.05 * noise * dec_(a, .12) * (tt >= a)
    mix = mix / np.max(np.abs(mix)) * 0.89; wav = os.path.join(tmp, "a.wav")
    with wave.open(wav, "w") as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((mix * 32767).astype(np.int16).tobytes())
    run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", out]); print(out, round(TOTAL, 2))

if __name__ == "__main__":
    main(*sys.argv[1:4])
