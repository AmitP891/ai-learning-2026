# Bit: Level 1 — director's brief

You are the director, animator, sound designer and render engineer for **"Bit: Level 1"**, a film made entirely in code.

## 1. Film in one line
A 20-second retro arcade boss fight: Bit, a small pink robot, defeats Professor Vague by turning his vague words into testable requirements, and the screen ends on **BOSS DEFEATED → TESTABLE ✓**.

## 2. Deliverables
| File | Spec |
|---|---|
| `out/teaser_9x16.mp4` | 1080×1920, 30 fps, H.264, AAC, exactly 20.0 s (YouTube Short / TikTok / Reel) |
| `out/teaser_16x9.mp4` | 1920×1080 re-layout of the same film for the long-form video |
| `out/beats.json` | `{bpm, beats[], downbeats[], hits[]}` in seconds |
| `out/style_frames/` | 3 PNG stills (Gate 1) |
| `out/beat_grid.md` | Shot table (Gate 2) |
| `out/critique.md` | Scores and fixes for every round (section 9) |
| `build.py` | One script that rebuilds everything from scratch |

## 3. References (take the grammar, never the content)
- **Style:** 16-bit arcade boss fights: chunky HUD, health bars, score counter, screen shake on hits, pixel wipes, "PRESS START" blink, combo counters.
- **Do not** copy any real game's characters, logos, fonts, level layouts or music. Everything is original.
- **Bit:** `brand/bit/bit.svg` (the source of truth for his design).
- **Professor Vague:** `brand/adventures/prof.py` (the `professor()` function draws him; reuse it).
- **Existing pipeline to match:** `brand/video-template/` and `brand/adventures/build_ep1.py` (PIL + cairosvg + numpy, raw frames piped to ffmpeg, sound synthesised with numpy).

## 4. Tools and keys
- Python 3 with PIL, cairosvg, numpy and ffmpeg only. No Remotion, no web frameworks, no paid APIs, no AI image or video models.
- Fonts: InterDisplay-Black for big titles, DejaVu Sans Mono Bold for HUD text, both pixelated (see Look).
- No voiceover in the teaser. Leave the mix at −6 dB peak so Amit's voice can sit on top in the long-form.

## 5. Character bible

### Bit (hero)
- **Build:** 600×700 SVG. Rounded pink head (#F0359E, shade #B81F75), dark visor (#171A2B) with two cyan (#00F0FF) eyes, cyan antenna ball, pink arms with grey (#3A3F5C) hands, `</>` on the chest panel, grey legs, pink feet. Outlines #0B0C14.
- **Proportions:** head ≈ 40% of height. Keep the SVG proportions exactly. Never redraw him freehand.
- **Expressions (eyes only, drawn on the visor):**
  - idle: tall rounded rectangles
  - blink: thin lines for 3 frames every ~3 s
  - determined: rectangles with a flat top edge (brows down)
  - hit: X X for 6 frames
  - happy: ^ ^ arcs
- **Moves:** idle bob (±10 px, 0.6 Hz); jump (0.5 s arc, squash on landing); dash left/right; **fire**: right arm raised, cyan beam from the hand.
- **Personality:** calm, precise, never panics. He wins by being specific, not by being stronger.

### Professor Vague (boss)
- **Build:** as drawn by `prof.py`: elderly professor, white hair, purple-grey jacket with elbow patches, bow tie, yellow pen in pocket, pointer stick, and a **fog tail instead of legs**.
- **Expressions:** smug (default), laughing (mouth open, shoulders shake), shocked, defeated (fog breaks into pixels).
- **Attacks:** throws vague words as glowing projectiles: **FAST**, **USER-FRIENDLY**, **TBD**, **ADEQUATE**. Each word is a pill-shaped block of grey fog with the word in it.
- **Personality:** pompous, loves words that mean nothing.

## 6. Look
- **Canvas:** dark navy #0D0D14 with a faint 60 px grid, as in the other Bit videos.
- **Pixel feel:** render the game layer at 1/4 resolution (270×480) and upscale with nearest-neighbour so it reads as pixel art. Bit and the Professor go through the same downscale, so they look like game sprites.
- **HUD (always on during the fight):**
  - Top left: `BIT` + a 10-segment cyan HP bar
  - Top right: `SCORE 000000`, ticking up
  - Bottom: the boss bar `PROFESSOR VAGUE`, purple, draining as he's hit
- **Palette:** only the brand colours above, plus purple #7838AA for the boss, yellow #FFD600 for score and highlights, green #39FF88 for "TESTABLE ✓" and red #FF465A for damage.
- **Banned:** centred text on a gradient, lens flares, real game logos, lorem ipsum, any font that isn't pixelated, any shot longer than 2.5 s without movement.

## 7. Beat sheet (120 BPM: 1 beat = 0.5 s, 40 beats, 10 bars)
| Bar | Time | Shot | Sync |
|---|---|---|---|
| 1 | 0–2 s | Black. **PRESS START** blinks. Coin sound on beat 4 | Music starts on the bar 2 downbeat |
| 2 | 2–4 s | Pixel wipe → **LEVEL 1: THE VAGUE REQUIREMENTS** slams in, one word per beat | Snare on each word |
| 3 | 4–6 s | Bit drops in from the top, squashes on landing. HUD slides in | Landing thump on beat 1 |
| 4 | 6–8 s | Fog rolls in. Professor Vague rises out of it, laughing. Boss name card: **BOSS: PROFESSOR VAGUE** | Laugh on beat 1, boss bar fills over 4 beats |
| 5 | 8–10 s | Professor throws **FAST**, then **USER-FRIENDLY**. Bit jumps the first and dashes past the second | One projectile per 2 beats |
| 6 | 10–12 s | **TBD** hits Bit: X X eyes, screen shake, HP −3. **ADEQUATE** misses | Hit sound on the downbeat |
| 7 | 12–14 s | Bit's eyes go "determined". Charge meter: **REQUIREMENTS CHECK v2** fills over 4 beats | Rising arpeggio |
| 8 | 14–16 s | Bit fires. Each beam hit turns a word testable: **FAST → WITHIN 200 ms**, **TBD → 10 MB/s**. Combo **×2, ×3, ×4**. Score ticks up | One hit per beat |
| 9 | 16–18 s | Boss bar hits zero. **BOSS DEFEATED**. Professor's fog breaks into pixels. **TESTABLE ✓** in green | Explosion on beat 1, chord on beat 3 |
| 10 | 18–20 s | Bit happy (^ ^). **THE ADVENTURES OF BIT · THE GAME · COMING 2027** and **@vibewithamitai** | Final thump exactly on beat 40 |

## 8. Text on screen (exact wording)
`PRESS START` · `LEVEL 1` · `THE VAGUE REQUIREMENTS` · `BIT` · `SCORE` · `BOSS: PROFESSOR VAGUE` · `FAST` · `USER-FRIENDLY` · `TBD` · `ADEQUATE` · `REQUIREMENTS CHECK v2` · `WITHIN 200 ms` · `10 MB/s` · `×2` `×3` `×4` · `BOSS DEFEATED` · `TESTABLE ✓` · `THE ADVENTURES OF BIT` · `THE GAME` · `COMING 2027` · `@vibewithamitai`

Nothing else. All text must be readable on a phone at arm's length: minimum 48 px tall on the 1080×1920 canvas.

## 9. Sound
- **Music:** an original 120 BPM chiptune synthesised in numpy: square-wave lead, triangle bass, noise-channel drums. Key of A minor. 8 bars plus a 2-bar outro hit.
- **SFX (synthesised):** coin, landing thump, jump, dash whoosh, projectile throw, hit, laser charge, laser fire, combo ding (pitch rises with the combo), explosion, victory chord.
- Measure the track and write `beats.json`. **Every animation event is timed from `beats.json`, never from hand-typed numbers.**

## 10. Workflow gates (stop and show Amit at each one)
1. **Style frames:** render 3 stills (title card, mid-fight with HUD, BOSS DEFEATED). Wait for approval.
2. **Beat grid:** print the shot table with exact frame numbers for every event. Wait for approval.
3. **First render:** render the 9:16 teaser, then start the critique loop.

## 11. Critique loop
After each render, extract one frame per beat and score 1–10 on:
1. **Hook:** would someone stop scrolling in the first 2 s?
2. **Readability:** every word legible on a phone
3. **Beat sync:** every hit, word and cut lands on a beat from `beats.json`
4. **On-model:** Bit and the Professor match the character bible
5. **Game feel:** HUD, shake, combos and sound make it feel like a real game
6. **Ending:** "TESTABLE ✓" and "COMING 2027" are unmissable

Fix everything below 8 and re-render. Stop when every score is 8 or more, or after 4 rounds. Append each round's scores and fixes to `out/critique.md`.

## 12. Gotchas
- Bit's mouth is not drawn in the fight (the visor has eyes only), so there's no lip-sync to do.
- `prof.py` caches the fog tail. Reuse the cache or the render will be slow.
- Pipe raw RGB frames to ffmpeg. Don't save 600 PNGs.
- Keep the 1/4-resolution game layer and the full-resolution HUD separate, then composite, so HUD text stays crisp if pixelation hurts readability.
- The film must be exactly 600 frames. Pad or trim the audio to match.
- Synthetic, original content only: no real company names, no real requirements documents.
