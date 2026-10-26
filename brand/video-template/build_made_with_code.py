import re, io, math, subprocess, wave, numpy as np, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from prof import professor
W,H=1080,1920; FPS=30; SR=44100
raw=subprocess.run(["ffmpeg","-v","error","-i","vo.mp3","-f","s16le","-ac","1","-ar",str(SR),"-"],capture_output=True).stdout
voice=np.frombuffer(raw,np.int16).astype(np.float32)/32768
DUR=len(voice)/SR+1.5; N=int(DUR*FPS); hop=SR//FPS
rms=np.array([np.sqrt(np.mean(voice[i*hop:(i+1)*hop]**2)) if i*hop<len(voice) else 0 for i in range(N)])
env=np.clip((rms-0.01)/(np.percentile(rms[rms>0.01],90)-0.01),0,1); env=np.convolve(env,[.25,.5,.25],"same")
T2,T3,T3b,T4,T4b,T5,T5b,T6,T6b,T7,T8,T9,T9b=3.68,8.97,10.13,13.38,14.42,19.9,21.12,26.35,28.64,30.83,34.85,37.5,42.4
CY=(0,240,255); PK=(255,43,214); GR=(57,255,136); RD=(255,70,90); WH=(255,255,255); GY=(170,175,190); BG=(13,13,20); YL=(255,214,0)
FD=lambda s,w="DejaVuSans-Bold": ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{w}.ttf",s)
FI=lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",s)
def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3
def fade(c,k): return tuple(int(BG[i]+(c[i]-BG[i])*k) for i in range(3))
SVG=open("/home/claude/ai-learning-2026/brand/bit/bit.svg").read()
svg=re.sub(r'<g id="eyes">.*?</g>','',SVG,flags=re.S); svg=re.sub(r'<path id="mouth"[^>]*/>','',svg)
def png(s,scale): return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=s.encode(),output_width=int(600*scale),output_height=int(700*scale)))).convert("RGBA")
S=1.0; base=png(svg,S)
# wireframe version
wire=re.sub(r'fill="#[0-9A-Fa-f]{6}"','fill="none"',svg); wire=re.sub(r'stroke="#[0-9A-Fa-f]{6}"','stroke="#00F0FF"',wire)
wire=re.sub(r'(<line[^>]*stroke=")#00F0FF(" stroke-width=")\d+','\\1#00F0FF\\2 4',wire)
WIRE=png(wire,S)
# progressive assembly: top-level elements
head,body=svg.split(">",1); body=body.rsplit("</svg>",1)[0]
elems=re.findall(r'(<g[^>]*>.*?</g>|<[a-z]+[^>]*/>|<text[^>]*>.*?</text>)',body,flags=re.S)
ASM=[png(head+">"+"".join(elems[:k])+"</svg>",S) for k in range(len(elems)+1)]
CODE=[l.strip() for l in SVG.splitlines() if l.strip()][1:]
def bitimg(f,mood="norm",img=None):
    r=(img or base).copy(); d=ImageDraw.Draw(r); s=S; P=lambda x,y:(x*s,y*s); a=env[f]
    for ex in (244,356):
        cx,cy=P(ex,199)
        if mood=="happy": d.arc((cx-24*s,cy-14*s,cx+24*s,cy+30*s),200,340,fill=CY,width=int(10*s))
        elif (f%95) in (0,1,2): d.rounded_rectangle((cx-22*s,cy-4*s,cx+22*s,cy+4*s),radius=3,fill=CY)
        else: d.rounded_rectangle((cx-22*s,cy-29*s,cx+22*s,cy+29*s),radius=int(12*s),fill=CY)
    mx,my=P(300,262)
    if a>0.08:
        h=(8+38*a)*s; w=56*s; d.rounded_rectangle((mx-w/2,my-h/2,mx+w/2,my+h/2),radius=int(min(h,w)/2),fill=CY)
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
# sfx
tt=np.arange(int(DUR*SR))/SR; sfx=np.zeros_like(tt,dtype=np.float32); noise=np.random.default_rng(2).standard_normal(len(tt)).astype(np.float32)
def tone(t0,fr,d=.15,dec=20,amp=.12):
    i=int(t0*SR); n=int(d*SR); s=np.sin(2*np.pi*fr*tt[:n])*np.exp(-tt[:n]*dec)*amp; sfx[i:i+n]+=s[:len(sfx)-i]
def zap(t0,amp=.2):
    i=int(t0*SR); n=int(.18*SR); sfx[i:i+n]+=noise[:n]*amp*np.exp(-np.arange(n)/SR*15)
zap(1.8); zap(2.2,.12)
for k in range(3): tone(T2+k*1.3,700 if k<2 else 1320,.25,8,.12)
for k in range(len(elems)): tone(T3+0.25+k*0.25,900+k*40,.06,40,.08)
for k,fr in enumerate((440,660,880,1320)): tone(T6b+k*.45,fr,.3,6,.12)
for k in range(10): tone(T7+0.3+k*0.25,1600,.03,80,.05)
tone(T9,660,.3,6,.14); tone(T9+.12,880,.3,6,.14); tone(T9+.24,1320,.5,5,.14)
mix=sfx.copy(); mix[:len(voice)]+=voice; mix=np.clip(mix,-1,1)
with wave.open("audio.wav","wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
ff=subprocess.Popen(["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i","audio.wav","-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest","made-with-code.mp4"],stdin=subprocess.PIPE)
labels=[(T2,"// 01 — no video AI"),(T3,"// 02 — the hook"),(T4,"// 03 — I'm a drawing"),(T5,"// 04 — lip sync"),(T6,"// 05 — the professor"),(T7,"// 06 — sound"),(T8,"// 07 — render"),(T9,"// 08 — the code"),(99,"// 09 — your turn")]
mono=FD(30,"DejaVuSansMono"); monob=FD(26,"DejaVuSansMono")
for f in range(N):
    t=f/FPS; im=grid.copy(); d=ImageDraw.Draw(im)
    lab=next(l for lim,l in [(T2,"// made with code")]+[(lim,l) for lim,l in zip([T3,T4,T5,T6,T7,T8,T9,99],["// no video generator","// I'm a drawing","// lip sync","// the professor","// sound","// render","// the code","// your turn"])] if t<lim)
    d.text((60,80),lab,font=mono,fill=CY); d.text((1020,78),f"FRAME {f+1:04d}",font=FD(34,"DejaVuSansMono-Bold"),fill=PK,anchor="ra")
    show_bit=True; bimg=None; mood="norm"; bscale=1.0; by=1920
    if t<T2:
        k=ease(t/.4); tl=Image.new("RGBA",(W,H),(0,0,0,0)); td=ImageDraw.Draw(tl)
        td.text((W/2,380),"MADE",font=FI(170),fill=WH+(255,),anchor="mm"); td.text((W/2,560),"WITH CODE",font=FI(150),fill=CY+(255,),anchor="mm")
        for L in (tl.filter(ImageFilter.GaussianBlur(18)),tl):
            L2=L.copy(); L2.putalpha(L2.getchannel("A").point(lambda v:int(v*k))); im.alpha_composite(L2)
        d=ImageDraw.Draw(im)
        if t>1.8 and (int(t*14)%3!=0 or t>2.6): bimg=WIRE.copy()
    elif t<T3:
        items=[("✗  video generator",RD,T2),("✗  animation app",RD,T2+1.3),("✓  Claude + Python",GR,T2+2.6)]
        for j,(s_,c,t0) in enumerate(items):
            if card(d,(140,330+j*170,940,460+j*170),c,t,t0,(40,8,16) if c==RD else (12,26,20)): d.text((540,395+j*170),s_,font=FD(56),fill=c,anchor="mm")
        if t>T2+3.2:
            card(d,(140,860,940,960),CY,t,T2+3.2); d.text((180,910),"$ python3 build.py",font=FD(40,"DejaVuSansMono-Bold"),fill=CY,anchor="lm")
    elif t<T4:
        txt(d,(W/2,190),"I'm a drawing.",FI(90),WH,t,T3)
        card(d,(60,320,1020,860),CY,t,T3); d.text((90,345),"bit.svg",font=FD(28,"DejaVuSansMono-Bold"),fill=CY)
        n=int(min(len(CODE),(t-T3)*4)); vis=CODE[max(0,n-11):n]
        for j,l in enumerate(vis): d.text((90,395+j*42),(l[:56]+"…") if len(l)>57 else l,font=monob,fill=(200,205,220))
        k=int(min(len(elems),max(0,(t-T3-.25)/.25))); bimg=ASM[k] if k<len(elems) else None
        if k<len(elems): show_bit=True
    elif t<T5:
        txt(d,(W/2,190),"My mouth = your voice",FI(70),WH,t,T4)
        txt(d,(W/2,280),"measured 30× a second",FD(48),CY,t,T4b)
        card(d,(60,360,1020,800),CY,t,T4)
        if t>=T4:
            i0=int(t*SR); seg=voice[max(0,i0-int(1.2*SR)):i0]
            if len(seg)>10:
                seg=seg[::max(1,len(seg)//880)][:880]; pts=[(100+j,580-int(seg[j]*600)) for j in range(len(seg))]
                d.line(pts,fill=CY,width=3)
            lv=env[f]; d.rectangle((100,720,100+int(860*lv),760),fill=PK); d.rectangle((100,720,960,760),outline=(60,64,90),width=2)
            d.text((100,690),"loudness →  mouth size",font=FD(26),fill=GY)
    elif t<T7:
        show_bit=False
        if t<T6:
            txt(d,(W/2,190),"Professor Vague?",FI(80),(200,196,230),t,T5); txt(d,(W/2,290),"Also code.",FI(80),CY,t,T5b)
            k=ease((t-T5-.3)/1.8)
            p=professor(0.5+0.5*math.sin(t*12) if t>T5b+1.2 else 0,t,"smug",1.25)
            al=np.array(p.getchannel("A")).astype(np.float32); yy=np.arange(p.height)[:,None]
            al*=np.clip((k*p.height*1.1-yy)/60,0,1); p.putalpha(Image.fromarray(al.astype(np.uint8)))
            im.alpha_composite(p,(W//2-p.width//2,1920-p.height+60))
            d=ImageDraw.Draw(im)
            if t>T5b+3.0:
                card(d,(120,420,960,540),YL,t,T5b+3.0,(36,30,8)); d.text((540,480),"fog = e^(−r² / 2σ²)",font=FD(46,"DejaVuSans-Bold"),fill=YL,anchor="mm")
        else:
            txt(d,(W/2,190),"Every beep",FI(84),WH,t,T6); txt(d,(W/2,290),"is a sine wave.",FI(84),CY,t,T6+.3)
            card(d,(60,380,1020,820),CY,t,T6)
            ph=t*6; pts=[(100+x,600-int(150*math.sin(x/40+ph))) for x in range(0,860,4)]
            d.line(pts,fill=CY,width=6)
            if t>T6b: d.text((540,760),"sin(2π · 880 · t)",font=FD(44,"DejaVuSansMono-Bold"),fill=YL,anchor="mm")
    elif t<T8:
        txt(d,(W/2,190),"Frame by frame.",FI(84),WH,t,T7)
        for j in range(12):
            x=90+(j%4)*230; y=330+(j//4)*230; ph=(int(t*10)+j)%4
            d.rounded_rectangle((x,y,x+200,y+200),radius=16,fill=(20,22,34),outline=(60,64,90),width=3)
            m=["norm","happy","norm","happy"][ph]; th=bitimg(f,m).resize((150,175)); im.alpha_composite(th,(x+25,y+15)); d=ImageDraw.Draw(im)
        cnt=min(N,int(1+(t-T7)/(T8-T7)*N)); d.text((540,1080),f"frame {cnt:,} of {N:,}",font=FD(48,"DejaVuSansMono-Bold"),fill=PK,anchor="mm")
        show_bit=False
    elif t<T9:
        txt(d,(W/2,190),"The code is free.",FI(84),GR,t,T8)
        if card(d,(80,340,1000,640),GR,t,T8+.2,(12,26,20),5):
            d.text((540,420),"★  GitHub",font=FI(70),fill=WH,anchor="mm")
            d.text((540,520),"AmitP891/ai-learning-2026",font=FD(44,"DejaVuSansMono-Bold"),fill=GR,anchor="mm")
            d.text((540,585),"brand/ · link in bio",font=FD(36),fill=GY,anchor="mm")
    else:
        txt(d,(W/2,190),"Follow for the next build",FI(66),WH,t,T9)
        if t>=T9+.3:
            k=ease((t-T9-.3)/.35); pulse=1+0.04*math.sin((t-T9)*8); bw,bh=int(520*pulse),int(120*pulse)
            d.rounded_rectangle((540-bw/2,360-bh/2,540+bw/2,360+bh/2),radius=60,fill=fade((230,30,40),k)); d.text((540,360),"SUBSCRIBE",font=FI(64),fill=fade(WH,k),anchor="mm")
            for j,ic in enumerate(ICONS):
                a=ic.copy(); a.putalpha(a.getchannel("A").point(lambda v:int(v*k))); im.alpha_composite(a,(250+j*100,470))
            d=ImageDraw.Draw(im); d.text((560,512),"@vibewithamitai",font=FD(44),fill=fade(PK,k),anchor="lm")
        txt(d,(W/2,640),"Share with someone who still",FD(42),GY,t,T9+1.6); txt(d,(W/2,700),"uses an animation app 👀" if False else "uses an animation app",FD(42),GY,t,T9+1.6)
        txt(d,(W/2,860),"Build it. Test it. Ship it.",FD(56),CY,t,T9b)
        mood="happy" if t>T9b else "norm"
    if show_bit:
        r=bimg if bimg is not None and bimg is not base else bitimg(f,mood)
        if bimg is not None and bimg is WIRE: r=WIRE
        bob=int(10*math.sin(t*2*math.pi*.6))
        if T3<=t<T4: r=r.resize((int(r.width*1.0),int(r.height*1.0))); im.alpha_composite(r,(W//2-r.width//2,1920-r.height+10+bob))
        else: im.alpha_composite(r,(W//2-r.width//2,1920-r.height+20+bob))
    ff.stdin.write(im.convert("RGB").tobytes())
ff.stdin.close(); ff.wait(); print("done",N,round(DUR,1),len(elems))
