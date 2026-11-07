"""Thumbnail v2 for the boss-fight long-form (21 Nov) and Adventures of Bit Ep 1 (28 Nov), 1280x720.
One focal point each, readable at phone size. Brand colours only."""
import io, os, re, sys, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "brand/adventures"))
from prof import professor  # noqa: E402
W, H = 1280, 720
BG, PK, CY, WH, YL = (13, 13, 20), (240, 53, 158), (0, 240, 255), (245, 244, 239), (255, 214, 0)
GR, RD_SOFT, VIS = (57, 255, 136), (150, 155, 175), (23, 26, 43)
F = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", s)
OUT = os.path.join(ROOT, "content/thumbnails")


def bit(height, mood="determined"):
    s = open(os.path.join(ROOT, "brand/bit/bit.svg")).read()
    s = re.sub(r'<g id="eyes">.*?</g>', "", s, flags=re.S); s = re.sub(r'<path id="mouth"[^>]*/>', "", s)
    k = 2.0
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=s.encode(), output_width=int(600 * k),
                                                 output_height=int(700 * k)))).convert("RGBA")
    d = ImageDraw.Draw(im); P = lambda x, y: (x * k, y * k)
    for ex in (244, 356):
        cx, cy = P(ex, 199)
        if mood == "determined":
            hi, lo = (cy - 20 * k, cy - 6 * k) if ex < 300 else (cy - 6 * k, cy - 20 * k)
            d.polygon([(cx - 26 * k, hi), (cx + 26 * k, lo), (cx + 26 * k, cy + 24 * k), (cx - 26 * k, cy + 24 * k)], fill=CY)
        else:  # happy
            d.arc((cx - 24 * k, cy - 14 * k, cx + 24 * k, cy + 30 * k), 200, 340, fill=CY, width=int(10 * k))
    mx, my = P(300, 262)
    if mood == "determined": d.line((mx - 34 * k, my + 4 * k, mx + 34 * k, my - 4 * k), fill=CY, width=int(9 * k))
    else: d.arc((mx - 40 * k, my - 40 * k, mx + 40 * k, my + 12 * k), 25, 155, fill=CY, width=int(9 * k))
    im = im.crop(im.getbbox())
    return im.resize((round(im.width * height / im.height), height), Image.LANCZOS)


def prof(height, mood="smug"):
    p = professor(0.0, 0.0, mood, 1.0)
    p = p.crop(p.getbbox())
    return p.resize((round(p.width * height / p.height), height), Image.LANCZOS)


def base():
    return Image.new("RGBA", (W, H), BG + (255,))


def glow(im, box, col, a=90, blur=110):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse(box, fill=col + (a,))
    return Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(blur)))


def fit(d, s, size, maxw):
    while d.textlength(s, font=F(size)) > maxw: size -= 4
    return F(size)


def arrow(d, x0, x1, y, col, w=34):
    d.line((x0, y, x1 - 40, y), fill=col, width=w)
    d.polygon([(x1, y), (x1 - 70, y - 56), (x1 - 70, y + 56)], fill=col)


# ---------------------------------------------------------------- boss fight: 3/10 -> 8/10
def boss_fight():
    im = base()
    im = glow(im, (720, 60, 1300, 720), PK, 80)
    im = glow(im, (-100, 300, 700, 900), GR, 40)
    pr = prof(600)
    pr.putalpha(pr.getchannel("A").point(lambda v: int(v * 0.55)))  # the old 3/10 boss, faded behind
    im.alpha_composite(pr, (W - pr.width + 70, H - pr.height + 120))
    b = bit(560)
    im.alpha_composite(b, (W - b.width - 215, H - b.height + 40))
    d = ImageDraw.Draw(im)
    f1 = F(170)
    d.text((56, 40), "3/10", font=f1, fill=RD_SOFT, stroke_width=6, stroke_fill=BG)
    w3 = d.textlength("3/10", font=f1)
    d.line((50, 145, 70 + w3, 125), fill=PK, width=18)   # crossed out
    arrow(d, 70, 360, 330, WH)
    d.text((48, 400), "8/10", font=F(270), fill=GR, stroke_width=8, stroke_fill=BG)
    im.convert("RGB").save(os.path.join(OUT, "2026-11-21-claude-boss-fight-v2.jpg"), quality=92)


# ---------------------------------------------------------------- Ep 1: BIT VS VAGUE
def ep1():
    im = base()
    im = glow(im, (-200, 120, 620, 900), PK, 90)
    im = glow(im, (700, 120, 1500, 900), (150, 120, 220), 70)
    d = ImageDraw.Draw(im)
    b = bit(500); pr = prof(680, "smug")
    im.alpha_composite(b, (40, H - b.height + 30))
    im.alpha_composite(pr, (W - pr.width + 40, H - pr.height + 190))
    d = ImageDraw.Draw(im)
    # stacked title in the middle-top
    y = 26
    for s, col, size in (("BIT", PK, 210), ("VS", WH, 120), ("VAGUE", YL, 210)):
        f = fit(d, s, size, 620)
        d.text((W / 2, y), s, font=f, fill=col, anchor="mt", stroke_width=8, stroke_fill=BG)
        y += f.size * (0.78 if s != "VS" else 0.86)
    # episode tag, top left
    tag = "EP 1"; ft = F(54); tw = d.textlength(tag, font=ft)
    d.rounded_rectangle((36, 34, 36 + tw + 44, 34 + 80), radius=18, fill=CY)
    d.text((58, 74), tag, font=ft, fill=BG, anchor="lm")
    im.convert("RGB").save(os.path.join(OUT, "2026-11-28-adventures-of-bit-ep1-v2.jpg"), quality=92)


if __name__ == "__main__":
    boss_fight(); ep1(); print("ok")
