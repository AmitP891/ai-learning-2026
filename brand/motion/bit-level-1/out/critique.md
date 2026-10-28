# Bit: Level 1 — critique log

Method: one frame per beat (beat time + 2 frames, 40 frames) pulled from the encoded MP4, plus three automated checks:
the Shorts safe zone on every frame, the cap height of every on-screen word, and the timing of every sound hit in the encoded audio against `beats.json`.

## Round 1 — first render (`teaser_9x16.mp4`, 600 frames, 20.000 s)

| # | Criterion | Score | Why |
|---|---|---|---|
| 1 | Hook | **3** | Beats 1–4 are black with only "PRESS START" blinking. Nothing moves and no character appears until 2 s, so there's no reason to stop scrolling. |
| 2 | Readability | **6** | "THE ADVENTURES OF BIT" is shrunk to a 44 px cap height (minimum 48). The BOSS: PROFESSOR VAGUE card (beats 13–16) and the REQUIREMENTS CHECK v2 meter (beats 25–28) cover Bit. On beat 37, TESTABLE ✓ rises straight through THE ADVENTURES OF BIT. |
| 3 | Beat sync | **8** | All 28 sound hits in the encoded audio land within 3.1 ms of `beats.json` (mean −1.1 ms; one frame is 33 ms). Every word slam, hit, combo and cut is on a beat or half beat. |
| 4 | On-model | **7** | Bit is the real SVG and every expression is present; the Professor comes from `prof.py`. But Bit's eyes stay a fixed 7×9 px, and at that size "determined" barely differs from "idle". |
| 5 | Game feel | **6** | The HUD, shake, combo and score all work. But TBD keeps flying after it hits Bit, and ADEQUATE drifts slowly for two beats after missing. Bit is small next to the boss, and the charge meter hides him during his power-up. |
| 6 | Ending | **6** | COMING 2027 and TESTABLE ✓ are big and clear, but THE ADVENTURES OF BIT is tiny, there's the collision on beat 37, and the hero is small on the end card. |

### Viewer notes from Amit (included in this round)
1. **Hook:** replace the black opening with a 1 s cold open of the bar 8 beam hit (×3, WITHIN 200 ms, shake), then a hard cut to PRESS START over the level, with the Professor on screen by 2 s.
2. The BOSS: PROFESSOR VAGUE card must never cover Bit.
3. Scale Bit up about 1.3× in the fight and on the end card, keeping him inside the safe zone.
4. Make THE ADVENTURES OF BIT as big as COMING 2027.
5. Keep the 120 BPM grid (move events instead of breaking sync) and keep the film at exactly 20 s.

### Fixes for round 2
**Hook (3)**
- **Cold open, beats 1–2 (frames 0–29):** a replay of film time beat 30 & → 31 &. The TBD → 10 MB/s hit and **×3** land at 0.5 s (beat 2), with WITHIN 200 ms already on screen and the shake. The same slice of audio is copied in, so it lands on the beat with its own laser, ding and music.
- **Hard cut on beat 3 (1.0 s, frame 30)** to PRESS START over the level, not black. The coin stays on beat 4.
- **Professor on screen from 1.0 s:** he lurks low in the fog, head and shoulders showing, and still rises fully on beat 13 as in the grid. The bar 2 title card sits over the dimmed level with him in it.

**Readability (6)**
- **Boss card:** moved to y≈700, in the gap between the HUD and Bit's head. It no longer overlaps Bit.
- **Charge meter:** moved to the top, under the HUD (y 360–510). The Professor drops 36 game px so the meter doesn't cover his face.
- **Bar 8 restaging:** the "shield" stack no longer fits above a larger Bit. Instead the Professor throws one word per beat, and Bit shoots it out of the air on the beat. WITHIN 200 ms and 10 MB/s then float up and stay parked at the top left; USER-FRIENDLY and ADEQUATE burst. Hits stay on beats 29, 30, 31 and 32.
- **Beat 37 collision:** TESTABLE ✓ rises on beat 36 & (finished by beat 37) and BOSS DEFEATED clears first, so THE ADVENTURES OF BIT slams into empty space.
- **New size check:** `build.py` will fail any frame where a word's capitals are under 48 px tall.

**Ending (6)**
- THE ADVENTURES OF BIT is set on two lines ("THE ADVENTURES" / "OF BIT") at exactly the same size as COMING 2027. All three lines use the largest size that fits the 800 px safe width.
- Bit stands centre stage at 1.3×, under the text block.

**Game feel (6) and On-model (7)**
- **Bit 1.3×:** 156 game px tall, standing at x=76 so he isn't clipped at the left edge. His jump goes up from 48 to 60 px so FAST still clears his feet. ADEQUATE's miss is raised to stay above his antenna.
- **Eyes:** they now scale with Bit, and "determined" gets a clear flat, lowered top with the inner corners cut down like brows.
- **TBD on impact:** it now bursts into pixels when it hits Bit.
- **Misses:** a word that misses speeds up and leaves the screen within half a beat.
- **Unchanged:** beat sync. No event leaves its beat, and the film stays at 600 frames.

## Round 2 — after the round 1 fixes (`teaser_9x16.mp4`, 600 frames, 20.000 s)

All round 1 fixes and Amit's four notes are in. Two bugs turned up while checking the new cut and are fixed in this render:
1. **Cut one frame late:** beat 3 falls at 1.0015 s, just after frame 30 (1.000 s), so the cold open spilled one frame (the ×4 hit) past the cut. The cut and the copied audio are now both placed on the frame nearest the beat.
2. **Professor missing from frame 30:** his "on stage" test had the same 1.5 ms edge, so frame 30 showed PRESS START without him. He's now there from the cut.

Automated checks on this render:
- **Safe zone and text size:** OK on all 600 frames. No text under the platform buttons, and no capitals under 48 px tall.
- **Sound timing:** all 36 hits in the encoded audio (including the copied cold-open hits) land within 3.1 ms of `beats.json` (mean −1.1 ms).
- **Audio peak:** −6.4 dB in stereo, −6.5 dB before encoding.

| # | Criterion | R1 | R2 | Why |
|---|---|---|---|---|
| 1 | Hook | 3 | **8** | Frame 0 is mid-fight: beam, ×2, screen shake, WITHIN 200 ms on screen. ×3 slams on beat 2, then a hard cut on beat 3 to PRESS START over the level, with the Professor lurking in the fog from 1.0 s. Not a 9, because the PRESS START second itself is quiet: only his idle bob and the blink. |
| 2 | Readability | 6 | **8** | Every word passes both checks. The boss card (y 712–940) clears Bit's head (y 960), and the charge meter sits under the HUD, so nothing covers Bit. The beat 37 collision is gone. The end card is dense, with six lines in the top half. |
| 3 | Beat sync | 8 | **9** | All 36 sound hits are within 3.1 ms. The cut, every word slam, throw, hit and combo is on a beat or half beat. |
| 4 | On-model | 7 | **8** | Bit is 1.3× and his eyes scale with him. "Determined" now has a flat, lowered top with brow-cut inner corners, clearly different from "idle"; X X, ^ ^ and the blink all read. The Professor is the real `prof.py` drawing in all four moods. |
| 5 | Game feel | 6 | **8** | Bar 8 is now a real shoot-'em-up beat: a word pops out of his pointer and Bit shoots it out of the air, four times. TBD bursts on Bit, misses speed off screen, and there's a hit flash, shake, combo slam, boss bar drain and score roll-up. |
| 6 | Ending | 6 | **8** | THE ADVENTURES / OF BIT and COMING 2027 use the same size (the largest that fits the safe width). TESTABLE ✓ finishes rising before the end card arrives, and a 1.3× happy Bit is centre stage. THE GAME is set at 0.8× that size. |

**Every score is 8 or more, so the 9:16 critique loop stops here, after 2 of the allowed 4 rounds.**
Still to do: the 16:9 re-layout (`teaser_16x9.mp4`).

## Final pass — Amit's Gate 4b notes, plus the 16:9 version

**Changes (both versions)**
- **THE GAME:** now the same size as the other end-card title lines.
- **Slam overshoot:** a slam-in is now capped so the enlarged word stays fully on screen as well as out of the safe zone. A word sliding in or out (HUD, boss card) is drawn only once it's fully on screen. The per-frame check now also fails any word drawn partly off screen.
- **`.gitignore`:** ignores `.venv/`, `.DS_Store` and `out/**/*.png`. The `**` is needed because the brief's `out/*.png` wouldn't match `out/style_frames/`.
- **16:9 (`teaser_16x9.mp4`):** a re-layout of the same timeline, audio and beat grid.
  - **HUD:** a single top band, with BIT and HP on the left, PROFESSOR VAGUE and the boss bar in the middle, and SCORE on the right.
  - **Fight:** Bit on the left and the Professor on the right, with the boss card placed clear of both.
  - **Big text:** BOSS DEFEATED on one line, and THE ADVENTURES OF BIT on one line at the same size as THE GAME and COMING 2027. The text sits on a plate to the right of a happy Bit.

**Bug found and fixed:** the round 2 render had the wrong audio in the cold open. When the cut was moved to beat 3's exact frame, the audio source offset was computed as "cut + offset", so frames 0–29 played film audio from 15.5 s (the ×4 hit and the explosion) instead of 14.5 s. It turned up as hit-timing error rising from 3.1 ms to 11.8 ms. It's fixed: the cold-open audio now matches film time 14.5 s (correlation 0.99), and the hits are back within 3.1 ms.

**Checks on the final renders**
| | 9:16 | 16:9 |
|---|---|---|
| Frames / length | 600 / 20.000 s (video and audio) | 600 / 20.000 s (video and audio) |
| Text on screen, 48 px minimum | OK, all 600 frames | OK, all 600 frames |
| Shorts safe zone | OK, all 600 frames | not applicable (long-form) |
| Sound hits vs `beats.json` | 36 hits, max 3.1 ms | 36 hits, max 3.1 ms |
| Audio peak | −6.5 dB | −6.5 dB |

Scores stay as in round 2: every criterion 8 or more.
