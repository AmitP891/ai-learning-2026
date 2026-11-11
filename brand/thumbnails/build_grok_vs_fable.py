"""Grok vs Claude Fable 5.2 thumbnail (1280x720), in the layout Amit liked from vidIQ:
blue/orange split, big italic two-line title, character on the left, two tiles with VS and labels.
Changes from the vidIQ draft: real 3D-printed Bit instead of an AI face, real gameplay frames
instead of logos, and the right model name (Fable 5.2)."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
from build_boss_v3 import grade_photo, light_eyes, rim, drop_shadow  # noqa: E402
W, H = 1280, 720
BLUE, ORANGE, WHITE = (40, 150, 255), (255, 120, 40), (255, 255, 255)
IT = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf", s)
BD = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", s)
SEAM = lambda y: 860 - (y - 360) * 0.18      # x of the diagonal split at height y

def background():
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    left = xx < (860 - (yy - 360) * 0.18)
    a = np.zeros((H, W, 3))
    # left: deep navy to electric blue; right: dark rust to warm orange
    tl = np.clip(1 - np.hypot(xx - 420, yy - 300) / 900, 0, 1)[..., None]
    tr = np.clip(1 - np.hypot(xx - 1150, yy - 360) / 700, 0, 1)[..., None]
    a[left] = (np.array([6, 14, 36]) + tl * np.array([20, 80, 170]))[left]
    a[~left] = (np.array([30, 10, 4]) + tr * np.array([200, 90, 20]))[~left]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    # soft bokeh blobs for depth
    b = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
    for (x, y, r, c, al) in [(120, 120, 140, BLUE, 70), (600, 90, 110, BLUE, 50), (1180, 140, 150, ORANGE, 80),
                             (1220, 600, 160, ORANGE, 70), (40, 620, 120, (255, 140, 60), 45), (980, 640, 90, ORANGE, 50)]:
        d.ellipse((x - r, y - r, x + r, y + r), fill=c + (al,))
    im.alpha_composite(b.filter(ImageFilter.GaussianBlur(60)))
    # bright seam line
    s = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(s).line([(SEAM(0), 0), (SEAM(H), H)], fill=(255, 255, 255, 230), width=5)
    im.alpha_composite(s.filter(ImageFilter.GaussianBlur(6))); im.alpha_composite(s)
    return im

def glow_rect(im, box, col, a=200, blur=28, grow=14):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(g).rounded_rectangle((box[0] - grow, box[1] - grow, box[2] + grow, box[3] + grow), 46, fill=col + (a,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur)))

def tile(im, path, box, col):
    glow_rect(im, box, col)
    w, h = box[2] - box[0], box[3] - box[1]
    t = Image.open(os.path.join(HERE, path)).convert("RGBA").resize((w, h), Image.LANCZOS)
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), 38, fill=255)
    t.putalpha(m); im.alpha_composite(t, box[:2])
    ImageDraw.Draw(im).rounded_rectangle(box, 38, outline=WHITE + (235,), width=5)

def text(im, xy, s, font, fill=WHITE, stroke=8, anchor="la", glow_col=None):
    if glow_col:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).text(xy, s, font=font, fill=glow_col + (220,), anchor=anchor, stroke_width=stroke + 6, stroke_fill=glow_col + (220,))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(18)))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).text((xy[0] + 6, xy[1] + 8), s, font=font, fill=(0, 0, 0, 200), anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0, 200))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(im).text(xy, s, font=font, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(14, 18, 40))

def build():
    im = background()
    # Bit on the left, big, cropped at the bottom like the presenter in the reference
    p = Image.open(os.path.join(ROOT, "brand/photos/bit_real_cutout.png")).convert("RGBA")
    a = p.getchannel("A").point(lambda v: 0 if v < 60 else v); p.putalpha(a)  # drop faint halo
    p = light_eyes(grade_photo(p)); hgt = 900; p = p.resize((round(p.width * hgt / p.height), hgt), Image.LANCZOS)
    x, y = -40, 110
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse((x + 40, y + 40, x + p.width - 20, y + 520), fill=(255, 80, 170, 150))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(80)))
    drop_shadow(im, p, (x, y)); im.alpha_composite(p, (x, y)); im.alpha_composite(rim(p, (120, 210, 255), 9, 190), (x, y))
    # two game tiles + VS + labels
    tile(im, "src/bugblaster_grok.jpg", (455, 285, 755, 585), BLUE)
    tile(im, "src/bugblaster_fable.jpg", (945, 285, 1245, 585), ORANGE)
    text(im, (850, 445), "vs", IT(96), stroke=7, anchor="mm")
    text(im, (605, 645), "Grok", BD(64), stroke=5, anchor="mm")
    text(im, (1095, 645), "Fable 5.2", BD(64), stroke=5, anchor="mm")
    # title, top right, two lines
    text(im, (1250, 92), "GROK vs CLAUDE:", IT(98), anchor="rm", glow_col=(60, 140, 255))
    text(im, (1250, 205), "The Winner?", IT(110), anchor="rm", glow_col=(255, 130, 50))
    out = os.path.join(ROOT, "content/thumbnails/2026-11-13-grok-vs-fable.jpg")
    im.convert("RGB").save(out, quality=92); print(out)

if __name__ == "__main__":
    build()
