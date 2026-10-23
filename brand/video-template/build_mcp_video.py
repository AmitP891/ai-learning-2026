"""Bit presenter video: requirements checker as an MCP server (23 Oct 2026).

Usage:  python3 build_mcp_video.py voiceover.mp3 ../bit
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
def tt_icon(size):
    ic=Image.new("RGBA",(size,size),(0,0,0,0)); d=ImageDraw.Draw(ic)
    d.rounded_rectangle((0,0,size-1,size-1),radius=int(size*0.22),fill=(10,10,10,255),outline=(90,90,100,255),width=3)
    f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",int(size*0.62))
    c=size//2
    d.text((c-3,c+2),"♪",font=f,fill=(37,244,238,255),anchor="mm"); d.text((c+3,c-2),"♪",font=f,fill=(254,44,85,255),anchor="mm"); d.text((c,c),"♪",font=f,fill=(255,255,255,255),anchor="mm")
    return ic
TT=tt_icon(84)
T_MCP=4.5; T_CC=7.2; T_ANY=8.93; T_ASK=10.53; T_NINE=12.99; T_TWIST=15.49; T_BUGS=18.01; T_FIX=21.38; T_CTA=24.40
def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3
def mood_at(t):
    if T_TWIST<=t<T_FIX-0.2: return "shock"
    if T_NINE<=t<T_NINE+1.5 or t>=T_FIX: return "happy"
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
M34b=F("DejaVuSansMono",34); MB36=F("DejaVuSansMono-Bold",36); R38=F("DejaVuSans",38); B40=F("DejaVuSans-Bold",40)
def term(d,y,lines,t,t0,outline=(60,64,90)):
    # lines: (text, colour, appear_time)
    if t<t0: return y
    shown=[l for l in lines if t>=l[2]]
    h=50+len(lines)*58
    d.rounded_rectangle((60,y,1020,y+h),radius=18,fill=(18,20,30),outline=outline,width=3)
    for i,(s,c,ts) in enumerate(lines):
        if t>=ts:
            cc,_=col(c,t,ts,0.2); d.text((90,y+28+i*58),s,font=M34b,fill=cc)
    return y+h
def box(d,x,y,w,h,label,sub,c,t,t0):
    if t<t0: return
    cc,k=col(c,t,t0); y=y+int(20*(1-k))
    d.rounded_rectangle((x,y,x+w,y+h),radius=20,fill=(24,26,40),outline=cc,width=4)
    d.text((x+w/2,y+h/2-16),label,font=B40,fill=cc,anchor="mm")
    if sub: d.text((x+w/2,y+h/2+26),sub,font=F("DejaVuSans",28),fill=GY,anchor="mm")
def arrow(d,x1,y1,x2,y2,c):
    d.line((x1,y1,x2,y2),fill=c,width=6)
    import math as m
    a=m.atan2(y2-y1,x2-x1); L=22
    d.polygon([(x2,y2),(x2-L*m.cos(a-0.45),y2-L*m.sin(a-0.45)),(x2-L*m.cos(a+0.45),y2-L*m.sin(a+0.45))],fill=c)
def label(t):
    for lim,l in ((T_MCP,"// 01 — last week"),(T_ASK,"// 02 — the upgrade"),(T_TWIST,"// 03 — the test"),(T_FIX,"// 04 — the twist")):
        if t<lim: return l
    return "// 05 — the fix"
def counter(t):
    if t<T_NINE: return "WEEK 3 · MCP"
    if t<T_TWIST: return "TOOL CALLS 9"
    if t<T_FIX: return "BUGS FOUND 2"
    return "BUGS FIXED ✓"
for f in range(N):
    t=f/FPS
    im=Image.new("RGB",(1080,1920),BG); d=ImageDraw.Draw(im)
    for y in range(0,1920,60): d.line((0,y,1080,y),fill=(20,21,32))
    d.text((60,80),label(t),font=M34,fill=CY)
    d.text((1020,78),counter(t),font=MB38,fill=(RD if T_TWIST<=t<T_FIX else GR if t>=T_FIX else PK),anchor="ra")
    if t<T_MCP:
        txt(d,(60,230),"Last week, my checker",B56,WH,t,0.05)
        txt(d,(60,305),"only worked in",B56,WH,t,0.6)
        txt(d,(60,380),"my own script.",B56,RD,t,1.2)
        box(d,240,540,600,170,"requirements_checker.py","python3 only · nowhere else",GY,t,1.6)
    elif t<T_ASK:
        txt(d,(60,210),"So I turned it into an",B56,WH,t,T_MCP); txt(d,(60,285),"MCP server.",B70,CY,t,T_MCP+0.3)
        box(d,60,430,440,160,"my tools","list · check",GY,t,T_MCP+0.2)
        box(d,580,430,440,160,"MCP server","requirements-checker",CY,t,T_MCP+0.6)
        if t>=T_MCP+0.6: arrow(d,505,510,575,510,CY)
        if t>=T_CC:
            box(d,320,660,440,140,"Claude Code","",PK,t,T_CC)
            if t>=T_CC+0.2: arrow(d,800,595,600,655,PK)
        if t>=T_ANY:
            y=term(d,860,[("$ claude mcp list",GY,T_ANY),("vidIQ                ✓ Connected",GY,T_ANY+0.1),("Google Drive         ✓ Connected",GY,T_ANY+0.2),("requirements-checker ✓ Connected",GR,T_ANY+0.35)],t,T_ANY)
    elif t<T_TWIST:
        txt(d,(60,210),"I asked it to review",B56,WH,t,T_ASK); txt(d,(60,285),"8 requirements.",B70,CY,t,T_ASK+0.3)
        term(d,430,[("> Use requirements-checker to",WH,T_ASK+0.4),("  review the sample requirements.",WH,T_ASK+0.4),("● Calling requirements-checker",PK,T_NINE),("  9 times…",PK,T_NINE)],t,T_ASK+0.4)
        if t>=T_NINE+0.3:
            cc,k=col(GR,t,T_NINE+0.3); d.text((540,820),"9 calls to MY server",font=F("DejaVuSans-Bold",72),fill=cc,anchor="mm")
    elif t<T_FIX:
        txt(d,(60,210),"Then it did something",B56,WH,t,T_TWIST); txt(d,(60,285),"I didn't expect.",B70,PK,t,T_TWIST+0.4)
        if t>=T_BUGS:
            term(d,430,[("Two things the checker",WH,T_BUGS),("gets wrong on REQ-004:",WH,T_BUGS),("✗ 'daily' is a frequency,",RD,T_BUGS+0.8),("  so it IS measurable",RD,T_BUGS+0.8),("✗ 'encrypt' needs a",RD,T_BUGS+1.6),("  standard, e.g. AES-256",RD,T_BUGS+1.6)],t,T_BUGS,outline=RD)
    else:
        txt(d,(60,210),"So I let Claude fix",B56,WH,t,T_FIX); txt(d,(60,285),"the tool it just used.",B56,GR,t,T_FIX+0.4)
        term(d,410,[("● Frequency words now count",WH,T_FIX+0.5),("  as measurable.",WH,T_FIX+0.5),("Pushed to main · 6042ef7",GR,T_FIX+0.9)],t,T_FIX+0.5,outline=GR)
        if t>=T_CTA:
            k=ease((t-T_CTA)/0.35)
            for i,ic in enumerate((TT,YT,IG)):
                a=ic.copy(); a.putalpha(a.getchannel("A").point(lambda v:int(v*k))); im.paste(a,(60+i*100,720),a)
            cc,_=col(PK,t,T_CTA); d.text((370,762),"@vibewithamitai",font=B56,fill=cc,anchor="lm")
            cc,_=col(GY,t,T_CTA+0.2); d.text((60,840),"Code in bio",font=R34,fill=cc)
    bob=int(10*math.sin(t*2*math.pi*0.6))
    for jt in (T_NINE,T_FIX):
        if jt<=t<jt+0.5: bob-=int(30*math.sin((t-jt)/0.5*math.pi))
    shake=int(8*math.sin(t*90)) if T_TWIST<=t<T_TWIST+0.35 else 0
    r=base.copy(); face(ImageDraw.Draw(r),f,t)
    im.paste(r,(330+shake,1150+bob),r)
    im.save(f"frames/{f:04d}.png")
sfx=np.zeros(int(DUR*SR),np.float32)
def add(t0,sig):
    i=int(t0*SR); sfx[i:i+len(sig)]+=sig[:len(sfx)-i]
def tone(fr,d,dec=30,amp=.25,sq=False):
    tt=np.arange(int(d*SR))/SR; w=np.sin(2*np.pi*fr*tt)
    if sq: w=np.sign(w)*.5
    return (amp*w*np.exp(-dec*tt)).astype(np.float32)
for x in (T_MCP+0.6,T_CC,T_ANY+0.35): add(x,tone(1400,.08,40,.14))
for i in range(9): add(T_NINE+i*0.07,tone(1600,.04,60,.08))
add(T_TWIST,tone(150,.35,6,.2,True)); add(T_BUGS+0.8,tone(220,.2,10,.12,True)); add(T_BUGS+1.6,tone(220,.2,10,.12,True))
add(T_FIX+0.9,tone(880,.3,8,.16)); add(T_FIX+1.0,tone(1320,.4,7,.16))
add(T_CTA,tone(660,.3,6,.15)); add(T_CTA+.12,tone(880,.3,6,.15)); add(T_CTA+.24,tone(1320,.5,5,.15))
mix=sfx.copy(); mix[:len(voice)]+=voice; mix=np.clip(mix,-1,1)
with wave.open("audio.wav","wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
print("frames",N)
