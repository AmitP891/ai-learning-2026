"""Four design options for GLITCH, Bit's rival (Level 3). Same drawing style as brand/bit/bit.svg:
600x700 viewBox, #0B0C14 outlines, flat fills. Renders a comparison sheet with Bit for scale,
the signature sideways glitch, and an in-game pixel preview."""
import io, os, random, cairosvg
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
OL, GM, GD, GS, LI, LD, VIS = "#0B0C14", "#3A3F55", "#23263A", "#4A5070", "#39FF88", "#1F9E55", "#101220"
S = 'stroke="#0B0C14" stroke-width="6" stroke-linejoin="round"'

def smirk_eyes(lx, rx, y, w=44, h=58):
    # left eye narrowed (flat top), right eye full: the smirk
    return (f'<rect x="{lx}" y="{y+22}" width="{w}" height="{h-22}" rx="8" fill="{LI}"/>'
            f'<rect x="{rx}" y="{y}" width="{w}" height="{h}" rx="10" fill="{LI}"/>')

def legs(colour):
    return (f'<rect x="250" y="580" width="40" height="70" rx="8" fill="{GD}" {S}/>'
            f'<rect x="310" y="580" width="40" height="70" rx="8" fill="{GD}" {S}/>'
            f'<rect x="222" y="640" width="84" height="34" rx="8" fill="{colour}" {S}/>'
            f'<rect x="294" y="640" width="84" height="34" rx="8" fill="{colour}" {S}/>')

def arms(c=GM):
    return (f'<line x1="190" y1="400" x2="130" y2="510" stroke="{OL}" stroke-width="58" stroke-linecap="square"/>'
            f'<line x1="190" y1="400" x2="130" y2="510" stroke="{c}" stroke-width="46" stroke-linecap="square"/>'
            f'<rect x="100" y="500" width="58" height="50" rx="10" fill="{GD}" {S}/>'
            f'<line x1="410" y1="400" x2="470" y2="510" stroke="{OL}" stroke-width="58" stroke-linecap="square"/>'
            f'<line x1="410" y1="400" x2="470" y2="510" stroke="{c}" stroke-width="46" stroke-linecap="square"/>'
            f'<rect x="442" y="500" width="58" height="50" rx="10" fill="{GD}" {S}/>')

def bent_antenna(x=330):
    return (f'<polyline points="{x},98 {x},62 {x+34},40" fill="none" stroke="{GS}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<rect x="{x+24}" y="22" width="26" height="26" fill="{LI}" {S}/>')

# A: Classic rival. Bit's silhouette made boxy and sharp, wide visor, >_ chest screen
A = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 700" width="600" height="700">
{bent_antenna()}{arms()}{legs(LI)}
<rect x="168" y="350" width="264" height="240" rx="18" fill="{GM}" {S}/>
<rect x="168" y="530" width="264" height="60" rx="14" fill="{GD}"/>
<rect x="225" y="400" width="150" height="95" rx="10" fill="{VIS}" {S}/>
<text x="300" y="463" font-family="DejaVu Sans Mono" font-weight="bold" font-size="48" fill="{LI}" text-anchor="middle">&gt;_</text>
<rect x="272" y="320" width="56" height="40" fill="{GD}" {S}/>
<rect x="140" y="95" width="320" height="240" rx="16" fill="{GM}" {S}/>
<rect x="140" y="275" width="320" height="60" rx="12" fill="{GD}" opacity="0.8"/>
<rect x="166" y="130" width="268" height="150" rx="10" fill="{VIS}" {S}/>
{smirk_eyes(214, 340, 170)}
<path d="M262 255 L300 262 L344 246" stroke="{LI}" stroke-width="9" fill="none" stroke-linecap="round"/>
<rect x="440" y="140" width="14" height="40" fill="{LI}"/>
</svg>'''

# B: Hacker hood. A dark hood over the head, glowing lime visor band in the shadow, { } chest
B = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 700" width="600" height="700">
{arms(GD)}{legs(GD)}
<rect x="168" y="350" width="264" height="240" rx="40" fill="{GD}" {S}/>
<path d="M232 352 L300 420 L368 352" fill="none" stroke="{GS}" stroke-width="10"/>
<line x1="270" y1="400" x2="262" y2="470" stroke="{LI}" stroke-width="6"/><line x1="330" y1="400" x2="338" y2="470" stroke="{LI}" stroke-width="6"/>
<rect x="232" y="480" width="136" height="70" rx="12" fill="{VIS}" {S}/>
<text x="300" y="530" font-family="DejaVu Sans Mono" font-weight="bold" font-size="42" fill="{LI}" text-anchor="middle">{{ }}</text>
<path d="M118 330 Q120 60 300 52 Q480 60 482 330 L440 345 L160 345 Z" fill="{GD}" {S}/>
<rect x="166" y="120" width="268" height="210" rx="40" fill="{GM}" {S}/>
<rect x="182" y="158" width="236" height="122" rx="20" fill="{VIS}" {S}/>
{smirk_eyes(216, 340, 182, 44, 52)}
<path d="M264 262 L300 268 L340 254" stroke="{LI}" stroke-width="8" fill="none" stroke-linecap="round"/>
</svg>'''

# C: CRT head. An old chunky monitor for a head with scanlines, tank treads for speed, SHIP on the chest
scan = "".join(f'<line x1="186" y1="{y}" x2="414" y2="{y}" stroke="{LI}" stroke-width="2" opacity="0.18"/>' for y in range(150, 290, 10))
C = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 700" width="600" height="700">
{bent_antenna(250)}{arms()}
<rect x="190" y="590" width="220" height="80" rx="40" fill="{GD}" {S}/>
<circle cx="236" cy="630" r="22" fill="{GS}" {S}/><circle cx="300" cy="630" r="22" fill="{GS}" {S}/><circle cx="364" cy="630" r="22" fill="{GS}" {S}/>
<rect x="178" y="350" width="244" height="240" rx="24" fill="{GM}" {S}/>
<rect x="210" y="410" width="180" height="76" rx="10" fill="{VIS}" {S}/>
<text x="300" y="463" font-family="DejaVu Sans Mono" font-weight="bold" font-size="40" fill="{LI}" text-anchor="middle">SHIP</text>
<rect x="272" y="320" width="56" height="40" fill="{GD}" {S}/>
<rect x="128" y="92" width="344" height="246" rx="30" fill="{GM}" {S}/>
<rect x="430" y="120" width="30" height="190" rx="6" fill="{GD}"/>
<rect x="160" y="122" width="270" height="186" rx="40" fill="{VIS}" {S}/>
{scan}
{smirk_eyes(204, 316, 168)}
<path d="M250 258 L290 266 L330 250" stroke="{LI}" stroke-width="9" fill="none" stroke-linecap="round"/>
<circle cx="448" cy="290" r="9" fill="{LI}"/>
</svg>'''

# D: Speed bot. Slimmer and angular, a single shades-style visor, lightning-bolt antenna, wheel feet
D = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 700" width="600" height="700">
<polygon points="300,98 316,62 296,62 318,18 280,70 300,70 288,98" fill="{LI}" {S}/>
{arms()}
<rect x="252" y="580" width="36" height="56" rx="6" fill="{GD}" {S}/><rect x="312" y="580" width="36" height="56" rx="6" fill="{GD}" {S}/>
<circle cx="270" cy="652" r="24" fill="{GS}" {S}/><circle cx="330" cy="652" r="24" fill="{GS}" {S}/>
<circle cx="270" cy="652" r="8" fill="{LI}"/><circle cx="330" cy="652" r="8" fill="{LI}"/>
<polygon points="182,350 418,350 400,590 200,590" fill="{GM}" stroke="{OL}" stroke-width="6" stroke-linejoin="round"/>
<polygon points="200,350 240,350 222,590 205,590" fill="{LI}" opacity="0.9"/>
<rect x="250" y="410" width="120" height="80" rx="8" fill="{VIS}" {S}/>
<text x="310" y="462" font-family="DejaVu Sans Mono" font-weight="bold" font-size="34" fill="{LI}" text-anchor="middle">2X</text>
<rect x="272" y="320" width="56" height="40" fill="{GD}" {S}/>
<polygon points="150,110 450,95 440,335 160,335" fill="{GM}" stroke="{OL}" stroke-width="6" stroke-linejoin="round"/>
<polygon points="160,175 446,160 444,236 158,246" fill="{VIS}" stroke="{OL}" stroke-width="6" stroke-linejoin="round"/>
<polygon points="196,214 262,208 262,224 196,230" fill="{LI}"/>
<polygon points="334,186 404,180 404,226 334,230" fill="{LI}"/>
<path d="M262 292 L300 298 L348 280" stroke="{LI}" stroke-width="9" fill="none" stroke-linecap="round"/>
</svg>'''

OPTIONS = {"A": ("Classic rival", A), "B": ("Hacker hood", B), "C": ("CRT head", C), "D": ("Speed bot", D)}

def render(svg, h):
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=round(600 * h / 700), output_height=h))).convert("RGBA")
    return im

def glitch(im, seed, px=4):
    """Signature move: a few horizontal slices shifted sideways by whole 'game pixels'."""
    r = random.Random(seed); out = im.copy(); out.paste((0, 0, 0, 0), (0, 0, *im.size))
    out.alpha_composite(im)
    for _ in range(3):
        y0 = r.randrange(im.height // 6, im.height * 5 // 6); hgt = r.choice([2, 3, 4]) * px
        dx = r.choice([-3, -2, 2, 3]) * px
        sl = im.crop((0, y0, im.width, y0 + hgt))
        out.paste((0, 0, 0, 0), (0, y0, im.width, y0 + hgt)); out.alpha_composite(sl, (max(0, dx), y0)) if dx > 0 else out.alpha_composite(sl.crop((-dx, 0, sl.width, sl.height)), (0, y0))
    return out

def pixel(im, h=39):
    w = round(im.width * h / im.height)
    small = im.resize((w, h), Image.BOX)
    a = small.getchannel("A").point(lambda v: 255 if v > 110 else 0); small.putalpha(a)
    return small.resize((w * 6, h * 6), Image.NEAREST)

if __name__ == "__main__":
    F = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", s)
    M = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", s)
    bit = render(open(os.path.join(ROOT, "brand/bit/bit.svg")).read(), 420)
    CW, CH = 820, 900
    sheet = Image.new("RGBA", (CW * 2, CH * 2), (13, 13, 20, 255)); d = ImageDraw.Draw(sheet)
    for i, (k, (name, svg)) in enumerate(OPTIONS.items()):
        open(os.path.join(HERE, f"glitch_{k}.svg"), "w").write(svg)
        ox, oy = (i % 2) * CW, (i // 2) * CH
        d.rounded_rectangle((ox + 14, oy + 14, ox + CW - 14, oy + CH - 14), 26, outline=(57, 255, 136), width=3)
        d.text((ox + 40, oy + 34), f"{k}  {name.upper()}", font=F(52), fill=(245, 244, 239))
        g = render(svg, 420)
        sheet.alpha_composite(bit, (ox + 40, oy + 130))                      # Bit for scale
        sheet.alpha_composite(g, (ox + 400, oy + 130))                       # clean design
        gl = glitch(render(svg, 230), seed=i)
        sheet.alpha_composite(gl, (ox + 60, oy + 590))                       # glitching
        d.text((ox + 60, oy + 830), "GLITCHING", font=M(26), fill=(57, 255, 136))
        px = pixel(g)
        sheet.alpha_composite(px, (ox + 330, oy + 590))                      # in-game pixel size
        bp = pixel(bit); sheet.alpha_composite(bp, (ox + 330 + px.width + 30, oy + 590))
        d.text((ox + 330, oy + 830), "IN-GAME, WITH BIT", font=M(26), fill=(57, 255, 136))
        render(svg, 1400).save(os.path.join(HERE, f"glitch_{k}.png"))
    out = os.path.join(HERE, "glitch_options.png"); sheet.convert("RGB").save(out); print(out)
