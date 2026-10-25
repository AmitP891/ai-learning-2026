import math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT=(28,24,44)  # outline
JK=(104,98,132); JK2=(128,122,158); SKIN=(190,186,208); SHIRT=(222,220,232); TIE=(120,60,170); HAIR=(236,236,244)
EYE=(0,0,0)
def fog_tail(w,h,t):
    im=Image.new("RGBA",(w,h),(0,0,0,0)); a=np.zeros((h,w),np.float32); yy,xx=np.mgrid[0:h,0:w]
    for i in range(14):
        cx=w/2+math.sin(t*1.3+i*1.7)*w*0.18+ (i-7)*w*0.03; cy=h*0.15+i*h*0.055
        r=w*0.22*(1-i/18)
        a+=np.exp(-(((xx-cx)**2+(yy-cy)**2)/(2*r**2)))
    a=np.clip(a/a.max(),0,1)*np.clip(1-yy/h,0,1)*np.clip(yy/(h*0.3),0,1)*np.clip(1-np.abs(xx-w/2)/(w/2),0,1)**0.7
    im=Image.new("RGBA",(w,h),(185,180,212,0)); im.putalpha(Image.fromarray((np.clip(a*1.6,0,1)*235).astype(np.uint8)))
    return im.filter(ImageFilter.GaussianBlur(4))
_TC={}
def _tail(t):
    k=int(t*6)%36
    if k not in _TC: _TC[k]=fog_tail(440,460,k/6)
    return _TC[k]
QF=ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",56)
def professor(mouth=0.0,t=0.0,mood="smug",scale=1.0):
    W,H=640,1120; im=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(im)
    cx=320
    # body / jacket
    d.polygon([(cx-170,470),(cx+170,470),(cx+150,800),(cx-150,800)],fill=JK,outline=OUT)
    d.rounded_rectangle((cx-175,450,cx+175,560),radius=60,fill=JK,outline=OUT,width=6)
    d.polygon([(cx-170,500),(cx+170,500),(cx+150,800),(cx-150,800)],fill=JK)
    d.line((cx-150,800,cx-170,470),fill=OUT,width=6); d.line((cx+150,800,cx+170,470),fill=OUT,width=6)
    # shirt V + lapels
    d.polygon([(cx-60,455),(cx+60,455),(cx,640)],fill=SHIRT,outline=OUT)
    d.polygon([(cx-60,455),(cx-120,470),(cx-20,700),(cx,640)],fill=JK2,outline=OUT)
    d.polygon([(cx+60,455),(cx+120,470),(cx+20,700),(cx,640)],fill=JK2,outline=OUT)
    # elbow patches hint & pocket with pen
    d.rounded_rectangle((cx+70,600,cx+135,640),radius=8,fill=JK2,outline=OUT,width=4)
    d.rectangle((cx+90,575,cx+98,612),fill=(255,214,0),outline=OUT,width=2)
    # bow tie
    d.polygon([(cx,470),(cx-50,445),(cx-50,500)],fill=TIE,outline=OUT); d.polygon([(cx,470),(cx+50,445),(cx+50,500)],fill=TIE,outline=OUT)
    d.ellipse((cx-14,456,cx+14,484),fill=TIE,outline=OUT,width=3)
    # arm holding pointer (right side of image)
    d.line((cx+165,500,cx+250,600),fill=OUT,width=58); d.line((cx+165,500,cx+250,600),fill=JK,width=46)
    d.ellipse((cx+228,580,cx+278,630),fill=SKIN,outline=OUT,width=5)
    d.line((cx+255,600,cx+300,330),fill=(90,60,30),width=10); d.ellipse((cx+292,318,cx+310,336),fill=(240,240,250))
    # other arm, holding clipboard
    d.line((cx-165,500,cx-210,640),fill=OUT,width=58); d.line((cx-165,500,cx-210,640),fill=JK,width=46)
    d.rounded_rectangle((cx-285,560,cx-165,720),radius=10,fill=(200,170,120),outline=OUT,width=5)
    d.rectangle((cx-268,580,cx-182,700),fill=(245,245,240))
    f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",34); d.text((cx-225,640),"TBD",font=f,fill=(200,40,60),anchor="mm")
    d.ellipse((cx-185,650,cx-140,695),fill=SKIN,outline=OUT,width=5)
    # neck + head
    d.rectangle((cx-30,400,cx+30,460),fill=SKIN,outline=OUT,width=5)
    d.ellipse((cx-130,170,cx+130,440),fill=SKIN,outline=OUT,width=6)
    # wild white hair tufts
    for a in (-1,1):
        for k in range(3):
            x0=cx+a*(118+k*6); y0=230+k*40
            d.ellipse((x0-40,y0-30,x0+40,y0+30),fill=HAIR,outline=OUT,width=4)
    # mortarboard
    d.polygon([(cx-170,165),(cx,115),(cx+170,165),(cx,215)],fill=(40,36,60),outline=OUT)
    d.rectangle((cx-90,165,cx+90,215),fill=(40,36,60),outline=OUT,width=5)
    d.polygon([(cx-170,165),(cx,115),(cx+170,165),(cx,215)],fill=(52,48,76),outline=OUT)
    sw=math.sin(t*2.2)*12
    d.line((cx,165,cx+120+sw,175),fill=(255,214,0),width=5); d.line((cx+120+sw,175,cx+125+sw,240),fill=(255,214,0),width=5)
    d.ellipse((cx+113+sw,232,cx+137+sw,262),fill=(255,214,0))
    # eyebrows (bushy) – mood
    lift=-10 if mood=="shock" else (8 if mood=="angry" else 0)
    for a in (-1,1):
        x=cx+a*55
        tilt=(10*a if mood=="angry" else -6*a)
        d.polygon([(x-45,262+lift-tilt),(x+45,262+lift+tilt),(x+40,282+lift+tilt),(x-40,282+lift-tilt)],fill=HAIR,outline=OUT)
    # round spectacles with ? eyes
    for a in (-1,1):
        x=cx+a*55; d.ellipse((x-42,280,x+42,364),fill=(232,234,248),outline=OUT,width=7)
        q="!" if mood=="shock" else "?"
        d.text((x,322),q,font=QF,fill=(70,60,120),anchor="mm")
    d.line((cx-13,318,cx+13,318),fill=OUT,width=6)
    # nose
    d.ellipse((cx-18,350,cx+18,388),fill=(170,166,192),outline=OUT,width=4)
    # mouth (opens with audio) under moustache
    mh=6+44*mouth
    d.rounded_rectangle((cx-34,392,cx+34,392+mh),radius=int(min(mh,34)/2),fill=(60,30,60),outline=OUT,width=4)
    # big moustache
    for a in (-1,1):
        d.chord((cx-5 if a>0 else cx-85, 370, cx+85 if a>0 else cx+5, 418),180,360,fill=HAIR,outline=OUT,width=4) if False else None
        pts=[(cx,380),(cx+a*30,372),(cx+a*70,382),(cx+a*92,405),(cx+a*70,402),(cx+a*35,396),(cx,398)]
        d.polygon(pts,fill=HAIR,outline=OUT)
    al=np.array(im.getchannel("A")).astype(np.float32); yy=np.arange(H)[:,None]
    al*=np.clip((790-yy)/150,0,1); im.putalpha(Image.fromarray(al.astype(np.uint8)))
    tail=_tail(t); im.alpha_composite(tail,(100,660))
    if scale!=1.0: im=im.resize((int(W*scale),int(H*scale)),Image.LANCZOS)
    return im
if __name__=="__main__":
    bg=Image.new("RGB",(1400,1150),(12,13,26))
    for i,(m,md) in enumerate(((0,"smug"),(0.8,"angry"),(0.4,"shock"))):
        p=professor(m,i,md,0.7); bg.paste(p,(20+i*460,20),p)
    bg.save("prof_preview.png")
