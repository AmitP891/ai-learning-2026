# Ask Bit: series brief (build episode 1)

You are the director, animator, sound designer and render engineer for **"Ask Bit"**, a recurring 9:16 explainer series made entirely in code, as a **3D animated podcast studio** (reference: a low-poly 3D studio explainer reel Amit shared: warm studio lighting, two characters at a desk with broadcast mics, 2D graphics panels over the top, calm conversational voices). Each episode is a ~45–55 s conversation in a small neon studio: **GLITCH** asks about something trending in AI and coding, **BIT** explains it in **3 parts** with on-screen graphics, ends on an honest reality check and a dry one-liner.

Build it so every future episode is just a new `epNN-script.md` + `epNN.json` and one command.

## 1. Deliverables (episode 1)
| File | Spec |
|---|---|
| `out/ep01_9x16.mp4` | 1080×1920, 30 fps, H.264 + AAC, length set by the voice track + 3 s end card |
| `out/voices/ep01_*.mp3` | One file per line (git-ignored) |
| `out/timeline.json` | Start/end of every line, word timings if available, and every graphic event |
| `out/style_frames/` | 3 PNG stills (Gate 2) |
| `out/critique.md` | Scores and fixes per round |
| `ep01.json` | The script from `ep01-script.md` as data: lines, speaker, graphic cues |
| `build.py` | `python3 build.py ep01` rebuilds the episode from scratch (re-uses cached voices) |

## 2. Cast
- **BIT** (3D: `brand/bit/3d/bit_pink.stl`, `bit_cyan.stl`, `bit_dark.stl`, `bit_grey.stl`, the same model as the real 3D-printed Bit; 2D reference `brand/bit/bit.svg`): the expert. Calm, clever, brief, a little dry. His visor shows eyes only (no mouth). **When he talks, his chest screen becomes a cyan audio waveform** driven by his voice loudness, 30× a second. Expressions: neutral, thinking (eyes up), happy (^ ^).
- **GLITCH** (reference `brand/glitch/glitch.svg` and `glitch_sheet.png`, expressions from `brand/glitch/build_glitch.py` EXPR): cocky, impatient, wants shortcuts. **Build him in 3D from simple shapes** to match the sheet: dark hood (#2B2F45) with a lime rim, gunmetal face plate, dark visor, hoodie strings, `{ }` chest screen, lime soles. His eyes and expressions are an emissive texture on the visor drawn from the EXPR shapes. **When he talks, his `{ }` chest screen pulses lime with his voice.** Keep his signature 1–3 px sideways slice glitch every few frames, subtle.
- Both robots idle-bob gently when not talking and turn slightly towards whoever is speaking.

## 3. Voices (ElevenLabs, on Amit's Mac)
- Bit: `ELEVENLABS_VOICE_ID` (his existing cloned voice). Glitch: `ELEVENLABS_GLITCH_VOICE_ID`.
- **Gate 1 picks Glitch's voice:** list 5 voices from the ElevenLabs voice library that fit "young, fast, cocky, playful" and make each say line 1. Amit picks one and puts its ID in `.env` himself.
- Generate each line once and cache it in `out/voices/`. Re-generate a line only if Amit asks.
- **Security:** read keys with python-dotenv from `builds/bit-assistant/.env` (or a local `.env`). Never print, log or echo a key, never put one in a shell command, never commit `.env` or `out/voices/`.
- Gap between lines: 0.15 s (snappy), 0.4 s before a new part starts. Glitch's "…Respect." gets a 0.6 s pause before it.

## 4. Look
- **Engine:** Three.js in a single HTML page, rendered **frame by frame** with headless Chromium (Playwright): step the scene to time t, screenshot the canvas, pipe frames to ffmpeg. Never record in real time. Load Bit's STLs with `STLLoader` and give each part its colour (pink body, cyan eyes and screen, dark visor, grey parts).
- **Studio (3D, low-poly, warm):** a cosy dark room with **depth**: wooden slat wall behind with warm practical lights, acoustic panels, a shelf with a tiny 3D printer, a plant and a monitor of scrolling code, a pink neon `ASK BIT` sign on the back wall. A desk across the lower third with two broadcast mics on arms. Bit sits left, Glitch right. Soft key light, warm rim lights, gentle shadows, subtle depth of field on the background. Pink accent lights on Bit's side, lime on Glitch's. All original.
- **HUD (top ~45 % of the frame):** dark rounded panels with a cyan border slide in for each part. Title chip at the top (`WHAT PEOPLE SAY`, `WHAT WE TRIED`, `FACT CHECK`). Text and simple icons animate in on the words they match. A small footer chip `UP NEXT: …` at the end of each part. Gameplay stills for line 6: `brand/thumbnails/src/bugblaster_grok.jpg` and `bugblaster_fable.jpg`.
- **Captions:** the spoken line, 2 lines max, bottom centre above the Shorts UI (inside the safe zone), current word highlighted pink for Bit and lime for Glitch.
- **Camera:** a slow drifting wide shot of the studio for most of it, cuts to a medium close-up of whoever is speaking on their key lines (always for lines 7, 9, 12), a slight push-in on reveals. No shot longer than 6 s without some movement (HUD change, push-in or cut).
- **Fonts:** Inter Display (Black for titles, Bold for HUD and captions). No pixel font here; this series is cleaner than the Level films.
- **Banned:** real company logos (write "Grok" and "Claude Fable 5.2" as plain text only), any human face, lens flares, centred text on a gradient.

## 5. Sound
- Low-key lo-fi synth bed (original, synthesised: soft chords, light hats, ~85 BPM), ducked 8 dB under voices.
- Small UI sounds: soft pop when a HUD item appears, a stamp for `REAL`, a short whoosh between parts.
- Voices peak around −3 dB, mix peaks at −1 dB.

## 6. End card (3 s, no voice)
Dark screen, warm glow, both robots small at the bottom. Text: `Full showdown on the channel` · `Comment GAME for the prompt` · `Follow for the next one`.

## 7. Gates (stop and show Amit at each one)

After Gate 2 is approved, also render a **12 s coming-soon teaser** from the same studio (`out/coming_soon_9x16.mp4`): the sign lights up, wide shot, Glitch: "Bit, what's this show?" Bit: "You ask. I explain. In three parts." Glitch: "…Fine." Then text `NEW SERIES · STARTS SUNDAY · FOLLOW`.

At every gate, finish your message with this line on its own:

> ⏹ **STOP RECORDING** — Gate N done. Start a new recording before you reply.

1. **Voices:** Glitch voice audition (5 options saying line 1), Amit picks. Then generate all 12 lines and play them in order with the gaps. Report total length.
2. **Style frames:** 3 stills: the wide studio with both robots, the `WHAT WE TRIED` panel with the two game cards, Glitch's "…Respect." close-up. Wait for approval.
3. **Timeline:** print the table of every line and graphic event with exact times from the voice files. Wait for approval.
4. **First render**, then the critique loop (section 8). After each round show the scores and fixes, stop with Gate 4a, 4b, …
5. **Finished:** every score 8+ or 4 rounds done. ⏹ **STOP RECORDING** — Episode finished.

## 8. Critique loop
Extract one frame every 2 s and score 1–10:
1. **Hook:** does Glitch's question land in the first 2 s, with the HUD tag visible?
2. **Readability:** every HUD word and caption readable on a phone, inside the safe zone
3. **Sync:** waveform/pulse matches the voice; HUD items appear on the matching words
4. **On-model:** Bit and Glitch match their bibles
5. **Clarity:** someone who's never coded understands the 3 parts with the sound off (captions + HUD)
6. **Ending:** the reality check and the one-liner land; the CTA is the clearest thing on the end card

## 9. Gotchas
- Three.js from a CDN pinned to one version (or vendored into the folder). Fonts for HUD and captions are drawn in a 2D overlay (HTML/canvas on top of the WebGL canvas) so they stay crisp.
- Rendering 1,500+ frames headless will take a while: render a low-res preview (540×960) for critique rounds, full res only for the final.
- Timings come from the real voice files, never hand-typed.
- Shorts safe zone: keep text out of the bottom 420 px and the right 140 px.
- `out/voices/` and any `.env` stay git-ignored. Run a secret scan before committing.
