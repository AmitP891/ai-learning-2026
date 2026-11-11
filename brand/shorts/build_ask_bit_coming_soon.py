"""'Ask Bit' coming-soon teaser (1080x1920, 12 s, 30 fps): neon sign flickers on, Glitch slides in
('GLITCH ASKS.'), Bit slides in ('BIT EXPLAINS.'), the 3-part HUD drops, then 'STARTS SUNDAY'.
Usage: python3 build_ask_bit_coming_soon.py OUT.mp4"""
import os, sys, subprocess, tempfile, wave, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
W, H, FPS, DUR = 1080, 1920, 30, 12.0
N = int(FPS * DUR)
IT = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf", s)
BK = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", s)
BD = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", s)
PINK, LIME, CYAN, WHITE = (240, 53, 158), (57, 255, 136), (0, 240, 255), (255, 255, 255)
ease = lambda x: 1 - (1 - max(0, min(1, x))) ** 3                      # ease-out cubic
pop = lambda x: 0.05 if x <= 0 else (1 + 0.18 * math.sin(math.pi * min(1, x)) if x < 1 else 1)

def static_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    a = np.zeros((H, W, 3)) + np.array([8, 9, 20])
    a += np.clip(1 - np.hypot(xx - 250, yy - 1000) / 700, 0, 1)[..., None] * np.array([90, 15, 60])
    a += np.clip(1 - np.hypot(xx - 830, yy - 1000) / 700, 0, 1)[..., None] * np.array([10, 70, 35])
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for x in range(45, W, 90): d.line((x, 0, x, 1500), fill=(255, 255, 255, 10), width=2)   # acoustic panels, faint
    im.alpha_composite(ov)
    return im

def desk_layer():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((0, 1500, W, H), fill=(14, 15, 28)); d.rectangle((0, 1500, W, 1518), fill=(70, 74, 110))
    d.rectangle((0, 1560, W // 2, 1566), fill=PINK + (160,)); d.rectangle((W // 2, 1560, W, 1566), fill=LIME + (160,))   # neon strip on the desk front
    for cx, col in ((330, PINK), (750, LIME)):                          # mic on an arm + glowing ring
        arm = 1 if cx < 500 else -1
        d.line((cx + arm * 150, 1500, cx + arm * 110, 1330), fill=(40, 42, 60), width=14); d.line((cx + arm * 110, 1330, cx + arm * 40, 1360), fill=(40, 42, 60), width=12)
        d.rounded_rectangle((cx - 30, 1300, cx + 30, 1420), 28, fill=(30, 31, 44), outline=col + (200,), width=4)
        for k in range(6): d.line((cx - 18, 1322 + k * 15, cx + 18, 1322 + k * 15), fill=(70, 72, 96), width=3)
    return im

def sign(on):
    """'ASK BIT' neon sign; on = 0..1 brightness."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((170, 170, 910, 390), 40, outline=PINK + (int(70 + 160 * on),), width=6)
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).text((W // 2, 280), "ASK BIT", font=BK(170), fill=PINK + (int(255 * on),), anchor="mm")
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(26))); im.alpha_composite(g.filter(ImageFilter.GaussianBlur(8)))
    d.text((W // 2, 280), "ASK BIT", font=BK(170), fill=(255, 210, 235, int(80 + 175 * on)), anchor="mm")
    return im

def chip(text, col, y):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    w = d.textlength(text, font=BD(44)) + 56
    d.rounded_rectangle((W // 2 - w / 2, y, W // 2 + w / 2, y + 74), 37, fill=col + (255,))
    d.text((W // 2, y + 37), text, font=BD(44), fill=(10, 10, 20), anchor="mm"); return im

def big(text, col, size, y):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((W // 2, y), text, font=IT(size), fill=col, anchor="mm", stroke_width=8, stroke_fill=(8, 9, 20)); return im

def hud(n_items):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((110, 460, 970, 830), 30, fill=(10, 12, 26, 235), outline=CYAN + (255,), width=5)
    d.text((W // 2, 515), "3 SIMPLE PARTS", font=BD(46), fill=CYAN, anchor="mm")
    items = [("WHAT PEOPLE SAY", WHITE), ("WHAT WE TRIED", WHITE), ("IS IT REAL?", (255, 200, 80))]
    for i, (s, c) in enumerate(items[:n_items]):
        y = 600 + i * 78
        if i == 2:                                                       # little padlock
            d.rounded_rectangle((180, y - 8, 214, y + 22), 6, fill=c); d.arc((184, y - 30, 210, y + 4), 180, 360, fill=c, width=6)
        else:
            d.ellipse((186, y - 6, 206, y + 14), fill=PINK)
        d.text((240, y + 4), s, font=BK(54), fill=c, anchor="lm")
    return im

def scaled(layer, s, cx, cy):
    if abs(s - 1) < 1e-3: return layer
    w, h = layer.size; big_ = layer.resize((int(w * s), int(h * s)), Image.LANCZOS)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); out.alpha_composite(big_, (int(cx - cx * s), int(cy - cy * s))); return out

def glitch_slice(sprite, t, seed):
    r = random.Random(int(t * 12) + seed)
    if r.random() > 0.35: return sprite
    a = np.array(sprite); y0 = r.randint(0, a.shape[0] - 40); h = r.randint(10, 36); dx = r.choice([-1, 1]) * r.randint(6, 16)
    a[y0:y0 + h] = np.roll(a[y0:y0 + h], dx, axis=1); return Image.fromarray(a)

def music(path):
    sr = 44100; n = int(sr * DUR); t = np.arange(n) / sr; out = np.zeros(n); beat = 60 / 90
    rng = np.random.default_rng(5); noise = rng.uniform(-1, 1, n)
    def env(s, d):
        e = np.zeros(n); i0 = int(s * sr)
        if i0 < n: e[i0:] = np.exp(-np.arange(n - i0) / sr / d)
        return e
    chords = [(220, 261.6, 329.6), (174.6, 220, 261.6), (196, 246.9, 293.7), (164.8, 207.7, 246.9)]
    for k in range(int(DUR / (beat * 4)) + 1):
        for f in chords[k % 4]: out += 0.10 * np.sin(2 * np.pi * f * t) * env(k * beat * 4, 2.2) * (t >= k * beat * 4)
    for k in range(int(DUR / beat)):
        s = k * beat
        if s < 1.4: continue
        f = 55 * 2 ** (-np.clip((t - s) * 30, 0, 3))
        out += 0.6 * np.sin(2 * np.pi * np.cumsum(f) / sr) * env(s, 0.09) * (t >= s)
        out += 0.1 * noise * env(s + beat / 2, 0.02) * (t >= s + beat / 2)
    for s in (0.2, 0.5, 0.9): out += 0.3 * noise * env(s, 0.03) * (t >= s)        # neon buzz clicks
    for s in (2.0, 4.0): out += 0.25 * noise * env(s, 0.18) * np.linspace(1, 0.2, n)  # whooshes
    for i, s in enumerate((6.6, 7.2, 7.8)): out += 0.22 * np.sin(2 * np.pi * (660 + i * 220) * t) * env(s, 0.08) * (t >= s)  # pops
    out += 0.25 * np.sin(2 * np.pi * 440 * t) * env(9.2, 1.5) * (t >= 9.2)
    out = out / np.max(np.abs(out)) * 0.5
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out * 32767).astype(np.int16).tobytes())

def main(out):
    tmp = tempfile.mkdtemp(); bg = static_bg(); desk = desk_layer()
    bit = Image.open(os.path.join(ROOT, "brand/bit/bit.png")).convert("RGBA").crop((85, 20, 521, 677))
    bit = bit.resize((int(bit.width * 780 / bit.height), 780), Image.LANCZOS)
    gl = {k: Image.open(os.path.join(ROOT, f"brand/glitch/glitch_{k}.png")).convert("RGBA").crop((181, 82, 1019, 1354)) for k in ("smirk", "typing")}
    gl = {k: v.resize((int(v.width * 790 / v.height), 790), Image.LANCZOS) for k, v in gl.items()}
    signs = {round(v, 2): sign(v) for v in (0, 0.25, 0.6, 1)}
    L = {"new": chip("NEW SERIES", PINK, 420), "asks": big("GLITCH ASKS.", LIME, 120, 590), "expl": big("BIT EXPLAINS.", PINK, 120, 730),
         "h1": hud(1), "h2": hud(2), "h3": hud(3), "sun": big("STARTS SUNDAY", WHITE, 112, 590),
         "fol": ImageDraw.Draw(Image.new("RGBA", (1, 1)))}
    fol = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(fol).text((W // 2, 700), "AI & CODING, ANSWERED IN 60s", font=BD(50), fill=CYAN, anchor="mm", stroke_width=5, stroke_fill=(8, 9, 20))
    ImageDraw.Draw(fol).text((W // 2, 780), "FOLLOW SO YOU DON'T MISS IT", font=BD(46), fill=WHITE, anchor="mm", stroke_width=5, stroke_fill=(8, 9, 20))
    music(os.path.join(tmp, "m.wav"))
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", os.path.join(tmp, "m.wav"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", out], stdin=subprocess.PIPE)
    for i in range(N):
        t = i / FPS; f = bg.copy()
        # neon sign: flicker on 0.2-1.2 s, steady after, tiny buzz flicker at 8 s
        if t < 0.2: s = 0
        elif t < 1.2: s = [0.25, 0, 0.6, 0.25, 1, 0.6, 1][int((t - 0.2) * 7) % 7]
        else: s = 0.6 if 8.0 < t < 8.08 else 1
        f.alpha_composite(signs[s])
        # characters: Glitch from the right at 1.6 s, Bit from the left at 3.6 s
        gx = 520 + int(700 * (1 - ease((t - 1.6) / 0.6))); bob = int(6 * math.sin(t * 3.1))
        gs = gl["typing"] if 6.4 < t < 9 else gl["smirk"]
        if t > 1.5: f.alpha_composite(glitch_slice(gs, t, 1), (gx, 860 + bob))
        bx = 40 - int(700 * (1 - ease((t - 3.6) / 0.6))); bbob = int(6 * math.sin(t * 2.7 + 1))
        if t > 3.5: f.alpha_composite(bit, (bx, 860 + bbob))
        f.alpha_composite(desk)
        # text beats
        if 1.9 < t < 6.4: f.alpha_composite(scaled(L["asks"], pop((t - 1.9) / 0.35), W // 2, 590))
        if 3.9 < t < 6.4: f.alpha_composite(scaled(L["expl"], pop((t - 3.9) / 0.35), W // 2, 730))
        if 0.3 < t < 9.0: f.alpha_composite(L["new"])
        if 6.4 <= t < 9.0:
            n = 1 + (t >= 7.0) + (t >= 7.6); f.alpha_composite(L[f"h{n}"])
        if t >= 9.0:
            f.alpha_composite(scaled(L["sun"], pop((t - 9.0) / 0.35), W // 2, 590))
            if t >= 9.5: f.alpha_composite(fol)
        ff.stdin.write(f.convert("RGB").tobytes())
    ff.stdin.close(); ff.wait(); print(out)

if __name__ == "__main__":
    main(sys.argv[1])
