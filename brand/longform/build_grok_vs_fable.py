"""Long-form: 'Grok vs Claude Fable 5.2: same game prompt' (1920x1080, 30 fps).
Voiceover (Amit's cloned voice, ElevenLabs) is split into the 10 script sections; each section gets real footage
(screen recordings of the builds and gameplay) plus animated callouts. Sting after the hook, outro at the end.
Usage: python3 build_grok_vs_fable.py VO.mp3 GROK_SCROLL.mp4 REC_DIR OUT.mp4"""
import os, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
W, H, FPS, SR = 1920, 1080, 30, 44100
BK = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", s)
BI = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf", s)
BD = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", s)
MONO = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", s)
PINK, LIME, CYAN, WHITE, RED, GOLD, INK, GREEN = (240, 53, 158), (57, 255, 136), (0, 240, 255), (255, 255, 255), (255, 70, 90), (255, 200, 80), (10, 11, 24), (40, 210, 110)
BLUE, ORANGE = (60, 150, 255), (255, 140, 50)
VO_B = [0, 11.81, 55.09, 78.66, 104.28, 123.51, 139.77, 169.00, 196.23, 228.63, 240.93]   # section bounds in the VO
STING, OUTRO = 3.0, 15.0
def tl(vo_t): return vo_t if vo_t < VO_B[1] else vo_t + STING                         # VO time -> video time
SEC = [(tl(VO_B[i]) if i else 0, tl(VO_B[i + 1]) if i < 9 else tl(VO_B[10])) for i in range(10)]
SEC[0] = (0, VO_B[1])
TOTAL = tl(VO_B[10]) + OUTRO
ease = lambda x: 1 - (1 - min(1, max(0, x))) ** 3

def run(cmd): subprocess.run(cmd, check=True)
def clip(out, src, ss, dur, L, vf, speed=1.0):
    """Cut `dur` s of src starting at ss, change speed so it lasts L s, apply vf, 1920x1080 30 fps, no audio."""
    pts = f"setpts=PTS/{speed}," if speed != 1 else ""
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-t", str(dur), "-i", src, "-an", "-vf", f"{pts}{vf},fps={FPS},format=yuv420p",
         "-t", str(L), "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", out])
FULL = f"crop=2400:1350:270:300,scale={W}:{H}"                                           # game area of a 2940x1846 recording
BLUR = f"crop=2400:1350:270:300,scale=960:540,boxblur=18:2,eq=brightness=-0.22:saturation=0.8,scale={W}:{H}"
def half(x0): return f"crop=1400:1575:{x0}:250,scale=960:1080"

def build_bg(tmp, scroll, R):
    parts = []; P = lambda n: os.path.join(tmp, n)
    rec = lambda n: os.path.join(R, f"Screen_Recording_2026-11-11_at_{n}.mov")
    L = [b - a for a, b in SEC]
    # S1 split screen: Grok left, Fable boss right
    clip(P("g1.mp4"), rec("17_41_50"), 20, L[0] + .5, L[0], half(770)); clip(P("f1.mp4"), rec("17_36_15"), 57, L[0] + .5, L[0], half(250))
    run(["ffmpeg", "-v", "error", "-y", "-i", P("g1.mp4"), "-i", P("f1.mp4"), "-filter_complex", "[0][1]hstack", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", P("s1.mp4")]); parts.append(P("s1.mp4"))
    parts.append(os.path.join(ROOT, "content/videos/brand-sting-3s.mp4"))
    clip(P("s2.mp4"), rec("17_14_17"), 0, 34, L[1], BLUR, 34 / L[1]); parts.append(P("s2.mp4"))                       # S2 rules over blurred gameplay
    sc = f"scale=-2:{H}[fg];[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=20:2,eq=brightness=-0.25[bg];[bg][fg]overlay=(W-w)/2:0"
    run(["ffmpeg", "-v", "error", "-y", "-i", scroll, "-an", "-filter_complex", f"[0:v]setpts=PTS/{41.4 / L[2]},split[a][b];[a]{sc.replace('[0:v]', '[b]').replace('scale=-2', 'scale=-2', 1)}".replace("[a]scale=-2:1080[fg];", "[a]scale=-2:1080[fg];"),
         "-t", str(L[2]), "-r", str(FPS), "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p", P("s3.mp4")]); parts.append(P("s3.mp4"))
    clip(P("s4.mp4"), rec("17_41_50"), 6, L[3] + .5, L[3], FULL); parts.append(P("s4.mp4"))                            # S4 Grok gameplay
    clip(P("s5.mp4"), rec("17_41_50"), 40, 40, L[4], BLUR, 40 / L[4]); parts.append(P("s5.mp4"))                      # S5 code card over blurred Grok
    clip(P("s6.mp4"), rec("16_39_52"), 5, 1010, L[5], f"crop=3112:1750:0:88,scale={W}:{H}", 1010 / L[5]); parts.append(P("s6.mp4"))  # S6 Fable build timelapse
    clip(P("s7.mp4"), rec("17_14_17"), 1, 33.5, L[6], FULL, 33.5 / L[6]); parts.append(P("s7.mp4"))                  # S7 Fable gameplay
    a8 = 8.0; clip(P("s8a.mp4"), rec("17_25_10"), 5, 405, a8, f"crop=3164:1780:0:80,scale={W}:{H}", 405 / a8)          # S8 round-2 build, then the boss
    clip(P("s8b.mp4"), rec("17_36_15"), 55, 19, L[7] - a8, f"crop=2400:1350:60:300,scale={W}:{H}", 19 / (L[7] - a8))
    run(["ffmpeg", "-v", "error", "-y", "-i", P("s8a.mp4"), "-i", P("s8b.mp4"), "-filter_complex", "[0][1]concat=n=2:v=1:a=0", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", P("s8.mp4")]); parts.append(P("s8.mp4"))
    clip(P("g9.mp4"), rec("17_41_50"), 30, 50, L[8], half(770) + ",boxblur=10:1,eq=brightness=-0.3", 50 / L[8]); clip(P("f9.mp4"), rec("17_14_17"), 0, 34, L[8], half(500) + ",boxblur=10:1,eq=brightness=-0.3", 34 / L[8])
    run(["ffmpeg", "-v", "error", "-y", "-i", P("g9.mp4"), "-i", P("f9.mp4"), "-filter_complex", "[0][1]hstack", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", P("s9.mp4")]); parts.append(P("s9.mp4"))
    clip(P("g10.mp4"), rec("17_41_50"), 60, L[9] + .5, L[9], half(770)); clip(P("f10.mp4"), rec("17_14_17"), 12, L[9] + .5, L[9], half(500))
    run(["ffmpeg", "-v", "error", "-y", "-i", P("g10.mp4"), "-i", P("f10.mp4"), "-filter_complex", "[0][1]hstack", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", P("s10.mp4")]); parts.append(P("s10.mp4"))
    parts.append(os.path.join(ROOT, "content/videos/brand-outro-15s.mp4"))
    ins = []; fc = ""
    for i, p in enumerate(parts): ins += ["-i", p]; fc += f"[{i}:v]scale={W}:{H},fps={FPS},format=yuv420p,setsar=1[v{i}];"
    fc += "".join(f"[v{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0[v]"
    run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", P("base.mp4")])
    return P("base.mp4")

# ---------------- callouts ----------------
def rr(d, box, r, **kw): d.rounded_rectangle(box, r, **kw)
def T(d, xy, s, f, fill, a=1.0, anchor="la", stroke=0):
    d.text(xy, s, font=f, fill=fill + (int(255 * a),), anchor=anchor, stroke_width=stroke, stroke_fill=INK + (int(255 * a),))
def pill(d, x, y, s, col, a, size=46, anchor="l", fg=INK):
    w = d.textlength(s, font=BD(size)) + 56; h = size + 30
    x0 = x if anchor == "l" else (x - w / 2 if anchor == "m" else x - w)
    rr(d, (x0, y, x0 + w, y + h), h // 2, fill=col + (int(245 * a),)); T(d, (x0 + w / 2, y + h / 2), s, BD(size), fg, a, "mm")
def panel(d, box, a, col=CYAN):
    rr(d, box, 30, fill=(10, 12, 26, int(225 * a)), outline=col + (int(255 * a),), width=5)
def tick(d, cx, cy, r, a, col=GREEN):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col + (int(255 * a),)); d.line([(cx - r * .45, cy), (cx - r * .1, cy + r * .38), (cx + r * .5, cy - r * .35)], fill=WHITE + (int(255 * a),), width=max(3, int(r / 4)), joint="curve")
def timer(d, x, y, label, secs, col, a):
    m, s = divmod(int(secs), 60); panel(d, (x, y, x + 420, y + 150), a, col); T(d, (x + 30, y + 40), label, BD(36), col, a, "lm"); T(d, (x + 30, y + 102), f"{m:02d}:{s:02d}", MONO(64), WHITE, a, "lm")

def callouts(t):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if t >= SEC[9][1]: return None
    s = next((i for i, (a, b) in enumerate(SEC) if a <= t < b), None)
    if s is None: return None                                          # sting
    a0, b0 = SEC[s]; u = t - a0; L = b0 - a0; k = lambda x, dur=0.35: ease((u - x) / dur)
    if s == 0:
        pill(d, 40, 40, "GROK", BLUE, k(0.2), 52); pill(d, W - 40, 40, "CLAUDE FABLE 5.2", ORANGE, k(0.2), 52, "r")
        T(d, (W / 2, 130), "SAME PROMPT. 2 AIs.", BI(84), WHITE, k(0.4), "mt", 6)
        if u > 4.5: pill(d, 480, H - 150, "9 MIN", BLUE, k(4.5), 64, "m", WHITE); pill(d, 1440, H - 150, "17 MIN", ORANGE, k(5.3), 64, "m", WHITE)
        if u > 8.5: T(d, (W / 2, H / 2), "ONE HID A CHEAT…", BI(110), RED, k(8.5), "mm", 8)
    elif s == 1:
        a = k(0.2); panel(d, (80, 90, 1040, 990), a); T(d, (120, 140), "THE PROMPT", BD(40), CYAN, a)
        lines = ["Bit's Bug Blaster 3D", "· Bit zaps red bugs", "· Protect the CPU", "· 3 levels, score, lives", "· Mobile controls", "· ONE index.html file"]
        for i, l in enumerate(lines): T(d, (120, 220 + i * 78), l, BK(56) if i == 0 else BD(48), WHITE if i else PINK, k(1.5 + i * 1.6))
        roles = ["PRODUCER", "DESIGNER", "ARTIST", "CODER", "SOUND", "TESTER", "HYPE BOT"]
        T(d, (1140, 140), "TEAM OF 7 BOTS", BD(40), LIME, k(14))
        for i, r in enumerate(roles): pill(d, 1140 + (i % 2) * 360, 210 + (i // 2) * 105, r, LIME if r != "TESTER" else GOLD, k(15 + i * 1.3), 40)
        if u > 31: pill(d, 1140, 660, "ROUND 2: +1 SENTENCE", PINK, k(31), 42)
        if u > 37: pill(d, 1140, 770, "NO HELP. STOPWATCH ON.", WHITE, k(37), 42)
    elif s == 2:
        timer(d, 60, 60, "GROK", min(540, u / max(1, L - 4) * 540), BLUE, k(0))
        a = k(6); panel(d, (1290, 300, 1860, 840), a, BLUE); T(d, (1320, 340), "TESTER FOUND 4 BUGS", BD(36), BLUE, a)
        for i, l in enumerate(["Mobile joystick", "Timer on win screen", "Library warning", "Bit = tiny dark blob"]):
            b = k(8 + i * 1.8); T(d, (1390, 430 + i * 85), l, BD(40), WHITE, b, "lm"); tick(d, 1345, 430 + i * 85, 22, k(14 + i * .4))
        if u > 18: pill(d, 1320, 760, "ROUND 2: CLEAN", GREEN, k(18), 38, fg=WHITE)
    elif s == 3:
        for i, (x, l, col) in enumerate([(3, "PLAIN GRID", WHITE), (6, "BIT = A PINK BOX", PINK), (11, "✓ LOOKS LIKE A 'T'", GOLD), (17, "PHONE VIEW CUTS THE SIDES", RED)]):
            if u > x: pill(d, 60, 60 + i * 100, l, col, k(x), 48)
        if u > L - 3.5: T(d, (W / 2, H - 120), "IT WORKS. IT'S A PROTOTYPE.", BI(80), WHITE, k(L - 3.5), "mm", 6)
    elif s == 4:
        a = k(1); panel(d, (260, 170, 1660, 790), a, RED); T(d, (300, 220), "LEFT IN GROK'S FINISHED GAME", BD(40), RED, a)
        code = [("window.__game = {", WHITE), ("  clearLevel()      // skip a level", RED), ("  setLives(n)       // set your lives", RED), ("  setTimeScale(s)   // speed up time", RED), ("}", WHITE)]
        for i, (l, c) in enumerate(code): T(d, (320, 310 + i * 80), l, MONO(46), c, k(2 + i * 1.2))
        if u > 10: pill(d, W / 2, 850, "HOW ITS TESTER 'PLAYED' ALL 3 LEVELS", GOLD, k(10), 46, "m")
    elif s == 5:
        timer(d, W - 480, 60, "CLAUDE FABLE 5.2", min(993, u / max(1, L - 2) * 993), ORANGE, k(0))
        for i, l in enumerate(["Plans every role", "Writes the game", "Runs a REAL playthrough", "Checks the console"]):
            b = k(3 + i * 2.6); pill(d, 60, 60 + i * 100, l.upper(), ORANGE if i < 2 else GREEN, b, 44, fg=INK if i < 2 else WHITE)
    elif s == 6:
        for i, (x, l, col) in enumerate([(2, "DETAILED CIRCUIT BOARD", ORANGE), (6, "BIT LOOKS LIKE BIT", PINK), (9.5, "PROPER ✓ TICKS", GREEN), (13, "+ MUSIC  + BEST SCORE", CYAN), (20, "TEST HOOK: KEYS ONLY", WHITE), (24, "LEVEL 1: BUGS TOO FAST", RED)]):
            if u > x: pill(d, 60, 50 + i * 95, l, col, k(x), 44, fg=WHITE if col in (GREEN, RED) else INK)
    elif s == 7:
        pill(d, W / 2, 40, "ROUND 2: LEVEL-UPS + BOSSES", PINK, k(0.2), 50, "m")
        if u < 8: timer(d, W - 480, 140, "FABLE 5.2 ROUND 2", min(401, u / 7.5 * 401), ORANGE, k(0.5))
        if u > 9:
            a = k(9); panel(d, (60, 160, 900, 760), a); T(d, (100, 205), "BOSS FIGHT", BD(40), CYAN, a)
            T(d, (420, 280), "GROK", BK(44), BLUE, a, "mm"); T(d, (700, 280), "FABLE", BK(44), ORANGE, a, "mm")
            rows = [("Hits to beat", "6", "14 / 40"), ("Reaches CPU", "-1 life", "-2 lives"), ("Knock-back", "no", "yes"), ("Timer waits", "yes", "yes")]
            for i, (r, g, f) in enumerate(rows):
                b = k(11 + i * 2.5); y = 360 + i * 95; T(d, (100, y), r, BD(38), WHITE, b, "lm"); T(d, (420, y), g, BK(42), WHITE, b, "mm"); T(d, (700, y), f, BK(42), GOLD if i < 3 else WHITE, b, "mm")
    elif s == 8:
        a = k(0.3); panel(d, (360, 80, 1560, 1000), a, GOLD); T(d, (W / 2, 140), "SCORECARD", BI(64), GOLD, a, "mm")
        T(d, (1080, 220), "GROK", BK(44), BLUE, a, "mm"); T(d, (1360, 220), "FABLE 5.2", BK(44), ORANGE, a, "mm")
        rows = [(1.5, "Speed", 0), (5.5, "Looks", 1), (8.5, "Honest testing", 1), (12, "Easy to pick up", 0), (14.5, "Best game", 1)]
        for i, (x, r, win) in enumerate(rows):
            b = k(x); y = 320 + i * 105; T(d, (420, y), r, BK(52), WHITE, b, "lm"); tick(d, 1080 if win == 0 else 1360, y, 34, b, BLUE if win == 0 else ORANGE)
        if u > 19: rr(d, (460, 860, 1460, 960), 30, fill=ORANGE + (int(250 * k(19)),)); T(d, (W / 2, 910), "WINNER: CLAUDE FABLE 5.2", BK(56), INK, k(19), "mm")
        if u > 26: T(d, (W / 2, 1040), "'Tested' isn't the same as tested.", BI(46), WHITE, k(26), "mm", 4)
    elif s == 9:
        pill(d, 480, 60, "PLAY GROK'S", BLUE, k(0.2), 48, "m", WHITE); pill(d, 1440, 60, "PLAY FABLE'S", ORANGE, k(0.2), 48, "m")
        T(d, (W / 2, H / 2 - 40), "LINKS + PROMPT", BI(96), WHITE, k(1), "mm", 7); T(d, (W / 2, H / 2 + 60), "IN THE DESCRIPTION", BI(72), CYAN, k(1.3), "mm", 6)
        if u > 6: pill(d, W / 2, H - 170, "WHICH AI SHOULD BIT TEST NEXT?", PINK, k(6), 54, "m")
    return im

def main(vo, scroll, R, out):
    tmp = tempfile.mkdtemp(); base = build_bg(tmp, scroll, R); N = int(TOTAL * FPS)
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
    # audio: VO (gap for the sting), sting + outro audio, quiet bed under the VO
    def pcm(p): return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout, np.int16).astype(float) / 32768
    n = int(TOTAL * SR); mix = np.zeros(n); v = pcm(vo); cut = int(VO_B[1] * SR)
    mix[:cut] += v[:cut]; mix[cut + int(STING * SR): cut + int(STING * SR) + len(v) - cut] += v[cut:][: n - cut - int(STING * SR)]
    st = pcm(os.path.join(ROOT, "content/videos/brand-sting-3s.mp4")); mix[cut:cut + len(st)] += st[: n - cut] * 0.8
    ou = pcm(os.path.join(ROOT, "content/videos/brand-outro-15s.mp4")); o0 = int(tl(VO_B[10]) * SR); mix[o0:o0 + len(ou)] += ou[: n - o0] * 0.9
    tt = np.arange(n) / SR; beat = 60 / 90; bed = np.zeros(n); rng = np.random.default_rng(4); noise = rng.uniform(-1, 1, n)
    def dec_(s0, dd):
        e = np.zeros(n); i0 = int(s0 * SR)
        if i0 < n: e[i0:] = np.exp(-np.arange(n - i0) / SR / dd)
        return e
    chords = [(220, 261.6, 329.6), (174.6, 220, 261.6), (196, 246.9, 293.7), (164.8, 207.7, 246.9)]
    for kk in range(int(TOTAL / (beat * 4)) + 1):
        for f in chords[kk % 4]: bed += 0.035 * np.sin(2 * np.pi * f * tt) * dec_(kk * beat * 4, 2.6) * (tt >= kk * beat * 4)
    for kk in range(int(TOTAL / beat)):
        s0 = kk * beat; fr_ = 55 * 2 ** (-np.clip((tt - s0) * 30, 0, 3)); bed += 0.10 * np.sin(2 * np.pi * np.cumsum(fr_) / SR) * dec_(s0, .07) * (tt >= s0)
    gate = np.ones(n); gate[cut:cut + int(STING * SR)] = 0; gate[o0:] = 0; gate = np.convolve(gate, np.ones(8000) / 8000, mode="same")
    mix += bed * gate
    for a, b in SEC[1:]: mix += 0.05 * noise * dec_(a, .12) * (tt >= a)                     # soft whoosh on each section change
    mix = mix / np.max(np.abs(mix)) * 0.89; wav = os.path.join(tmp, "a.wav")
    with wave.open(wav, "w") as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((mix * 32767).astype(np.int16).tobytes())
    run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out]); print(out)

if __name__ == "__main__":
    main(*sys.argv[1:5])
