# Bit: Level 3 — director's brief

You are the director, animator, sound designer and render engineer for **"Bit: Level 3"**, a film made entirely in code. It is the sequel to `brand/motion/bit-level-2/` and must look and sound like the same game.

## 1. Film in one line
A 20-second retro arcade **build race**: Bit and his new rival **GLITCH** get the same prompt, *MAKE A GAME*. Glitch types twice as fast and ships first, but his game is full of bugs that swarm out and wreck it. Bit tests as he builds, zaps the bugs, and his game boots clean. The film ends on **WHO SHOULD BIT RACE NEXT? ↓ COMMENTS**.

No requirements, no systems engineering. The joke is one every coder and gamer knows: **ship it now vs test it first**.

## 2. Deliverables
| File | Spec |
|---|---|
| `out/level3_9x16.mp4` | 1080×1920, 30 fps, H.264, AAC, exactly 20.0 s (YouTube Short / TikTok / Reel) |
| `out/beats.json` | `{bpm, beats[], downbeats[], hits[]}` in seconds |
| `out/style_frames/` | 3 PNG stills (Gate 1) |
| `out/beat_grid.md` | Shot table (Gate 2) |
| `out/critique.md` | Scores and fixes for every round (section 11) |
| `build.py` | One script that rebuilds everything from scratch |

## 3. Start from Level 2 (reuse, don't rewrite)
- Copy `brand/motion/bit-level-2/build.py` as the starting point. Keep its engine: 1/4-resolution game layer upscaled ×4 nearest-neighbour, `ptext` pixel text, `bit_sprite`, `blit` with the Shorts safe zone, `dither_alpha`, the synth functions, Bit's shield, raw RGB frames piped to ffmpeg.
- Keep the HUD layout, fonts, palette, wipes, card and plate styles identical.
- Remove Scope Creep and the Professor. The new cast is Bit, GLITCH and the bugs (section 5).
- **Do not** copy any real game's characters, logos, fonts, level layouts or music, or any real AI company's logo, colours or product names. Everything is original.

## 4. Tools and keys
- Python 3 with PIL, cairosvg, numpy and ffmpeg only. No Remotion, no web frameworks, no paid APIs, no AI image or video models.
- Fonts as Levels 1 and 2: InterDisplay-Black for big titles, DejaVu Sans Mono Bold for HUD text, both pixelated.
- No voiceover. Mix peaks at −6 dB.

## 5. Character bible

### Bit (hero)
Exactly as the Level 2 bible (`brand/bit/bit.svg`, eyes-only visor; idle / blink / determined / hit / happy; shield). New this level: a **TEST** zap, a short cyan beam from his chest screen that turns a bug into a green ✓ and pops it.

### GLITCH (rival)
- **Build:** his master design is `brand/glitch/glitch.svg` (character sheet: `brand/glitch/glitch_sheet.png`). Load it the same way Level 1 loads `bit.svg`: strip the `eyes` group and `mouth` path, render to the same height as Bit so they read as equals, snap to his palette, then draw the expression on the visor in code. He's a **hacker-hood robot**: dark hood (#2B2F45) with a lime rim, gunmetal face plate (#3A3F55), dark visor with **lime** (#39FF88) eyes, hoodie strings, `{ }` chest screen, lime soles. Every few frames a horizontal slice of his sprite **shifts sideways by 1–3 game pixels** (a digital glitch). That shift is his signature.
- **Personality:** cocky, fast, impatient. Not evil, just "move fast and ship". He smirks a lot.
- **Expressions (visor only, match `brand/glitch/build_glitch.py` EXPR):** smirk (default, left eye narrowed), typing (eyes become scrolling code dashes), shocked (hollow square eyes), crashed (visor full of static).
- **Move:** **SHIP IT!**, a stamp he slams on his game before it's finished.

### The bugs
Small pixel beetles (6×5 game pixels), red #FF465A body with a dark outline and two legs that wiggle. They crawl out of Glitch's game in a swarm. Cute, not scary.

## 6. Look
- **Canvas, grid, pixel feel, HUD positions:** identical to Levels 1 and 2.
- **Split arena:** a thin vertical divider down the centre. Bit's side on the left with a pink-tinted floor; Glitch's side on the right with a lime-tinted floor. Each side has a small **game window** above its robot that fills with blocks as they build.
- **HUD:** top left `BIT` + build bar (cyan); top right `GLITCH` + build bar (lime). Both start at 0% and race. `SCORE` stays centred at the top, continuing from Level 2's final score.
- **Palette:** brand colours plus Glitch's lime and gunmetal. Red only for bugs and damage.
- **Banned:** centred text on a gradient, lens flares, real game or company logos, any non-pixel font, any shot longer than 2.5 s without movement, any engineering jargon (requirements, shall, spec, verification).

## 7. Beat sheet (120 BPM: 1 beat = 0.5 s, 40 beats, 10 bars)
| Bar | Time | Shot | Sync |
|---|---|---|---|
| 1 | 0–2 s | Hard open: Level 2's last frame (SCOPE LOCKED ✓) glitches apart; Glitch's face tears through the static and smirks straight at camera | Static burst on beat 1, smirk on beat 3 |
| 2 | 2–4 s | **LEVEL 3: BUILD RACE** slams in, one word per beat. Split arena wipes in | Snare on each word |
| 3 | 4–6 s | Prompt card drops between them: **PROMPT: MAKE A GAME**. Both robots crack their knuckles. **3, 2, 1, GO** | One count per beat |
| 4 | 6–8 s | Race. Glitch types in a blur, his bar shoots to 70%; Bit's climbs slowly to 30% while he zaps **TEST ✓** on each block | Keystroke ticks on every 8th note |
| 5 | 8–10 s | Glitch slams **SHIP IT!** at 100%. Confetti on his side. Bit is still at 60%, still testing | Stamp on the downbeat |
| 6 | 10–12 s | Glitch's game window boots: flashy for one beat, then **ERROR** text, then bugs pour out of it. His visor goes shocked | Error buzz on beat 1, bug skitters from beat 2 |
| 7 | 12–14 s | Bugs swarm across the divider towards Bit. Combo **BUG ×1 ×2 ×3 ×4**: Bit zaps each one, and each pops into a green ✓ | One zap per beat |
| 8 | 14–16 s | Bit's bar hits 100%. His game window boots clean: a tiny playable game runs inside it (original design, e.g. a pink dot collecting stars). **TESTED ✓** | Chord on beat 1 |
| 9 | 16–18 s | Glitch's visor fills with static, **CRASHED**. **BIT WINS** in pink | Crash on beat 1, win sting on beat 3 |
| 10 | 18–20 s | Bit happy (^ ^), Glitch sulking but already typing again. **WHO SHOULD BIT RACE NEXT?**, **↓ COMMENTS**, **@vibewithamitai** | Final thump exactly on beat 40 |

## 8. Text on screen (exact wording)
`LEVEL 3` · `BUILD RACE` · `BIT` · `GLITCH` · `SCORE` · `PROMPT: MAKE A GAME` · `3` `2` `1` `GO` · `TEST ✓` · `SHIP IT!` · `ERROR` · `BUG ×1` `×2` `×3` `×4` · `TESTED ✓` · `CRASHED` · `BIT WINS` · `WHO SHOULD BIT RACE NEXT?` · `COMMENTS` · `@vibewithamitai`

Nothing else. Minimum 48 px tall on the 1080×1920 canvas, inside the Shorts safe zone.

## 9. Sound
- **Music:** reuse the chiptune engine and drum kit (A minor, 120 BPM) with a **new 8-bar melody** that is faster and more frantic than Level 2 (race energy: 16th-note arpeggios in bars 4–7).
- **SFX (synthesised):** reuse Levels 1–2's, plus **keystroke ticks** (very short noise clicks), a **static burst** (filtered white noise), an **error buzz** (low square-wave drone), **bug skitter** (tiny random high clicks), a **test zap** (rising sine blip) and a **crash** (noise burst falling in pitch).
- Measure the track and write `beats.json`. **Every animation event is timed from `beats.json`, never from hand-typed numbers.**

## 10. Workflow gates (stop and show Amit at each one)
If Amit is screen-recording, each gate is one clip. At every gate, finish your message with this line on its own, exactly as written:

> ⏹ **STOP RECORDING** — Gate N done. Start a new recording before you reply.

1. **Style frames:** render 3 stills (Glitch's close-up smirk, the race at its midpoint with both build bars visible, the bug swarm being zapped). Wait for approval.
2. **Beat grid:** print the shot table with exact frame numbers for every event. Wait for approval.
3. **First render:** render the 9:16 film, then start the critique loop.
4. **After each critique round:** show the scores and the fixes you'll make, then stop with the same line (Gate 4a, 4b, …) before re-rendering.
5. **Finished:** when every score is 8 or more, or after round 4, show the final scores and end with: ⏹ **STOP RECORDING** — Film finished.

## 11. Critique loop
After each render, extract one frame per beat and score 1–10 on:
1. **Hook:** would someone stop scrolling in the first 2 s? (Glitch tearing through the screen must land.)
2. **Readability:** every word legible on a phone, inside the safe zone
3. **Beat sync:** every hit, word and cut lands on a beat from `beats.json`
4. **On-model:** Bit matches his bible; Glitch's sideways glitch is visible but never makes him unreadable
5. **Story:** a viewer who has never coded gets "fast but broken vs slower but works" with the sound off
6. **Ending:** the comments question is the clearest thing in the last 2 s

Fix everything below 8 and re-render. Stop when every score is 8 or more, or after 4 rounds. Append each round's scores and fixes to `out/critique.md`.

## 12. Gotchas
- Level 2's `build.py` remaps Linux font paths for macOS and sets `DYLD_FALLBACK_LIBRARY_PATH` for cairo. Keep that.
- Bit's and Glitch's visors show eyes only; no lip-sync.
- Glitch's slice-shift must use whole game pixels so it stays crisp after the ×4 upscale.
- The film must be exactly 600 frames. Pad or trim the audio to match.
- Original content only: no real company names, products, logos or game characters.
