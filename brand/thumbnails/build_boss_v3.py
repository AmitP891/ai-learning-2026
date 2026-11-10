"""Boss-fight thumbnail v3, two house-style candidates (1280x720):
  A  real 3D-printed Bit (photo cutout, colour-graded only) on a lit code background
  B  on-model code-drawn Bit with depth: lighting, rim light, glow, code background
Same hook in both: 3/10 -> 8/10. No AI image generation."""
import os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
from build_boss_ep1_v2 import bit, prof, arrow, F, W, H, PK, CY, WH, GR, RD_SOFT  # noqa: E402
OUT = os.path.join(ROOT, "content/thumbnails")
MONO = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", s)

def background(seed=3, words=None):
    y = np.linspace(0, 1, H)[:, None]; x = np.linspace(0, 1, W)[None, :]
    base = np.zeros((H, W, 3)); base[..., 0] = 12 + 10 * y; base[..., 1] = 12 + 8 * y; base[..., 2] = 22 + 30 * y
    im = Image.fromarray(base.astype(np.uint8)).convert("RGBA")
    code = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(code); r = random.Random(seed)
    words = words or ["def", "boss_fight():", "hp", "-=", "10", "if", "score", ">=", "8:", "render(frame)", "for", "beat", "in", "beats:", "return", "shield()", "bit.attack()", "# 3/10 -> 8/10"]
    for row in range(0, H, 30):
        xx = r.randint(-40, 40)
        while xx < W:
            w = r.choice(words); col = r.choice([(0, 240, 255, 60), (240, 53, 158, 55), (150, 160, 200, 45)])
            d.text((xx, row), w, font=MONO(20), fill=col); xx += d.textlength(w + " ", font=MONO(20)) + r.randint(0, 30)
    im.alpha_composite(code.filter(ImageFilter.GaussianBlur(1.8)))
    vign = Image.new("L", (W, H), 0); ImageDraw.Draw(vign).ellipse((-300, -250, W + 300, H + 250), fill=255)
    dark = Image.new("RGBA", (W, H), (6, 6, 12, 255)); dark.putalpha(ImageChops.invert(vign.filter(ImageFilter.GaussianBlur(160))))
    im.alpha_composite(dark)
    return im

def glow(im, box, col, a, blur):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse(box, fill=col + (a,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur)))

def rim(sprite, col, width=10, a=200):
    """Coloured light wrapping the cutout's edge."""
    al = sprite.getchannel("A"); edge = ImageChops.subtract(al.filter(ImageFilter.MaxFilter(width * 2 + 1)), al)
    out = Image.new("RGBA", sprite.size, col + (0,)); out.putalpha(edge.filter(ImageFilter.GaussianBlur(width / 2)).point(lambda v: min(255, v * a // 255)))
    return out

def shade(sprite, strength=0.32):
    """Key light from the top left, falling off to the bottom right (depth for the flat drawing)."""
    w, h = sprite.size; yy, xx = np.mgrid[0:h, 0:w]
    k = 1 + strength * (0.6 - (xx / w * 0.5 + yy / h * 0.8))
    a = np.array(sprite).astype(float); a[..., :3] = np.clip(a[..., :3] * k[..., None], 0, 255)
    spec = Image.new("L", (w, h), 0); ImageDraw.Draw(spec).ellipse((w * 0.12, h * 0.04, w * 0.5, h * 0.2), fill=70)
    out = Image.fromarray(a.astype(np.uint8))
    hl = Image.new("RGBA", (w, h), (255, 255, 255, 0)); hl.putalpha(ImageChops.multiply(spec.filter(ImageFilter.GaussianBlur(30)), sprite.getchannel("A")))
    out.alpha_composite(hl); return out

def grade_photo(p):
    """Colour grade only: push the salmon print towards brand pink and add contrast."""
    a = np.array(p).astype(float); rgb = a[..., :3]
    tint = np.array([240, 53, 158]) / 255.0
    lum = rgb.mean(-1, keepdims=True) / 255.0
    graded = 0.45 * rgb + 0.55 * (np.clip((lum - 0.5) * 1.5 + 0.62, 0, 1.2) * tint * 255)
    a[..., :3] = np.clip(graded, 0, 255); return Image.fromarray(a.astype(np.uint8))

def drop_shadow(im, sprite, xy, off=(18, 22), blur=22, a=150):
    sh = Image.new("RGBA", sprite.size, (0, 0, 0, 0)); sh.putalpha(sprite.getchannel("A").point(lambda v: v * a // 255))
    big = Image.new("RGBA", (W, H), (0, 0, 0, 0)); big.alpha_composite(sh, (xy[0] + off[0], xy[1] + off[1]))
    im.alpha_composite(big.filter(ImageFilter.GaussianBlur(blur)))

def score_text(im):
    d = ImageDraw.Draw(im)
    f1 = F(150); d.text((60, 52), "3/10", font=f1, fill=RD_SOFT, stroke_width=6, stroke_fill=(10, 10, 16))
    w3 = d.textlength("3/10", font=f1); d.line((52, 150, 72 + w3, 128), fill=PK, width=16)
    arrow(d, 70, 330, 316, WH, w=30)
    t = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(t).text((50, 372), "8/10", font=F(280), fill=GR + (255,))
    im.alpha_composite(t.filter(ImageFilter.GaussianBlur(18)))           # green glow behind the hook
    d.text((50, 372), "8/10", font=F(280), fill=GR, stroke_width=8, stroke_fill=(10, 10, 16))

# eye recesses on the photo cutout, as fractions of its width/height (920x1507 cutout)
EYES = [(279 / 920, 189 / 1507, 381 / 920, 318 / 1507), (525 / 920, 189 / 1507, 630 / 920, 318 / 1507)]

def light_eyes(p):
    """Light the printed eye recesses cyan, like the screen eyes in the videos (the only paint-over)."""
    w, h = p.size; layer = Image.new("RGBA", p.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    for x0, y0, x1, y1 in EYES:
        bx = (x0 * w + 0.16 * (x1 - x0) * w, y0 * h + 0.14 * (y1 - y0) * h, x1 * w - 0.16 * (x1 - x0) * w, y1 * h - 0.14 * (y1 - y0) * h)
        d.rounded_rectangle(bx, radius=int((bx[2] - bx[0]) * 0.28), fill=CY + (255,))
    glow_l = layer.filter(ImageFilter.GaussianBlur(w * 0.02))
    out = p.copy(); out.alpha_composite(glow_l); out.alpha_composite(layer); return out

def version_a():
    im = background(); glow(im, (640, 40, 1320, 760), PK, 120, 120); glow(im, (900, 420, 1300, 760), CY, 60, 90)
    p = Image.open(os.path.join(ROOT, "brand/photos/bit_real_cutout.png")).convert("RGBA")
    p = light_eyes(grade_photo(p)); hgt = 900; p = p.resize((round(p.width * hgt / p.height), hgt), Image.LANCZOS)
    x, y = W - p.width - 70, 30
    drop_shadow(im, p, (x, y)); im.alpha_composite(p, (x, y)); im.alpha_composite(rim(p, CY, 9, 170), (x, y))
    score_text(im)
    d = ImageDraw.Draw(im); d.rounded_rectangle((W - 330, H - 74, W - 26, H - 24), 14, fill=(13, 13, 20, 225))
    d.text((W - 178, H - 49), "REAL 3D-PRINTED BIT", font=F(26), fill=CY, anchor="mm")
    im.convert("RGB").save(os.path.join(OUT, "2026-11-21-claude-boss-fight-v3a-real.jpg"), quality=92)

def version_b():
    im = background(); glow(im, (640, 40, 1320, 760), PK, 120, 120); glow(im, (900, 420, 1300, 760), CY, 60, 90)
    pr = prof(560); pr.putalpha(pr.getchannel("A").point(lambda v: int(v * 0.45)))
    im.alpha_composite(pr.filter(ImageFilter.GaussianBlur(2)), (W - pr.width + 90, H - pr.height + 140))
    b = shade(bit(600)); x, y = W - b.width - 190, H - b.height + 40
    drop_shadow(im, b, (x, y)); im.alpha_composite(b, (x, y)); im.alpha_composite(rim(b, CY, 8, 150), (x, y))
    score_text(im)
    im.convert("RGB").save(os.path.join(OUT, "2026-11-21-claude-boss-fight-v3b-code.jpg"), quality=92)

if __name__ == "__main__":
    version_a(); version_b(); print("ok")
