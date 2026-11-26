from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import math
W,H=1280,720
F='/home/claude/ai-learning-2026/brand/fonts/Bangers-Regular.ttf'
# background: pink-to-purple radial
bg=Image.new('RGB',(W,H))
px=bg.load()
for y in range(H):
    for x in range(W):
        d=math.hypot((x-640)/900,(y-380)/600)
        t=min(1,d)
        px[x,y]=(int(236*(1-t)+40*t),int(72*(1-t)+12*t),int(153*(1-t)+70*t))
# light rays
ray=Image.new('L',(W,H),0); rd=ImageDraw.Draw(ray)
for a in range(0,360,15):
    r=math.radians(a); r2=math.radians(a+6)
    rd.polygon([(640,380),(640+1500*math.cos(r),380+1500*math.sin(r)),(640+1500*math.cos(r2),380+1500*math.sin(r2))],fill=35)
bg=Image.composite(Image.new('RGB',(W,H),(255,170,220)),bg,ray)

def panel(img,box,h,border,glow):
    p=img.crop(box); p=p.resize((int(p.width*h/p.height),h),Image.LANCZOS)
    m=Image.new('L',p.size,0); ImageDraw.Draw(m).rounded_rectangle((0,0,p.width-1,p.height-1),28,fill=255)
    return p,m
happy=Image.open('/mnt/user-data/uploads/6c533ec5-image.png').convert('RGB')
dead=Image.open('fr_0.5.png').convert('RGB')
hp,hm=panel(happy,(1065,420,1875,1230),420,None,None)
dp,dm=panel(dead,(1065,420,1875,1230),440,None,None)
dp=ImageEnhance.Brightness(dp).enhance(0.9)

def place(base,p,m,xy,col,rot):
    # glow + border, rotated
    pad=30
    canvas=Image.new('RGBA',(p.width+pad*2,p.height+pad*2),(0,0,0,0))
    border=Image.new('RGBA',canvas.size,(0,0,0,0))
    ImageDraw.Draw(border).rounded_rectangle((pad-10,pad-10,pad+p.width+9,pad+p.height+9),36,fill=col)
    glow=border.filter(ImageFilter.GaussianBlur(14))
    canvas=Image.alpha_composite(canvas,glow); canvas=Image.alpha_composite(canvas,border)
    pr=p.convert('RGBA'); pr.putalpha(m)
    canvas.alpha_composite(pr,(pad,pad))
    canvas=canvas.rotate(rot,expand=True,resample=Image.BICUBIC)
    base.paste(canvas,xy,canvas)
base=bg.convert('RGBA')
place(base,hp,hm,(30,170),(120,255,170,255),4)
place(base,dp,dm,(700,160),(255,60,60,255),-4)
d=ImageDraw.Draw(base)
def text(s,xy,size,fill,stroke=10,anchor='la'):
    f=ImageFont.truetype(F,size)
    d.text((xy[0]+6,xy[1]+8),s,font=f,fill=(0,0,0,160),anchor=anchor,stroke_width=stroke,stroke_fill=(0,0,0,160))
    d.text(xy,s,font=f,fill=fill,anchor=anchor,stroke_width=stroke,stroke_fill=(20,10,40))
text('I LEFT HIM FOR 24 HOURS',(640,20),118,(255,224,60),12,'ma')
# arrow
d.polygon([(720,400),(630,345),(630,375),(555,375),(555,425),(630,425),(630,455)],fill=(255,224,60),outline=(20,10,40),width=6)
# tags
text('1 HOUR',(270,690),66,(140,255,180),8,'ms')
text('24 HOURS',(950,700),66,(255,90,90),8,'ms')
# battery 0%
bx,by=1100,150
d.rounded_rectangle((bx,by,bx+130,by+62),12,fill=(20,10,40),outline=(255,255,255),width=6)
d.rectangle((bx+130,by+18,bx+142,by+44),fill=(255,255,255))
text('0%',(bx+65,by+31),44,(255,80,80),5,'mm')
base.convert('RGB').save('bit-pet-thumb-draft.jpg',quality=92)
