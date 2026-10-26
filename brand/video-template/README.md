# Bit video pipeline: made with code

Every video on [Vibe with Amit](https://vibewithamit.com) is drawn by code. No video generator, no animation app: Python scripts written with Claude turn a voiceover into a finished vertical or landscape video.

## How it works

1. **Bit is an SVG** ([`../bit/bit.svg`](../bit/bit.svg)): rectangles, circles and lines. The scripts render it with `cairosvg` and draw his eyes and mouth on top each frame.
2. **Lip sync**: the voiceover (an ElevenLabs MP3) is decoded with `ffmpeg`, its loudness measured 30 times a second (RMS), and that number sets how far Bit's mouth opens.
3. **Scenes** are drawn frame by frame with `Pillow`: cards, captions, code panels, waveforms, all timed to the pauses in the voiceover.
4. **Sound effects** are synthesised with `numpy`: every beep is a decaying sine wave, every "zap" is filtered noise.
5. **Render**: raw frames are piped into `ffmpeg` with the mixed audio and encoded as H.264 MP4 (1080x1920 for Shorts, 1920x1080 for long-form).

Professor Vague (the villain in *The Adventures of Bit*) is drawn the same way in [`../adventures/prof.py`](../adventures/prof.py); his fog is a sum of Gaussian blobs.

## Run one

```bash
pip install numpy pillow cairosvg
# needs ffmpeg and the DejaVu / Inter fonts installed
python3 build_meet_bit_video.py voiceover.mp3 ../bit
```

Most scripts expect the voiceover next to them (see the top of each file) and write an MP4 in the same folder. They were written for this channel, so expect to edit paths, timings and text for your own videos.

| Script | Video |
| --- | --- |
| `build_meet_bit_video.py` | Meet Bit |
| `build_eval_video.py`, `build_prompt_fix_video.py` | Prompt evaluation episodes |
| `build_requirements_video.py`, `build_mcp_video.py` | Requirements checker and MCP episodes |
| `build_website_video.py` | Website glow-up |
| `build_vague_req_of_week.py` | Vague Requirement of the Week |
| `build_made_with_code.py` | This behind-the-scenes Short |
| [`../adventures/`](../adventures/) | The Adventures of Bit (16:9 episodes) |
