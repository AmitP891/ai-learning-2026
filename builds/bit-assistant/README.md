# Bit: my own J.A.R.V.I.S.

Bit is a voice assistant that lives on my Mac. Say **"Hey Bit"**, ask something, and Bit answers out loud in his own cloned voice, through a speaker hidden behind the 3D-printed Bit on the desk. He reads the calendar, sets reminders, takes notes, plays Spotify, opens apps, checks the weather, and starts a build session. His face on screen listens, thinks and talks, with his mouth moving to his voice.

Everything here is Python. One command starts it: `python3 bit.py`.

## How it works (60 seconds)

> Bit is always listening, but only on this Mac. A tiny neural network, trained just for this project, checks every 80 milliseconds of audio for "hey bit". No audio ever leaves the Mac.
>
> When it hears "hey bit", Bit chimes and records until I stop talking. Whisper turns that into text, still on the Mac.
>
> The text goes to Claude, along with a short list of tools: read the calendar, add a reminder, and a few more. Nothing else: no shell commands, no deleting, no emails. If Claude needs a tool, Bit says "On it!", the tool runs, and Claude turns the result into at most two spoken sentences.
>
> ElevenLabs speaks them in Bit's cloned voice. As the audio plays, Bit measures its loudness thirty times a second and sends it to his face in Chrome, so his mouth moves with every word.
>
> From the end of my question to Bit's first word: about two seconds.

```
mic ─► "hey bit" (openWakeWord, on-device) ─► record until 1 s silence (webrtcvad)
         or hold SPACE                         ─► Whisper base.en (on-device)
                                                    │ text
                                                    ▼
                        Claude Sonnet 5.5 + allow-listed tools ─► Mac (EventKit, AppleScript, open)
                                                    │ reply, sentence by sentence
                                                    ▼
                         ElevenLabs (Bit's voice) ─► speaker in the real Bit
                                                    │ loudness 30x/s
                                                    ▼
                         face/index.html in Chrome (idle · listening · thinking · talking)
```

## Setup

You need: a Mac (Apple silicon, macOS 14+), Python 3.13, Google Chrome, Spotify (for music), an [Anthropic API key](https://console.anthropic.com), and an [ElevenLabs](https://elevenlabs.io) account with a cloned voice.

```bash
cd builds/bit-assistant
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env        # then fill in the keys (see below)
.venv/bin/python bit.py
```

**`.env`** (never committed). Required: `ANTHROPIC_API_KEY`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`. Recommended: `BIT_HOME_CITY` and `BIT_AUDIO_DEVICE` (part of the speaker's name, e.g. `JBL Go`). Every other setting is listed in `.env.example` with its default.

Two things that cost me time:
- The ElevenLabs key needs the **Text to Speech** permission switched on, or every request fails with `401 missing_permissions` (Bit then falls back to the macOS `say` voice).
- Type keys into `.env` plainly. A key pasted with curly "smart" quotes around it is rejected as `Invalid bearer token`.

**macOS permissions.** The first time each feature runs, macOS asks once. Allow them for the app you run Bit from (Terminal, iTerm, VS Code...):

| Prompt | When | Needed for |
|---|---|---|
| Microphone | first start | wake word and speech |
| Accessibility / Input Monitoring | first start | the hold-SPACE backup trigger |
| Calendars (full access) | first calendar question | `get_calendar` (EventKit) |
| Automation → Reminders | first reminder | `add_reminder` |
| Automation → Spotify | first "play something" | `play_music` |

If you click "Don't Allow", turn it back on in **System Settings → Privacy & Security**.

## Using it

| Command | What it does |
|---|---|
| `python3 bit.py` | Bit, with the face opening in Chrome. Say "hey bit" or hold SPACE while you talk. |
| `python3 bit.py --record` | Same, and saves the session to `recordings/bit-<date>.wav`: **left = your mic, right = Bit**, on one timeline. Prints the exact start time; clap on camera to sync. Works with every mode. |
| `python3 bit.py --no-face` | Without the face page. |
| `python3 bit.py --ask "what time is it?"` | Typed question, spoken answer (no mic). |
| `python3 bit.py --say "hello"` | Just say a line in Bit's voice. |
| `python3 bit.py --face-demo` | Shows the four face states for filming. |
| `python3 bit.py --demo-run` | The video demo script, three times, with timings. |
| `python3 bit.py --wake-test` | Say the wake word 5 times, then talk normally for 30 s; counts misses and false triggers. |

**The face** is at `http://localhost:8765`. Click it or press **F** for full screen; **L** hides the labels; **1-4** preview the states; `?state=thinking` freezes a state for thumbnails. Bit is about 75% of the screen height in both 9:16 and 16:9.

**What Bit can do.** These are his only tools: today's or tomorrow's calendar, add a reminder, open Spotify / Chrome / VS Code / Terminal / Notes / Calendar, play chill, focus or happy music, open a saved bookmark (YouTube Studio, the GitHub repo, vibewithamit.com, the content plan), add a dated note to `notes/bit-notes.md`, the weather (Open-Meteo, no key), the time, and "start my build session" (Terminal and VS Code in the repo, YouTube Studio, and the first unticked `- [ ]` line of `notes/next.md`). Anything else, he says he can't and does nothing. Every tool call is logged to `logs/bit.log`.

## Privacy

- **Your voice never leaves the Mac.** The wake word and Whisper both run on-device. The mic is always on while Bit runs, but its audio is only ever processed locally.
- After "hey bit", the **text** of what you said goes to Anthropic (Claude), with any tool results it asks for, such as your event titles. Bit's reply **text** goes to ElevenLabs to be spoken.
- The face server only listens on `localhost`.
- `.env`, `logs/`, `notes/`, `recordings/` and the wake-word training data are git-ignored. `--record` keeps your mic audio on disk, in `recordings/`.
- On camera the calendar is visible. Use a demo calendar or check today's events before filming.

## The "hey bit" wake word

`models/hey_bit.onnx` was trained for this project with `wakeword/train_hey_bit.py`, on a Mac with no GPU:
- **"hey bit"** spoken by 28 macOS voices at four speeds, with noise and room echo added.
- **Sound-alikes** that must *not* trigger ("hey Bill", "a bit", "habit", "hey Siri"...).
- **8.4 hours of everyday speech** from openWakeWord's published features.

Tested on 7 voices and 2.1 hours of speech it never heard, it caught 100% of "hey bit", with about 0.5 false triggers per hour. My live test: 5/5, 0 false triggers in 30 s of normal talk. It still sometimes fires on close rhymes ("hey bix", "hey big").

- **Switch back to the built-in wake word:** `WAKE_MODEL=hey_jarvis` in `.env`.
- **Retrain:**
  1. `.venv/bin/pip install torch onnx`
  2. Download [`validation_set_features.npy`](https://huggingface.co/datasets/davidscripka/openwakeword_features) (185 MB) into `wakeword/data/`.
  3. Run `.venv/bin/python wakeword/train_hey_bit.py`. The first run takes about 22 min; later runs about 6 min, because the voice clips are cached.
  4. To make it better on your voice, put recordings of yourself saying "hey bit" in `wakeword/data/amit/*.wav`.
- Judge a model by the **streaming test** at the end of the training output, which feeds audio in the way the live mic does.

## Speed

Measured in Gate 5 with the full demo script, three times, typed (spoken adds about 0.5 s for Whisper):

| | median | worst |
|---|---|---|
| Question → Bit's first sound ("On it!") | 1.43 s | 1.65 s |
| Question → the actual answer starts | 2.88 s | 3.55 s |

Where the time goes: each tool question needs two Claude calls in a row (pick the tool, then phrase the answer). Each call takes 0.9–3 s depending on the time of day. The tools themselves take 0–0.7 s (the calendar takes 0.001 s via EventKit). ElevenLabs' first audio arrives after about 0.13 s. Saying "On it!" while the second call runs is what keeps the first sound around 2 s.

## Adding a tool (the v2 list)

Each tool is one function plus one schema in `bitcore/tools.py`:
1. Write the function. Raise `ToolError("...")` for anything Bit should say went wrong.
2. Add a `_schema("name", "description", {...})` entry to `SCHEMAS`.
3. Register it in `FUNCS`.

The brain, logging, and the "On it!" behaviour pick it up automatically. Ideas waiting: screenshot + vision, pink smart lights, channel stats, "what should I make next?", running the Bit video build scripts, daily standup, morning briefing, focus mode, memory across sessions.

## Files

```
bit.py                    entry point and modes (demo run, wake test, face demo, --record)
bitcore/config.py         settings from .env
bitcore/ears.py           mic, wake word, SPACE trigger, silence detection, Whisper
bitcore/brain.py          Claude: prompt, tool loop, streaming, caching
bitcore/tools.py          the allow-listed tools
bitcore/voice.py          ElevenLabs streaming voice (macOS `say` fallback)
bitcore/speaker.py        output device, chime, playback
bitcore/face.py           face server (page + WebSocket), mouth timing
bitcore/recorder.py       --record: mic + Bit on one timeline
face/index.html           Bit's face, drawn from brand/bit/bit.svg
models/hey_bit.onnx       the trained wake word
wakeword/train_hey_bit.py how it was trained
```

## Troubleshooting

- **Bit sounds like the robotic Mac voice:** ElevenLabs failed. The terminal shows why; usually the key permission (see Setup).
- **The mouth runs ahead of the voice on a Bluetooth speaker:** set `BIT_AV_OFFSET_MS=200` and adjust.
- **`[speaker] '...' not connected - using Mac speakers`:** the `BIT_AUDIO_DEVICE` name didn't match. Check the exact name in System Settings → Sound.
- **The wake word misses you:** try `WAKE_THRESHOLD=0.7`, or retrain with your own recordings (see above). Hold SPACE always works.
- **"Spotify isn't installed":** install it and log in. Playlists can be changed with `BIT_PLAYLIST_*`.
