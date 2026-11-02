"""'Who's that?' teaser: Specs arrives and inspects Bit's requirement. 1080x1920, 30 fps, ~15 s, no voiceover."""
import re, io, sys, math, wave, subprocess, numpy as np, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1080, 1920; FPS = 30; SR = 44100; DUR = 15.5; N = int(DUR * FPS)
REPO = "/home/claude/ai-learning-2026"
CY = (0, 240, 255); PK = (240, 53, 158); GR = (57, 255, 136); RD = (255, 70, 90); WH = (255, 255, 255); GY = (160, 165, 185); BG = (13, 13, 20); YL = (255, 214, 0); PANEL = (20, 22, 34)
FD = lambda s, w="DejaVuSans-Bold": ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{w}.ttf", s)
FI = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", s)
FB = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", s)
MB = lambda s: FD(s, "DejaVuSansMono-Bold")
def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def eio(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
def fade(c, k): return tuple(int(BG[i] + (c[i] - BG[i]) * k) for i in range(3))
def png(s, w, h): return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=s.encode(), output_width=w, output_height=h))).convert("RGBA")

# --- Bit
SVG = open(f"{REPO}/brand/bit/bit.svg").read()
svg = re.sub(r'<g id="eyes">.*?</g>', '', SVG, flags=re.S); svg = re.sub(r'<path id="mouth"[^>]*/>', '', svg)
BASE = png(svg, 600, 700)
def bitimg(f, mood):
    r = BASE.copy(); d = ImageDraw.Draw(r)
    for ex in (244, 356):
        cx, cy = ex, 199
        if mood == "happy": d.arc((cx - 24, cy - 14, cx + 24, cy + 30), 200, 340, fill=CY, width=10)
        elif mood == "shock": d.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), outline=CY, width=9)
        elif mood == "look": d.rounded_rectangle((cx - 4, cy - 29, cx + 36, cy + 29), radius=12, fill=CY)
        elif (f % 95) in (0, 1, 2): d.rounded_rectangle((cx - 22, cy - 4, cx + 22, cy + 4), radius=3, fill=CY)
        else: d.rounded_rectangle((cx - 22, cy - 29, cx + 22, cy + 29), radius=12, fill=CY)
    if mood == "shock": d.ellipse((278, 240, 322, 284), outline=CY, width=8)
    else: d.arc((260, 222, 340, 274), 25, 155, fill=CY, width=9)
    return r

# --- Specs (from brand/specs, with spinning rotors)
O = '#0B0C14'; PKh = '#F0359E'; CYh = '#00F0FF'; DK = '#171A2B'; GYh = '#3A3F5C'; YLh = '#FFD600'; YD = '#D9A800'; GRh = '#39FF88'; RDh = '#FF465A'
S = 'stroke="%s" stroke-width="6" stroke-linejoin="round"' % O
def specs_svg(mood, rx):
    if mood == "squint":
        le = f'<rect x="146" y="186" width="34" height="12" rx="6" fill="{CYh}"/>'; re_ = f'<rect x="222" y="184" width="40" height="14" rx="7" fill="{CYh}"/>'
        brow = f'<line x1="140" y1="170" x2="184" y2="180" stroke="{CYh}" stroke-width="7" stroke-linecap="round"/>'
    elif mood == "alarm":
        le = f'<circle cx="163" cy="190" r="17" fill="none" stroke="{CYh}" stroke-width="7"/>'; re_ = f'<circle cx="242" cy="190" r="22" fill="none" stroke="{CYh}" stroke-width="8"/>'; brow = ''
    else:
        le = f'<rect x="150" y="168" width="28" height="44" rx="10" fill="{CYh}"/>'; re_ = f'<rect x="226" y="164" width="32" height="52" rx="12" fill="{CYh}"/><circle cx="248" cy="174" r="6" fill="#fff"/>'; brow = ''
    panel = {"idle": f'<text x="200" y="335" text-anchor="middle" font-family="DejaVu Sans Mono" font-weight="bold" font-size="28" fill="{GYh}">✓ ✗</text>',
             "squint": f'<text x="200" y="335" text-anchor="middle" font-family="DejaVu Sans Mono" font-weight="bold" font-size="30" fill="{YLh}">? ?</text>',
             "alarm": f'<path d="M185 307 l30 30 M215 307 l-30 30" stroke="{RDh}" stroke-width="8" stroke-linecap="round"/>'}[mood]
    ring = RDh if mood == "alarm" else YLh
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 420">
<line x1="120" y1="140" x2="60" y2="90" stroke="{GYh}" stroke-width="14" stroke-linecap="round"/><line x1="280" y1="140" x2="340" y2="90" stroke="{GYh}" stroke-width="14" stroke-linecap="round"/>
<ellipse cx="60" cy="80" rx="{rx}" ry="12" fill="{CYh}" {S}/><ellipse cx="340" cy="80" rx="{rx}" ry="12" fill="{CYh}" {S}/>
<circle cx="60" cy="90" r="10" fill="{GYh}" {S}/><circle cx="340" cy="90" r="10" fill="{GYh}" {S}/>
<line x1="200" y1="120" x2="200" y2="96" stroke="{GYh}" stroke-width="8" stroke-linecap="round"/><circle cx="200" cy="88" r="11" fill="{PKh}" {S}/>
<rect x="100" y="120" width="200" height="170" rx="40" fill="{YLh}" {S}/>
<path d="M106 240 Q200 280 294 240 L294 250 Q294 290 254 290 L146 290 Q106 290 106 250 Z" fill="{YD}"/>
<rect x="100" y="120" width="200" height="170" rx="40" fill="none" {S}/>
<rect x="124" y="140" width="152" height="104" rx="24" fill="{DK}" {S}/>
{le}{re_}{brow}
<line x1="276" y1="222" x2="318" y2="262" stroke="{O}" stroke-width="20" stroke-linecap="round"/><line x1="276" y1="222" x2="318" y2="262" stroke="{ring}" stroke-width="10" stroke-linecap="round"/>
<circle cx="242" cy="190" r="44" fill="none" stroke="{O}" stroke-width="18"/><circle cx="242" cy="190" r="44" fill="none" stroke="{ring}" stroke-width="9"/>
<line x1="140" y1="290" x2="130" y2="320" stroke="{GYh}" stroke-width="8" stroke-linecap="round"/><line x1="260" y1="290" x2="270" y2="320" stroke="{GYh}" stroke-width="8" stroke-linecap="round"/>
<rect x="150" y="300" width="100" height="50" rx="14" fill="{DK}" {S}/>
{panel}
</svg>'''
SPEC = {(m, r): png(specs_svg(m, r), 440, 462) for m in ("idle", "squint", "alarm") for r in (52, 30, 10)}
def specs(f, mood): return SPEC[(mood, (52, 30, 10)[f % 3])]

grid = Image.new("RGBA", (W, H), BG + (255,)); gd = ImageDraw.Draw(grid)
for y in range(0, H, 60): gd.line((0, y, W, y), fill=(20, 21, 32))
def req_card(state):
    c = Image.new("RGBA", (720, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    col = {"ok": GR, "check": YL, "bad": RD}[state]
    d.rounded_rectangle((0, 0, 719, 299), radius=24, fill=PANEL, outline=col, width=6)
    d.rectangle((30, 28, 190, 70), fill=PK); d.text((110, 49), "REQ-001", font=MB(28), fill=WH, anchor="mm")
    d.text((40, 110), "The system shall", font=FI(58), fill=WH); d.text((40, 180), "be fast.", font=FI(58), fill=WH)
    st = {"ok": "✓ DONE", "check": "CHECKING…", "bad": "✗ UNTESTABLE"}[state]
    d.text((690, 49), st, font=MB(30), fill=col, anchor="rm")
    return c

# --- audio: rotor buzz + R2-style chirps + alarm + sting
tt = np.arange(int(DUR * SR)) / SR; a = np.zeros_like(tt, dtype=np.float32)
rng = np.random.default_rng(3); noise = rng.standard_normal(len(tt)).astype(np.float32)
def chirp(t0, f0, f1, d=.12, amp=.12):
    i = int(t0 * SR); n = int(d * SR); x = np.arange(n) / SR; fr = np.linspace(f0, f1, n)
    s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-x * 6) * amp; a[i:i + n] += s[:len(a) - i]
def tone(t0, fr, d=.15, dec=20, amp=.1):
    i = int(t0 * SR); n = int(d * SR); s = np.sin(2 * np.pi * fr * tt[:n]) * np.exp(-tt[:n] * dec) * amp; a[i:i + n] += s[:len(a) - i]
# rotor buzz: 3.0 -> 11.0, fades in/out, pans in loudness
b0, b1 = int(2.6 * SR), int(11.2 * SR); x = tt[b0:b1]
buzz = (np.sign(np.sin(2 * np.pi * 118 * x)) * .5 + np.sin(2 * np.pi * 236 * x) * .3) * (0.6 + .4 * np.sin(2 * np.pi * 21 * x))
envb = np.clip((x - 2.6) / 1.2, 0, 1) * np.clip((11.2 - x) / .8, 0, 1) * (0.4 + 0.6 * np.clip((x - 2.6) / 2.0, 0, 1))
a[b0:b1] += (buzz * envb * .035).astype(np.float32)
tone(.3, 660, .2, 10, .1); tone(.42, 990, .3, 8, .1)            # Bit "done" ding
chirp(4.3, 900, 1800); chirp(4.5, 1800, 1100)                    # hello?
for k in range(3): chirp(6.6 + k * .22, 700, 1300 + k * 200, .1, .1)  # inspecting
chirp(7.8, 1400, 600, .25, .12); chirp(8.15, 600, 1500, .2, .12)  # "? ?"
for k in range(6): tone(9.3 + k * .18, 1500 if k % 2 == 0 else 1100, .12, 12, .12)  # alarm
a[int(9.3 * SR):int(9.6 * SR)] += noise[:int(.3 * SR)] * np.exp(-np.arange(int(.3 * SR)) / SR * 14) * .15
for k, fr in enumerate((220, 277, 330, 440)): tone(11.3 + k * .12, fr, .9, 3, .09)  # sting
tone(14.2, 660, .3, 6, .1); tone(14.32, 990, .45, 6, .1)
with wave.open("audio.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())

PREVIEW = [float(v) for v in sys.argv[1:]]
OUT = "specs-teaser.mp4"
ff = None if PREVIEW else subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "audio.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], stdin=subprocess.PIPE)
def cap(d, s, col, t, t0, y=1700):
    if t < t0: return
    k = ease((t - t0) / .25); d.text((W / 2, y + 20 * (1 - k)), s, font=FI(64), fill=fade(col, k), anchor="ma", stroke_width=6, stroke_fill=(0, 0, 0))
for f in ([int(p * FPS) for p in PREVIEW] if PREVIEW else range(N)):
    t = f / FPS; im = grid.copy(); d = ImageDraw.Draw(im)
    if t < 11.0:
        d.text((60, 80), "// the adventures of bit", font=MB(30), fill=CY)
        state = "ok" if t < 6.3 else ("check" if t < 9.2 else "bad")
        shake = int(10 * math.sin(t * 80) * max(0, 1 - (t - 9.3) / .5)) if t > 9.3 else 0
        im.alpha_composite(req_card(state), (180 + shake, 300)); d = ImageDraw.Draw(im)
        mood = "happy" if t < 3.2 else ("look" if t < 9.3 else "shock")
        b = bitimg(f, mood).resize((420, 490), Image.LANCZOS); im.alpha_composite(b, (90, 1150 + int(8 * math.sin(t * 3.8))))
        # Specs flight path
        if t >= 3.6:
            k = eio((t - 3.6) / 2.2); x = int(1250 + (640 - 1250) * k); y = int(-450 + (780 - (-450)) * k)
            if t > 6.3: x, y = 640 - int(40 * eio((t - 6.3) / .6)), 780 - int(90 * eio((t - 6.3) / .6))   # lean in to the card
            if t > 9.3: x, y = x + int(40 * eio((t - 9.3) / .3)), y + int(30 * eio((t - 9.3) / .3))      # recoil
            y += int(14 * math.sin(t * 5))
            mood_s = "idle" if t < 7.6 else ("squint" if t < 9.3 else "alarm")
            im.alpha_composite(specs(f, mood_s), (x, y)); d = ImageDraw.Draw(im)
            if 6.6 < t < 9.3:  # magnified "fast."
                k2 = ease((t - 6.6) / .4); r = int(120 * k2)
                d.rounded_rectangle((292, 498, 440, 570), radius=12, outline=YL, width=6)
                d.line((366, 570, 330, 800 - r), fill=YL, width=5)
                d.ellipse((330 - r, 800 - r, 330 + r, 800 + r), fill=PANEL, outline=YL, width=8)
                if k2 > .6: d.text((330, 800), "fast?", font=FI(int(70 * k2)), fill=YL, anchor="mm")
        if 2.6 < t < 3.6:  # shadow passes
            k = (t - 2.6) / 1.0; sh = Image.new("RGBA", (W, H)); ImageDraw.Draw(sh).ellipse((int(-300 + 1600 * k), 900, int(100 + 1600 * k), 1050), fill=(0, 0, 0, 120)); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(30))); d = ImageDraw.Draw(im)
        cap(d, "Done! ✓", GR, t, 0.3) if t < 2.6 else None
        cap(d, "…what's that noise?", WH, t, 2.8) if 2.8 <= t < 4.3 else None
        cap(d, "[beep boop?]", YL, t, 4.3) if 4.3 <= t < 6.6 else None
        cap(d, "[zooms in]", YL, t, 6.6) if 6.6 <= t < 7.8 else None
        cap(d, "[beep… beep?]", YL, t, 7.8) if 7.8 <= t < 9.3 else None
        if t >= 9.3: cap(d, "\"FAST?! THAT'S UNTESTABLE!\"", RD, t, 9.3)
        if t >= 9.3 and int(t * 6) % 2 == 0:
            ov = Image.new("RGBA", (W, H), (255, 70, 90, 28)); im.alpha_composite(ov); d = ImageDraw.Draw(im)
    else:
        k = ease((t - 11.0) / .4)
        im.alpha_composite(specs(f, "squint").resize((560, 588), Image.LANCZOS), (260, 520 + int(14 * math.sin(t * 5)))); d = ImageDraw.Draw(im)
        d.text((W / 2, 260 + 30 * (1 - k)), "WHO'S THAT?", font=FI(130), fill=fade(WH, k), anchor="mm")
        if t > 12.0:
            k2 = ease((t - 12.0) / .35)
            d.text((W / 2, 1230), "SPECS", font=FI(150), fill=fade(YL, k2), anchor="mm")
            d.text((W / 2, 1340), "the reviewer drone joins the team", font=FB(44), fill=fade(WH, k2), anchor="mm")
        if t > 13.0:
            k3 = ease((t - 13.0) / .35)
            d.rounded_rectangle((140, 1440, 940, 1600), radius=24, fill=fade(PANEL, k3), outline=fade(PK, k3), width=5)
            d.text((W / 2, 1490), "THE ADVENTURES OF BIT", font=FI(50), fill=fade(WH, k3), anchor="mm")
            d.text((W / 2, 1555), "Episode 2 · 26 Dec", font=FB(44), fill=fade(PK, k3), anchor="mm")
            d.text((W / 2, 1680), "@vibewithamitai", font=FB(44), fill=fade(CY, k3), anchor="mm")
    if PREVIEW: im.convert("RGB").save(f"tz_{t:.1f}.png")
    else: ff.stdin.write(im.convert("RGB").tobytes())
if ff: ff.stdin.close(); ff.wait()
print("done", DUR)
