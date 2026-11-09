# Bit: my own J.A.R.V.I.S. — build brief

You are building **Bit**, a voice assistant that runs on Amit's Mac. Amit talks, Bit listens, thinks with Claude, answers out loud in Bit's own (cloned) voice, and does real things on the Mac. On screen, Bit's face reacts while he listens, thinks and talks, so the whole thing can be filmed for a YouTube long-form and a Short.

Build it in gates. At each gate, stop, show Amit, and end your message with this line on its own:

> ⏹ **STOP RECORDING** — Gate N done. Start a new recording before you reply.

## 1. What "done" looks like (the demo for the video)
Amit holds the space bar and says *"Bit, what's on my calendar today?"*. Bit's face switches to listening, then thinking, then he answers in his own voice with his mouth moving in sync, and reads out today's events. Then:
- *"Open Spotify and play something chill."* → Spotify opens and starts playing.
- *"Remind me to rehearse my talk at 7."* → a real reminder appears in Reminders.
- *"Make a note: Level 4 idea, Bit vs a speedrunner."* → the note lands in `notes/bit-notes.md`.
- *"Start my build session."* → opens Terminal in the repo, VS Code, and YouTube Studio in Chrome, and Bit says what's next on the content plan.
- *"What's the weather?"* / *"What time is it?"* → answered from real data.
- Anything it can't or shouldn't do → Bit says so in one short sentence and does nothing.

## 2. Architecture (keep it simple, all Python)
```
mic ──► push-to-talk (hold SPACE) ──► speech-to-text (local Whisper)
                                              │
                                              ▼
                                 Claude (tool use, short replies)
                                   │                    │
                                   ▼                    ▼
                      tools on the Mac (allow-list)   reply text
                                                        │
                                                        ▼
                               ElevenLabs TTS (Bit's voice) ──► speaker
                                                        │
                                   face window ◄── state + mouth level
```
- **Speech-to-text:** `faster-whisper` (model `base.en`), runs locally and free. Record with `sounddevice` while SPACE is held.
- **Brain:** Anthropic Python SDK, model `claude-sonnet-5-5`, tool use. System prompt: you are Bit, a small pink robot made of code, cheerful and brief; replies are **at most 2 sentences** because they're spoken; never read out URLs or code.
- **Voice:** ElevenLabs API with Bit's existing cloned voice (`ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID` in `.env`). Stream the audio if easy, else generate then play. Fallback if ElevenLabs fails: macOS `say` (so the demo never dies on camera).
- **Face:** a local web page (`face/index.html`, served by the Python app over a WebSocket) that draws Bit from `brand/bit/bit.svg` with four states: **idle** (blink), **listening** (eyes wide, cyan sound bars), **thinking** (eyes look up, three dots), **talking** (mouth opens with the audio's loudness, measured 30× a second like the video build scripts). Full-screen in Chrome for filming, 9:16 and 16:9 both readable.
- **Config:** everything in `.env` (never commit it). `python3 bit.py` starts it.

## 3. Tools Bit can use (allow-list only)
| Tool | Does | How |
|---|---|---|
| `get_calendar(day)` | Today's / tomorrow's events | AppleScript to Calendar |
| `add_reminder(text, time)` | Adds a reminder | AppleScript to Reminders |
| `open_app(name)` | Opens an app from an allow-list (Spotify, Chrome, VS Code, Terminal, Notes, Calendar) | `open -a` |
| `play_music(mood)` | Plays in Spotify | AppleScript to Spotify |
| `open_url(name)` | Opens a named bookmark only (YouTube Studio, GitHub repo, vibewithamit.com, content plan) | allow-listed URLs |
| `add_note(text)` | Appends a dated line to `notes/bit-notes.md` | file append |
| `get_weather(city)` | Current weather | Open-Meteo (free, no key) |
| `start_build_session()` | The macro in section 1 | the tools above |
| `get_time()` | Time and date | Python |

**Rules:** no free-form shell commands, no deleting, no sending messages or emails, no purchases. Anything outside the allow-list → refuse politely. Log every tool call to `logs/bit.log` (handy for the video).

## 4. Gates
1. **Ears and voice:** push-to-talk → Whisper → print the text; ElevenLabs says a fixed line in Bit's voice. Show both working.
2. **Brain:** Claude answers spoken questions with no tools yet. Show 3 exchanges, replies ≤ 2 sentences.
3. **Hands:** add the tools one by one; demo calendar, reminder, note, open app. Show the log.
4. **Face:** the web face with all four states and mouth sync. Show it full-screen.
5. **The demo run:** run the whole section 1 script end to end, three times. Fix anything flaky (latency over 4 s from release to first sound is flaky). Report timings.
6. **Finished:** README with setup steps and a 60-second "how it works", then ⏹ **STOP RECORDING** — Build finished.

## 5. Gotchas
- macOS will ask for Microphone, Accessibility (for the space-bar listener) and Automation (Calendar, Reminders, Spotify) permissions the first time. Say which one is being asked for when it pops up.
- Use the Python that has the packages (a venv in `builds/bit-assistant/.venv`, **not** in /tmp).
- Keep latency low: Whisper `base.en`, short Claude replies, start playing audio as soon as the first chunk arrives.
- Nothing personal goes into the repo: `.env`, `logs/` and `notes/` are git-ignored.
- On camera, the calendar will be visible: Amit should use a demo calendar or check what's in today's events before filming.
