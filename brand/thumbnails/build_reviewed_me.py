"""Thumbnail v2 for 'I Built an AI Requirements Reviewer. Then It Reviewed Me.' (1280x720).
One focal point: big Bit examining you through a magnifier, three big words. Brand colours only."""
import io, os, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
W, H = 1280, 720
BG, PK, CY, WH, YL = (13, 13, 20), (240, 53, 158), (0, 240, 255), (245, 244, 239), (255, 214, 0)
F = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", s)

svg = open(os.path.join(ROOT, "brand/bit/bit.svg")).read()
keep = [l for l in svg.splitlines() if l.startswith(("<svg", "</svg", '<line x1="300"', '<circle cx="300"'))
        or 'x="140"' in l or 'x="172"' in l or 'id="eyes"' in l or 'id="mouth"' in l]
head = "\n".join(keep).replace('viewBox="0 0 600 700" width="600" height="700"', 'viewBox="130 15 340 330" width="340" height="330"')
bit = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=head.encode(), output_width=1020, output_height=990))).convert("RGBA")
bit = bit.crop(bit.getbbox()); bh = 560; bit = bit.resize((round(bit.width * bh / bit.height), bh), Image.LANCZOS)

im = Image.new("RGBA", (W, H), BG + (255,))
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((620, 40, 1280, 700), fill=PK + (90,))
im = Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(110)))
bx, by = W - bit.width - 20, (H - bit.height) // 2 + 30
im.alpha_composite(bit, (bx, by))

# magnifier over Bit's right eye (the focal point)
d = ImageDraw.Draw(im)
cx, cy, r = bx + int(bit.width * 0.64), by + int(bit.height * 0.50), 118
lens = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(lens).ellipse((cx - r, cy - r, cx + r, cy + r), fill=CY + (40,))
im = Image.alpha_composite(im, lens); d = ImageDraw.Draw(im)
d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=WH, width=22)
d.line((cx - int(r * 0.72), cy + int(r * 0.72), cx - int(r * 1.55), cy + int(r * 1.55)), fill=WH, width=40)

# three words, left, huge
MAXW = bx - 90
def text(s, y, size, col, stroke=0):
    while d.textlength(s, font=F(size)) > MAXW: size -= 4
    d.text((56, y), s, font=F(size), fill=col, stroke_width=stroke, stroke_fill=BG)
    return size
text("IT", 60, 200, WH, 6)
text("REVIEWED", 280, 150, WH, 6)
text("ME", 400, 300, YL, 8)
im.convert("RGB").save(os.path.join(ROOT, "content/thumbnails/2026-11-07-ai-reviewed-my-rules-v2.jpg"), quality=92)
print("ok")
