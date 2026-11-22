"""Ask Bit episode 2: 'Do AI skills actually make Claude better?' (1080x1920, 30 fps).
Same studio and look as episode 1 (studio/render.js + PIL HUD). The two ElevenLabs takes (one per voice) are split
on their long pauses, re-assembled in script order, and every caption/HUD cue is timed from that assembled track.
Usage: python3 build_ep02.py BIT.mp3 GLITCH.mp3 OUT.mp4 [w h]"""
import json, os, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..", "..")
sys.path.insert(0, HERE)
from build_coming_soon import pcm, envelope, FPS  # noqa: E402
from build_ep01 import BK, BI, BD, PINK, LIME, CYAN, WHITE, RED, GOLD, INK, ease, rr, chip, panel, txt, paste_card  # noqa: E402
SR = 44100
GREEN = (40, 220, 120)

# segments (start, end) in each take, from silencedetect at -40 dB (long pauses ~1 s between lines)
BIT_SEG = [(0.00, 7.05), (8.73, 13.88), (14.93, 15.89), (16.87, 26.86), (27.81, 33.36), (34.32, 45.35), (46.29, 50.13)]
GL_SEG = [(0.00, 4.43), (5.57, 7.60), (8.72, 11.34), (12.64, 13.99), (15.25, 17.40)]
# script order: (speaker, take index, gap before, caption chunks)
SCRIPT = [
    ("G", 0, 0.10, ["Bit. Everyone's installing AI skills.", "Do they actually make Claude better?"]),
    ("B", 0, 0.40, ["Let's check. Three parts.", "What people say. What we tried. And is it real."]),
    ("B", 1, 0.40, ["What people say: install a skill pack,", "and Claude codes like a pro game studio."]),
    ("G", 1, 0.15, ["So I install them… and I'm done?"]),
    ("B", 2, 0.15, ["That's the claim."]),
    ("B", 3, 0.40, ["What we tried: the same maze game prompt, three times.", "Claude on its own took twenty-seven minutes.", "With seventy-nine skills installed… twelve."]),
    ("G", 2, 0.15, ["Twelve minutes. Skills win. Next."]),
    ("B", 4, 0.15, ["I asked which skills it used. None.", "It said it should probably have checked them first."]),
    ("G", 3, 0.60, ["…Relatable."]),
    ("B", 5, 0.40, ["Is it real? Only if you ask.", "One extra line, \"use the skills\",", "and it loaded four, needed one fix round…", "and its tester won with two lives to spare."]),
    ("G", 4, 0.20, ["So skills make me a pro?"]),
    ("B", 6, 0.15, ["Skills make Claude a pro.", "You just have to tell it."]),
]

def pauses(x, s0, min_len=0.12, db=-38):
    """Internal pauses (start, end), in seconds on the assembled track, inside one line: 10 ms RMS under -38 dBFS for 0.12 s+."""
    hop = SR // 100; thr = 10 ** (db / 20)
    r = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x) - hop, hop)]); quiet = r < thr; out = []; i = 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]: j += 1
            if (j - i) / 100 >= min_len and i > 0 and j < len(quiet): out.append((s0 + i / 100, s0 + j / 100))
            i = j
        else: i += 1
    return out

def assemble(bit, gl):
    b, g = pcm(bit), pcm(gl); parts, lines, t = [], [], 0.0
    for who, idx, gap, chunks in SCRIPT:
        a, e = (BIT_SEG if who == "B" else GL_SEG)[idx]; seg = (b if who == "B" else g)[int(max(0, a - .03) * SR):int((e + .05) * SR)]
        # trim residual silence at both ends
        lv = np.abs(seg) > 0.01; nz = np.nonzero(lv)[0]; seg = seg[max(0, nz[0] - 600):min(len(seg), nz[-1] + 1500)] if len(nz) else seg
        parts.append(np.zeros(int(gap * SR))); t += gap; s0 = t; parts.append(seg); t += len(seg) / SR
        lines.append({"who": who, "s": s0, "e": t, "chunks": chunks, "pauses": pauses(seg, s0)})
    return np.concatenate(parts), lines

# word boundaries measured on the assembled track (silencedetect -38 dB, 0.12 s); these win over the estimate
PINNED = {"And is it real.": 10.32, "and Claude codes": 15.07, "None.": 36.58, "It said": 37.50, "Only if you ask.": 43.73, "One extra line": 45.16,
          "and it loaded four": 46.80, "needed one fix round": 48.02, "and its tester won": 49.25, "You just have to tell it.": 57.99,
          "It said it should probably have checked them first.": 37.50, "and it loaded four, needed one fix round…": 46.80,
          "and its tester won with two lives to spare.": 49.25}

def at(L, phrase, line, after=-1.0):
    """Time a phrase starts inside a line: proportional to characters, snapped to the end of the nearest internal pause
    (never earlier than `after` + 0.4 s, so consecutive phrases can't share a pause)."""
    full = " ".join(L[line]["chunks"]); k = full.find(phrase); assert k >= 0, phrase
    if phrase in PINNED: return PINNED[phrase]
    s, e = L[line]["s"], L[line]["e"]; ps = L[line]["pauses"]
    speech, cur = [], s                                                   # spread characters over speaking time only
    for a, b in ps: speech.append((cur, a)); cur = b
    speech.append((cur, e)); total = sum(b - a for a, b in speech); want = total * k / len(full); est = e
    for a, b in speech:
        if want <= b - a: est = a + want; break
        want -= b - a
    est = max(est, after + 0.4)
    if k == 0: return s
    cands = [p[1] for p in L[line]["pauses"] if abs(p[1] - est) < 0.9 and p[1] > after + 0.4]
    return min(cands, key=lambda c: abs(c - est)) if cands else est

def captions(L):
    caps = []
    for i, l in enumerate(L):
        starts = []
        for c in l["chunks"]: starts.append(at(L, c, i, starts[-1] if starts else -1.0))
        starts.append(l["e"] + 0.15)
        for j, c in enumerate(l["chunks"]): caps.append((starts[j], starts[j + 1], l["who"], c))
    return caps

CARD = {k: Image.open(os.path.join(ROOT, f"brand/thumbnails/src/pacbit_{k}.jpg")).convert("RGB").resize((380, 380)) for k in ("run1", "run2", "run3")}

def stamp(im, text, cx, cy, a, col, size=96, rot=-8, w=None):
    if a <= 0: return
    s = 1.6 - 0.6 * a; f = BK(size); tw = int(ImageDraw.Draw(im).textlength(text, font=f)) + 70; w = w or tw
    st = Image.new("RGBA", (w, size + 70), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
    rr(sd, (8, 8, w - 8, size + 62), 20, outline=col + (255,), width=12); sd.text((w // 2, (size + 70) // 2), text, font=f, fill=col + (255,), anchor="mm")
    st = st.resize((int(st.width * s), int(st.height * s))).rotate(rot, expand=True, resample=Image.BICUBIC)
    st.putalpha(st.getchannel("A").point(lambda v: int(v * a))); im.alpha_composite(st, (int(cx - st.width / 2), int(cy - st.height / 2)))

def make_hud(L, END):
    T = {  # every cue, from the voice
        "list1": at(L, "What people say.", 1), "list2": at(L, "What we tried.", 1), "list3": at(L, "And is it real.", 1),
        "p1": L[2]["s"], "pack": at(L, "install a skill pack", 2), "pro": at(L, "and Claude codes", 2), "next1": L[4]["s"],
        "p2": L[5]["s"], "run1": at(L, "Claude on its own", 5), "run2": at(L, "With seventy-nine", 5), "g3": L[6]["s"], "g3e": L[6]["e"],
        "none": at(L, "None.", 7), "quote": None, "next2": L[8]["e"] - 0.2,
        "p3": L[9]["s"], "ask": at(L, "Only if you ask.", 9), "line": at(L, "One extra line", 9), "four": at(L, "and it loaded four", 9),
        "lives": at(L, "and its tester won", 9),
    }
    T["quote"] = at(L, "It said", 7, T["none"]); T["line"] = at(L, "One extra line", 9, T["ask"])
    T["four"] = at(L, "and it loaded four", 9, T["line"]); T["fix"] = at(L, "needed one fix round", 9, T["four"])
    T["lives"] = at(L, "and its tester won", 9, T["fix"])
    def hud(t):
        im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        k = lambda s0, dur=0.3: ease((t - s0) / dur)
        if t < L[1]["s"] - 0.1:                                           # hook tag
            a = k(0.15); chip(im, "DO AI SKILLS WORK?", 150 - int((1 - a) * 40), PINK, a, 64)
        elif t < T["p1"] - 0.1:                                           # 3 parts
            a = k(L[1]["s"]); chip(im, "3 SIMPLE PARTS", 130, CYAN, a); off = panel(im, a, 250, 650)
            for i, (s0, label, col) in enumerate([(T["list1"], "WHAT PEOPLE SAY", WHITE), (T["list2"], "WHAT WE TRIED", WHITE), (T["list3"], "IS IT REAL?", GOLD)]):
                b = k(s0, .25); y = 330 + i * 105 + off
                if b <= 0: continue
                x = 140 - int((1 - b) * 60)
                if i == 2: rr(d, (x, y - 4, x + 40, y + 34), 7, fill=GOLD + (int(255 * b),)); d.arc((x + 5, y - 30, x + 35, y + 6), 180, 360, fill=GOLD + (int(255 * b),), width=7)
                else: d.ellipse((x + 6, y + 2, x + 34, y + 30), fill=PINK + (int(255 * b),))
                txt(d, (x + 70, y + 16), label, BK(62), col, b, "lm")
        elif t < T["p2"] - 0.1:                                           # what people say
            a = k(T["p1"]); chip(im, "WHAT PEOPLE SAY", 130, CYAN, a); off = panel(im, a, 250, 800)
            b = k(T["pack"], .3)
            if b > 0:                                                     # skill pack box with skill chips
                rr(d, (120, 300 + off, 560, 640 + off), 24, fill=(24, 28, 50, int(255 * b)), outline=LIME + (int(255 * b),), width=4)
                txt(d, (340, 350 + off), "79 SKILLS", BK(62), LIME, b, "mm")
                for j, sk in enumerate(["GAME AI", "GAME FEEL", "CONTROLS", "AUDIO", "LEVEL DESIGN"]):
                    c = k(T["pack"] + 0.15 + j * 0.12, .2)
                    if c > 0:
                        yy = 396 + j * 47 + off; rr(d, (150, yy, 530, yy + 41), 12, fill=(40, 46, 80, int(255 * c))); txt(d, (340, yy + 21), sk, BD(32), WHITE, c, "mm")
                txt(d, (340, 670 + off), "one command each", BD(34), (180, 190, 220), b, "mm")
            c = k(T["pro"], .35)
            if c > 0:
                txt(d, (640, 470 + off), "→", BK(90), CYAN, c, "mm")
                cx, cy = 830, 430 + off; r = 70                                # trophy
                d.pieslice((cx - r, cy - r - 20, cx + r, cy + r - 20), 0, 180, fill=GOLD + (int(255 * c),)); rr(d, (cx - r, cy - 26, cx + r, cy), 6, fill=GOLD + (int(255 * c),))
                d.arc((cx - r - 34, cy - 20, cx - r + 14, cy + 30), 90, 270, fill=GOLD + (int(255 * c),), width=10); d.arc((cx + r - 14, cy - 20, cx + r + 34, cy + 30), 270, 90, fill=GOLD + (int(255 * c),), width=10)
                rr(d, (cx - 14, cy + 48, cx + 14, cy + 90), 4, fill=GOLD + (int(255 * c),)); rr(d, (cx - 56, cy + 88, cx + 56, cy + 112), 8, fill=GOLD + (int(255 * c),))
                txt(d, (830, 600 + off), "PRO GAME", BK(52), WHITE, c, "mm"); txt(d, (830, 660 + off), "STUDIO", BK(52), WHITE, c, "mm")
            if t >= T["next1"]: chip(im, "UP NEXT: WHAT WE TRIED", 840, PINK, k(T["next1"], .25), 40)
        elif t < T["p3"] - 0.1:                                           # what we tried
            a = k(T["p2"]); chip(im, "WHAT WE TRIED", 130, CYAN, a); off = panel(im, a, 250, 960)
            b = k(T["p2"] + 0.3, .35); txt(d, (540, 300 + off), "SAME PROMPT · 3 RUNS", BD(44), WHITE, b, "mm")
            pulse = 0.5 + 0.5 * np.sin((t - T["g3"]) * 8) if T["g3"] <= t < T["g3e"] else 0
            paste_card(im, CARD["run1"], 100, 360 + off, k(T["run1"], .3), "RUN 1 · ALONE · 27:43", k(T["run1"] + .3, .25))
            paste_card(im, CARD["run2"], 600, 360 + off, k(T["run2"], .3), "RUN 2 · SKILLS · 12:50", k(T["run2"] + .3, .25), LIME, 0, pulse)
            c = k(T["none"], .18)
            if c > 0:
                st = Image.new("RGBA", (440, 200), (0, 0, 0, 0)); sd = ImageDraw.Draw(st); s = 1.6 - 0.6 * c
                rr(sd, (8, 8, 432, 192), 20, fill=(40, 6, 14, 235), outline=RED + (255,), width=12)
                sd.text((220, 62), "SKILLS USED", font=BK(44), fill=RED + (255,), anchor="mm"); sd.text((220, 136), "0", font=BK(110), fill=RED + (255,), anchor="mm")
                st = st.resize((int(440 * s), int(200 * s))).rotate(-7, expand=True, resample=Image.BICUBIC); st.putalpha(st.getchannel("A").point(lambda v: int(v * c)))
                im.alpha_composite(st, (790 - st.width // 2, 560 + off - st.height // 2))
            e = k(T["quote"], .3)
            if e > 0:
                rr(d, (110, 790 + off, 970, 925 + off), 26, fill=(255, 255, 255, int(240 * e)))
                d.polygon([(780, 790 + off), (850, 790 + off), (830, 760 + off)], fill=(255, 255, 255, int(240 * e)))
                txt(d, (540, 845 + off), "“I should probably have", BI(48), INK, e, "mm"); txt(d, (540, 900 + off), "checked them first.”", BI(48), INK, e, "mm")
            if t >= T["next2"]: chip(im, "UP NEXT: IS IT REAL?", 985, PINK, k(T["next2"], .25), 40)
        elif t < END:                                                     # fact check
            a = k(T["p3"]); chip(im, "FACT CHECK", 130, GOLD, a); off = panel(im, a, 250, 930)
            stamp(im, "ONLY IF YOU ASK", 540, 370 + off, k(T["ask"], .18), GREEN, 76)
            b = k(T["line"], .3)
            if b > 0:
                sm = CARD["run3"].resize((300, 300)); g = sm.convert("RGBA"); m = Image.new("L", g.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 299, 299), 22, fill=int(255 * b)); g.putalpha(m)
                im.alpha_composite(g, (110, 500 + off)); rr(d, (110, 500 + off, 410, 800 + off), 22, outline=GREEN + (int(255 * b),), width=5)
                rr(d, (124, 740 + off, 396, 790 + off), 14, fill=(10, 12, 26, int(230 * b))); txt(d, (260, 765 + off), "RUN 3 · 15:12", BK(34), GREEN, b, "mm")
            for i, (s0, line, col) in enumerate([(T["line"] + 0.35, "+1 prompt line", WHITE), (T["four"], "4 skills used", LIME), (T["fix"], "1 fix round", WHITE), (T["lives"], "2 lives spare", GOLD)]):
                c = k(s0, .25)
                if c <= 0: continue
                y = 530 + i * 82 + off; x = 450 - int((1 - c) * 40); d.ellipse((x, y - 13, x + 26, y + 13), fill=col + (int(255 * c),)); txt(d, (x + 44, y), line, BK(44), col, c, "lm")
            if t >= T["lives"] + 1.0:
                c = k(T["lives"] + 1.0, .3); txt(d, (540, 880 + off), "Installed ≠ used", BK(54), PINK, c, "mm", 4)
        else:                                                             # end card
            a = k(END, .4); ov = Image.new("RGBA", (1080, 1920), (6, 7, 16, int(200 * a))); im.alpha_composite(ov); d = ImageDraw.Draw(im)
            txt(d, (540, 520), "FULL TEST", BI(104), CYAN, a, "mm", 6); txt(d, (540, 625), "ON THE CHANNEL", BI(96), CYAN, a, "mm", 6)
            b = k(END + .5, .35); txt(d, (540, 800), "COMMENT", BK(80), WHITE, b, "mm", 5)
            rr(d, (290, 870, 790, 1010), 30, fill=LIME + (int(255 * b),)); txt(d, (540, 940), "SKILLS", BK(100), INK, b, "mm")
            txt(d, (540, 1080), "FOR THE PROMPT", BK(64), WHITE, b, "mm", 5)
            c = k(END + 1.1, .35); txt(d, (540, 1230), "Follow for the next one", BD(50), PINK, c, "mm", 4)
        return im
    return hud, T

def main(bit, gl, out, w=1080, h=1920):
    voice, L = assemble(bit, gl); END = L[-1]["e"] + 0.35; DUR = END + 4.2; CAPS = captions(L)
    tmp = tempfile.mkdtemp(); vwav = os.path.join(tmp, "voice.wav")
    with wave.open(vwav, "w") as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((np.clip(voice, -1, 1) * 32767).astype(np.int16).tobytes())
    hud, T = make_hud(L, END)
    json.dump({"lines": [{k: v for k, v in l.items() if k != "pauses"} for l in L], "captions": CAPS, "cues": T, "end": END}, open(os.path.join(HERE, "out", "ep02_timeline.json"), "w"), indent=1)
    shots = [(0, "glitch")] + [(l["s"] - 0.1, {"G": "glitch", "B": "bit"}[l["who"]]) for l in L[1:]]
    for i in (2, 5, 9): shots[i] = (shots[i][0], "wide")                  # the three part openers go wide
    shots.append((END, "wide"))
    def shot_at(t):
        cur, t0 = shots[0][1], 0
        for s, name in shots:
            if t >= s: cur, t0 = name, s
        return cur, t - t0
    env = envelope(voice); N = int(DUR * FPS); states = []
    for i in range(N):
        t = i / FPS; shot, dt = shot_at(t)
        s = {"t": t, "shot": [shot], "drift": [0, 0, -dt * (10 if shot == "wide" else 6)], "bitLevel": 0, "glLevel": 0, "speaker": None, "glExpr": "smirk"}
        lv = float(env[min(i, len(env) - 1)]) if i < len(env) else 0
        for l in L:
            if l["s"] - 0.05 <= t <= l["e"] + 0.1:
                if l["who"] == "B": s["bitLevel"] = lv; s["speaker"] = "bit"
                else: s["glLevel"] = lv; s["speaker"] = "glitch"
        if L[10]["s"] - 0.1 <= t < L[11]["s"]: s["glExpr"] = "neutral"
        if t >= L[11]["s"]: s["bitExpr"] = "happy"
        elif T["none"] <= t < L[7]["e"]: s["bitExpr"] = "smug"
        for (a, b, who, text) in CAPS:
            if a <= t < b: s["caption"] = {"who": "BIT" if who == "B" else "GLITCH", "text": text, "o": 1}
        states.append(s)
    sj = os.path.join(tmp, "s.json"); json.dump(states, open(sj, "w")); raw = os.path.join(tmp, "studio.mp4")
    subprocess.run(["node", os.path.join(HERE, "studio/render.js"), sj, raw, str(w), str(h)], check=True)
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
    # audio: voice + ducked lo-fi bed + UI pops + stamps (same recipe as ep 1)
    n = int(DUR * SR); tt = np.arange(n) / SR; v = voice; mix = np.zeros(n); mix[:min(n, len(v))] += v[:n] * 0.95
    noise = np.random.default_rng(9).uniform(-1, 1, n)
    def dec_(s0, d): e = np.zeros(n); i0 = int(s0 * SR); e[i0:] = np.exp(-np.arange(n - i0) / SR / d) if i0 < n else 0; return e
    beat = 60 / 85; chords = [(220, 261.6, 329.6), (174.6, 220, 261.6), (196, 246.9, 293.7), (164.8, 207.7, 246.9)]; bed = np.zeros(n)
    for kk in range(int(DUR / (beat * 4)) + 1):
        for f in chords[kk % 4]: bed += 0.05 * np.sin(2 * np.pi * f * tt) * dec_(kk * beat * 4, 2.5) * (tt >= kk * beat * 4)
    for kk in range(int(DUR / beat)):
        s0 = kk * beat; fr_ = 55 * 2 ** (-np.clip((tt - s0) * 30, 0, 3)); bed += 0.18 * np.sin(2 * np.pi * np.cumsum(fr_) / SR) * dec_(s0, .08) * (tt >= s0); bed += .035 * noise * dec_(s0 + beat / 2, .02) * (tt >= s0 + beat / 2)
    env_v = np.convolve(np.abs(np.pad(v, (0, max(0, n - len(v))))[:n]), np.ones(6000) / 6000, mode="same"); duck = 1 - 0.65 * np.clip(env_v / (env_v.max() * 0.25), 0, 1)
    mix += bed * duck
    for s0 in (0.15, T["list1"], T["list2"], T["list3"], T["pack"], T["pro"], T["run1"], T["run2"], T["quote"], T["line"], T["four"], T["fix"], T["lives"], END + .5):
        mix += 0.10 * np.sin(2 * np.pi * 880 * tt) * dec_(s0, .05) * (tt >= s0) + 0.06 * np.sin(2 * np.pi * 1320 * tt) * dec_(s0, .04) * (tt >= s0)
    for s0 in (T["none"], T["ask"]):                                     # stamps
        f2 = 70 * 2 ** (-np.clip((tt - s0) * 25, 0, 2)); mix += 0.5 * np.sin(2 * np.pi * np.cumsum(f2) / SR) * dec_(s0, .15) * (tt >= s0) + 0.15 * noise * dec_(s0, .05) * (tt >= s0)
    for s0 in (T["p1"] - .1, T["p2"] - .1, T["p3"] - .1): mix += 0.06 * noise * dec_(s0, .15) * (tt >= s0)
    mix = mix / np.max(np.abs(mix)) * 0.89; wav = os.path.join(tmp, "a.wav")
    with wave.open(wav, "w") as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((mix * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.5", "-shortest", out], check=True); print(out)

if __name__ == "__main__":
    a = sys.argv[1:]; main(a[0], a[1], a[2], *(int(v) for v in a[3:5]))
