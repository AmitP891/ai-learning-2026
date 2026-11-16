# Bit's Maze Muncher: the shared prompt (video 22 Nov)

Video: "Can Claude Make Pac-Man? Then I Gave It 79 Game-Dev Skills" (Opus 5.5, two runs)

- **Run 1: Opus alone** in `builds/pac-bit/opus/`. Do this BEFORE installing the skills.
- **Run 2: skills installed but not used** in `builds/pac-bit/opus-skills/`, after installing
  [awesome-gamedev-agent-skills](https://github.com/gamedev-skills/awesome-gamedev-agent-skills) (Apache-2.0):
  ```
  claude plugin marketplace add gamedev-skills/awesome-gamedev-agent-skills
  claude plugin install router@awesome-gamedev-agent-skills
  claude plugin install web-engines@awesome-gamedev-agent-skills
  claude plugin install disciplines@awesome-gamedev-agent-skills
  ```
  Same prompt word for word, fresh Claude Code session. Note which skills it loads (shown in the session). Claude never called them.
- **Run 3: skills forced on** in `~/pac-bit/opus-skills-on/`: same prompt with one first line added: "Before you start, use the router skill to load the right game-dev skills, and use them throughout."

Give this to Opus 5.5 **word for word** in a fresh Claude Code session inside each run's empty folder.
Start a screen recording ("Record Entire Screen") and note the clock time when you press Enter.

```
You are a team of 7 bots building a game together. Play each role in order,
label each section with the bot's name, and hand work to the next bot.

Bots: Producer, Game Designer, Artist, Coder, Sound Designer, Tester, Hype Bot.

THE GAME: "Bit's Maze Muncher"
A maze-chase arcade game in the spirit of the 1980s classics, but every design
is original.
- Bit is a small, cute pink robot with a dark visor showing two glowing cyan eyes
  and a small screen on his chest. He is seen from directly above.
- The maze is a neon circuit board. Corridors are filled with small glowing
  "data bits" for Bit to collect.
- 4 glitch bugs chase him, each with its own colour and its own chase style
  (one hunts him directly, one cuts him off ahead, one wanders, one is shy).
- 4 big "antivirus chips" in the corners: eat one and the bugs turn blue and
  flee for a few seconds, and Bit can zap them for bonus points.
- Clear every data bit to finish the level. 3 levels, faster bugs each time.
- 3 lives. Score, best score, level and lives on screen. Arrow keys or WASD;
  on mobile, swipe to turn.

RULES
- One single index.html file. Plain JavaScript and canvas (no libraries).
  No image or sound files: draw everything in code and use Web Audio.
- Original designs only: no real game characters, ghost shapes, logos, names
  or music from any existing game.
- Must run by opening the file in Chrome. No errors in the console.
- Tester must play through all 3 levels and report what's broken; Coder fixes it.
  Maximum 2 fix rounds.

At the end, give me: the final index.html in full, the tester's last report,
and the Hype Bot's 3 title ideas.
```

## Results
| | Run 1: Opus alone | Run 2: skills installed, NOT used | Run 3: skills forced on |
|---|---|---|---|
| Date | 16 Nov 2026 | 16 Nov 2026 | 16 Nov 2026 |
| Time (send to finished) | 27m 43s | 12m 50s | 15m 12s |
| Fix rounds | 2 labelled, 3-4 in practice (admitted it broke the 2-round limit) | 2 (kept the limit; round 2 found nothing new) | 1 fix round (round 1 found 3 bugs; round 2 clean) |
| Lines | 911 (41 KB) | |  |
| Skills loaded | n/a | none (Claude never called them) | router → game-ai, input-systems, audio-design, game-ui-ux (not game-feel) |
| Notes | Neon circuit maze, 4 named bugs (ZAPP, SNIP, WOBBLE, SHY) with their own chase styles, chips, title/game-over screens, sound. Amit lost all 3 lives on level 1 (2,770 pts). Tester's own autopilot also died on L1 with 3 lives; needed 99 lives to win (20 deaths). Hidden debug hook window.__bitDebug (setLives). Titles: Glitch Patrol / Byte Night / Circuit Crunch. | Tester autopilot won all 3 levels in 2 of 3 runs on 3 lives; tested phone 390x844 layout; fixed blue bugs blending into L1 walls. Titles: Byte Club / Glitch Panic! / Debug or Be Bugged. | Tester bot won with 2 lives left (9,810); second bot run lost with 8 bits left. Bug state machine, BFS home, buffered turns, music ducking, auto-pause. Titles: Glitch Panic! / Byte Night / Bit Rush. |
