"""'IT REVIEWED ME' thumbnail v3 in the house style: real 3D-printed Bit (graded, eyes lit) holding up to a
magnifier, code background with glow, all text inside the frame. 1280x720."""
import os, sys
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
from build_boss_v3 import background, glow, rim, drop_shadow, grade_photo, light_eyes, EYES, F, W, H, PK, CY, WH  # noqa: E402
YL = (255, 214, 0); INK = (10, 10, 16)

def fit(d, s, size, maxw):
    while d.textlength(s, font=F(size)) > maxw: size -= 4
    return F(size)

def main():
    im = background(seed=7, words=["def", "check_requirement(req):", "shall", "TBD", "if", "vague:", "flag(req)", "return", "verdict", "[ASSUMED]", "review(rules)", "# it reviewed me", "for", "req", "in", "reqs:"]); glow(im, (620, 20, 1320, 760), PK, 120, 120); glow(im, (900, 440, 1300, 760), CY, 60, 90)
    p = Image.open(os.path.join(ROOT, "brand/photos/bit_real_cutout.png")).convert("RGBA")
    p = light_eyes(grade_photo(p)); hgt = 900; s = hgt / p.height
    p = p.resize((round(p.width * s), hgt), Image.LANCZOS); x, y = W - p.width - 70, 30
    drop_shadow(im, p, (x, y)); im.alpha_composite(p, (x, y)); im.alpha_composite(rim(p, CY, 9, 170), (x, y))
    # magnifier over Bit's right eye (viewer's right)
    ex0, ey0, ex1, ey1 = EYES[1]; cx = x + (ex0 + ex1) / 2 * p.width; cy = y + (ey0 + ey1) / 2 * p.height
    R = 92; d = ImageDraw.Draw(im)
    lens = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(lens).ellipse((cx - R, cy - R, cx + R, cy + R), fill=(150, 240, 255, 60))
    im.alpha_composite(lens)
    d.line((cx + R * 0.62, cy + R * 0.62, cx + R * 1.75, cy + R * 1.75), fill=INK, width=44)
    d.line((cx + R * 0.66, cy + R * 0.66, cx + R * 1.72, cy + R * 1.72), fill=WH, width=30)
    d.ellipse((cx - R - 12, cy - R - 12, cx + R + 12, cy + R + 12), outline=INK, width=34)
    d.ellipse((cx - R - 8, cy - R - 8, cx + R + 8, cy + R + 8), outline=WH, width=20)
    d.arc((cx - R + 22, cy - R + 22, cx + R - 22, cy + R - 22), 200, 250, fill=(255, 255, 255), width=8)
    # text, left column, always inside the frame
    maxw = x - 70; ty = 60
    for txt, col, size in (("IT", WH, 190), ("REVIEWED", WH, 130), ("ME", YL, 260)):
        f = fit(d, txt, size, maxw)
        if txt == "ME":
            g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).text((52, ty), txt, font=f, fill=YL + (255,))
            im.alpha_composite(g.filter(ImageFilter.GaussianBlur(16))); d = ImageDraw.Draw(im)
        d.text((52, ty), txt, font=f, fill=col, stroke_width=8, stroke_fill=INK)
        ty += int(f.size * 0.92)
    d.rounded_rectangle((W - 330, H - 74, W - 26, H - 24), 14, fill=(13, 13, 20, 225))
    d.text((W - 178, H - 49), "REAL 3D-PRINTED BIT", font=F(26), fill=CY, anchor="mm")
    out = os.path.join(ROOT, "content/thumbnails/2026-11-07-ai-reviewed-my-rules-v3.jpg")
    im.convert("RGB").save(out, quality=92); print(out)

if __name__ == "__main__":
    main()
