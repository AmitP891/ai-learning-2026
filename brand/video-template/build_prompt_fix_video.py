"""Bit presenter video: prompt v1 vs v2, "I fixed my prompt and proved it" (21 Oct 2026).

Usage:  python3 build_prompt_fix_video.py voiceover.mp3 ../bit
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
def thumb(p):
    im=Image.open(p).convert("RGB").resize((330,587),Image.LANCZOS); return im

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

YL=(255,214,0)
T_HOW=4.06; T_FIX=5.52; TECH=[8.39,9.64,11.09,12.1]; T_Q=13.70; T_G=15.22; T_RUNS=16.48
T_BEFORE=17.66; T_B56=18.46; T_AFTER=20.01; T_A66=20.76; T_BOTH=22.11; T_SHORT=23.0; T_QUAL=26.17; T_CTA=28.89
def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3
def mood_at(t):
    if 1.2<=t<3.7: return "shock"
    if t>=T_A66 or (any(tt<=t<tt+0.6 for tt in TECH)): return "happy"
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
def label(t):
    for lim,l in ((T_FIX,"// 01 — last week"),(T_Q,"// 02 — the fix"),(T_BEFORE,"// 03 — the test"),(T_SHORT,"// 04 — before vs after"),(T_CTA,"// 05 — the bonus")):
        if t<lim: return l
    return "// 06 — the code"
def counter(t):
    if t<T_FIX: return "PASSED 5/6"
    if t<T_Q: return f"TECHNIQUES {sum(t>=x for x in TECH)}/4"
    if t<T_A66: return "PASSED 5/6"
    return "PASSED 6/6"
M30=F("DejaVuSansMono",30); R30=F("DejaVuSans",30)
for f in range(N):
    t=f/FPS
    im=Image.new("RGB",(1080,1920),BG); d=ImageDraw.Draw(im)
    for y in range(0,1920,60): d.line((0,y,1080,y),fill=(20,21,32))
    d.text((60,80),label(t),font=M34,fill=CY); d.text((1020,78),counter(t),font=MB38,fill=(GR if t>=T_A66 else PK),anchor="ra")
    if t<T_FIX:
        txt(d,(60,260),"Last week,",B70,WH,t,0.05); txt(d,(60,350),"my AI failed",B84,RD,t,0.6)
        txt(d,(60,460),"for writing too much.",B56,WH,t,1.4)
        if t>=1.2:
            cc,k=col(RD,t,1.2); y=600+int(30*(1-k))
            d.rounded_rectangle((60,y,1020,y+84),radius=18,fill=(24,26,40),outline=cc,width=4)
            d.text((88,y+42),"4",font=B36,fill=CY,anchor="lm"); d.text((140,y+42),"Why never commit an API key?",font=R30,fill=WH,anchor="lm")
            d.text((760,y+42),"125w",font=B36,fill=RD,anchor="rm")
            d.rounded_rectangle((790,y+20,930,y+64),radius=12,fill=RD); d.text((860,y+42),"FAIL",font=B36,fill=BG,anchor="mm")
        txt(d,(60,770),"Here's how I fixed it →",B44,GY,t,T_HOW)
    elif t<T_Q:
        txt(d,(60,210),"4 prompt engineering",B56,WH,t,T_FIX); txt(d,(60,285),"techniques",B70,CY,t,T_FIX+0.3)
        items=[("Clear audience","\"for complete beginners\""),("Hard word limit","\"80 words or fewer\""),("XML tags","<rules> … </rules>"),("One example","show the answer shape")]
        for i,(a,b) in enumerate(items):
            t0=TECH[i]
            if t<t0: continue
            cc,k=col(GR,t,t0); y=430+i*130+int(24*(1-k))
            d.rounded_rectangle((60,y,1020,y+110),radius=20,fill=(24,26,40),outline=(40,44,66),width=2)
            d.ellipse((84,y+30,134,y+80),fill=cc); d.text((109,y+55),"✓",font=B36,fill=BG,anchor="mm")
            d.text((160,y+10),a,font=B44,fill=WH); d.text((160,y+84),b,font=M30 if i==2 else R30,fill=GY,anchor="lm")
    elif t<T_BEFORE:
        txt(d,(60,300),"Same 6 questions.",B70,WH,t,T_Q)
        txt(d,(60,400),"Same graders.",B70,WH,t,T_G)
        txt(d,(60,500),"2 runs.",B84,CY,t,T_RUNS)
    elif t<T_SHORT:
        for side,(hdr,t0,score,tsc,dots,c) in enumerate((("BEFORE  v1",T_BEFORE,"5/6",T_B56,[1,1,1,0,1,1],YL),("AFTER  v2",T_AFTER,"6/6",T_A66,[1]*6,GR))):
            x=60+side*500
            if t>=t0:
                cc,_=col(GY,t,t0); d.rounded_rectangle((x,250,x+460,820),radius=26,fill=(24,26,40),outline=(c if t>=tsc else (40,44,66)),width=4)
                d.text((x+230,300),hdr,font=B44,fill=cc,anchor="mm")
            if t>=tsc:
                cc,k=col(c,t,tsc); d.text((x+230,460),score,font=F("DejaVuSans-Bold",150),fill=cc,anchor="mm")
                for j,ok in enumerate(dots):
                    if t>=tsc+0.1*j:
                        cx=x+80+j*60; d.ellipse((cx-22,620,cx+22,664),fill=(GR if ok else RD))
        if t>=T_BOTH:
            cc,_=col(GR,t,T_BOTH); d.rounded_rectangle((560,860,1020,930),radius=18,fill=cc); d.text((790,895),"both runs ✓✓",font=B44,fill=BG,anchor="mm")
    elif t<T_CTA:
        txt(d,(60,230),"Answers got shorter",B56,WH,t,T_SHORT)
        k=ease((t-T_SHORT-0.3)/1.2); full=900
        d.text((60,360),"v1",font=B44,fill=GY); d.rounded_rectangle((150,360,150+full,420),radius=14,fill=(90,95,120)); d.text((150+full-20,390),"99 words",font=B36,fill=WH,anchor="rm")
        w2=int(full*(1-(1-60/99)*k)); n2=round(99-(39*k))
        d.text((60,460),"v2",font=B44,fill=CY); d.rounded_rectangle((150,460,150+w2,520),radius=14,fill=CY); d.text((150+w2-20,490),f"{n2} words",font=B36,fill=BG,anchor="rm")
        if t>=T_SHORT+1.5: txt(d,(60,580),"−39% words",F("DejaVuSans-Bold",110),CY,t,T_SHORT+1.5)
        if t>=T_QUAL:
            txt(d,(60,760),"Quality:  8.7 → 8.8  ↑",B56,GR,t,T_QUAL)
    else:
        txt(d,(60,300),"Code in bio",B96,WH,t,T_CTA)
        if t>=T_CTA+0.2:
            k=ease((t-T_CTA-0.2)/0.35); yy=430+int(24*(1-k))
            for i,ic in enumerate((YT,IG)):
                a=ic.copy(); a.putalpha(a.getchannel("A").point(lambda v:int(v*k))); im.paste(a,(60+i*104,yy),a)
            cc,_=col(PK,t,T_CTA+0.2); d.text((280,yy+42),"@vibewithamitai",font=B56,fill=cc,anchor="lm")
        txt(d,(60,600),"prompt_compare.py · v1 vs v2",M34,GY,t,T_CTA+0.5)
    bob=int(10*math.sin(t*2*math.pi*0.6))
    if T_A66<=t<T_A66+0.5: bob-=int(40*math.sin((t-T_A66)/0.5*math.pi))
    if T_CTA<=t<T_CTA+0.5: bob-=int(30*math.sin((t-T_CTA)/0.5*math.pi))
    shake=int(8*math.sin(t*90)) if 1.2<=t<1.55 else 0
    r=base.copy(); face(ImageDraw.Draw(r),f,t)
    yb=1040 if not (T_FIX<=t<T_Q) else 1100
    im.paste(r,(330+shake,yb+bob),r)
    im.save(f"frames/{f:04d}.png")
sfx=np.zeros(int(DUR*SR),np.float32)
def add(t0,sig):
    i=int(t0*SR); sfx[i:i+len(sig)]+=sig[:len(sfx)-i]
def tone(fr,d,dec=30,amp=.25,sq=False):
    tt=np.arange(int(d*SR))/SR; w=np.sin(2*np.pi*fr*tt)
    if sq: w=np.sign(w)*.5
    return (amp*w*np.exp(-dec*tt)).astype(np.float32)
add(1.2,tone(150,.35,6,.2,True))
for x in TECH: add(x,tone(1400,.08,40,.15))
for x in (T_Q,T_G,T_RUNS): add(x,tone(1000,.06,40,.1))
add(T_B56,tone(520,.25,8,.14))
add(T_A66,tone(880,.3,8,.17)); add(T_A66+.12,tone(1320,.4,7,.17))
add(T_QUAL,tone(1320,.3,8,.14))
add(T_CTA,tone(660,.3,6,.15)); add(T_CTA+.12,tone(880,.3,6,.15)); add(T_CTA+.24,tone(1320,.5,5,.15))
mix=sfx.copy(); mix[:len(voice)]+=voice; mix=np.clip(mix,-1,1)
with wave.open("audio.wav","wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
print("frames",N)
