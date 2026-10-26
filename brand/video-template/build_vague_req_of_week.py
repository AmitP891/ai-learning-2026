import re, io, math, subprocess, wave, textwrap, numpy as np, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from prof import professor
W,H=1080,1920; FPS=30; SR=44100
def load(f,filt=None):
    cmd=["ffmpeg","-v","error","-i",f]+(["-af",filt] if filt else [])+["-f","s16le","-ac","1","-ar",str(SR),"-"]
    return np.frombuffer(subprocess.run(cmd,capture_output=True).stdout,np.int16).astype(np.float32)/32768
bit=load("bit.mp3"); vag=load("vague.mp3","asetrate=44100*0.9,aresample=44100,atempo=1.08,aecho=0.8:0.6:90|180:0.35|0.2,volume=1.1")
CUT=1.95; V0=CUT+0.3; OFF=V0+len(vag)/SR+0.4-2.0
tracks={"bit":np.zeros(int((len(bit)/SR+OFF+3)*SR),np.float32)}; tracks["vague"]=np.zeros_like(tracks["bit"])
tracks["bit"][:int(CUT*SR)]+=bit[:int(CUT*SR)]
i=int((2.0+OFF)*SR); seg=bit[int(2.0*SR):]; tracks["bit"][i:i+len(seg)]+=seg
i=int(V0*SR); tracks["vague"][i:i+len(vag)]+=vag
B=lambda t: t+OFF  # bit-file time -> timeline (after the cut)
T_V=V0; T_REQ=B(2.15); T_WHO_Q=B(4.8); T_HOW_Q=B(5.94); T_CANT=B(7.09); T_WHO=B(10.5); T_WHAT=B(12.89); T_HOW=B(16.31); T_RW=B(20.28); T_AS=B(27.68); T_CTA=B(31.32); T_SUB=B(35.05); T_SIGN=B(36.73)
DUR=len(bit)/SR+OFF+1.2; N=int(DUR*FPS); hop=SR//FPS
def env(x):
    r=np.array([np.sqrt(np.mean(x[k*hop:(k+1)*hop]**2)) for k in range(N)]); nz=r[r>0.01]
    e=np.clip((r-0.01)/(np.percentile(nz,90)-0.01),0,1); return np.convolve(e,[.25,.5,.25],"same")
ENV={k:env(v) for k,v in tracks.items()}
CY=(0,240,255); PK=(255,43,214); GR=(57,255,136); RD=(255,70,90); WH=(255,255,255); GY=(170,175,190); BG=(13,13,20); YL=(255,214,0)
FD=lambda s,w="DejaVuSans-Bold": ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{w}.ttf",s)
FI=lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",s)
def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3
def fade(c,k): return tuple(int(BG[i]+(c[i]-BG[i])*k) for i in range(3))
S=1.0
svg=open("/home/claude/ai-learning-2026/brand/bit/bit.svg").read()
svg=re.sub(r'<g id="eyes">.*?</g>','',svg,flags=re.S); svg=re.sub(r'<path id="mouth"[^>]*/>','',svg)
base=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(),output_width=int(600*S),output_height=int(700*S)))).convert("RGBA")
def bitimg(f,mood):
    r=base.copy(); d=ImageDraw.Draw(r); s=S; P=lambda x,y:(x*s,y*s); a=ENV["bit"][f]
    blink=(f%95) in (0,1,2) and mood=="norm"
    for ex in (244,356):
        cx,cy=P(ex,199)
        if blink: d.rounded_rectangle((cx-22*s,cy-4*s,cx+22*s,cy+4*s),radius=3,fill=CY)
        elif mood=="happy": d.arc((cx-24*s,cy-14*s,cx+24*s,cy+30*s),200,340,fill=CY,width=int(10*s))
        elif mood=="shock": d.ellipse((cx-27*s,cy-31*s,cx+27*s,cy+31*s),fill=CY); d.ellipse((cx-9*s,cy-9*s,cx+9*s,cy+9*s),fill=(23,26,43))
        elif mood=="determined":
            pts=[(cx-26*s,cy-20*s),(cx+26*s,cy-6*s),(cx+26*s,cy+24*s),(cx-26*s,cy+24*s)] if ex<300 else [(cx-26*s,cy-6*s),(cx+26*s,cy-20*s),(cx+26*s,cy+24*s),(cx-26*s,cy+24*s)]
            d.polygon(pts,fill=CY)
        else: d.rounded_rectangle((cx-22*s,cy-29*s,cx+22*s,cy+29*s),radius=int(12*s),fill=CY)
    mx,my=P(300,262)
    if a>0.08:
        h=(8+38*a)*s; w=(56 if mood!="shock" else 40)*s; d.rounded_rectangle((mx-w/2,my-h/2,mx+w/2,my+h/2),radius=int(min(h,w)/2),fill=CY)
    elif mood=="shock": d.ellipse((mx-12*s,my-12*s,mx+12*s,my+12*s),outline=CY,width=int(7*s))
    elif mood=="determined": d.line((mx-34*s,my+4*s,mx+34*s,my-4*s),fill=CY,width=int(9*s))
    else: d.arc((mx-40*s,my-40*s,mx+40*s,my+12*s),25,155,fill=CY,width=int(9*s))
    return r
src=open("/home/claude/ai-learning-2026/brand/video-template/build_mcp_video.py").read(); ns={"Image":Image,"ImageDraw":ImageDraw,"ImageFont":ImageFont}
exec(src[src.index("def yt_icon"):src.index("YT=yt_icon")],ns); exec(src[src.index("def tt_icon"):src.index("TT=tt_icon")],ns)
ICONS=[ns["tt_icon"](84),ns["yt_icon"](84),ns["ig_icon"](84)]
def txt(d,xy,s,font,c,t,t0,anchor="ma",dy=24):
    if t<t0: return
    k=ease((t-t0)/.35); d.text((xy[0],xy[1]+dy*(1-k)),s,font=font,fill=fade(c,k),anchor=anchor)
def card(d,box,c,t,t0,fill=(20,22,34),w=4):
    if t<t0: return 0
    k=ease((t-t0)/.35); y=int(20*(1-k)); d.rounded_rectangle((box[0],box[1]+y,box[2],box[3]+y),radius=24,fill=fill,outline=fade(c,k),width=w); return k
grid=Image.new("RGBA",(W,H),BG+(255,)); gd=ImageDraw.Draw(grid)
for y in range(0,H,60): gd.line((0,y,W,y),fill=(20,21,32))
REQ=["The system shall be","easy to maintain."]
RW=textwrap.wrap("The system shall allow a trained technician to replace any line-replaceable unit within 30 minutes, using standard tools.",30)
ff=subprocess.Popen(["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i","audio.wav","-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest","vague-req-01-easy-to-maintain.mp4"],stdin=subprocess.PIPE)
# audio
tt=np.arange(len(tracks["bit"]))/SR; sfx=np.zeros_like(tt,dtype=np.float32); rng=np.random.default_rng(1); noise=rng.standard_normal(len(tt)).astype(np.float32)
def tone(t0,fr,d=.3,dec=8,amp=.14):
    i=int(t0*SR); n=int(d*SR); s=np.sin(2*np.pi*fr*tt[:n])*np.exp(-tt[:n]*dec)*amp; sfx[i:i+n]+=s[:len(sfx)-i]
def zap(t0,amp=.22):
    i=int(t0*SR); n=int(.2*SR); sfx[i:i+n]+=noise[:n]*amp*np.exp(-np.arange(n)/SR*15)
tone(0.1,660); tone(0.22,880); zap(T_V); zap(T_WHO_Q,.15); zap(T_HOW_Q,.15)
for x in (T_WHO,T_WHAT,T_HOW): tone(x,1400,.08,40,.12)
tone(T_RW,880); tone(T_RW+.1,1320); tone(T_CTA,660); tone(T_CTA+.12,880); tone(T_CTA+.24,1320,.5,5)
mix=sfx+tracks["bit"]+tracks["vague"]; mix=np.clip(mix/max(1,np.abs(mix).max()/.95),-1,1)
with wave.open("audio.wav","wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
for f in range(N):
    t=f/FPS; im=grid.copy(); d=ImageDraw.Draw(im)
    d.text((60,80),"// vague requirement of the week",font=FD(32,"DejaVuSansMono"),fill=CY)
    d.text((1020,78),"#1",font=FD(40,"DejaVuSansMono-Bold"),fill=PK,anchor="ra")
    mood="happy"
    if t<T_V:
        k=ease(t/.5); tl=Image.new("RGBA",(W,H),(0,0,0,0)); td=ImageDraw.Draw(tl)
        for j,(s_,c) in enumerate((("VAGUE",RD),("REQUIREMENT",WH),("OF THE WEEK",CY))): td.text((W/2,420+j*150),s_,font=FI(120),fill=c+(255,),anchor="mm")
        for L in (tl.filter(ImageFilter.GaussianBlur(16)),tl):
            L2=L.copy(); L2.putalpha(L2.getchannel("A").point(lambda v:int(v*k))); im.alpha_composite(L2)
        d=ImageDraw.Draw(im)
    elif t<T_REQ:
        k=ease((t-T_V)/.6)
        txt(d,(W/2,190),"Professor Vague",FI(70),(200,196,230),t,T_V)
        txt(d,(W/2,280),"has a new requirement...",FD(46),GY,t,T_V+.3)
        p=professor(ENV["vague"][f],t,"smug",1.15); p.putalpha(p.getchannel("A").point(lambda v:int(v*k)))
        im.alpha_composite(p,(W//2-p.width//2,1920-p.height+120+int(200*(1-k))))
        d=ImageDraw.Draw(im)
    else:
        mood="shock" if t<T_CANT else ("determined" if t<T_RW else "happy")
        if t<T_WHO:
            txt(d,(W/2,190),"You can't test",FI(76),WH,t,T_CANT); txt(d,(W/2,280),"\"easy\".",FI(90),RD,t,T_CANT+.2)
            card(d,(80,420,1000,700),CY,t,T_REQ)
            if t>=T_REQ:
                d.text((130,470),"REQ",font=FD(34,"DejaVuSansMono-Bold"),fill=CY)
                d.text((130,540),"The system shall be",font=FD(54),fill=WH)
                d.text((130,615),"easy",font=FD(54),fill=RD if t>=T_WHO_Q else WH); d.text((290,615),"to",font=FD(54),fill=WH); d.text((370,615),"maintain.",font=FD(54),fill=RD if t>=T_HOW_Q else WH)
            if card(d,(140,760,520,880),RD,t,T_WHO_Q,(40,8,16)): d.text((330,820),"Easy for who?",font=FD(42),fill=RD,anchor="mm")
            if card(d,(560,760,940,880),RD,t,T_HOW_Q,(40,8,16)): d.text((750,820),"How easy?",font=FD(42),fill=RD,anchor="mm")
        elif t<T_RW:
            txt(d,(W/2,190),"The fix:",FI(84),GR,t,T_WHO-.3); txt(d,(W/2,290),"who · what · how well",FD(48),GY,t,T_WHO-.1)
            for j,(lab,val,t0) in enumerate((("WHO","a trained technician",T_WHO),("WHAT","replaces any line-",T_WHAT),("HOW WELL","in under 30 minutes,",T_HOW))):
                y=400+j*255
                if card(d,(80,y,1000,y+225),GR,t,t0):
                    d.text((120,y+30),lab,font=FD(36,"DejaVuSansMono-Bold"),fill=GR)
                    d.text((120,y+90),val,font=FD(52),fill=WH)
                    extra={1:"replaceable unit",2:"with standard tools"}.get(j)
                    if extra: d.text((120,y+158),extra,font=FD(44),fill=WH)
        elif t<T_CTA:
            txt(d,(W/2,190),"Now it's",FI(76),WH,t,T_RW); txt(d,(W/2,280),"testable. ✓",FI(90),GR,t,T_RW+.2)
            if card(d,(70,420,1010,960),GR,t,T_RW,(12,26,20),5):
                d.text((110,460),"REQ (rewritten)",font=FD(34,"DejaVuSansMono-Bold"),fill=GR)
                for j,l in enumerate(RW): d.text((110,530+j*72),l,font=FD(50),fill=WH)
            if card(d,(140,1010,940,1130),YL,t,T_AS,(36,30,8)): d.text((540,1070),"30 min = [ASSUMED] ask your lead",font=FD(40),fill=YL,anchor="mm")
        else:
            txt(d,(W/2,190),"Got a worse one?",FI(80),WH,t,T_CTA)
            if card(d,(90,330,990,470),PK,t,T_CTA+.4,(40,8,34)): d.text((540,400),"Comment it below 👇" if False else "Comment it below",font=FD(58),fill=WH,anchor="mm")
            txt(d,(W/2,520),"I'll fix it next week.",FD(48),GY,t,T_CTA+1.0)
            if t>=T_SUB:
                k=ease((t-T_SUB)/.35); pulse=1+0.04*math.sin((t-T_SUB)*8)
                bw,bh=int(520*pulse),int(120*pulse); d.rounded_rectangle((540-bw/2,670-bh/2,540+bw/2,670+bh/2),radius=60,fill=fade((230,30,40),k))
                d.text((540,670),"SUBSCRIBE",font=FI(64),fill=fade(WH,k),anchor="mm")
                for j,ic in enumerate(ICONS):
                    a=ic.copy(); a.putalpha(a.getchannel("A").point(lambda v:int(v*k))); im.alpha_composite(a,(250+j*100,790))
                d=ImageDraw.Draw(im); d.text((560,832),"@vibewithamitai",font=FD(44),fill=fade(PK,k),anchor="lm")
            txt(d,(W/2,980),"Build it. Test it. Ship it.",FD(54),CY,t,T_SIGN)
    if not (T_V<=t<T_REQ):
        r=bitimg(f,mood); bob=int(10*math.sin(t*2*math.pi*.6)); sh=int(7*math.sin(t*80)) if mood=="shock" and t<T_REQ+1.0 else 0
        im.alpha_composite(r,(W//2-r.width//2+sh,1920-r.height+20+bob))
    ff.stdin.write(im.convert("RGB").tobytes())
ff.stdin.close(); ff.wait(); print("done",round(DUR,1))
