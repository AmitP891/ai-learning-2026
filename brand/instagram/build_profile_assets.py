"""Instagram profile assets: the cropped Bit photo and the reel covers.
Text sits inside the 3:4 grid crop (y 240-1680) so it survives at thumbnail size.
Needs Pillow and cairosvg (on macOS: DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib). Output lands next to this file."""
import io, os, re, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE=os.path.dirname(os.path.abspath(__file__))
W,H=1080,1920
CY=(0,240,255); PK=(255,43,214); GR=(57,255,136); RD=(240,53,158); WH=(255,255,255); BG=(13,13,20); YL=(255,214,0)  # RD is brand pink for "problem" words (was red)
FONTS=os.path.expanduser("~/Library/Fonts")
FI=lambda s: ImageFont.truetype(f"{FONTS}/InterDisplay-Black.otf",s)
FM=lambda s: ImageFont.truetype(f"{FONTS}/DejaVuSansMono.ttf",s)
FMB=lambda s: ImageFont.truetype(f"{FONTS}/DejaVuSansMono-Bold.ttf",s)
SVG=open(os.path.join(HERE,"../bit/bit.svg")).read()
FACELESS=re.sub(r'<path id="mouth"[^>]*/>','',re.sub(r'<g id="eyes">.*?</g>','',SVG,flags=re.S))

def bit(width,mood):
    """Bit with the same happy and shocked faces the videos use."""
    s=width/600
    r=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=FACELESS.encode(),output_width=width,output_height=int(700*s)))).convert("RGBA")
    d=ImageDraw.Draw(r)
    for ex in (244,356):
        cx,cy=ex*s,199*s
        if mood=="happy": d.arc((cx-24*s,cy-14*s,cx+24*s,cy+30*s),200,340,fill=CY,width=int(10*s))
        else: d.ellipse((cx-27*s,cy-31*s,cx+27*s,cy+31*s),fill=CY); d.ellipse((cx-9*s,cy-9*s,cx+9*s,cy+9*s),fill=(23,26,43))
    mx,my=300*s,262*s
    if mood=="happy": d.arc((mx-40*s,my-40*s,mx+40*s,my+12*s),25,155,fill=CY,width=int(9*s))
    else: d.ellipse((mx-12*s,my-12*s,mx+12*s,my+12*s),outline=CY,width=int(7*s))
    return r

def photo():
    """Head only, so the face still reads in a 40 px circle."""
    svg=re.sub(r'<g id="arm-(left|right)">.*?</g>','',SVG,flags=re.S).replace('viewBox="0 0 600 700"','viewBox="84 -28 432 432"').replace('height="700"','height="600"')
    b=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(),output_width=1080,output_height=1080))).convert("RGBA")
    im=Image.new("RGBA",(1080,1080),BG+(255,)); im.alpha_composite(b)
    im.convert("RGB").save(os.path.join(HERE,"profile-photo.png"))

def cover(name,label,tag,lines,mood):
    im=Image.new("RGBA",(W,H),BG+(255,)); d=ImageDraw.Draw(im)
    for y in range(0,H,60): d.line((0,y,W,y),fill=(20,21,32))
    d.text((60,270),label,font=FM(32),fill=CY); d.text((1020,268),tag,font=FMB(36),fill=PK,anchor="ra")
    size=min(FI_fit(t) for t,_ in lines)
    gap=int(size*1.14); y0=400+gap//2
    tl=Image.new("RGBA",(W,H),(0,0,0,0)); td=ImageDraw.Draw(tl)
    for j,(t,c) in enumerate(lines): td.text((W/2,y0+j*gap),t,font=FI(size),fill=c+(255,),anchor="mm")
    im.alpha_composite(tl.filter(ImageFilter.GaussianBlur(16))); im.alpha_composite(tl)
    b=bit(620,mood); top=y0+len(lines)*gap-30
    im.alpha_composite(b,(W//2-b.width//2,max(top,860)))
    im.convert("RGB").save(os.path.join(HERE,"covers",name+".jpg"),quality=93)

def FI_fit(t,maxw=960,mx=190):
    s=mx
    while FI(s).getlength(t)>maxw: s-=2
    return s

COVERS=[
 ("meet-bit-DezeG3dThUR","// meet bit","BIT v1.0",[("I BUILT",WH),("A ROBOT",PK)],"happy"),
 ("requirements-DfDBvW7Tvxo","// the review","TOOL CALLS 9/9",[("6 OF 8",RD),("FLAGGED",WH)],"shock"),
 ("mcp-server-DfILUoZz4DZ","// mcp server","WEEK 3",[("CLAUDE",CY),("FOUND",WH),("MY BUGS",RD)],"shock"),
 ("prompt-fix-De7TREsz3eV","// before vs after","PROMPT v2",[("FROM 5/6",YL),("TO 6/6",GR)],"happy"),
 ("two-bugs-De2C3IgzRqJ","// claude api","BUGS 2/2",[("COURSE",WH),("MISSED",WH),("2 BUGS",RD)],"shock"),
 ("website-De96dVcCiPl","// the fix","vibewithamit.com",[("MY SITE",WH),("WAS WRONG",RD)],"shock"),
 ("prompt-eval-DeuUdi2TUzb","// eval","125 WORDS",[("9/10 AND",YL),("STILL",WH),("FAILED",RD)],"shock"),
 ("first-script-DesG0qcitPh","// first script","chat.py",[("BROKE",RD),("TWICE",RD),("FIRST",WH)],"happy"),
]
if __name__=="__main__":
    os.makedirs(os.path.join(HERE,"covers"),exist_ok=True)
    photo()
    for c in COVERS: cover(*c)
