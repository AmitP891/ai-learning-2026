"""GLITCH, Bit's rival: final design (option B, 'hacker hood'), refined so he reads at in-game pixel size.
Writes glitch.svg (master, eyes and mouth in their own groups like bit.svg), one PNG per expression,
and a character sheet. Fixes over option B: lighter hood with a lime rim, hood and body in different
greys, brighter visor, lime soles, bigger chest screen."""
import io, os, re, cairosvg
from PIL import Image, ImageDraw, ImageFont
from build_options import glitch, pixel, render
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
OL, HOOD, BODY, HL, LI, VIS = "#0B0C14", "#2B2F45", "#3A3F55", "#4A5070", "#39FF88", "#0E1A16"
S = f'stroke="{OL}" stroke-width="6" stroke-linejoin="round"'

BASE = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 700" width="600" height="700">
<g id="arm-left"><line x1="190" y1="400" x2="130" y2="510" stroke="{OL}" stroke-width="58" stroke-linecap="square"/><line x1="190" y1="400" x2="130" y2="510" stroke="{HOOD}" stroke-width="46" stroke-linecap="square"/><rect x="100" y="500" width="58" height="50" rx="10" fill="{BODY}" {S}/></g>
<g id="arm-right"><line x1="410" y1="400" x2="470" y2="510" stroke="{OL}" stroke-width="58" stroke-linecap="square"/><line x1="410" y1="400" x2="470" y2="510" stroke="{HOOD}" stroke-width="46" stroke-linecap="square"/><rect x="442" y="500" width="58" height="50" rx="10" fill="{BODY}" {S}/></g>
<rect x="250" y="580" width="40" height="70" rx="8" fill="{BODY}" {S}/><rect x="310" y="580" width="40" height="70" rx="8" fill="{BODY}" {S}/>
<rect x="222" y="640" width="84" height="34" rx="8" fill="{HOOD}" {S}/><rect x="294" y="640" width="84" height="34" rx="8" fill="{HOOD}" {S}/>
<rect x="222" y="662" width="84" height="12" rx="4" fill="{LI}"/><rect x="294" y="662" width="84" height="12" rx="4" fill="{LI}"/>
<rect x="168" y="350" width="264" height="240" rx="40" fill="{HOOD}" {S}/>
<path d="M226 354 L300 424 L374 354" fill="none" stroke="{HL}" stroke-width="12" stroke-linejoin="round"/>
<line x1="268" y1="404" x2="258" y2="462" stroke="{LI}" stroke-width="7" stroke-linecap="round"/><circle cx="257" cy="468" r="7" fill="{LI}"/>
<line x1="332" y1="404" x2="342" y2="462" stroke="{LI}" stroke-width="7" stroke-linecap="round"/><circle cx="343" cy="468" r="7" fill="{LI}"/>
<rect x="216" y="482" width="168" height="78" rx="14" fill="{VIS}" {S}/>
<text x="300" y="537" font-family="DejaVu Sans Mono" font-weight="bold" font-size="48" fill="{LI}" text-anchor="middle">{{ }}</text>
<path d="M112 336 Q114 52 300 44 Q486 52 488 336 L444 350 L156 350 Z" fill="{HOOD}" {S}/>
<path d="M132 330 Q136 72 300 64 Q464 72 468 330" fill="none" stroke="{LI}" stroke-width="6" opacity="0.85"/>
<rect x="164" y="118" width="272" height="214" rx="42" fill="{BODY}" {S}/>
<rect x="164" y="282" width="272" height="50" rx="24" fill="{HOOD}" opacity="0.6"/>
<rect x="180" y="152" width="240" height="128" rx="22" fill="{VIS}" {S}/>
<g id="eyes">EYES</g>
<path id="mouth" d="MOUTH" stroke="{LI}" stroke-width="9" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

EXPR = {   # eyes, mouth path
    "smirk":   (f'<rect x="214" y="200" width="48" height="34" rx="8" fill="{LI}"/><rect x="338" y="178" width="48" height="58" rx="10" fill="{LI}"/>',
                "M262 258 L300 265 L344 248"),
    "typing":  ("".join(f'<rect x="{x}" y="{y}" width="{w}" height="10" rx="3" fill="{LI}"/>'
                        for x, y, w in [(208, 186, 40), (254, 186, 14), (206, 204, 22), (234, 204, 34), (210, 222, 44),
                                        (330, 186, 22), (358, 186, 34), (334, 204, 48), (330, 222, 18), (354, 222, 30)]),
                "M270 258 L330 258"),
    "shocked": (f'<rect x="206" y="168" width="64" height="68" rx="6" fill="{LI}"/><rect x="216" y="178" width="44" height="48" rx="4" fill="{VIS}"/>'
                f'<rect x="330" y="168" width="64" height="68" rx="6" fill="{LI}"/><rect x="340" y="178" width="44" height="48" rx="4" fill="{VIS}"/>',
                "M286 266 L314 266 L314 252 L286 252 Z"),
    "crashed": ("".join(f'<rect x="{196 + (i * 37) % 200}" y="{164 + (i * 23) % 104}" width="{8 + (i * 7) % 18}" height="8" fill="{LI if i % 3 else "#F5F4EF"}" opacity="{0.4 + (i % 4) * 0.15:.2f}"/>'
                        for i in range(46)),
                "M300 300 L300 300"),
}

def svg(expr):
    e, m = EXPR[expr]
    return BASE.replace("EYES", e).replace("MOUTH", m)

if __name__ == "__main__":
    open(os.path.join(HERE, "glitch.svg"), "w").write(svg("smirk"))
    for k in EXPR:
        render(svg(k), 1400).save(os.path.join(HERE, f"glitch_{k}.png"))
    F = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", s)
    M = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", s)
    W, H = 1640, 1100
    sh = Image.new("RGBA", (W, H), (13, 13, 20, 255)); d = ImageDraw.Draw(sh)
    d.text((40, 30), "GLITCH", font=F(96), fill=(57, 255, 136))
    d.text((40, 140), "Bit's rival. Cocky, fast, ships first, tests never.", font=M(30), fill=(245, 244, 239))
    bit = render(open(os.path.join(ROOT, "brand/bit/bit.svg")).read(), 520)
    sh.alpha_composite(bit, (40, 220)); sh.alpha_composite(render(svg("smirk"), 520), (470, 220))
    for i, k in enumerate(EXPR):
        x = 940 + (i % 2) * 340; y = 200 + (i // 2) * 330
        sh.alpha_composite(render(svg(k), 270), (x + 40, y))
        d.text((x + 175, y + 278), k.upper(), font=M(28), fill=(57, 255, 136), anchor="mt")
    d.text((40, 780), "GLITCHING", font=M(28), fill=(57, 255, 136))
    sh.alpha_composite(glitch(render(svg("smirk"), 260), seed=3), (40, 820))
    d.text((420, 780), "IN-GAME PIXEL SIZE, WITH BIT", font=M(28), fill=(57, 255, 136))
    gp = pixel(render(svg("smirk"), 420)); bp = pixel(bit)
    sh.alpha_composite(bp, (420, 830)); sh.alpha_composite(gp, (420 + bp.width + 40, 830))
    gp2 = pixel(render(svg("crashed"), 420)); sh.alpha_composite(gp2, (420 + bp.width + gp.width + 80, 830))
    out = os.path.join(HERE, "glitch_sheet.png"); sh.convert("RGB").save(out); print(out)
