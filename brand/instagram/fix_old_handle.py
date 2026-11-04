"""Replace the burned-in @gymvibecoder strip on the two oldest reels with @vibewithamitai.
Originals in content/videos stay as they are. New files land in reuploads/. Needs Pillow and ffmpeg."""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont
HERE=os.path.dirname(os.path.abspath(__file__)); VIDS=os.path.join(HERE,"../../content/videos")
TXT="Code in bio  |  @vibewithamitai"; INK=(195,195,200); BG=(13,13,20)
FONT=ImageFont.truetype(os.path.expanduser("~/Library/Fonts/DejaVuSans.ttf"),38)
REELS=[("2026-10-18-first-claude-api-script",1700),("2026-10-19-prompt-eval",1760)]  # top of the old strip
for name,y in REELS:
    strip=Image.new("RGB",(1080,60),BG); ImageDraw.Draw(strip).text((540,30),TXT,font=FONT,fill=INK,anchor="mm")
    png=os.path.join(HERE,"reuploads",f"strip-{y}.png"); strip.save(png)
    subprocess.run(["ffmpeg","-y","-v","error","-i",os.path.join(VIDS,name+".mp4"),"-i",png,"-filter_complex",f"[0][1]overlay=0:{y-10}","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",os.path.join(HERE,"reuploads",name+"-new-handle.mp4")],check=True)
    os.remove(png)
