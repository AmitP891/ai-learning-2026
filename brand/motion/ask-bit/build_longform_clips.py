"""Long-form brand clips from the 3D studio (1920x1080, 30 fps):
  sting  - 3 s: 'VIBE WITH AMIT' neon flickers on, Bit's eyes light up, camera pulls back. Goes right after the cold-open hook.
  outro  - 15 s: end-screen layout (WATCH NEXT box left, SUBSCRIBE circle), Bit: 'Thanks for watching. This one's next.'
           Glitch: 'Or don't. Your loss.'  Put YouTube's end-screen elements over the box and circle (last 15 s).
Usage: python3 build_longform_clips.py sting OUT.mp4
       python3 build_longform_clips.py outro OUT.mp4 BIT.mp3 GLITCH.mp3"""
import json, os, subprocess, sys, tempfile, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_coming_soon import pcm, envelope, FPS  # noqa: E402
HERE = os.path.dirname(os.path.abspath(__file__)); SR = 44100

def render(states, w=1920, h=1080):
    tmp = tempfile.mkdtemp(); sj = os.path.join(tmp, "s.json"); json.dump(states, open(sj, "w")); vid = os.path.join(tmp, "v.mp4")
    env = dict(os.environ, QS="sign=VIBE%20WITH%20AMIT")
    subprocess.run(["node", os.path.join(HERE, "studio/render.js"), sj, vid, str(w), str(h)], check=True, env=env); return vid

def write_wav(x, path):
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.89
    with wave.open(path, "w") as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((x * 32767).astype(np.int16).tobytes())

def decay(n, s0, d):
    e = np.zeros(n); i0 = int(s0 * SR)
    if i0 < n: e[i0:] = np.exp(-np.arange(n - i0) / SR / d)
    return e

def mux(vid, wav, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True); print(out)

def sting(out):
    D = 3.0; N = int(D * FPS); st = []
    for i in range(N):
        t = i / FPS
        sg = 0 if t < 0.3 else ([0.3, 0, 0.9, 0.2, 1, 0.6, 1][int((t - 0.3) * 9) % 7] if t < 1.05 else 1)
        k = min(1, max(0, (t - 0.9) / 1.6))
        st.append({"t": t, "shot": ["lsign", "lwide", k], "drift": [0, 0, -t * 6], "sign": sg, "eyes": min(1, max(0, (t - 1.35) / 0.25)), "speaker": None})
    vid = render(st)
    n = int(D * SR); t = np.arange(n) / SR; noise = np.random.default_rng(2).uniform(-1, 1, n); x = np.zeros(n)
    for s0 in (0.3, 0.42, 0.55, 0.7, 0.85): x += 0.18 * noise * decay(n, s0, 0.02) * (t >= s0)      # neon buzz
    x += 0.10 * np.sin(2 * np.pi * 120 * t) * (t > 1.05) * np.clip((t - 1.05) * 4, 0, 1) * np.clip((3 - t) * 2, 0, 1)  # neon hum
    f = 60 * 2 ** (-np.clip((t - 1.35) * 20, 0, 2.5)); x += 0.8 * np.sin(2 * np.pi * np.cumsum(f) / SR) * decay(n, 1.35, 0.25) * (t >= 1.35)  # bass hit on eyes
    for fr, a in ((659.3, .22), (987.8, .16), (1318.5, .1)): x += a * np.sin(2 * np.pi * fr * t) * decay(n, 1.4, 0.7) * (t >= 1.4)  # chime
    tmp = tempfile.mkdtemp(); wav = os.path.join(tmp, "a.wav"); write_wav(x, wav); mux(vid, wav, out)

def outro(out, bit_mp3, gl_mp3):
    D = 15.0; N = int(D * FPS); b = pcm(bit_mp3); g = pcm(gl_mp3); eb, eg = envelope(b), envelope(g); B0, G0 = 1.0, 3.9
    st = []
    for i in range(N):
        t = i / FPS; s = {"t": t, "shot": ["lend"], "drift": [np.sin(t * .25) * 6, 0, -t * 1.5], "es": min(1, t / 0.4), "speaker": None, "glExpr": "smirk"}
        kb, kg = int((t - B0) * FPS), int((t - G0) * FPS)
        if 0 <= kb < len(eb): s["bitLevel"] = float(eb[kb]); s["speaker"] = "bit"
        if 0 <= kg < len(eg): s["glLevel"] = float(eg[kg]); s["speaker"] = "glitch"
        if B0 + 1.35 <= t < G0 + 0.2: s["bitTurn"] = -0.5                    # Bit looks at the WATCH NEXT box on "This one's next"
        st.append(s)
    vid = render(st)
    n = int(D * SR); t = np.arange(n) / SR; x = np.zeros(n); noise = np.random.default_rng(3).uniform(-1, 1, n)
    beat = 60 / 85; chords = [(220, 261.6, 329.6), (174.6, 220, 261.6), (196, 246.9, 293.7), (164.8, 207.7, 246.9)]; bed = np.zeros(n)
    for k in range(int(D / (beat * 4)) + 1):
        for f in chords[k % 4]: bed += 0.06 * np.sin(2 * np.pi * f * t) * decay(n, k * beat * 4, 2.5) * (t >= k * beat * 4)
    for k in range(int(D / beat)):
        s0 = k * beat; fr = 55 * 2 ** (-np.clip((t - s0) * 30, 0, 3))
        bed += 0.22 * np.sin(2 * np.pi * np.cumsum(fr) / SR) * decay(n, s0, 0.08) * (t >= s0); bed += 0.04 * noise * decay(n, s0 + beat / 2, 0.02) * (t >= s0 + beat / 2)
    duck = np.ones(n)
    for v, s0 in ((b, B0), (g, G0)):
        i0 = int(s0 * SR); x[i0:i0 + len(v)] += v * 0.9; duck[max(0, i0 - 2000):i0 + len(v) + 4000] = 0.4
    duck = np.convolve(duck, np.ones(4000) / 4000, mode="same")
    x += bed * duck * np.clip((D - t) / 2.5, 0, 1)                         # fade the bed out over the last 2.5 s
    tmp = tempfile.mkdtemp(); wav = os.path.join(tmp, "a.wav"); write_wav(x, wav); mux(vid, wav, out)

if __name__ == "__main__":
    if sys.argv[1] == "sting": sting(sys.argv[2])
    else: outro(sys.argv[2], sys.argv[3], sys.argv[4])
