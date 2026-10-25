import re, io, math, subprocess, wave, random, numpy as np, cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
W,H=1080,1920; FPS=30; DUR=15.0; N=int(DUR*FPS); SR=44100
random.seed(7); rng=np.random.default_rng(7)
CY=(0,240,255); PK=(255,43,214); WH=(255,255,255); GRY=(150,155,170); BG=(8,9,18); RD=(255,70,90)
F=lambda n,s: ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{n}.ttf",s)
FB=lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",s)
M40=F("DejaVuSansMono-Bold",40); M30=F("DejaVuSansMono",30)
def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3
# --- sky
sky=Image.new("RGB",(W,H)); px=np.zeros((H,W,3),np.uint8)
g=np.linspace(0,1,H)[:,None]
px[...,0]=(8+18*g).astype(np.uint8); px[...,1]=(9+10*g).astype(np.uint8); px[...,2]=(22+30*g).astype(np.uint8)
sky=Image.fromarray(px); sd=ImageDraw.Draw(sky)
for _ in range(160):
    x,y=rng.integers(0,W),rng.integers(0,1100); r=rng.choice([1,1,2]); sd.ellipse((x-r,y-r,x+r,y+r),fill=(200,210,255))
# --- city: towers of requirement docs
towers=[]
x=-40
while x<W+40:
    w=int(rng.integers(110,190)); h=int(rng.integers(500,1150)); towers.append((x,w,h)); x+=w+int(rng.integers(8,30))
def city(grey):  # grey 0..1
    im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    base=1500
    for i,(x,w,h) in enumerate(towers):
        gi=min(1,max(0,grey*1.6-(i%5)*0.12))
        edge=tuple(int(CY[k]*(1-gi)+GRY[k]*gi*0.6) for k in range(3))
        d.rectangle((x,base-h,x+w,base),fill=(14,18,34),outline=edge,width=3)
        for ly in range(base-h+30,base-20,28):
            ln=int(w*rng.uniform(0.35,0.8)) if True else 0
            c=tuple(int(edge[k]*0.55) for k in range(3))
            d.line((x+16,ly,x+16+ln,ly),fill=c,width=4)
    d.rectangle((0,base,W,H),fill=(10,12,24))
    return im
rng_state=rng.bit_generator.state
cities=[]
for gv in np.linspace(0,1,11):
    rng.bit_generator.state=rng_state; cities.append(city(gv))
glow_c=[c.filter(ImageFilter.GaussianBlur(12)) for c in cities]
# --- fog sprite
def fog_sprite(sz,seed):
    r=np.random.default_rng(seed); a=np.zeros((sz,sz),np.float32); yy,xx=np.mgrid[0:sz,0:sz]
    for _ in range(40):
        cx,cy=r.normal(sz/2,sz/7,2); rr=r.uniform(sz/10,sz/4.5)
        a+=np.exp(-(((xx-cx)**2+(yy-cy)**2)/(2*rr**2)))*r.uniform(0.3,0.8)
    a=np.clip(a/a.max(),0,1)**1.2
    rr2=np.sqrt((xx-sz/2)**2+(yy-sz/2)**2)/(sz/2); a*=np.clip(1-rr2,0,1)**1.5
    im=Image.new("RGBA",(sz,sz),(120,124,140,0)); im.putalpha(Image.fromarray((a*235).astype(np.uint8)))
    return im.filter(ImageFilter.GaussianBlur(6))
fogs=[fog_sprite(700,s) for s in range(3)]
blob=fog_sprite(820,11)
# --- Bit
S=0.9
svg=open("/home/claude/ai-learning-2026/brand/bit/bit.svg").read()
svg=re.sub(r'<g id="eyes">.*?</g>','',svg,flags=re.S); svg=re.sub(r'<path id="mouth"[^>]*/>','',svg)
bitbase=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(),output_width=int(600*S),output_height=int(700*S)))).convert("RGBA")
def bit_face(mood,f):
    r=bitbase.copy(); d=ImageDraw.Draw(r); s=S; P=lambda x,y:(x*s,y*s)
    for ex in (244,356):
        cx,cy=P(ex,199)
        if mood=="shock": d.ellipse((cx-27*s,cy-31*s,cx+27*s,cy+31*s),fill=CY); d.ellipse((cx-9*s,cy-9*s,cx+9*s,cy+9*s),fill=(23,26,43))
        elif mood=="alert": d.rectangle((cx-24*s,cy-6*s,cx+24*s,cy+14*s),fill=RD)
        else: d.polygon([(cx-26*s,cy-20*s),(cx+26*s,cy-6*s),(cx+26*s,cy+24*s),(cx-26*s,cy+24*s)] if ex<300 else [(cx-26*s,cy-6*s),(cx+26*s,cy-20*s),(cx+26*s,cy+24*s),(cx-26*s,cy+24*s)],fill=CY)
    mx,my=P(300,262)
    if mood=="shock": d.ellipse((mx-14*s,my-14*s,mx+14*s,my+14*s),outline=CY,width=int(7*s))
    elif mood=="alert": d.line((mx-30*s,my,mx+30*s,my),fill=RD,width=int(9*s))
    else: d.line((mx-34*s,my+4*s,mx+34*s,my-4*s),fill=CY,width=int(9*s))
    return r
BIT={m:bit_face(m,0) for m in ("shock","alert","determined")}
def glitch_text(im,text,xy,font,col,t,t0,amp=1.0):
    if t<t0: return
    n=int(min(len(text),(t-t0)*18)); s=text[:n]
    d=ImageDraw.Draw(im); j=amp*(6 if random.random()<0.25 else 1.5)
    d.text((xy[0]+j,xy[1]),s,font=font,fill=(255,40,80),anchor="ma"); d.text((xy[0]-j,xy[1]),s,font=font,fill=(0,200,255),anchor="ma"); d.text(xy,s,font=font,fill=col,anchor="ma")
# --- render
ff=subprocess.Popen(["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p","silent.mp4"],stdin=subprocess.PIPE)
T_FOG,T_EYES,T_BIT,T_TITLE=2.8,6.0,8.6,10.6
title_f=FB(118); ep_f=FB(56); sm_f=F("DejaVuSans-Bold",40)
for f in range(N):
    t=f/FPS
    im=sky.copy()
    zoom=1+0.04*t/DUR
    gv=min(1,max(0,(t-T_FOG)/3.5))
    ci=int(round(gv*10))
    layer=Image.alpha_composite(glow_c[ci],cities[ci])
    if zoom!=1:
        lw,lh=int(W*zoom),int(H*zoom); layer=layer.resize((lw,lh)); layer=layer.crop(((lw-W)//2,(lh-H)//2,(lw-W)//2+W,(lh-H)//2+H))
    im.paste(layer,(0,0),layer)
    # fog drift
    if t>=T_FOG:
        k=ease((t-T_FOG)/3.0)
        for i,fg in enumerate(fogs):
            x=int(-700+ (W+200)*k*0.9 + i*260 + 30*math.sin(t*0.8+i)); y=900+i*170+int(20*math.sin(t*1.1+i))
            im.paste(fg,(x,y),fg); im.paste(fg,(x-650,y+80),fg)
    d=ImageDraw.Draw(im)
    # villain eyes
    if T_EYES<=t<T_TITLE+0.4:
        k=ease((t-T_EYES)/0.6); bx,by=W//2-410,420
        b=blob.copy(); b.putalpha(b.getchannel("A").point(lambda v:int(v*k))); im.paste(b,(bx,by),b)
        d=ImageDraw.Draw(im); qf=FB(int(150+20*math.sin(t*6)))
        for ex in (W//2-120,W//2+120):
            c=(int(235*k),int(235*k),int(250*k)); d.text((ex,760),"?",font=qf,fill=c,anchor="mm")
        glitch_text(im,"The system shall be... fast.",(W//2,1000),F("DejaVuSans-Bold",50),(220,220,235),t,T_EYES+0.4)
        glitch_text(im,"T B D . . .",(W//2,1090),F("DejaVuSansMono-Bold",58),RD,t,T_EYES+1.6,amp=2)
    elif T_FOG<=t<T_EYES:
        glitch_text(im,"Something is spreading in Spec City...",(W//2,330),F("DejaVuSans-Bold",44),(200,205,220),t,T_FOG+0.3)
    if t<T_FOG:
        k=ease(t/0.8); c=tuple(int(v*k) for v in CY)
        d.text((W//2,300),"In Spec City,",font=F("DejaVuSans-Bold",54),fill=c,anchor="ma")
        if t>1.0: k2=ease((t-1.0)/0.6); d.text((W//2,380),"every requirement must be tested.",font=F("DejaVuSans-Bold",44),fill=tuple(int(v*k2) for v in WH),anchor="ma")
    # Bit
    if T_BIT<=t<T_TITLE+0.2:
        k=ease((t-T_BIT)/0.45); mood="shock" if t<T_BIT+0.8 else ("alert" if t<T_BIT+1.4 else "determined")
        r=BIT[mood]; y=int(1920-(r.height-40)*k); sh=int(8*math.sin(t*80)) if mood=="shock" else 0
        im.paste(r,(W//2-r.width//2+sh,y),r); d=ImageDraw.Draw(im)
        if mood!="shock":
            fl=0.6+0.4*abs(math.sin(t*10)); d.rounded_rectangle((W//2-260,1195,W//2+260,1285),radius=20,fill=(40,0,10),outline=tuple(int(v*fl) for v in RD),width=5)
            d.text((W//2,1240),"MISSION ALERT",font=M40,fill=tuple(int(v*fl) for v in RD),anchor="mm")
    # title card
    if t>=T_TITLE:
        k=ease((t-T_TITLE)/0.5)
        ov=Image.new("RGBA",(W,H),(6,6,14,int(215*k))); im.paste(ov,(0,0),ov)
        tl=Image.new("RGBA",(W,H),(0,0,0,0)); td=ImageDraw.Draw(tl)
        td.text((W//2,560),"THE",font=FB(70),fill=CY+(255,),anchor="mm")
        td.text((W//2,690),"ADVENTURES",font=title_f,fill=WH+(255,),anchor="mm")
        td.text((W//2,830),"OF BIT",font=FB(150),fill=PK+(255,),anchor="mm")
        gl=tl.filter(ImageFilter.GaussianBlur(18))
        a=int(255*k); 
        for L in (gl,gl,tl): L2=L.copy(); L2.putalpha(L2.getchannel("A").point(lambda v:int(v*k))); im.paste(L2,(0,0),L2)
        d=ImageDraw.Draw(im)
        if t>T_TITLE+0.7:
            k2=ease((t-T_TITLE-0.7)/0.4)
            d.text((W//2,990),"Episode 1: The Vague One",font=ep_f,fill=tuple(int(v*k2) for v in WH),anchor="mm")
        if t>T_TITLE+1.3:
            k3=ease((t-T_TITLE-1.3)/0.4)
            d.rounded_rectangle((W//2-330,1080,W//2+330,1180),radius=50,fill=tuple(int(v*k3) for v in (40,10,40)),outline=tuple(int(v*k3) for v in PK),width=4)
            d.text((W//2,1130),"COMING 28 NOVEMBER",font=F("DejaVuSans-Bold",46),fill=tuple(int(v*k3) for v in WH),anchor="mm")
            d.text((W//2,1260),"on YouTube  ·  @vibewithamitai",font=sm_f,fill=tuple(int(v*k3) for v in GRY),anchor="mm")
        r=BIT["determined"]; small=r.resize((int(r.width*0.55),int(r.height*0.55)))
        bob=int(8*math.sin(t*3)); im.paste(small,(W//2-small.width//2,1400+bob),small)
    # vignette flash on impact
    if T_TITLE<=t<T_TITLE+0.12:
        fl=Image.new("RGB",(W,H),(255,255,255)); im=Image.blend(im,fl,0.5*(1-(t-T_TITLE)/0.12))
    ff.stdin.write(im.convert("RGB").tobytes())
ff.stdin.close(); ff.wait()
# --- music
tt=np.arange(int(DUR*SR))/SR; mus=np.zeros_like(tt,dtype=np.float32)
def env(a,b,att=0.5,rel=0.8):
    e=np.clip((tt-a)/att,0,1)*np.clip((b-tt)/rel,0,1); return e
drone=(np.sin(2*np.pi*55*tt)+0.5*np.sin(2*np.pi*82.4*tt)+0.3*np.sign(np.sin(2*np.pi*27.5*tt)))*0.12
mus+=drone*env(0,T_TITLE,1.5,0.3)
for b in np.arange(T_FOG,T_TITLE,0.75):
    i=int(b*SR); n=int(0.25*SR); s=np.sin(2*np.pi*48*tt[:n])*np.exp(-tt[:n]*18)*0.5; mus[i:i+n]+=s[:len(mus)-i]
for b in np.arange(0,T_FOG,0.5):
    i=int(b*SR); n=int(0.4*SR); s=np.sin(2*np.pi*(880 if int(b*2)%2==0 else 660)*tt[:n])*np.exp(-tt[:n]*6)*0.08; mus[i:i+n]+=s[:len(mus)-i]
# riser
r0,r1=T_BIT,T_TITLE; m=(tt>=r0)&(tt<r1); ph=np.cumsum(np.where(m,2*np.pi*(200+1800*((tt-r0)/(r1-r0))**2)/SR,0))
mus+=np.where(m,np.sin(ph)*0.1*((tt-r0)/(r1-r0)),0)
noise=rng.standard_normal(len(tt)).astype(np.float32)
mus+=np.where(m,noise*0.06*((tt-r0)/(r1-r0)),0)
# glitch zaps
for z in (T_EYES+0.4,T_EYES+1.6,T_BIT):
    i=int(z*SR); n=int(0.18*SR); mus[i:i+n]+=noise[:n]*0.25*np.exp(-np.arange(n)/SR*15)
# impact + chord
i=int(T_TITLE*SR); n=int(3*SR)
imp=(np.sin(2*np.pi*45*tt[:n])*np.exp(-tt[:n]*3)*0.7+noise[:n]*np.exp(-tt[:n]*10)*0.3)
mus[i:i+n]+=imp[:len(mus)-i]
for fr in (220,277.2,329.6,440):
    ch=np.sin(2*np.pi*fr*tt[:n])*np.exp(-tt[:n]*0.6)*0.07; mus[i:i+n]+=ch[:len(mus)-i]
mus=mus/np.max(np.abs(mus))*0.85
with wave.open("music.wav","wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mus*32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg","-y","-v","error","-i","silent.mp4","-i","music.wav","-c:v","copy","-c:a","aac","-b:a","192k","-shortest","adventures-of-bit-coming-soon.mp4"])
print("done")
