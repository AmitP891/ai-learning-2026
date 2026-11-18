"""Long-form thumbnails re-done with the painted Bit (brand/photos/bit_painted_mockup.png).
Same layouts as the 3D-printed versions; only Bit changes (and the "REAL 3D-PRINTED BIT" badge goes).
Outputs in content/thumbnails/:
  2026-11-14-faceless-v3-painted.jpg
  2026-11-07-ai-reviewed-my-rules-v4-painted.jpg
  2026-11-21-claude-boss-fight-v4-painted.jpg
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
import build_house_v2_pair as v2  # noqa: E402
from build_boss_v3 import background, glow, score_text, F, W, H, PK, CY, WH  # noqa: E402
from build_grok_vs_fable_painted import bit_painted  # noqa: E402

OUT = os.path.join(ROOT, "content/thumbnails")
RIGHT_EYE = (0.625, 0.166)  # centre of Bit's right eye (viewer's right) as a fraction of the painted image
SRC_W, SRC_H = 920, 1507

def faceless():
    im = background(seed=5, words=["ffmpeg", "-i", "bit.svg", "render()", "frames", "voice.mp3", "lip_sync()", "python3", "build.py", "no_camera", "no_editor", "30fps", "mouth.open", "claude", "code"])
    glow(im, (620, 20, 1320, 760), PK, 120, 120); glow(im, (900, 440, 1300, 760), CY, 60, 90)
    x = bit_painted(im)
    v2.stack(im, x, [("NO FACE.", WH, 150, False), ("NO EDITOR.", WH, 150, False), ("100%", v2.YL, 200, True), ("CODE", v2.YL, 200, True)], 40)
    out = os.path.join(OUT, "2026-11-14-faceless-v3-painted.jpg"); im.convert("RGB").save(out, quality=92); print(out)

def reviewed_me():
    im = background(seed=7, words=["def", "check_requirement(req):", "shall", "TBD", "if", "vague:", "flag(req)", "return", "verdict", "[ASSUMED]", "review(rules)", "# it reviewed me", "for", "req", "in", "reqs:"])
    glow(im, (620, 20, 1320, 760), PK, 120, 120); glow(im, (900, 440, 1300, 760), CY, 60, 90)
    hgt = 900; x = bit_painted(im, hgt); pw = SRC_W * hgt / SRC_H
    cx = x + RIGHT_EYE[0] * pw; cy = 30 + RIGHT_EYE[1] * hgt; R = 92; d = ImageDraw.Draw(im)
    lens = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(lens).ellipse((cx - R, cy - R, cx + R, cy + R), fill=(150, 240, 255, 60)); im.alpha_composite(lens)
    d.line((cx + R * 0.62, cy + R * 0.62, cx + R * 1.75, cy + R * 1.75), fill=v2.INK, width=44)
    d.line((cx + R * 0.66, cy + R * 0.66, cx + R * 1.72, cy + R * 1.72), fill=WH, width=30)
    d.ellipse((cx - R - 12, cy - R - 12, cx + R + 12, cy + R + 12), outline=v2.INK, width=34)
    d.ellipse((cx - R - 8, cy - R - 8, cx + R + 8, cy + R + 8), outline=WH, width=20)
    d.arc((cx - R + 22, cy - R + 22, cx + R - 22, cy + R - 22), 200, 250, fill=(255, 255, 255), width=8)
    maxw = x - 70; ty = 60
    for txt, col, size in (("IT", WH, 190), ("REVIEWED", WH, 130), ("ME", v2.YL, 260)):
        f = v2.fit(d, txt, size, maxw)
        if txt == "ME":
            g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).text((52, ty), txt, font=f, fill=v2.YL + (255,))
            im.alpha_composite(g.filter(ImageFilter.GaussianBlur(16))); d = ImageDraw.Draw(im)
        d.text((52, ty), txt, font=f, fill=col, stroke_width=8, stroke_fill=v2.INK); ty += int(f.size * 0.92)
    out = os.path.join(OUT, "2026-11-07-ai-reviewed-my-rules-v4-painted.jpg"); im.convert("RGB").save(out, quality=92); print(out)

def boss_fight():
    im = background(); glow(im, (640, 40, 1320, 760), PK, 120, 120); glow(im, (900, 420, 1300, 760), CY, 60, 90)
    bit_painted(im); score_text(im)
    out = os.path.join(OUT, "2026-11-21-claude-boss-fight-v4-painted.jpg"); im.convert("RGB").save(out, quality=92); print(out)

if __name__ == "__main__":
    faceless(); reviewed_me(); boss_fight()
