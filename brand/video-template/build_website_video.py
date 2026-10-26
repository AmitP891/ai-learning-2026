import re, io, math, json, subprocess, wave, numpy as np, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FPS=30; SR=44100
raw=subprocess.run(["ffmpeg","-v","error","-i","vo.mp3","-f","s16le","-ac","1","-ar",str(SR),"-"],capture_output=True).stdout
voice=np.frombuffer(raw,np.int16).astype(np.float32)/32768
VD=len(voice)/SR; DUR=VD+1.5; N=int(DUR*FPS); hop=SR//FPS
rms=np.array([np.sqrt(np.mean(voice[i*hop:(i+1)*hop]**2)) if i*hop<len(voice) else 0 for i in range(N)])
env=np.clip((rms-0.01)/(np.percentile(rms[rms>0.01],90)-0.01),0,1); env=np.convolve(env,[.25,.5,.25],"same")
src=open("/home/claude/ai-learning-2026/brand/video-template/build_mcp_video.py").read()
ns={"Image":Image,"ImageDraw":ImageDraw,"ImageFont":ImageFont}
exec(src[src.index("def yt_icon"):src.index("YT=yt_icon")],ns); exec(src[src.index("def tt_icon"):src.index("TT=tt_icon")],ns)
YT,IG,TT=ns["yt_icon"](84),ns["ig_icon"](84),ns["tt_icon"](84)
CY=(0,240,255); PK=(255,43,214); GR=(57,255,136); RD=(255,70,90); WH=(255,255,255); GY=(170,175,190); BG=(13,13,20)
F=lambda n,s: ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{n}.ttf",s)
B70,B60,B44,B40=F("DejaVuSans-Bold",70),F("DejaVuSans-Bold",60),F("DejaVuSans-Bold",44),F("DejaVuSans-Bold",40)
M34,MB38,R34=F("DejaVuSansMono",34),F("DejaVuSansMono-Bold",38),F("DejaVuSans",34)
T1,T2,T3,T4,T5,T6,T6b,T7=5.44,7.5,9.97,12.05,18.28,19.26,24.2,0
Tyt,Ttt,Tig,Tgh=14.25,14.95,15.58,16.45
boxes=json.load(open("boxes.json"))
PW,PH=560,997; PX,PY=(1080-PW)//2,400; SC=PW/390
def scr(n): return Image.open(n+".png").convert("RGB").resize((PW,PH),Image.LANCZOS)
S={k:scr(k) for k in ["old_contact","new_contact","new_hero","new_videos"]}
S=dict(S); dim=Image.blend(S["new_hero"],Image.new("RGB",(PW,PH),BG),0.82)
S=S|{"dim":dim}
S_=1.0*0.72
svg=open("/home/claude/ai-learning-2026/brand/bit/bit.svg").read()
svg=re.sub(r'<g id="eyes">.*?</g>','',svg,flags=re.S); svg=re.sub(r'<path id="mouth"[^>]*/>','',svg)
base=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(),output_width=int(600*S_),output_height=int(700*S_)))).convert("RGBA")
def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3
def mood(t):
    if 1.2<=t<T1: return "shock"
    if T1<=t<T2 or t>=T6b: return "happy"
    return "norm"
def face(d,f,t):
    s=S_; P=lambda x,y:(x*s,y*s); a=env[f]; m=mood(t)
    blink=(f%95) in (0,1,2) and m=="norm"
    for ex in (244,356):
        cx,cy=P(ex,199)
        if blink: d.rounded_rectangle((cx-22*s,cy-4*s,cx+22*s,cy+4*s),radius=3,fill=CY)
        elif m=="happy": d.arc((cx-24*s,cy-14*s,cx+24*s,cy+30*s),200,340,fill=CY,width=int(10*s))
        elif m=="shock": d.ellipse((cx-27*s,cy-31*s,cx+27*s,cy+31*s),fill=CY); d.ellipse((cx-9*s,cy-9*s,cx+9*s,cy+9*s),fill=(23,26,43))
        else: d.rounded_rectangle((cx-22*s,cy-29*s,cx+22*s,cy+29*s),radius=int(12*s),fill=CY)
    mx,my=P(300,262)
    if a>0.08:
        h=(8+38*a)*s; w=(56 if m!="shock" else 40)*s
        d.rounded_rectangle((mx-w/2,my-h/2,mx+w/2,my+h/2),radius=int(min(h,w)/2),fill=CY)
    elif m=="shock": d.ellipse((mx-12*s,my-12*s,mx+12*s,my+12*s),outline=CY,width=int(7*s))
    else: d.arc((mx-40*s,my-40*s,mx+40*s,my+12*s),25,155,fill=CY,width=int(9*s))
def col(c,t,t0,dur=.35):
    k=ease((t-t0)/dur); return tuple(int(BG[i]+(c[i]-BG[i])*k) for i in range(3)),k
def txt(d,xy,s,font,c,t,t0,anchor="ma",dy=24):
    if t<t0: return
    cc,k=col(c,t,t0); d.text((xy[0],xy[1]+dy*(1-k)),s,font=font,fill=cc,anchor=anchor)
def hl(d,box,c,t,t0,label=None):
    if t<t0: return
    k=ease((t-t0)/0.3); x,y,w,h=box; x0=PX+x*SC-6; y0=PY+y*SC-6; x1=x0+w*SC+12; y1=y0+h*SC+12
    cc=tuple(int(BG[i]+(c[i]-BG[i])*k) for i in range(3))
    d.rounded_rectangle((x0,y0,x1,y1),radius=18,outline=cc,width=6)
def screen_at(t):
    if t<T1: return "old_contact"
    if t<T2: return "new_contact"
    if t<T3: return "new_hero"
    if t<T4: return "new_videos"
    if t<T5: return "new_contact"
    if t<T6b: return "dim"
    return "new_hero"
cuts=[T1,T2,T3,T4,T5,T6b]
def label(t):
    for lim,l in ((T1,"// 01 — the problem"),(T2,"// 02 — the fix"),(T4,"// 03 — the glow-up"),(T5,"// 04 — every platform"),(T6b,"// 05 — the best part")):
        if t<lim: return l
    return "// 06 — go see it"
def flowbox(d,y,txt_,c,t,t0):
    if t<t0: return
    cc,k=col(c,t,t0); yy=y+int(20*(1-k))
    d.rounded_rectangle((PX+40,yy,PX+PW-40,yy+120),radius=20,fill=(24,26,40),outline=cc,width=4)
    d.text((540,yy+60),txt_,font=B44,fill=cc,anchor="mm")
def arrow(d,y,c,t,t0):
    if t<t0: return
    cc,_=col(c,t,t0); d.line((540,y,540,y+50),fill=cc,width=6); d.polygon([(540,y+64),(524,y+40),(556,y+40)],fill=cc)
ff=subprocess.Popen(["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s","1080x1920","-r",str(FPS),"-i","-","-i","audio.wav","-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest","website-glow-up.mp4"],stdin=subprocess.PIPE)
# audio + sfx
sfx=np.zeros(int(DUR*SR),np.float32)
def add(t0,sig): i=int(t0*SR); sfx[i:i+len(sig)]+=sig[:len(sfx)-i]
def tone(fr,dd,dec=30,amp=.25,sq=False):
    tt=np.arange(int(dd*SR))/SR; w=np.sin(2*np.pi*fr*tt)
    if sq: w=np.sign(w)*.5
    return (amp*w*np.exp(-dec*tt)).astype(np.float32)
add(1.5,tone(150,.35,6,.18,True)); add(T1+0.3,tone(880,.3,8,.14)); add(T1+0.4,tone(1320,.4,7,.14))
for x in (Tyt,Ttt,Tig,Tgh): add(x,tone(1400,.08,40,.12))
for i,x in enumerate((T6,T6+0.9,T6+1.8,T6+2.7)): add(x,tone(900+200*i,.12,25,.12))
add(T6b,tone(660,.3,6,.14)); add(T6b+.12,tone(880,.3,6,.14)); add(T6b+.24,tone(1320,.5,5,.14))
mix=sfx.copy(); mix[:len(voice)]+=voice; mix=np.clip(mix,-1,1)
with wave.open("audio.wav","wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
ff=subprocess.Popen(ff.args,stdin=subprocess.PIPE) if False else ff
grid=Image.new("RGB",(1080,1920),BG); gd=ImageDraw.Draw(grid)
for y in range(0,1920,60): gd.line((0,y,1080,y),fill=(20,21,32))
for f in range(N):
    t=f/FPS
    im=grid.copy(); d=ImageDraw.Draw(im)
    d.text((60,80),label(t),font=M34,fill=CY)
    d.text((1020,78),"vibewithamit.com",font=MB38,fill=PK,anchor="ra")
    # headlines
    if t<T1: txt(d,(540,190),"My site still linked",B60,WH,t,0.05); txt(d,(540,270),"my OLD TikTok.",B70,RD,t,0.8)
    elif t<T2: txt(d,(540,190),"So I let Claude",B60,WH,t,T1); txt(d,(540,270),"fix it.",B70,GR,t,T1+0.2)
    elif t<T3: txt(d,(540,190),"Bit is now",B60,WH,t,T2); txt(d,(540,270),"front and centre.",B70,PK,t,T2+0.2)
    elif t<T4: txt(d,(540,190),"Newest video",B60,WH,t,T3); txt(d,(540,270),"on the homepage.",B70,CY,t,T3+0.2)
    elif t<T5: txt(d,(540,190),"Every platform,",B60,WH,t,T4); txt(d,(540,270),"one place.",B70,CY,t,T4+0.3)
    elif t<T6b: txt(d,(540,190),"The best part?",B60,WH,t,T5); txt(d,(540,270),"It updates itself.",B70,GR,t,T6)
    else: txt(d,(540,190),"Go see it 👇",B60,WH,t,T6b) if False else txt(d,(540,190),"Go take a look",B60,WH,t,T6b); txt(d,(540,270),"vibewithamit.com",B70,PK,t,T6b+0.2)
    # phone
    sc=screen_at(t); scrn=S[sc]
    prev=None
    for c in cuts:
        if c<=t<c+0.3: prev=screen_at(c-0.01); k=(t-c)/0.3
    if prev: scrn=Image.blend(S[prev],scrn,k)
    d.rounded_rectangle((PX-14,PY-14,PX+PW+14,PY+PH+14),radius=46,fill=(30,32,48),outline=(70,74,100),width=3)
    m=Image.new("L",(PW,PH),0); ImageDraw.Draw(m).rounded_rectangle((0,0,PW-1,PH-1),radius=34,fill=255)
    im.paste(scrn,(PX,PY),m)
    if t<T1: hl(d,boxes["old"][0],RD,t,1.3); hl(d,boxes["old"][2],RD,t,2.6); hl(d,boxes["old"][3],RD,t,2.9)
    elif t<T2: hl(d,boxes["new"][0],GR,t,T1+0.3)
    elif T4<=t<T5:
        for tt_,i in ((Tyt,2),(Ttt,0),(Tig,3),(Tgh,4)): hl(d,boxes["new"][i],GR,t,tt_)
    def pill(text,c,t0):
        if t<t0: return
        cc,k=col(c,t,t0); y=PY+PH-170+int(20*(1-k))
        w=d.textlength(text,font=B44)+70
        d.rounded_rectangle((540-w/2,y,540+w/2,y+96),radius=48,fill=(18,20,30),outline=cc,width=5)
        d.text((540,y+48),text,font=B44,fill=cc,anchor="mm")
    if 1.3<=t<T1: pill("TikTok: @gymvibecoder ✗",RD,1.3)
    elif T1<=t<T2: pill("TikTok: @vibewithamitai ✓",GR,T1+0.3)
    if T5<=t<T6b:
        y=PY+150
        flowbox(d,y,"I push a change",WH,t,T6); arrow(d,y+130,GY,t,T6+0.6)
        flowbox(d,y+210,"GitHub",WH,t,T6+0.9); arrow(d,y+340,GY,t,T6+1.5)
        flowbox(d,y+420,"Netlify builds it",CY,t,T6+1.8); arrow(d,y+550,GY,t,T6+2.4)
        flowbox(d,y+630,"Live ✓",GR,t,T6+2.7)
    if t>=T6b:
        k=ease((t-T6b-0.4)/0.35)
        if k>0:
            ov=Image.new("RGBA",(1080,1920),(0,0,0,0)); od=ImageDraw.Draw(ov)
            od.rounded_rectangle((PX+20,PY+PH-260,PX+PW-20,PY+PH-40),radius=28,fill=(13,13,20,int(235*k)),outline=PK+(int(255*k),),width=4)
            im.paste(ov,(0,0),ov); d=ImageDraw.Draw(im)
            for i,ic in enumerate((TT,YT,IG)):
                a=ic.copy(); a.putalpha(a.getchannel("A").point(lambda v:int(v*k))); im.paste(a,(PX+PW//2-140+i*100,PY+PH-235),a)
            cc,_=col(WH,t,T6b+0.5); d.text((540,PY+PH-110),"Link in bio",font=B44,fill=cc,anchor="mm")
    bob=int(8*math.sin(t*2*math.pi*0.6))
    shake=int(7*math.sin(t*90)) if 1.3<=t<1.65 else 0
    r=base.copy(); face(ImageDraw.Draw(r),f,t)
    im.paste(r,(540-r.width//2+shake,1405+bob),r)
    ff.stdin.write(im.tobytes())
ff.stdin.close(); ff.wait(); print("frames",N,DUR)
