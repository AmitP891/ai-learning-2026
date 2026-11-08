#!/usr/bin/env python3
"""Bit: Level 3 — Build Race. A 20 s retro arcade build race against GLITCH, drawn and scored in code.

    python build.py frames     # Gate 1: three style frames -> out/style_frames/
    python build.py grid       # Gate 2: out/beats.json + out/beat_grid.md
    python build.py render     # Gate 3: out/level3_9x16.mp4
    python build.py            # everything

Same engine as Levels 1 and 2 (../bit-level-2/build.py): the game layer is drawn at 270x480 and
upscaled 4x nearest-neighbour; HUD and words are drawn at full resolution with an un-antialiased
pixel font, then composited. Bar 1 tears through Level 2's SCOPE LOCKED frame.
"""
import importlib.util, io, json, math, os, re, sys
from pathlib import Path

# cairo on macOS: dyld only reads DYLD_* at process launch, so set it and re-exec once.
if sys.platform == "darwin" and "DYLD_FALLBACK_LIBRARY_PATH" not in os.environ:
    os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = "/opt/homebrew/lib"
    os.execv(sys.executable, [sys.executable] + sys.argv)
import numpy as np, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).resolve().parent
BRAND = HERE.parents[1]
OUT = HERE / "out"
LEVEL2 = HERE.parent / "bit-level-2" / "build.py"

# The shared brand scripts hard-code Linux font paths; find the same files here.
FONT_DIRS = [Path.home() / "Library/Fonts", Path("/Library/Fonts"),
             Path("/usr/share/fonts/opentype/inter"), Path("/usr/share/fonts/truetype/dejavu")]
def font_path(name):
    for d in FONT_DIRS:
        if (d / name).exists(): return str(d / name)
    raise FileNotFoundError(name)
_truetype = ImageFont.truetype
def _remap(font, *a, **k):
    if isinstance(font, str) and font.startswith("/usr/share/fonts/") and not os.path.exists(font):
        font = font_path(os.path.basename(font))
    return _truetype(font, *a, **k)
ImageFont.truetype = _remap

W, H, PX = 1080, 1920, 4
GW, GH = W // PX, H // PX
FPS, N = 30, 600
GROUND = 396                     # game-layer y of the floor

NAVY = (13, 13, 20); GRID = (24, 24, 38); PK = (240, 53, 158); PK2 = (184, 31, 117)
VIS = (23, 26, 43); CY = (0, 240, 255); GRY = (58, 63, 92); OUTL = (11, 12, 20)
PU = (120, 56, 170); YL = (255, 214, 0); GR = (57, 255, 136); RD = (255, 70, 90); WH = (255, 255, 255)
BIT_PAL = np.array([PK, PK2, VIS, CY, GRY, OUTL], np.float32)
# GLITCH (brand/glitch/build_glitch.py): hood, gunmetal face plate, hood highlight, lime, visor, outline
G_OL = (11, 12, 20); HOOD = (43, 47, 69); GUN = (58, 63, 85); G_HL = (74, 80, 112); LI = GR; G_VIS = (14, 26, 22)
GL_PAL = np.array([G_OL, HOOD, GUN, G_HL, LI, G_VIS], np.float32)
RD2 = (150, 20, 40)              # bug shading

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def lerp(a, b, u): return a + (b - a) * u
def mix(c1, c2, u): return tuple(round(lerp(a, b, u)) for a, b in zip(c1, c2))

# ---------------------------------------------------------------- beat grid
def load_beats():
    p = OUT / "beats.json"
    if p.exists():
        j = json.loads(p.read_text()); return j["beats"] + [j["beats"][-1] + 60 / j["bpm"]]
    return [i * 0.5 for i in range(41)]   # nominal 120 BPM until the track is measured (write_beats)
BEATS = load_beats()
def B(x):
    """Time of beat x (0-based, fractional allowed)."""
    i = int(math.floor(x)); f = x - i
    return BEATS[i] + f * (BEATS[i + 1] - BEATS[i]) if f else BEATS[i]
def since(t, b): return t - B(b)

# ---------------------------------------------------------------- Level 2 (bar 1 source frame + carried-over score)
_L2 = []
def level2():
    if not _L2:
        spec = importlib.util.spec_from_file_location("level2", LEVEL2)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        m.setup(); _L2.append(m)
    return _L2[0]
def l2_final_score():
    m = level2(); return m.score((m.N - 1) / m.FPS)       # the number on Level 2's last frame
L2_CROP = (28, 690, 1052, 948)                             # SCOPE / LOCKED ✓ on Level 2's plate
def l2_locked_frame():
    """Level 2's SCOPE LOCKED ✓ moment (its beat 35), the image GLITCH tears through: Level 2's game layer
    (arena, happy Bit) with only the SCOPE LOCKED ✓ lines on a plate; no BOSS DEFEATED, no Level 2 HUD."""
    m = level2(); f2 = round(m.B(35.2) * m.FPS); t2 = f2 / m.FPS
    full = m.frame(f2).convert("RGBA")
    g, _ = m.game_layer(t2, f2)
    im = scanlines(g.resize((W, H), Image.NEAREST)).convert("RGBA")
    x0, y0, x1, y1 = L2_CROP
    plate(im, (x0 - 4, y0 - 4, x1 + 4, y1 + 4))
    im.paste(full.crop(L2_CROP), (x0, y0))
    return im

# ---------------------------------------------------------------- pixel text
_FC = {}
def font(kind, size):
    k = (kind, size)
    if k not in _FC:
        _FC[k] = ImageFont.truetype(font_path("InterDisplay-Black.otf" if kind == "title" else "DejaVuSansMono-Bold.ttf"), size)
    return _FC[k]

_TC = {}
def ptext(s, size, fill, kind="mono", px=3, edge=OUTL, shadow=True, angle=0):
    """Un-antialiased text rendered at size/px and blown up px times, with a pixel outline (optionally rotated)."""
    key = (s, size, fill, kind, px, edge, shadow, angle)
    if key in _TC: return _TC[key]
    f = font(kind, round(size / px))
    x0, y0, x1, y1 = f.getbbox(s)
    m = Image.new("L", (x1 - x0 + 4, y1 - y0 + 4)); d = ImageDraw.Draw(m); d.fontmode = "1"
    d.text((2 - x0, 2 - y0), s, font=f, fill=255)
    out = Image.new("RGBA", m.size, (0, 0, 0, 0))
    if edge is not None:
        ring = m.filter(ImageFilter.MaxFilter(3))
        if shadow: out.paste(edge + (255,), (1, 1), ring)
        out.paste(edge + (255,), (0, 0), ring)
    out.paste(fill + (255,), (0, 0), m)
    if angle: out = out.rotate(angle, Image.NEAREST, expand=True)       # rotated on the small grid: stays pixel art
    out = out.resize((out.width * px, out.height * px), Image.NEAREST)
    hx0, hy0, hx1, hy1 = f.getbbox("H")
    out.info["text"] = s; out.info["cap"] = (hy1 - hy0) * px
    _TC[key] = out
    return out

def fit_size(s, size, maxw, **kw):
    """Largest size <= size at which ptext(s) is at most maxw wide."""
    while ptext(s, size, WH, **kw).width > maxw:
        size = round(size * maxw / ptext(s, size, WH, **kw).width) - 1
    return size
def fit(s, size, fill, maxw, **kw): return ptext(s, fit_size(s, size, maxw, **kw), fill, **kw)

# Shorts safe zone: platform buttons cover the bottom 350 px, and the right 140 px between y=700 and y=1600.
SAFE_BOTTOM, SAFE_RIGHT, SAFE_BAND = H - 350, W - 140, (700, 1600)
TEXT_BOXES = []                               # (text, box, cap) for every text sprite in the current frame

def _offscreen(x0, y0, x1, y1): return x0 < 0 or y0 < 0 or x1 > W or y1 > H
def _unsafe(x0, y0, x1, y1):
    return _offscreen(x0, y0, x1, y1) or y1 > SAFE_BOTTOM or (x1 > SAFE_RIGHT and y1 > SAFE_BAND[0] and y0 < SAFE_BAND[1])

def blit(im, spr, x, y, anchor="mm", scale=1.0):
    if "text" in spr.info:
        ax = {"l": 0, "m": 0.5, "r": 1}[anchor[0]]; ay = {"t": 0, "m": 0.5, "b": 1}[anchor[1]]
        box = lambda k: (x - spr.width * k * ax, y - spr.height * k * ay, x + spr.width * k * (1 - ax), y + spr.height * k * (1 - ay))
        while scale > 1.0 and _unsafe(*box(scale)): scale = max(1.0, scale - 0.02)   # slam overshoot stays on screen and safe
        if _offscreen(*box(scale)): return       # a word sliding in or out appears only once it is fully on screen
        w, h = spr.width * scale, spr.height * scale
        TEXT_BOXES.append((spr.info["text"], (x - w * ax, y - h * ay, x + w * (1 - ax), y + h * (1 - ay)), spr.info["cap"] * scale))
    if scale != 1.0:
        spr = spr.resize((max(1, round(spr.width * scale)), max(1, round(spr.height * scale))), Image.NEAREST)
    ax = {"l": 0, "m": 0.5, "r": 1}[anchor[0]]; ay = {"t": 0, "m": 0.5, "b": 1}[anchor[1]]
    comp(im, spr, round(x - spr.width * ax), round(y - spr.height * ay))

def comp(im, spr, x, y):
    """alpha_composite that crops a sprite hanging off any edge."""
    x, y = int(x), int(y)
    cx0, cy0 = max(0, -x), max(0, -y)
    cx1, cy1 = min(spr.width, im.width - x), min(spr.height, im.height - y)
    if cx1 <= cx0 or cy1 <= cy0: return
    if (cx0, cy0, cx1, cy1) != (0, 0, spr.width, spr.height): spr = spr.crop((cx0, cy0, cx1, cy1))
    im.alpha_composite(spr, (x + cx0, y + cy0))

# ---------------------------------------------------------------- dithering
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 + 1 / 32
def bayer(h, w): return np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w]
def dither_alpha(a):
    """Float alpha 0..1 -> hard 0/255 with an ordered 4x4 dither (pixel-art transparency)."""
    return np.where(a > bayer(*a.shape), 255, 0).astype(np.uint8)

def snap(svg, w, h, pal):
    """Render an SVG and snap every pixel to a palette, hard alpha: a crisp game sprite."""
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=w, output_height=h)
    a = np.array(Image.open(io.BytesIO(png)).convert("RGBA")).astype(np.float32)
    idx = ((a[..., :3][:, :, None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1)
    out = np.zeros_like(a, dtype=np.uint8)
    out[..., :3] = pal[idx]; out[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    return Image.fromarray(out)

# ---------------------------------------------------------------- Bit (Level 1/2 sprite; new arm poses for typing)
BIT_H = 156
EZ = BIT_H / 120
BK = BIT_H / 700
SVG = (BRAND / "bit/bit.svg").read_text()
def bit_arm(sx, sy, hx, hy):
    return (f'<line x1="{sx}" y1="{sy}" x2="{hx}" y2="{hy}" stroke="#0B0C14" stroke-width="62" stroke-linecap="round"/>'
            f'<line x1="{sx}" y1="{sy}" x2="{hx}" y2="{hy}" stroke="#F0359E" stroke-width="50" stroke-linecap="round"/>'
            f'<circle cx="{hx}" cy="{hy}" r="30" fill="#3A3F5C" stroke="#0B0C14" stroke-width="6" stroke-linejoin="round"/>')
BIT_HANDS = {"type": ((228, 548), (372, 548)), "type2": ((232, 534), (368, 534)), "crack": ((272, 520), (328, 520))}
def bit_svg(pose):
    s = re.sub(r'<g id="eyes">.*?</g>', "", SVG, flags=re.S)
    s = re.sub(r'<path id="mouth"[^>]*/>', "", s)          # visor shows eyes only in the game
    if pose == "idle":                                     # right arm down, mirroring the left
        s = s.replace('x2="478" y2="300"', 'x2="475" y2="500"').replace('cx="488" cy="280"', 'cx="482" cy="515"')
    elif pose in BIT_HANDS:                                # arms forward onto the keyboard, drawn in front of the body
        s = re.sub(r'<g id="arm-(left|right)">.*?</g>', "", s, flags=re.S)
        (lx, ly), (rx, ry) = BIT_HANDS[pose]
        s = s.replace("</svg>", bit_arm(190, 400, lx, ly) + bit_arm(410, 400, rx, ry) + "</svg>")
    return s
BIT_BASE = {}

def bit_sprite(pose, expr):
    spr = BIT_BASE[pose].copy(); d = ImageDraw.Draw(spr)
    ew, eh, lw = round(7 * EZ), round(10 * EZ), max(2, round(2 * EZ))
    for i, ex in enumerate((244, 356)):
        x0 = round(ex * BK - ew / 2); y0 = round(199 * BK - eh / 2); x1, y1 = x0 + ew - 1, y0 + eh - 1
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        if expr == "blink":
            d.rectangle((x0, round(my) - 1, x1, round(my)), fill=CY)
        elif expr == "determined":                      # flat lowered top, inner corner cut down like a brow
            top = y0 + round(eh * 0.35)
            d.rectangle((x0, top, x1, y1), fill=CY)
            ix, ox = (x1, x0) if i == 0 else (x0, x1)
            d.polygon([(ix, top), (ix - (4 if i == 0 else -4), top), (ix, top + 4)], fill=VIS)
        elif expr == "hit":
            d.line((x0, y0 + 1, x1, y1 - 1), fill=CY, width=lw); d.line((x1, y0 + 1, x0, y1 - 1), fill=CY, width=lw)
        elif expr == "happy":
            d.line((x0, y1 - 3, mx, y0 + 2), fill=CY, width=lw); d.line((mx, y0 + 2, x1, y1 - 3), fill=CY, width=lw)
        else:
            d.rectangle((x0, y0, x1, y1), fill=CY)
            for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)): d.point((cx, cy), fill=VIS)
    return spr
CHEST = (300, 447)                                        # Bit's </> screen centre in SVG units: where the TEST beam starts

# ---------------------------------------------------------------- GLITCH (brand/glitch/glitch.svg)
GSVG = (BRAND / "glitch/glitch.svg").read_text()
def gl_arm(sx, sy, hx, hy):
    S = 'stroke="#0B0C14" stroke-width="6" stroke-linejoin="round"'
    return (f'<line x1="{sx}" y1="{sy}" x2="{hx}" y2="{hy}" stroke="#0B0C14" stroke-width="58" stroke-linecap="square"/>'
            f'<line x1="{sx}" y1="{sy}" x2="{hx}" y2="{hy}" stroke="#2B2F45" stroke-width="46" stroke-linecap="square"/>'
            f'<rect x="{hx - 29}" y="{hy - 25}" width="58" height="50" rx="10" fill="#3A3F55" {S}/>')
GL_HANDS = {"type": ((222, 604), (378, 604)), "type2": ((232, 590), (368, 594)), "crack": ((272, 520), (328, 520)),
            "raise": ((130, 510), (470, 250))}
def glitch_svg(pose):
    s = re.sub(r'<g id="eyes">.*?</g>', "", GSVG, flags=re.S)
    s = re.sub(r'<path id="mouth"[^>]*/>', "", s)
    if pose in GL_HANDS:
        s = re.sub(r'<g id="arm-(left|right)">.*?</g>', "", s, flags=re.S)
        (lx, ly), (rx, ry) = GL_HANDS[pose]
        s = s.replace("</svg>", gl_arm(190, 400, lx, ly) + gl_arm(410, 400, rx, ry) + "</svg>")
    return s
GL_BASE = {}
def gl_base(pose, h):
    if (pose, h) not in GL_BASE: GL_BASE[pose, h] = snap(glitch_svg(pose), round(600 * h / 700), h, GL_PAL)
    return GL_BASE[pose, h]

# visor-only expressions, in SVG units (brand/glitch/build_glitch.py EXPR)
TYPE_DASHES = [(208, 186, 40), (254, 186, 14), (206, 204, 22), (234, 204, 34), (210, 222, 44),
               (330, 186, 22), (358, 186, 34), (334, 204, 48), (330, 222, 18), (354, 222, 30)]
def gl_eyes(spr, k, expr, f):
    d = ImageDraw.Draw(spr)
    def R(x, y, w, h, c):
        box = (round(x * k), round(y * k), round((x + w) * k) - 1, round((y + h) * k) - 1)
        if box[2] >= box[0] and box[3] >= box[1]: d.rectangle(box, fill=c)
    if expr == "smirk":                                    # left eye narrowed
        R(214, 200, 48, 34, LI); R(338, 178, 48, 58, LI)
    elif expr == "open":
        R(214, 178, 48, 58, LI); R(338, 178, 48, 58, LI)
    elif expr == "shocked":                                # hollow squares
        for x in (206, 330): R(x, 168, 64, 68, LI); R(x + 12, 180, 40, 44, G_VIS)
    elif expr in ("typing", "sulk"):                       # scrolling code dashes
        sp = (f * (9 if expr == "typing" else 3)) % 72
        for x, y, w in TYPE_DASHES:
            a0, a1 = (200, 272) if x < 300 else (326, 398)
            xx = a0 + (x - a0 + sp) % (a1 - a0)
            yy = y + (8 if expr == "sulk" else 0)
            R(xx, yy, min(w, a1 - xx), 10, LI)
            if w > a1 - xx: R(a0, yy, w - (a1 - xx), 10, LI)          # wraps round to the start of the line
    elif expr == "crashed":                                # static fills the visor
        r = np.random.default_rng(f)
        for i in range(70):
            R(r.uniform(186, 404), r.uniform(158, 268), r.choice([8, 14, 22]), 8, WH if r.random() < 0.3 else LI)

EYE_BAND = (176, 240)                                      # SVG y of his eyes (all four expressions live here)
GL_CUTS = [(488, 552), (60, 140)]                          # second cut: { } screen or hood rim
def gl_shift(spr, f, heavy=False, big=False):
    """His signature, in every frame: one slice through his eyes shifted 3 whole game pixels, plus one through
    his { } screen or his hood rim shifted 2-3 (both re-rolled every 2 frames). heavy = crashed (more slices);
    big = bar 1 close-up (one tall band through the visor, shoved 5-6 px)."""
    r = np.random.default_rng(1000 + f // 2)
    a = np.array(spr); hh = a.shape[0]; k = hh / 700
    def cut(y0, h, dx): a[y0:y0 + h] = np.roll(a[y0:y0 + h], dx, axis=1)
    sgn = lambda: 1 if r.random() < 0.5 else -1
    y_a, y_b = EYE_BAND
    h = max(3, round((y_b - y_a) * k * r.uniform(0.4, 0.6)))
    cut(round(r.uniform(y_a * k, y_b * k - h)), h, 3 * sgn())
    y_a, y_b = GL_CUTS[int(r.integers(0, len(GL_CUTS)))]
    h = max(2, round((y_b - y_a) * k * r.uniform(0.3, 0.5)))
    cut(round(r.uniform(y_a * k, y_b * k - h)), h, int(r.integers(2, 4)) * sgn())
    for _ in range(int(r.integers(3, 6)) if heavy else 0):
        h = int(r.integers(2, 10)); cut(int(r.integers(round(40 * k), hh - h)), h, int(r.integers(2, 4)) * sgn())
    if big:
        h = round(r.uniform(60, 110) * k); cut(round(r.uniform(150 * k, 290 * k - h)), h, int(r.choice([5, 6])) * sgn())
    return Image.fromarray(a)

def glitch_sprite(pose, expr, f, h=BIT_H, heavy=False, big=False):
    spr = gl_base(pose, h).copy(); gl_eyes(spr, h / 700, expr, f)
    return gl_shift(spr, f, heavy, big)

# ---------------------------------------------------------------- the bugs
BUG = ["...oo.", "oRRRRo", "RRWRRo", "oRRRRo", ".l..l."]   # 6x5 design, drawn at 2x: 12x10 game px; facing left
BUG_K = 2
def draw_bug(d, x, y, t, face=-1, seed=0):
    """12x10 pixel beetle (the 6x5 design with 2x2 pixels), top-left at (x, y)."""
    legs = int(t * 14 + seed) % 2
    for j, row in enumerate(BUG):
        if j == 4: row = ".l..l." if legs else "l..l.."
        for i, c in enumerate(row):
            if c == ".": continue
            col = {"o": OUTL, "R": RD, "W": WH, "l": OUTL}[c]
            if c == "R" and j == 3: col = RD2
            xi = i if face < 0 else 5 - i
            X, Y = round(x) + xi * BUG_K, round(y) + j * BUG_K
            d.rectangle((X, Y, X + BUG_K - 1, Y + BUG_K - 1), fill=col)

TICK = ["......g", ".....gg", "g...gg.", "gg.gg..", ".ggg...", "..g...."]
def draw_tick(d, x, y, col=GR, edge=OUTL, k=1):
    """7x6 pixel ✓ (k = pixel size) with a 1-px outline, top-left at (x, y)."""
    pts = [(x + i * k + a, y + j * k + b) for j, row in enumerate(TICK) for i, c in enumerate(row) if c == "g"
           for a in range(k) for b in range(k)]
    for px_, py_ in pts:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)): d.point((px_ + dx, py_ + dy), fill=edge)
    for p in pts: d.point(p, fill=col)

# ---------------------------------------------------------------- the beat sheet, in beats (0-based; brief beat = index + 1)
BIT_X, GL_X, DIV = 68, 202, 135
WIN = {"bit": (12, 118, 124, 196), "glitch": (146, 118, 258, 196)}       # game windows above each robot
COUNT = [(8, "3"), (9, "2"), (10, "1"), (11, "GO")]
GL_BLOCKS = [12.5, 13, 13.5, 14, 14.5, 15, 15.5]           # 7 blocks on the 8ths of bar 4: 70 %
SHIP = 16                                                  # SHIP IT! stamp: bar forced to 100 %, 3 slots still empty
BOOT_G, ERROR = 19, 20                                     # his game boots flashy for a beat, then ERROR
BUG_OUT = 21                                               # bugs pour out from here
BIT_PLACE = [12.5, 13.5, 14.5, 16.5, 17.5, 18.5, 20.5, 21.5, 22.5, 27.5]
BIT_TEST = [13, 14, 15, 17, 18, 19, 21, 22, 23, 28]         # TEST ✓ zaps: 30 % by bar 5, 60 % in bar 5, 100 % on beat 29
ZAPS = [24, 25, 26, 27]                                    # bar 7: BUG ×1..×4
BOOT_B = 28                                                # Bit's game boots clean: TESTED ✓
EAT = [28.5, 29, 29.5, 30, 30.5, 31, 31.5]                 # bugs eat Glitch's blocks one by one
CRASH, WIN_ = 32, 34                                       # CRASHED, BIT WINS
END = 36

# ---------------------------------------------------------------- blocks and windows
TILE = [PK, CY, YL, PU, PK, CY, YL, PU, CY, PK]
def block_rect(side, i):
    x0, y0, _, _ = WIN[side]; c, r = i % 5, i // 5
    return x0 + 7 + c * 20, y0 + 11 + r * 30, x0 + 7 + c * 20 + 17, y0 + 11 + r * 30 + 25

def draw_window(d, side, t):
    x0, y0, x1, y1 = WIN[side]
    head = PK if side == "bit" else LI
    d.rectangle((x0 - 2, y0 - 2, x1 + 2, y1 + 2), fill=OUTL)
    d.rectangle((x0, y0, x1, y1), fill=(10, 11, 20), outline=GRY, width=2)
    d.rectangle((x0, y0, x1, y0 + 7), fill=head)
    for i in range(3): d.rectangle((x0 + 4 + i * 6, y0 + 2, x0 + 7 + i * 6, y0 + 5), fill=OUTL)

def bit_blocks(d, t):
    for i, (pb, tb) in enumerate(zip(BIT_PLACE, BIT_TEST)):
        if t < B(pb) or t >= B(BOOT_B): continue
        bx0, by0, bx1, by1 = block_rect("bit", i)
        drop = round(-8 * (1 - ease(since(t, pb) / 0.12)))
        if t < B(tb):                                      # placed, not tested yet: grey outline, dim
            d.rectangle((bx0, by0 + drop, bx1, by1 + drop), fill=(30, 33, 52), outline=GRY)
            continue
        c = TILE[i]
        d.rectangle((bx0, by0, bx1, by1), fill=c)
        d.rectangle((bx0, by1 - 3, bx1, by1), fill=mix(c, OUTL, 0.4))
        d.rectangle((bx0, by0, bx1, by0 + 1), fill=mix(c, WH, 0.45))
        u = since(t, tb)
        if u < 0.1: d.rectangle((bx0, by0, bx1, by1), fill=WH)           # tested: white flash, then the tick
        draw_tick(d, bx1 - 8, by0 + 3)

def gl_blocks(d, t, f):
    eaten = sum(1 for b in EAT if t >= B(b))
    for i in range(10):
        bx0, by0, bx1, by1 = block_rect("glitch", i)
        if i >= len(GL_BLOCKS):                            # never built: empty slots
            if t >= B(SHIP): d.rectangle((bx0, by0, bx1, by1), outline=(70, 40, 60))
            continue
        if t < B(GL_BLOCKS[i]): continue
        if i < eaten: continue                             # chewed away
        r = np.random.default_rng(i)
        sk = int(r.integers(-2, 3)); sy = int(r.integers(-2, 3))      # slapped down crooked
        c = (LI, GUN, YL, CY)[i % 4]
        d.rectangle((bx0 + sk, by0 + sy, bx1 + sk, by1 + sy), fill=c)
        d.rectangle((bx0 + sk, by1 + sy - 3, bx1 + sk, by1 + sy), fill=mix(c, OUTL, 0.45))
        d.point((bx0 + sk + 3 + i % 4, by0 + sy + 5 + i % 3), fill=RD)      # a hidden bug in every block
        if i == eaten and t >= B(EAT[0]) and int(t * 12) % 2: d.rectangle((bx0 + sk, by0 + sy, bx1 + sk, by1 + sy), outline=RD)

def gl_window_inner(d, t, f):
    """Bar 6 onwards: flashy boot, then ERROR red, then (bar 9) static."""
    x0, y0, x1, y1 = WIN["glitch"]
    if B(BOOT_G) <= t < B(ERROR):                          # one beat of flashy rainbow boot
        k = int(t * FPS)
        cols = [PK, YL, LI, CY, PU]
        for j in range(y0 + 9, y1 - 1, 4): d.rectangle((x0 + 2, j, x1 - 2, j + 3), fill=cols[(j // 4 + k) % 5])
    elif B(ERROR) <= t < B(CRASH):
        d.rectangle((x0 + 2, y0 + 9, x1 - 2, y1 - 2), fill=(60, 10, 22) if int(t * 8) % 2 else (40, 8, 18))
    elif t >= B(CRASH):
        r = np.random.default_rng(f)
        a = r.random((y1 - y0 - 10, x1 - x0 - 3))
        for (yy, xx) in zip(*np.nonzero(a > 0.62)):
            d.point((x0 + 2 + xx, y0 + 9 + yy), fill=WH if a[yy, xx] > 0.9 else (GRY if a[yy, xx] > 0.75 else (40, 44, 64)))

COLLECT = [(29, 44), (31, 94), (33, 62)]                    # (beat, star x): the player jumps and grabs a star on each
HERO = ["..oooooooooooooooo..", ".oPPPPPPPPPPPPPPPPo.", "oPPWWPPPPPPPPPPPPPPo", "oPWWPPPPPPPPPPPPPPPo",
        "oPPPPPPPPPPPPPPPPPPo", "oPPPPPEEEPPPPEEEPPPo", "oPPPPPEEEPPPPEEEPPPo", "oPPPPPEEEPPPPEEEPPPo",
        "oPPPPPEEEPPPPEEEPPPo", "oPPPPPPPPPPPPPPPPPPo", "oPPPPPPPPPPPPPPPPPPo", "oPPPPPPPPPPPPPPPPPPo",
        "oPPPPPPPPPPPPPPPPPPo", "oDDPPPPPPPPPPPPPPDDo", "oDDDDDDDDDDDDDDDDDDo", ".oDDDDDDDDDDDDDDDDo.",
        "..oooooooooooooooo..", "...oooo......oooo...", "...oDDo......oDDo...", "...oooo......oooo..."]
STAR = ["....o....", "...oYo...", "..oYYYo..", "ooYYWYYoo", "oYYWWWYYo", "ooYYWYYoo", "..oYYYo..", "..oYoYo..", "..o...o.."]
def pix(d, x, y, rows, pal, flip=False, k=1):
    for j, row in enumerate(rows):
        for i, c in enumerate(row[::-1] if flip else row):
            if c != ".":
                X, Y = round(x) + i * k, round(y) + j * k
                d.rectangle((X, Y, X + k - 1, Y + k - 1), fill=pal[c])
GAME_GY = WIN["bit"][3] - 7                                # game floor y
def hero_state(t):
    """(x, y_top, flip, airborne) of the mini-game player: runs to each star, jumps on the beat to grab it."""
    pts = [(B(BOOT_B), 26)] + [(B(b) - 0.25, sx) for b, sx in COLLECT] + [(B(COLLECT[-1][0]) + 0.6, 30)]
    x, flip = pts[-1][1], True
    for (t0, x0_), (t1, x1_) in zip(pts, pts[1:]):
        if t0 <= t < t1: x = lerp(x0_, x1_, (t - t0) / (t1 - t0)); flip = x1_ < x0_; break
        if t < t0: x = x0_; break
    lift = 0.0
    for b, sx in COLLECT:                                  # jump: up 0.25 s, apex on the beat, down 0.25 s
        u = (t - (B(b) - 0.25)) / 0.5
        if 0 <= u < 1: x = sx; lift = 30 * math.sin(math.pi * u)
    if t >= B(COLLECT[-1][0]) + 0.6: lift = 6 * abs(math.sin(math.pi * since(t, COLLECT[-1][0]) / (B(1) - B(0))))   # happy hops
    return x - 10, GAME_GY - 20 - lift, flip, lift > 0

def bit_game(d, t):
    """Bit's booted game (original): a chunky pink hero runs, jumps on the beat and grabs big stars with a sparkle."""
    x0, y0, x1, y1 = WIN["bit"]
    ix0, iy0, ix1, iy1 = x0 + 2, y0 + 9, x1 - 2, y1 - 2
    d.rectangle((ix0, iy0, ix1, iy1), fill=(18, 16, 42))
    for sx, sy in ((22, 134), (58, 131), (104, 138), (80, 150), (34, 156)): d.point((sx, sy), fill=GRY)   # far stars
    gy = GAME_GY
    d.rectangle((ix0, gy, ix1, iy1), fill=PU); d.line((ix0, gy, ix1, gy), fill=PK, width=2)
    for xx in range(ix0 + (int(t * 20) % 8), ix1, 8): d.point((xx, gy + 3), fill=PK2)
    for b, sx in COLLECT:                                  # stars: big, bright, twinkling, until grabbed
        sy = gy - 20 - 30 - 2
        if t < B(b):                                       # 18x18: the 9x9 star at 2x, core twinkles
            tw = int(t * 8 + sx) % 3 == 0
            bob = round(math.sin(t * 6 + sx))
            pix(d, sx - 9, sy - 9 + bob, STAR, {"o": OUTL, "Y": YL, "W": WH if tw else (255, 245, 160)}, k=2)
        else:                                              # sparkle burst
            u = since(t, b) / 0.4
            if u < 1:
                for k in range(8):
                    a_ = k * math.pi / 4; r1, r2 = 6 + 16 * u, 12 + 20 * u
                    c = WH if k % 2 else YL
                    d.line((sx + math.cos(a_) * r1, sy + math.sin(a_) * r1, sx + math.cos(a_) * r2, sy + math.sin(a_) * r2), fill=c)
                if u < 0.25: d.ellipse((sx - 9, sy - 9, sx + 9, sy + 9), fill=WH)
    hx, hy, flip, air = hero_state(t)
    rows = HERO if air or int(t * 8) % 2 else HERO[:17] + ["....oooo....oooo....", "....oDDo....oDDo....", "....oooo....oooo...."]
    pix(d, hx, hy, rows, {"o": OUTL, "P": PK, "W": WH, "E": OUTL, "D": PK2}, flip)

def keyboard(d, cx, y, col, t, fast):
    """Small floating holo keyboard in front of a robot."""
    d.rectangle((cx - 22, y, cx + 22, y + 6), fill=OUTL)
    d.rectangle((cx - 21, y + 1, cx + 21, y + 5), fill=(16, 20, 32))
    k = int(t * (40 if fast else 8))
    for i in range(10):
        on = (k * 7 + i * 3) % 10 < (4 if fast else 2)
        d.point((cx - 19 + i * 4, y + 2), fill=col if on else GRY); d.point((cx - 17 + i * 4, y + 4), fill=GRY if on else col)

# ---------------------------------------------------------------- bugs: who is where
NB = 20
CROSS = [0, 4, 8, 12]                                       # these four charge across the divider, one per zap
ZAP_X = 116                                                # where Bit zaps them, just in front of him
def bug_pos(i, t):
    """(x, y, face) top-left in game coords, or None."""
    ts = B(BUG_OUT) + i * (B(0.125) - B(0))                # pour out: one every 32nd
    if t < ts: return None
    r = np.random.default_rng(50 + i)
    x0 = WIN["glitch"][0] + 14 + r.uniform(0, 76)
    u = (t - ts) / 0.35
    fy = GROUND - 10
    if u < 1:                                              # tumble out of the window to the floor
        return x0, lerp(WIN["glitch"][3] - 8, fy, u * u), -1
    if i in CROSS:
        j = CROSS.index(i)
        xq = ZAP_X + 34 * (B(ZAPS[j]) - t)                 # queue up and march left, 34 game px a second
        if t >= B(ZAPS[j]): return None
        k = clamp((t - ts - 0.35) / 0.4)
        return lerp(x0, xq, k), fy, -1
    tt = t - ts
    x = x0 + 14 * math.sin(1.7 * tt + i) + 6 * math.sin(4.1 * tt + 2 * i)
    face = -1 if math.cos(1.7 * tt + i) < 0 else 1
    if t >= B(EAT[0]) and i % 2:                           # half of them climb onto his window and chew it
        k = clamp(since(t, EAT[0]) / 0.5)
        wx = WIN["glitch"][0] + 10 + (i * 17) % 90
        return lerp(x, wx, k), lerp(fy, WIN["glitch"][1] + 14 + (i * 11) % 50, k), face
    return min(x, GW - 14), fy, face

# ---------------------------------------------------------------- choreography
def bit_state(t, f):
    """x, y offset (negative = up), squash, pose, expr."""
    x, y, sq, pose, expr = BIT_X, 0.0, 1.0, "idle", "idle"
    def jump(t0, h, dur=0.5):
        u = (t - t0) / dur
        return -4 * h * u * (1 - u) if 0 <= u < 1 else 0.0
    def land(t0, dur=0.18):
        u = (t - t0) / dur
        return 1 - 0.28 * math.sin(math.pi * u) if 0 <= u < 1 else 1.0
    if t < B(8):                                           # drops in under the wipe
        u = clamp(since(t, 7.5) / (B(8) - B(7.5))); y = -(GROUND + 40) * (1 - u * u)
    sq *= land(B(8))
    if B(8.5) <= t < B(9): pose = "crack"
    if B(11.5) <= t < B(BOOT_B):                           # types on the beat, zaps on the beat
        pose = "type" if int(t * 4) % 2 else "type2"
        if any(0 <= since(t, b) < 0.18 for b in BIT_TEST + ZAPS): pose = "idle"
    if t >= B(11): expr = "determined"
    if t >= B(BOOT_B): expr = "happy"
    if t >= B(BOOT_B): y += jump(B(BOOT_B), 26); sq *= land(B(BOOT_B) + 0.5)
    if t >= B(WIN_): y += jump(B(WIN_), 40); sq *= land(B(WIN_) + 0.5)
    if t >= B(END): y += jump(B(END), 34) + jump(B(38), 26); sq *= land(B(END) + 0.5) * land(B(38) + 0.5)
    if expr == "idle" and f % 90 in (40, 41, 42): expr = "blink"
    if y == 0 and sq == 1.0: y = round(2.5 * math.sin(t * 2 * math.pi * 0.6))
    return x, y, sq, pose, expr

def gl_state(t, f):
    x, y, sq, pose, expr = GL_X, 0.0, 1.0, "idle", "smirk"
    if t < B(8):
        u = clamp(since(t, 7.5) / (B(8) - B(7.5))); y = -(GROUND + 40) * (1 - u * u)
    u = since(t, 8) / 0.18
    if 0 <= u < 1: sq = 1 - 0.28 * math.sin(math.pi * u)
    if B(8.5) <= t < B(9): pose = "crack"
    if B(11.5) <= t < B(SHIP):                             # a blur: arms swap every frame, eyes scroll code
        pose = "type" if f % 2 else "type2"; expr = "typing"; x += 1 if f % 2 else -1
    if B(15.5) <= t < B(SHIP) + 0.15: pose = "raise"; expr = "smirk"
    u = since(t, SHIP) / 0.18
    if 0 <= u < 1: sq = 1 - 0.3 * math.sin(math.pi * u)
    if t >= B(ERROR): expr = "shocked"
    if B(ERROR) <= t < B(ERROR) + 0.25: y -= 10 * math.sin(math.pi * since(t, ERROR) / 0.25)      # jumps back in shock
    if t >= B(CRASH): expr = "crashed"
    if t >= B(END): expr, pose = "sulk", ("type" if f % 6 < 3 else "type2")                        # sulking, typing again
    if y == 0 and sq == 1.0: y = round(2 * math.sin(t * 2 * math.pi * 0.7 + 1))
    return x, y, sq, pose, expr

# ---------------------------------------------------------------- HUD numbers
def bit_prog(t): return sum(1 for b in BIT_TEST if t >= B(b))
def gl_prog(t):
    n = sum(1 for b in GL_BLOCKS if t >= B(b))
    return 10 if t >= B(SHIP) else n
def gl_red(t):
    """How many of Glitch's bar segments have gone red (bugs eating it), from the right."""
    if t >= B(CRASH): return 10
    if t < B(ERROR): return 0
    return 3 + sum(1 for b in EAT if t >= B(b))           # the 3 he never built, then one per bite
def score(t):
    ev = [(b, 100) for b in BIT_TEST] + [(b, 500) for b in ZAPS] + [(b, 500) for b, _ in COLLECT] + [(BOOT_B, 1000), (WIN_, 10000)]
    s = sum(a * ease(since(t, b) / 0.3) for b, a in ev if t >= B(b))
    return int(L2_SCORE + s + max(0, t - B(8)) * 37)

# ---------------------------------------------------------------- game layer
def arena():
    g = Image.new("RGBA", (GW, GH), NAVY + (255,)); d = ImageDraw.Draw(g)
    for x in range(0, GW, 15): d.line((x, 0, x, GH), fill=GRID)
    for y in range(0, GH, 15): d.line((0, y, GW, y), fill=GRID)
    for side, x0, x1, tint in (("bit", 0, DIV - 1, PK), ("glitch", DIV + 1, GW, LI)):     # tinted floors
        d.rectangle((x0, GROUND, x1, GROUND + 14), fill=mix(VIS, tint, 0.22))
        d.line((x0, GROUND, x1, GROUND), fill=mix(GRY, tint, 0.55), width=2)
        for x in range(x0, x1, 15): d.line((x, GROUND + 3, x, GROUND + 14), fill=mix(GRY, tint, 0.3))
    for y in range(92, GROUND + 15, 6): d.line((DIV, y, DIV, y + 3), fill=GRY)            # thin centre divider
    return g

def particles(seed, n, origin, t, t0, spread=90, life=1.2, cols=(YL, RD, WH), grav=60):
    r = np.random.default_rng(seed); out = []
    dt = t - t0
    if dt < 0 or dt > life: return out
    for i in range(n):
        a = r.uniform(0, 2 * math.pi); v = r.uniform(0.3, 1) * spread
        x = origin[0] + math.cos(a) * v * dt; y = origin[1] + math.sin(a) * v * dt + grav * dt * dt
        if r.random() > 1 - dt / life: continue
        out.append((x, y, cols[i % len(cols)], 2 if i % 3 else 3))
    return out

def shake(t):
    ev = [(CRASH, 4, 0.4), (ERROR, 3, 0.3), (SHIP, 3, 0.25), (8, 2, 0.15), (BOOT_B, 2, 0.15), (WIN_, 2, 0.2)]
    ev += [(b, 1, 0.1) for b in ZAPS]
    for b, amp, dur in ev:
        u = since(t, b)
        if 0 <= u < dur:
            k = int(t * FPS)
            return (amp if k % 2 else -amp) * round(1 - u / dur + 0.4), (amp if k % 3 else -amp) * round(1 - u / dur + 0.4)
    return 0, 0

def beam(d, a, b):
    """TEST zap: short cyan beam with a white core."""
    d.line((*a, *b), fill=CY, width=3); d.line((*a, *b), fill=WH, width=1)
    d.ellipse((b[0] - 4, b[1] - 4, b[0] + 4, b[1] + 4), outline=CY, width=1)

def trace_beam(d, a, b, u):
    """TEST zap into the window: out of the chest, round Bit's head like a circuit trace, up into the block."""
    lane = a[0] + 54
    pts = [a, (lane, a[1]), (lane, b[1] + 8), (b[0], b[1] + 8), b]
    for p, q in zip(pts, pts[1:]): d.line((*p, *q), fill=CY, width=3)
    for p, q in zip(pts, pts[1:]): d.line((*p, *q), fill=WH, width=1)
    d.ellipse((b[0] - 4, b[1] - 4, b[0] + 4, b[1] + 4), outline=CY, width=1)
    seg = [math.dist(p, q) for p, q in zip(pts, pts[1:])]; L = sum(seg) * clamp(u / 0.12)   # bright pulse runs along it
    for (p, q), s_ in zip(zip(pts, pts[1:]), seg):
        if L <= s_:
            k = L / s_ if s_ else 0; x, y = p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k
            d.rectangle((x - 2, y - 2, x + 2, y + 2), fill=WH); break
        L -= s_

def place(spr, x, y, sq):
    if sq != 1.0: spr = spr.resize((round(spr.width * (2 - sq)), round(spr.height * sq)), Image.NEAREST)
    return spr, round(x - spr.width / 2), round(GROUND - spr.height + y)

def game_layer(t, f):
    g = ARENA.copy(); d = ImageDraw.Draw(g)
    if t >= B(11.5):                                       # the two game windows pop up with GO
        for side in ("bit", "glitch"): draw_window(d, side, t)
        if t >= B(BOOT_B): bit_game(d, t)
        else: bit_blocks(d, t)
        if t >= B(BOOT_G): gl_window_inner(d, t, f)
        if t < B(CRASH) and not (B(BOOT_G) <= t < B(ERROR)): gl_blocks(d, t, f)
        if B(BOOT_B) <= t < B(BOOT_B) + 0.1: d.rectangle(WIN["bit"], fill=WH)
    # robots
    bx, by, bsq, bpose, bexpr = bit_state(t, f)
    bs, bx0, by0 = place(bit_sprite(bpose, bexpr), bx, by, bsq)
    comp(g, bs, bx0, by0)
    gx, gy, gsq, gpose, gexpr = gl_state(t, f)
    gs, gx0, gy0 = place(glitch_sprite(gpose, gexpr, f, heavy=t >= B(CRASH) and t < B(END)), gx, gy, gsq)
    comp(g, gs, gx0, gy0)
    if B(11.5) <= t < B(BOOT_B) and bpose in ("type", "type2"): keyboard(d, bx, GROUND - 38, CY, t, False)
    if (B(11.5) <= t < B(SHIP) - 0.25 or t >= B(END)) and gpose in ("type", "type2"):
        keyboard(d, gx, GROUND - 24, LI, t, t < B(SHIP))
        if t < B(SHIP):                                    # keystroke sparks and speed lines
            r = np.random.default_rng(f)
            for _ in range(6): d.point((gx + r.integers(-20, 21), GROUND - 28 - r.integers(0, 14)), fill=LI if r.random() < 0.7 else WH)
            for k in range(3):
                yy = GROUND - 52 + k * 7
                d.line((gx - 50 - (f * 5 + k * 7) % 12, yy, gx - 42 - (f * 5 + k * 7) % 12, yy), fill=WH)
                d.line((gx + 42 + (f * 5 + k * 7) % 12, yy, gx + 50 + (f * 5 + k * 7) % 12, yy), fill=WH)
    if B(8.5) <= t < B(9) and int(t * 20) % 2:             # knuckle crack sparks
        for cx in (bx, gx):
            for dx, dy in ((-6, -2), (6, -3), (-3, -7), (4, -8)): d.point((cx + dx, GROUND - 40 + dy), fill=WH)
    chest = (bx, GROUND - BIT_H + CHEST[1] * BK + by)
    for i, b in enumerate(BIT_TEST[:-1]):                  # TEST ✓ beams into the window
        if 0 <= since(t, b) < 0.15:
            x0, y0, x1, y1 = block_rect("bit", i); trace_beam(d, chest, ((x0 + x1) / 2, y1), since(t, b))
    for i, b in enumerate(BIT_TEST[6:9]):                   # bar 6: no TEST ✓ label, a ✓ pops out of the window instead
        u = since(t, b)
        if 0 <= u < 0.45:
            bx0_, by0_, bx1_, _ = block_rect("bit", 6 + i)
            draw_tick(d, (bx0_ + bx1_) / 2 - 7, WIN["bit"][1] - 16 - round(10 * ease(u / 0.3)), k=2)
    if t >= B(SHIP):                                       # confetti on his side
        wx0, wy0, wx1, wy1 = WIN["glitch"]
        for px_, py_, c, sz in particles(7, 70, ((wx0 + wx1) / 2, wy0 + 10), t, B(SHIP), spread=110, life=1.6, cols=(LI, YL, WH, CY)):
            if px_ > DIV + 2: d.rectangle((px_, py_, px_ + sz - 1, py_ + sz - 1), fill=c)
    # bugs
    for i in range(NB):
        p = bug_pos(i, t)
        if p and not (t >= B(CRASH) and i % 2 and p[1] < GROUND - 20): draw_bug(d, *p[:2], t, p[2], seed=i)
    for j, b in enumerate(ZAPS):                           # zap -> bug becomes a green tick and pops
        u = since(t, b)
        if 0 <= u < 0.15: beam(d, chest, (ZAP_X + 6, GROUND - 5))
        if 0 <= u < 0.6:
            draw_tick(d, ZAP_X - 1, GROUND - 16 - round(34 * ease(u / 0.5)), k=2)
            for px_, py_, c, sz in particles(30 + j, 16, (ZAP_X + 6, GROUND - 5), t, B(b), spread=60, life=0.5, cols=(GR, WH)):
                d.rectangle((px_, py_, px_ + sz - 1, py_ + sz - 1), fill=c)
    if t >= B(WIN_):                                       # BIT WINS confetti on his side
        for px_, py_, c, sz in particles(9, 80, (bx, GROUND - 170), t, B(WIN_), spread=130, life=1.8, cols=(PK, CY, YL, WH)):
            if px_ < DIV - 2: d.rectangle((px_, py_, px_ + sz - 1, py_ + sz - 1), fill=c)
    return g

def scanlines(im):
    a = np.array(im); a[3::4] = (a[3::4] * 0.82).astype(np.uint8); return Image.fromarray(a)

# ---------------------------------------------------------------- full-res overlays (Level 1/2 layout)
UI = dict(hud=dict(bottom=350, bit=(48, 28), glitch=(1032, 28), score_lbl=(540, 28), score=(540, 112), bars_y=(206, 266)),
          card_y=400, count=(540, 840), combo=(540, 880),
          title=dict(box=(36, 380, 1044, 1240), lines=[(200, 560), (190, 800), (190, 1035)], maxw=800, mini=(270, 810)),
          win=dict(plate=(24, 375, 1056, 700), y=540, size=230, maxw=960),
          end=dict(plate=(24, 150, 1056, 960), cx=540, maxw=960,
                   lines=[("WHO SHOULD", 36, WH, 270), ("BIT RACE", 36.5, PK, 425), ("NEXT?", 37, YL, 580)],
                   ask=("↓ COMMENTS", 38, CY, 740), handle=("@vibewithamitai", 38.5, CY, 870)))
TEXT_W = 800

def bar(d, x0, y0, y1, n, col, hi, red=0, flash=False):
    """10-segment build bar: n lit, the last `red` lit ones turned red."""
    for i in range(10):
        sx = x0 + i * 45
        d.rectangle((sx - 4, y0 - 4, sx + 42, y1 + 4), fill=OUTL)
        lit = i < n; isred = lit and i >= 10 - red
        c = (RD if isred else (WH if flash else col)) if lit else (35, 38, 58)
        d.rectangle((sx, y0, sx + 38, y1), fill=c)
        if lit and not isred: d.rectangle((sx, y0, sx + 38, y0 + 8), fill=hi)

def hud(im, t):
    if t < B(8): return
    L = UI["hud"]
    u = ease(since(t, 8) / 0.35)
    out = clamp(since(t, 35.5) / 0.3) if t >= B(35.5) else 0
    dy = round(-L["bottom"] * (1 - u) - (L["bottom"] + 20) * out)
    if L["bottom"] + dy <= 0: return
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, L["bottom"] + dy), fill=(8, 8, 14))
    d.line((0, L["bottom"] + dy, W, L["bottom"] + dy), fill=GRY, width=4)
    blit(im, ptext("BIT", 72, WH), L["bit"][0], L["bit"][1] + dy, "lt")
    blit(im, ptext("GLITCH", 72, LI), L["glitch"][0], L["glitch"][1] + dy, "rt")
    blit(im, ptext("SCORE", 72, WH), L["score_lbl"][0], L["score_lbl"][1] + dy, "mt")
    blit(im, ptext(f"{score(t):06d}", 72, YL), L["score"][0], L["score"][1] + dy, "mt")
    y0, y1 = L["bars_y"]; y0 += dy; y1 += dy
    bflash = any(0 <= since(t, b) < 0.1 for b in BIT_TEST)
    bar(d, 48, y0, y1, bit_prog(t), CY, (170, 255, 255), flash=bflash)
    gflash = 0 <= since(t, SHIP) < 0.3 and int(t * 15) % 2 == 0
    bar(d, W - 48 - 9 * 45 - 38, y0, y1, gl_prog(t), LI, (180, 255, 210), red=gl_red(t), flash=gflash)

def slam(t, b, dur=0.12):
    """Scale for a word slamming in on beat b: big -> 1."""
    u = since(t, b) / dur
    return None if u < 0 else (1 + 0.6 * (1 - ease(u)) if u < 1 else 1.0)

def title_card(im, t, f):
    L = UI["title"]; d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = L["box"]
    d.rectangle((x0, y0, x1, y1), fill=(8, 8, 14), outline=PU, width=12); d.rectangle((x0 + 24, y0 + 24, x1 - 24, y1 - 24), outline=GRY, width=4)
    (s0, y_lv), (s1, y_a), (s2, y_b) = L["lines"]
    size = fit_size("LEVEL 3", s0, L["maxw"], kind="title", px=5)                # "LEVEL" then "3", one per beat, one line
    full = ptext("LEVEL 3", size, YL, kind="title", px=5)
    lv, three = ptext("LEVEL", size, YL, kind="title", px=5), ptext("3", size, YL, kind="title", px=5)
    left, right = W / 2 - full.width / 2, W / 2 + full.width / 2
    for spr, cx, b in ((lv, left + lv.width / 2, 4), (three, right - three.width / 2, 5)):
        sc = slam(t, b)
        if sc is not None: blit(im, spr, cx, y_lv, "mm", sc)
    for s, b, col, size_, y in (("BUILD", 6, WH, s1, y_a), ("RACE", 7, PK, s2, y_b)):
        sc = slam(t, b)
        if sc is not None: blit(im, fit(s, size_, col, L["maxw"], kind="title", px=5), W / 2, y, "mm", sc)
    bob = round(6 * math.sin(t * 2 * math.pi * 0.6)) * 2
    spr = bit_sprite("idle", "blink" if f % 90 in (40, 41, 42) else "idle")      # small pixel Bit and GLITCH on the floor
    blit(im, spr.resize((spr.width * 2, spr.height * 2), Image.NEAREST), L["mini"][0], GROUND * PX + bob, "mb")
    gs = glitch_sprite("idle", "smirk", f)
    blit(im, gs.resize((gs.width * 2, gs.height * 2), Image.NEAREST), L["mini"][1], GROUND * PX - bob, "mb")

def wipe_mask(t, t0, dur, reverse=False):
    """Blocks (60 px) swept diagonally; returns (covered, edge) boolean grids."""
    u = (t - t0) / dur
    nx, ny = W // 60, H // 60
    gx, gy = np.meshgrid(np.arange(nx), np.arange(ny))
    k = (gx + gy) / (nx + ny - 2)
    if reverse: k = 1 - k
    return k < u, (k < u) & (k > u - 0.12)

def draw_wipe(im, t, t0, dur, reverse=False):
    cov, edge = wipe_mask(t, t0, dur, reverse)
    nav = Image.new("RGBA", (W, H), NAVY + (255,))
    m = ((~cov if reverse else cov).repeat(60, 0).repeat(60, 1) * 255).astype(np.uint8)
    im.paste(nav, (0, 0), Image.fromarray(m))
    d = ImageDraw.Draw(im)
    for (gy, gx) in zip(*np.nonzero(edge)):
        d.rectangle((gx * 60, gy * 60, gx * 60 + 59, gy * 60 + 59), fill=CY if (gx + gy) % 2 else PK)

def card(im, lines, y, border, t, t0, t_out=None):
    """Panel that drops in from the top and stops centred (Level 2's card, dropping instead of sliding)."""
    sprs = [fit(s, sz, c, TEXT_W - 96, kind=k) for s, sz, c, k in lines]
    h = sum(s.height for s in sprs) + 28 * (len(sprs) + 1)
    w = max(s.width for s in sprs) + 96
    u = ease((t - t0) / 0.25)
    yy0 = round(lerp(-h - 20, y, u))
    if t_out is not None and t >= t_out: yy0 = round(lerp(y, -h - 20, clamp((t - t_out) / 0.2) ** 2))
    x = round(W / 2 - w / 2)
    d = ImageDraw.Draw(im)
    d.rectangle((x - 8, yy0 - 8, x + w + 8, yy0 + h + 8), fill=OUTL)
    d.rectangle((x, yy0, x + w, yy0 + h), fill=(20, 16, 34), outline=border, width=8)
    yy = yy0 + 28
    for s in sprs:
        blit(im, s, W / 2, yy, "mt"); yy += s.height + 28

def plate(im, box, k=1.0):
    """Dark backing so debris never reads through the big words."""
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.rectangle(box, fill=(8, 8, 14, round(225 * k)))
    d.rectangle(box, outline=GRY + (round(255 * k),), width=4)
    im.alpha_composite(g)

def flash(im, t, b, dur=0.1, a=160):
    u = since(t, b)
    if 0 <= u < dur: im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, round(a * (1 - u / dur)))))

# ---------------------------------------------------------------- bar 1: GLITCH tears through Level 2
_CAM = {}
def closeup(expr, f):
    """GLITCH's head filling the screen, same 4x pixel grid, on the arena background."""
    h = 560; k = h / 700
    g = Image.new("RGBA", (GW, GH), NAVY + (255,)); d = ImageDraw.Draw(g)
    for x in range(0, GW, 15): d.line((x, 0, x, GH), fill=GRID)
    for y in range(0, GH, 15): d.line((0, y, GW, y), fill=GRID)
    spr = glitch_sprite("idle", expr, f, h=h, big=True)
    comp(g, spr, round(GW / 2 - spr.width / 2), round(GH * 0.42 - 210 * k))
    return scanlines(g.resize((W, H), Image.NEAREST))

def static_noise(f, density):
    r = np.random.default_rng(f + 77)
    a = r.random((GH, GW))
    rgb = np.zeros((GH, GW, 4), np.uint8)
    on = a < density
    v = (r.random((GH, GW)) * 200 + 55).astype(np.uint8)
    rgb[..., 0] = v; rgb[..., 1] = v; rgb[..., 2] = v
    lime = r.random((GH, GW)) < 0.25
    rgb[lime, 0], rgb[lime, 1], rgb[lime, 2] = LI
    rgb[..., 3] = np.where(on, 255, 0)
    return Image.fromarray(rgb).resize((W, H), Image.NEAREST)

def tear(base, face, f, p):
    """Rows of 4-px-aligned bands: a share p of them show GLITCH, all shifted sideways by whole game pixels."""
    r = np.random.default_rng(f * 3 + 1)
    a = np.array(base); fa = np.array(face)
    y = 0
    while y < H:
        h = int(r.integers(2, 14)) * PX
        src = fa if r.random() < p else a
        dx = int(r.integers(-6, 7)) * PX if r.random() < 0.6 * (1 - p) + 0.1 else 0
        a[y:y + h] = np.roll(src[y:y + h], dx, axis=1)
        y += h
    return Image.fromarray(a)

def rgb_split(im, dx):
    a = np.array(im); b = a.copy()
    b[..., 0] = np.roll(a[..., 0], dx, axis=1); b[..., 2] = np.roll(a[..., 2], -dx, axis=1)
    return Image.fromarray(b)

def cameo(im, t, f):
    base = L2_FRAME
    if t < B(1):                                           # static burst on beat 1, the old frame breaking up
        u = since(t, 0)
        k = clamp(1 - u / 0.13)                            # heavy for 4 frames, then SCOPE LOCKED ✓ reads through it
        out = tear(base, closeup("typing", f), f, 0.04 if u > 0.25 else 0.0)
        if (f // 2) % 2 == 0 or u < 0.13: out = rgb_split(out, PX * (2 if u < 0.13 else 1))
        out.alpha_composite(static_noise(f, 0.10 + 0.65 * k))
    elif t < B(1.75):                                      # GLITCH tears through, band by band
        p = 0.25 + 0.75 * ease(since(t, 1) / (B(1.75) - B(1)))
        out = tear(base, closeup("typing", f), f, p)
        out = rgb_split(out, PX)
        out.alpha_composite(static_noise(f, 0.10 * (1 - p) + 0.02))
    else:                                                  # full face: typing, then the smirk on beat 3
        out = closeup("smirk" if t >= B(2) else "typing", f)
        if (f // 2) % 3 == 0: out = tear(out, out, f, 1.0)            # he never quite holds still
        if (f // 3) % 4 == 0: out = rgb_split(out, PX)
        out.alpha_composite(static_noise(f, 0.025))
        if t >= B(2) and since(t, 2) < 0.1:
            out = rgb_split(out, PX * 2)
    comp(im, out, 0, 0)

# ---------------------------------------------------------------- frame
def level(im, t, f):
    g = game_layer(t, f)
    off = shake(t)
    comp(im, scanlines(g.resize((W, H), Image.NEAREST)), off[0] * PX, off[1] * PX)
    return off

def overlays(im, t, f, off):
    ox, oy = off[0] * PX, off[1] * PX
    wx = lambda side: ((WIN[side][0] + WIN[side][2]) / 2 * PX + ox, (WIN[side][1] + WIN[side][3]) / 2 * PX + oy)
    if B(8) <= t < B(11.5):                                # bar 3: the prompt drops in between them
        card(im, [("PROMPT:", 72, YL, "mono"), ("MAKE A GAME", 104, WH, "title")], UI["card_y"], PU, t, B(8), B(11.25))
    for b, s in COUNT:                                     # 3, 2, 1, GO: one per beat
        if B(b) <= t < B(b + 1) - (0.1 if s == "GO" else 0):
            col = GR if s == "GO" else YL
            blit(im, ptext(s, 300, col, kind="title", px=5), *UI["count"], "mm", slam(t, b, 0.12))
    for i, b in enumerate(BIT_TEST[:6]):                   # TEST ✓ over Bit's window (bars 4-5)
        if 0 <= since(t, b) < 0.42:
            blit(im, ptext("TEST ✓", 92, CY, kind="title", px=4), 272 + ox, WIN["bit"][1] * PX - 58 + oy, "mm", slam(t, b, 0.1))
    if B(SHIP) <= t < B(BOOT_G):                           # SHIP IT! stamp on his unfinished game
        x, y = wx("glitch")
        blit(im, ptext("SHIP IT!", 116, YL, kind="title", px=5, angle=8), x, y - 30, "mm", slam(t, SHIP, 0.1))
    if B(ERROR) <= t < B(CRASH) and (t < B(ERROR) + 0.4 or int(since(t, ERROR) * 6) % 3):
        x, y = wx("glitch")
        blit(im, ptext("ERROR", 120, RD, kind="title", px=5), x, y, "mm", slam(t, ERROR, 0.1))
    n = sum(1 for b in ZAPS if t >= B(b))                  # BUG ×1..×4 combo
    if n and t < B(BOOT_B):
        blit(im, ptext(f"BUG ×{n}", 150, YL, kind="title", px=5), *UI["combo"], "mm", slam(t, ZAPS[n - 1], 0.12))
    if B(BOOT_B) <= t < B(WIN_):
        x, y = wx("bit")
        blit(im, fit("TESTED ✓", 120, GR, 500, kind="title", px=5), x, 872 + oy, "mm", slam(t, BOOT_B, 0.12))
    for b, sx in COLLECT:                                  # +500 rises off each star Bit's game hero grabs
        u = since(t, b)
        if 0 <= u < 0.5 and t < B(WIN_):
            blit(im, ptext("+500", 72, YL), sx * PX + ox, (GAME_GY - 52) * PX - 40 - round(50 * ease(u / 0.5)) + oy, "mm")
    if B(CRASH) <= t < B(WIN_):
        x, y = wx("glitch")
        blit(im, fit("CRASHED", 120, RD, 480, kind="title", px=5), x, y, "mm", slam(t, CRASH, 0.12))
    if t >= B(WIN_):
        Wn = UI["win"]
        if t < B(35.5):
            plate(im, Wn["plate"], ease(since(t, WIN_) / 0.1))
            blit(im, fit("BIT WINS", Wn["size"], PK, Wn["maxw"], kind="title", px=5), W / 2, Wn["y"], "mm", slam(t, WIN_, 0.15))
        else:                                              # the plate grows into the end card's plate
            k = ease(since(t, 35.5) / (B(36) - B(35.5)))
            plate(im, tuple(round(lerp(a, b, k)) for a, b in zip(Wn["plate"], UI["end"]["plate"])))
    if t >= B(END): end_card(im, t)

_END = []
def end_size():
    if not _END:
        size = 260
        while max(ptext(s, size, WH, kind="title", px=4).width for s, *_ in UI["end"]["lines"]) > UI["end"]["maxw"]: size -= 2
        _END.append(size)
    return _END[0]

def end_card(im, t):
    E = UI["end"]; big = end_size()
    for s, b, col, y in E["lines"]:
        sc = slam(t, b, 0.12)
        if sc and t >= B(39): sc = slam(t, 39, 0.15)
        if sc: blit(im, ptext(s, big, col, kind="title", px=4), E["cx"], y, "mm", sc)
    s, b, col, y = E["ask"]
    sc = slam(t, b, 0.12)
    alt = t >= B(38.5) and int(since(t, 38.5) / (B(39) - B(38.5))) % 2 == 1
    if sc: blit(im, ptext(s, 120, PK if alt else col, kind="mono", px=3), E["cx"], y, "mm", sc)
    s, b, col, y = E["handle"]
    sc = slam(t, b, 0.12)
    if sc: blit(im, ptext(s, 72, col, kind="mono", px=3), E["cx"], y, "mm", sc)
    flash(im, t, 39, 0.1, 45)

def frame(f):
    t = f / FPS
    TEXT_BOXES.clear()
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    if t < B(4):
        cameo(im, t, f)
        if t >= B(3.5): draw_wipe(im, t, B(3.5), B(4) - B(3.5))
        return im.convert("RGB")
    if t < B(7.5):                                         # bar 2: title card over the empty split arena
        comp(im, scanlines(ARENA.resize((W, H), Image.NEAREST)), 0, 0)
        title_card(im, t, f)
        return im.convert("RGB")
    off = level(im, t, f)
    if t < B(8): draw_wipe(im, t, B(7.5), B(8) - B(7.5), reverse=True)
    hud(im, t)
    overlays(im, t, f, off)
    return im.convert("RGB")

def safe_zone_violations(f):
    bad = []
    for s, (x0, y0, x1, y1), cap in TEXT_BOXES:
        if _offscreen(x0, y0, x1, y1): bad.append((f, s, "off screen", tuple(round(v) for v in (x0, y0, x1, y1))))
        elif _unsafe(x0, y0, x1, y1): bad.append((f, s, "safe zone", tuple(round(v) for v in (x0, y0, x1, y1))))
        if cap < 48: bad.append((f, s, f"cap height {cap:.0f} px"))
    return bad

def setup():
    g = globals()
    g["BIT_BASE"] = {p: snap(bit_svg(p), round(600 * BK), BIT_H, BIT_PAL) for p in ("idle", "fire", "type", "type2", "crack")}
    g["ARENA"] = arena()
    g["L2_SCORE"] = l2_final_score()
    g["L2_FRAME"] = l2_locked_frame()
    _END.clear()

# ---------------------------------------------------------------- sound (Levels 1-2's engine and kit)
SR, BPM = 44100, 120
SPB = 60 / BPM
NS = N * SR // FPS                                           # exactly 20.0 s of samples
RNG = np.random.default_rng(11)
def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def tt(dur): return np.arange(int(dur * SR)) / SR
def adsr(n, a=0.004, d=0.08, s=0.5, r=0.02):
    e = np.full(n, s, np.float32); ai, di, ri = int(a * SR), int(d * SR), int(r * SR)
    e[:ai] = np.linspace(0, 1, ai); e[ai:ai + di] = np.linspace(1, s, len(e[ai:ai + di]))
    if ri: e[-ri:] *= np.linspace(1, 0, ri)
    return e
def sweep(f0, f1, dur, shape="sq", duty=0.5, curve=1.0):
    x = tt(dur); f = f0 + (f1 - f0) * (x / dur) ** curve
    ph = np.cumsum(f) / SR % 1
    if shape == "sq": return np.where(ph < duty, 1.0, -1.0)
    if shape == "tri": return 4 * np.abs(ph - 0.5) - 1
    return np.sin(2 * np.pi * ph)
def tone(m, dur, shape="sq", duty=0.5, **env):
    return sweep(hz(m), hz(m), dur, shape, duty) * adsr(int(dur * SR), **env)
def noise(dur): return RNG.uniform(-1, 1, int(dur * SR))
def lowpass(x, k):
    """One-pole lowpass, k in (0,1]: smaller = darker."""
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x): acc += k * (v - acc); y[i] = acc
    return y
def decay(n, tau): return np.exp(-np.arange(n) / (tau * SR))
def put(buf, t, x, vol=1.0):
    i = int(round(t * SR)); x = x[: max(0, len(buf) - i)]
    if i >= 0: buf[i:i + len(x)] += x * vol

# --- drums (same kit as Levels 1-2)
def kick(): x = sweep(160, 40, 0.16, "tri", curve=0.4); return x * decay(len(x), 0.05)
def snare(): n = noise(0.14); return (n * 0.8 + sweep(220, 160, 0.14, "tri") * 0.4) * decay(len(n), 0.04)
def hat(): n = np.diff(noise(0.035), prepend=0) * 0.5; return n * decay(len(n), 0.008)
def crash(): n = np.diff(noise(1.0), prepend=0) * 0.4; return n * decay(len(n), 0.3)

A, C, D, E, F, G = 57, 60, 62, 64, 65, 67                    # A3 = 57
def music():
    """Level 3 theme: 120 BPM, A minor, new 8-bar melody over bars 2-9, faster than Level 2:
    16th-note arpeggios and four-on-the-floor through the race (bars 4-7). Bar 1 has no music (static + GLITCH)."""
    buf = np.zeros(NS + SR, np.float32)
    bt = lambda bar, beat: ((bar - 1) * 4 + beat) * SPB      # composer's grid: bar 1-10, beat 0-3.75
    roots = {2: [A], 3: [E], 4: [A], 5: [F], 6: [D, E], 7: [A, G], 8: [C], 9: [F, E]}
    for bar, rs in roots.items():                            # triangle bass: 8ths, 16ths in the race
        n = 16 if 4 <= bar <= 7 else 8
        for i in range(n):
            if bar == 9 and 2 <= i * 8 // n < 4: continue    # bass drops out under CRASHED, back for BIT WINS
            r = rs[min(i // (n // len(rs)), len(rs) - 1)] - 12
            put(buf, bt(bar, i * 4 / n), tone(r + (12 if i % 2 else 0), SPB * 4 / n * 0.9, "tri", s=0.8), 0.30)
    for b in range(4):                                       # bar 2: snare + kick on every title word
        put(buf, bt(2, b), snare(), 0.5); put(buf, bt(2, b), kick(), 0.6)
    for b in range(4): put(buf, bt(3, b), kick(), 0.7); put(buf, bt(3, b + 0.5), hat(), 0.3)   # bar 3: the count
    for bar in (4, 5, 6, 7):                                 # the race: four on the floor, snare 2 & 4, 16th hats
        for b in range(4):
            put(buf, bt(bar, b), kick(), 0.7)
            if b in (1, 3): put(buf, bt(bar, b), snare(), 0.45)
            for q in range(4): put(buf, bt(bar, b + q / 4), hat(), 0.32 if q == 2 else 0.18)
    for i in range(8): put(buf, bt(7, 2 + i / 4), snare(), 0.12 + 0.05 * i)      # roll into the clean boot
    for b in range(4):                                       # bar 8: backbeat, happy
        if b in (0, 2): put(buf, bt(8, b), kick(), 0.7)
        if b in (1, 3): put(buf, bt(8, b), snare(), 0.45)
        put(buf, bt(8, b + 0.5), hat(), 0.3)
    put(buf, bt(9, 0), kick(), 0.8); put(buf, bt(9, 2), kick(), 0.8); put(buf, bt(9, 3), kick(), 0.6); put(buf, bt(9, 3), snare(), 0.4)
    put(buf, bt(4, 0), crash(), 0.5); put(buf, bt(8, 0), crash(), 0.6)
    arp = {4: [A, C, E, A + 12], 5: [F - 12, A, C, F], 6: [D, F, A, D + 12, E, G + 1, 59, E + 12], 7: [A, C, E, A + 12, G - 12, 59, D, G]}
    for bar, ns in arp.items():                              # 16th-note arpeggios: race energy
        for i in range(16):
            m = ns[(i % 4) + (4 if len(ns) == 8 and i >= 8 else 0)]
            put(buf, bt(bar, i / 4), tone(m + 12, SPB / 4 * 0.8, duty=0.125, s=0.4), 0.075)
    lead = {                                                 # square lead, 25% duty, 8th notes (None = rest)
        2: [76, None, 76, 79, 81, None, 79, 76],             # Am  - the hook, under LEVEL 3: BUILD RACE
        3: [76, None, 75, None, 76, None, 83, None],         # E   - 3, 2, 1, GO (chromatic wind-up)
        4: [81, 79, 81, 84, 83, 81, 79, 76],                 # Am  - race
        5: [77, 81, 84, 89, 88, 84, 81, 77],                 # F   - SHIP IT!
        6: [74, 77, 81, 80, None, 80, 83, 86],               # Dm E - ERROR (G# leading note)
        7: [81, 84, 88, 84, 83, 86, 91, 86],                 # Am G - BUG x1..x4
        8: [84, 88, 91, 88, 84, 86, 88, 91],                 # C   - TESTED, the clean game
        9: [89, None, None, None, None, None, None, None]}   # F   - CRASHED, then the win sting SFX
    for bar, ns in lead.items():
        for i, m in enumerate(ns):
            if m: put(buf, bt(bar, i / 2), tone(m, SPB / 2 * 0.85, duty=0.25, s=0.6), 0.10 if bar == 2 else 0.12)
    for i, m in enumerate([73, 76, 81]):                     # bar 10: outro stabs, A major
        put(buf, bt(10, i), tone(m + 12, SPB * 0.7, duty=0.25, s=0.5), 0.14); put(buf, bt(10, i), kick(), 0.5)
    return buf[:NS]

# --- SFX: Levels 1-2's set, plus keystroke, static, error buzz, skitter, test zap, crash
def coin(): return np.concatenate([tone(83, 0.07, duty=0.5, s=1), tone(88, 0.3, duty=0.5, d=0.25, s=0.0)])
def thump(): x = sweep(120, 32, 0.3, "sin", curve=0.5); return x * decay(len(x), 0.09) + np.pad(snare()[:2000], (0, len(x) - 2000)) * 0.3
def jump(): x = sweep(300, 1000, 0.16, duty=0.25, curve=0.7); return x * adsr(len(x), d=0.1, s=0.3)
def whoosh():
    n = noise(0.24); e = np.sin(np.linspace(0, np.pi, len(n))) ** 2
    return (lowpass(n, 0.25) - lowpass(n, 0.03)) * e * 2
def victory():
    out = np.zeros(int(1.3 * SR))
    for i, m in enumerate([69, 73, 76, 81]):
        x = tone(m + 12, 1.3 - i * 0.04, duty=0.25, d=0.5, s=0.35, r=0.3); put(out, i * 0.04, x, 0.5)
    return out
def final_thump():
    x = thump() * 1.4; ch = sum(tone(m, 0.3, duty=0.5, d=0.25, s=0.0) for m in (57, 64, 69)) * 0.35
    return x + np.pad(ch, (0, max(0, len(x) - len(ch))))[:len(x)]
def ding(step): return tone(88 + step, 0.18, duty=0.5, d=0.16, s=0.0)
def bloop(): x = sweep(560, 130, 0.18, duty=0.25, curve=0.6); return x * decay(len(x), 0.07)
def pop():
    up = sweep(300, 1900, 0.05, "sin"); n = noise(0.12) * decay(int(0.12 * SR), 0.02)
    return np.concatenate([up * 0.8, n * 1.2])
def beep(m, dur=0.16): return tone(m, dur, duty=0.5, d=0.1, s=0.4, r=0.03)
def keystroke():
    """Very short noise click."""
    n = np.diff(noise(0.012), prepend=0); return n * decay(len(n), 0.0025)
def static_burst(dur=0.9):
    """Filtered white noise, crackling, dying away."""
    n = noise(dur); x = n - lowpass(n, 0.08)
    crackle = (RNG.random(len(n)) > 0.985) * RNG.uniform(-1, 1, len(n)) * 2
    return (x * 0.9 + crackle) * decay(len(n), dur / 3)
def error_buzz(dur=0.55):
    """Low square-wave drone, two detuned squares."""
    x = sweep(hz(40), hz(40), dur, "sq", 0.5) * 0.6 + sweep(hz(40) * 1.01, hz(40) * 1.01, dur, "sq", 0.3) * 0.5
    return x * adsr(len(x), a=0.005, d=0.05, s=0.9, r=0.06)
def skitter(dur=0.5, seed=0):
    """Tiny random high clicks: little legs."""
    r = np.random.default_rng(seed); out = np.zeros(int(dur * SR))
    for _ in range(int(dur * 38)):
        c = sweep(r.uniform(2500, 5200), r.uniform(2000, 4500), 0.006, "sq", 0.5) * decay(int(0.006 * SR), 0.0015)
        put(out, r.uniform(0, dur - 0.01), c, r.uniform(0.4, 1))
    return out
def test_zap():
    """Rising sine blip."""
    x = sweep(600, 1900, 0.12, "sin", curve=0.6); return x * adsr(len(x), a=0.002, d=0.1, s=0.2, r=0.02)
def crash_fx(dur=1.2):
    """Noise burst falling in pitch (a resampled-down sweep of filtered noise) with a low drop."""
    n = noise(dur); k = np.linspace(0.6, 0.02, len(n)) ** 1.5
    y = np.empty_like(n); acc = 0.0
    for i, v in enumerate(n): acc += k[i] * (v - acc); y[i] = acc
    return y * decay(len(n), dur / 3) * 2.2 + sweep(400, 40, dur, "sq", 0.5, curve=0.5) * decay(len(n), dur / 4) * 0.35
def stamp(): return thump() * 1.1 + np.pad(snare(), (0, int(0.3 * SR) - len(snare()))) * 0.5
def boot_flashy():
    """Over-the-top boot jingle: fast rising arpeggio."""
    out = np.zeros(int(0.5 * SR))
    for i, m in enumerate([69, 72, 76, 81, 84, 88, 93, 96]): put(out, i * 0.05, tone(m, 0.07, duty=0.125, s=0.5), 0.5)
    return out
def boot_clean():
    out = np.zeros(int(0.6 * SR))
    for i, m in enumerate([72, 76, 79, 84]): put(out, i * 0.08, tone(m, 0.4 - i * 0.05, duty=0.5, d=0.3, s=0.2), 0.45)
    return out
def chord():
    out = np.zeros(int(1.0 * SR))
    for m in (72, 76, 79, 84): put(out, 0, tone(m, 1.0, duty=0.25, d=0.6, s=0.3, r=0.2), 0.32)
    return out
def crack():
    out = np.zeros(int(0.15 * SR))
    for k in (0, 0.05, 0.09): put(out, k, np.diff(noise(0.01), prepend=0) * decay(int(0.01 * SR), 0.002), 1.0)
    return out
def smirk_sting():
    """Sly two-note square 'heh'."""
    return np.concatenate([tone(74, 0.08, duty=0.25, s=0.6), tone(70, 0.22, duty=0.25, d=0.18, s=0.1)])
def sub_hit():
    """Low bass hit: sine dropping 90 -> 34 Hz with a long tail."""
    x = sweep(90, 34, 0.9, "sin", curve=0.4); return x * decay(len(x), 0.35)
def drone(dur):
    """Bar 1 bed: A1 triangle + a detuned square an octave up, tremolo speeding up, swelling into bar 2."""
    x = tt(dur); trem = 0.7 + 0.3 * np.sin(2 * np.pi * (3 + 5 * x / dur) * x)
    y = sweep(hz(33), hz(33), dur, "tri") * 0.8 + sweep(hz(45) * 1.006, hz(45) * 1.006, dur, "sq", 0.3) * 0.18
    env = np.minimum(1, x / 0.03) * (0.55 + 0.45 * x / dur); env[-int(0.04 * SR):] *= np.linspace(1, 0, int(0.04 * SR))
    return y * trem * env
def crunch(): n = noise(0.08); return n * (RNG.random(len(n)) > 0.5) * decay(len(n), 0.02)

def events():
    """Every sound event: (beat, label, sound, gain). The animation code uses the same beat numbers."""
    ev = [(0, "static burst: Level 2's frame breaks up", static_burst(0.9), 0.8),
          (0, "low bass hit", sub_hit(), 0.9), (0, "bar 1 drone (to the bar 2 downbeat)", drone(B(4) - B(0)), 0.45),
          (2, "bass hit under the smirk", sub_hit(), 0.6),
          (1, "GLITCH tears through: static", static_burst(0.4), 0.45),
          (2, "smirk sting", smirk_sting(), 0.45), (3.5, "wipe", whoosh(), 0.5),
          (7.5, "wipe", whoosh(), 0.5), (8, "both robots land", thump(), 0.8), (8.5, "knuckle crack", crack(), 0.6)]
    ev += [(b, f"count {s}", beep(84 if s == "GO" else 72, 0.3 if s == "GO" else 0.16), 0.4) for b, s in COUNT]
    ev += [(11.5, "game windows pop up", bloop(), 0.3)]
    ev += [(12 + i / 2, "keystroke tick (8th)", keystroke(), 0.9) for i in range(8)]
    ev += [(12.25 + i / 2, "keystroke tick (16th, GLITCH's blur)", keystroke(), 0.45) for i in range(8)]
    ev += [(b, f"GLITCH block {i + 1} (+10%)", tone(91, 0.04, duty=0.125, s=0.3), 0.18) for i, b in enumerate(GL_BLOCKS)]
    ev += [(b, f"Bit places block {i + 1}", tone(79, 0.05, duty=0.5, s=0.3), 0.15) for i, b in enumerate(BIT_PLACE[:9])]
    ev += [(b, f"TEST ✓ zap, block {i + 1} (+10%)", test_zap(), 0.45) for i, b in enumerate(BIT_TEST[:9])]
    ev += [(15.5, "GLITCH winds up", jump(), 0.3), (SHIP, "SHIP IT! stamp", stamp(), 0.9), (SHIP, "confetti", pop(), 0.5),
           (BOOT_G, "GLITCH's game boots (flashy)", boot_flashy(), 0.5), (ERROR, "error buzz", error_buzz(), 0.7)]
    ev += [(BUG_OUT + k, "bug skitter", skitter(0.5, seed=k), 0.35) for k in range(3)]
    ev += [(23.5, "bugs charge across", skitter(0.5, seed=9), 0.35)]
    for j, b in enumerate(ZAPS):
        ev += [(b, f"zap BUG ×{j + 1}", test_zap(), 0.5), (b, "bug pops into ✓", pop(), 0.5), (b, f"combo ding ×{j + 1}", ding(j * 2), 0.3)]
    ev += [(BOOT_B, "Bit's last block tested: chord", chord(), 0.6), (BOOT_B, "clean boot", boot_clean(), 0.4),
           (BOOT_B, "Bit hops", jump(), 0.3)]
    ev += [(b, "bugs chew GLITCH's block", crunch(), 0.35) for b in EAT]
    ev += [(b, "mini-game hero grabs a star (+500)", coin(), 0.4) for b, _ in COLLECT]
    ev += [(b - 0.5, "mini-game hero jumps", jump(), 0.18) for b, _ in COLLECT]
    ev += [(CRASH, "crash", crash_fx(), 0.85), (WIN_, "win sting", victory(), 0.55), (WIN_, "Bit hops", jump(), 0.3),
           (END, "end card: hop", jump(), 0.3), (39, "final thump", final_thump(), 0.9)]
    return ev

def mixdown():
    m = music()
    s = np.zeros(NS + 2 * SR, np.float32)
    for b, _, x, g in events(): put(s, B(b), x, g)
    out = m + s[:NS]
    out[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
    return (out / np.abs(out).max() * 10 ** (-6.5 / 20)).astype(np.float32)

# ---------------------------------------------------------------- beat measurement (Levels 1-2's)
def measure_beats(x):
    """Tempo and phase measured from the music track itself (onset flux + autocorrelation + least squares)."""
    hop = 128; fr = SR / hop; n = len(x) // hop
    e = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1))
    flux = np.maximum(np.diff(np.log1p(200 * e), prepend=0), 0)
    ac = np.correlate(flux, flux, "full")[n - 1:]
    lags = np.arange(n) / fr; m = (lags > 0.3) & (lags < 1.0)
    i = np.argmax(np.where(m, ac, -1))
    a, b_, c = ac[i - 1], ac[i], ac[i + 1]
    period = (i + 0.5 * (a - c) / (a - 2 * b_ + c)) / fr     # parabolic peak refinement
    pk = [j for j in range(1, n - 1) if flux[j] > 0.25 * flux.max() and flux[j] >= flux[j - 1] and flux[j] > flux[j + 1]]
    onsets = np.array(pk) / fr
    first = onsets[0]                                        # music starts on bar 2's downbeat = beat 4
    k = 4 + (onsets - first) / period
    on_beat = np.abs(k - np.round(k)) < 0.12                 # drop 8th/16th notes and off-beats
    A_ = np.vstack([np.ones(on_beat.sum()), np.round(k[on_beat])]).T
    (t0, p), *_ = np.linalg.lstsq(A_, onsets[on_beat], rcond=None)
    beats = [max(0.0, round(t0 + j * p, 4)) for j in range(40)]
    return {"bpm": round(60 / p, 3), "beats": beats, "downbeats": beats[::4],
            "measured_onsets": int(on_beat.sum()), "period_autocorr": round(period, 4)}

def write_beats():
    OUT.mkdir(exist_ok=True)
    info = measure_beats(music())
    BEATS[:] = info["beats"] + [info["beats"][-1] + 60 / info["bpm"]]
    info["hits"] = sorted({round(B(b), 4) for b, *_ in events()})
    (OUT / "beats.json").write_text(json.dumps(info, indent=1))
    print(f"beats.json: {info['bpm']} BPM from {info['measured_onsets']} on-beat onsets, beat 0 at {info['beats'][0]} s")
    return info

# ---------------------------------------------------------------- beat grid (Gate 2)
SHOTS = [
    (1, "Hard open: Level 2's SCOPE LOCKED ✓ (cropped: just those words on their plate, Level 2's arena and happy Bit behind) "
        "breaks into static; GLITCH's face tears through band by band and smirks straight at camera",
     [(0, "frame 0: static burst + RGB split over SCOPE LOCKED ✓"), (1, "GLITCH's face tears through in shifted bands (typing eyes)"),
      (1.75, "face complete; a tall band through his visor shoved 5-6 px every frame"), (2, "SMIRK (left eye narrows) + sting"),
      (3.5, "pixel wipe starts; ends on the bar 2 downbeat")]),
    (2, "Title card over the empty split arena: LEVEL / 3 / BUILD / RACE, one word per beat; mini Bit and mini GLITCH on their floors",
     [(4, "music starts; LEVEL + snare"), (5, "3 + snare"), (6, "BUILD + snare"), (7, "RACE + snare"),
      (7.5, "pixel wipe out to the split arena; both robots drop in")]),
    (3, "PROMPT: MAKE A GAME card drops between them; HUD slides down (bars at 0, SCORE carries on from Level 2); knuckle crack; 3, 2, 1, GO",
     [(8, "both land (thump); prompt card drops; HUD in; 3"), (8.5, "both crack knuckles: sparks + crack"), (9, "2"), (10, "1"),
      (11, "GO"), (11.25, "prompt card flies up"), (11.5, "both game windows pop up; typing starts")]),
    (4, "The race. GLITCH types in a blur (scrolling code eyes, arms every frame, speed lines): a crooked block on every 8th, bar to 70%. "
        "Bit types calmly, places a block, then zaps it TEST ✓ (beam round his head into the block): 30%",
     [(12, "keystroke ticks start on every 8th"), (12.5, "GLITCH block 1; Bit places block 1"), (13, "TEST ✓ block 1: Bit 10%"),
      (14, "TEST ✓: 20%"), (15, "TEST ✓: 30%"), (15.5, "GLITCH block 7 = 70%; he raises his arm")]),
    (5, "GLITCH slams SHIP IT! on his window with 3 slots still empty; his bar jumps to 100%, confetti on his side. Bit keeps testing to 60%",
     [(16, "SHIP IT! stamp on the downbeat; GLITCH bar 70 -> 100% (flashes); confetti"), (17, "TEST ✓: 40%"), (18, "TEST ✓: 50%"),
      (19, "TEST ✓: 60%; GLITCH's game boots: one beat of flashy rainbow")]),
    (6, "ERROR. His visor goes shocked; his 3 never-built bar segments turn red; bugs pour out of the window onto his floor",
     [(20, "ERROR (red, blinking) + error buzz + shake; shocked eyes"), (21, "bugs start pouring out (one every 32nd) + skitters; Bit TEST ✓: 70%"),
      (22, "Bit 80%"), (23, "Bit 90%"), (23.5, "four bugs break off and charge across the divider")]),
    (7, "Bugs swarm across the divider towards Bit. He zaps one per beat; each pops into a green ✓. Combo BUG ×1 ×2 ×3 ×4",
     [(24, "zap: BUG ×1"), (25, "zap: BUG ×2"), (26, "zap: BUG ×3"), (27, "zap: BUG ×4"), (27.5, "Bit places his last block")]),
    (8, "Bit's bar hits 100%. His window boots clean: a pink dot hopping across platforms collecting stars. TESTED ✓. "
        "Bugs climb GLITCH's window and chew his blocks; his bar goes red segment by segment",
     [(28, "last block tested -> 100%; chord; white boot flash; mini-game runs; TESTED ✓; Bit hops, happy ^ ^"),
      (28.5, "bugs chew block 1 (then one every half beat to 31.5)")]),
    (9, "GLITCH crashes: visor full of static, window full of static, heavy slice shifts. CRASHED, then BIT WINS in pink",
     [(32, "CRASHED + crash sound + big shake; GLITCH bar all red"), (34, "BIT WINS on a plate + win sting; Bit hops; confetti; +10000"),
      (35.5, "HUD slides out; plate grows into the end card")]),
    (10, "Bit happy and hopping, GLITCH sulking but already typing again. WHO SHOULD / BIT RACE / NEXT?, ↓ COMMENTS (blinking), @vibewithamitai",
     [(36, "WHO SHOULD"), (36.5, "BIT RACE"), (37, "NEXT?"), (38, "↓ COMMENTS"), (38.5, "@vibewithamitai; COMMENTS starts blinking"),
      (39, "final thump + soft flash (beat 40)"), (40, "end of film, frame 600")]),
]
def beat_label(b):
    whole = int(b); frac = b - whole
    return f"{whole + 1}" + {0: "", 0.5: " &", 0.25: " e", 0.75: " a"}.get(round(frac, 2), f" +{frac:.2f}")

def write_grid():
    rows = ["# Bit: Level 3 — beat grid", "",
            f"Measured from the music track: **{json.loads((OUT / 'beats.json').read_text())['bpm']} BPM**, beat 1 at {BEATS[0]:.4f} s. "
            "Frame = round(time × 30). Beats are numbered 1–40 as in the brief; `&` = the half beat, `e`/`a` = the 16ths. "
            "Every time below is read from `out/beats.json`.", ""]
    for bar, shot, evs in SHOTS:
        t0, t1 = B((bar - 1) * 4), B(bar * 4) if bar < 10 else N / FPS
        rows += [f"## Bar {bar} · {t0:.2f}–{t1:.2f} s · frames {round(t0 * FPS)}–{round(t1 * FPS) - 1}", "", shot, "",
                 "| Beat | Time (s) | Frame | Event |", "|---|---|---|---|"]
        for b, what in evs:
            tm = B(b) if b < 40 else N / FPS
            rows.append(f"| {beat_label(b) if b < 40 else 'end'} | {tm:.3f} | {round(tm * FPS)} | {what} |")
        rows.append("")
    rows += ["## Sound events", "", "| Beat | Time (s) | Frame | Sound |", "|---|---|---|---|"]
    for b, label, *_ in sorted(events(), key=lambda e: e[0]):
        rows.append(f"| {beat_label(b)} | {B(b):.3f} | {round(B(b) * FPS)} | {label} |")
    (OUT / "beat_grid.md").write_text("\n".join(rows) + "\n")
    print("beat_grid.md written")

def write_wav(path, x):
    import wave
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.repeat(pcm, 2).tobytes())

def aac_peak_db(path):
    import subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return 20 * math.log10(np.abs(np.frombuffer(raw, np.float32)).max())

def encode_audio(x, target=-6.0):
    """Encode to AAC, measure the decoded stereo peak, rescale, repeat until it sits in (target - 0.3, target] dBFS."""
    import subprocess
    wav, aac = OUT / "mix.wav", OUT / "mix.m4a"
    for _ in range(6):
        write_wav(wav, x)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-c:a", "aac", "-b:a", "192k", str(aac)], check=True)
        pk = aac_peak_db(aac)
        if target - 0.3 < pk <= target: break
        x = x * 10 ** ((target - 0.15 - pk) / 20)
    wav.unlink(); print(f"audio: AAC peak {pk:.2f} dBFS")
    return aac

def render():
    """Raw RGB frames piped to ffmpeg, muxed with the synthesised mix. Exactly 600 frames / 20.0 s."""
    import subprocess, time
    aac = encode_audio(mixdown())
    dst = OUT / "level3_9x16.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", str(aac), "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                           "-pix_fmt", "yuv420p", "-c:a", "copy", "-t", f"{N / FPS:.3f}", "-movflags", "+faststart",
                           str(dst)], stdin=subprocess.PIPE)
    bad, t0 = [], time.time()
    for f in range(N):
        ff.stdin.write(frame(f).tobytes()); bad += safe_zone_violations(f)
        if f % 100 == 99: print(f"  frame {f + 1}/{N}  {time.time() - t0:.0f}s", flush=True)
    ff.stdin.close(); ff.wait(); aac.unlink()
    print(f"{dst.name} written;", f"{len(bad)} readability violations" if bad else "on screen, safe zone and 48 px minimum OK on all 600 frames")
    for v in bad[:20]: print("  ", v)

# ---------------------------------------------------------------- commands
STYLE = {"01_glitch_smirk": 2.2, "02_race_midpoint": 15.25, "03_bug_swarm_zap": 26.06}
def style_frames():
    d = OUT / "style_frames"; d.mkdir(parents=True, exist_ok=True)
    for name, b in STYLE.items():
        f = round(B(b) * FPS); frame(f).save(d / f"{name}.png")
        print(f"{name}.png  frame {f}  t={f / FPS:.2f}s", safe_zone_violations(f) or "safe zone OK")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    setup()
    if cmd in ("beats", "grid", "frames", "all"): write_beats()
    if cmd in ("grid", "all"): write_grid()
    if cmd in ("frames", "all"): style_frames()
    if cmd in ("render", "all"): render()
    if cmd == "at":                                        # debug: python build.py at <dir> <beat> [<beat> ...]
        dst = Path(sys.argv[2]); dst.mkdir(parents=True, exist_ok=True)
        for b in sys.argv[3:]:
            f = round(B(float(b)) * FPS); frame(f).save(dst / f"b{float(b):05.2f}.png")
            print(b, f, safe_zone_violations(f) or "ok")
