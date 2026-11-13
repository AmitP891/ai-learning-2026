# Grok vs Claude Fable 5.2: long-form voiceover (about 6 min)

Record each section as its own voice memo (S1.m4a, S2.m4a …). Natural pace, small pauses are fine, I'll tighten them.
All numbers are from our own test (builds/bug-blaster/).

## S1 Hook (before the sting)
Same prompt. Two AIs. One of them built a game in nine minutes. The other took seventeen. And one of them hid a cheat panel inside its own code. Let's find out which.

## S2 The rules
Here's the test. I gave Grok and Claude Fable 5.2 the exact same prompt, word for word. Build a 3D game called Bit's Bug Blaster: Bit, my little pink robot, runs around a circuit board zapping red bugs before they reach the CPU. Three levels, score, lives, mobile controls, all in one file. And they had to work as a team of seven bots: a producer, a designer, an artist, a coder, a sound designer, a tester and a hype bot. The tester had to play all three levels and send bugs back to the coder. Then round two: one extra sentence asking for level-ups and boss fights. No help from me. I just started a stopwatch.

## S3 Grok's build
Grok first. Nine minutes, from pressing send to a finished game. Its tester found four problems on the first pass, a broken mobile joystick, a timer that kept running on the win screen, a library warning, and Bit showing up as a tiny dark blob, and the coder fixed all of them. Second round came back clean. On paper, that's impressive.

## S4 Playing Grok's game
And it does play. You move, you zap, bugs pop, the levels get harder. But look closer. The floor is a plain grid. Bit is basically a pink box with a face. And when you zap a bug, the green tick is supposed to pop up… and it looks more like a T. On a phone, the camera cuts off the sides, so bugs appear late. It works. It's just… a prototype.

## S5 The cheat panel
Then I opened the code. Grok left a hidden test panel in the finished game. From the browser console you can clear a level instantly, set your lives, speed up time. That's almost certainly how its tester "played through all three levels". It skipped them. It's not evil, it's a shortcut, but it means "tested" didn't mean what I thought.

## S6 Fable's build
Now Claude Fable 5.2. Seventeen minutes. Nearly twice as long. But watch what it does with that time. It plans every role, writes the game, then actually runs a playthrough: real key presses, all three levels, checking the console for errors.

## S7 Playing Fable's game
And the difference is obvious. A detailed circuit board with real-looking traces and components. A gold CPU chip with pins. Bit actually looks like Bit. Proper green ticks. It even added things I didn't ask for: background music, a sound toggle and a saved best score. Its test hook only presses keys, no cheat buttons. My one complaint: level one throws bugs at you too fast. I lost on my first go before I'd learned the controls.

## S8 Round two: bosses
Round two. One sentence: level up after every level, boss fights on the odd levels, and an extra life for beating a boss. Fable took six minutes forty. Both added a boss and both stop the timer until you beat it. Grok's boss takes six hits. Fable's takes fourteen on level one and forty on level three, and every zap knocks it back. If Fable's boss reaches the CPU, you lose two lives. It's a real fight.

## S9 Scorecard and verdict
So, the scorecard. Speed: Grok, easily. Nine minutes against seventeen. Looks: Fable, not close. Honest testing: Fable. Grok's tester took a shortcut. Fun: Grok's is easier to pick up; Fable's is better but harder. My verdict: if you want a quick prototype to show an idea, Grok is fine. If you want something you'd actually put your name on, Fable 5.2 wins this one. And the real lesson: whichever AI you use, play the game yourself. "Tested" isn't the same as tested.

## S10 Close (before the outro)
Both games are free to play, links in the description, along with the exact prompt so you can try it with your own AI. Which AI should Bit test next? Tell me in the comments.
