# Bit: Level 3 — critique log

Each round: one frame per beat from the encoded `level3_9x16.mp4` (beat time from `beats.json` + 2 frames), plus a crop of GLITCH every 2 beats through bars 4–9, scored 1–10 on the brief's six criteria.

## Round 1 — first render

Automated checks on this render:
- **Length:** 600 frames, 20.000 s of video and 20.000 s of audio.
- **Safe zone and text size:** OK on all 600 frames. No text under the platform buttons, nothing off screen, and no capitals under 48 px tall.
- **Audio:** the AAC peak is **−6.23 dBFS**. Loudness per 2-second bar is −23.4 / −27.5 / −25.3 / −25.0 / −24.2 / −22.7 / −24.3 / −22.8 / −21.3 / −26.0 dB RMS. Bar 1 is no longer near-silent: the bass hit and drone put it level with the rest of the film.
- **Sync:** every sound and animation event is placed in code at a `beats.json` time (the `B()` lookup), including the bar 1 bass hits on beats 1 and 3.

| # | Criterion | R1 | Why |
|---|---|---|---|
| 1 | Hook | 8 | Frame 0 is a static burst over SCOPE LOCKED ✓ with a bass hit. GLITCH's face is tearing through by 0.5 s, fills the screen by 0.9 s and smirks at 1.0 s. But frame 0 is almost all noise, so the SCOPE LOCKED ✓ callback barely reads. |
| 2 | Readability | 8 | Every word passes both automated checks. While the HUD slides in on beat 9, the bars arrive before BIT / GLITCH, which only appear once fully on screen (by design). ERROR blinks over GLITCH's blocks, but it stays readable. |
| 3 | Beat sync | 9 | Title words, counts, TEST ✓ zaps, SHIP IT!, ERROR, BUG ×1–4, TESTED ✓, CRASHED, BIT WINS and the end-card words all land on a beat or half beat. Keystroke ticks fall on the 8th notes, and GLITCH's blocks on his 8th-note keystrokes. |
| 4 | On-model | **7** | Bit is the Level 1/2 sprite with determined, happy ^ ^ and blink eyes. GLITCH's smirk, typing, shocked and crashed visors match `build_glitch.py`. **The slice shift is not clearly visible in every mid-film shot:** in the bars 4–9 crops it shows on the typing, raise, smirk and crashed poses, but in 4 of the 12 shocked crops (bars 6–8) the cut fell on flat hood or body colour and can't be seen. |
| 5 | Story | 8 | It reads with the sound off: GLITCH's crooked blocks; SHIP IT! with 3 empty slots while his bar jumps to 100%; rainbow boot; ERROR; bugs; Bit zapping them into ✓s; TESTED ✓ with a working mini-game; CRASHED; BIT WINS. One weak spot: in bar 6 Bit keeps building silently, so for about a beat his side has nothing new to look at. |
| 6 | Ending | 9 | WHO SHOULD / BIT RACE / NEXT? is the biggest, brightest thing in the last 2 s. ↓ COMMENTS blinks, and @vibewithamitai sits underneath. Bit hops, and GLITCH sulks while typing again. |

**Fixes for round 2**
1. **On-model (slice shift):** every frame GLITCH is in gets **two** cuts. One always crosses his visor's eye band (at least 40% of the band tall, shifted a full 3 game px). The other crosses his `{ }` screen or his hood rim. Both re-roll every 2 frames. The shocked, typing, smirk and crashed eyes then always show a visible notch, and the shift never covers more than the visor plus one thin band, so he stays readable.
2. **Hook:** the static burst eases off faster (heavy for 4 frames instead of 9), so SCOPE LOCKED ✓ reads for a moment under the noise before GLITCH tears through. The bass hit is unchanged.
3. **Story (bar 6, Bit's side):** Bit's TEST beams in bar 6 stay, and each tested block gets a small ✓ pop above his window (no new words), so his side keeps moving while ERROR plays out.

**Fix added by Amit for round 2**
4. **Story (Bit's finished game):** the player is now a 20×20 game-px pink hero (4× the old 5-px dot). The stars are 18×18 bright yellow with a twinkling core. On beats 30, 32 and 34 the hero runs to a star, jumps (apex on the beat) and grabs it: a white flash and an 8-ray sparkle, a coin sound, +500 rising off the star and +500 on the HUD score.

## Round 2 — fixes 1–4 applied

Automated checks: 600 frames, 20.000 s of video and audio, AAC peak −6.23 dBFS, and safe zone and 48 px minimum OK on all 600 frames. Bar loudness is unchanged apart from bars 8–9 (−21.7 / −21.0 dB RMS, from the coin and jump sounds).

| # | Criterion | R1 | R2 | Why |
|---|---|---|---|---|
| 1 | Hook | 8 | 9 | The static burst is heavy for only 4 frames, so SCOPE LOCKED ✓ reads under the noise before GLITCH's face tears through (0.5 s) and smirks (1.0 s) over the bass hit. |
| 2 | Readability | 8 | 8 | Every word passes both checks. +500 is 72 px and sits on the game window's title bar: readable, but it shares space with the window chrome. |
| 3 | Beat sync | 9 | 9 | Unchanged. The mini-game's jumps peak and its stars are grabbed on beats 30, 32 and 34, with the coin sound on the same `beats.json` times. |
| 4 | On-model | 7 | 9 | All 12 GLITCH crops in bars 4–9 now show the shift: a 3-px notch through his eyes (typing dashes, smirk, shocked squares, crashed static) plus a second cut through his `{ }` screen or hood rim. He is readable in every one. |
| 5 | Story | 8 | 9 | Bar 6: a ✓ pops above Bit's window on every test, so his side keeps moving under ERROR. Bar 8: a hero you can see at a glance jumps and grabs stars with sparkles and +500, so "it works" reads on a phone next to GLITCH's window being eaten. |
| 6 | Ending | 9 | 9 | Unchanged: the question is the biggest, brightest thing in the last 2 s. |

**Result:** every score is 8 or more, so the film is finished after round 2. The only extra on-screen text beyond the brief's list is `+500`, which Amit asked for in round 2.
