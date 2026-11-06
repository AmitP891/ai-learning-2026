# Bit: Level 2 — director's brief

You are the director, animator, sound designer and render engineer for **"Bit: Level 2"**, a film made entirely in code. It is the sequel to `brand/motion/bit-level-1/` and must look and sound like the same game.

## 1. Film in one line
A 20-second retro arcade boss fight: Bit fights **Scope Creep**, a blob that grows every time someone says "and also…", and shrinks it back down by turning every "quick extra" into **NEXT VERSION**. The film ends on **SUBSCRIBE TO UNLOCK LEVEL 3**.

## 2. Deliverables
| File | Spec |
|---|---|
| `out/level2_9x16.mp4` | 1080×1920, 30 fps, H.264, AAC, exactly 20.0 s (YouTube Short / TikTok / Reel) |
| `out/beats.json` | `{bpm, beats[], downbeats[], hits[]}` in seconds |
| `out/style_frames/` | 3 PNG stills (Gate 1) |
| `out/beat_grid.md` | Shot table (Gate 2) |
| `out/critique.md` | Scores and fixes for every round (section 11) |
| `build.py` | One script that rebuilds everything from scratch |

No 16:9 version this time.

## 3. Start from Level 1 (reuse, don't rewrite)
- Copy `brand/motion/bit-level-1/build.py` as the starting point. Keep its engine: 1/4-resolution game layer upscaled ×4 nearest-neighbour, `ptext` pixel text, `bit_sprite`, `blit` with the Shorts safe zone, `dither_alpha`, the synth functions, raw RGB frames piped to ffmpeg.
- Keep the HUD layout, fonts, palette, wipes, card and plate styles identical, so Level 2 feels like the next level of the same game.
- Replace the Professor with Scope Creep (section 5). The Professor appears only as a 1-second cameo (section 7, bar 1).
- **Do not** copy any real game's characters, logos, fonts, level layouts or music. Everything is original.

## 4. Tools and keys
- Python 3 with PIL, cairosvg, numpy and ffmpeg only. No Remotion, no web frameworks, no paid APIs, no AI image or video models.
- Fonts as Level 1: InterDisplay-Black for big titles, DejaVu Sans Mono Bold for HUD text, both pixelated.
- No voiceover. Mix peaks at −6 dB.

## 5. Character bible

### Bit (hero)
Exactly as Level 1's character bible (`brand/bit/bit.svg`, eyes-only visor, idle / blink / determined / hit / happy). New move this level: **shield**, a cyan hexagon in front of him for 0.5 s with `NEXT VERSION` stamped across it when something hits it.

### Scope Creep (boss)
- **Build:** draw him in code at game resolution: a lumpy, wobbling blob (soft purple #7838AA body, darker #4E2470 outline, a few pale-lilac highlight pixels), two small white eyes and a wide grin. He is made of sticky notes: 6–10 small yellow (#FFD600) rectangles stuck to his body at slight angles.
- **Size:** starts about the same height as Bit. **Every attack makes him visibly bigger** (+15% each, wobble on the change). At full size he fills most of the right half of the arena.
- **Expressions:** grin (default), greedy (eyes wide, mouth open, when he grows), shocked, defeated (sticky notes fly off, blob shrinks to a tiny dot and pops).
- **Attacks:** throws sticky notes as projectiles, each a pill like Level 1's words: **AND ALSO…**, **ONE MORE THING**, **QUICK CHANGE**, **SHOULD BE EASY**.
- **Personality:** cheerful, endlessly hungry for "just one more feature". Not evil, just never satisfied.

## 6. Look
- **Canvas, grid, pixel feel, HUD positions:** identical to Level 1.
- **HUD:** top left `BIT` + 10-segment cyan HP bar; top right `SCORE` (start at Level 1's final score, keep ticking up); boss bar `SCOPE CREEP` in purple, which **grows longer** when he grows, then drains.
- **Palette:** brand colours only, as Level 1. Green #39FF88 for `NEXT VERSION` and `SCOPE LOCKED ✓`, red #FF465A for damage.
- **Banned:** centred text on a gradient, lens flares, real game logos, any non-pixel font, any shot longer than 2.5 s without movement, any text Level 1 viewers would need to be engineers to understand.

## 7. Beat sheet (120 BPM: 1 beat = 0.5 s, 40 beats, 10 bars)
| Bar | Time | Shot | Sync |
|---|---|---|---|
| 1 | 0–2 s | Hard open mid-action: the last second of Level 1's explosion (the Professor's fog bursting into pixels), then **LEVEL 1 CLEARED ✓** | Explosion on beat 1, coin on beat 4 |
| 2 | 2–4 s | Pixel wipe → **LEVEL 2: SCOPE CREEP** slams in, one word per beat | Snare on each word |
| 3 | 4–6 s | Bit walks in, idle bob. A small sticky-note blob bounces in on the right. It looks harmless. HUD slides in | Landing thump on beat 1 |
| 4 | 6–8 s | Boss card **BOSS: SCOPE CREEP**. He throws **AND ALSO…**, it hits Bit (HP −1) and the blob **grows** | Hit on the downbeat, grow "gulp" on beat 3 |
| 5 | 8–10 s | **ONE MORE THING** and **QUICK CHANGE**: Bit dodges one, the other hits. Blob grows twice; boss bar stretches | One projectile per 2 beats |
| 6 | 10–12 s | **SHOULD BE EASY**: the biggest note, Scope Creep now huge, laughing. Screen shake | Hit on the downbeat |
| 7 | 12–14 s | Bit's eyes go "determined". Meter: **CHANGE CONTROL** fills over 4 beats | Rising arpeggio |
| 8 | 14–16 s | He throws all four again. Bit's **shield** stamps each one **NEXT VERSION** (green) and they bounce back into the blob. Combo **×2 ×3 ×4**. He **shrinks** with each hit | One hit per beat |
| 9 | 16–18 s | Boss bar hits zero. **BOSS DEFEATED**. Sticky notes fly off, blob shrinks to a dot and pops. **SCOPE LOCKED ✓** in green | Pop on beat 1, chord on beat 3 |
| 10 | 18–20 s | Bit happy (^ ^). **SUBSCRIBE TO UNLOCK LEVEL 3** blinking, **PICK THE NEXT BOSS ↓ COMMENTS** and **@vibewithamitai** | Final thump exactly on beat 40 |

## 8. Text on screen (exact wording)
`LEVEL 1 CLEARED ✓` · `LEVEL 2` · `SCOPE CREEP` · `BIT` · `SCORE` · `BOSS: SCOPE CREEP` · `AND ALSO…` · `ONE MORE THING` · `QUICK CHANGE` · `SHOULD BE EASY` · `CHANGE CONTROL` · `NEXT VERSION` · `×2` `×3` `×4` · `BOSS DEFEATED` · `SCOPE LOCKED ✓` · `SUBSCRIBE TO UNLOCK LEVEL 3` · `PICK THE NEXT BOSS` · `COMMENTS` · `@vibewithamitai`

Nothing else. Minimum 48 px tall on the 1080×1920 canvas, inside the Shorts safe zone.

## 9. Sound
- **Music:** reuse Level 1's chiptune engine and key (A minor, 120 BPM), but write a **new 8-bar melody** so it sounds like the next level, not a repeat. Keep the same drum kit.
- **SFX (synthesised):** reuse Level 1's, plus a **gulp** when he grows (low sweep up), a **shield clang** (short metallic square-wave hit) and a **pop** for the final defeat.
- Measure the track and write `beats.json`. **Every animation event is timed from `beats.json`, never from hand-typed numbers.**

## 10. Workflow gates (stop and show Amit at each one)
If Amit is screen-recording, each gate is one clip. At every gate, finish your message with this line on its own, exactly as written:

> ⏹ **STOP RECORDING** — Gate N done. Start a new recording before you reply.

1. **Style frames:** render 3 stills (title card, Scope Creep at full size mid-fight, the SUBSCRIBE end card). Wait for approval.
2. **Beat grid:** print the shot table with exact frame numbers for every event. Wait for approval.
3. **First render:** render the 9:16 film, then start the critique loop.
4. **After each critique round:** show the scores and the fixes you'll make, then stop with the same line (Gate 4a, 4b, …) before re-rendering.
5. **Finished:** when every score is 8 or more, or after round 4, show the final scores and end with: ⏹ **STOP RECORDING** — Film finished.

## 11. Critique loop
After each render, extract one frame per beat and score 1–10 on:
1. **Hook:** would someone stop scrolling in the first 2 s?
2. **Readability:** every word legible on a phone, inside the safe zone
3. **Beat sync:** every hit, word and cut lands on a beat from `beats.json`
4. **On-model:** Bit matches his bible; Scope Creep visibly grows then shrinks
5. **Game feel:** HUD, shake, combos and sound feel like the same game as Level 1
6. **Ending:** the SUBSCRIBE line is the clearest thing in the last 2 s

Fix everything below 8 and re-render. Stop when every score is 8 or more, or after 4 rounds. Append each round's scores and fixes to `out/critique.md`.

## 12. Gotchas
- Level 1's `build.py` remaps Linux font paths for macOS and sets `DYLD_FALLBACK_LIBRARY_PATH` for cairo. Keep that.
- Bit's visor shows eyes only in the game; no lip-sync.
- The film must be exactly 600 frames. Pad or trim the audio to match.
- Synthetic, original content only: no real company names, products or documents.
