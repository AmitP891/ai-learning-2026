#!/usr/bin/env python3
"""9 s 'Level 1 · tomorrow 6pm' story (Instagram / TikTok), built from the Level 1 game's own
sprites, fog, pixel fonts and chiptune so it matches the teaser.

    python build_story_countdown.py      ->  out/story_countdown_9x16.mp4

Beats: fog rolls in -> Professor Vague rises and laughs -> Bit drops in -> VS -> charge -> end card.
Text stays between y 280 and 1600 (story top bar and reply bar)."""
import math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw
import build as G

G.use_layout("9x16")
W, H, PX, FPS = G.W, G.H, G.PX, 30
DUR = 9.0; N = int(DUR * FPS)
ease, clamp, ptext, fit, blit = G.ease, G.clamp, G.ptext, G.fit, G.blit
GROUND, GW, BIT_H = G.GROUND, G.GW, G.BIT_H

# timeline (s)
T_FOG, T_RISE, T_LAUGH, T_DROP, T_LAND, T_VS, T_CHARGE, T_END = 0.0, 1.0, 2.2, 3.4, 3.8, 4.4, 4.9, 6.2


def fog(t):
    k = ease(t / 1.4) * (1 - 0.5 * clamp((t - T_END) / 0.6))
    yy, xx = np.mgrid[0:140, 0:GW].astype(np.float32)
    a = np.zeros_like(xx)
    for i in range(8):
        cx = (GW + 80) * (1 - k) + GW * (0.05 + 0.13 * i) + 10 * math.sin(t * 1.3 + i)
        cy = 80 + 12 * math.sin(t * 0.9 + i * 2.1)
        a += np.exp(-((xx - cx) ** 2 / (2 * 32 ** 2) + (yy - cy) ** 2 / (2 * 24 ** 2)))
    a = np.clip(a * 0.5, 0, 0.6) * k * np.clip(yy / 70, 0, 1)
    arr = np.zeros((140, GW, 4), np.uint8); arr[..., :3] = G.FOG; arr[..., 3] = G.dither_alpha(a)
    return Image.fromarray(arr)


def game(t, f):
    g = G.ARENA.copy(); d = ImageDraw.Draw(g)
    if t >= T_RISE:                                            # Professor rises out of the fog
        rise = ease((t - T_RISE) / 1.1)
        laughing = T_LAUGH <= t < T_LAUGH + 1.1
        mouth = (0.5 + 0.5 * abs(math.sin(t * 14))) if laughing else 0.0
        spr = G.prof_sprite("smug", t, mouth)
        w = round(640 * G.PK_S)
        shake = (1 if int(t * 16) % 2 else -1) if laughing else 0
        x = G.PROF_X - w // 2 + shake
        y = round(G.PROF_TOP + (1 - rise) * (G.LURK + 140) + 2 * math.sin(t * math.pi))
        if y < GROUND:
            g.alpha_composite(spr.crop((0, 0, spr.width, max(1, GROUND - y))), (x, y))
    g.alpha_composite(fog(t), (0, GROUND - 112))
    if t >= T_DROP:                                            # Bit drops in and lands
        u = clamp((t - T_DROP) / (T_LAND - T_DROP))
        y = -(1 - u ** 2) * 420
        sq = 1.0
        if t >= T_LAND: sq = 1 - 0.18 * math.exp(-(t - T_LAND) * 14) * math.cos((t - T_LAND) * 30)
        expr = "blink" if f % 75 in (60, 61, 62) else "determined"
        spr = G.bit_sprite("idle", expr)
        if sq != 1.0: spr = spr.resize((round(spr.width * (2 - sq)), round(spr.height * sq)), Image.NEAREST)
        bx, by = round(G.BIT_X - spr.width / 2), round(GROUND - spr.height + y)
        g.alpha_composite(spr, (bx, by))
        if T_CHARGE <= t < T_END:                               # charge sparks
            for i in range(8):
                a_ = t * 7 + i * math.pi / 4; rr = 48 - 22 * ((t - T_CHARGE) % 0.4) / 0.4
                cx, cy = bx + spr.width / 2 + math.cos(a_) * rr, by + spr.height / 2 + math.sin(a_) * rr
                d.rectangle((cx - 1, cy - 1, cx + 1, cy + 1), fill=G.CY if i % 2 else G.WH)
    return g


def slam(t, t0, dur=0.14):
    u = (t - t0) / dur
    return None if u < 0 else (1 + 0.6 * (1 - ease(u)) if u < 1 else 1.0)


def frame(f):
    t = f / FPS
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    g = game(t, f)
    sh = (0, 0)
    if T_LAND <= t < T_LAND + 0.25: sh = (0, 2 if int(t * 40) % 2 else -2)
    if T_END <= t < T_END + 0.3: sh = (2 if int(t * 40) % 2 else -2, 0)
    im.alpha_composite(G.scanlines(g.resize((W, H), Image.NEAREST)), (sh[0] * PX, sh[1] * PX))

    if t < T_RISE + 0.6 and int(t * 4) % 2 == 0:              # blinking warning
        blit(im, ptext("WARNING", 110, G.RD), W / 2, 420, "mm")
        blit(im, ptext("BOSS INCOMING", 72, G.WH), W / 2, 540, "mm")
    if T_LAUGH <= t < T_VS + 0.3:
        G.card(im, [("BOSS:", 72, G.RD, "mono"), ("PROFESSOR VAGUE", 96, G.WH, "title")], 330, G.PU, t, T_LAUGH)
    if T_VS <= t < T_END:
        sc = slam(t, T_VS)
        blit(im, fit("VS", 260, G.YL, 600, kind="title", px=5), W / 2, 900, "mm", sc)
    if T_CHARGE <= t < T_END:                                  # charge meter
        y0 = 330; d = ImageDraw.Draw(im)
        d.rectangle((40, y0, W - 40, y0 + 150), fill=(10, 12, 24), outline=G.CY, width=6)
        blit(im, ptext("REQUIREMENTS CHECK v2", 66, G.CY), W / 2, y0 + 14, "mt")
        fill = clamp((t - T_CHARGE) / (T_END - T_CHARGE - 0.1)); nseg = (W - 144) // 59
        for i in range(round(nseg * fill)):
            x = 72 + i * 59; d.rectangle((x, y0 + 82, x + 50, y0 + 126), fill=G.CY if i < nseg - 3 else G.YL)

    if t >= T_END:                                             # end card
        k = ease((t - T_END) / 0.25)
        G.plate(im, (24, 300, 1056, 1560), k)
        lines = [("LEVEL 1", 200, G.PK, "title", 470, 0.0), ("TOMORROW", 150, G.WH, "title", 760, 0.25),
                 ("6PM", 230, G.YL, "title", 1000, 0.5)]
        for s, size, col, kind, y, dt in lines:
            sc = slam(t, T_END + dt)
            if sc is not None: blit(im, fit(s, size, col, 900, kind=kind, px=5), W / 2, y, "mm", sc)
        if t >= T_END + 0.9:
            blit(im, ptext("YOUTUBE  TIKTOK  INSTAGRAM", 44, G.CY), W / 2, 1220, "mm")
            if int((t - T_END) * 3) % 2 == 0:
                blit(im, ptext("PRESS START", 80, G.WH), W / 2, 1360, "mm")
            blit(im, ptext("@vibewithamitai", 52, (215, 180, 255)), W / 2, 1480, "mm")
    return im.convert("RGB")


def mix():
    SR = G.SR; buf = np.zeros(int(DUR * SR) + SR, np.float32)
    m = G.music()
    seg = m[int(4.0 * SR): int(4.0 * SR) + int(DUR * SR)]        # bars 3-7 of the Level 1 chiptune
    fade = np.ones(len(seg), np.float32)
    fi = int(0.9 * SR); fade[:fi] = np.linspace(0, 1, fi) ** 2
    fo = int(0.8 * SR); fade[-fo:] = np.linspace(1, 0, fo)
    G.put(buf, 0.6, seg * fade, 0.75)
    for t, x, v in [(0.1, G.whoosh(), 0.7), (T_LAUGH, G.laugh(), 0.5), (T_DROP, G.whoosh(), 0.6),
                    (T_LAND, G.thump(), 0.9), (T_VS, G.crash(), 0.5), (T_VS, G.kick(), 0.8),
                    (T_CHARGE, G.charge(T_END - T_CHARGE), 0.25), (T_END, G.final_thump(), 0.9),
                    (T_END + 0.25, G.kick(), 0.6), (T_END + 0.5, G.crash(), 0.5), (T_END + 0.9, G.coin(), 0.45)]:
        G.put(buf, t, x, v)
    buf = buf[: int(DUR * SR)]
    return buf / max(1.0, np.abs(buf).max() / 0.9)


def main():
    out = G.OUT / "story_countdown_9x16.mp4"; wav = G.OUT / "story_mix.wav"
    pcm = (np.clip(mix(), -1, 1) * 32767).astype(np.int16)
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(G.SR); w.writeframes(np.repeat(pcm, 2).tobytes())
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-t", f"{DUR:.3f}", "-movflags", "+faststart",
                           str(out)], stdin=subprocess.PIPE)
    for f in range(N): ff.stdin.write(frame(f).tobytes())
    ff.stdin.close(); ff.wait(); wav.unlink()
    print(out)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "frames":
        for t in (0.6, 2.6, 4.6, 5.8, 8.0):
            frame(round(t * FPS)).save(G.OUT / f"story_{t:.1f}.png")
    else:
        main()
