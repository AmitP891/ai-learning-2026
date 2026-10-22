"""Bit presenter video: requirements checker with Claude tool use (22 Oct 2026).

Usage:  python3 build_requirements_video.py voiceover.mp3 ../bit
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
T_CALLS=5.10; T_FLAG=7.6; A_B=8.92; A_Q=10.94; A_A=12.27; B_B=14.50; B_A=16.4; C_B=18.86; C_A=20.3
T_ASSUME=22.16; T_HUMAN=25.52; T_TAKE=27.13; T_TIRED=30.08; T_CTA=31.0
def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3
def mood_at(t):
    if T_FLAG<=t<T_FLAG+1.2 or A_B<=t<A_A-0.2 or B_B<=t<B_A-0.2 or C_B<=t<C_A-0.2: return "shock"
    if A_A<=t<A_A+1.4 or B_A<=t<B_A+1.4 or C_A<=t<C_A+1.4 or t>=T_HUMAN: return "happy"
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
def wrap(d,s,font,maxw):
    words=s.split(); lines=[]; cur=""
    for w in words:
        tryl=(cur+" "+w).strip()
        if d.textlength(tryl,font=font)<=maxw: cur=tryl
        else: lines.append(cur); cur=w
    lines.append(cur); return lines
R38=F("DejaVuSans",38); M30=F("DejaVuSansMono",30); MB32=F("DejaVuSansMono-Bold",32); B40=F("DejaVuSans-Bold",40)
def card(d,y,tag,text,c,t,t0,assume_hl=False):
    if t<t0: return y
    cc,k=col(c,t,t0); y=y+int(20*(1-k))
    lines=wrap(d,text,R38,880); h=80+len(lines)*50
    d.rounded_rectangle((60,y,1020,y+h),radius=20,fill=(24,26,40),outline=cc,width=4)
    d.text((90,y+20),tag,font=B36,fill=cc)
    for i,l in enumerate(lines):
        x=90; ly=y+66+i*50
        for part in re.split(r"(\[assumed\])",l):
            if not part: continue
            pc=YL if (part=="[assumed]") else WH
            if part=="[assumed]" and assume_hl: 
                w=d.textlength(part,font=R38); d.rounded_rectangle((x-4,ly-2,x+w+4,ly+46),radius=8,fill=(70,58,0))
            d.text((x,ly),part,font=R38,fill=pc); x+=d.textlength(part,font=R38)
    return y+h+24
def label(t):
    for lim,l in ((T_CALLS,"// 01 — the setup"),(A_B,"// 02 — the review"),(T_ASSUME,"// 03 — the rewrites"),(T_TAKE,"// 04 — the guardrail")):
        if t<lim: return l
    return "// 05 — the takeaway"
CALLS=[("list_requirements()","")]+[(f"check_requirement(REQ-00{i})","PASS" if i in (1,6) else "REVIEW") for i in range(1,9)]
def counter(t):
    if t<T_CALLS: return "REQS 8"
    if t<A_B:
        n=min(9,int((t-T_CALLS)/0.26)+1); return f"TOOL CALLS {n}/9"
    return "FLAGGED 6/8"
for f in range(N):
    t=f/FPS
    im=Image.new("RGB",(1080,1920),BG); d=ImageDraw.Draw(im)
    for y in range(0,1920,60): d.line((0,y,1080,y),fill=(20,21,32))
    d.text((60,80),label(t),font=M34,fill=CY); d.text((1020,78),counter(t),font=MB38,fill=(RD if t>=T_FLAG and t<T_TAKE else PK),anchor="ra")
    if t<T_CALLS:
        txt(d,(60,220),"2 Python tools",B70,CY,t,0.05)
        txt(d,(60,310),"8 requirements",B70,WH,t,0.9)
        txt(d,(60,400),"flight data logger (synthetic)",R34,GY,t,2.6)
        for i,s in enumerate(("list_requirements()","check_requirement(id)")):
            if t>=0.5+i*0.3:
                cc,k=col(CY,t,0.5+i*0.3); y=500+i*90
                d.rounded_rectangle((60,y,60+d.textlength(s,font=MB32)+50,y+70),radius=16,fill=(10,40,48),outline=cc,width=3); d.text((85,y+35),s,font=MB32,fill=cc,anchor="lm")
    elif t<A_B:
        d.text((60,200),"Claude calls my tools:",font=B56,fill=WH)
        for i,(s,v) in enumerate(CALLS):
            t0=T_CALLS+i*0.26
            if t<t0: continue
            y=300+i*62; cc,_=col(GY,t,t0,0.15)
            d.text((60,y),"[tool] "+s,font=M30,fill=cc)
            if v:
                bc=GR if v=="PASS" else RD; w=d.textlength(v,font=MB32)+30
                d.rounded_rectangle((760,y-4,760+w,y+42),radius=10,fill=bc); d.text((775,y+19),v,font=MB32,fill=BG,anchor="lm")
        if t>=T_FLAG:
            cc,k=col(RD,t,T_FLAG); d.rounded_rectangle((60,880,1020,960),radius=18,fill=(40,12,22),outline=cc,width=4)
            d.text((540,920),"6 of 8 flagged",font=B56,fill=cc,anchor="mm")
    elif t<T_ASSUME:
        if t<B_B:
            y=card(d,220,"BEFORE · REQ-002","The system shall be fast.",RD,t,A_B)
            if t>=A_Q: txt(d,(60,y+10),"Fast how?",B70,PK,t,A_Q); y+=110
            card(d,y+10,"AFTER","The system shall respond to any user input within 200 ms [assumed].",GR,t,A_A)
        elif t<C_B:
            y=card(d,220,"BEFORE · REQ-003","The display should be user-friendly.",RD,t,B_B)
            card(d,y+10,"AFTER","A first-time user shall complete 5 [assumed] core tasks within 3 minutes [assumed].",GR,t,B_A)
        else:
            y=card(d,220,"BEFORE · REQ-004","…shall store 72 hours of data AND shall encrypt it AND shall upload it daily.",RD,t,C_B)
            if t>=C_A:
                cc,k=col(GR,t,C_A); y0=y+10+int(20*(1-k))
                d.rounded_rectangle((60,y0,1020,y0+80+3*56),radius=20,fill=(24,26,40),outline=cc,width=4)
                d.text((90,y0+20),"AFTER · split into 3",font=B36,fill=cc)
                for i,line in enumerate(("004a: store at least 72 hours of data","004b: encrypt with AES-256 [assumed]","004c: upload every 24 hours [assumed]")):
                    if t<C_A+i*0.3: continue
                    x=90; ly=y0+70+i*56
                    for part in re.split(r"(\[assumed\])",line):
                        if not part: continue
                        d.text((x,ly),part,font=R38,fill=(YL if part=="[assumed]" else WH)); x+=d.textlength(part,font=R38)
    elif t<T_TAKE:
        txt(d,(60,210),"Every number it invented…",B56,WH,t,T_ASSUME)
        rows=["200 ms [assumed]","5 core tasks [assumed]","AES-256 [assumed]","12 hours at 25 °C [assumed]","1 Mbit/s [assumed]"]
        for i,s in enumerate(rows):
            t0=T_ASSUME+0.8+i*0.4
            if t<t0: continue
            cc,_=col(WH,t,t0,0.2); y=330+i*80; x=90
            a,b=s.split(" [assumed]")
            d.text((x,y),a,font=R38,fill=cc); x+=d.textlength(a+" ",font=R38)
            w=d.textlength("[assumed]",font=R38); d.rounded_rectangle((x-4,y-2,x+w+4,y+46),radius=8,fill=(70,58,0)); d.text((x,y),"[assumed]",font=R38,fill=YL)
        if t>=T_HUMAN: txt(d,(60,760),"…flagged for a human ✓",B56,GR,t,T_HUMAN)
    else:
        txt(d,(60,260),"AI won't replace",B70,WH,t,T_TAKE); txt(d,(60,350),"the systems engineer.",B70,WH,t,T_TAKE+0.5)
        txt(d,(60,500),"It's a reviewer that",B56,CY,t,T_TIRED); txt(d,(60,575),"never gets tired.",B56,CY,t,T_TIRED+0.4)
        if t>=T_CTA:
            k=ease((t-T_CTA)/0.35)
            for i,ic in enumerate((YT,IG)):
                a=ic.copy(); a.putalpha(a.getchannel("A").point(lambda v:int(v*k))); im.paste(a,(60+i*104,720),a)
            cc,_=col(PK,t,T_CTA); d.text((280,762),"@vibewithamitai",font=B56,fill=cc,anchor="lm")
            cc,_=col(GY,t,T_CTA+0.2); d.text((60,840),"Code in bio",font=R34,fill=cc)
    bob=int(10*math.sin(t*2*math.pi*0.6))
    for jt in (A_A,B_A,C_A,T_HUMAN):
        if jt<=t<jt+0.5: bob-=int(30*math.sin((t-jt)/0.5*math.pi))
    shake=int(8*math.sin(t*90)) if T_FLAG<=t<T_FLAG+0.35 else 0
    r=base.copy(); face(ImageDraw.Draw(r),f,t)
    im.paste(r,(330+shake,1100+bob),r)
    im.save(f"frames/{f:04d}.png")
sfx=np.zeros(int(DUR*SR),np.float32)
def add(t0,sig):
    i=int(t0*SR); sfx[i:i+len(sig)]+=sig[:len(sfx)-i]
def tone(fr,d,dec=30,amp=.25,sq=False):
    tt=np.arange(int(d*SR))/SR; w=np.sin(2*np.pi*fr*tt)
    if sq: w=np.sign(w)*.5
    return (amp*w*np.exp(-dec*tt)).astype(np.float32)
for i in range(9): add(T_CALLS+i*0.26,tone(1600,.05,50,.1))
add(T_FLAG,tone(150,.35,6,.2,True))
for b in (A_B,B_B,C_B): add(b,tone(220,.2,10,.12,True))
for a in (A_A,B_A,C_A): add(a,tone(880,.25,8,.15)); add(a+.1,tone(1320,.35,7,.15))
for i in range(5): add(T_ASSUME+0.8+i*0.4,tone(1200,.06,40,.1))
add(T_HUMAN,tone(1320,.3,8,.14))
add(T_CTA,tone(660,.3,6,.15)); add(T_CTA+.12,tone(880,.3,6,.15)); add(T_CTA+.24,tone(1320,.5,5,.15))
mix=sfx.copy(); mix[:len(voice)]+=voice; mix=np.clip(mix,-1,1)
with wave.open("audio.wav","wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
print("frames",N)
