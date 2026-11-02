# Long-form: How I make faceless YouTube videos with code (no editor, no face)

Target: Sat 14 Nov, 9am. 16:9, about 7 minutes. Idea #66.
Voiceover: one ElevenLabs file, blank line between lines (I split it at the pauses).

## Working title options
1. How I Make Faceless YouTube Videos With Code (No Editor, No Face)
2. I Don't Show My Face. A Robot Made of Code Does It for Me
3. My Entire YouTube Channel Is a Python Script

## Script and visuals

| # | Visual | Voiceover |
|---|---|---|
| 1 | Fast montage: Bit talking, boss fight, REQ X-RAY scan, MCP crash | Every video on this channel was made without a camera, without a face, and without a video editor. |
| 2 | Bit waves; "100% code" stamp | This is Bit. He's a drawing made of code, he talks with my voice, and in two weeks he's pulled in two thousand views. |
| 3 | Bit intro card: Amit, systems engineer | I'm Amit. I'm a systems engineer, not a video editor. So I built the whole pipeline with Claude, and today I'll show you every part of it. |
| 4 | Chapter card: 1. The character | Step one: the character. |
| 5 | bit.svg code scrolling, Bit assembling piece by piece | Bit is an SVG file. Shapes and colours written as code. That means he's sharp at any size, and Claude can edit him like any other file. |
| 6 | Eye expressions grid (idle, blink, happy, shock) | His eyes and mouth are drawn separately, so code can change his expression on any frame. |
| 7 | Chapter card: 2. The voice | Step two: the voice. |
| 8 | ElevenLabs screen (blur account details), waveform | I write the script, then generate it in my own cloned voice. One file, a blank line between each line. |
| 9 | Waveform with pauses highlighted, cut markers dropping in | A script finds the pauses and splits it into lines automatically, so every line can drive its own scene. |
| 10 | Chapter card: 3. Lip-sync | Step three: making him talk. |
| 11 | Loudness meter driving Bit's mouth, side by side | There's no AI lip-sync here. The code measures how loud my voice is thirty times a second. Louder means a bigger mouth. Silence means a smile. |
| 12 | Chapter card: 4. The scenes | Step four: the scenes. |
| 13 | build.py scrolling; frames rendering in a grid | Every scene is Python drawing frames. Text, charts, score tables, even a boss fight. Thirty frames a second, about two thousand frames for a one-minute video. |
| 14 | Synth waveform, beep, whoosh | Even the sound effects are code. Every beep is a sine wave. |
| 15 | Terminal: ffmpeg encoding progress | Then ffmpeg stitches the frames and the voice into an MP4. No timeline. No dragging clips around. |
| 16 | Chapter card: 5. Where Claude comes in | Step five: where Claude comes in. |
| 17 | Chat screenshot: request → finished video | I describe the video I want, Claude writes and runs the code, and I review it like a design review. When something's wrong, I say what, and it fixes it. |
| 18 | Boss-fight critique table 3 → 8 | For bigger pieces I give it a one-page brief, and it scores its own work. My boss fight started at three out of ten and finished at eight. |
| 19 | Chapter card: 6. Honest numbers | So, does it actually work? |
| 20 | Stat cards: 2,000 views, 10 subs, 2 weeks; weakest Short 78 views | Two weeks in: two thousand views and ten subscribers. Not viral. But growing. And the Shorts with Bit beat my plain screen recordings every time. |
| 21 | Pros / cons list | The upside: I never film, every video looks on-brand, and a change is a ten-second re-render. The downside: the first setup took real time, and it's only as good as your script. |
| 22 | Three tips cards | If you want to try it: start with one character, keep it simple, and let the voice carry the video. |
| 23 | GitHub card, Subscribe | The whole pipeline is free on my GitHub. If this helped, like it, share it with someone who wants a faceless channel, and subscribe for the next build. Build it, test it, ship it. |

## Fact check before recording
- Views and subscribers in line 2 and 20: update to the numbers on the day.
- Don't quote ElevenLabs or Claude prices; say "a voice tool" if unsure.
- Blur any account details in screenshots.
