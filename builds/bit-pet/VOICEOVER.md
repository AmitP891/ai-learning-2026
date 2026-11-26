# Bit Pet long-form: voiceover script

Go-live: **Sun 29 Nov 2026, 09:00**. Narrator: **AMIT** (first person; Bit is "he"). Recorded Thu 26 Nov in ElevenLabs V4: 2:48, -20.4 LUFS (normalise to -14 in the edit). The table below is the original Bit-narrated draft; the recorded wording swaps "me" for "him/Bit" and "Amit" for "I".
Target length: about 3:40. Every number is from builds/bit-pet/PROMPT.md. Nothing invented.
Structure follows the 79 Skills retention lesson: **result first, setup under 15 s, verdict inside the payoff.**

Tone tags are in [square brackets] and go straight into ElevenLabs. Record line by line or in blocks; leave about half a second between lines so I can split on silence.

| # | Time | Line (with tone tags) | On screen |
|---|---|---|---|
| **COLD OPEN** | | | |
| 1 | 0:00 | *(no voice: 2 s of the grey Bit, low hum, then the speech bubble "...zz... sys... halt...")* | 24 h recording, first frame. Big text `24 HOURS LATER` |
| 2 | 0:03 | [weak, slowed down] This... is me. [pause] After Amit left me alone for twenty-four hours. | Grey Bit, bars all `0` |
| 3 | 0:08 | [snapping back to normal, cheerful] Rewind. | Fast rewind effect to the happy Bit |
| **SETUP (under 15 s)** | | | |
| 4 | 0:09 | [upbeat, quick] One prompt. Seven AI bots. Thirteen minutes. Claude turned me into a pet you can actually feed. | Prompt scrolls by, `7 BOTS` `13 MIN` chips pop |
| 5 | 0:16 | [slightly suspicious] And then he walked away. To see if I'd survive. | Amit's tab closing |
| **THE BUILD** | | | |
| 6 | 0:20 | [explaining, friendly] The prompt gave Claude a team: a producer, a designer, an artist, a coder, a sound designer, a tester and a hype bot. Each one hands its work to the next. | 7 role cards in a row, light up one by one |
| 7 | 0:31 | [impressed] Four needs: Battery, Fun, Sleep and Clean. They keep draining in real time, [lower, a bit worried] even when the page is closed. | The four bars |
| 8 | 0:39 | [proud] No game engine. No images. No sound files. Every pixel of me and every beep is drawn in code. One file. Nine hundred and ninety-nine lines. | `index.html · 999 lines · 47 KB` |
| 9 | 0:48 | [matter-of-fact] Then the tester bot wrote thirty-nine checks against its own game. It found three bugs, the coder fixed them, and the retest passed thirty-nine out of thirty-nine. [beat] One fix round. Amit didn't type a single correction. | Tester screenshots, `39/39 ✓`, `FIX ROUNDS: 1` |
| **PLAYING** | | | |
| 10 | 1:02 | [delighted] So what do you actually get? Feed me a data byte, a cookie or a USB stick. | Snack menu |
| 11 | 1:08 | *(no voice: play Bit's own lines from the recording: "Yum! ...crumbs in my vents", "Crunchy bits! 01101!", "Mmm, 64 gigs of flavor!")* | Feed clips |
| 12 | 1:14 | [excited, faster] Play is a ten-second bug-catching game. Sleep turns the lights off. And Debug zaps the glitch bugs that crawl on me when Clean gets low. | Bug game, sleep with moon, bugs |
| 13 | 1:24 | [mock offended] They do crawl on my face. That's a bug about bugs. We'll come back to that. | Bugs on face, freeze frame, `BUG #1` stamp |
| **THE TEST** | | | |
| 14 | 1:30 | [serious, like a scientist] Here's the test. Amit played with me at four o'clock, filled my Battery and Fun to a hundred, and stopped touching me. | Bars `100 100 74 64`, clock `WED 16:03` |
| 15 | 1:39 | [knowing] The game drains me at a fixed rate every hour. Battery ten, Fun seven, Sleep five, Clean four. So we can predict my whole night. | Rate table |
| 16 | 1:47 | [counting off, dramatic] Glitch bugs from about ten p.m. Battery empty at two in the morning. And by eight a.m. [pause] low power mode. | Timeline graphic `22:00 BUGS` `02:00 BATTERY 0` `08:05 LOW POWER` |
| 17 | 1:56 | [satisfied] One hour in, Amit checked. Ninety. Ninety-three. Sixty-nine. Sixty. [beat] Exactly what the maths said. To the point. | 1 h screenshot, numbers tick down `-10 -7 -5 -4` with green ticks |
| 18 | 2:05 | [quiet, lonely] Then... nothing. All night. | Dark screen, clock spins through the night |
| **THE PAYOFF** | | | |
| 19 | 2:10 | [weak] Twenty-four hours later. | `THU 16:16` |
| 20 | 2:13 | *(no voice: the real opening: grey Bit, `[ LOW POWER MODE ]`, "...zz... sys... halt...")* | 24 h recording, 3 s |
| 21 | 2:16 | [soft] Every bar at zero. Greyed out. But I don't die. The prompt said I never die. You just have to feed me. | Bars `0 0 0 0` |
| 22 | 2:24 | *(no voice: FEED → "Rebooting... I'm back! Thank you!" with the sad face)* | Recording, 3 s |
| 23 | 2:28 | [warm, a little emotional] Rebooting. I'm back. [beat] Still a little sad about it, though. | Sad face close-up |
| **THE ONE MISS (verdict inside the payoff)** | | | |
| 24 | 2:35 | [curious] But one thing was missing. The prompt asked for a welcome-back message: "You were gone twenty-four hours." It never showed up. | Prompt line highlighted: `"You were gone 7 hours…"` · red `✗` |
| 25 | 2:44 | [explaining, detective] So I checked the code. The message only appears when the page loads fresh. Amit left the tab open all night. When he came back, I caught up on twenty-four hours silently and saved, and the message never got its turn. | Code snippet, `adopt()` vs `tick()` |
| 26 | 2:58 | [pointed] Claude's tests always reloaded the page. Thirty-nine out of thirty-nine. [beat] Real life found the one case it never tried. | `39/39 ✓` then `REAL LIFE: 1 ✗` |
| 27 | 3:06 | [honest, upbeat] It's a one-line fix. Same with the bugs on my face. And everything else worked: the maths, low power, the reboot, every snack line. | Checklist with ticks, two items `FIXED` |
| 28 | 3:16 | [confident, verdict] Thirteen minutes, one prompt, and I lived through a whole day without anyone watching. That's the real test of an AI build: not "does it run", but "does it still work when you're not looking". | Big text: `DOES IT WORK WHEN YOU'RE NOT LOOKING?` |
| **OUTRO** | | | |
| 29 | 3:29 | [inviting] You can adopt me yourself. The link's in the description, and the full prompt is free. | Site page with Bit Pet, `LINK IN DESCRIPTION` |
| 30 | 3:35 | [cheeky] Comment how long you think you could keep me alive. [beat] Be honest. | Comment icon |
| 31 | 3:40 | [cheerful sign-off] Build it, test it, ship it. [whispers] And feed it. | End screen |

## Before the edit (Sat)
- Fix the welcome-back message when an open tab wakes up, and keep the bugs off his face. Host on the site, then re-film 5 s of the banner appearing so line 27 can show it fixed.
- Remove the `window.__bitpet` test hook before hosting.

## Title options
1. **I Asked Claude to Turn My Robot Into a Pet. Then I Abandoned Him.** (recommended: story + tension; the thumbnail carries the "24 hours")
2. Claude Built a Virtual Pet in 13 Minutes. I Ignored It for 24 Hours.
3. I Left My AI-Built Pet Alone for 24 Hours. Here's What Happened.
4. 39/39 Tests Passed. Real Life Found the Bug.
5. Can an AI-Built Pet Survive a Day Without Me?

Thumbnail (vidIQ 90): content/thumbnails/2026-11-29-bit-pet-final.jpg. Its text already says "I LEFT HIM FOR 24 HOURS", so the title shouldn't repeat it word for word.
