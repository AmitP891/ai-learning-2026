"""Teaser Short (1080x1920, 18 s): Grok vs Claude Fable 5.2, same game prompt.
Split screen of real gameplay (Grok top, Fable bottom) + text beats + Bit end card + synth beat.
Usage: python3 build_grok_vs_fable_teaser.py GROK_REC.mov FABLE_REC.mov OUT.mp4"""
import os, sys, subprocess, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "brand/thumbnails"))
from build_boss_v3 import grade_photo, light_eyes  # noqa: E402
W, H, DUR, BPM = 1080, 1920, 18.0, 120
IT = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf", s)
BD = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", s)
BLUE, ORANGE, PINK, CYAN, WHITE = (40, 150, 255), (255, 130, 40), (240, 53, 158), (0, 240, 255), (255, 255, 255)

def txt(d, xy, s, f, fill=WHITE, stroke=8, anchor="mm"):
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(10, 12, 28))

def label(path, text, col, y):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    w = d.textlength(text, font=BD(52)) + 60
    d.rounded_rectangle((40, y, 40 + w, y + 84), 20, fill=col + (235,))
    d.text((70, y + 42), text, font=BD(52), fill=WHITE, anchor="lm")
    im.save(path)

def band(path, lines, cols):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((0, 960 - 120, W, 960 + 120), fill=(8, 10, 22, 230))
    d.line((0, 840, W, 840), fill=BLUE + (255,), width=6); d.line((0, 1080, W, 1080), fill=ORANGE + (255,), width=6)
    ys = [960] if len(lines) == 1 else [905, 1015]
    for s, y, c in zip(lines, ys, cols):
        size = 104
        while d.textlength(s, font=IT(size)) > W - 90: size -= 4
        txt(d, (W // 2, y), s, IT(size), fill=c)
    im.save(path)

def end_card(path):
    im = Image.new("RGBA", (W, H), (6, 8, 20, 235)); d = ImageDraw.Draw(im)
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse((140, 420, 940, 1220), fill=PINK + (120,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(120)))
    p = Image.open(os.path.join(ROOT, "brand/photos/bit_real_cutout.png")).convert("RGBA")
    p.putalpha(p.getchannel("A").point(lambda v: 0 if v < 60 else v))
    p = light_eyes(grade_photo(p)); h = 820; p = p.resize((round(p.width * h / p.height), h), Image.LANCZOS)
    im.alpha_composite(p, ((W - p.width) // 2, 470))
    txt(d, (W // 2, 300), "WHO WON?", IT(150), fill=WHITE, stroke=10)
    txt(d, (W // 2, 1370), "FULL VIDEO FRIDAY", IT(92), fill=CYAN)
    txt(d, (W // 2, 1490), "SUBSCRIBE SO YOU DON'T MISS IT", BD(52), fill=WHITE, stroke=6)
    im.save(path)

def music(path):
    sr = 44100; n = int(sr * DUR); t = np.arange(n) / sr; beat = 60 / BPM; out = np.zeros(n)
    def env(start, length, decay):
        e = np.zeros(n); i0 = int(start * sr); i1 = min(n, i0 + int(length * sr))
        if i0 < n: e[i0:i1] = np.exp(-np.arange(i1 - i0) / sr / decay)
        return e
    rng = np.random.default_rng(3); noise = rng.uniform(-1, 1, n)
    notes = [110, 110, 130.8, 146.8, 110, 164.8, 146.8, 130.8]          # A minor bass line, 8ths
    for k in range(int(DUR / beat)):
        s = k * beat
        if s >= 15: break                                               # beat drops out under the end card
        f = 55 * 2 ** (-np.clip((t - s) * 30, 0, 3))                     # kick
        out += 0.9 * np.sin(2 * np.pi * np.cumsum(f) / sr) * env(s, 0.25, 0.08) * (t >= s)
        if k % 2 == 1: out += 0.35 * noise * env(s, 0.15, 0.04)          # snare-ish
    for k in range(int(DUR / (beat / 2))):
        s = k * beat / 2
        if s >= 15: break
        out += 0.12 * noise * env(s, 0.04, 0.01)                         # hats
        fr = notes[k % 8]
        out += 0.22 * np.sign(np.sin(2 * np.pi * fr * t)) * env(s, 0.24, 0.12)
        arp = [440, 523.3, 659.3, 880][k % 4] * (1.5 if 7.5 <= s < 15 else 1)
        out += 0.07 * np.sin(2 * np.pi * arp * t) * env(s, 0.2, 0.08)
    for s in (0, 3.5, 7.5, 11.5):                                       # whoosh on each text change
        out += 0.25 * noise * env(s, 0.4, 0.15) * np.linspace(1, 0.3, n)
    out += 0.3 * np.sin(2 * np.pi * 220 * t) * env(15, 3, 1.2) + 0.2 * np.sin(2 * np.pi * 329.6 * t) * env(15, 3, 1.2)
    out = out / np.max(np.abs(out)) * 0.5                               # peak about -6 dB
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out * 32767).astype(np.int16).tobytes())

def main(grok, fable, out):
    tmp = tempfile.mkdtemp()
    P = lambda n: os.path.join(tmp, n)
    label(P("lg.png"), "GROK  ·  9 MIN", BLUE, 70)
    label(P("lf.png"), "CLAUDE FABLE 5.2  ·  17 MIN", ORANGE, 1110)
    band(P("b1.png"), ["SAME GAME PROMPT", "2 AIs"], [WHITE, CYAN])
    band(P("b2.png"), ["9 MINUTES", "vs 17 MINUTES"], [BLUE, ORANGE])
    band(P("b3.png"), ["ONE HID A CHEAT", "IN ITS OWN CODE"], [WHITE, PINK])
    band(P("b4.png"), ["THEN WE ADDED", "BOSS FIGHTS"], [WHITE, ORANGE])
    end_card(P("end.png")); music(P("m.wav"))
    crop = "crop=1800:1600:570:240,scale=1080:960,setsar=1"
    cropf = "crop=1800:1600:120:240,scale=1080:960,setsar=1"   # shifted left so the boss bug (enters on the left) is fully in shot
    fc = (f"[0:v]{crop},fps=30[g];[1:v]{cropf},fps=30[f];[g][f]vstack[v0];"
          "[v0][2:v]overlay=0:0[v1];[v1][3:v]overlay=0:0[v2];"
          "[v2][4:v]overlay=0:0:enable='lt(t,3.5)'[v3];[v3][5:v]overlay=0:0:enable='between(t,3.5,7.5)'[v4];"
          "[v4][6:v]overlay=0:0:enable='between(t,7.5,11.5)'[v5];[v5][7:v]overlay=0:0:enable='between(t,11.5,15)'[v6];"
          "[8:v]format=rgba,fade=t=in:st=15:d=0.35:alpha=1[e];[v6][e]overlay=0:0:enable='gte(t,15)'[v]")
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", "20", "-t", str(DUR), "-i", grok, "-ss", "51.5", "-t", str(DUR), "-i", fable]
    for n in ["lg", "lf", "b1", "b2", "b3", "b4", "end"]: cmd += ["-loop", "1", "-t", str(DUR), "-i", P(n + ".png")]
    cmd += ["-i", P("m.wav"), "-filter_complex", fc, "-map", "[v]", "-map", "9:a", "-t", str(DUR),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "-r", "30", out]
    subprocess.run(cmd, check=True); print(out)

if __name__ == "__main__":
    main(*sys.argv[1:4])
