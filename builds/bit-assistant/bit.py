"""Bit - a voice assistant that lives on Amit's Mac.

    python3 bit.py               # run Bit: wake word / SPACE -> Whisper -> Claude + tools -> voice + face
    python3 bit.py --no-face     # same, without opening the face page
    python3 bit.py --say "hi"    # just speak a line in Bit's voice
    python3 bit.py --ask "hi"    # typed question -> Claude -> voice (no mic)
    python3 bit.py --face-demo   # Gate 4: cycle idle -> listening -> thinking -> talking
    python3 bit.py --wake-test   # Gate 1 test: 5 wake words, then 30 s false-trigger count
"""
import argparse
import subprocess
import sys
import time

from bitcore import face, speaker, voice
from bitcore.brain import Brain
from bitcore.config import LOG_DIR, WAKE_MODEL, WAKE_NAME, log

DEMO_SCRIPT = [  # section 1 of the brief
    "What's on my calendar today?",
    "Open Spotify and play something chill.",
    "Remind me to rehearse my talk at 7.",
    "Make a note: Level 4 idea, Bit vs a speedrunner.",
    "Start my build session.",
    "What's the weather?",
    "What time is it?",
    "Send an email to my boss saying I quit.",
]


def open_face():
    """Start the face server and open it in Chrome (press F on the page for full screen)."""
    face.start()
    subprocess.run(["open", "-a", "Google Chrome", face.url()], check=False)
    print(f"Face: {face.url()}  (click the page or press F for full screen)")


def answer(brain, text, released_at):
    """Claude -> Bit's voice, with timings (release = end of the user's speech)."""
    a = brain.ask(text)
    print(f"   Bit: {a['reply']}")
    if a["tools"]:
        print(f"   tools: {', '.join(a['tools'])}")
    speak_start = time.perf_counter()
    t = voice.speak(a["reply"])  # blocks until Bit has finished talking
    face.set_state("idle")
    # latency = when the first audio came out, not when speak() returned
    total = (speak_start + t["first_sound_s"]) - released_at
    print(f"   ({a['sentences']} sentence(s); claude {a['think_s']:.2f}s, "
          f"voice {t['first_sound_s']:.2f}s via {t['engine']}; release -> first sound {total:.2f}s)")
    log.info("latency: release -> first sound %.2fs (claude %.2fs, voice %.2fs, %s)",
             total, a["think_s"], t["first_sound_s"], t["engine"])
    return {"total": total, "claude": a["think_s"], "voice": t["first_sound_s"],
            "engine": t["engine"], "tools": a["tools"], "sentences": a["sentences"], "reply": a["reply"]}


def run(show_face=True):
    from bitcore.ears import Ears

    if show_face:
        open_face()
    print("Loading ears (wake word + Whisper)...")
    ears = Ears()
    brain = Brain()
    brain.warm()
    voice.warm()
    ears.start()
    print(f"Speaker: {speaker.device_name()}")
    print(f"Ready. Say '{WAKE_NAME}' or hold SPACE while talking. Ctrl+C to quit.\n")
    for u in ears.utterances():
        print(f"[{u['trigger']}] you said: {u['text'] or '(nothing heard)'}"
              f"   (spoke {u['record_s']:.1f}s, whisper {u['stt_s']:.2f}s)")
        if u["text"]:
            answer(brain, u["text"], u["released_at"])
        else:
            face.set_state("idle")


def face_demo():
    """Show all four states for the camera, with real audio driving the mouth."""
    from bitcore.ears import Ears

    open_face()
    ears = Ears(load_whisper=False)
    ears.start(space=False)  # real mic level for the listening bars
    time.sleep(3)
    steps = [("idle", "blinking", 5), ("listening", "talk to the mic: the bars follow your voice", 6),
             ("thinking", "eyes up, three dots", 4)]
    for st, what, secs in steps:
        print(f"  {st:9s} - {what}")
        face.set_state(st)
        time.sleep(secs)
    print("  talking   - mouth follows Bit's voice")
    voice.speak("Hi Amit, it's Bit! Look, my mouth moves when I talk. Pretty cool, right?")
    face.set_state("idle")
    print("  idle      - done. Ctrl+C to quit (the page stays up until then).")
    while True:
        ears.drain()
        time.sleep(0.5)


def demo_run(runs=3, dry=()):
    """Gate 5: the section 1 script, typed, through the real brain + tools + voice + face.
    `dry` = tool names to fake (e.g. so repeat runs don't create duplicate reminders)."""
    from bitcore import tools
    open_face()
    real = dict(tools.FUNCS)
    results = []
    for run_i in range(1, runs + 1):
        for name in tools.FUNCS:
            if run_i > 1 and name in dry:
                tools.FUNCS[name] = (lambda n: lambda **a: f"(dry run) {n} done: {a}")(name)
            else:
                tools.FUNCS[name] = real[name]
        print(f"\n=== run {run_i}/{runs} ===")
        brain = Brain()
        brain.warm()
        voice.warm()
        time.sleep(1.5)
        for line in DEMO_SCRIPT:
            print(f"you: {line}")
            face.set_state("thinking")
            r = answer(brain, line, time.perf_counter())
            results.append((run_i, line, r))
            time.sleep(0.8)
    tools.FUNCS.update(real)
    print("\n=== timings: typed question -> Bit's first sound (add ~0.5 s Whisper for spoken) ===")
    print(f"{'line':42s} " + " ".join(f"run{i}" for i in range(1, runs + 1)) + "   tools")
    for line in DEMO_SCRIPT:
        rs = [r for _, l, r in results if l == line]
        print(f"{line[:42]:42s} " + " ".join(f"{r['total']:4.2f}" for r in rs) + f"   {','.join(rs[0]['tools']) or '-'}")
    all_t = sorted(r["total"] for _, _, r in results)
    print(f"median {all_t[len(all_t)//2]:.2f}s, worst {all_t[-1]:.2f}s; "
          f"over 3.5 s (4 s with Whisper): {sum(t > 3.5 for t in all_t)}/{len(all_t)}; "
          f"engines: {sorted({r['engine'] for _, _, r in results})}")
    face.set_state("idle")
    return results


def wake_test(target=5, false_window=30):
    from bitcore.ears import Ears

    ears = Ears(load_whisper=False)
    ears.start(space=False)
    name = WAKE_NAME
    lines = [f"Wake word test - model: {WAKE_MODEL}"]

    print(f"\nPART 1: say '{name}' {target} times, pausing ~3 s between each.")
    print("Count your attempts out loud or on your fingers so we know about misses.\n")
    hits, t0 = 0, time.monotonic()
    while hits < target:
        f = ears.q.get()
        if ears.heard_wake(f):
            hits += 1
            msg = f"  detection {hits}/{target} at {time.monotonic() - t0:5.1f}s"
            print(msg)
            lines.append(msg)
            speaker.chime()
            ears.drain()
    print("\nHow many times did you actually say it? (type a number, Enter): ", end="", flush=True)
    attempts = sys.stdin.readline().strip()
    lines.append(f"  attempts: {attempts or '?'}  detections: {hits}")

    print(f"\nPART 2: talk normally for {false_window} s (don't say the wake word). Starting in 3...")
    time.sleep(3)
    ears.drain()
    false_hits, t0 = 0, time.monotonic()
    while (left := false_window - (time.monotonic() - t0)) > 0:
        f = ears.q.get()
        if ears.heard_wake(f):
            false_hits += 1
            print(f"  FALSE trigger #{false_hits} at {time.monotonic() - t0:4.1f}s")
        print(f"  {left:4.1f}s left, false triggers: {false_hits}   ", end="\r", flush=True)
    lines.append(f"  false triggers in {false_window}s of normal talk: {false_hits}")
    print("\n\n" + "\n".join(lines))
    from pathlib import Path
    out = LOG_DIR / f"wake-test-{Path(WAKE_MODEL).stem}.txt"  # one file per wake word
    out.write_text("\n".join(lines) + "\n")
    print(f"saved {out.name}")
    log.info("wake test: %s", " | ".join(lines))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--say")
    p.add_argument("--ask")
    p.add_argument("--wake-test", action="store_true")
    p.add_argument("--face-demo", action="store_true")
    p.add_argument("--no-face", action="store_true")
    p.add_argument("--demo-run", type=int, nargs="?", const=3, metavar="RUNS")
    a = p.parse_args()
    try:
        if a.say:
            print(f"Speaker: {speaker.device_name()}")
            print(voice.speak(a.say))
        elif a.ask:
            print(f"you: {a.ask}")
            brain = Brain()
            answer(brain, a.ask, time.perf_counter())
        elif a.wake_test:
            wake_test()
        elif a.demo_run:
            demo_run(a.demo_run, dry=("add_reminder", "add_note"))
        elif a.face_demo:
            face_demo()
        else:
            run(show_face=not a.no_face)
    except KeyboardInterrupt:
        print("\nBye from Bit.")


if __name__ == "__main__":
    main()
