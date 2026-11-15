"""Mock-ups of physical upgrades on the real 3D-printed Bit photo (look-dev only, not final art).
  real_leds.png      : cyan LED eyes behind the visor
  real_painted.png   : painted collectible finish (dark visor, cyan face, chest screen)
  real_amoled.png    : ESP32 AMOLED screen face (true black, glowing expression)"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..", "..")
sys.path.insert(0, os.path.join(ROOT, "brand/thumbnails"))
import build_boss_v3 as b  # noqa: E402
OUT = sys.argv[1] if len(sys.argv) > 1 else HERE
CY = (0, 240, 255); PK = (240, 53, 158)
src = b.grade_photo(Image.open(os.path.join(ROOT, "brand/photos/bit_real_cutout.png")).convert("RGBA"))
w, h = src.size
VISOR = (188, 128, 732, 452); CHEST = (282, 702, 640, 930)
EYES = [(279, 189, 381, 318), (525, 189, 630, 318)]

def glow_layer(draw_fn, blur):
    lay = Image.new("RGBA", src.size, (0, 0, 0, 0)); draw_fn(ImageDraw.Draw(lay)); return lay, lay.filter(ImageFilter.GaussianBlur(blur))

def shade_paint(img, box, col, a, r):
    """Paint a region but keep the print's light and shadow (multiply with the photo's luminance)."""
    m = Image.new("L", img.size, 0); ImageDraw.Draw(m).rounded_rectangle(box, r, fill=255); m = m.filter(ImageFilter.GaussianBlur(2))
    lum = img.convert("L").point(lambda v: min(255, int(v * 1.25)))
    paint = ImageChops.multiply(Image.new("RGB", img.size, col), Image.merge("RGB", (lum, lum, lum))).convert("RGBA")
    paint.putalpha(m.point(lambda v: v * a // 255)); out = img.copy(); out.alpha_composite(paint); return out

def eyes_rects(d, col, inset=0.16):
    for x0, y0, x1, y1 in EYES:
        ix, iy = (x1 - x0) * inset, (y1 - y0) * 0.14
        d.rounded_rectangle((x0 + ix, y0 + iy, x1 - ix, y1 - iy), int((x1 - x0) * 0.2), fill=col + (255,))

def smile(d, col, wdt=16):
    d.arc((352, 300, 560, 420), 20, 160, fill=col + (255,), width=wdt)

def bg(img):
    W, H = 900, 1100; b.W, b.H = W, H
    canvas = b.background(seed=3, words=["bit", "led", "paint", "esp32", "amoled", "face()", "glow"])
    s = 1000 / img.height; p = img.resize((round(img.width * s), 1000), Image.LANCZOS)
    x = (W - p.width) // 2; b.drop_shadow(canvas, p, (x, 60)); canvas.alpha_composite(p, (x, 60)); return canvas.convert("RGB")

# 1. LED eyes
lay, gl = glow_layer(lambda d: eyes_rects(d, CY), 28)
spill = Image.new("RGBA", src.size, (0, 0, 0, 0)); ImageDraw.Draw(spill).ellipse((200, 120, 720, 420), fill=CY + (60,))
leds = src.copy(); leds.alpha_composite(spill.filter(ImageFilter.GaussianBlur(60))); leds.alpha_composite(gl); leds.alpha_composite(gl); leds.alpha_composite(lay)
leds.putalpha(src.getchannel("A")); bg(leds).save(os.path.join(OUT, "real_leds.png"))

# 2. painted collectible
pt = shade_paint(src, VISOR, (34, 38, 58), 235, 60); pt = shade_paint(pt, CHEST, (34, 38, 58), 235, 40)
lay, gl = glow_layer(lambda d: (eyes_rects(d, CY), smile(d, CY)), 10)
pt.alpha_composite(gl); pt.alpha_composite(lay)
d = ImageDraw.Draw(pt); f = b.MONO(118)
d.text(((CHEST[0] + CHEST[2]) / 2, (CHEST[1] + CHEST[3]) / 2), "</>", font=f, fill=CY, anchor="mm")
hl = Image.new("RGBA", src.size, (0, 0, 0, 0)); ImageDraw.Draw(hl).rounded_rectangle((220, 145, 520, 175), 15, fill=(255, 255, 255, 50))
pt.alpha_composite(hl.filter(ImageFilter.GaussianBlur(6))); pt.putalpha(src.getchannel("A")); bg(pt).save(os.path.join(OUT, "real_painted.png"))
pt.save(os.path.join(ROOT, "brand/photos/bit_painted_mockup.png"))  # cutout used by the banner

# 3. AMOLED face: true-black screen, happy eyes, little pixel glare
am = shade_paint(src, VISOR, (2, 2, 4), 255, 60)
def face(d):
    for cx in (330, 578):
        d.arc((cx - 62, 205, cx + 62, 330), 200, 340, fill=CY + (255,), width=22)
    d.arc((370, 300, 540, 410), 25, 155, fill=CY + (255,), width=16)
    for cx in (262, 652): d.ellipse((cx - 28, 330, cx + 28, 362), fill=PK + (150,))
lay, gl = glow_layer(face, 14)
am.alpha_composite(gl); am.alpha_composite(lay)
hl = Image.new("RGBA", src.size, (0, 0, 0, 0)); ImageDraw.Draw(hl).polygon([(560, 135), (720, 135), (720, 200), (610, 300)], fill=(255, 255, 255, 22))
am.alpha_composite(hl.filter(ImageFilter.GaussianBlur(10))); am.putalpha(src.getchannel("A")); bg(am).save(os.path.join(OUT, "real_amoled.png"))
print("ok")
