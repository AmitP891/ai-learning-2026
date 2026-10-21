"""Bit presenter video: "Meet Bit" channel intro (21 Oct 2026).

Usage:  python3 build_meet_bit_video.py voiceover.mp3 ../bit
Needs thumbA.png and thumbB.png (stills from two earlier videos) in the working folder.
"""
import os; os.makedirs("frames", exist_ok=True)
import re, math, subprocess, numpy as np, cairosvg, io, wave, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageOps
A=sys.argv[1]; MDIR=sys.argv[2]
FPS=30; SR=44100
raw=subprocess.run(["ffmpeg","-v","error","-i",A,"-f","s16le","-ac","1","-ar",str(SR),"-"],capture_output=True).stdout
voice=np.frombuffer(raw,np.int16).astype(np.float32)/32768
VD=len(voice)/SR; DUR=VD+1.3; N=int(DUR*FPS); hop=SR//FPS
rms=np.array([np.sqrt(np.mean(voice[i*hop:(i+1)*hop]**2)) if i*hop<len(voice) else 0 for i in range(N)])
env=np.clip((rms-0.01)/(np.percentile(rms[rms>0.01],90)-0.01),0,1); env=np.convolve(env,[.25,.5,.25],"same")
svg=open(f"{MDIR}/bit.svg").read()
svg=re.sub(r'<g id="eyes">.*?</g>','',svg,flags=re.S); svg=re.sub(r'<path id="mouth"[^>]*/>','',svg)
S=1.35
base=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(),output_width=int(600*S),output_height=int(700*S)))).convert("RGBA")
designs=[Image.open(f"{MDIR}/{k}.png").convert("RGBA").resize((300,350),Image.LANCZOS) for k in ("vibe","bit","loop")]
def thumb(p):
    im=Image.open(p).convert("RGB").resize((330,587),Image.LANCZOS); return im
thA,thB=thumb("thumbA.png"),thumb("thumbB.png")

def yt_icon(size):
    ic=Image.new("RGBA",(size,size),(0,0,0,0)); d=ImageDraw.Draw(ic)
    h=int(size*0.72); y0=(size-h)//2
    d.rounded_rectangle((0,y0,size-1,y0+h),radius=int(size*0.22),fill=(255,0,0,255))
    cx,cy=size//2,size//2; r=int(size*0.2)
    d.polygon([(cx-r*0.8,cy-r),(cx-r*0.8,cy+r),(cx+r*1.05,cy)],fill=(255,255,255,255))
    return ic
def ig_icon(size):
    g=Image.new("RGBA",(size,size)); px=g.load()
    stops=[(0,(254,218,117)),(0.35,(250,126,30)),(0.6,(214,41,118)),(0.8,(150,47,191)),(1,(79,91,213))]
    for y in range(size):
        for x in range(size):
            u=min(1,max(0,((x)+(size-y))/(2*size)))
            u=1-u
            for i in range(len(stops)-1):
                if stops[i][0]<=u<=stops[i+1][0]:
                    k=(u-stops[i][0])/(stops[i+1][0]-stops[i][0]); a,b=stops[i][1],stops[i+1][1]
                    px[x,y]=tuple(int(a[j]+(b[j]-a[j])*k) for j in range(3))+(255,); break
    m=Image.new("L",(size,size),0); ImageDraw.Draw(m).rounded_rectangle((0,0,size-1,size-1),radius=int(size*0.28),fill=255)
    g.putalpha(m); d=ImageDraw.Draw(g); w=max(3,size//14)
    p=int(size*0.18); d.rounded_rectangle((p,p,size-p,size-p),radius=int(size*0.18),outline=(255,255,255,255),width=w)
    c=size//2; r=int(size*0.17); d.ellipse((c-r,c-r,c+r,c+r),outline=(255,255,255,255),width=w)
    rr=max(2,size//22); d.ellipse((size-p-int(size*0.16)-rr,p+int(size*0.10)-rr,size-p-int(size*0.16)+rr,p+int(size*0.10)+rr),fill=(255,255,255,255))
    return g
YT=yt_icon(84); IG=ig_icon(84)
CY=(0,240,255); PK=(255,43,214); GR=(57,255,136); RD=(255,70,90); WH=(255,255,255); GY=(170,175,190); BG=(13,13,20)
F=lambda n,s: ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{n}.ttf",s)
B96,B84,B70,B56,B44,B36=[F("DejaVuSans-Bold",s) for s in (96,84,70,56,44,36)]
R34=F("DejaVuSans",34); M34,MB38,M44=F("DejaVuSansMono",34),F("DejaVuSansMono-Bold",38),F("DejaVuSansMono",44)
# timeline from pauses
T_FACE=3.43; T_DES=5.83; T_WON=8.23; T_MEET=9.53; T_FACESHOWS=10.59; T_HAPPY=12.88; T_SHOCK=14.30; T_WEEK=16.10
T_WINS=19.30; T_BUGS=20.13; T_FOLLOW=21.36
def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3
def mood_at(t):
    if T_HAPPY<=t<T_SHOCK-0.1 or T_WINS<=t<T_BUGS or t>=T_FOLLOW: return "happy"
    if T_SHOCK<=t<T_WEEK-0.3 or T_BUGS<=t<T_FOLLOW-0.2: return "shock"
    return "norm"
def face(d,f,t):
    s=S; P=lambda x,y:(x*s,y*s); a=env[f]; mood=mood_at(t)
    blink=(f%95) in (0,1,2) and mood=="norm"
    for ex in (244,356):
        cx,cy=P(ex,199)
        if blink: d.rounded_rectangle((cx-22*s,cy-4*s,cx+22*s,cy+4*s),radius=4,fill=CY)
        elif mood=="happy": d.arc((cx-24*s,cy-14*s,cx+24*s,cy+30*s),200,340,fill=CY,width=int(10*s))
        elif mood=="shock": d.ellipse((cx-27*s,cy-31*s,cx+27*s,cy+31*s),fill=CY); d.ellipse((cx-9*s,cy-9*s,cx+9*s,cy+9*s),fill=(23,26,43))
        else: d.rounded_rectangle((cx-22*s,cy-29*s,cx+22*s,cy+29*s),radius=int(12*s),fill=CY)
    mx,my=P(300,262)
    if a>0.08:
        h=(8+38*a)*s; w=(56 if mood!="shock" else 40)*s
        d.rounded_rectangle((mx-w/2,my-h/2,mx+w/2,my+h/2),radius=int(min(h,w)/2),fill=CY)
    elif mood=="shock": d.ellipse((mx-12*s,my-12*s,mx+12*s,my+12*s),outline=CY,width=int(7*s))
    else: d.arc((mx-40*s,my-40*s,mx+40*s,my+12*s),25,155,fill=CY,width=int(9*s))
def col(c,t,t0,dur=.35):
    k=ease((t-t0)/dur); return tuple(int(BG[i]+(c[i]-BG[i])*k) for i in range(3)),k
def txt(d,xy,s,font,c,t,t0,anchor="la",dy=24):
    if t<t0: return
    cc,k=col(c,t,t0); d.text((xy[0],xy[1]+dy*(1-k)),s,font=font,fill=cc,anchor=anchor)
def typed(d,xy,s,font,c,t,t0,cps=22):
    if t<t0: return
    n=min(len(s),int((t-t0)*cps)); cur="▌" if n<len(s) or int(t*3)%2==0 else ""
    d.text(xy,s[:n]+cur,font=font,fill=c)
def label(t):
    return "// 00 — hello" if t<T_DES else "// 01 — the design" if t<T_MEET else "// 02 — meet bit" if t<T_WEEK else "// 03 — every week" if t<T_FOLLOW else "// 04 — follow"
def counter(t):
    return "" if t<T_DES else "DESIGNS 3" if t<T_MEET else "BIT v1.0" if t<T_WEEK else "WEEK 2/12"
for f in range(N):
    t=f/FPS
    im=Image.new("RGB",(1080,1920),BG); d=ImageDraw.Draw(im)
    for y in range(0,1920,60): d.line((0,y,1080,y),fill=(20,21,32))
    d.text((60,80),label(t),font=M34,fill=CY); d.text((1020,78),counter(t),font=MB38,fill=PK,anchor="ra")
    show_bit=t>=T_MEET
    if t<T_DES:
        typed(d,(60,380),"> systems engineer",M44,CY,t,0.1)
        typed(d,(60,450),"> learning AI in public",M44,CY,t,1.2)
        txt(d,(60,600),"but I didn't want to",B70,WH,t,T_FACE)
        txt(d,(60,690),"show my face.",B84,PK,t,T_FACE+0.8)
        if t>=T_FACE+0.8:
            k=ease((t-T_FACE-0.8)/0.4); cx,cy=540,1250
            d.ellipse((cx-110,cy-250,cx+110,cy-30),fill=(45,48,70)); d.pieslice((cx-220,cy-10,cx+220,cy+380),180,360,fill=(45,48,70))
            L=int(200*k); d.line((cx-L,cy-L-70,cx+L,cy+L-70),fill=RD,width=22); d.line((cx+L,cy-L-70,cx-L,cy+L-70),fill=RD,width=22)
    elif t<T_MEET:
        txt(d,(60,260),"So I designed",B70,WH,t,T_DES); txt(d,(60,350),"3 robots.",B84,CY,t,T_DES+0.3)
        for i,img in enumerate(designs):
            t0=T_DES+0.5+i*0.25
            if t<t0: continue
            k=ease((t-t0)/0.3); x=40+i*340; y=700+int(60*(1-k))
            dimmed = t>=T_WON and i!=1
            tile=img.copy()
            if dimmed:
                a=np.array(tile).astype(float); a[:,:,:3]*=0.35; tile=Image.fromarray(a.astype(np.uint8))
            if t>=T_WON and i==1:
                d.rounded_rectangle((x-10,y-10,x+310,y+360),radius=26,outline=CY,width=6)
            im.paste(tile,(x,y),tile)
            if dimmed:
                d.line((x+40,y+60,x+260,y+300),fill=RD,width=14); d.line((x+260,y+60,x+40,y+300),fill=RD,width=14)
        if t>=T_WON:
            cc,k=col(GR,t,T_WON); d.rounded_rectangle((420,1090,660,1150),radius=16,fill=cc); d.text((540,1120),"WINNER",font=B36,fill=BG,anchor="mm")
            txt(d,(60,480),"This one won.",B56,GR,t,T_WON)
    elif t<T_WEEK:
        g=(t-T_MEET)<0.35
        if g:
            d.text((54,226),"Meet Bit.",font=B96,fill=PK); d.text((66,234),"Meet Bit.",font=B96,fill=CY)
        d.text((60,230),"Meet Bit.",font=B96,fill=WH)
        rowsy=420
        items=[(T_FACESHOWS,"screen face","→ shows his mood",CY),(T_FACESHOWS+0.9,"</>","→ only speaks code",CY),(T_HAPPY,"passes","→ happy ^ ^",GR),(T_SHOCK,"breaks","→ shocked O O",RD)]
        for i,(t0,a,b,c) in enumerate(items):
            txt(d,(60,rowsy+i*95),a,B44,c,t,t0); txt(d,(420,rowsy+i*95+6),b,R34,WH,t,t0)
    elif t<T_FOLLOW:
        txt(d,(60,220),"Every week:",B70,WH,t,T_WEEK); txt(d,(60,310),"what I build with AI",B56,CY,t,T_WEEK+0.8)
        for i,(th,t0,lab,c) in enumerate(((thA,T_WEEK+1.0,"the wins",GR),(thB,T_WEEK+1.4,"and the bugs",RD))):
            if t<t0: continue
            k=ease((t-t0)/0.35); x=110+i*530; y=430+int(50*(1-k))
            hl = (i==0 and T_WINS<=t<T_BUGS) or (i==1 and t>=T_BUGS)
            d.rounded_rectangle((x-8,y-8,x+338,y+595),radius=22,outline=(c if hl else (50,54,78)),width=6 if hl else 3)
            im.paste(th,(x,y))
            if t>=(T_WINS if i==0 else T_BUGS): txt(d,(x+165,y+610),lab,B44,c,t,(T_WINS if i==0 else T_BUGS),anchor="ma")
    else:
        txt(d,(60,300),"Follow",B96,WH,t,T_FOLLOW)
        if t>=T_FOLLOW+0.2:
            k=ease((t-T_FOLLOW-0.2)/0.35); yy=430+int(24*(1-k))
            for i,ic in enumerate((YT,IG)):
                a=ic.copy(); a.putalpha(a.getchannel("A").point(lambda v:int(v*k)))
                im.paste(a,(60+i*104,yy),a)
            cc,_=col(PK,t,T_FOLLOW+0.2); d.text((280,yy+42),"@vibewithamitai",font=B56,fill=cc,anchor="lm")
            cc,_=col(GY,t,T_FOLLOW+0.3); d.text((60,yy+110),"YouTube  ·  Instagram",font=R34,fill=cc)
        txt(d,(60,640),"so Bit doesn't get lonely",B44,GY,t,T_FOLLOW+0.6)
    if show_bit:
        dt=t-T_MEET
        if dt<0.6: oy=int(-900*(1-ease(dt/0.6))); 
        else: oy=0
        bob=int(10*math.sin(t*2*math.pi*0.6)) if dt>0.6 else 0
        if T_FOLLOW<=t<T_FOLLOW+0.5: bob-=int(40*math.sin((t-T_FOLLOW)/0.5*math.pi))
        shake=int(8*math.sin(t*90)) if (T_SHOCK<=t<T_SHOCK+0.35 or T_BUGS<=t<T_BUGS+0.35) else 0
        r=base.copy(); face(ImageDraw.Draw(r),f,t)
        yb=1040 if t<T_WEEK or t>=T_FOLLOW else 1180
        im.paste(r,(330+shake,yb+oy+bob),r)
    im.save(f"frames/{f:04d}.png")
sfx=np.zeros(int(DUR*SR),np.float32)
def add(t0,sig):
    i=int(t0*SR); sfx[i:i+len(sig)]+=sig[:len(sfx)-i]
def tone(fr,d,dec=30,amp=.25,sq=False):
    tt=np.arange(int(d*SR))/SR; w=np.sin(2*np.pi*fr*tt)
    if sq: w=np.sign(w)*.5
    return (amp*w*np.exp(-dec*tt)).astype(np.float32)
for i in range(18): add(0.1+i/22,tone(2400,.02,120,.05))
for i in range(22): add(1.2+i/22,tone(2400,.02,120,.05))
for i in range(3): add(T_DES+0.5+i*0.25,tone(1400,.08,40,.14))
add(T_WON,tone(880,.3,8,.16)); add(T_WON+.12,tone(1320,.4,7,.16))
rng=np.random.default_rng(1); n=(rng.standard_normal(int(.35*SR))*np.exp(-np.arange(int(.35*SR))/SR*10)*.18).astype(np.float32); add(T_MEET,n)
add(T_MEET+0.55,tone(220,.25,10,.25))
for t0 in (T_FACESHOWS,T_FACESHOWS+0.9): add(t0,tone(1400,.08,40,.12))
add(T_HAPPY,tone(1320,.3,8,.14)); add(T_SHOCK,tone(150,.35,6,.2,True))
add(T_WINS,tone(1320,.3,8,.14)); add(T_BUGS,tone(150,.35,6,.2,True))
add(T_FOLLOW,tone(660,.3,6,.15)); add(T_FOLLOW+.12,tone(880,.3,6,.15)); add(T_FOLLOW+.24,tone(1320,.5,5,.15))
mix=sfx.copy(); mix[:len(voice)]+=voice; mix=np.clip(mix,-1,1)
with wave.open("audio.wav","wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
print("frames",N)
