"""YouTube banner v2 (15 Nov 2026): states the channel promise for new viewers.
Output: brand/banners/youtube-banner-v2-2560x1440.png
Everything important sits inside the 1546x423 safe area (x 507-2053, y 508-931)
that shows on every device; the rest only shows on TV."""
import os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "brand/thumbnails"))
import build_boss_v3 as b  # noqa: E402

W, H = 2560, 1440
b.W, b.H = W, H  # helpers read module-level size
SX0, SY0, SX1, SY1 = 507, 508, 2053, 931
PK, CY, WH, F = b.PK, b.CY, b.WH, b.F
YL = (255, 214, 0); GR = (60, 230, 130); MUTE = (150, 158, 190); INK = (10, 10, 16)

im = b.background(seed=21, words=["make", "me", "a", "game", "bit.zap()", "boss.hp", "level++", "index.html",
                                  "three.js", "claude", "ship()", "test()", "score", "lives", "play()"])
b.glow(im, (SX0 - 80, SY0 - 120, SX0 + 560, SY1 + 120), PK, 110, 140)
b.glow(im, (SX0 + 600, SY0, SX1, SY1), CY, 28, 180)

# real 3D-printed Bit, left side of the safe area
# painted-collectible look (option E, 15 Nov): made by brand/bit/lab/physical_mockups.py
p = Image.open(os.path.join(ROOT, "brand/photos/bit_painted_mockup.png")).convert("RGBA"); hgt = 420; s = hgt / p.height
p = p.resize((round(p.width * s), hgt), Image.LANCZOS)
rimp = b.rim(p, CY, 9, 170)
# the photo is cropped through the base: fade the bottom so no hard edge shows
fade = Image.linear_gradient("L").resize((p.width, hgt)).point(lambda v: 255 if v < 190 else max(0, 255 - (v - 190) * 4))
for spr in (p, rimp):
    spr.putalpha(Image.composite(spr.getchannel("A"), Image.new("L", spr.size, 0), fade))
bx, by = SX0 + 10, SY0 + 8
b.drop_shadow(im, p, (bx, by)); im.alpha_composite(p, (bx, by)); im.alpha_composite(rimp, (bx, by))

d = ImageDraw.Draw(im)
tx = bx + p.width + 60; maxw = SX1 - tx
d.text((tx, SY0 + 22), "// VIBE WITH AMIT", font=b.MONO(40), fill=CY)

def line(y, parts, size):
    f = F(size)
    while sum(d.textlength(t, font=f) for t, _ in parts) > maxw: size -= 4; f = F(size)
    x = tx
    for t, col in parts:
        d.text((x, y), t, font=f, fill=col, stroke_width=6, stroke_fill=INK); x += d.textlength(t, font=f)
    return y + int(size * 0.98)

y = line(SY0 + 78, [("I make AI build ", WH), ("games.", YL)], 116)
y = line(y, [("Bit ", PK), ("plays them.", WH)], 116)

# series chips
cx = tx; cy = y + 26; f = b.MONO(38)
for label, col in [("Bit's Arcade", PK), ("Ask Bit", CY), ("Playable games", GR)]:
    w = d.textlength(label, font=f) + 48
    d.rounded_rectangle((cx, cy, cx + w, cy + 66), 16, outline=col, width=4, fill=(14, 14, 24))
    d.text((cx + w / 2, cy + 33), label, font=f, fill=col, anchor="mm"); cx += w + 22

# schedule line under the safe area (visible on desktop/TV)
d.text((W / 2, SY1 + 95), "New Shorts most days · Long-form every Sunday 9am", font=F(54), fill=MUTE, anchor="mm")

out = os.path.join(ROOT, "brand/banners/youtube-banner-v2-2560x1440.png")
im.convert("RGB").save(out); print(out)

