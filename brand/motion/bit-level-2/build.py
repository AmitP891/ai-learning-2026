#!/usr/bin/env python3
"""Bit: Level 2 — Scope Creep. A 20 s retro arcade boss fight, drawn and scored in code.

    python build.py frames     # Gate 1: three style frames -> out/style_frames/
    python build.py grid       # Gate 2: out/beats.json + out/beat_grid.md
    python build.py render     # Gate 3: out/level2_9x16.mp4
    python build.py            # everything

Same engine as Level 1 (../bit-level-1/build.py): the game layer is drawn at 270x480 and
upscaled 4x nearest-neighbour; HUD and words are drawn at full resolution with an
un-antialiased pixel font, then composited. Bar 1 replays Level 1's own game layer.
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
LEVEL1 = HERE.parent / "bit-level-1" / "build.py"

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
PILL = (74, 72, 98)
BIT_PAL = np.array([PK, PK2, VIS, CY, GRY, OUTL], np.float32)
# Scope Creep (brief section 5): purple body, darker outline, pale-lilac highlights, yellow sticky notes
PUD = (78, 36, 112); PUS = (98, 44, 142); LIL = (214, 186, 240); YLD = (200, 150, 0); INK = (150, 105, 0)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def lerp(a, b, u): return a + (b - a) * u

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

# ---------------------------------------------------------------- Level 1 (bar 1 cameo + carried-over score)
_L1 = []
def level1():
    """Level 1's build.py as a module: its game layer is the bar 1 cameo, its score is where ours starts."""
    if not _L1:
        spec = importlib.util.spec_from_file_location("level1", LEVEL1)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        m.use_layout("9x16"); _L1.append(m)
    return _L1[0]
def l1_final_score():
    m = level1(); return m.score((m.N - 1) / m.FPS)      # the number on Level 1's last frame

# ---------------------------------------------------------------- pixel text
_FC = {}
def font(kind, size):
    k = (kind, size)
    if k not in _FC:
        _FC[k] = ImageFont.truetype(font_path("InterDisplay-Black.otf" if kind == "title" else "DejaVuSansMono-Bold.ttf"), size)
    return _FC[k]

_TC = {}
def ptext(s, size, fill, kind="mono", px=3, edge=OUTL, shadow=True):
    """Un-antialiased text rendered at size/px and blown up px times, with a pixel outline."""
    key = (s, size, fill, kind, px, edge, shadow)
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

def pixelise(im):
    arr = np.array(im)
    arr[..., 3] = dither_alpha(arr[..., 3] / 255.0)
    return Image.fromarray(arr)

# ---------------------------------------------------------------- Bit (unchanged from Level 1)
BIT_H = 156
EZ = BIT_H / 120
BK = BIT_H / 700
SVG = (BRAND / "bit/bit.svg").read_text()
def bit_svg(pose):
    s = re.sub(r'<g id="eyes">.*?</g>', "", SVG, flags=re.S)
    s = re.sub(r'<path id="mouth"[^>]*/>', "", s)          # visor shows eyes only in the game
    if pose == "idle":                                     # right arm down, mirroring the left
        s = s.replace('x2="478" y2="300"', 'x2="475" y2="500"').replace('cx="488" cy="280"', 'cx="482" cy="515"')
    return s

def _bit_base(pose):
    png = cairosvg.svg2png(bytestring=bit_svg(pose).encode(), output_width=round(600 * BK), output_height=BIT_H)
    a = np.array(Image.open(io.BytesIO(png)).convert("RGBA")).astype(np.float32)
    rgb = a[..., :3]
    idx = ((rgb[:, :, None, :] - BIT_PAL[None, None]) ** 2).sum(-1).argmin(-1)   # snap to Bit's palette
    out = np.zeros_like(a, dtype=np.uint8)
    out[..., :3] = BIT_PAL[idx]; out[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    return Image.fromarray(out)
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

# ---------------------------------------------------------------- the beat sheet, in beats (0-based; brief beat = index + 1)
BIT_X, END_BIT_X, JUMP = 76, 135, 60
GROWS = [14, 16, 18, 19.5]                   # each attack: +15 % (bar 4 gulp on beat 3, bar 5 x2, bar 6)
SHRINKS = [28.5, 29.5, 30.5]                 # a NEXT VERSION note flies back into him: -15 %
DEFLATE, POP = 31.5, 32                      # the 4th one: notes fly off, he shrinks to a dot and pops
FULL = 1.15 ** len(GROWS)
ATTACKS = ["AND ALSO…", "ONE MORE THING", "QUICK CHANGE", "SHOULD BE EASY"]
NOTE_PX, BIG_PX, STAMP_PX = 81, 96, 81      # text px: Level 1's words were 66; SHOULD BE EASY is the biggest
def note_sc(w): return (BIG_PX if w == "SHOULD BE EASY" else NOTE_PX) / 66
STAMP_SC = STAMP_PX / 66
# bars 3-6: throw beat, arrival beat, where it aims, whether it hits Bit (HP loss)
THROWS = {"AND ALSO…": (11, 12, "chest", 1), "ONE MORE THING": (16, 17, "low", 0),
          "QUICK CHANGE": (18, 19, "chest", 1), "SHOULD BE EASY": (19.5, 20, "head", 2)}
CLANG = {w: 28 + i for i, w in enumerate(ATTACKS)}    # bar 8: thrown half a beat before, shield on the beat, back into him half a beat after
SHIELD_R = 28
STAMP = "NEXT VERSION"

# ---------------------------------------------------------------- Scope Creep
C_W0, C_H0 = 124, 130                        # starting body size (game px): about Bit's height
C_X0, C_X1 = 212, 236                        # body centre x at start and at full size (he leans in as he grows)
_EV = sorted([(b, 1.15) for b in GROWS] + [(b, 1 / 1.15) for b in SHRINKS])

def creep_scale(t):
    """Size factor with a springy wobble on every change; collapses to a dot from DEFLATE to POP."""
    s, val = 1.0, 1.0
    for b, k in _EV:
        if t < B(b): break
        prev, s = s, s * k; u = since(t, b)
        val = s + (prev - s) * math.exp(-6 * u) * math.cos(22 * u)
    if t >= B(DEFLATE):
        u = clamp(since(t, DEFLATE) / (B(POP) - B(DEFLATE)))
        val = s * max(0.05, 1 - u ** 1.4) * (1 + 0.08 * math.sin(u * 30))
    return val

def creep_hop(t):
    """Bar 3 entrance: drops in during the wipe, lands on beat 9 (index 8), two smaller bounces. (lift, squash)"""
    if t < B(8):
        u = clamp(since(t, 7.5) / (B(8) - B(7.5))); return (GROUND + 40) * (1 - u * u), 1.0
    lift, sq = 0.0, 1.0
    for b0, b1, hgt in ((8, 9, 24), (9, 10, 10)):
        if B(b0) <= t < B(b1):
            u = since(t, b0) / (B(b1) - B(b0)); lift = 4 * hgt * u * (1 - u)
    for b in (8, 9, 10):
        u = since(t, b) / 0.16
        if 0 <= u < 1: sq *= 1 - (0.28 if b == 8 else 0.14) * math.sin(math.pi * u)
    return lift, sq

def creep_mood(t):
    if t >= B(28.5): return "shocked"
    if B(20.1) <= t < B(23.5): return "laughing"
    if any(-0.05 <= since(t, b) < 0.45 for b in GROWS + [11, 27.5, 28]): return "greedy"
    return "grin"

def creep_state(t):
    """(cx, bottom, w, h, mood) in game coords, or None when he is not on stage."""
    if t < B(7.5) or t >= B(POP): return None
    s = creep_scale(t)
    cx = lerp(C_X0, C_X1, clamp((s - 1) / (FULL - 1), -0.2, 1.2))
    br = math.sin(2 * math.pi * 1.1 * t)
    lift, sq = creep_hop(t)
    w = C_W0 * s * (1 + 0.035 * br) * (2 - sq); h = C_H0 * s * (1 - 0.035 * br) * sq
    mood = creep_mood(t)
    if mood == "laughing": cx += 1 if int(t * 16) % 2 else -1
    return cx, GROUND - lift, w, h, mood

def face_geom(st):
    cx, bot, w, h, mood = st
    cy = bot - h / 2
    fx, fy = cx - 0.2 * w, cy - 0.12 * h
    return fx, fy, fy + 0.15 * h                         # face centre x, eye line y, mouth y

def mouth(t):
    st = creep_state(t); fx, fy, my = face_geom(st); return fx, my

# sticky notes on his body: (nx, ny, degrees) in body-radius units, clear of the face. 6 to start, +1 per growth.
NOTE_SPOTS = [(0.35, -0.55, 9), (0.62, -0.05, -12), (0.20, 0.55, 6), (-0.45, 0.62, -8), (0.62, 0.50, 14),
              (-0.28, -0.74, -6), (0.78, -0.42, 10), (0.30, 0.16, -15), (-0.78, 0.42, 12), (0.06, -0.90, 4)]
NOTE_ON = {6 + i: b for i, b in enumerate(GROWS)}                      # appears at growth i
NOTE_OFF = {9: SHRINKS[0], 8: SHRINKS[1], 7: SHRINKS[2], **{i: DEFLATE for i in range(7)}}

def note_pos(i, st):
    cx, bot, w, h, mood = st
    nx, ny, ang = NOTE_SPOTS[i]
    return cx + nx * w / 2, bot - h / 2 + ny * h / 2, max(6, 0.15 * min(w, h)), ang

def draw_note(d, x, y, size, ang, k=1.0):
    """A tiny yellow sticky note, rotated, with a folded corner and two scribbled lines."""
    s = size * k / 2; a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    P = lambda u, v: (x + u * ca - v * sa, y + u * sa + v * ca)
    d.polygon([P(-s, -s), P(s, -s), P(s, s), P(-s, s)], fill=YL, outline=YLD)
    f = s * 0.55
    d.polygon([P(s - f, s), P(s, s - f), P(s - f, s - f)], fill=YLD)
    if s >= 5:
        d.line([P(-s * 0.6, -s * 0.35), P(s * 0.55, -s * 0.35)], fill=INK)
        d.line([P(-s * 0.6, s * 0.15), P(s * 0.15, s * 0.15)], fill=INK)

def creep_body(cx, bot, w, h, t):
    """Lumpy, wobbling blob at game res with dithered shading, a 2 px outline and lilac highlight pixels."""
    rx, ry = w / 2, h / 2; cy = bot - ry
    x0, y0 = int(cx - rx * 1.15) - 4, int(cy - ry * 1.15) - 4
    x1, y1 = int(cx + rx * 1.15) + 4, int(bot) + 2
    m = Image.new("L", (x1 - x0, y1 - y0)); d = ImageDraw.Draw(m)
    pts = []
    for i in range(64):
        a = 2 * math.pi * i / 64
        r = 1 + 0.045 * math.sin(3 * a + 4.2 * t) + 0.03 * math.sin(5 * a - 3.1 * t + 1) + 0.018 * math.sin(7 * a + 2 * t)
        pts.append((cx + rx * r * math.cos(a) - x0, min(cy + ry * r * math.sin(a), bot) - y0))
    d.polygon(pts, fill=255)
    body = np.array(m) > 0
    inner = np.array(m.filter(ImageFilter.MinFilter(5))) > 0
    yy, xx = np.mgrid[0:m.height, 0:m.width].astype(np.float32)
    nx, ny = (xx + x0 - cx) / rx, (yy + y0 - cy) / ry
    shade = 0.6 * ny + 0.25 * nx
    th = bayer(*body.shape)
    out = np.zeros((m.height, m.width, 4), np.uint8)
    out[...] = PU + (255,)
    out[shade > 0.30 + 0.35 * th] = PUS + (255,)
    hl = (((nx + 0.40) / 0.07) ** 2 + ((ny + 0.60) / 0.045) ** 2 < 1) & (th > 0.3)
    hl |= (((nx + 0.66) / 0.025) ** 2 + ((ny + 0.30) / 0.07) ** 2 < 1) & (th > 0.5)
    out[hl] = LIL + (255,)
    out[body & ~inner] = PUD + (255,)
    out[~body] = 0
    return Image.fromarray(out), x0, y0

def draw_face(d, st, t):
    cx, bot, w, h, mood = st
    fx, fy, my = face_geom(st)
    ew = max(5, round(0.07 * w)); eh = round(ew * 1.35)
    for ex in (fx - 0.12 * w, fx + 0.12 * w):
        if mood == "laughing":                                       # squeezed shut: ^ ^
            d.line((ex - ew / 2, fy + 2, ex, fy - eh / 3, ex + ew / 2, fy + 2), fill=WH, width=2)
            continue
        k = 1.35 if mood in ("greedy", "shocked") else 1.0
        ww, hh = ew * k, eh * k
        d.ellipse((ex - ww / 2, fy - hh / 2, ex + ww / 2, fy + hh / 2), fill=WH, outline=PUD)
        p = max(2, round(ww * (0.25 if mood == "shocked" else 0.45)))
        px_ = ex - ww * 0.12 if mood != "shocked" else ex                 # pupils look left, at Bit
        d.rectangle((px_ - p / 2, fy - p / 2 + 1, px_ + p / 2 - 1, fy + p / 2), fill=OUTL)
    mw = 0.42 * w; mh = 0.1 * h
    if mood == "grin":                                               # wide grin, teeth along the top
        d.chord((fx - mw / 2, my - mh, fx + mw / 2, my + mh), 0, 180, fill=OUTL)
        d.rectangle((fx - mw * 0.44, my, fx + mw * 0.44, my + max(1, mh * 0.22)), fill=WH)
        d.ellipse((fx - mw * 0.14, my + mh * 0.45, fx + mw * 0.14, my + mh * 0.95), fill=PK)
    elif mood in ("greedy", "laughing"):                             # mouth wide open
        o = 1.3 if mood == "greedy" else 0.7 + 0.6 * abs(math.sin(t * 14))
        d.ellipse((fx - mw / 2, my - mh * 0.5, fx + mw / 2, my + mh * o * 1.2), fill=OUTL)
        d.rectangle((fx - mw * 0.32, my - mh * 0.25, fx + mw * 0.32, my - mh * 0.25 + max(1, mh * 0.2)), fill=WH)
        d.ellipse((fx - mw * 0.18, my + mh * o * 0.5, fx + mw * 0.18, my + mh * o * 1.1), fill=PK)
    else:                                                            # shocked: small O
        r = 0.07 * w
        d.ellipse((fx - r, my - r * 0.6, fx + r, my + r * 1.2), fill=OUTL)

def draw_creep(g, t):
    st = creep_state(t)
    if not st: return
    cx, bot, w, h, mood = st
    d = ImageDraw.Draw(g)
    if bot >= GROUND - 2: d.ellipse((cx - w * 0.42, GROUND - 2, cx + w * 0.42, GROUND + 3), fill=OUTL)
    body, x0, y0 = creep_body(cx, bot, w, h, t)
    comp(g, body, x0, y0)
    for i in range(len(NOTE_SPOTS)):
        on, off = NOTE_ON.get(i), NOTE_OFF[i]
        if (on is not None and t < B(on)) or t >= B(off): continue
        k = 1.0
        if on is not None:                                           # pops on with an overshoot
            u = since(t, on) / 0.15; k = 1.0 if u >= 1 else ease(u) * (1 + 0.4 * math.sin(math.pi * u))
        x, y, size, ang = note_pos(i, st)
        draw_note(d, x, y, size, ang + 4 * math.sin(t * 3 + i), k)
    draw_face(d, st, t)

def flying_notes(d, t):
    """Notes knocked off his body: each NEXT VERSION hit knocks one off, the last hit knocks them all off."""
    for i, te in NOTE_OFF.items():
        dt = t - B(te)
        if not 0 <= dt < 1.4: continue
        st = creep_state(B(te) - 1e-3)
        x, y, size, ang = note_pos(i, st)
        r = np.random.default_rng(100 + i)
        vx = (x - st[0]) / (st[2] / 2) * r.uniform(60, 110) + r.uniform(-20, 20); vy = -r.uniform(70, 140)
        draw_note(d, x + vx * dt, y + vy * dt + 160 * dt * dt, size, ang + r.uniform(-1, 1) * 500 * dt)

# ---------------------------------------------------------------- the fight's notes
_PILL = {}
def pill(word, kind, sc=1.0):
    if (word, kind, sc) not in _PILL: _PILL[word, kind, sc] = _pill(word, kind, sc)
    return _PILL[word, kind, sc]

def _pill(word, kind, sc):
    """Game-res pill body; text goes on at full res. 'note' = yellow sticky note, 'fixed' = green NEXT VERSION."""
    tw = ptext(word, round(66 * sc), WH).width / PX
    w, h = round(tw + 10), round(24 * sc)
    g = Image.new("RGBA", (w + 4, h + 4), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    r = h // 2 + 1
    if kind == "fixed":
        d.rounded_rectangle((0, 0, w + 3, h + 3), radius=r + 1, fill=GR + (255,))
        d.rounded_rectangle((2, 2, w + 1, h + 1), radius=r - 1, fill=VIS + (255,))
        return g
    d.rounded_rectangle((0, 0, w + 3, h + 3), radius=r + 1, fill=OUTL + (255,))
    d.rounded_rectangle((2, 2, w + 1, h + 1), radius=r - 1, fill=YL + (255,))
    d.rounded_rectangle((2, h - 2, w + 1, h + 1), radius=3, fill=YLD + (255,))           # shadow lip
    f = max(4, h // 4)
    d.polygon([(w + 1 - f - r // 2, 2), (w + 1 - r // 2, 2 + f), (w + 1 - f - r // 2, 2 + f)], fill=YLD + (255,))  # folded corner
    return g

def text_limit(word, kind, sc=1.0):
    """Max game x for a pill's centre so its text stays clear of the Shorts button column."""
    return SAFE_RIGHT / PX - pill(word, kind, sc).width / 2 - 1
def text_min(word, kind, sc=1.0): return pill(word, kind, sc).width / 2 + 1

def spawn(w, t, kind="note"):
    sc = note_sc(w); mx, my = mouth(t)
    return min(mx, text_limit(w, kind, sc)), my

def aim(w, where):
    sc = note_sc(w)
    y = {"chest": GROUND - BIT_H * 0.42, "low": GROUND - 17, "head": GROUND - BIT_H * 0.6}[where]
    x = BIT_X + 24 if where == "low" else BIT_X + 18                         # low: right under his front foot
    return max(x, text_min(w, "note", sc)), y

SHIELD = (BIT_X + 74, GROUND - 28)    # in front of him, right of and below his </> panel (game x 59-93, y 329-350)
def clang_pt(w):
    sc = note_sc(w)
    x = min(SHIELD[0] + 6, text_limit(w, "note", sc))
    return max(x, text_min(w, "note", sc)), SHIELD[1] + (3 if w == "SHOULD BE EASY" else 0)

def stamp_pt():
    """Where NEXT VERSION appears: on the shield's right half, towards Scope Creep."""
    return min(SHIELD[0] + 12, text_limit(STAMP, "fixed", STAMP_SC)), SHIELD[1]

def return_pt(w):
    """Where a NEXT VERSION note hits him: his upper-left body, just before he shrinks."""
    hb = CLANG[w]; st = creep_state(B(hb + 0.5) - 1e-3)
    cx, bot, ww, hh, _ = st
    return min(cx - 0.25 * ww, text_limit(STAMP, "fixed", STAMP_SC)), SHIELD[1] - 4           # straight back, low, into his body

def word_state(w, t):
    """(x, y, kind, text, scale, t_event) in game coords; kind in {'note','fixed','burst','fburst'}; None when not on screen."""
    sc = note_sc(w)
    b0, b1, where, dmg = THROWS[w]
    if B(b0) <= t < B(24):
        sx, sy = spawn(w, B(b0)); tx, ty = aim(w, where)
        u = since(t, b0) / (B(b1) - B(b0))
        if u >= 1:
            if dmg: return (tx, ty, "burst", w, sc, B(b1)) if u < 2.5 else None
            x = tx - (u - 1) * GW                                                # a miss slides out from under him
            xm = text_min(w, "note", sc)                                       # ...and bursts at the edge, before its text would clip
            if x >= xm: return x, ty, "note", w, sc, 0
            te = B(b1) + (tx - xm) / GW * (B(b1 + 1) - B(b1))
            return (xm, ty, "burst", w, sc, te) if t < te + 1.2 else None
        return lerp(sx, tx, u), lerp(sy, ty, ease(u * 1.3)) - 22 * math.sin(math.pi * u), "note", w, sc, 0
    hb = CLANG[w]
    if B(hb - 0.5) <= t < B(hb + 0.5) + 1.0:
        if t < B(hb):                                                           # pops out of his mouth onto the shield
            sx, sy = spawn(w, B(hb - 0.5)); cx_, cy_ = clang_pt(w)
            sy = max(sy, cy_ - 4)                                               # peeled off his body low down, clear of Bit's visor and panel
            u = since(t, hb - 0.5) / (B(hb) - B(hb - 0.5))
            return lerp(sx, cx_, ease(u * 1.2)), lerp(sy, cy_, u * u) + 10 * math.sin(math.pi * u), "note", w, sc, 0
        rx, ry = return_pt(w)
        if t >= B(hb + 0.5): return rx, ry, "fburst", STAMP, STAMP_SC, B(hb + 0.5)
        if t < B(hb) + 2 / FPS: return (*clang_pt(w), "note", w, sc, 0)          # stamped: two frames on the shield
        cx_, cy_ = stamp_pt()
        u = since(t, hb) / (B(hb + 0.5) - B(hb))
        return lerp(cx_, rx, ease(u)), lerp(cy_, ry, u) + 8 * math.sin(math.pi * u), "fixed", STAMP, STAMP_SC, 0
    return None

# ---------------------------------------------------------------- Bit's choreography
def bit_state(t, f):
    """x, y offset (negative = up), squash, pose, expr."""
    if t < B(8): return None
    x, y, sq, pose, expr = BIT_X, 0.0, 1.0, "idle", "idle"
    def jump(t0, h, dur=0.5):
        u = (t - t0) / dur
        return -4 * h * u * (1 - u) if 0 <= u < 1 else 0.0
    def land(t0, dur=0.18):
        u = (t - t0) / dur
        return 1 - 0.28 * math.sin(math.pi * u) if 0 <= u < 1 else 1.0
    if t < B(10):                                          # walks in from the left, a step every half beat
        u = since(t, 8) / (B(10) - B(8))
        x = lerp(-50, BIT_X, u)
        y = -4 * abs(math.sin(math.pi * since(t, 8) / (B(8.5) - B(8))))
    jt = B(17) - 0.25; y += jump(jt, JUMP); sq *= land(jt + 0.5)   # jumps ONE MORE THING
    for b, kb, dur in ((12, 6, 0.25), (19, 6, 0.25), (20, 12, 0.35)):  # knockback on each hit
        if 0 <= since(t, b) < dur: x -= kb * (1 - since(t, b) / dur)
    if B(36) <= t:                                         # victory hop to centre stage
        y += jump(B(36), 70); sq *= land(B(36) + 0.5)
        x = lerp(BIT_X, END_BIT_X, ease(since(t, 36) / 0.5))
    if t >= B(24): expr = "determined"
    if t >= B(33): expr = "happy"
    for b, n in ((12, 6), (19, 6), (20, 9)):
        if B(b) <= t < B(b) + n / FPS: expr = "hit"
    if expr == "idle" and f % 90 in (40, 41, 42): expr = "blink"
    if y == 0 and sq == 1.0: y = round(2.5 * math.sin(t * 2 * math.pi * 0.6))   # idle bob, ±10 px
    return x, y, sq, pose, expr

def shield_k(t):
    """0..1 size of the shield, up for half a second around each clang."""
    for hb in CLANG.values():
        u = since(t, hb)
        if -0.25 <= u < 0.25: return ease((u + 0.25) / 0.07) * (1 - clamp((u - 0.17) / 0.08)), u
    return 0, None

def draw_shield(g, t):
    k, u = shield_k(t)
    if k <= 0: return
    sx, sy = SHIELD; r = SHIELD_R * k * (1.12 if u is not None and 0 <= u < 0.07 else 1.0)
    hexp = lambda rr: [(sx + rr * math.cos(math.pi / 3 * i + math.pi / 6), sy + rr * math.sin(math.pi / 3 * i + math.pi / 6)) for i in range(6)]
    lay = Image.new("RGBA", g.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.polygon(hexp(r), fill=(WH + (200,)) if 0 <= u < 0.07 else (CY + (70,)))
    d.polygon(hexp(r), outline=CY, width=3)
    d.polygon(hexp(r * 0.72), outline=WH, width=1)
    g.alpha_composite(lay)

# ---------------------------------------------------------------- HUD numbers
def score(t):
    ev = [(17, 500), (28, 1000), (29, 2000), (30, 3000), (31, 4000), (POP, 10000)]
    s = sum(a * ease(since(t, b) / 0.4) for b, a in ev if t >= B(b))
    return int(L1_SCORE + s + max(0, t - B(9)) * 37)

def bit_hp(t): return 10 - sum(d for w, (b0, b1, _, d) in THROWS.items() if t >= B(b1))
def hp_flash(t): return any(0 <= since(t, b1) < 0.5 for b0, b1, _, d in THROWS.values() if d) and int(t * 12) % 2 == 0

def boss_len(t):
    """Boss bar length, 0.4 .. 1.0 of the full width: it stretches every time he grows."""
    if t >= B(28): return 1.0
    n = math.log(max(creep_scale(t), 1e-3)) / math.log(1.15)
    return 0.4 + 0.15 * clamp(n, -0.3, 4.3)
def boss_hp(t):
    if t < B(12): return 0.0
    hp = 1.0
    for b in SHRINKS + [DEFLATE]: hp -= 0.2 * ease(since(t, b) / 0.15) if t >= B(b) else 0
    if t >= B(DEFLATE) + 0.15: hp -= 0.2 * clamp((t - B(DEFLATE) - 0.15) / (B(POP) - B(DEFLATE) - 0.15))
    return clamp(hp)
def combo(t):
    c = sum(1 for b in CLANG.values() if t >= B(b))
    return c if t < B(POP) else 0

# ---------------------------------------------------------------- game layer
def arena():
    g = Image.new("RGBA", (GW, GH), NAVY + (255,)); d = ImageDraw.Draw(g)
    for x in range(0, GW, 15): d.line((x, 0, x, GH), fill=GRID)
    for y in range(0, GH, 15): d.line((0, y, GW, y), fill=GRID)
    d.rectangle((0, GROUND, GW, GROUND + 14), fill=VIS)
    d.line((0, GROUND, GW, GROUND), fill=GRY, width=2)
    for x in range(0, GW, 15): d.line((x, GROUND + 3, x, GROUND + 14), fill=GRY)
    return g

def particles(seed, n, origin, t, t0, spread=90, life=1.2, cols=(YL, RD, WH)):
    r = np.random.default_rng(seed); out = []
    dt = t - t0
    if dt < 0 or dt > life: return out
    for i in range(n):
        a = r.uniform(0, 2 * math.pi); v = r.uniform(0.3, 1) * spread
        x = origin[0] + math.cos(a) * v * dt; y = origin[1] + math.sin(a) * v * dt + 60 * dt * dt
        if r.random() > 1 - dt / life: continue
        out.append((x, y, cols[i % len(cols)], 2 if i % 3 else 3))
    return out

def shake(t):
    ev = [(20, 4, 0.35), (POP, 4, 0.4), (12, 2, 0.2), (19, 2, 0.2), (8, 1, 0.12)]
    ev += [(b, 1, 0.1) for b in CLANG.values()] + [(b, 1, 0.12) for b in GROWS + SHRINKS]
    for b, amp, dur in ev:
        u = since(t, b)
        if 0 <= u < dur:
            k = int(t * FPS)
            return (amp if k % 2 else -amp) * round(1 - u / dur + 0.4), (amp if k % 3 else -amp) * round(1 - u / dur + 0.4)
    if B(20.5) <= t < B(23.5) and int(t * FPS) % 4 == 0: return 1, 0        # he laughs so hard the screen rattles
    return 0, 0

_POPAT = []
def pop_origin():
    if not _POPAT:
        cx, bot, w, h, _ = creep_state(B(POP) - 1e-3); _POPAT.append((cx, bot - h / 2))
    return _POPAT[0]

def game_layer(t, f):
    g = ARENA.copy(); d = ImageDraw.Draw(g)
    draw_creep(g, t); d = ImageDraw.Draw(g)
    flying_notes(d, t)
    if t >= B(POP):                                          # the pop: rings and confetti
        u = since(t, POP); cx, cy = pop_origin()
        if u < 0.45:
            r_ = 6 + 160 * u
            d.ellipse((cx - r_, cy - r_, cx + r_, cy + r_), outline=YL, width=4)
            d.ellipse((cx - r_ * .65, cy - r_ * .65, cx + r_ * .65, cy + r_ * .65), outline=PU, width=3)
        for px_, py_, c, sz in particles(5, 110, (cx, cy), t, B(POP), spread=150, life=1.5, cols=(YL, PU, LIL, WH)):
            d.rectangle((px_, py_, px_ + sz - 1, py_ + sz - 1), fill=c)
    bs = bit_state(t, f)
    if bs:
        x, y, sq, pose, expr = bs
        spr = bit_sprite(pose, expr)
        if sq != 1.0:
            spr = spr.resize((round(spr.width * (2 - sq)), round(spr.height * sq)), Image.NEAREST)
        bx, by = round(x - spr.width / 2), round(GROUND - spr.height + y)
        comp(g, spr, bx, by)
        if B(24) <= t < B(28):                               # charging sparks around Bit
            for i in range(6):
                a_ = t * 6 + i * math.pi / 3; rr = (44 - 22 * ((t - B(24)) % 0.5) / 0.5) * BIT_H / 156
                cx, cy = bx + spr.width / 2 + math.cos(a_) * rr, by + spr.height / 2 + math.sin(a_) * rr
                d.rectangle((cx - 1, cy - 1, cx + 1, cy + 1), fill=CY if i % 2 else WH)
    draw_shield(g, t); d = ImageDraw.Draw(g)
    pills = []
    for w in ATTACKS:
        s = word_state(w, t)
        if not s: continue
        x, y, kind, text, sc, te = s
        if kind in ("burst", "fburst"):
            cols = (YL, YLD, WH) if kind == "burst" else (GR, WH, LIL)
            for px_, py_, c, sz in particles(ATTACKS.index(w) * 31 + int(te * 10), 44, (x, y), t, te, spread=75, cols=cols):
                d.rectangle((px_, py_, px_ + sz - 1, py_ + sz - 1), fill=c)
            continue
        body = pill(text, kind, sc)
        comp(g, body, round(x - body.width / 2), round(y - body.height / 2))
        pills.append((x, y, text, kind, sc))
    return g, pills

def scanlines(im):
    a = np.array(im); a[3::4] = (a[3::4] * 0.82).astype(np.uint8); return Image.fromarray(a)

# ---------------------------------------------------------------- full-res overlays (Level 1 layout)
UI = dict(hud=dict(bottom=350, bit=(48, 28), hp=(48, 118), score=112, boss_label=(48, 190, "lt"), boss_bar=(48, 280, 1032, 326)),
          card=(540, 712), meter_y=368, combo=(680, 1250), TEXT_W=800,
          cleared=dict(plate=(24, 375, 1056, 700), lines=[("LEVEL 1", 0, YL, 470), ("CLEARED ✓", 1, GR, 615)], size=170, maxw=960),
          title=dict(box=(36, 380, 1044, 1240), lines=[(200, 560), (190, 800), (190, 1035)], maxw=800, mini_bit_x=300),
          defeated=dict(plate=(24, 375, 1056, 690, 950), lines=[("BOSS", 460), ("DEFEATED", 610)], size=170, maxw=960,
                        cx=540, lock=[("SCOPE", 765), ("LOCKED ✓", 878)]),
          end=dict(plate=(24, 150, 1056, 940), cx=540, handle_y=870,
                   lines=[("SUBSCRIBE", 36, 1.0, 255), ("TO UNLOCK", 36.5, 0.72, 395), ("LEVEL 3", 37, 1.0, 535)],
                   ask=[("PICK THE NEXT BOSS", 38, WH, 690), ("↓ COMMENTS", 38, CY, 775)]))
TEXT_W = UI["TEXT_W"]

def hud(im, t):
    if t < B(9): return
    L = UI["hud"]
    u = ease(since(t, 9) / 0.35)
    out = clamp(since(t, 35.5) / 0.3) if t >= B(35.5) else 0
    dy = round(-L["bottom"] * (1 - u) - (L["bottom"] + 20) * out)
    if L["bottom"] + dy <= 0: return
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, L["bottom"] + dy), fill=(8, 8, 14))
    d.line((0, L["bottom"] + dy, W, L["bottom"] + dy), fill=GRY, width=4)
    blit(im, ptext("BIT", 72, WH), L["bit"][0], L["bit"][1] + dy, "lt")
    hp = bit_hp(t); flash = hp_flash(t)
    for i in range(10):
        x0, y0 = L["hp"][0] + i * 58, L["hp"][1] + dy
        on = i < hp
        d.rectangle((x0 - 4, y0 - 4, x0 + 52, y0 + 44), fill=OUTL)
        d.rectangle((x0, y0, x0 + 48, y0 + 40), fill=CY if on else (RD if flash else (35, 38, 58)))
        if on: d.rectangle((x0, y0, x0 + 48, y0 + 8), fill=(170, 255, 255))
    blit(im, ptext("SCORE", 72, WH), W - 48, L["bit"][1] + dy, "rt")
    blit(im, ptext(f"{score(t):06d}", 72, YL), W - 48, L["score"] + dy, "rt")
    if t < B(12): return                                     # boss bar
    k = ease(since(t, 12) / 0.3)
    lx, ly, la = L["boss_label"]
    blit(im, ptext("SCOPE CREEP", 72, (215, 180, 255)), lx - round((1 - k) * 1000), ly + dy, la)
    x0, y0, xmax, y1 = L["boss_bar"]; y0 += dy; y1 += dy
    x1 = round(x0 + (xmax - x0) * boss_len(t) * k)
    if x1 <= x0 + 12: return
    grow = any(0 <= since(t, b) < 0.25 for b in GROWS) and int(t * 15) % 2 == 0
    d.rectangle((x0 - 6, y0 - 6, x1 + 6, y1 + 6), fill=YL if grow else OUTL); d.rectangle((x0, y0, x1, y1), fill=(35, 20, 55))
    hp = boss_hp(t); xf = x0 + (x1 - x0) * hp
    hurt = any(0 <= since(t, b) < 0.2 for b in SHRINKS + [DEFLATE])
    if hp > 0:
        d.rectangle((x0, y0, xf, y1), fill=RD if hurt else PU); d.rectangle((x0, y0, xf, y0 + 10), fill=(165, 110, 215))
    for sx in range(x0, x1, 48): d.line((sx, y0, sx, y1), fill=OUTL, width=4)

def pill_text(im, pills, off):
    for x, y, text, kind, sc in pills:
        spr = ptext(text, round(66 * sc), GR) if kind == "fixed" else ptext(text, round(66 * sc), OUTL, edge=None)
        blit(im, spr, x * PX + off[0], y * PX + off[1] + 2)

def slam(t, b, dur=0.12):
    """Scale for a word slamming in on beat b: big -> 1."""
    u = since(t, b) / dur
    return None if u < 0 else (1 + 0.6 * (1 - ease(u)) if u < 1 else 1.0)

def title_card(im, t, f):
    L = UI["title"]; d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = L["box"]
    d.rectangle((x0, y0, x1, y1), fill=(8, 8, 14), outline=PU, width=12); d.rectangle((x0 + 24, y0 + 24, x1 - 24, y1 - 24), outline=GRY, width=4)
    (s0, y_lv), (s1, y_sc), (s2, y_cr) = L["lines"]
    size = fit_size("LEVEL 2", s0, L["maxw"], kind="title", px=5)                # "LEVEL" then "2", one per beat, one line
    full = ptext("LEVEL 2", size, YL, kind="title", px=5)
    lv, two = ptext("LEVEL", size, YL, kind="title", px=5), ptext("2", size, YL, kind="title", px=5)
    left, right = W / 2 - full.width / 2, W / 2 + full.width / 2
    for spr, cx, b in ((lv, left + lv.width / 2, 4), (two, right - two.width / 2, 5)):
        sc = slam(t, b)
        if sc is not None: blit(im, spr, cx, y_lv, "mm", sc)
    for s, b, col, size_, y in (("SCOPE", 6, WH, s1, y_sc), ("CREEP", 7, PK, s2, y_cr)):
        sc = slam(t, b)
        if sc is not None: blit(im, fit(s, size_, col, L["maxw"], kind="title", px=5), W / 2, y, "mm", sc)
    spr = bit_sprite("idle", "blink" if f % 90 in (40, 41, 42) else "idle")   # a small pixel Bit on the floor
    spr = spr.resize((spr.width * 2, spr.height * 2), Image.NEAREST)
    blit(im, spr, L["mini_bit_x"], GROUND * PX + round(6 * math.sin(t * 2 * math.pi * 0.6)) * 2, "mb")

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

def card(im, lines, y, border, t, t0):
    """Panel that slides in from the left and stops centred, never wider than the safe band."""
    u = ease((t - t0) / 0.25)
    sprs = [fit(s, sz, c, TEXT_W - 96, kind=k) for s, sz, c, k in lines]
    h = sum(s.height for s in sprs) + 28 * (len(sprs) + 1)
    w = max(s.width for s in sprs) + 96
    x = round(-w + (UI["card"][0] + w / 2) * u)
    d = ImageDraw.Draw(im)
    d.rectangle((x - 8, y - 8, x + w + 8, y + h + 8), fill=OUTL)
    d.rectangle((x, y, x + w, y + h), fill=(20, 16, 34), outline=border, width=8)
    yy = y + 28
    for s in sprs:
        blit(im, s, x + w / 2, yy, "mt"); yy += s.height + 28

def plate(im, box, k=1.0):
    """Dark backing so debris never reads through the big words."""
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.rectangle(box, fill=(8, 8, 14, round(225 * k)))
    d.rectangle(box, outline=GRY + (round(255 * k),), width=4)
    im.alpha_composite(g)

def flash(im, t, b, dur=0.1, a=160):
    u = since(t, b)
    if 0 <= u < dur: im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, round(a * (1 - u / dur)))))

# ---------------------------------------------------------------- frame
def level(im, t, f):
    """The game layer, upscaled, with scanlines, shake and note text."""
    g, pills = game_layer(t, f)
    off = shake(t)
    comp(im, scanlines(g.resize((W, H), Image.NEAREST)), off[0] * PX, off[1] * PX)
    pill_text(im, pills, (off[0] * PX, off[1] * PX))

def cameo(im, t):
    """Bar 1: Level 1's own game layer from the explosion on, LEVEL 1 / CLEARED ✓ on top."""
    m = level1()
    t1 = m.B(32) + max(0.0, t - B(0)); f1 = round(t1 * m.FPS)
    g, _ = m.game_layer(t1, f1); off = m.shake(t1)
    comp(im, scanlines(g.resize((W, H), Image.NEAREST)), off[0] * PX, off[1] * PX)
    flash(im, t, 0, 2 / FPS, 120)                                           # 2 soft frames: the explosion stays readable
    C = UI["cleared"]
    if t >= B(0):
        plate(im, C["plate"], ease(since(t, 0) / 0.1))
        for s, b, col, y in C["lines"]:
            sc = slam(t, b, 0.15)
            if sc is not None and t >= B(3): sc = slam(t, 3, 0.15)              # coin: both lines pulse once
            if sc is not None: blit(im, fit(s, C["size"], col, C["maxw"], kind="title", px=5), W / 2, y, "mm", sc)

def frame(f):
    t = f / FPS
    TEXT_BOXES.clear()
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    if t < B(4):
        cameo(im, t)
        if t >= B(3.5): draw_wipe(im, t, B(3.5), B(4) - B(3.5))
        return im.convert("RGB")
    level(im, t, f)
    if t < B(7.5):                                               # bar 2: title card over the empty arena
        title_card(im, t, f)
        return im.convert("RGB")
    if t < B(8): draw_wipe(im, t, B(7.5), B(8) - B(7.5), reverse=True)
    hud(im, t)
    if B(12) <= t < B(16):                                       # boss name card: between the HUD and Bit's head
        card(im, [("BOSS:", 72, RD, "mono"), ("SCOPE CREEP", 96, WH, "title")], UI["card"][1], PU, t, B(12))
    if B(24) <= t < B(28):                                       # CHANGE CONTROL meter, under the HUD
        y0 = UI["meter_y"]; d = ImageDraw.Draw(im)
        d.rectangle((40, y0, W - 40, y0 + 150), fill=(10, 12, 24), outline=CY, width=6)
        blit(im, ptext("CHANGE CONTROL", 66, CY), W / 2, y0 + 14, "mt")
        fill_ = clamp(since(t, 24) / (B(28) - B(24)))
        nseg = (W - 144) // 59
        for i in range(nseg):
            x0 = 72 + i * 59
            lit = i < round(fill_ * nseg)
            d.rectangle((x0, y0 + 92, x0 + 50, y0 + 130), fill=(YL if fill_ > 0.97 and int(t * 12) % 2 else CY) if lit else (30, 34, 52))
    c = combo(t)
    if c >= 2:
        sc = slam(t, 27 + c, 0.15) or 1
        blit(im, ptext(f"×{c}", 220, YL, kind="title", px=5), *UI["combo"], "mm", sc)
    if t >= B(POP):                                              # BOSS DEFEATED / SCOPE LOCKED ✓
        flash(im, t, POP)
        D = UI["defeated"]
        if t < B(35.5):
            x0, y0, x1, y1a, y1b = D["plate"]
            plate(im, (x0, y0, x1, y1a if t < B(34) else y1b), ease(since(t, POP) / 0.1))
            sc = slam(t, POP, 0.15)
            for s, y in D["lines"]: blit(im, fit(s, D["size"], YL, D["maxw"], kind="title", px=5), D["cx"], y, "mm", sc)
            if t >= B(34):
                size = fit_size("LOCKED ✓", 160, TEXT_W, kind="title", px=5)        # two lines: bigger, still clear of the buttons
                for s, y in D["lock"]: blit(im, ptext(s, size, GR, kind="title", px=5), D["cx"], y, "mm", slam(t, 34, 0.15))
        else:                                                    # the plate becomes the end card's plate
            k = ease(since(t, 35.5) / (B(36) - B(35.5)))
            x0, y0, x1, _, y1 = D["plate"]; E = UI["end"]["plate"]
            plate(im, tuple(round(lerp(a, b, k)) for a, b in zip((x0, y0, x1, y1), E)))
    if t >= B(36): end_card(im, t)
    return im.convert("RGB")

def end_card(im, t):
    E = UI["end"]; big = end_size()
    alt = t >= B(37.5) and int(since(t, 37.5) / (B(38) - B(37.5))) % 2 == 1        # blinks every half beat from 37.5
    cols = {"SUBSCRIBE": YL if alt else PK, "TO UNLOCK": WH, "LEVEL 3": PK if alt else YL}
    for s, b, k, y in E["lines"]:
        sc = slam(t, b, 0.12)
        if sc and t >= B(39): sc = slam(t, 39, 0.15)                              # final thump: one more punch
        if sc: blit(im, ptext(s, round(big * k), cols[s], kind="title", px=4), E["cx"], y, "mm", sc)
    for s, b, col, y in E["ask"]:
        sc = slam(t, b, 0.12)
        if sc: blit(im, ptext(s, 72, col, kind="mono", px=3), E["cx"], y, "mm", sc)
    sc = slam(t, 38.5, 0.12)
    if sc: blit(im, ptext("@vibewithamitai", 72, CY, kind="mono", px=3), E["cx"], E["handle_y"], "mm", sc)
    flash(im, t, 39, 0.1, 45)

_END = []
def end_size():
    """One size for SUBSCRIBE and LEVEL 3: the largest that fits the text width."""
    if not _END:
        size = 220
        while max(ptext(s, round(size * k), WH, kind="title", px=4).width for s, _, k, _ in UI["end"]["lines"]) > TEXT_W: size -= 2
        _END.append(size)
    return _END[0]

def safe_zone_violations(f):
    """Text from the last frame() call that sits under the platform buttons or has capitals under 48 px."""
    bad = []
    for s, (x0, y0, x1, y1), cap in TEXT_BOXES:
        if _offscreen(x0, y0, x1, y1): bad.append((f, s, "off screen", tuple(round(v) for v in (x0, y0, x1, y1))))
        elif _unsafe(x0, y0, x1, y1): bad.append((f, s, "safe zone", tuple(round(v) for v in (x0, y0, x1, y1))))
        if cap < 48: bad.append((f, s, f"cap height {cap:.0f} px"))
    return bad

def setup():
    g = globals()
    g["BIT_BASE"] = {p: _bit_base(p) for p in ("idle", "fire")}
    g["ARENA"] = arena()
    g["L1_SCORE"] = l1_final_score()
    _POPAT.clear(); _END.clear()

# ---------------------------------------------------------------- sound (Level 1's engine and kit)
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

# --- drums (same kit as Level 1)
def kick(): x = sweep(160, 40, 0.16, "tri", curve=0.4); return x * decay(len(x), 0.05)
def snare(): n = noise(0.14); return (n * 0.8 + sweep(220, 160, 0.14, "tri") * 0.4) * decay(len(n), 0.04)
def hat(): n = np.diff(noise(0.035), prepend=0) * 0.5; return n * decay(len(n), 0.008)
def crash(): n = np.diff(noise(1.0), prepend=0) * 0.4; return n * decay(len(n), 0.3)

A, C, D, E, F, G = 57, 60, 62, 64, 65, 67                    # A3 = 57
def music():
    """Level 2 theme: 120 BPM, A minor, new 8-bar melody over bars 2-9. Bar 1 has no music (Level 1's explosion)."""
    buf = np.zeros(NS + SR, np.float32)
    bt = lambda bar, beat: ((bar - 1) * 4 + beat) * SPB      # composer's grid: bar 1-10, beat 0-3.75
    roots = {2: [A], 3: [C], 4: [G], 5: [F], 6: [D, E], 7: [E], 8: [A, G], 9: [F]}
    for bar, rs in roots.items():                            # triangle bass, octave-bouncing 8ths
        for i in range(8):
            if bar == 9 and i >= 2: break                    # bass drops out after the pop
            r = rs[min(i // (8 // len(rs)), len(rs) - 1)] - 12
            put(buf, bt(bar, i / 2), tone(r + (12 if i % 2 else 0), SPB / 2 * 0.9, "tri", s=0.8), 0.32)
    for b in range(4):                                       # bar 2: snare on every title word
        put(buf, bt(2, b), snare(), 0.5); put(buf, bt(2, b), kick(), 0.6)
    for bar in (3, 4, 5, 6, 8):
        for b in range(4):
            if b in (0, 2) or bar == 8: put(buf, bt(bar, b), kick(), 0.7)
            if b in (1, 3): put(buf, bt(bar, b), snare(), 0.45)
            put(buf, bt(bar, b + 0.5), hat(), 0.35); put(buf, bt(bar, b), hat(), 0.25)
        if bar in (4, 6): put(buf, bt(bar, 2.5), kick(), 0.5)
    for b in range(4): put(buf, bt(7, b), kick(), 0.7)       # bar 7: four on the floor + snare roll
    for i in range(8): put(buf, bt(7, 2 + i / 4), snare(), 0.15 + 0.05 * i)
    put(buf, bt(5, 0), crash(), 0.5); put(buf, bt(8, 0), crash(), 0.6)
    arp = {3: [C, E, G, E + 12], 4: [G - 12, D, G, 59]}  # quiet 16th arps under the entrance
    for bar, ns in arp.items():
        for i in range(16): put(buf, bt(bar, i / 4), tone(ns[i % 4] + 12, SPB / 4 * 0.8, duty=0.125, s=0.3), 0.07)
    lead = {                                                 # square lead, 25% duty, 8th notes (None = rest)
        2: [69, None, 69, 72, None, 76, 74, None],           # Am  - the hook, under the title slams
        3: [72, 76, 79, 76, 74, 72, 71, 72],                 # C   - he bounces in
        4: [71, 74, 79, 74, 76, 74, 71, 67],                 # G   - "and also…"
        5: [69, 72, 77, 76, 74, 72, 69, None],               # F   - one more thing
        6: [74, 77, 81, 77, 76, 80, 83, 80],                 # Dm E - should be easy (G# leading note)
        8: [81, 76, 81, 84, 83, 79, 83, 86],                 # Am G - NEXT VERSION x4
        9: [84, 81, 77, None, None, None, None, None]}       # F   - the pop, then the chord SFX
    for bar, ns in lead.items():
        for i, m in enumerate(ns):
            if m: put(buf, bt(bar, i / 2), tone(m, SPB / 2 * 0.85, duty=0.25, s=0.6), 0.10 if bar == 2 else 0.13)
    rise = [64, 68, 71, 74, 68, 71, 74, 76, 71, 74, 76, 80, 74, 76, 80, 83]   # bar 7: rising arpeggio over E7
    for i, m in enumerate(rise):
        put(buf, bt(7, i / 4), tone(m + 12, SPB / 4 * 0.85, duty=0.25, s=0.6), 0.08 + 0.006 * i)
    for i, m in enumerate([73, 76, 81]):                     # bar 10: outro stabs, A major
        put(buf, bt(10, i), tone(m + 12, SPB * 0.7, duty=0.25, s=0.5), 0.14); put(buf, bt(10, i), kick(), 0.5)
    return buf[:NS]

# --- SFX: Level 1's set, plus gulp, shield clang and pop
def coin(): return np.concatenate([tone(83, 0.07, duty=0.5, s=1), tone(88, 0.3, duty=0.5, d=0.25, s=0.0)])
def thump(): x = sweep(120, 32, 0.3, "sin", curve=0.5); return x * decay(len(x), 0.09) + np.pad(snare()[:2000], (0, len(x) - 2000)) * 0.3
def jump(): x = sweep(300, 1000, 0.16, duty=0.25, curve=0.7); return x * adsr(len(x), d=0.1, s=0.3)
def whoosh():
    n = noise(0.24); e = np.sin(np.linspace(0, np.pi, len(n))) ** 2
    return (lowpass(n, 0.25) - lowpass(n, 0.03)) * e * 2
def throw(): x = sweep(700, 220, 0.2, duty=0.25); return (x * 0.6 + noise(0.2) * 0.3) * decay(int(0.2 * SR), 0.07)
def hit():
    n = int(0.3 * SR); return (noise(0.3) * 0.7 + sweep(160, 50, 0.3, duty=0.5) * 0.6) * decay(n, 0.07)
def laugh(notes=(62, 61, 60, 58, 57)):
    out = []
    for i, m in enumerate(notes):                            # "HA ha ha ha ha", falling, with wobble
        d = 0.09 if i else 0.12; x = tt(d)
        f = hz(m) * (1 + 0.03 * np.sin(2 * np.pi * 28 * x)); ph = np.cumsum(f) / SR % 1
        v = (2 * ph - 1) * np.sin(np.pi * x / d) ** 0.5 + noise(d) * 0.15
        out += [v * (1.0 - 0.12 * i), np.zeros(int(0.035 * SR))]
    return np.concatenate(out)
def charge(dur):
    x = sweep(180, 1400, dur, duty=0.25, curve=1.6); trem = 0.6 + 0.4 * np.sin(2 * np.pi * 16 * tt(dur))
    return x * trem * np.linspace(0.2, 1, len(x))
def ding(step): return tone(88 + step, 0.18, duty=0.5, d=0.16, s=0.0)
def burst(): n = noise(0.25); return n * (RNG.random(len(n)) > 0.6) * decay(len(n), 0.06)
def explosion():
    n = noise(1.6); return lowpass(n, 0.12) * decay(len(n), 0.35) * 2.2 + sweep(70, 30, 1.6, "sin") * decay(len(n), 0.4)
def victory():
    out = np.zeros(int(1.3 * SR))
    for i, m in enumerate([69, 73, 76, 81]):
        x = tone(m + 12, 1.3 - i * 0.04, duty=0.25, d=0.5, s=0.35, r=0.3); put(out, i * 0.04, x, 0.5)
    return out
def final_thump():
    x = thump() * 1.4; ch = sum(tone(m, 0.3, duty=0.5, d=0.25, s=0.0) for m in (57, 64, 69)) * 0.35
    return x + np.pad(ch, (0, max(0, len(x) - len(ch))))[:len(x)]
def boing(f0=180):
    x = sweep(f0, f0 * 2.6, 0.14, "tri", curve=0.6); return x * adsr(len(x), d=0.1, s=0.4)
def gulp():
    """Low sweep up with a swallowing wobble."""
    x = sweep(70, 280, 0.3, "tri", curve=1.6); am = 0.6 + 0.4 * np.sin(2 * np.pi * 18 * tt(0.3))
    return (x * 0.8 + sweep(70, 280, 0.3, "sq", duty=0.5, curve=1.6) * 0.25) * am * adsr(len(x), a=0.01, d=0.22, s=0.6, r=0.05)
def clang():
    """Short metallic square-wave hit: three inharmonic squares and a click."""
    n = int(0.22 * SR)
    x = sum(sweep(f, f * 0.985, 0.22, "sq", duty=0.3) for f in (1180, 1663, 2391)) / 3
    return x * decay(n, 0.05) + noise(0.22) * decay(n, 0.005) * 0.7
def bloop(): x = sweep(560, 130, 0.18, duty=0.25, curve=0.6); return x * decay(len(x), 0.07)
def deflate(dur):
    x = tt(dur); f = 900 * (80 / 900) ** (x / dur) * (1 + 0.06 * np.sin(2 * np.pi * 22 * x))
    ph = np.cumsum(f) / SR % 1; return np.where(ph < 0.25, 1.0, -1.0) * np.linspace(1, 0.4, len(x))
def pop():
    up = sweep(300, 1900, 0.05, "sin"); n = noise(0.12) * decay(int(0.12 * SR), 0.02)
    return np.concatenate([up * 0.8, n * 1.2])

def events():
    """Every sound event: (beat, label, sound, gain). The animation code uses the same beat numbers."""
    ev = [(0, "explosion (Level 1's last second)", explosion(), 0.9),
          (0, "LEVEL 1 slam", snare(), 0.5), (1, "CLEARED ✓ slam", snare(), 0.5), (1, "CLEARED ✓ kick", kick(), 0.6),
          (3, "coin", coin(), 0.5),
          (8, "landing thump (Scope Creep lands)", thump(), 0.9), (9, "bounce", boing(), 0.3), (10, "bounce", boing(220), 0.2)]
    for w, (b0, b1, where, dmg) in THROWS.items():
        ev += [(b0, f"throw {w}", throw(), 0.5)]
        ev += [(b1, f"hit {w} (HP -{dmg})", hit(), 0.8 if dmg < 2 else 1.0), (b1, f"{w} bursts on Bit", burst(), 0.4)] if dmg \
            else [(b1, f"{w} misses", whoosh(), 0.6)]
    ev += [(16.5, "jump", jump(), 0.4)]
    ev += [(b, f"gulp {i + 1} (+15%)", gulp(), 0.75) for i, b in enumerate(GROWS)]
    ev += [(20.5, "Scope Creep laughs", laugh((69, 68, 67, 65, 64, 62)), 0.45), (24, "change control charge", charge(B(28) - B(24)), 0.25)]
    for i, (w, hb) in enumerate(CLANG.items()):
        ev += [(hb - 0.5, f"throw {w}", throw(), 0.35), (hb, f"shield clang {w} -> NEXT VERSION", clang(), 0.55)]
        ev += [(hb, f"combo ding ×{i + 1}", ding(i * 2), 0.3)] if i else []
    ev += [(b, "NEXT VERSION hits him, shrink", bloop(), 0.5) for b in SHRINKS]
    ev += [(DEFLATE, "last NEXT VERSION hits, notes fly off, deflate", deflate(B(POP) - B(DEFLATE)), 0.4),
           (DEFLATE, "last NEXT VERSION hit", bloop(), 0.5),
           (POP, "pop", pop(), 0.9), (POP, "pop boom", explosion()[: int(0.8 * SR)], 0.45), (34, "victory chord", victory(), 0.5),
           (36, "victory hop", jump(), 0.3), (39, "final thump", final_thump(), 0.9)]
    return ev

def mix():
    m = music()
    s = np.zeros(NS + 2 * SR, np.float32)
    for b, _, x, g in events(): put(s, B(b), x, g)
    out = m + s[:NS]
    out[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
    return (out / np.abs(out).max() * 10 ** (-6.5 / 20)).astype(np.float32)  # -6 dBFS peak after AAC, with margin

# ---------------------------------------------------------------- beat measurement (Level 1's)
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
    on_beat = np.abs(k - np.round(k)) < 0.12                 # drop 8th-note hats and off-beats
    A_ = np.vstack([np.ones(on_beat.sum()), np.round(k[on_beat])]).T
    (t0, p), *_ = np.linalg.lstsq(A_, onsets[on_beat], rcond=None)
    beats = [max(0.0, round(t0 + j * p, 4)) for j in range(40)]
    return {"bpm": round(60 / p, 3), "beats": beats, "downbeats": beats[::4],
            "measured_onsets": int(on_beat.sum()), "period_autocorr": round(period, 4)}

def write_beats():
    OUT.mkdir(exist_ok=True)
    info = measure_beats(music())
    BEATS[:] = info["beats"] + [info["beats"][-1] + 60 / info["bpm"]]
    _POPAT.clear()
    info["hits"] = sorted({round(B(b), 4) for b, *_ in events()})
    (OUT / "beats.json").write_text(json.dumps(info, indent=1))
    print(f"beats.json: {info['bpm']} BPM from {info['measured_onsets']} on-beat onsets, beat 0 at {info['beats'][0]} s")
    return info

# ---------------------------------------------------------------- beat grid (Gate 2)
SHOTS = [
    (1, "Hard open on Level 1's last second: the Professor's fog bursts into pixels (Level 1's own game layer). "
        "LEVEL 1 / CLEARED ✓ slam in on a plate",
     [(0, "explosion + 2-frame flash, Professor shatters (Level 1 film time 16.0 s); LEVEL 1 slams in"),
      (1, "CLEARED ✓ slams in (green)"), (3, "coin; both lines pulse"), (3.5, "pixel wipe starts; ends on the bar 2 downbeat")]),
    (2, "Title card over the empty arena: LEVEL / 2 / SCOPE / CREEP slam in, one per beat; small Bit on the floor",
     [(4, "music starts; LEVEL + snare"), (5, "2 + snare"), (6, "SCOPE + snare"), (7, "CREEP + snare"),
      (7.5, "pixel wipe out to the arena; Scope Creep drops from the top")]),
    (3, "Bit walks in from the left (a step every half beat). A small sticky-note blob lands on the right and bounces. HUD slides in",
     [(8, "Scope Creep lands: thump, squash, small shake; Bit starts walking"), (9, "HUD slides down (SCORE carries on from Level 1); bounce"),
      (10, "last bounce; Bit reaches his mark"), (11, "throw AND ALSO… (greedy face)")]),
    (4, "BOSS: SCOPE CREEP card. AND ALSO… hits Bit (HP -1). Boss bar appears short; he gulps and grows +15%, the bar stretches",
     [(12, "AND ALSO… hits Bit: X X, shake, HP 10 -> 9; boss card + boss bar in"), (14, "gulp 1: +15%, a 7th sticky note pops on, bar stretches"),
      (16, "card out")]),
    (5, "ONE MORE THING and QUICK CHANGE, one per 2 beats. Bit jumps the first; the second hits. He grows twice",
     [(16, "throw ONE MORE THING; gulp 2"), (16.5, "Bit jumps"), (17, "ONE MORE THING passes under Bit and speeds off; +500"),
      (18, "throw QUICK CHANGE; gulp 3"), (19, "QUICK CHANGE hits Bit: HP 9 -> 8")]),
    (6, "SHOULD BE EASY, the biggest note: he is now full size (1.75×), the boss bar at full length. He laughs; screen rattles",
     [(19.5, "throw SHOULD BE EASY; gulp 4 (full size)"), (20, "SHOULD BE EASY hits Bit: big shake, X X, HP 8 -> 6"),
      (20.5, "Scope Creep laughs until beat 23.5")]),
    (7, "Bit's eyes go determined. CHANGE CONTROL meter (under the HUD) fills over 4 beats; charge sparks; rising arpeggio",
     [(24, "determined eyes; meter and charge start"), (27.5, "he throws AND ALSO… again"), (28, "meter full")]),
    (8, "He throws all four again, one per beat. Bit's cyan hexagon shield stamps each one NEXT VERSION and it flies back into him. "
        "He shrinks with each hit; combo ×2 ×3 ×4",
     [(28, "clang: AND ALSO… -> NEXT VERSION; +1000"), (28.5, "it hits him: -15%, a note flies off; throw ONE MORE THING"),
      (29, "clang -> NEXT VERSION; ×2"), (29.5, "hit: -15%; throw QUICK CHANGE"), (30, "clang -> NEXT VERSION; ×3"),
      (30.5, "hit: -15%; throw SHOULD BE EASY"), (31, "clang -> NEXT VERSION; ×4"),
      (31.5, "last hit: all sticky notes fly off, he deflates to a dot; boss bar drains to zero")]),
    (9, "Boss bar at zero. He pops. BOSS DEFEATED. SCOPE LOCKED ✓ in green",
     [(32, "pop, flash, big shake, confetti; BOSS DEFEATED; +10000"), (33, "Bit happy ^ ^"), (34, "victory chord; SCOPE LOCKED ✓"),
      (35.5, "texts clear; HUD slides out; plate grows into the end card")]),
    (10, "Bit hops to centre stage, happy. SUBSCRIBE / TO UNLOCK / LEVEL 3 (blinking), PICK THE NEXT BOSS / ↓ COMMENTS, @vibewithamitai",
     [(36, "victory hop; SUBSCRIBE"), (36.5, "TO UNLOCK"), (37, "LEVEL 3"), (37.5, "SUBSCRIBE / LEVEL 3 start blinking (colour swap every half beat)"),
      (38, "PICK THE NEXT BOSS / ↓ COMMENTS"), (38.5, "@vibewithamitai"), (39, "final thump + flash (beat 40)"), (40, "end of film, frame 600")]),
]
def beat_label(b):
    whole = int(b); frac = b - whole
    return f"{whole + 1}" + {0: "", 0.5: " &"}.get(round(frac, 2), f" +{frac:.2f}")

def write_grid():
    rows = ["# Bit: Level 2 — beat grid", "",
            f"Measured from the music track: **{json.loads((OUT / 'beats.json').read_text())['bpm']} BPM**, beat 1 at {BEATS[0]:.4f} s. "
            "Frame = round(time × 30). Beats are numbered 1–40 as in the brief; `&` = the half beat. "
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

# ---------------------------------------------------------------- commands
STYLE = {"01_title_card": 7.3, "02_scope_creep_full_size": 28.12, "03_subscribe_end_card": 38.8}
def style_frames():
    d = OUT / "style_frames"; d.mkdir(parents=True, exist_ok=True)
    for name, b in STYLE.items():
        f = round(B(b) * FPS); frame(f).save(d / f"{name}.png")
        print(f"{name}.png  frame {f}  t={f / FPS:.2f}s", safe_zone_violations(f) or "safe zone OK")

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
    aac = encode_audio(mix())
    dst = OUT / "level2_9x16.mp4"
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

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    setup()
    if cmd in ("beats", "grid", "frames", "all"): write_beats()
    if cmd in ("grid", "all"): write_grid()
    if cmd in ("frames", "all"): style_frames()
    if cmd in ("render", "all"): render()
