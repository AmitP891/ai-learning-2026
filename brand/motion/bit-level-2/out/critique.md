# Bit: Level 2 — critique log

Each round: one frame per beat from the encoded `level2_9x16.mp4` (beat time + 2 frames), scored 1–10 on the brief's six criteria.

## Round 1 — first render

Automated checks on this render:
- **Length:** 600 frames, 20.000 s video and audio.
- **Safe zone and text size:** OK on all 600 frames. No text under the platform buttons, and no capitals under 48 px tall.
- **Sound timing:** every sound is placed sample-exactly at its `beats.json` time in code. Cross-correlating each deterministic event (tones, clangs, gulps, kicks, coin, pop) against the encoded audio puts them all within ±2.3 ms. The noise-based events (bursts, whooshes, charge) and the sustained victory chord can't be located by correlation, because the regenerated noise differs from the rendered noise, so they aren't scored on that check.
- **Audio peak:** **−3.9 dB after AAC** (−6.5 dB before encoding). This fails the brief's −6 dB. The overshoot is on the SHOULD BE EASY hit at 10.0 s.

| # | Criterion | R1 | Why |
|---|---|---|---|
| 1 | Hook | 7 | Frame 0 is real action (Level 1's Professor shattering, Bit in fire pose), but the white flash washes out the first 4 frames, and no words appear until 0.5 s. |
| 2 | Readability | 8 | Every word passes both checks, and the notes never cover Bit's visor or chest panel. SCOPE LOCKED ✓ is small next to BOSS DEFEATED, and ONE MORE THING's text drops out as it leaves the left edge. |
| 3 | Beat sync | 9 | Every word slam, throw, hit, gulp, clang, shrink and cut is on a beat or a half beat from `beats.json`, and the deterministic sounds are within ±2.3 ms. |
| 4 | On-model | 8 | Bit is Level 1's sprite, with idle, blink, hit X X, determined and happy ^ ^ eyes. Scope Creep clearly grows (6 notes up to 10, then off the screen edge) and clearly shrinks (beats 29 → 32), then deflates and pops. |
| 5 | Game feel | 7 | HUD, shake, the boss bar stretching then draining, combos and score roll-up all work. Two problems: the bar 5 dodge is hard to read (ONE MORE THING flies off before you see it pass under Bit), and the mix is 2 dB hotter than spec. |
| 6 | Ending | 8 | SUBSCRIBE / LEVEL 3 is the biggest, brightest thing in the last 2 s and blinks. The final-thump flash greys the whole card on the very last frames. |

**Fixes for round 2**
1. **Hook:** LEVEL 1 slams on beat 1 (frame 0) with the explosion and CLEARED ✓ on beat 2; the coin pulse stays on beat 4. The flash drops to 2 frames at lower strength, so the explosion stays readable.
2. **Game feel (dodge):** ONE MORE THING aims under Bit's front foot, then slides out at half the speed, so it visibly passes under him at the top of his jump.
3. **Game feel (mix):** after encoding, measure the AAC peak and trim the mix until it is at or below −6.0 dB (a re-mux, no frame re-render).
4. **Readability:** SCOPE LOCKED ✓ fits to 960 px, the same width as BOSS DEFEATED.
5. **Ending:** the final-thump flash is softer (about 40% of its current strength), so the last frame stays clean.

**Correction to round 1:** the "−3.9 dB" peak was a measuring error. The critique script decoded the audio with `ffmpeg -ac 1`, and that mono downmix adds about +3 dB, so the real stereo peak in round 1 was about −6.9 dB. The script now measures the stereo stream directly. Fix 3 still went in: the build now measures the encoded AAC peak and sets it to −6.0 dB, as the brief asks.

## Round 2 — after Amit's Gate 4a notes

Changes:
1. **Hook:** LEVEL 1 slams in on frame 0 with the explosion, and CLEARED ✓ on beat 2. The coin pulse stays on beat 4. The flash is 2 soft frames, so the Professor shattering stays readable.
2. **Dodge:** ONE MORE THING passes right under Bit's front foot at the top of his jump, slides out at half the speed, and bursts into paper bits at the left edge, where its text would otherwise drop out.
3. **Mix:** the AAC is encoded, measured and rescaled until the decoded peak sits at −6.0 dB.
4. **SCOPE LOCKED ✓:** 960 px wide would have run under the Shorts button column (the checker caught it on frames 510–532). It is now two lines, SCOPE / LOCKED ✓, each fitted to 800 px, so it is much bigger and still safe.
5. **Final flash:** softened to about 40% of its round 1 strength; the last frames stay clean.
6. **Note text size (Amit):** the attack notes go from 66 px (Level 1's FAST / TBD size) to **81 px**, and SHOULD BE EASY to **96 px**, the biggest. NEXT VERSION also goes to 81 px, so the stamp isn't smaller than the note it replaces. The shield moved 2 px lower so the bigger notes still clear Bit's `</>` panel.

Automated checks on this render:
- **Length:** 600 frames, 20.000 s video and audio.
- **Safe zone and text size:** OK on all 600 frames.
- **Sound timing:** every deterministic event is within ±2.3 ms of `beats.json`.
- **Audio peak:** −6.01 dBFS (stereo, decoded from the AAC in the MP4).

| # | Criterion | R1 | R2 | Why |
|---|---|---|---|---|
| 1 | Hook | 7 | **8** | Frame 0 has LEVEL 1 in big yellow over the Professor exploding into pixels, then CLEARED ✓ half a second later. It's a sequel cold open that tells you what you missed. Not a 9: the rest of bar 1 is debris settling. |
| 2 | Readability | 8 | **9** | The notes are 81 / 96 px dark-on-yellow, larger than any fight word in Level 1. SCOPE LOCKED ✓ now holds its own under BOSS DEFEATED. Everything passes the safe-zone and 48 px checks. |
| 3 | Beat sync | 9 | **9** | Unchanged: every event is on a beat or half beat, and the sounds are within ±2.3 ms. |
| 4 | On-model | 8 | **8** | Bit matches his bible in every expression. Scope Creep grows four times (beats 15, 17, 19, 20 &) until he spills off screen, shrinks on beats 29 & – 31 &, then deflates and pops. |
| 5 | Game feel | 7 | **8** | The dodge reads now: the note goes under Bit mid-jump and bursts at the edge. Hit X X, shake, HP flashes, the boss bar stretching then draining, shield clangs, ×2 ×3 ×4 and the score roll-up all land. |
| 6 | Ending | 8 | **8** | SUBSCRIBE / TO UNLOCK / LEVEL 3 is the biggest, brightest block in the last 2 s, blinking pink/yellow from beat 38 &. The final thump no longer greys the card. PICK THE NEXT BOSS and the handle only get about 1 s each. |

**Every score is 8 or more, so the critique loop stops here, after 2 of the allowed 4 rounds.**
