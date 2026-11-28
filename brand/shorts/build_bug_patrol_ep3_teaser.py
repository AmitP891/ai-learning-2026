"""Bit: Bug Patrol Ep 3 midweek teaser "I see everything" (~10 s, 9:16). Wed 9 Dec 2026, 18:00.
Cut from the Ep 3 clips and Wallhack's voice take; no new Runway credits.
Usage: python3 build_bug_patrol_ep3_teaser.py CLIPS_DIR WALLHACK.mp3 OUT.mp4"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter
CLIPS, VO_WH, OUT = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__)); BANG = os.path.join(HERE, "..", "fonts", "Bangers-Regular.ttf")
B = lambda s: ImageFont.truetype(BANG, s); W, H, BORDER = 1080, 1920, 22; TMP = tempfile.mkdtemp(prefix="bp3t_")

def st(d, xy, t, f, fill, s=8): d.text(xy, t, font=f, fill=fill, stroke_width=s, stroke_fill=(0, 0, 0), anchor="mm")

def card(path):
    fr = f"{TMP}/bg.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "2.5", "-i", os.path.join(CLIPS, "04.mp4"), "-frames:v", "1", fr], check=True)
    bg = Image.open(fr).convert("RGB"); bg = bg.crop((BORDER, BORDER, bg.width - BORDER, bg.height - BORDER)).resize((W, H))
    bg = Image.blend(bg.filter(ImageFilter.GaussianBlur(8)), Image.new("RGB", (W, H), (5, 8, 20)), 0.7); d = ImageDraw.Draw(bg)
    st(d, (W / 2, 560), "BIT: BUG PATROL", B(110), (255, 79, 163), 9)
    for dx, col in ((-9, (0, 230, 255)), (9, (255, 79, 163)), (0, (255, 60, 80))):
        st(d, (W / 2 + dx, 820), "SOMEONE'S", B(220), col, 12 if dx == 0 else 0)
        st(d, (W / 2 + dx, 1030), "CHEATING", B(220), col, 12 if dx == 0 else 0)
    st(d, (W / 2, 1230), "EPISODE 3", B(96), (255, 255, 255), 7)
    d.rounded_rectangle([200, 1330, 880, 1460], 65, fill=(255, 225, 77), outline=(0, 0, 0), width=7)
    d.text((W / 2, 1395), "SAT 12 DEC · 9AM", font=B(80), fill=(17, 17, 17), anchor="mm"); bg.save(path)

def cap(path, text):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); f = B(74); y = 210
    bw = f.getlength(text) + 70; x0 = (W - bw) / 2
    d.rectangle([x0 + 10, y + 10, x0 + bw + 10, y + 130], fill=(0, 0, 0, 200))
    d.rectangle([x0, y, x0 + bw, y + 120], fill=(255, 60, 80, 255), outline=(0, 0, 0, 255), width=6)
    d.text((x0 + 18, y - 22), "WALLHACK", font=B(40), fill=(20, 20, 30), stroke_width=4, stroke_fill=(0, 230, 255))
    d.text((W / 2, y + 62), text, font=f, fill=(255, 255, 255), anchor="mm"); im.save(path)

card(f"{TMP}/card.png"); cap(f"{TMP}/c1.png", "I SEE YOU, LITTLE ROBOT."); cap(f"{TMP}/c2.png", "I SEE EVERYTHING.")
crop = f"crop=iw-{2 * BORDER}:ih-{2 * BORDER}:{BORDER}:{BORDER},scale={W}:{H}:flags=lanczos,setsar=1,fps=30"
fc = (f"[0:v]{crop},trim=0:5.2,setpts=PTS-STARTPTS[a];[1:v]{crop},trim=0.4:2.2,setpts=PTS-STARTPTS[b];"
      f"[2:v]fps=30,scale={W}:{H},setsar=1,trim=duration=3.0,fade=in:st=0:d=0.2[c];[a][b][c]concat=n=3:v=1:a=0[base];"
      "[3:v]format=rgba[o1];[base][o1]overlay=enable='between(t,0.3,2.2)'[v1];[4:v]format=rgba[o2];[v1][o2]overlay=enable='between(t,2.2,5.2)'[v];"
      # audio: Wallhack line through the headset, low drone, glitch hit on the cut, sting on the card
      "[5:a]atrim=0:3.7,asetpts=PTS-STARTPTS,highpass=f=300,lowpass=f=3600,acrusher=bits=10:mix=0.25,adelay=300|300,volume=1.6[vo];"
      "sine=f=55:d=10[dr];[dr]volume=0.25[d1];anoisesrc=d=0.4:c=pink:a=0.5,adelay=5200|5200[gl];"
      "sine=f=110:d=2.5,adelay=7000|7000,volume=0.3[s1];sine=f=165:d=2.5,adelay=7000|7000,volume=0.2[s2];"
      "[vo][d1][gl][s1][s2]amix=inputs=5:normalize=0,atrim=0:10,loudnorm=I=-14:TP=-1.5[aout]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(CLIPS, "04.mp4"), "-i", os.path.join(CLIPS, "01.mp4"),
                "-loop", "1", "-t", "3", "-i", f"{TMP}/card.png", "-loop", "1", "-t", "10", "-i", f"{TMP}/c1.png",
                "-loop", "1", "-t", "10", "-i", f"{TMP}/c2.png", "-i", VO_WH, "-filter_complex", fc,
                "-map", "[v]", "-map", "[aout]", "-r", "30", "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", OUT], check=True)
print("wrote", OUT)
