"""Bit presenter video template, first used for the prompt-eval video (21 Oct 2026).

Usage:  python3 build_eval_video.py voiceover.mp3
Then:   ffmpeg -framerate 30 -i frames/%04d.png -i audio.wav -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest out.mp4

To make a new video: copy this file, change the scene text, the rows and the timeline
constants (T_*), which are set to where the pauses fall in the voiceover.
"""
import re, math, subprocess, numpy as np, cairosvg, io, wave
from PIL import Image, ImageDraw, ImageFont
import sys, os
A=sys.argv[1]  # path to the voiceover (mp3/wav)
HERE=os.path.dirname(os.path.abspath(__file__))
os.makedirs("frames",exist_ok=True)
FPS=30; SR=44100
raw=subprocess.run(["ffmpeg","-v","error","-i",A,"-f","s16le","-ac","1","-ar",str(SR),"-"],capture_output=True).stdout
voice=np.frombuffer(raw,np.int16).astype(np.float32)/32768
VD=len(voice)/SR; DUR=VD+1.3; N=int(DUR*FPS)
hop=SR//FPS
rms=np.array([np.sqrt(np.mean(voice[i*hop:(i+1)*hop]**2)) if i*hop<len(voice) else 0 for i in range(N)])
env=np.clip((rms-0.01)/ (np.percentile(rms[rms>0.01],90)-0.01),0,1)
env=np.convolve(env,[.25,.5,.25],"same")

# ---- robot base (Bit) without face features
svg=open(os.path.join(HERE,"..","bit","bit.svg")).read()
svg=re.sub(r'<g id="eyes">.*?</g>','',svg,flags=re.S); svg=re.sub(r'<path id="mouth"[^>]*/>','',svg)
S=1.35
base=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(),output_width=int(600*S),output_height=int(700*S)))).convert("RGBA")
CY=(0,240,255); PK=(255,43,214); GR=(57,255,136); RD=(255,70,90); WH=(255,255,255); GY=(170,175,190); BG=(13,13,20); PANEL=(24,26,40)
F=lambda n,s: ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{n}.ttf",s)
B84,B70,B56,B44,B36=F("DejaVuSans-Bold",84),F("DejaVuSans-Bold",70),F("DejaVuSans-Bold",56),F("DejaVuSans-Bold",44),F("DejaVuSans-Bold",36)
R34,R30=F("DejaVuSans",34),F("DejaVuSans",32)
M34,MB38=F("DejaVuSansMono",34),F("DejaVuSansMono-Bold",38)
rows=[("What is an API?",9,110),("What does git commit do?",9,114),("A Python list in 1 sentence",8,32),("Why never commit an API key?",9,125),("What is JSON?",9,106),("What does a for loop do?",9,112)]
# timeline (seconds)
T_TEST=3.4; T_PIPE=5.2; ROW_T=[6.0,7.0,8.0,9.75,16.6,16.9]; T_FAILWORD=11.1; T_CALLOUT=12.7; T_RESULT=16.5; T_SCORE=18.0; T_CTA=19.2
def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3
def face(d,f,t,ox,oy):
    s=S; P=lambda x,y:(ox+x*s,oy+y*s)
    a=env[f]; mood="norm"
    if T_FAILWORD<=t<T_RESULT: mood="shock"
    if t>=T_SCORE: mood="happy"
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
def label(d,t):
    if t<T_TEST: return "// 01 — the question"
    if t<9.6: return "// 02 — the test"
    if t<T_RESULT: return "// 03 — the fail"
    return "// 04 — result"
def counter(t):
    if t>=T_SCORE: return "SCORE 8.8/10"
    done=sum(1 for rt in ROW_T if t>=rt); return f"TESTS {done}/6"
def text_in(d,xy,txt,font,fill,t,t0,anchor="la",dy=30):
    k=ease((t-t0)/0.35)
    if k<=0: return
    col=tuple(int(BG[i]+(fill[i]-BG[i])*k) for i in range(3))
    d.text((xy[0],xy[1]+dy*(1-k)),txt,font=font,fill=col,anchor=anchor)
for f in range(N):
    t=f/FPS
    im=Image.new("RGB",(1080,1920),BG); d=ImageDraw.Draw(im)
    for y in range(0,1920,60): d.line((0,y,1080,y),fill=(20,21,32))
    d.text((60,80),label(d,t),font=M34,fill=CY)
    d.text((1020,78),counter(t),font=MB38,fill=PK,anchor="ra")
    if t<T_TEST:
        text_in(d,(60,330),"How do you know",B70,WH,t,0.05)
        text_in(d,(60,420),"if your",B70,WH,t,0.5)
        text_in(d,(60,510),"AI prompt",B84,CY,t,0.9)
        text_in(d,(60,620),"is actually good?",B70,WH,t,1.6)
    elif t<T_RESULT:
        text_in(d,(60,200),"Test it like code.",B70,WH,t,T_TEST)
        if t>=T_PIPE:
            text_in(d,(60,300),"6 questions → Claude → AI grader",R34,GY,t,T_PIPE,dy=15)
        dim = t>=T_CALLOUT
        for i,(q,sc,w) in enumerate(rows[:4]):
            rt=ROW_T[i]
            if t<rt: continue
            k=ease((t-rt)/0.3); y=380+i*100; x=60+int(40*(1-k))
            fail = i==3 and t>=T_FAILWORD
            box=(RD if fail else PANEL)
            d.rounded_rectangle((x,y,1020,y+84),radius=18,fill=PANEL,outline=(RD if fail else (40,44,66)),width=4 if fail else 2)
            fc=(110,110,125) if dim and i!=3 else WH
            d.text((x+28,y+42),f"{i+1}",font=B36,fill=CY,anchor="lm")
            d.text((x+80,y+42),q,font=R30,fill=fc,anchor="lm")
            d.text((x+770,y+42),f"{sc}/10",font=B36,fill=(255,214,0),anchor="rm")
            if i<3 or t>=T_FAILWORD:
                badge="FAIL" if fail else "PASS"; bc=RD if fail else GR
                d.rounded_rectangle((x+790,y+20,x+930,y+64),radius=12,fill=bc)
                d.text((x+860,y+42),badge,font=B36,fill=BG,anchor="mm")
        if t>=T_CALLOUT:
            k=ease((t-T_CALLOUT)/0.3)
            y0=800+int(40*(1-k))
            d.rounded_rectangle((60,y0,1020,y0+230),radius=24,fill=(40,12,22),outline=RD,width=5)
            d.text((100,y0+40),"125 words",font=B84,fill=RD)
            d.text((980,y0+62),"limit: 120",font=B56,fill=WH,anchor="ra")
            d.text((100,y0+160),"AI grader: 9/10 ✓    Code check: ✗",font=R34,fill=GY)
    else:
        text_in(d,(60,300),"5/6",B84,GR,t,T_RESULT+0.1)
        text_in(d,(270,300),"PASSED",B84,WH,t,T_RESULT+0.3)
        for i in range(6):
            if t>=T_RESULT+0.5+i*0.12:
                cx=90+i*90; d.ellipse((cx-30,470,cx+30,530),fill=(RD if i==3 else GR))
        if t>=T_SCORE: text_in(d,(60,600),"8.8/10 average",B70,CY,t,T_SCORE)
        if t>=T_CTA:
            text_in(d,(60,760),"Code in bio",B56,WH,t,T_CTA)
            text_in(d,(60,840),"@vibewithamitai",B44,PK,t,T_CTA+0.2)
    # robot
    bob=int(10*math.sin(t*2*math.pi*0.6))
    if T_RESULT<=t<T_RESULT+0.5: bob-=int(40*math.sin((t-T_RESULT)/0.5*math.pi))
    r=base.copy(); face(ImageDraw.Draw(r),f,t,0,0)
    if T_FAILWORD<=t<T_FAILWORD+0.4: ox=int(8*math.sin(t*90))
    else: ox=0
    im.paste(r,(330+ox,1040+bob),r)
    im.save(f"frames/{f:04d}.png")
# SFX
sfx=np.zeros(int(DUR*SR),np.float32)
def add(t0,sig):
    i=int(t0*SR); sfx[i:i+len(sig)]+=sig[:len(sfx)-i]
def tone(fr,d,dec=30,amp=.25,sq=False):
    tt=np.arange(int(d*SR))/SR; w=np.sin(2*np.pi*fr*tt)
    if sq: w=np.sign(w)*.5
    return (amp*w*np.exp(-dec*tt)).astype(np.float32)
for rt in ROW_T: add(rt,tone(1400,.08,40,.18))
add(T_FAILWORD,tone(150,.35,6,.22,True)); add(T_CALLOUT,tone(120,.25,8,.15,True))
add(T_SCORE,tone(880,.3,8,.18)); add(T_SCORE+0.12,tone(1320,.4,7,.18))
mix=sfx.copy(); mix[:len(voice)]+=voice
mix=np.clip(mix,-1,1)
with wave.open("audio.wav","wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
print("frames",N,"dur",DUR)
