"""Ask Bit episode 1: 'Can AI really build a game in 10 minutes?' (1080x1920, 30 fps).
Studio frames come from studio/render.js (3D, mouths, waveforms, captions); the HUD panels, end card and
sound are added here. Timings below are measured from Amit's ElevenLabs conversation (pauses + pitch).
Usage: python3 build_ep01.py VOICE.mp3 OUT.mp4 [w h]"""
import json, os, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..", "..")
sys.path.insert(0, HERE)
from build_coming_soon import pcm, envelope, FPS  # noqa: E402
SR = 44100
BK = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", s)
BI = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf", s)
BD = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", s)
MONO = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", s)
PINK, LIME, CYAN, WHITE, RED, GOLD, INK = (240, 53, 158), (57, 255, 136), (0, 240, 255), (255, 255, 255), (255, 70, 90), (255, 200, 80), (10, 11, 24)

# (start, end, speaker) per script line, measured from the audio
LINES = [(0.00, 4.60, "G"), (4.97, 11.38, "B"), (12.08, 18.39, "B"), (18.75, 20.91, "G"), (21.25, 22.00, "B"), (22.68, 32.39, "B"),
         (32.86, 35.53, "G"), (35.88, 39.78, "B"), (40.07, 40.71, "G"), (41.17, 49.12, "B"), (49.60, 51.29, "G"), (51.60, 53.54, "B")]
CAPS = [(0.0, 4.0, "G", "Bit. People say AI can build a whole game in ten minutes."), (4.0, 4.8, "G", "True?"),
        (4.9, 7.6, "B", "Let's check. Three simple parts."), (7.6, 11.6, "B", "What people say. What we tried. And is it real."),
        (12.0, 14.25, "B", "What people say: one prompt, one shot,"), (14.25, 18.6, "B", "a full 3D game. Done before your coffee's cold."),
        (18.7, 21.1, "G", "So I type one sentence and ship it?"), (21.15, 22.3, "B", "That's the claim."),
        (22.6, 26.1, "B", "What we tried: the same prompt to two AIs."), (26.1, 30.8, "B", "Grok took nine minutes. Claude Fable 5.2 took seventeen."),
        (30.8, 32.7, "B", "Both games ran first time."), (32.8, 35.75, "G", "Nine minutes. Grok wins. Next."),
        (35.8, 39.95, "B", "Grok's tester skipped the levels using a cheat it hid in its own code."), (39.95, 41.0, "G", "…Respect."),
        (41.1, 43.0, "B", "Is it real? It's real."), (43.0, 46.6, "B", "But a human still has to play it. The fast one cut corners."),
        (46.6, 49.4, "B", "And the slow one made level one too hard to beat."), (49.5, 51.45, "G", "So am I a game dev now?"),
        (51.5, 53.9, "B", "You're a prompt writer. With a game.")]
END = 53.9; DUR = END + 3.6

def shot_at(t):
    plan = [(0, "wide"), (4.85, "bit"), (11.9, "wide"), (18.6, "glitch"), (21.1, "bit"), (22.5, "wide"), (32.75, "glitch"),
            (35.75, "bit"), (39.95, "glitch"), (41.0, "wide"), (49.45, "glitch"), (51.45, "bit"), (END, "wide")]
    cur, t0 = plan[0][1], 0
    for s, name in plan:
        if t >= s: cur, t0 = name, s
    return cur, t - t0

# ---------------- HUD (drawn per frame with PIL) ----------------
ease = lambda x: 1 - (1 - min(1, max(0, x))) ** 3
def rr(d, box, r, **kw): d.rounded_rectangle(box, r, **kw)
def chip(im, text, y, col, a=1.0, size=48):
    d = ImageDraw.Draw(im); w = d.textlength(text, font=BD(size)) + 60; x0 = (1080 - w) / 2
    rr(d, (x0, y, x0 + w, y + size + 34), (size + 34) // 2, fill=col + (int(250 * a),)); d.text((540, y + (size + 34) / 2), text, font=BD(size), fill=INK + (int(255 * a),), anchor="mm")
def panel(im, a, top=230, bot=800):
    d = ImageDraw.Draw(im); off = int((1 - a) * -30)
    rr(d, (70, top + off, 1010, bot + off), 34, fill=(10, 12, 26, int(228 * a)), outline=CYAN + (int(255 * a),), width=5); return off
def txt(d, xy, s, f, fill, a=1.0, anchor="la", stroke=0):
    d.text(xy, s, font=f, fill=fill + (int(255 * a),), anchor=anchor, stroke_width=stroke, stroke_fill=INK + (int(255 * a),))
GROK = Image.open(os.path.join(ROOT, "brand/thumbnails/src/bugblaster_grok.jpg")).convert("RGB").resize((380, 380))
FABLE = Image.open(os.path.join(ROOT, "brand/thumbnails/src/bugblaster_fable.jpg")).convert("RGB").resize((380, 380))
def paste_card(im, img, x, y, a, label=None, la=0, col=WHITE, tick=0, glow=0):
    if a <= 0: return
    card = img.copy().convert("RGBA"); m = Image.new("L", card.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 379, 379), 26, fill=int(255 * a)); card.putalpha(m)
    if glow > 0:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle((x - 14, y - 14, x + 394, y + 394), 36, fill=CYAN + (int(170 * glow),)); im.alpha_composite(g.filter(ImageFilter.GaussianBlur(18)))
    im.alpha_composite(card, (x, y)); d = ImageDraw.Draw(im); rr(d, (x, y, x + 380, y + 380), 26, outline=WHITE + (int(220 * a),), width=4)
    if label and la > 0:
        fs = 40
        while d.textlength(label, font=BK(fs)) > 320: fs -= 2
        rr(d, (x + 14, y + 300, x + 366, y + 362), 18, fill=(10, 12, 26, int(230 * la))); txt(d, (x + 190, y + 331), label, BK(fs), col, la, "mm")
    if tick > 0:
        s = 0.6 + 0.4 * ease(tick * 1.6); cx, cy, r = x + 330, y + 50, 40 * s
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(30, 200, 100, int(255 * min(1, tick * 3))))
        d.line([(cx - r * .45, cy), (cx - r * .1, cy + r * .38), (cx + r * .5, cy - r * .35)], fill=WHITE + (255,), width=int(9 * s), joint="curve")

def hud(t):
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    k = lambda s0, dur=0.3: ease((t - s0) / dur)
    if t < 4.85:                                                   # hook tag
        a = k(0.15); chip(im, "AI GAME IN 10 MIN?", 150 - int((1 - a) * 40), PINK, a, 64)
    elif t < 11.9:                                                 # 3 parts
        a = k(4.9); chip(im, "3 SIMPLE PARTS", 130, CYAN, a); off = panel(im, a, 250, 650)
        for i, (s0, label, col) in enumerate([(7.72, "WHAT PEOPLE SAY", WHITE), (8.98, "WHAT WE TRIED", WHITE), (10.15, "IS IT REAL?", GOLD)]):
            b = k(s0, .25); y = 330 + i * 105 + off
            if b <= 0: continue
            x = 140 - int((1 - b) * 60)
            if i == 2: rr(d, (x, y - 4, x + 40, y + 34), 7, fill=GOLD + (int(255 * b),)); d.arc((x + 5, y - 30, x + 35, y + 6), 180, 360, fill=GOLD + (int(255 * b),), width=7)
            else: d.ellipse((x + 6, y + 2, x + 34, y + 30), fill=PINK + (int(255 * b),))
            txt(d, (x + 70, y + 16), label, BK(62), col, b, "lm")
    elif t < 22.5:                                                 # what people say
        a = k(12.0); chip(im, "WHAT PEOPLE SAY", 130, CYAN, a); off = panel(im, a, 250, 780)
        b = k(12.1, .3)
        if b > 0:
            rr(d, (120, 300 + off, 960, 390 + off), 18, fill=(24, 28, 50, int(255 * b)), outline=(90, 100, 150, int(255 * b)), width=3)
            n = int(len("> make me a 3D game") * min(1, (t - 12.1) / 1.2)); txt(d, (150, 345 + off), "> make me a 3D game"[:n] + ("_" if int(t * 3) % 2 else ""), MONO(44), LIME, b, "lm")
        c = k(14.31, .35)
        if c > 0:
            txt(d, (290, 455 + off), "↓", BK(80), CYAN, c, "mm"); txt(d, (420, 455 + off), "ONE SHOT", BK(46), WHITE, c, "lm")
            g = FABLE.resize((300, 230)).convert("RGBA"); m = Image.new("L", g.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 299, 229), 18, fill=int(255 * c)); g.putalpha(m); im.alpha_composite(g, (140, 520 + off))
            rr(d, (140, 520 + off, 440, 750 + off), 18, outline=WHITE + (int(220 * c),), width=4); txt(d, (470, 590 + off), "FULL 3D GAME", BK(52), WHITE, c, "lm")
        e = k(16.98, .3)
        if e > 0:
            cx, cy = 600, 715 + off; rr(d, (cx, cy - 40, cx + 70, cy + 40), 12, fill=(240, 240, 240, int(255 * e))); d.arc((cx + 50, cy - 25, cx + 100, cy + 20), 270, 90, fill=(240, 240, 240, int(255 * e)), width=10)
            for j in range(3): d.line([(cx + 15 + j * 20, cy - 50), (cx + 20 + j * 20, cy - 66)], fill=(220, 220, 220, int(180 * e)), width=6)
            txt(d, (720, 715 + off), "BEFORE YOUR\nCOFFEE'S COLD", BD(40), GOLD, e, "lm")
        if t >= 21.15: chip(im, "UP NEXT: WHAT WE TRIED", 820, PINK, k(21.15, .25), 40)
    elif t < 41.0:                                                 # what we tried
        a = k(22.6); chip(im, "WHAT WE TRIED", 130, CYAN, a); off = panel(im, a, 250, 870)
        b = k(23.87, .35); txt(d, (540, 300 + off), "SAME PROMPT · 2 AIs", BD(44), WHITE, b, "mm")
        pulse = 0.5 + 0.5 * np.sin((t - 32.86) * 8) if 32.86 <= t < 35.6 else 0
        paste_card(im, GROK, 100, 360 + off, b, "GROK · 9 MIN", k(26.2, .25), WHITE, k(30.9, .4) if t >= 30.9 else 0, pulse)
        paste_card(im, FABLE, 600, 360 + off, b, "FABLE 5.2 · 17 MIN", k(27.87, .25), WHITE, k(30.9, .4) if t >= 30.9 else 0)
        c = k(36.4, .3)
        if c > 0:
            rr(d, (90, 765 + off, 990, 845 + off), 16, fill=(40, 6, 14, int(240 * c)), outline=RED + (int(255 * c),), width=4)
            txt(d, (120, 805 + off), "__game.clearLevel()  // hidden cheat", MONO(36), RED, c, "lm")
        if t >= 40.0: chip(im, "UP NEXT: IS IT REAL?", 890, PINK, k(40.0, .25), 40)
    elif t < END:                                                  # fact check
        a = k(41.1); chip(im, "FACT CHECK", 130, GOLD, a); off = panel(im, a, 250, 800)
        b = k(42.24, .18)
        if b > 0:
            s = 1.6 - 0.6 * b; st = Image.new("RGBA", (420, 170), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
            rr(sd, (8, 8, 412, 162), 20, outline=(40, 220, 120, 255), width=12); sd.text((210, 88), "REAL", font=BK(110), fill=(40, 220, 120, 255), anchor="mm")
            st = st.resize((int(420 * s), int(170 * s))).rotate(-8, expand=True, resample=Image.BICUBIC)
            st.putalpha(st.getchannel("A").point(lambda v: int(v * b))); im.alpha_composite(st, (540 - st.width // 2, 375 + off - st.height // 2))
        for i, (s0, line, col) in enumerate([(43.09, "A human still has to play it", WHITE), (44.99, "Fast one cut corners", RED), (46.71, "Slow one: level 1 too hard", GOLD)]):
            c = k(s0, .25)
            if c <= 0: continue
            y = 520 + i * 90 + off; x = 130 - int((1 - c) * 50); d.ellipse((x, y - 14, x + 28, y + 14), fill=col + (int(255 * c),)); txt(d, (x + 52, y), line, BK(50), col, c, "lm")
    else:                                                          # end card
        a = k(END, .4); ov = Image.new("RGBA", (1080, 1920), (6, 7, 16, int(200 * a))); im.alpha_composite(ov); d = ImageDraw.Draw(im)
        txt(d, (540, 520), "FULL SHOWDOWN", BI(96), CYAN, a, "mm", 6); txt(d, (540, 620), "ON THE CHANNEL", BI(96), CYAN, a, "mm", 6)
        b = k(END + .5, .35); txt(d, (540, 800), "COMMENT", BK(80), WHITE, b, "mm", 5)
        rr(d, (330, 870, 750, 1010), 30, fill=PINK + (int(255 * b),)); txt(d, (540, 940), "GAME", BK(100), INK, b, "mm")
        txt(d, (540, 1080), "FOR THE PROMPT", BK(64), WHITE, b, "mm", 5)
        c = k(END + 1.1, .35); txt(d, (540, 1250), "Follow for the next one", BD(54), PINK, c, "mm", 4)
    return im

def main(voice, out, w=1080, h=1920):
    x = pcm(voice); env = envelope(x); tmp = tempfile.mkdtemp(); N = int(DUR * FPS); states = []
    for i in range(N):
        t = i / FPS; shot, dt = shot_at(t)
        s = {"t": t, "shot": [shot], "drift": [0, 0, -dt * (10 if shot == "wide" else 6)], "bitLevel": 0, "glLevel": 0, "speaker": None, "glExpr": "smirk"}
        k = min(i, len(env) - 1)
        for (a, b, who) in LINES:
            if a - 0.05 <= t <= b + 0.1:
                lv = float(env[k]) if i < len(env) else 0
                if who == "B": s["bitLevel"] = lv; s["speaker"] = "bit"
                else: s["glLevel"] = lv; s["speaker"] = "glitch"
        if 49.5 <= t < 51.5: s["glExpr"] = "neutral"
        for (a, b, who, text) in CAPS:
            if a <= t < b: s["caption"] = {"who": "BIT" if who == "B" else "GLITCH", "text": text, "o": 1}
        states.append(s)
    sj = os.path.join(tmp, "s.json"); json.dump(states, open(sj, "w")); raw = os.path.join(tmp, "studio.mp4")
    subprocess.run(["node", os.path.join(HERE, "studio/render.js"), sj, raw, str(w), str(h)], check=True)
    # HUD pass
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", raw, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    vid = os.path.join(tmp, "hud.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", vid], stdin=subprocess.PIPE)
    for i in range(N):
        buf = dec.stdout.read(w * h * 3)
        if len(buf) < w * h * 3: break
        fr = Image.frombuffer("RGB", (w, h), buf).convert("RGBA"); H = hud(i / FPS)
        if (w, h) != (1080, 1920): H = H.resize((w, h))
        fr.alpha_composite(H); enc.stdin.write(fr.convert("RGB").tobytes())
    enc.stdin.close(); enc.wait(); dec.wait()
    # audio: voice + ducked lo-fi bed + UI pops
    n = int(DUR * SR); tt = np.arange(n) / SR; v = pcm(voice); mix = np.zeros(n); mix[:len(v)] += v[:n] * 0.95
    noise = np.random.default_rng(9).uniform(-1, 1, n)
    def dec_(s0, d): e = np.zeros(n); i0 = int(s0 * SR); e[i0:] = np.exp(-np.arange(n - i0) / SR / d) if i0 < n else 0; return e
    beat = 60 / 85; chords = [(220, 261.6, 329.6), (174.6, 220, 261.6), (196, 246.9, 293.7), (164.8, 207.7, 246.9)]; bed = np.zeros(n)
    for kk in range(int(DUR / (beat * 4)) + 1):
        for f in chords[kk % 4]: bed += 0.05 * np.sin(2 * np.pi * f * tt) * dec_(kk * beat * 4, 2.5) * (tt >= kk * beat * 4)
    for kk in range(int(DUR / beat)):
        s0 = kk * beat; fr_ = 55 * 2 ** (-np.clip((tt - s0) * 30, 0, 3)); bed += 0.18 * np.sin(2 * np.pi * np.cumsum(fr_) / SR) * dec_(s0, .08) * (tt >= s0); bed += .035 * noise * dec_(s0 + beat / 2, .02) * (tt >= s0 + beat / 2)
    env_v = np.convolve(np.abs(np.pad(v, (0, max(0, n - len(v))))[:n]), np.ones(6000) / 6000, mode="same"); duck = 1 - 0.65 * np.clip(env_v / (env_v.max() * 0.25), 0, 1)
    mix += bed * duck
    for s0 in (0.15, 7.72, 8.98, 10.15, 12.1, 14.31, 16.98, 23.87, 26.2, 27.87, 30.9, 36.4, 43.09, 44.99, 46.71, END + .5):
        mix += 0.10 * np.sin(2 * np.pi * 880 * tt) * dec_(s0, .05) * (tt >= s0) + 0.06 * np.sin(2 * np.pi * 1320 * tt) * dec_(s0, .04) * (tt >= s0)
    f2 = 70 * 2 ** (-np.clip((tt - 42.24) * 25, 0, 2)); mix += 0.5 * np.sin(2 * np.pi * np.cumsum(f2) / SR) * dec_(42.24, .15) * (tt >= 42.24) + 0.15 * noise * dec_(42.24, .05) * (tt >= 42.24)  # REAL stamp
    for s0 in (11.9, 22.5, 41.0): mix += 0.06 * noise * dec_(s0, .15) * (tt >= s0)   # whooshes between parts
    mix = mix / np.max(np.abs(mix)) * 0.89; wav = os.path.join(tmp, "a.wav")
    with wave.open(wav, "w") as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((mix * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True); print(out)

if __name__ == "__main__":
    a = sys.argv[1:]; main(a[0], a[1], *(int(v) for v in a[2:4]))
