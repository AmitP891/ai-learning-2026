"""Grok vs Fable thumbnail, painted-Bit version (for YouTube Test & Compare against v2).
Output: content/thumbnails/2026-11-15-grok-vs-fable-v3-painted.jpg"""
import os, sys
from PIL import Image, ImageDraw, ImageEnhance
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
import build_house_v2_pair as v2  # noqa: E402
from build_boss_v3 import background, glow, rim, drop_shadow, grade_photo, F, W, H, PK, CY, WH  # noqa: E402

def bit_painted(im, hgt=900, right=70):
    p = Image.open(os.path.join(ROOT, "brand/photos/bit_painted_mockup.png")).convert("RGBA"); a = p.getchannel("A")
    p = ImageEnhance.Contrast(ImageEnhance.Color(p.convert("RGB")).enhance(1.3)).enhance(1.12).convert("RGBA"); p.putalpha(a)
    s = hgt / p.height; p = p.resize((round(p.width * s), hgt), Image.LANCZOS)
    x, y = W - p.width - right, 30; drop_shadow(im, p, (x, y)); im.alpha_composite(p, (x, y)); im.alpha_composite(rim(p, CY, 9, 170), (x, y)); return x

v2.bit = bit_painted
im = background(seed=11, words=["make", "me", "a", "3D", "game", "zap(bug)", "cpu.lives", "boss", "ship()", "test()", "__game", "clearLevel()", "index.html", "three.js", "9:00", "17:00"])
glow(im, (620, 20, 1320, 760), PK, 120, 120); glow(im, (0, 0, 640, 720), v2.BLUE, 40, 140)
x = bit_painted(im)
ty = v2.stack(im, x, [("GROK", v2.BLUE, 200, False), ("vs", WH, 90, False), ("FABLE", v2.ORANGE, 200, True)], 30)
d = ImageDraw.Draw(im); s = "ONE CHEATED"; f = F(64); w = d.textlength(s, font=f) + 60
d.rounded_rectangle((52, ty + 46, 52 + w, ty + 142), 22, fill=v2.RED, outline=v2.INK, width=6); d.text((52 + w / 2, ty + 94), s, font=f, fill=WH, anchor="mm", stroke_width=3, stroke_fill=v2.INK)
out = os.path.join(ROOT, "content/thumbnails/2026-11-15-grok-vs-fable-v3-painted.jpg"); im.convert("RGB").save(out, quality=92); print(out)
