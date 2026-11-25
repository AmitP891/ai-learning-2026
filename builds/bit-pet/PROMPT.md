# Bit Pet: the prompt and test plan (long-form, Sun 29 Nov 2026, 09:00)

Promised at the end of "I Gave Claude 79 Game-Dev Skills. It Ignored Them.": "Next week: Bit becomes a pet you can actually feed."

**Working title:** I Asked Claude to Turn My Robot Into a Pet. Then I Ignored It for 24 Hours.
**The test:** one build by Claude (Opus 5.5) in a fresh Claude Code session, then a real 24-hour neglect test. Does Bit get hungry, sad and buggy while the tab is closed, and does he forgive you?

## Run it
1. Make an empty folder `~/bit-pet/opus/`, open a fresh Claude Code session in it.
2. Start a screen recording ("Record Entire Screen"), note the clock time, paste the prompt below word for word.
3. When it's done, open `index.html` in Chrome, play for 2 minutes on camera (feed, play, debug, sleep).
4. Then the 24-hour test below. Don't open the tab in between check-ins.

```
You are a team of 7 bots building a game together. Play each role in order,
label each section with the bot's name, and hand work to the next bot.

Bots: Producer, Game Designer, Artist, Coder, Sound Designer, Tester, Hype Bot.

THE GAME: "Bit Pet"
A virtual pet game in the spirit of the 1990s pocket pets, but every design is
original. The pet is Bit: a small, cute pink robot with a square head, a dark
screen face with two glowing cyan eyes, a short antenna with a cyan ball, and a
small screen on his chest showing </>.

- Four needs, each 0-100, shown as bars: Battery (food), Fun, Sleep, Clean.
- Actions: FEED (choose a snack: a data byte, a cookie, a USB stick), PLAY (a
  10-second tap-the-bug mini-game), SLEEP (lights off, Bit snores), DEBUG (zap
  the glitch bugs crawling on him).
- Needs drop over real time, even while the page is closed: save the state and a
  timestamp in localStorage and catch up when the page reopens. Battery drops
  fastest. Purple glitch bugs appear when Clean is low.
- Bit's face and chest screen show his mood: happy, hungry, bored, sleepy,
  buggy, and sad if everything is low. He says a short line for each mood.
- If every need hits 0, Bit goes into "low power mode" (greyed out, slow
  blinking) but never dies; feeding him wakes him up.
- Show how long you were away when you come back ("You were gone 7 hours…").
- Works on desktop and mobile (tap buttons, portrait layout).

RULES
- One single index.html file. Plain JavaScript and canvas (no libraries).
  No image or sound files: draw everything in code and use Web Audio.
- Original designs only: no real pet-game characters, shapes, logos or names.
- Must run by opening the file in Chrome. No errors in the console.
- Tester must test every action and the time catch-up (fake a 24-hour gap by
  changing the saved timestamp) and report what's broken; Coder fixes it.
  Maximum 2 fix rounds.

At the end, give me: the final index.html in full, the tester's last report,
and the Hype Bot's 3 title ideas.
```

## The 24-hour neglect test (screenshot or screen-record each check-in)
| Check-in | When | Record |
|---|---|---|
| 0 h | right after the build, all bars full | bars, mood, line |
| 1 h | | bars, mood, "you were gone" message |
| 8 h | e.g. next morning | bars, mood, any bugs |
| 24 h | same time next day | bars, mood, low power? then feed him and record his reaction |

Write the real numbers here; nothing in the video is made up.

## Results
| | Value |
|---|---|
| Date | 25 Nov 2026 (Opus 5.5, fresh session in ~/pac-bit/bit-pet) |
| Time (send to finished) | recording 15:38–15:51; index.html saved 15:46 (about 8 min after start) |
| Fix rounds | (from the session: TBC) |
| Lines / size | 999 lines, 47 KB |
| Bugs the tester found | |
| 1 h / 8 h / 24 h bars | |
| What broke in real life (if anything) | |

## Catch-up check (Claude, headless Chrome, 25 Nov): faked gaps from full bars
No console errors. Rates per awake hour: Battery -10, Fun -7, Sleep -5, Clean -4 (asleep: Sleep +120).

| Away | Battery | Fun | Sleep | Clean | Mood / line |
|---|---|---|---|---|---|
| 1 h | 90 | 93 | 95 | 96 | happy, "Beep boop! Life is good." |
| 8 h | 20 | 44 | 60 | 68 | hungry, "Battery low... snack please?" |
| 24 h | 0 | 0 | 0 | 4 | sad + glitch bugs, "I need a lot of help..." |
| 26 h | 0 | 0 | 0 | 0 | low power mode (grey), "...feed... me..." |

From full bars Bit hangs on for 24 hours with Clean at 4 and only hits low power at about 25 hours. A new pet starts at 80, not 100.
Screens: catchup-test.png
