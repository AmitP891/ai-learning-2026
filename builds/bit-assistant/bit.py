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
from bitcore.config import LOG_DIR, WAKE_MODEL, log


def open_face():
    """Start the face server and open it in Chrome (press F on the page for full screen)."""
    face.start()
    subprocess.run(["open", "-a", "Google Chrome", face.url()], check=False)
    print(f"Face: {face.url()}  (click the page or press F for full screen)")


def answer(brain, text, released_at):
    """Claude -> Bit's voice, with timings (release = end of the user's speech)."""
    a = brain.ask(text)
    print(f"   Bit: {a['reply']}")
    speak_start = time.perf_counter()
    t = voice.speak(a["reply"])  # blocks until Bit has finished talking
    face.set_state("idle")
    # latency = when the first audio came out, not when speak() returned
    total = (speak_start + t["first_sound_s"]) - released_at
    print(f"   ({a['sentences']} sentence(s); claude {a['think_s']:.2f}s, "
          f"voice {t['first_sound_s']:.2f}s via {t['engine']}; release -> first sound {total:.2f}s)")
    log.info("latency: release -> first sound %.2fs (claude %.2fs, voice %.2fs, %s)",
             total, a["think_s"], t["first_sound_s"], t["engine"])


def run(show_face=True):
    from bitcore.ears import Ears

    if show_face:
        open_face()
    print("Loading ears (wake word + Whisper)...")
    ears = Ears()
    brain = Brain()
    ears.start()
    print(f"Speaker: {speaker.device_name()}")
    print(f"Ready. Say '{WAKE_MODEL.replace('_', ' ')}' or hold SPACE while talking. Ctrl+C to quit.\n")
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


def wake_test(target=5, false_window=30):
    from bitcore.ears import Ears

    ears = Ears(load_whisper=False)
    ears.start(space=False)
    name = WAKE_MODEL.replace("_", " ")
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
    (LOG_DIR / "gate1-wake-test.txt").write_text("\n".join(lines) + "\n")
    log.info("wake test: %s", " | ".join(lines))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--say")
    p.add_argument("--ask")
    p.add_argument("--wake-test", action="store_true")
    p.add_argument("--face-demo", action="store_true")
    p.add_argument("--no-face", action="store_true")
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
        elif a.face_demo:
            face_demo()
        else:
            run(show_face=not a.no_face)
    except KeyboardInterrupt:
        print("\nBye from Bit.")


if __name__ == "__main__":
    main()
