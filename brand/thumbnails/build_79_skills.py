"""Long-form thumbnail for 'I Gave Claude 79 Game-Dev Skills. It Ignored Them.' (II-9d9HuPn0).
Painted Bit (brand), the real Run 2 maze, and text that adds to the title instead of repeating it: 79 SKILLS / USED: 0.
Out: content/thumbnails/2026-11-22-79-skills-v2-painted.jpg"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
import build_house_v2_pair as v2  # noqa: E402
from build_boss_v3 import background, glow, drop_shadow, F, W, H, PK, CY, WH  # noqa: E402
from build_grok_vs_fable_painted import bit_painted  # noqa: E402

def maze_still(t=140, size=470):
    """The real Run 2 game (skills installed, 0 used), from the long-form."""
    tmp = os.path.join(tempfile.mkdtemp(), "m.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", os.path.join(ROOT, "content/videos/2026-11-22-pac-bit.mp4"),
                    "-frames:v", "1", "-vf", "crop=1000:1000:900:40", tmp], check=True)
    m = ImageEnhance.Contrast(Image.open(tmp).convert("RGB")).enhance(1.25).resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", m.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), 26, fill=255); m.putalpha(mask)
    frame = Image.new("RGBA", (size + 24, size + 24), (0, 0, 0, 0)); fd = ImageDraw.Draw(frame)
    fd.rounded_rectangle((0, 0, size + 23, size + 23), 34, fill=CY + (255,)); frame.alpha_composite(m, (12, 12))
    return frame.rotate(5, expand=True, resample=Image.BICUBIC)

def shocked_face(im, x, hgt, top=30):
    """Repaint Bit's screen with a shocked face (wide eyes, small 'o' mouth); fractions measured on bit_painted_mockup.png."""
    w = 920 * hgt / 1507; fx = lambda a: x + a * w; fy = lambda b: top + b * hgt
    d = ImageDraw.Draw(im); scr = (fx(0.215), fy(0.098), fx(0.735), fy(0.300)); d.rounded_rectangle(scr, 22, fill=(22, 22, 30))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g); cy_, r = fy(0.185), 0.062 * w
    for cx in (fx(0.355), fx(0.595)): gd.ellipse((cx - r, cy_ - r, cx + r, cy_ + r), fill=CY + (255,))
    mx, my = fx(0.475), fy(0.262); gd.ellipse((mx - 0.03 * w, my - 0.032 * w, mx + 0.03 * w, my + 0.032 * w), outline=CY + (255,), width=9)
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(10))); im.alpha_composite(g)
    for cx in (fx(0.355), fx(0.595)): d.ellipse((cx - r * 0.3 + 8, cy_ - r * 0.55, cx + r * 0.3 + 8, cy_ + r * 0.05 - 8), fill=(235, 255, 255))

def main():
    im = background(seed=22, words=["skills/", "79", "SKILL.md", "game-feel", "ghost-ai", "maze.js", "used: 0", "__bitDebug", "setLives(n)", "PROMPT.md", "27:43", "12:50", "15:12", "opus", "claude"])
    glow(im, (640, 20, 1320, 760), PK, 120, 120); glow(im, (0, 300, 620, 760), CY, 50, 120)
    mz = maze_still(); mx, my = 150, 250; drop_shadow(im, mz, (mx, my)); im.alpha_composite(mz, (mx, my))
    x = bit_painted(im, 880, 40); shocked_face(im, x, 880)
    d = ImageDraw.Draw(im)
    f = v2.fit(d, "79 SKILLS", 170, x - 70)                                    # headline, top left
    d.text((48, 28), "79 SKILLS", font=f, fill=WH, stroke_width=10, stroke_fill=v2.INK)
    # red stamp over the maze: USED: 0
    sw, sh = 520, 190; st = Image.new("RGBA", (sw, sh), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
    sd.rounded_rectangle((6, 6, sw - 6, sh - 6), 28, fill=v2.RED + (255,), outline=v2.INK + (255,), width=10)
    sd.text((sw // 2, sh // 2 + 4), "USED: 0", font=F(130), fill=WH, anchor="mm", stroke_width=6, stroke_fill=v2.INK)
    st = st.rotate(-7, expand=True, resample=Image.BICUBIC); g = st.filter(ImageFilter.GaussianBlur(14)); g.putalpha(g.getchannel("A").point(lambda v: v // 2))
    sx, sy = 40, 440; im.alpha_composite(g, (sx + 10, sy + 14)); im.alpha_composite(st, (sx, sy))
    out = os.path.join(ROOT, "content/thumbnails/2026-11-22-79-skills-v2-painted.jpg"); im.convert("RGB").save(out, quality=92); print(out)

if __name__ == "__main__":
    main()
