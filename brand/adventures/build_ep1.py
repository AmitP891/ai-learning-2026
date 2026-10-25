"""The Adventures of Bit - Episode 1: The Vague One (16:9, 1920x1080)."""
import re, io, math, random, subprocess, wave
import numpy as np, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from prof import professor

W, H = 1920, 1080
FPS, SR = 30, 44100
random.seed(3); rng = np.random.default_rng(3)
CY = (0, 240, 255); PK = (255, 43, 214); WH = (255, 255, 255); GR = (57, 255, 136)
RD = (255, 70, 90); YL = (255, 214, 0); GRY = (150, 155, 175); OR = (217, 119, 87)
INTER = "/usr/share/fonts/opentype/inter/"
DJ = "/usr/share/fonts/truetype/dejavu/"
def FI(s, w="InterDisplay-Black"): return ImageFont.truetype(INTER + w + ".otf", s)
def FD(s, w="DejaVuSans-Bold"): return ImageFont.truetype(DJ + w + ".ttf", s)
def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def fade(c, k): return tuple(int(v * k) for v in c)

# ---------------------------------------------------------------- audio
def wav(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
clip = {}
for i in range(1, 11): clip[f"bit{i}"] = wav(f"seg_bit{i}.wav")
for i in range(1, 5): clip[f"narrator{i}"] = wav(f"seg_narrator{i}.wav")
for i in range(1, 6): clip[f"vague{i}"] = wav(f"segfx_vague{i}.wav")
for i in range(1, 8): clip[f"bitx{i}"] = wav(f"seg_bitx{i}.wav")
for i in range(1, 4): clip[f"narratorx{i}"] = wav(f"seg_narratorx{i}.wav")
for i in range(1, 4): clip[f"vaguex{i}"] = wav(f"segfx_vaguex{i}.wav")
SCENES = [["narrator1", "vague1"], ["bit1", "narrator2"], ["bit2", "narratorx1", "bitx1", "vague2"],
          ["bit3", "bitx2", "bitx3", "vaguex1", "bitx4", "bit4"], ["narrator3", "narratorx2", "bitx5", "bit5"],
          ["bit6", "bit7", "vaguex2", "bitx6", "narratorx3", "vague3"], ["narrator4", "vague4", "bitx7", "vaguex3", "bit8"],
          ["bit9"], ["vague5", "bit10"]]
INTRO, OUTRO, LGAP, SGAP = 4.0, 7.0, 0.55, 1.1
events = []; scene_t = []; t = INTRO
for sc in SCENES:
    s0 = t
    for name in sc:
        events.append((name, t, len(clip[name]) / SR)); t += len(clip[name]) / SR + LGAP
    t += SGAP - LGAP; scene_t.append((s0, t))
END_T = t; DUR = t + OUTRO; N = int(DUR * FPS)
EV = {e[0]: (e[1], e[2]) for e in events}
track = {k: np.zeros(int(DUR * SR) + SR, np.float32) for k in ("bit", "narrator", "vague")}
for name, st, d in events:
    k = re.match(r"[a-z]+", name).group(0).rstrip("x"); i = int(st * SR); track[k][i:i + len(clip[name])] += clip[name]
hop = SR // FPS
def envelope(x):
    r = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) for i in range(N)])
    nz = r[r > 0.01]; p = np.percentile(nz, 90) if len(nz) else 1
    e = np.clip((r - 0.01) / (p - 0.01), 0, 1); return np.convolve(e, [.25, .5, .25], "same")
ENV = {k: envelope(v) for k, v in track.items()}
def S(name): return EV[name][0]
def E(name): return EV[name][0] + EV[name][1]
def scene_of(t):
    for i, (a, b) in enumerate(scene_t):
        if t < b: return i
    return len(scene_t)

# ---------------------------------------------------------------- Bit
BS = 0.95
svg = open("/home/claude/ai-learning-2026/brand/bit/bit.svg").read()
svg = re.sub(r'<g id="eyes">.*?</g>', '', svg, flags=re.S); svg = re.sub(r'<path id="mouth"[^>]*/>', '', svg)
def svg_img(s, scale):
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=s.encode(), output_width=int(600 * scale), output_height=int(700 * scale)))).convert("RGBA")
BIT_BASE = svg_img(svg, BS)
def bit_img(f, mood, belt=0.0):
    r = BIT_BASE.copy(); d = ImageDraw.Draw(r); s = BS; P = lambda x, y: (x * s, y * s); a = ENV["bit"][f]
    blink = (f % 100) in (0, 1, 2) and mood == "norm"
    for ex in (244, 356):
        cx, cy = P(ex, 199)
        if blink: d.rounded_rectangle((cx - 22 * s, cy - 4 * s, cx + 22 * s, cy + 4 * s), radius=3, fill=CY)
        elif mood == "happy": d.arc((cx - 24 * s, cy - 14 * s, cx + 24 * s, cy + 30 * s), 200, 340, fill=CY, width=int(10 * s))
        elif mood == "shock":
            d.ellipse((cx - 27 * s, cy - 31 * s, cx + 27 * s, cy + 31 * s), fill=CY); d.ellipse((cx - 9 * s, cy - 9 * s, cx + 9 * s, cy + 9 * s), fill=(23, 26, 43))
        elif mood == "alert": d.rectangle((cx - 24 * s, cy - 6 * s, cx + 24 * s, cy + 14 * s), fill=RD)
        elif mood == "determined":
            pts = [(cx - 26 * s, cy - 20 * s), (cx + 26 * s, cy - 6 * s), (cx + 26 * s, cy + 24 * s), (cx - 26 * s, cy + 24 * s)] if ex < 300 else \
                  [(cx - 26 * s, cy - 6 * s), (cx + 26 * s, cy - 20 * s), (cx + 26 * s, cy + 24 * s), (cx - 26 * s, cy + 24 * s)]
            d.polygon(pts, fill=CY)
        else: d.rounded_rectangle((cx - 22 * s, cy - 29 * s, cx + 22 * s, cy + 29 * s), radius=int(12 * s), fill=CY)
    mx, my = P(300, 262); col = RD if mood == "alert" else CY
    if a > 0.08:
        h = (8 + 38 * a) * s; w = (56 if mood != "shock" else 40) * s
        d.rounded_rectangle((mx - w / 2, my - h / 2, mx + w / 2, my + h / 2), radius=int(min(h, w) / 2), fill=col)
    elif mood == "shock": d.ellipse((mx - 12 * s, my - 12 * s, mx + 12 * s, my + 12 * s), outline=CY, width=int(7 * s))
    elif mood == "determined": d.line((mx - 34 * s, my + 4 * s, mx + 34 * s, my - 4 * s), fill=CY, width=int(9 * s))
    else: d.arc((mx - 40 * s, my - 40 * s, mx + 40 * s, my + 12 * s), 25, 155, fill=col, width=int(9 * s))
    if belt > 0:
        y0, y1 = 560 * s, 600 * s
        g = Image.new("RGBA", r.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        gd.rounded_rectangle((165 * s, y0 - 6, 435 * s, y1 + 6), radius=14, fill=CY + (int(160 * belt),)); g = g.filter(ImageFilter.GaussianBlur(12))
        r.alpha_composite(g); d = ImageDraw.Draw(r)
        d.rounded_rectangle((170 * s, y0, 430 * s, y1), radius=10, fill=fade((20, 30, 50), 1), outline=fade(CY, belt), width=4)
        d.text((300 * s, (y0 + y1) / 2), "MCP", font=FD(int(30 * s)), fill=fade(CY, belt), anchor="mm")
    return r
def paste_bit(im, f, mood, x, y, scale=1.0, belt=0.0, t=0.0, bob=True):
    r = bit_img(f, mood, belt)
    if scale != 1.0: r = r.resize((int(r.width * scale), int(r.height * scale)), Image.LANCZOS)
    by = int(6 * math.sin(t * 2 * math.pi * 0.6)) if bob else 0
    sh = int(7 * math.sin(t * 80)) if mood == "shock" else 0
    im.alpha_composite(r, (int(x - r.width / 2 + sh), int(y - r.height + by)))

def paste_prof(im, f, t, x, y, scale=0.8, mood="smug", alpha=1.0):
    p = professor(ENV["vague"][f], t, mood, scale)
    if alpha < 1: p.putalpha(p.getchannel("A").point(lambda v: int(v * alpha)))
    im.alpha_composite(p, (int(x - p.width / 2), int(y - p.height)))

def spark(im, x, y, t, k=1.0, size=1.0):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    r = (40 + 8 * math.sin(t * 6)) * size
    d.ellipse((x - r * 2, y - r * 2, x + r * 2, y + r * 2), fill=OR + (int(90 * k),)); g = g.filter(ImageFilter.GaussianBlur(25))
    im.alpha_composite(g); d = ImageDraw.Draw(im)
    pts = []
    for i in range(16):
        a = i * math.pi / 8 + t * 0.8; rr = r if i % 2 == 0 else r * 0.38
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    d.polygon(pts, fill=fade((255, 170, 130), k))

# ---------------------------------------------------------------- backgrounds
sky = np.zeros((H, W, 3), np.uint8); gg = np.linspace(0, 1, H)[:, None]
sky[..., 0] = 8 + 16 * gg; sky[..., 1] = 9 + 10 * gg; sky[..., 2] = 22 + 30 * gg
SKY = Image.fromarray(sky).convert("RGBA"); sd = ImageDraw.Draw(SKY)
for _ in range(220):
    x, y = rng.integers(0, W), rng.integers(0, 700); rr = rng.choice([1, 1, 2]); sd.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(200, 210, 255))
towers = []; x = -30
while x < W + 30:
    w = int(rng.integers(110, 200)); h = int(rng.integers(320, 700)); towers.append((x, w, h, [int(w * rng.uniform(.35, .8)) for _ in range(40)])); x += w + int(rng.integers(10, 34))
VT = len(towers) // 2
def city(grey, tower_fail=0.0):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); base = 940
    for i, (x, w, h, lens) in enumerate(towers):
        hh = h + (160 if i == VT else 0)
        gi = min(1, max(0, grey * 1.6 - (i % 5) * 0.12))
        edge = tuple(int(CY[k] * (1 - gi) + GRY[k] * gi * 0.55) for k in range(3))
        d.rectangle((x, base - hh, x + w, base), fill=(14, 18, 34), outline=edge, width=3)
        for j, ly in enumerate(range(base - hh + 26, base - 16, 24)):
            d.line((x + 14, ly, x + 14 + lens[j % 40], ly), fill=tuple(int(v * .55) for v in edge), width=4)
    d.rectangle((0, base, W, H), fill=(10, 12, 24))
    return im
CITY = [city(g) for g in np.linspace(0, 1, 11)]
CITYG = [c.filter(ImageFilter.GaussianBlur(10)) for c in CITY]
def fog_sprite(sz, seed):
    r = np.random.default_rng(seed); a = np.zeros((sz, sz), np.float32); yy, xx = np.mgrid[0:sz, 0:sz]
    for _ in range(36):
        cx, cy = r.normal(sz / 2, sz / 7, 2); rr = r.uniform(sz / 10, sz / 4.5)
        a += np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * rr ** 2))) * r.uniform(.3, .8)
    a = np.clip(a / a.max(), 0, 1) ** 1.2; rr2 = np.sqrt((xx - sz / 2) ** 2 + (yy - sz / 2) ** 2) / (sz / 2); a *= np.clip(1 - rr2, 0, 1) ** 1.5
    im = Image.new("RGBA", (sz, sz), (150, 150, 175, 0)); im.putalpha(Image.fromarray((a * 220).astype(np.uint8))); return im
FOGS = [fog_sprite(640, s) for s in range(3)]
def city_scene(t, grey, fog=0.0):
    im = SKY.copy(); ci = int(round(min(1, max(0, grey)) * 10))
    im.alpha_composite(CITYG[ci]); im.alpha_composite(CITY[ci])
    if fog > 0:
        for i, fg in enumerate(FOGS):
            x = int(-640 + (W + 500) * fog * 0.85 + i * 420 + 40 * math.sin(t * .7 + i)); y = 560 + i * 120
            im.alpha_composite(fg, (x, y)); im.alpha_composite(fg, (x - 700, y + 60))
    return im
LAB = Image.new("RGBA", (W, H), (12, 13, 26, 255)); ld = ImageDraw.Draw(LAB)
for gx in range(-2000, 4000, 120): ld.line((W / 2 + (gx - W / 2) * 0.25, 760, gx, H), fill=(30, 34, 60), width=2)
for i, gy in enumerate([760, 790, 830, 885, 960, 1060]): ld.line((0, gy, W, gy), fill=(30, 34, 60), width=2)
ld.rectangle((0, 0, W, 760), fill=(14, 15, 30))
for x in range(0, W, 80): ld.line((x, 0, x, 760), fill=(18, 20, 38))

# ---------------------------------------------------------------- UI helpers
def card(d, box, title=None, border=CY, fill=(18, 20, 32), k=1.0, r=22, width=4):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=fade(border, k), width=width)
    if title: d.text((box[0] + 28, box[1] + 22), title, font=FD(26, "DejaVuSansMono-Bold"), fill=fade(border, k))
def caption(im, text, t0, t, y=980, col=WH, size=46):
    if t < t0: return
    k = ease((t - t0) / 0.35); d = ImageDraw.Draw(im); f = FD(size)
    w = d.textlength(text, font=f)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    od.rounded_rectangle((W / 2 - w / 2 - 34, y - 42, W / 2 + w / 2 + 34, y + 42), radius=40, fill=(8, 8, 16, int(200 * k)))
    im.alpha_composite(ov); d = ImageDraw.Draw(im); d.text((W / 2, y), text, font=f, fill=fade(col, k), anchor="mm")
def glitch(im, text, xy, font, col, t, t0, cps=18):
    if t < t0: return
    s = text[:int(min(len(text), (t - t0) * cps))]; d = ImageDraw.Draw(im); j = 6 if random.random() < .2 else 1.5
    d.text((xy[0] + j, xy[1]), s, font=font, fill=(255, 40, 80), anchor="mm"); d.text((xy[0] - j, xy[1]), s, font=font, fill=(0, 200, 255), anchor="mm")
    d.text(xy, s, font=font, fill=col, anchor="mm")
def arrow(d, x1, y1, x2, y2, c, w=6):
    d.line((x1, y1, x2, y2), fill=c, width=w); a = math.atan2(y2 - y1, x2 - x1); L = 24
    d.polygon([(x2, y2), (x2 - L * math.cos(a - .45), y2 - L * math.sin(a - .45)), (x2 - L * math.cos(a + .45), y2 - L * math.sin(a + .45))], fill=c)
RUN = Image.open("/tmp/claude-0/-home-claude/21daa8ca-6e20-5e95-ae03-055ac8e41af7/scratchpad/ytlong/run-output-clean.png").convert("RGBA")
RUN = RUN.resize((1000, int(RUN.height * 1000 / RUN.width)), Image.LANCZOS)
CODE = ['VAGUE = ["fast", "quick", "user-friendly",', '         "easy", "adequate", ...]', '',
        'def check_requirement(req_id):', '    if not re.search(r"\\bshall\\b", low):', '        issues.append("Weak modal verb")',
        '    if vague: issues.append("Vague words")', '    if "tbd" in low:', '        issues.append("Contains TBD")',
        '    if low.count("shall") > 1:', '        issues.append("Split it up")', '    if not is_measurable(clause):', '        issues.append("Nothing measurable")']

# ---------------------------------------------------------------- scenes
def sc_intro(f, t):
    im = SKY.copy(); im.alpha_composite(CITYG[0]); im.alpha_composite(CITY[0])
    ov = Image.new("RGBA", (W, H), (6, 6, 14, 190)); im.alpha_composite(ov)
    k = ease((t - .3) / .8); tl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); td = ImageDraw.Draw(tl)
    td.text((W / 2, 300), "THE", font=FI(70), fill=CY + (255,), anchor="mm")
    td.text((W / 2, 420), "ADVENTURES OF BIT", font=FI(140), fill=PK + (255,), anchor="mm")
    for L in (tl.filter(ImageFilter.GaussianBlur(20)), tl):
        L2 = L.copy(); L2.putalpha(L2.getchannel("A").point(lambda v: int(v * k))); im.alpha_composite(L2)
    d = ImageDraw.Draw(im)
    if t > 1.4:
        k2 = ease((t - 1.4) / .5); d.text((W / 2, 560), "Episode 1: The Vague One", font=FI(64, "InterDisplay-Bold"), fill=fade(WH, k2), anchor="mm")
    if t > 2.0:
        paste_bit(im, f, "determined", W / 2, 1010, 0.6, t=t)
    return im

def sc1(f, t):
    n1, v1 = S("narrator1"), S("vague1")
    grey = ease((t - (n1 + 3.5)) / 4.0); fog = ease((t - (n1 + 3.0)) / 5.0)
    im = city_scene(t, grey, fog); d = ImageDraw.Draw(im)
    vx = towers[VT][0] + towers[VT][1] / 2
    d.text((vx, max(60, 940 - towers[VT][2] - 190)), "VERIFICATION", font=FD(24, "DejaVuSansMono-Bold"), fill=CY if t < v1 + 3 else RD, anchor="mm")
    if t >= v1:
        k = ease((t - v1) / 1.0); paste_prof(im, f, t, 1420, 1080 + int(260 * (1 - k)), 0.82, "smug", k)
        L = EV["vague1"][1]; f1 = FD(54)
        glitch(im, "The system shall be... fast.", (720, 260), f1, (225, 225, 240), t, v1 + 0.2)
        glitch(im, "The display should be... user-friendly.", (720, 350), f1, (225, 225, 240), t, v1 + L * .36)
        glitch(im, "The upload rate shall be... TBD.", (720, 440), f1, RD, t, v1 + L * .7)
    if t >= v1 + EV["vague1"][1] - 1.2:
        k = ease((t - (v1 + EV["vague1"][1] - 1.2)) / .4)
        card(d, (vx - 260, 120, vx + 260, 200), None, RD, (40, 0, 10), k)
        d.text((vx, 160), "TEST CANNOT BE WRITTEN", font=FD(30, "DejaVuSansMono-Bold"), fill=fade(RD, k), anchor="mm")
    elif t < v1:
        caption(im, "In Spec City, every requirement has one job: to be tested.", n1 + .2, t, 1000, CY, 40)
    return im

def sc2(f, t):
    b1, n2 = S("bit1"), S("narrator2")
    im = LAB.copy(); d = ImageDraw.Draw(im)
    fl = 0.55 + 0.45 * abs(math.sin(t * 6))
    card(d, (980, 160, 1760, 560), None, RD, (30, 6, 14), fl, 30, 6)
    d.text((1370, 300), "MISSION ALERT", font=FI(86), fill=fade(RD, fl), anchor="mm")
    d.text((1370, 420), "Requirement: \"shall be fast\"", font=FD(40, "DejaVuSansMono-Bold"), fill=(230, 230, 240), anchor="mm")
    mood = "shock" if t < b1 + 1.2 else ("alert" if t < n2 else "determined")
    paste_bit(im, f, mood, 520, 1000, 1.05, t=t)
    if t >= n2:
        caption(im, "1 week. A lot of requirements.", n2 + .1, t, 960, YL, 46)
    return im

GRID = [(c, r) for r in range(4) for c in range(6)]
def sc3(f, t):
    b2, n3a, b3a, v2 = S("bit2"), S("narratorx1"), S("bitx1"), S("vague2")
    im = LAB.copy(); d = ImageDraw.Draw(im)
    fixed_t = b2 + 0.8
    for i, (c, r) in enumerate(GRID):
        x0 = 860 + c * 170; y0 = 190 + r * 150
        if i == 0: col = CY if t > fixed_t else GRY
        else:
            turn = b2 + 2.0 + i * 0.25
            col = GRY if t > turn else (60, 64, 90)
        d.rounded_rectangle((x0, y0, x0 + 150, y0 + 125), radius=12, fill=(18, 20, 32), outline=col, width=4)
        for j in range(3): d.line((x0 + 18, y0 + 32 + j * 28, x0 + 18 + (110 if j < 2 else 70), y0 + 32 + j * 28), fill=tuple(int(v * .6) for v in col), width=5)
        if i == 0 and t > fixed_t: d.text((x0 + 120, y0 + 100), "✓", font=FD(40), fill=GR, anchor="mm")
    if n3a <= t < v2:
        k = ease((t - n3a) / .4)
        card(d, (860, 40, 1360, 160), None, CY, (14, 22, 34), k); card(d, (1380, 40, 1880, 160), None, RD, (34, 10, 16), k)
        d.text((1110, 100), "Bit: 10 min per fix", font=FD(32), fill=fade(CY, k), anchor="mm")
        d.text((1630, 100), "Vague: 1 new every 10 s", font=FD(32), fill=fade(RD, k), anchor="mm")
    mood = "norm" if t < b2 + 2.2 else ("shock" if t < b3a else "determined")
    paste_bit(im, f, mood, 420, 1000, 1.0, t=t)
    if t >= v2:
        k = ease((t - v2) / .6); paste_prof(im, f, t, 1500, 1080 + int(300 * (1 - k)), 0.62, "smug", k)
    return im

def sc4(f, t):
    b3, r1, r2, v4a, b4c, b4 = S("bit3"), S("bitx2"), S("bitx3"), S("vaguex1"), S("bitx4"), S("bit4")
    im = LAB.copy(); d = ImageDraw.Draw(im)
    mood = "determined" if t < b4 else "happy"
    paste_bit(im, f, mood, 360, 1000, 0.95, t=t)
    if t < v4a:
        card(d, (760, 90, 1850, 830), "requirements_rules.py", CY)
        n = int(min(len(CODE), (t - b3) * 2.2 + 1))
        for i, line in enumerate(CODE[:n]):
            col = (230, 230, 240)
            if "issues.append" in line: col = YL
            if r1 <= t < r2 and i in (4, 5): col = GR
            if t >= r2 and i in (11, 12): col = GR
            d.text((800, 160 + i * 50), line, font=FD(30, "DejaVuSansMono"), fill=col)
        if r1 <= t < r2: caption(im, "Rule 1: shall. Not should, not may.", r1 + .2, t, 960, GR, 42)
        if t >= r2: caption(im, "Rule 2: no number, no test.", r2 + .2, t, 960, GR, 42)
    elif t < b4:
        k = ease((t - v4a) / .5)
        paste_prof(im, f, t, 1350, 1080, 0.85, "smug" if t < b4c else "angry", k)
        if t < b4c: caption(im, "\"Flexible. Open to interpretation.\"", v4a + .5, t, 120, (200, 196, 230), 44)
        else: caption(im, "Open to interpretation = open to argument.", b4c + .2, t, 120, CY, 44)
    else:
        k = ease((t - b4 - .4) / .5)
        spark(im, 900, 420, t, k); d = ImageDraw.Draw(im)
        d.text((900, 540), "Claude", font=FI(48, "InterDisplay-Bold"), fill=fade((255, 190, 160), k), anchor="mm")
        card(d, (1360, 330, 1840, 510), None, CY, (18, 20, 32), k)
        d.text((1600, 390), "check_requirement()", font=FD(32, "DejaVuSansMono-Bold"), fill=fade(CY, k), anchor="mm")
        d.text((1600, 450), "my Python rules", font=FD(28, "DejaVuSans"), fill=fade(GRY, k), anchor="mm")
        if t > b4 + 1.0:
            arrow(d, 990, 390, 1340, 390, fade(CY, k)); d.text((1165, 350), "tool_use", font=FD(28, "DejaVuSansMono"), fill=fade(CY, k), anchor="mm")
        if t > b4 + 2.0:
            arrow(d, 1340, 470, 990, 470, fade(OR, k)); d.text((1165, 512), "tool_result", font=FD(28, "DejaVuSansMono"), fill=fade(OR, k), anchor="mm")
        if t > b4 + 3.2:
            caption(im, "Claude asks. My code checks. Claude explains and suggests a fix.", b4 + 3.2, t, 760, WH, 36)
    return im

def sc5(f, t):
    n3, n5a, b5a, b5 = S("narrator3"), S("narratorx2"), S("bitx5"), S("bit5")
    im = LAB.copy(); d = ImageDraw.Draw(im)
    belt = ease((t - n3 - .5) / .8)
    apps = [("Claude Code", 330, 250), ("Claude Desktop", 960, 140), ("Any MCP app", 1590, 250)]
    for i, (name, x, y) in enumerate(apps):
        t0 = n3 + 2.0 + i * .7
        if t >= t0:
            k = ease((t - t0) / .4); card(d, (x - 220, y - 60, x + 220, y + 60), None, CY, (18, 20, 32), k)
            d.text((x, y), name, font=FI(40, "InterDisplay-Bold"), fill=fade(WH, k), anchor="mm")
            arrow(d, 960, 560, x, y + 70, fade(CY, k * .7), 4)
    paste_bit(im, f, "happy" if t > n3 + 1.5 else "norm", 960, 1010, 0.9, belt=belt, t=t)
    if n5a <= t < b5a: caption(im, "MCP = Model Context Protocol: one standard plug for AI tools", n5a + .2, t, 1040, CY, 36)
    if b5a <= t < b5: caption(im, "Before: one script.  Now: anywhere Claude runs.", b5a + .2, t, 1040, WH, 36)
    if t >= b5:
        k = ease((t - b5) / .4); card(d, (1240, 640, 1880, 760), None, GR, (12, 22, 18), k)
        cmd = "$ claude mcp add requirements-checker"
        d.text((1270, 700), cmd[:int((t - b5) * 30)], font=FD(28, "DejaVuSansMono-Bold"), fill=fade(GR, k), anchor="lm")
    return im

def sc6(f, t):
    b6, b7, v6a, b6a, n6a, v3 = S("bit6"), S("bit7"), S("vaguex2"), S("bitx6"), S("narratorx3"), S("vague3")
    im = LAB.copy(); d = ImageDraw.Draw(im)
    scroll = min(1, max(0, (t - b6) / 12)); crop_h = 600
    y0 = int((RUN.height - crop_h) * scroll * 0.9)
    panel = RUN.crop((0, y0, 1000, y0 + crop_h))
    card(d, (80, 90, 1100, 720), "the run", CY); im.alpha_composite(panel, (90, 115)); d = ImageDraw.Draw(im)
    calls = int(min(9, max(0, (t - b6) / .3)))
    d.text((1180, 140), f"TOOL CALLS  {calls}", font=FD(48, "DejaVuSansMono-Bold"), fill=PK, anchor="lm")
    if t > b6 + 2.6:
        d.text((1180, 220), "2 PASS", font=FI(64), fill=GR, anchor="lm"); d.text((1440, 220), "6 FLAGGED", font=FI(64), fill=RD, anchor="lm")
    if t >= b7:
        k = ease((t - b7) / .5)
        card(d, (1160, 290, 1880, 490), None, CY, (14, 26, 34), k, 30, 5)
        d.text((1200, 330), "REQ-002", font=FD(30, "DejaVuSansMono-Bold"), fill=fade(CY, k))
        d.text((1200, 378), "\"shall be fast\"  →", font=FD(32), fill=fade(GRY, k))
        d.text((1200, 428), "within 200 ms  [ASSUMED]", font=FD(38), fill=fade(WH, k))
    if v6a <= t < b6a:
        caption(im, "\"Battery life shall be adequate for typical missions!\"", v6a + .2, t, 980, (200, 196, 230), 38)
    if t >= b6a:
        k = ease((t - b6a) / .5)
        card(d, (1160, 510, 1660, 710), None, CY, (14, 26, 34), k, 30, 5)
        d.text((1200, 550), "REQ-005", font=FD(30, "DejaVuSansMono-Bold"), fill=fade(CY, k))
        d.text((1200, 598), "\"adequate\"  →", font=FD(32), fill=fade(GRY, k))
        d.text((1200, 648), "12 h at 25 °C [ASSUMED]", font=FD(32), fill=fade(WH, k))
    if t >= n6a:
        k = ease((t - n6a) / 1.0)
        mini = CITY[int(round((1 - k) * 10))].crop((0, 380, W, 960)).resize((960, 290))
        card(d, (120, 760, 1100, 1060), None, CY, (8, 10, 22), k); im.alpha_composite(mini, (130, 765)); d = ImageDraw.Draw(im)
    if t >= v6a:
        k = ease((t - v6a) / .4)
        if t < b6a: x, sc = 1560, 0.55
        else:
            m = ease((t - b6a) / .6); x, sc = 1560 + 230 * m, 0.55 - 0.15 * m
        if t >= v3: sc -= 0.1 * ease((t - v3) / 2.0)
        paste_prof(im, f, t + (random.random() * .1 if t >= v3 else 0), x, 1080, sc, "angry" if t >= b6a else "smug", k)
    paste_bit(im, f, "determined", 1300 if t < n6a else 1290, 1060, 0.5, t=t)
    return im

def sc7(f, t):
    n4, v4, b7a, v7a, b8 = S("narrator4"), S("vague4"), S("bitx7"), S("vaguex3"), S("bit8")
    im = LAB.copy(); d = ImageDraw.Draw(im)
    card(d, (120, 110, 1000, 300), "RULE", YL)
    d.text((160, 220), "contains a number  →  measurable ✓", font=FD(36, "DejaVuSansMono-Bold"), fill=WH)
    if t < v4:
        k = ease((t - n4 - 1.0) / 2.0); im.alpha_composite(FOGS[1], (int(-200 + 500 * k), -150))
        paste_prof(im, f, t, 1500, 1080, 0.7, "smug", ease((t - n4) / .8))
        return im
    card(d, (120, 360, 1160, 660), "REQ-004", CY)
    d.text((160, 450), "The logger shall store at least", font=FD(34), fill=WH)
    d.text((160, 500), "72 hours of data", font=FD(34), fill=GR)
    d.text((520, 500), "and shall encrypt it", font=FD(34), fill=RD if t > b7a else WH)
    d.text((160, 560), "and shall upload it daily.", font=FD(34), fill=WH)
    if v7a <= t < b8:
        k = ease((t - v7a - 1.5) / .5)
        for (x1, x2, y) in ((160, 500, 590), (520, 890, 540), (160, 590, 600)):
            pass
        d.line((160, 535, 490, 535), fill=fade(YL, k), width=5); d.line((520, 535, 880, 535), fill=fade(YL, k), width=5); d.line((160, 595, 600, 595), fill=fade(YL, k), width=5)
    if t < b8:
        paste_prof(im, f, t, 1580, 1080, 0.66, "smug")
        paste_bit(im, f, "shock" if t >= b7a and t < v7a else "determined", 560, 1060, 0.55, t=t)
        if t >= v7a: caption(im, "One number... covering three promises.", v7a + 1.0, t, 330, (200, 196, 230), 36)
        return im
    paste_bit(im, f, "happy" if t > b8 + 5.0 else "determined", 560, 1060, 0.55, t=t)
    if t < b8 + 2.0:
        k = ease((t - b8) / .4); spark(im, 1500, 420, t, k); d = ImageDraw.Draw(im)
        card(d, (1180, 560, 1890, 660), None, OR, (34, 18, 12), k)
        d.text((1535, 610), "\"shall encrypt it\": nothing to measure", font=FD(28), fill=fade((255, 200, 170), k), anchor="mm")
    else:
        fixes = [("✓ check each 'shall' clause on its own", GR, b8 + 2.0), ("✗ 'daily' flagged by mistake", RD, b8 + 3.3), ("✓ frequency words count as measurable", GR, b8 + 4.5)]
        card(d, (1200, 300, 1890, 640), "fix", GR)
        for i, (s_, c, ts) in enumerate(fixes):
            if t >= ts: d.text((1225, 380 + i * 60), s_, font=FD(26), fill=c)
        if t >= b8 + 5.5:
            d.text((1545, 590), "pushed  ·  commit 6042ef7", font=FD(32, "DejaVuSansMono-Bold"), fill=GR, anchor="mm")
    return im

def sc8(f, t):
    b9 = S("bit9")
    im = city_scene(t, 1 - ease((t - b9 + .5) / 2.0)); d = ImageDraw.Draw(im)
    paste_bit(im, f, "happy", 960, 1060, 0.85, t=t)
    L = EV["bit9"][1]
    for i, (s_, ts) in enumerate((("Rules hide assumptions.", b9 + .3), ("AI proposes. The engineer decides.", b9 + L * .5))):
        if t >= ts:
            k = ease((t - ts) / .4); y = 170 + i * 135
            w = d.textlength(s_, font=FI(60, "InterDisplay-Bold"))
            card(d, (W / 2 - w / 2 - 40, y - 50, W / 2 + w / 2 + 40, y + 50), None, CY, (10, 14, 28), k, 50)
            d.text((W / 2, y), s_, font=FI(60, "InterDisplay-Bold"), fill=fade(WH, k), anchor="mm")
    return im

def sc9(f, t):
    v5, b10 = S("vague5"), S("bit10")
    im = city_scene(t, 0); d = ImageDraw.Draw(im)
    dk = 0.6 + 0.4 * abs(math.sin(t * 2))
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(gl); gd.rectangle((1500, 380, 1760, 940), fill=PK + (int(120 * dk),)); im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(30)))
    d = ImageDraw.Draw(im); d.rectangle((1520, 400, 1740, 940), fill=(20, 8, 26), outline=PK, width=6); d.text((1630, 360), "AGENTS", font=FI(56), fill=PK, anchor="mm")
    if t < b10:
        k = ease((t - v5) / 4.5); paste_prof(im, f, t, 900 + 600 * k, 1060, 0.7 - 0.35 * k, "smug", 1 - .7 * k)
    else:
        paste_bit(im, f, "determined", 760, 1060, 0.95, t=t)
        if t > b10 + 3.0:
            caption(im, "Build it. Test it. Ship it.", b10 + 3.0, t, 160, CY, 56)
    return im

def sc_end(f, t):
    im = SKY.copy(); im.alpha_composite(CITYG[0]); im.alpha_composite(CITY[0])
    im.alpha_composite(Image.new("RGBA", (W, H), (6, 6, 14, 200))); d = ImageDraw.Draw(im)
    k = ease((t - END_T) / .6)
    d.text((W / 2, 260), "THE ADVENTURES OF BIT", font=FI(110), fill=fade(PK, k), anchor="mm")
    d.text((W / 2, 400), "Episode 2 coming soon", font=FI(64, "InterDisplay-Bold"), fill=fade(WH, k), anchor="mm")
    d.text((W / 2, 500), "Subscribe so you don't miss Bit's next mission", font=FD(40), fill=fade(GRY, k), anchor="mm")
    d.text((W / 2, 590), "@vibewithamitai  ·  vibewithamit.com", font=FD(44), fill=fade(CY, k), anchor="mm")
    paste_bit(im, f, "happy", W / 2, 1060, 0.55, t=t)
    return im

SC = [sc1, sc2, sc3, sc4, sc5, sc6, sc7, sc8, sc9]
def frame(f):
    t = f / FPS
    if t < INTRO: return sc_intro(f, t)
    if t >= END_T: return sc_end(f, t)
    i = scene_of(t); im = SC[i](f, t)
    s0 = scene_t[i][0]
    if i > 0 and t < s0 + 0.35:
        prev = SC[i - 1](f, s0 - 0.01); im = Image.blend(prev, im, (t - s0) / 0.35)
    return im

# ---------------------------------------------------------------- music + mix
tt = np.arange(int(DUR * SR)) / SR
mus = np.zeros_like(tt, dtype=np.float32)
drone = (np.sin(2 * np.pi * 55 * tt) + .5 * np.sin(2 * np.pi * 82.4 * tt)) * .05
mus += drone
for b in np.arange(0, DUR, 0.5):
    i = int(b * SR); n = int(.35 * SR); fr = [440, 523.25, 659.25, 523.25][int(b * 2) % 4]
    s_ = np.sin(2 * np.pi * fr * tt[:n]) * np.exp(-tt[:n] * 7) * .025; mus[i:i + n] += s_[:len(mus) - i]
noise = rng.standard_normal(len(tt)).astype(np.float32)
def hit(t0, amp=.5):
    i = int(t0 * SR); n = int(2 * SR); s_ = np.sin(2 * np.pi * 45 * tt[:n]) * np.exp(-tt[:n] * 3) * amp + noise[:n] * np.exp(-tt[:n] * 10) * amp * .4
    mus[i:i + n] += s_[:len(mus) - i]
def zap(t0, amp=.2):
    i = int(t0 * SR); n = int(.2 * SR); mus[i:i + n] += noise[:n] * amp * np.exp(-np.arange(n) / SR * 15)
def ding(t0, fr=880, amp=.12):
    i = int(t0 * SR); n = int(.5 * SR); s_ = np.sin(2 * np.pi * fr * tt[:n]) * np.exp(-tt[:n] * 6) * amp; mus[i:i + n] += s_[:len(mus) - i]
hit(0.3); hit(S("vague1"), .4); zap(S("vague1") + .2); zap(S("vague2")); hit(S("bit1"), .3)
for i_ in range(9): ding(S("bit6") + i_ * .3, 1400, .06)
ding(S("bit7"), 1320); zap(S("vague3"), .3); zap(S("bitx7"), .25); zap(S("vaguex1"), .2); zap(S("vaguex2"), .2); ding(S("bitx6"), 1320); ding(S("bit8"), 1000); ding(S("bit8") + 5.5, 880); ding(S("bit8") + 5.6, 1320)
hit(END_T, .4)
voice = track["bit"] + track["narrator"] + track["vague"]
mix = mus.copy(); L = min(len(mix), len(voice)); mix[:L] += voice[:L]
mix = np.clip(mix / max(1, np.abs(mix).max() / .95), -1, 1)
with wave.open("ep1_audio.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "stills":
        for k_, tt_ in enumerate([2.5] + [ (a + b) / 2 for a, b in scene_t] + [END_T + 3]):
            frame(int(tt_ * FPS)).convert("RGB").resize((960, 540)).save(f"still_{k_:02d}.png")
        print("scenes", [(round(a, 1), round(b, 1)) for a, b in scene_t], "dur", round(DUR, 1)); sys.exit()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", "ep1_audio.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                           "-shortest", "adventures-of-bit-ep1-the-vague-one.mp4"], stdin=subprocess.PIPE)
    for f in range(N):
        ff.stdin.write(frame(f).convert("RGB").tobytes())
        if f % 900 == 0: print(f, "/", N, flush=True)
    ff.stdin.close(); ff.wait(); print("done", DUR)
