"""Channel trailer for non-subscribers (15 Nov 2026), ~34 s, 1920x1080.
  1. Hook: first 11.8 s of the Grok vs Fable long-form (VO + bed as published)
  2. Montage: 5 x 3 s moments (cheat panel, Fable board, upgrades, boss fight, winner) over a lo-fi bed
  3. Brand sting (3 s)
  4. End card: "I make AI build games. Bit plays them." + Subscribe (5 s)
Output: content/videos/channel-trailer.mp4"""
import os, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "brand/thumbnails"))
import build_boss_v3 as b  # noqa: E402

LF = os.path.join(ROOT, "content/videos/2026-11-14-grok-vs-fable.mp4")
STING = os.path.join(ROOT, "content/videos/brand-sting-3s.mp4")
OUT = os.path.join(ROOT, "content/videos/channel-trailer.mp4")
HOOK = 11.8; MOMENTS = [111.5, 150.0, 160.5, 195.0, 224.5]; MD = 3.0; CARD = 5.0
SR = 48000; VF = "scale=1920:1080,fps=30,format=yuv420p"

def run(c): subprocess.run(c, check=True)

def end_card(path):
    W, H = 1920, 1080; b.W, b.H = W, H
    im = b.background(seed=8, words=["play()", "bit.zap()", "level++", "claude", "index.html", "boss.hp", "ship()", "game"])
    b.glow(im, (120, 160, 900, 1000), b.PK, 110, 140)
    p = Image.open(os.path.join(ROOT, "brand/photos/bit_real_cutout.png")).convert("RGBA")
    p = b.light_eyes(b.grade_photo(p)); h = 860; p = p.resize((round(p.width * h / p.height), h), Image.LANCZOS)
    b.drop_shadow(im, p, (170, 170)); im.alpha_composite(p, (170, 170)); im.alpha_composite(b.rim(p, b.CY, 9, 170), (170, 170))
    d = ImageDraw.Draw(im); x = 840; INK = (10, 10, 16); YL = (255, 214, 0)
    d.text((x, 250), "// VIBE WITH AMIT", font=b.MONO(46), fill=b.CY)
    for y, parts in [(320, [("I make AI", b.WH)]), (450, [("build ", b.WH), ("games.", YL)]), (580, [("Bit ", b.PK), ("plays them.", b.WH)])]:
        xx = x
        for t, c in parts:
            d.text((xx, y), t, font=b.F(124), fill=c, stroke_width=7, stroke_fill=INK); xx += d.textlength(t, font=b.F(124))
    d.rounded_rectangle((x, 770, x + 560, 880), 26, fill=(255, 40, 60), outline=INK, width=6)
    d.text((x + 280, 825), "SUBSCRIBE", font=b.F(68), fill=b.WH, anchor="mm", stroke_width=3, stroke_fill=INK)
    d.text((x, 930), "New game every Sunday", font=b.F(50), fill=(180, 186, 210), anchor="lm")
    im.convert("RGB").save(path)

def bed(n, seed=4):
    tt = np.arange(n) / SR; beat = 60 / 90; out = np.zeros(n)
    def dec(s0, dd):
        e = np.zeros(n); i0 = int(s0 * SR)
        if i0 < n: e[i0:] = np.exp(-np.arange(n - i0) / SR / dd)
        return e
    chords = [(220, 261.6, 329.6), (174.6, 220, 261.6), (196, 246.9, 293.7), (164.8, 207.7, 246.9)]
    for k in range(int(n / SR / (beat * 4)) + 1):
        for f in chords[k % 4]: out += 0.05 * np.sin(2 * np.pi * f * tt) * dec(k * beat * 4, 2.6) * (tt >= k * beat * 4)
    for k in range(int(n / SR / beat) + 1):
        s0 = k * beat; fr = 55 * 2 ** (-np.clip((tt - s0) * 30, 0, 3)); out += 0.14 * np.sin(2 * np.pi * np.cumsum(fr) / SR) * dec(s0, .07) * (tt >= s0)
        if k % 2: out += 0.03 * np.random.default_rng(seed + k).uniform(-1, 1, n) * dec(s0, .03) * (tt >= s0)
    return out

def pcm(p, ss=0, t=None):
    c = ["ffmpeg", "-v", "error", "-ss", str(ss), "-i", p] + (["-t", str(t)] if t else []) + ["-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]
    return np.frombuffer(subprocess.run(c, capture_output=True, check=True).stdout, np.int16).astype(float) / 32768

def main():
    tmp = tempfile.mkdtemp(); parts = []
    def seg(name, args):
        o = os.path.join(tmp, name + ".mp4"); run(["ffmpeg", "-v", "error", "-y"] + args + ["-an", "-vf", VF, "-c:v", "libx264", "-crf", "18", o]); parts.append(o)
    seg("hook", ["-ss", "0", "-t", str(HOOK), "-i", LF])
    for i, t in enumerate(MOMENTS): seg(f"m{i}", ["-ss", str(t), "-t", str(MD), "-i", LF])
    seg("sting", ["-i", STING])
    card = os.path.join(tmp, "card.png"); end_card(card)
    seg("card", ["-loop", "1", "-t", str(CARD), "-i", card])
    lst = os.path.join(tmp, "l.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    vid = os.path.join(tmp, "v.mp4"); run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid])

    # audio
    mt = len(MOMENTS) * MD; total = HOOK + mt + 3.0 + CARD; n = int(total * SR); mix = np.zeros(n)
    h = pcm(LF, 0, HOOK); fade = np.ones(len(h)); fade[-int(.4 * SR):] = np.linspace(1, 0, int(.4 * SR)); mix[:len(h)] += h * fade
    a0 = int(HOOK * SR); bd = bed(n - a0)
    g = np.ones(len(bd)); s_on = int(mt * SR); g[s_on:s_on + int(3 * SR)] = 0.25
    g[:int(.3 * SR)] = np.linspace(0, 1, int(.3 * SR)); g[-int(1.5 * SR):] *= np.linspace(1, 0, int(1.5 * SR))
    mix[a0:] += bd * g
    noise = np.random.default_rng(1).uniform(-1, 1, n); tt = np.arange(n) / SR
    for k in range(len(MOMENTS) + 1):                                                   # whoosh on each cut
        s0 = HOOK + k * MD; mix += 0.06 * noise * np.exp(-np.clip(tt - s0, 0, None) / .12) * (tt >= s0)
    st = pcm(STING); i0 = a0 + s_on; mix[i0:i0 + len(st)] += st[: n - i0] * 0.9
    mix = mix / np.max(np.abs(mix)) * 0.89; wav = os.path.join(tmp, "a.wav")
    with wave.open(wav, "w") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
    run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", OUT])
    print(OUT, round(total, 1), "s")

if __name__ == "__main__":
    main()
