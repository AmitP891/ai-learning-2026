"""House-style rebuilds (real 3D-printed Bit, code background, big stacked text) for:
  - Grok vs Claude Fable 5.2 long-form  -> content/thumbnails/2026-11-15-grok-vs-fable-v2.jpg
  - How I Make Faceless YouTube Videos  -> content/thumbnails/2026-11-14-faceless-v2.jpg
Same recipe as 'IT REVIEWED ME' v3 (vidIQ thumbnail score 94)."""
import os, sys
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
from build_boss_v3 import background, glow, rim, drop_shadow, grade_photo, light_eyes, F, W, H, PK, CY, WH  # noqa: E402
YL = (255, 214, 0); INK = (10, 10, 16); BLUE = (70, 160, 255); ORANGE = (255, 140, 50); RED = (255, 60, 80)

def fit(d, s, size, maxw):
    while d.textlength(s, font=F(size)) > maxw: size -= 4
    return F(size)

def bit(im, hgt=900, right=70):
    p = Image.open(os.path.join(ROOT, "brand/photos/bit_real_cutout.png")).convert("RGBA")
    p = light_eyes(grade_photo(p)); s = hgt / p.height; p = p.resize((round(p.width * s), hgt), Image.LANCZOS)
    x, y = W - p.width - right, 30; drop_shadow(im, p, (x, y)); im.alpha_composite(p, (x, y)); im.alpha_composite(rim(p, CY, 9, 170), (x, y)); return x

def stack(im, x_limit, lines, ty=50):
    d = ImageDraw.Draw(im); maxw = x_limit - 70
    for txt, col, size, glow_on in lines:
        f = fit(d, txt, size, maxw)
        if glow_on:
            g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).text((52, ty), txt, font=f, fill=col + (255,)); im.alpha_composite(g.filter(ImageFilter.GaussianBlur(16))); d = ImageDraw.Draw(im)
        d.text((52, ty), txt, font=f, fill=col, stroke_width=8, stroke_fill=INK); ty += int(f.size * 0.92)
    return ty

def grok_vs_fable():
    im = background(seed=11, words=["make", "me", "a", "3D", "game", "zap(bug)", "cpu.lives", "boss", "ship()", "test()", "__game", "clearLevel()", "index.html", "three.js", "9:00", "17:00"])
    glow(im, (620, 20, 1320, 760), PK, 120, 120); glow(im, (0, 0, 640, 720), BLUE, 40, 140)
    x = bit(im)
    ty = stack(im, x, [("GROK", BLUE, 200, False), ("vs", WH, 90, False), ("FABLE", ORANGE, 200, True)], 30)
    d = ImageDraw.Draw(im); s = "ONE CHEATED"; f = F(64); w = d.textlength(s, font=f) + 60
    d.rounded_rectangle((52, ty + 46, 52 + w, ty + 142), 22, fill=RED, outline=INK, width=6); d.text((52 + w / 2, ty + 94), s, font=f, fill=WH, anchor="mm", stroke_width=3, stroke_fill=INK)
    out = os.path.join(ROOT, "content/thumbnails/2026-11-15-grok-vs-fable-v2.jpg"); im.convert("RGB").save(out, quality=92); print(out)

def faceless():
    im = background(seed=5, words=["ffmpeg", "-i", "bit.svg", "render()", "frames", "voice.mp3", "lip_sync()", "python3", "build.py", "no_camera", "no_editor", "30fps", "mouth.open", "claude", "code"])
    glow(im, (620, 20, 1320, 760), PK, 120, 120); glow(im, (900, 440, 1300, 760), CY, 60, 90)
    x = bit(im)
    stack(im, x, [("NO FACE.", WH, 150, False), ("NO EDITOR.", WH, 150, False), ("100%", YL, 200, True), ("CODE", YL, 200, True)], 40)
    out = os.path.join(ROOT, "content/thumbnails/2026-11-14-faceless-v2.jpg"); im.convert("RGB").save(out, quality=92); print(out)

if __name__ == "__main__":
    grok_vs_fable(); faceless()
