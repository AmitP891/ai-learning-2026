"""Thumbnail: 'I Gave Claude 79 Game-Dev Skills. It Ignored Them.' (painted Bit, maze in the background).
Output: content/thumbnails/2026-11-22-pac-bit.jpg
Arg 1 (optional): a frame of run 3's maze gameplay (PNG) used as the background tile."""
import os, sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
import build_house_v2_pair as v2  # noqa: E402
from build_boss_v3 import background, glow, rim, drop_shadow, F, W, H, PK, CY, WH  # noqa: E402
GOLD, RED, INK, GREEN = (255, 200, 60), v2.RED, v2.INK, (57, 255, 136)
im = background(seed=22, words=["router", "game-ai", "skills: 0", "maze", "data.bits", "bug.chase()", "zap()", "index.html", "79", "level 1"])
if len(sys.argv) > 1:   # maze tile behind Bit
    m = Image.open(sys.argv[1]).convert("RGB").crop((760, 240, 2160, 1840)).resize((560, 640))
    m = ImageEnhance.Brightness(m).enhance(0.55).convert("RGBA"); m.putalpha(150); im.alpha_composite(m, (W - 600, 40))
glow(im, (640, 20, 1320, 760), PK, 120, 120); glow(im, (0, 0, 640, 720), GOLD, 30, 140)
p = Image.open(os.path.join(ROOT, "brand/photos/bit_painted_mockup.png")).convert("RGBA"); a = p.getchannel("A")
p = ImageEnhance.Contrast(ImageEnhance.Color(p.convert("RGB")).enhance(1.3)).enhance(1.12).convert("RGBA"); p.putalpha(a)
s = 900 / p.height; p = p.resize((round(p.width * s), 900), Image.LANCZOS); x = W - p.width - 70
drop_shadow(im, p, (x, 30)); im.alpha_composite(p, (x, 30)); im.alpha_composite(rim(p, CY, 9, 170), (x, 30))
ty = v2.stack(im, x, [("79 GAME-DEV", GOLD, 120, True), ("SKILLS…", WH, 120, False)], 40)
d = ImageDraw.Draw(im); s1 = "CLAUDE IGNORED THEM"; f = F(70); w = d.textlength(s1, font=f) + 60
w = min(w, x - 40); d.rounded_rectangle((52, ty + 40, 52 + w, ty + 145), 24, fill=RED, outline=INK, width=6)
d.text((52 + w / 2, ty + 92), s1, font=v2.fit(d, s1, 70, w - 50), fill=WH, anchor="mm", stroke_width=3, stroke_fill=INK)
d.text((60, ty + 180), "skills used: 0", font=F(60), fill=GREEN, stroke_width=6, stroke_fill=INK)
out = os.path.join(ROOT, "content/thumbnails/2026-11-22-pac-bit.jpg"); im.convert("RGB").save(out, quality=92); print(out)
