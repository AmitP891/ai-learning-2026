#!/usr/bin/env python3
"""Bit: Level 1 — a 20 s retro arcade boss fight, drawn and scored in code.

    python build.py frames     # Gate 1: three style frames -> out/style_frames/
    python build.py            # everything

Game layer is drawn at 270x480 and upscaled 4x nearest-neighbour; HUD and words
are drawn at full resolution with an un-antialiased pixel font, then composited.
"""
import io, json, math, os, re, sys
from pathlib import Path

os.environ.setdefault("DYLD_FALLBACK_LIBRARY_PATH", "/opt/homebrew/lib")  # cairo on macOS
import numpy as np, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).resolve().parent
BRAND = HERE.parents[1]
OUT = HERE / "out"

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
sys.path.insert(0, str(BRAND / "adventures"))
from prof import professor  # noqa: E402

W, H, PX = 1080, 1920, 4         # defaults; use_layout() switches canvas and positions per format
GW, GH = W // PX, H // PX
FPS, N = 30, 600
GROUND = 396                     # game-layer y of the floor

NAVY = (13, 13, 20); GRID = (24, 24, 38); PK = (240, 53, 158); PK2 = (184, 31, 117)
VIS = (23, 26, 43); CY = (0, 240, 255); GRY = (58, 63, 92); OUTL = (11, 12, 20)
PU = (120, 56, 170); YL = (255, 214, 0); GR = (57, 255, 136); RD = (255, 70, 90); WH = (255, 255, 255)
FOG = (185, 180, 212); PILL = (74, 72, 98)
BIT_PAL = np.array([PK, PK2, VIS, CY, GRY, OUTL], np.float32)

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

def fit(s, size, fill, maxw, **kw):
    """ptext, shrunk until it is at most maxw wide."""
    spr = ptext(s, size, fill, **kw)
    while spr.width > maxw:
        size = round(size * maxw / spr.width) - 1; spr = ptext(s, size, fill, **kw)
    return spr

# Shorts safe zone: platform buttons cover the bottom 350 px, and the right 140 px between y=700 and y=1600.
SAFE_BOTTOM, SAFE_RIGHT, SAFE_BAND = H - 350, W - 140, (700, 1600)
TEXT_BOXES = []                               # (text, box) for every text sprite in the current frame

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
    im.alpha_composite(spr, (round(x - spr.width * ax), round(y - spr.height * ay)))

# ---------------------------------------------------------------- dithering
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 + 1 / 32
def dither_alpha(a):
    """Float alpha 0..1 -> hard 0/255 with an ordered 4x4 dither (pixel-art transparency)."""
    h, w = a.shape
    th = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w]
    return np.where(a > th, 255, 0).astype(np.uint8)

def pixelise(im):
    arr = np.array(im)
    arr[..., 3] = dither_alpha(arr[..., 3] / 255.0)
    return Image.fromarray(arr)

# ---------------------------------------------------------------- Bit
BIT_H = 156                                                 # set per layout in use_layout()
EZ = BIT_H / 120                                            # eye scale
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
BIT_BASE, HAND = {}, (0, 0)                                 # built by use_layout(): sprites, raised right hand

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

# ---------------------------------------------------------------- Professor
PK_S = 0.24
_PC = {}
def prof_sprite(mood, t, mouth=0.0):
    k = int(t * 6) % 36
    key = (mood, round(mouth * 4), k, PK_S)
    if key not in _PC:
        p = professor(round(mouth * 4) / 4, k / 6, "shock" if mood in ("shocked", "defeated") else "smug", 1.0)
        p = p.resize((round(p.width * PK_S), round(p.height * PK_S)), Image.BOX)
        _PC[key] = pixelise(p)
    return _PC[key]
POINTER = (0, 0)                                            # pointer tip in sprite coords (use_layout)

def prof_pos(t):
    """Top-left of the Professor sprite, or None if he is off stage."""
    if t < B(2) - 0.5 / FPS: return None                    # on stage from the hard cut (beat 3's frame)
    rise = ease(since(t, 12) / 1.0) if t >= B(12) else 0.0
    bob = round(2 * math.sin(t * 2 * math.pi * 0.5))
    shake = (1 if int(t * 16) % 2 else -1) if prof_mood(t) == "laughing" else 0
    w = round(640 * PK_S)
    return PROF_X - w // 2 + shake, round(PROF_TOP + (1 - rise) * LURK + bob)

def prof_mood(t):
    if t >= B(32): return "defeated"
    if t >= B(28): return "shocked"
    if B(12) <= t < B(14) or B(20) <= t < B(21.5): return "laughing"
    return "smug"

# ---------------------------------------------------------------- the fight's words
WORDS = ["FAST", "USER-FRIENDLY", "TBD", "ADEQUATE"]
FIXED = {"FAST": "WITHIN 200 ms", "TBD": "10 MB/s"}
# bars 5-6: throw beat, beat it reaches Bit's column, target (x, y) there, and whether it hits Bit
THROWS = {}                                                 # use_layout(): word -> (throw beat, arrival beat, target, hits Bit)
# bar 8: thrown half a beat early, shot out of the air on its beat at INTERCEPT; fixed words park top left
HIT_BEAT = {"FAST": 28, "USER-FRIENDLY": 29, "TBD": 30, "ADEQUATE": 31}


def pointer_tip(t):
    p = prof_pos(t)
    return (p[0] + POINTER[0], p[1] + POINTER[1]) if p else (262, 200)

def spawn(w, t):
    sx, sy = pointer_tip(t)
    return min(sx, SAFE_RIGHT / PX - pill(w, "vague").width / 2), sy     # spawn clear of the button column

def word_state(w, t):
    """(x, y, kind, t_event) in game coords; kind in {'vague','fixed','burst'}; None when not on screen."""
    b0, b1, tgt, hits = THROWS[w]
    if B(b0) <= t < B(24):
        sx, sy = spawn(w, B(b0))
        u = since(t, b0) / (B(b1) - B(b0))
        if u >= 1:
            if hits: return (tgt[0], tgt[1], "burst", B(b1)) if u < 2.5 else None     # TBD bursts on Bit
            x = tgt[0] - (u - 1) * 2 * GW                                          # a miss speeds off screen
            return (x, tgt[1], "vague", 0) if x > -120 else None
        return lerp(sx, tgt[0], u), lerp(sy, tgt[1], ease(u * 1.4)), "vague", 0
    hb = HIT_BEAT[w]
    if B(hb - 0.5) <= t < B(32):
        sx, sy = spawn(w, B(hb - 0.5))
        u = since(t, hb - 0.5) / (B(hb) - B(hb - 0.5))
        if u < 1:                                                               # hops out of his pointer
            return lerp(sx, INTERCEPT[0], u), lerp(sy, INTERCEPT[1], u) - 30 * math.sin(math.pi * u), "vague", 0
        if w not in FIXED: return (*INTERCEPT, "burst", B(hb))
        k = ease(since(t, hb + 0.25) / 0.25) if t >= B(hb + 0.25) else 0             # flip, then float up and park
        return lerp(INTERCEPT[0], PARK[w][0], k), lerp(INTERCEPT[1], PARK[w][1], k), "fixed", B(hb)
    return None

# ---------------------------------------------------------------- Bit's choreography
def bit_state(t, f):
    """x, y offset (negative = up), squash, pose, expr, visible."""
    x, y, sq, pose, expr = BIT_X, 0.0, 1.0, "idle", "idle"
    if t < B(7.5): return None
    if t < B(8):                                          # drop in from the top
        u = since(t, 7.5) / (B(8) - B(7.5))
        y = -(GROUND + 20) * (1 - u * u)
    def jump(t0, h, dur=0.5):
        u = (t - t0) / dur
        return -4 * h * u * (1 - u) if 0 <= u < 1 else 0.0
    def land(t0, dur=0.18):
        u = (t - t0) / dur
        return 1 - 0.28 * math.sin(math.pi * u) if 0 <= u < 1 else 1.0
    sq = land(B(8))
    jt = B(17) - 0.25; y += jump(jt, JUMP); sq *= land(jt + 0.5)
    # dash right to dodge USER-FRIENDLY, dash back left before the charge
    x = lerp(x, DASH_X, ease((t - B(18.5)) / 0.18)) if t < B(23) else lerp(DASH_X, BIT_X, ease((t - B(23)) / 0.18))
    if B(20) <= t < B(20) + 0.25: x -= 8 * (1 - (t - B(20)) / 0.25)        # knockback
    if B(36) <= t:                                        # victory hop to centre stage
        y += jump(B(36), 70); sq *= land(B(36) + 0.5)
        x = lerp(BIT_X, END_BIT_X, ease(since(t, 36) / 0.5))
    if t >= B(24): expr = "determined"
    if B(28) <= t < B(32): pose = "fire"
    if t >= B(33): expr = "happy"
    if B(20) <= t < B(20) + 6 / FPS: expr = "hit"
    if expr == "idle" and f % 90 in (40, 41, 42): expr = "blink"
    if y == 0 and sq == 1.0: y = round(2.5 * math.sin(t * 2 * math.pi * 0.6))   # idle bob, ±10 px
    return x, y, sq, pose, expr

# ---------------------------------------------------------------- HUD numbers
def score(t):
    ev = [(17, 500), (19, 500), (22, 500), (28, 1000), (29, 2000), (30, 3000), (31, 4000), (32, 10000)]
    s = sum(a * ease(since(t, b) / 0.4) for b, a in ev if t >= B(b))
    return int(s + max(0, t - B(10)) * 37) if t >= B(10) else 0

def bit_hp(t): return 7 if t >= B(20) else 10
def boss_hp(t):
    if t < B(12): return 0.0
    if t < B(16): return ease(since(t, 12) / (B(16) - B(12)))
    hp = 1.0
    for b in (28, 29, 30): hp -= 0.2 * ease(since(t, b) / 0.15) if t >= B(b) else 0
    if t >= B(31): hp -= 0.2 * ease(since(t, 31) / 0.15) + 0.2 * clamp(since(t, 31.15) / (B(32) - B(31.15)))
    return clamp(hp)
def combo(t):
    c = sum(1 for b in (28, 29, 30, 31) if t >= B(b))
    return c if t < B(32) else 0

# ---------------------------------------------------------------- game layer
def arena():
    g = Image.new("RGBA", (GW, GH), NAVY + (255,)); d = ImageDraw.Draw(g)
    for x in range(0, GW, 15): d.line((x, 0, x, GH), fill=GRID)
    for y in range(0, GH, 15): d.line((0, y, GW, y), fill=GRID)
    d.rectangle((0, GROUND, GW, GROUND + 14), fill=VIS)
    d.line((0, GROUND, GW, GROUND), fill=GRY, width=2)
    for x in range(0, GW, 15): d.line((x, GROUND + 3, x, GROUND + 14), fill=GRY)
    return g

def fog_bank(t):
    """Low rolling fog the Professor rises from (bar 4 on); dithered blobs."""
    if t < B(2) - 0.5 / FPS or t >= B(32) + 0.6: return None
    k = (0.55 + 0.45 * ease((t - B(11.5)) / 1.2)) * (1 - clamp((t - B(32)) / 0.6))
    yy, xx = np.mgrid[0:120, 0:GW].astype(np.float32)
    a = np.zeros_like(xx)
    for i in range(7):
        cx = (GW + 60) * (1 - k) + GW * (0.15 + 0.126 * i) + 10 * math.sin(t * 1.3 + i)
        cy = 70 + 12 * math.sin(t * 0.9 + i * 2.1)
        a += np.exp(-((xx - cx) ** 2 / (2 * 30 ** 2) + (yy - cy) ** 2 / (2 * 22 ** 2)))
    a = np.clip(a * 0.5, 0, 0.55) * k * np.clip(yy / 60, 0, 1)
    arr = np.zeros((120, GW, 4), np.uint8); arr[..., :3] = FOG; arr[..., 3] = dither_alpha(a)
    return Image.fromarray(arr)

_PILL = {}
def pill(word, kind):
    if (word, kind) not in _PILL: _PILL[word, kind] = _pill(word, kind)
    return _PILL[word, kind]

def _pill(word, kind):
    """Game-res pill body; text goes on at full res."""
    tw = ptext(word, 66, WH).width / PX
    w, h = round(tw + 10), 24
    g = Image.new("RGBA", (w + 4, h + 4), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    if kind == "fixed":
        d.rounded_rectangle((0, 0, w + 3, h + 3), radius=13, fill=GR + (255,))
        d.rounded_rectangle((2, 2, w + 1, h + 1), radius=11, fill=VIS + (255,))
        return g
    d.rounded_rectangle((0, 0, w + 3, h + 3), radius=13, fill=(225, 222, 240, 120))   # fog glow
    d.rounded_rectangle((2, 2, w + 1, h + 1), radius=11, fill=PILL + (255,), outline=OUTL)
    return pixelise(g)

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

_SHATTER = {}
def prof_shatter(t):
    """The Professor and his fog breaking into pixels from beat 32."""
    if "src" not in _SHATTER:
        tt = B(32); spr = prof_sprite("defeated", tt); p = prof_pos(tt)
        a = np.array(spr); ys, xs = np.nonzero(a[..., 3])
        keep = (ys % 3 == 0) & (xs % 3 == 0)
        ys, xs = ys[keep], xs[keep]
        r = np.random.default_rng(7)
        cx, cy = spr.width / 2, spr.height * 0.45
        ang = np.arctan2(ys - cy, xs - cx) + r.normal(0, 0.4, len(xs))
        sp = r.uniform(15, 90, len(xs))
        _SHATTER["src"] = (xs + p[0], ys + p[1], a[ys, xs, :3], np.cos(ang) * sp, np.sin(ang) * sp - 40,
                           r.uniform(0, 0.5, len(xs)))
    x, y, c, vx, vy, delay = _SHATTER["src"]
    dt = np.clip(t - B(32) - delay, 0, None)
    px = x + vx * dt; py = y + vy * dt + 90 * dt * dt
    alive = (dt < 1.6) & (np.random.default_rng(int(t * 30)).random(len(x)) > dt / 1.6)
    return px[alive], py[alive], c[alive]

def shake(t):
    for b, amp, dur in ((20, 3, 0.27), (32, 4, 0.4), (28, 1, 0.1), (29, 1, 0.1), (30, 1, 0.1), (31, 1, 0.1), (8, 1, 0.12)):
        u = since(t, b)
        if 0 <= u < dur:
            k = int(t * FPS)
            return (amp if k % 2 else -amp) * round(1 - u / dur + 0.4), (amp if k % 3 else -amp) * round(1 - u / dur + 0.4)
    return 0, 0

def game_layer(t, f):
    g = ARENA.copy(); d = ImageDraw.Draw(g)
    fb = fog_bank(t)
    p = prof_pos(t)
    mood = prof_mood(t)
    if p and mood != "defeated":
        mouth = (0.5 + 0.5 * abs(math.sin(t * 14))) if mood == "laughing" else 0.0
        spr = prof_sprite(mood, t, mouth)
        if p[1] + spr.height > GROUND: spr = spr.crop((0, 0, spr.width, max(1, GROUND - p[1])))   # nothing below the floor
        g.alpha_composite(spr, p)
    if fb: g.alpha_composite(fb, (0, GROUND - 92))
    if mood == "defeated" and t < B(32) + 2.1:
        xs, ys, cs = prof_shatter(t)
        a = np.array(g)
        ok = (xs >= 0) & (xs < GW - 2) & (ys >= 0) & (ys < GH - 2)
        xi, yi = xs[ok].astype(int), ys[ok].astype(int)
        for dx in (0, 1, 2):
            for dy in (0, 1, 2):
                a[yi + dy, xi + dx, :3] = cs[ok]
        g = Image.fromarray(a); d = ImageDraw.Draw(g)
    bs = bit_state(t, f)
    if bs and bs[3] == "fire":                               # beam to the word being hit this beat
        x, y, sq, pose, expr = bs
        bx, by = round(x - BIT_BASE["fire"].width / 2), round(GROUND - BIT_H + y)
        hx, hy = bx + HAND[0], by + HAND[1]
        for w in WORDS:
            u = since(t, HIT_BEAT[w])
            if 0 <= u < 0.32:
                sx, sy = INTERCEPT; wid = 5 if u < 0.12 else 3
                d.line((hx, hy, sx, sy), fill=CY, width=wid); d.line((hx, hy, sx, sy), fill=WH, width=max(1, wid - 3))
                r_ = 10 - 20 * u
                d.rectangle((sx - r_, sy - r_, sx + r_, sy + r_), outline=WH, width=2)
        d.ellipse((hx - 4, hy - 4, hx + 4, hy + 4), fill=CY)  # muzzle glow
    pills = []
    for w in WORDS:
        s = word_state(w, t)
        if not s: continue
        x, y, kind, te = s
        if kind == "burst":
            for px_, py_, c, sz in particles(WORDS.index(w) * 31 + int(te * 10), 40, (x, y), t, te, spread=70, cols=(FOG, WH, CY)):
                d.rectangle((px_, py_, px_ + sz - 1, py_ + sz - 1), fill=c)
            continue
        text = FIXED.get(w, w) if kind == "fixed" else w
        if kind == "fixed" and t < te + 0.12: kind, text = "vague", w                  # flash, then flip
        body = pill(text, kind)
        g.alpha_composite(body, (round(x - body.width / 2), round(y - body.height / 2)))
        pills.append((x, y, text, kind))
    if bs:
        x, y, sq, pose, expr = bs
        spr = bit_sprite(pose, expr)
        if sq != 1.0:
            spr = spr.resize((round(spr.width * (2 - sq)), round(spr.height * sq)), Image.NEAREST)
        bx, by = round(x - spr.width / 2), round(GROUND - spr.height + y)
        g.alpha_composite(spr, (bx, by))
        if B(24) <= t < B(28):                               # charging sparks around Bit
            for i in range(6):
                a_ = t * 6 + i * math.pi / 3; rr = (44 - 22 * ((t - B(24)) % 0.5) / 0.5) * BIT_H / 156
                cx, cy = bx + spr.width / 2 + math.cos(a_) * rr, by + spr.height / 2 + math.sin(a_) * rr
                d.rectangle((cx - 1, cy - 1, cx + 1, cy + 1), fill=CY if i % 2 else WH)
    if t >= B(32):                                           # explosion ring + debris
        u = since(t, 32)
        if u < 0.5:
            pp = prof_pos(B(32)); cx, cy = pp[0] + 320 * PK_S, pp[1] + 460 * PK_S
            r_ = 10 + 220 * u
            d.ellipse((cx - r_, cy - r_, cx + r_, cy + r_), outline=YL, width=4)
            d.ellipse((cx - r_ * .7, cy - r_ * .7, cx + r_ * .7, cy + r_ * .7), outline=RD, width=3)
        for px_, py_, c, sz in particles(5, 120, (prof_pos(B(32))[0] + 320 * PK_S, prof_pos(B(32))[1] + 460 * PK_S), t, B(32), spread=160, life=1.4):
            d.rectangle((px_, py_, px_ + sz - 1, py_ + sz - 1), fill=c)
    return g, pills

def scanlines(im):
    a = np.array(im); a[3::4] = (a[3::4] * 0.82).astype(np.uint8); return Image.fromarray(a)

# ---------------------------------------------------------------- full-res overlays
def hud(im, t):
    if t < B(9): return
    L = UI["hud"]
    u = ease(since(t, 9) / 0.35)
    out = clamp(since(t, 35.5) / 0.3) if t >= B(35.5) else 0
    dy = round(-L["bottom"] * (1 - u) - (L["bottom"] + 20) * out)
    if L["bottom"] + dy <= 0: return                         # fully slid off after the fight
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, L["bottom"] + dy), fill=(8, 8, 14))
    d.line((0, L["bottom"] + dy, W, L["bottom"] + dy), fill=GRY, width=4)
    blit(im, ptext("BIT", 72, WH), L["bit"][0], L["bit"][1] + dy, "lt")
    hp = bit_hp(t); flash = B(20) <= t < B(20) + 0.5 and int(t * 12) % 2 == 0
    for i in range(10):
        x0, y0 = L["hp"][0] + i * 58, L["hp"][1] + dy
        on = i < hp
        d.rectangle((x0 - 4, y0 - 4, x0 + 52, y0 + 44), fill=OUTL)
        d.rectangle((x0, y0, x0 + 48, y0 + 40), fill=CY if on else (RD if flash else (35, 38, 58)))
        if on: d.rectangle((x0, y0, x0 + 48, y0 + 8), fill=(170, 255, 255))
    blit(im, ptext("SCORE", 72, WH), W - 48, L["bit"][1] + dy, "rt")
    blit(im, ptext(f"{score(t):06d}", 72, YL), W - 48, L["score"] + dy, "rt")
    if t < B(12): return                                     # boss bar
    bu = ease(since(t, 12) / 0.3)
    k = 1 if t >= B(12) + 0.3 else bu
    lx, ly, la = L["boss_label"]
    blit(im, ptext("PROFESSOR VAGUE", 72, (215, 180, 255)), lx - round((1 - k) * 1000), ly + dy, la)
    x0, y0, x1, y1 = L["boss_bar"]; y0 += dy; y1 += dy
    d.rectangle((x0 - 6, y0 - 6, x1 + 6, y1 + 6), fill=OUTL); d.rectangle((x0, y0, x1, y1), fill=(35, 20, 55))
    hp = boss_hp(t); xf = x0 + (x1 - x0) * hp
    hurt = any(0 <= since(t, b) < 0.2 for b in (28, 29, 30, 31))
    if hp > 0:
        d.rectangle((x0, y0, xf, y1), fill=RD if hurt else PU); d.rectangle((x0, y0, xf, y0 + 10), fill=(165, 110, 215))
    for sx in range(x0, x1, 48): d.line((sx, y0, sx, y1), fill=OUTL, width=4)

def pill_text(im, pills, off):
    for x, y, text, kind in pills:
        blit(im, ptext(text, 66, GR if kind == "fixed" else WH), x * PX + off[0], y * PX + off[1] + 2)

def slam(t, b, dur=0.12):
    """Scale for a word slamming in on beat b: big -> 1."""
    u = since(t, b) / dur
    return None if u < 0 else (1 + 0.6 * (1 - ease(u)) if u < 1 else 1.0)

def title_card(im, t, f):
    L = UI["title"]; d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = L["box"]
    d.rectangle((x0, y0, x1, y1), fill=(8, 8, 14), outline=PU, width=12); d.rectangle((x0 + 24, y0 + 24, x1 - 24, y1 - 24), outline=GRY, width=4)
    if int(since(t, 4) * 3) % 2 == 0:                        # left over from bar 1, still blinking
        blit(im, ptext("PRESS START", 96, WH), W / 2, L["press_y"], "mm")
    for (s, b, col), (size, y) in zip((("LEVEL 1", 4, YL), ("THE", 5, WH), ("VAGUE", 6, WH), ("REQUIREMENTS", 7, PK)), L["lines"]):
        sc = slam(t, b)
        if sc is not None: blit(im, fit(s, size, col, L["maxw"], kind="title", px=5), W / 2, y, "mm", sc)
    spr = bit_sprite("idle", "blink" if f % 90 in (40, 41, 42) else "idle")   # a small pixel Bit on the floor
    spr = spr.resize((spr.width * 2, spr.height * 2), Image.NEAREST)          # half size: 2x instead of 4x
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
    """Dark backing so debris and fog never read through the big words."""
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.rectangle(box, fill=(8, 8, 14, round(225 * k)))
    d.rectangle(box, outline=GRY + (round(255 * k),), width=4)
    im.alpha_composite(g)

# ---------------------------------------------------------------- frame
COLD_OPEN = (2, 29)          # beats 1-2 replay film time from beat 30 (0-based 29): ×2 on frame 0, ×3 on beat 2

def level(im, t, f):
    """The game layer, upscaled, with scanlines, shake and word text."""
    g, pills = game_layer(t, f)
    off = shake(t)
    im.alpha_composite(scanlines(g.resize((W, H), Image.NEAREST)), (off[0] * PX, off[1] * PX))
    pill_text(im, pills, (off[0] * PX, off[1] * PX))

def frame(f):
    t = f / FPS
    if f < round(B(COLD_OPEN[0]) * FPS):                         # cold open: hard cut to PRESS START on beat 3's frame
        return frame(f + round((B(COLD_OPEN[1]) - B(0)) * FPS))
    TEXT_BOXES.clear()
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    if t < B(4):                                                 # PRESS START over the level, Professor lurking
        level(im, t, f)
        on = (int(since(t, 2) * 3) % 2 == 0) if t < B(3) else (int(t * 10) % 2 == 0)
        if on: blit(im, ptext("PRESS START", 110, YL if t >= B(3) else WH), W / 2, UI["press_y"], "mm")
        if t >= B(3.5): draw_wipe(im, t, B(3.5), B(4) - B(3.5))
        return im.convert("RGB")
    level(im, t, f)
    if t < B(7.5):                                               # bar 2: title card over the level
        title_card(im, t, f)
        return im.convert("RGB")
    if t < B(8): draw_wipe(im, t, B(7.5), B(8) - B(7.5), reverse=True)   # wipe out of the title
    hud(im, t)
    if B(12) <= t < B(16):                                       # boss name card: between the HUD and Bit's head
        card(im, [("BOSS:", 72, RD, "mono"), ("PROFESSOR VAGUE", 96, WH, "title")], UI["card"][1], PU, t, B(12))
    if B(24) <= t < B(28):                                       # charge meter, under the HUD
        y0 = UI["meter_y"]; d = ImageDraw.Draw(im)
        d.rectangle((40, y0, W - 40, y0 + 150), fill=(10, 12, 24), outline=CY, width=6)
        blit(im, ptext("REQUIREMENTS CHECK v2", 66, CY), W / 2, y0 + 14, "mt")
        fill = clamp(since(t, 24) / (B(28) - B(24)))
        nseg = (W - 144) // 59
        for i in range(nseg):
            x0 = 72 + i * 59
            lit = i < round(fill * nseg)
            d.rectangle((x0, y0 + 92, x0 + 50, y0 + 130), fill=(YL if fill > 0.97 and int(t * 12) % 2 else CY) if lit else (30, 34, 52))
    c = combo(t)
    if c >= 2:
        sc = slam(t, 27 + c, 0.15) or 1
        blit(im, ptext(f"×{c}", 220, YL, kind="title", px=5), *UI["combo"], "mm", sc)
    if t >= B(32):                                               # BOSS DEFEATED / TESTABLE ✓
        u = since(t, 32)
        if u < 0.1: im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, round(160 * (1 - u / 0.1)))))
        rise = ease(since(t, 35.5) / (B(36) - B(35.5))) if t >= B(35.5) else 0     # done before the end card slams
        D = UI["defeated"]
        if t < B(35.5):
            x0, y0, x1, y1a, y1b = D["plate"]
            plate(im, (x0, y0, x1, y1a if t < B(34) else y1b), ease(u / 0.1))
            sc = slam(t, 32, 0.15)
            for s, y in D["lines"]: blit(im, fit(s, D["size"], YL, D["maxw"], kind="title", px=5), D["cx"], y, "mm", sc)
        else:
            x0, y0, x1, y1 = UI["end"]["plate"]
            plate(im, (x0, round(lerp(D["test_y"] - 100, y0, rise)), x1, round(lerp(D["test_y"] + 100, y1, rise))))
        if t >= B(34):
            sc = slam(t, 34, 0.15)
            blit(im, fit("TESTABLE ✓", 150, GR, TEXT_W, kind="title", px=5), lerp(D["cx"], UI["end"]["cx"], rise),
                 lerp(D["test_y"], UI["end"]["test_y"], rise), "mm", sc)
    if t >= B(36):                                               # end card
        E = UI["end"]; big = end_size()
        cols = {"THE GAME": PK, "COMING 2027": YL}
        for (s, b), y in zip(E["lines"], E["ys"]):
            sc = slam(t, b, 0.12)
            if sc: blit(im, ptext(s, big, cols.get(s, WH), kind="title", px=4), E["cx"], y, "mm", sc)
        sc = slam(t, 38.5, 0.12)
        if sc: blit(im, ptext("@vibewithamitai", 72, CY, kind="mono", px=3), E["cx"], E["handle_y"], "mm", sc)
    return im.convert("RGB")

_END = []
def end_size():
    """One size for every end-card title line: the largest that fits the text width."""
    if not _END:
        size = 200
        while max(ptext(s, size, WH, kind="title", px=4).width for s, _ in UI["end"]["lines"]) > TEXT_W: size -= 2
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

# ---------------------------------------------------------------- layouts
# Game coords (GROUND, BIT_X, ...) are in game pixels (1/4 res); UI positions are full-res pixels.
LAYOUTS = {
    "9x16": dict(W=1080, H=1920, SAFE=True, TEXT_W=800,
                 GROUND=396, BIT_H=156, BIT_X=76, DASH_X=150, END_BIT_X=135, JUMP=60,
                 PK_S=0.24, PROF_X=200, PROF_TOP=128, LURK=150,
                 INTERCEPT=(118, 190), PARK={"FAST": (100, 104), "TBD": (64, 140)},
                 UI=dict(hud=dict(bottom=350, bit=(48, 28), hp=(48, 118), score=112, boss_label=(48, 190, "lt"), boss_bar=(48, 280, 1032, 326)),
                         press_y=560, card=(540, 712), meter_y=368, combo=(680, 1250),
                         title=dict(box=(36, 380, 1044, 1240), press_y=250, lines=[(200, 540), (150, 760), (150, 920), (150, 1080)],
                                    maxw=800, mini_bit_x=300),
                         defeated=dict(plate=(24, 375, 1056, 690, 900), lines=[("BOSS", 460), ("DEFEATED", 610)], size=170, maxw=960,
                                       cx=540, test_y=800),
                         end=dict(plate=(24, 170, 1056, 950), cx=540, test_y=250, handle_y=890, ys=[400, 520, 640, 770],
                                  lines=[("THE ADVENTURES", 36), ("OF BIT", 36), ("THE GAME", 37), ("COMING 2027", 38)]))),
    "16x9": dict(W=1920, H=1080, SAFE=False, TEXT_W=1240,
                 GROUND=230, BIT_H=110, BIT_X=110, DASH_X=200, END_BIT_X=85, JUMP=48,
                 PK_S=0.19, PROF_X=345, PROF_TOP=50, LURK=110,
                 INTERCEPT=(190, 95), PARK={"FAST": (95, 64), "TBD": (60, 98)},
                 UI=dict(hud=dict(bottom=190, bit=(48, 24), hp=(48, 106), score=104, boss_label=(960, 24, "mt"), boss_bar=(700, 110, 1220, 150)),
                         press_y=300, card=(700, 220), meter_y=200, combo=(880, 560),
                         title=dict(box=(300, 150, 1620, 830), press_y=80, lines=[(170, 280), (130, 440), (130, 570), (130, 710)],
                                    maxw=1200, mini_bit_x=170),
                         defeated=dict(plate=(560, 210, 1880, 470, 640), lines=[("BOSS DEFEATED", 330)], size=150, maxw=1240,
                                       cx=1220, test_y=540),
                         end=dict(plate=(560, 60, 1880, 880), cx=1220, test_y=160, handle_y=770, ys=[330, 480, 630],
                                  lines=[("THE ADVENTURES OF BIT", 36), ("THE GAME", 37), ("COMING 2027", 38)]))),
}

def use_layout(name):
    """Switch every layout-dependent global (canvas, sprites, arena, positions) to one of LAYOUTS."""
    L = LAYOUTS[name]; g = globals()
    g.update(L); g["LAYOUT"] = name
    g["GW"], g["GH"] = L["W"] // PX, L["H"] // PX
    g["BK"], g["EZ"] = L["BIT_H"] / 700, L["BIT_H"] / 120
    if L["SAFE"]: g["SAFE_BOTTOM"], g["SAFE_RIGHT"], g["SAFE_BAND"] = L["H"] - 350, L["W"] - 140, (700, 1600)
    else: g["SAFE_BOTTOM"], g["SAFE_RIGHT"], g["SAFE_BAND"] = L["H"], L["W"], (0, 0)
    g["BIT_BASE"] = {p: _bit_base(p) for p in ("idle", "fire")}
    g["HAND"] = (488 * BK, 280 * BK)
    g["POINTER"] = (620 * PK_S, 330 * PK_S)
    mid, over = GROUND - BIT_H / 2, GROUND - BIT_H - 35
    g["THROWS"] = {"FAST": (16, 17, (BIT_X, GROUND - 16), False), "USER-FRIENDLY": (18, 19, (BIT_X, mid), False),
                   "TBD": (19, 20, (DASH_X, mid), True), "ADEQUATE": (21, 22, (DASH_X, over), False)}
    g["ARENA"] = arena()
    _SHATTER.clear(); _END.clear()

# ---------------------------------------------------------------- sound
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

# --- drums (noise channel + triangle kick)
def kick(): x = sweep(160, 40, 0.16, "tri", curve=0.4); return x * decay(len(x), 0.05)
def snare(): n = noise(0.14); return (n * 0.8 + sweep(220, 160, 0.14, "tri") * 0.4) * decay(len(n), 0.04)
def hat(): n = np.diff(noise(0.035), prepend=0) * 0.5; return n * decay(len(n), 0.008)
def crash(): n = np.diff(noise(1.0), prepend=0) * 0.4; return n * decay(len(n), 0.3)

A, Bb, C, D, E, F, G = 57, 58, 60, 62, 64, 65, 67            # A3 = 57
def music():
    """Original 120 BPM chiptune in A minor. Bar 1 is silence (PRESS START); music starts on bar 2's downbeat."""
    buf = np.zeros(NS + SR, np.float32)
    bt = lambda bar, beat: ((bar - 1) * 4 + beat) * SPB      # composer's grid: bar 1-10, beat 0-3.75
    roots = {2: [A], 3: [A], 4: [F], 5: [A], 6: [F, G], 7: [E], 8: [A], 9: [A]}
    for bar, rs in roots.items():                            # triangle bass, octave-bouncing 8ths
        for i in range(8):
            if bar == 9 and i >= 2: break                    # bass drops out after the explosion
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
    arp = {3: [A, C, E, C + 12], 4: [F, A, C + 12, A]}       # quiet 16th arps under the intro
    for bar, ns in arp.items():
        for i in range(16): put(buf, bt(bar, i / 4), tone(ns[i % 4] + 12, SPB / 4 * 0.8, duty=0.125, s=0.3), 0.07)
    lead = {5: [69, 72, 76, 74, 72, None, 69, 67], 6: [65, 69, 72, 74, 71, None, 67, 71],
            8: [81, 79, 76, 79, 81, 84, 83, 81]}
    for bar, ns in lead.items():                             # square lead, 25% duty
        for i, m in enumerate(ns):
            if m: put(buf, bt(bar, i / 2), tone(m, SPB / 2 * 0.85, duty=0.25, s=0.6), 0.13)
    rise = [52, 56, 59, 64, 56, 59, 64, 68, 59, 64, 68, 71, 64, 68, 71, 76]
    for i, m in enumerate(rise):                             # bar 7: rising arpeggio over E
        put(buf, bt(7, i / 4), tone(m + 12, SPB / 4 * 0.85, duty=0.25, s=0.6), 0.08 + 0.006 * i)
    for i, m in enumerate([69, 73, 76]):                     # bar 10: outro hit, rising A major
        put(buf, bt(10, i), tone(m + 12, SPB * 0.7, duty=0.25, s=0.5), 0.14); put(buf, bt(10, i), kick(), 0.5)
    return buf[:NS]

# --- SFX (all synthesised)
def coin(): return np.concatenate([tone(83, 0.07, duty=0.5, s=1), tone(88, 0.3, duty=0.5, d=0.25, s=0.0)])
def thump(): x = sweep(120, 32, 0.3, "sin", curve=0.5); return x * decay(len(x), 0.09) + np.pad(snare()[:2000], (0, len(x) - 2000)) * 0.3
def jump(): x = sweep(300, 1000, 0.16, duty=0.25, curve=0.7); return x * adsr(len(x), d=0.1, s=0.3)
def whoosh():
    n = noise(0.24); e = np.sin(np.linspace(0, np.pi, len(n))) ** 2
    return (lowpass(n, 0.25) - lowpass(n, 0.03)) * e * 2
def throw(): x = sweep(700, 220, 0.2, duty=0.25); return (x * 0.6 + noise(0.2) * 0.3) * decay(int(0.2 * SR), 0.07)
def hit():
    n = int(0.3 * SR); return (noise(0.3) * 0.7 + sweep(160, 50, 0.3, duty=0.5) * 0.6) * decay(n, 0.07)
def laugh():
    out = []
    for i, m in enumerate([62, 61, 60, 58, 57]):            # "HA ha ha ha ha", falling, with wobble
        d = 0.09 if i else 0.12; x = tt(d)
        f = hz(m) * (1 + 0.03 * np.sin(2 * np.pi * 28 * x)); ph = np.cumsum(f) / SR % 1
        v = (2 * ph - 1) * np.sin(np.pi * x / d) ** 0.5 + noise(d) * 0.15
        out += [v * (1.0 - 0.12 * i), np.zeros(int(0.035 * SR))]
    return np.concatenate(out)
def charge(dur):
    x = sweep(180, 1400, dur, duty=0.25, curve=1.6); trem = 0.6 + 0.4 * np.sin(2 * np.pi * 16 * tt(dur))
    return x * trem * np.linspace(0.2, 1, len(x))
def laser(): x = sweep(1800, 180, 0.28, duty=0.5, curve=0.5); return x * decay(len(x), 0.1)
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
def tick(): return tone(96, 0.03, duty=0.5, d=0.02, s=0.0)

# Every sound event: (beat, label, sound, gain). The animation code uses the same beat numbers.
def events():
    ev = [(3, "coin", coin(), 0.5), (8, "landing thump", thump(), 0.9), (12, "laugh", laugh(), 0.5)]
    ev += [(12 + i / 2, "boss bar tick", tick(), 0.25) for i in range(8)]
    ev += [(16, "throw FAST", throw(), 0.5), (16.5, "jump", jump(), 0.4),
           (18, "throw USER-FRIENDLY", throw(), 0.5), (18.5, "dash right", whoosh(), 0.7),
           (19, "throw TBD", throw(), 0.5), (20, "hit TBD", hit(), 0.8), (20, "TBD bursts on Bit", burst(), 0.4),
           (21, "throw ADEQUATE", throw(), 0.5), (22, "ADEQUATE misses", whoosh(), 0.5),
           (23, "dash left", whoosh(), 0.7), (24, "laser charge", charge(B(28) - B(24)), 0.25)]
    for i, (b, w) in enumerate(zip((28, 29, 30, 31), WORDS)):
        ev += [(b - 0.5, f"throw {w}", throw(), 0.35), (b, f"laser fire {w}", laser(), 0.35)]
        ev += [(b, f"combo ding ×{i + 1}", ding(i * 2), 0.3)] if i else []
        ev += [] if w in FIXED else [(b, f"{w} bursts", burst(), 0.4)]
    ev += [(32, "explosion", explosion(), 0.9), (34, "victory chord", victory(), 0.5),
           (36, "victory hop", jump(), 0.3), (39, "final thump", final_thump(), 0.9)]
    return ev

def mix():
    m = music()
    s = np.zeros(NS + 2 * SR, np.float32)
    for b, _, x, g in events(): put(s, B(b), x, g)
    out = m + s[:NS]
    cut = round(B(COLD_OPEN[0]) * FPS)                                 # cold open: the same second of the fight,
    n, src = cut * SR // FPS, round((B(COLD_OPEN[1]) - B(0)) * FPS) * SR // FPS   # frame-exact, matching frame()
    out[:n] = out[src:src + n]; out[n - 220:n] *= np.linspace(1, 0, 220)
    out[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
    return (out / np.abs(out).max() * 10 ** (-6.5 / 20)).astype(np.float32)  # -6 dBFS peak after AAC, with margin

# ---------------------------------------------------------------- beat measurement
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
    on_beat = np.abs(k - np.round(k)) < 0.12                 # drop 8th-note hats and SFX-free off-beats
    A_ = np.vstack([np.ones(on_beat.sum()), np.round(k[on_beat])]).T
    (t0, p), *_ = np.linalg.lstsq(A_, onsets[on_beat], rcond=None)
    beats = [max(0.0, round(t0 + j * p, 4)) for j in range(40)]
    return {"bpm": round(60 / p, 3), "beats": beats, "downbeats": beats[::4],
            "measured_onsets": int(on_beat.sum()), "period_autocorr": round(period, 4)}

def write_beats():
    OUT.mkdir(exist_ok=True)
    info = measure_beats(music())
    BEATS[:] = info["beats"] + [info["beats"][-1] + 60 / info["bpm"]]
    info["hits"] = sorted({round(B(b), 4) for b, *_ in events() if b >= COLD_OPEN[0]} |
                          {round(B(b - COLD_OPEN[1]), 4) for b, *_ in events() if COLD_OPEN[1] <= b < COLD_OPEN[1] + COLD_OPEN[0]})
    (OUT / "beats.json").write_text(json.dumps(info, indent=1))
    print(f"beats.json: {info['bpm']} BPM from {info['measured_onsets']} on-beat onsets, beat 0 at {info['beats'][0]} s")
    return info

# ---------------------------------------------------------------- beat grid (Gate 2)
SHOTS = [
    (1, "Cold open (beats 1-2): a replay of the bar 8 fight, USER-FRIENDLY bursts (×2) on frame 0 and TBD -> 10 MB/s (×3) on beat 2. "
        "Hard cut on beat 3 to PRESS START over the level, the Professor lurking in the fog",
     [(0, "cold open: ×2 burst, WITHIN 200 ms parked, shake"), (1, "cold open: TBD -> 10 MB/s, ×3, shake"),
      (2, "hard cut: PRESS START over the level, Professor in the fog"), (3, "coin; PRESS START goes yellow, fast blink"),
      (3.5, "pixel wipe starts; ends on the bar 2 downbeat")]),
    (2, "Title card over the level: LEVEL 1 / THE / VAGUE / REQUIREMENTS slam in, one per beat; PRESS START still blinks above, small Bit on the floor",
     [(4, "music starts; LEVEL 1 + snare"), (5, "THE + snare"), (6, "VAGUE + snare"), (7, "REQUIREMENTS + snare"),
      (7.5, "pixel wipe out to the arena; Bit starts falling from the top")]),
    (3, "Bit (1.3×) drops in and squashes on landing. HUD slides in",
     [(8, "landing thump + squash + small shake"), (9, "HUD slides down")]),
    (4, "Fog rolls in; Professor Vague rises out of it laughing. BOSS: PROFESSOR VAGUE card above Bit's head. Boss bar fills over 4 beats",
     [(11.5, "fog thickens"), (12, "laugh; Professor rises; name card; boss bar starts filling"), (14, "laugh ends"), (16, "boss bar full")]),
    (5, "Professor throws FAST, then USER-FRIENDLY. Bit jumps the first and dashes past the second",
     [(16, "throw FAST"), (16.5, "Bit jumps"), (17, "FAST passes under Bit (jump peak), then speeds off; +500"), (17.5, "Bit lands"),
      (18, "throw USER-FRIENDLY"), (18.5, "Bit dashes right"), (19, "USER-FRIENDLY misses and speeds off; throw TBD; +500")]),
    (6, "TBD hits Bit and bursts: X X eyes, screen shake, HP -3. ADEQUATE misses overhead. Bit dashes back",
     [(20, "TBD hits and bursts: X X eyes (6 frames), shake, HP 10 -> 7, Professor laughs"), (21, "throw ADEQUATE"),
      (22, "ADEQUATE misses overhead and speeds off; +500"), (23, "Bit dashes back left")]),
    (7, "Bit's eyes go determined. REQUIREMENTS CHECK v2 meter (under the HUD) fills over 4 beats; charge sparks around Bit",
     [(24, "determined eyes; meter and laser charge start"), (27.5, "Professor throws FAST"), (28, "meter full")]),
    (8, "The Professor throws one word per beat; Bit shoots each out of the air on the beat. Fixed words park top left",
     [(28, "beam hits FAST -> WITHIN 200 ms; +1000"), (28.5, "throw USER-FRIENDLY"), (29, "USER-FRIENDLY bursts; ×2"),
      (29.5, "throw TBD"), (30, "TBD -> 10 MB/s; ×3"), (30.5, "throw ADEQUATE"),
      (31, "ADEQUATE bursts; ×4; boss bar drains to zero by beat 33")]),
    (9, "Boss bar hits zero. BOSS DEFEATED. The Professor's fog breaks into pixels. TESTABLE ✓ in green",
     [(32, "explosion, flash, big shake; BOSS DEFEATED; Professor shatters; +10000"), (33, "Bit happy ^ ^"), (34, "victory chord; TESTABLE ✓"),
      (35.5, "BOSS DEFEATED clears; HUD slides out; TESTABLE ✓ rises to the top")]),
    (10, "Bit (1.3×) hops to centre stage. End card: THE ADVENTURES / OF BIT and COMING 2027 at the same size, THE GAME, @vibewithamitai",
     [(36, "victory hop; THE ADVENTURES / OF BIT"), (37, "THE GAME"), (38, "COMING 2027"),
      (38.5, "@vibewithamitai"), (39, "final thump (beat 40)"), (40, "end of film, frame 600")]),
]
def beat_label(b):
    whole = int(b); frac = b - whole
    s = f"{whole + 1}"
    return s + {0: "", 0.5: " &"}.get(round(frac, 2), f" +{frac:.2f}")

def write_grid():
    rows = ["# Bit: Level 1 — beat grid", "",
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
def style_frames():
    use_layout("9x16")
    d = OUT / "style_frames"; d.mkdir(parents=True, exist_ok=True)
    for name, b in {"01_title_card": 7.24, "02_mid_fight": 30.2, "03_boss_defeated": 34.4}.items():
        f = round(B(b) * FPS); frame(f).save(d / f"{name}.png")
        print(f"{name}.png  frame {f}  t={f / FPS:.2f}s", safe_zone_violations(f) or "safe zone OK")

def write_wav(path, x):
    import wave
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.repeat(pcm, 2).tobytes())

def render(name):
    """Raw RGB frames piped to ffmpeg, muxed with the synthesised mix. Exactly 600 frames / 20.0 s."""
    import subprocess, time
    use_layout(name)
    wav = OUT / "mix.wav"; write_wav(wav, mix())
    dst = OUT / f"teaser_{name}.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-t", f"{N / FPS:.3f}", "-movflags", "+faststart",
                           str(dst)], stdin=subprocess.PIPE)
    bad, t0 = [], time.time()
    for f in range(N):
        ff.stdin.write(frame(f).tobytes()); bad += safe_zone_violations(f)
        if f % 100 == 99: print(f"  frame {f + 1}/{N}  {time.time() - t0:.0f}s", flush=True)
    ff.stdin.close(); ff.wait(); wav.unlink()
    checks = "on screen, safe zone and 48 px minimum" if SAFE else "on screen and 48 px minimum"
    print(f"{dst.name} written;", f"{len(bad)} readability violations" if bad else f"{checks} OK on all 600 frames")
    for v in bad[:20]: print("  ", v)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    use_layout("9x16")
    if cmd in ("beats", "grid", "frames", "all"): write_beats()
    if cmd in ("grid", "all"): write_grid()
    if cmd in ("frames", "all"): style_frames()
    if cmd in ("render", "all"):
        for name in LAYOUTS: render(name)
