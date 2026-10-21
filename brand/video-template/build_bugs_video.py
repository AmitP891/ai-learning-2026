"""Bit presenter video: "2 bugs the Claude API course did not warn me about" (21 Oct 2026).

Usage:  python3 build_bugs_video.py voiceover.mp3 ../bit/bit.svg
Then:   ffmpeg -framerate 30 -i frames/%04d.png -i audio.wav -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest out.mp4
"""
import os; os.makedirs("frames", exist_ok=True)
import re, math, subprocess, numpy as np, cairosvg, io, wave, sys, os
from PIL import Image, ImageDraw, ImageFont
A=sys.argv[1]; MASCOT=sys.argv[2]
FPS=30; SR=44100
raw=subprocess.run(["ffmpeg","-v","error","-i",A,"-f","s16le","-ac","1","-ar",str(SR),"-"],capture_output=True).stdout
voice=np.frombuffer(raw,np.int16).astype(np.float32)/32768
VD=len(voice)/SR; DUR=VD+1.3; N=int(DUR*FPS); hop=SR//FPS
rms=np.array([np.sqrt(np.mean(voice[i*hop:(i+1)*hop]**2)) if i*hop<len(voice) else 0 for i in range(N)])
env=np.clip((rms-0.01)/(np.percentile(rms[rms>0.01],90)-0.01),0,1); env=np.convolve(env,[.25,.5,.25],"same")
svg=open(MASCOT).read()
svg=re.sub(r'<g id="eyes">.*?</g>','',svg,flags=re.S); svg=re.sub(r'<path id="mouth"[^>]*/>','',svg)
S=1.35
base=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(),output_width=int(600*S),output_height=int(700*S)))).convert("RGBA")
CY=(0,240,255); PK=(255,43,214); GR=(57,255,136); RD=(255,70,90); WH=(255,255,255); GY=(170,175,190); BG=(13,13,20); PANEL=(24,26,40); YL=(255,214,0)
F=lambda n,s: ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{n}.ttf",s)
B84,B70,B56,B44,B36=F("DejaVuSans-Bold",84),F("DejaVuSans-Bold",70),F("DejaVuSans-Bold",56),F("DejaVuSans-Bold",44),F("DejaVuSans-Bold",36)
R34=F("DejaVuSans",34); M34,MB38,M30,M26,MB30=F("DejaVuSansMono",34),F("DejaVuSansMono-Bold",38),F("DejaVuSansMono",30),F("DejaVuSansMono",26),F("DejaVuSansMono-Bold",30)
# timeline, matched to pauses in the voiceover
T_HOOK2=1.6; T_BUG1=4.45; T_TEMP=5.37; T_ERR1=7.6; T_FIX1=11.25
T_BUG2=12.69; T_THINK=13.8; T_CODE2=16.15; T_ERR2=18.6; T_FIXW=21.25; T_FIX2=22.2; T_DONE=24.1; T_CTA=25.9
def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3
def mood_at(t):
    if t>=T_DONE or (T_FIX1<=t<T_FIX1+1.2) or (T_FIX2<=t<T_FIX2+1.5): return "happy"
    if (T_HOOK2<=t<3.3) or (T_ERR1<=t<T_FIX1) or (T_ERR2<=t<T_FIXW): return "shock"
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
def fadein(c,t,t0,dur=0.35):
    k=ease((t-t0)/dur); return tuple(int(BG[i]+(c[i]-BG[i])*k) for i in range(3)), k
def txt(d,xy,s,font,c,t,t0,anchor="la",dy=24):
    if t<t0: return
    col,k=fadein(c,t,t0); d.text((xy[0],xy[1]+dy*(1-k)),s,font=font,fill=col,anchor=anchor)
def code_card(d,y,lines,t,t0,state):
    # state: 'bug' red outline, 'fixed' green outline
    if t<t0: return
    col=RD if state=="bug" else GR
    h=40+len(lines)*48
    d.rounded_rectangle((60,y,1020,y+h),radius=20,fill=(18,20,32),outline=col,width=4)
    for i,(s,style) in enumerate(lines):
        ly=y+26+i*48
        if style=="hl":   d.rounded_rectangle((76,ly-6,1004,ly+40),radius=8,fill=(70,18,32))
        if style=="good": d.rounded_rectangle((76,ly-6,1004,ly+40),radius=8,fill=(14,58,36))
        c={"hl":RD,"good":GR,"dim":(110,115,135),"cut":(110,115,135)}.get(style,WH)
        d.text((96,ly),s,font=M30,fill=c)
        if style=="cut":
            w=d.textlength(s,font=M30); d.line((96,ly+19,96+w,ly+19),fill=RD,width=4)
    return y+h
def label(t):
    return "// 01 — the hook" if t<T_BUG1 else "// 02 — bug one" if t<T_BUG2 else "// 03 — bug two" if t<T_DONE else "// 04 — fixed"
def counter(t):
    return f"BUGS FIXED {(t>=T_FIX1)+(t>=T_FIX2+0.4)}/2"
def badge(d,x,y,s,c):
    w=d.textlength(s,font=B36)+40; d.rounded_rectangle((x,y,x+w,y+52),radius=14,fill=c); d.text((x+20,y+26),s,font=B36,fill=BG,anchor="lm")
for f in range(N):
    t=f/FPS
    im=Image.new("RGB",(1080,1920),BG); d=ImageDraw.Draw(im)
    for y in range(0,1920,60): d.line((0,y,1080,y),fill=(20,21,32))
    d.text((60,80),label(t),font=M34,fill=CY)
    d.text((1020,78),counter(t),font=MB38,fill=(GR if t>=T_FIX2+0.4 else PK),anchor="ra")
    if t<T_BUG1:
        txt(d,(60,360),"My first",B70,WH,t,0.05); txt(d,(60,450),"Claude API script",B70,CY,t,0.5)
        txt(d,(60,560),"broke twice.",B84,RD,t,T_HOOK2)
        txt(d,(60,700),"Here's why →",B56,GY,t,3.3)
    elif t<T_BUG2:
        fixed=t>=T_FIX1
        txt(d,(60,200),"Bug 1: temperature",B70,WH,t,T_BUG1)
        if t>=T_TEMP:
            lines=[("client.messages.create(","n"),('    model="claude-sonnet-5-5",',"n"),
                   ("    temperature=0.7," if not fixed else "    temperature=0.7,", "cut" if fixed else "hl"),
                   ("    messages=messages)","n")]
            yb=code_card(d,330,lines,t,T_TEMP,"fixed" if fixed else "bug")
            if t>=T_ERR1 and not fixed:
                txt(d,(60,yb+30),"TypeError: unexpected keyword",M26,RD,t,T_ERR1,dy=10)
                txt(d,(60,yb+66),"argument 'temperature'",M26,RD,t,T_ERR1,dy=10)
                txt(d,(60,yb+130),"New models reject custom temperature",R34,GY,t,T_ERR1+0.6,dy=10)
            if fixed:
                badge(d,60,yb+30,"FIXED ✓  delete the line",GR)
    elif t<T_DONE:
        fixed=t>=T_FIX2
        txt(d,(60,200),"Bug 2: thinking blocks",B70,WH,t,T_BUG2)
        if t>=T_THINK:
            col,k=fadein(WH,t,T_THINK)
            d.text((60,320),"response.content =",font=M30,fill=col)
            d.rounded_rectangle((420,308,640,360),radius=14,fill=(60,30,80) if not fixed else (40,40,60)); d.text((530,334),"thinking",font=MB30,fill=PK,anchor="mm")
            d.rounded_rectangle((660,308,820,360),radius=14,fill=(14,58,36)); d.text((740,334),"text",font=MB30,fill=GR,anchor="mm")
            d.text((530,372),"[0]",font=M26,fill=PK,anchor="ma"); d.text((740,372),"[1]",font=M26,fill=GR,anchor="ma")
        if T_CODE2<=t<T_FIX2:
            yb=code_card(d,440,[("reply = response.content[0].text","hl")],t,T_CODE2,"bug")
            if t>=T_ERR2:
                txt(d,(60,yb+30),"AttributeError: 'ThinkingBlock'",M26,RD,t,T_ERR2,dy=10)
                txt(d,(60,yb+66),"object has no attribute 'text'",M26,RD,t,T_ERR2,dy=10)
            if t>=T_FIXW: txt(d,(60,yb+150),"The fix:",B56,GR,t,T_FIXW)
        if fixed:
            yb=code_card(d,440,[("# read blocks by type","dim"),('reply = "".join(b.text for b in','good'),("    response.content","good"),('    if b.type == "text")',"good")],t,T_FIX2,"fixed")
            if t>=T_FIX2+0.4: badge(d,60,yb+30,"FIXED ✓",GR)
    else:
        txt(d,(60,330),"2/2",B84,GR,t,T_DONE+0.05); txt(d,(250,330),"BUGS FIXED",B84,WH,t,T_DONE+0.25)
        txt(d,(60,470),"Both fixes are in my repo",B56,CY,t,T_DONE+0.4)
        txt(d,(60,620),"Code in bio",B56,WH,t,T_CTA); txt(d,(60,700),"@vibewithamitai",B44,PK,t,T_CTA+0.2)
    bob=int(10*math.sin(t*2*math.pi*0.6))
    if T_DONE<=t<T_DONE+0.5: bob-=int(40*math.sin((t-T_DONE)/0.5*math.pi))
    shake=int(8*math.sin(t*90)) if (T_HOOK2<=t<T_HOOK2+0.35 or T_ERR1<=t<T_ERR1+0.35 or T_ERR2<=t<T_ERR2+0.35) else 0
    r=base.copy(); face(ImageDraw.Draw(r),f,t)
    im.paste(r,(330+shake,1040+bob),r)
    im.save(f"frames/{f:04d}.png")
sfx=np.zeros(int(DUR*SR),np.float32)
def add(t0,sig):
    i=int(t0*SR); sfx[i:i+len(sig)]+=sig[:len(sfx)-i]
def tone(fr,d,dec=30,amp=.25,sq=False):
    tt=np.arange(int(d*SR))/SR; w=np.sin(2*np.pi*fr*tt)
    if sq: w=np.sign(w)*.5
    return (amp*w*np.exp(-dec*tt)).astype(np.float32)
for tb in (T_HOOK2,T_ERR1,T_ERR2): add(tb,tone(150,.35,6,.22,True))
for tf in (T_FIX1,T_FIX2): add(tf,tone(880,.3,8,.18)); add(tf+0.12,tone(1320,.4,7,.18))
for tk in (T_BUG1,T_TEMP,T_BUG2,T_THINK,T_CODE2): add(tk,tone(1400,.08,40,.15))
add(T_DONE,tone(660,.3,6,.16)); add(T_DONE+.12,tone(880,.3,6,.16)); add(T_DONE+.24,tone(1320,.5,5,.16))
mix=sfx.copy(); mix[:len(voice)]+=voice; mix=np.clip(mix,-1,1)
with wave.open("audio.wav","wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
print("frames",N)
