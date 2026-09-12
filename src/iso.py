# -*- coding: utf-8 -*-
"""Larktun 宣传片分镜 —— 等距(isometric)矢量分镜生成器 · 核心库"""
import math

# ---------- 画布 ----------
W, H = 1080, 1920

# ---------- 调色板（改这里即可换品牌色） ----------
P = dict(
    bg0="#05070E", bg1="#0C1220", bg2="#151E33", bg3="#202B45",
    ink="#F4F7FC", mute="#93A1BC", dim="#5A6784",
    wall="#EFE7DA", wallD="#D6C9B6", wallS="#BFB09A",
    floor="#CFA271", floorD="#B0834F", floorS="#8E6639",
    wood="#9C6F45", woodD="#7C5535",
    risk="#FF4B4B", risk2="#FF8A3D", riskDim="#7A1E24",
    brand="#2FE0C8", brand2="#49A0FF", brandDim="#0E5B55",
    gold="#FFC65C", cool="#8FD3FF", steel="#3D4A66", steelD="#2A344A",
)

C30, S30 = math.cos(math.radians(30)), 0.5

# ---------- 等距投影 ----------
def iso(x, y, z, s=1.0, ox=0.0, oy=0.0):
    """+x → 右下 , +y → 左下 , +z → 上"""
    return (ox + (x - y) * C30 * s, oy + ((x + y) * S30 - z) * s)

def pts(seq):
    return " ".join(f"{a:.2f},{b:.2f}" for a, b in seq)

# ---------- 颜色明暗 ----------
def shade(hexc, k):
    hexc = hexc.lstrip("#")
    r, g, b = (int(hexc[i:i+2], 16) for i in (0, 2, 4))
    if k <= 1:
        r, g, b = r*k, g*k, b*k
    else:
        r, g, b = r+(255-r)*(k-1), g+(255-g)*(k-1), b+(255-b)*(k-1)
    return "#%02x%02x%02x" % (max(0,min(255,int(r))), max(0,min(255,int(g))), max(0,min(255,int(b))))

TOPK, LK, RK = 1.0, 0.80, 0.60   # 顶面 / 左立面 / 右立面 亮度


class Art:
    """SVG 元素累加器（带等距坐标系配置）"""
    def __init__(self, s=1.0, ox=W/2, oy=900):
        self.s, self.ox, self.oy = s, ox, oy
        self.el = []

    def p(self, x, y, z):
        return iso(x, y, z, self.s, self.ox, self.oy)

    def add(self, e):
        self.el.append(e); return self

    def out(self):
        return "\n".join(self.el)

    # ---- 基础几何 ----
    def poly(self, coords3, fill, op=1.0, stroke="none", sw=0, extra=""):
        self.add(f'<polygon points="{pts([self.p(*c) for c in coords3])}" fill="{fill}" '
                 f'fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" {extra}/>')

    def box(self, x, y, z, dx, dy, dz, col, op=1.0, top=None, edge=None, extra=""):
        """等距立方体：顶面 + 左立面(y+dy) + 右立面(x+dx)"""
        t = top or shade(col, TOPK)
        L, R = shade(col, LK), shade(col, RK)
        e = f'stroke="{edge}" stroke-width="1.2"' if edge else 'stroke="none"'
        for coords, f in (
            ([(x,y,z+dz),(x+dx,y,z+dz),(x+dx,y+dy,z+dz),(x,y+dy,z+dz)], t),
            ([(x,y+dy,z),(x+dx,y+dy,z),(x+dx,y+dy,z+dz),(x,y+dy,z+dz)], L),
            ([(x+dx,y,z),(x+dx,y+dy,z),(x+dx,y+dy,z+dz),(x+dx,y,z+dz)], R),
        ):
            self.add(f'<polygon points="{pts([self.p(*c) for c in coords])}" fill="{f}" '
                     f'fill-opacity="{op}" {e} stroke-linejoin="round" {extra}/>')
        return self

    def slab(self, x, y, z, dx, dy, col, op=1.0, extra=""):
        self.poly([(x,y,z),(x+dx,y,z),(x+dx,y+dy,z),(x,y+dy,z)], col, op, extra=extra)
        return self

    def shadow(self, x, y, rx=1.0, ry=1.0, op=.35, z=0.02):
        cx, cy = self.p(x, y, z)
        self.add(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx*self.s*C30*2:.1f}" ry="{ry*self.s*S30*2:.1f}" '
                 f'fill="#000" fill-opacity="{op}" filter="url(#soft)"/>')
        return self

    # ---- 屏幕坐标绘制（人物 / UI 等） ----
    def sxy(self, x, y, z):
        return self.p(x, y, z)


# ---------- SVG 文档骨架 ----------
def defs(extra=""):
    return f'''<defs>
  <radialGradient id="sky" cx="50%" cy="30%" r="80%">
    <stop offset="0%" stop-color="{P['bg2']}"/><stop offset="60%" stop-color="{P['bg1']}"/>
    <stop offset="100%" stop-color="{P['bg0']}"/>
  </radialGradient>
  <linearGradient id="fadeB" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{P['bg0']}" stop-opacity="0"/>
    <stop offset="100%" stop-color="{P['bg0']}" stop-opacity="1"/>
  </linearGradient>
  <linearGradient id="fadeT" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{P['bg0']}" stop-opacity=".95"/>
    <stop offset="100%" stop-color="{P['bg0']}" stop-opacity="0"/>
  </linearGradient>
  <filter id="soft" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="14"/></filter>
  <filter id="soft6" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="6"/></filter>
  <filter id="glowR" x="-120%" y="-120%" width="340%" height="340%">
    <feGaussianBlur stdDeviation="16" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="glowS" x="-120%" y="-120%" width="340%" height="340%">
    <feGaussianBlur stdDeviation="7" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="grain">
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" stitchTiles="stitch"/>
    <feColorMatrix type="saturate" values="0"/>
  </filter>
  <radialGradient id="vig" cx="50%" cy="46%" r="72%">
    <stop offset="55%" stop-color="#000" stop-opacity="0"/>
    <stop offset="100%" stop-color="#000" stop-opacity=".72"/>
  </radialGradient>
  {extra}
</defs>'''


def frame_svg(body, sid, tc, dur, caption, kicker="", accent=None, bgextra="", topnote=""):
    """把一场戏包成 1080x1920 竖屏分镜画面"""
    accent = accent or P['brand']
    cap = ""
    if caption:
        lines = caption.split("\n")
        n = len(lines)
        y0 = 1592 - (n - 1) * 78
        tspans = "".join(
            f'<tspan x="540" dy="{0 if i==0 else 88}">{l}</tspan>' for i, l in enumerate(lines))
        cap = f'''<g>
  <text x="540" y="{y0}" text-anchor="middle" font-family="Noto Sans CJK SC" font-weight="900"
        font-size="74" fill="{P['ink']}" letter-spacing="1.5"
        style="paint-order:stroke;stroke:#05070E;stroke-width:14px;stroke-linejoin:round">{tspans}</text>
</g>'''
    kick = ""
    if kicker:
        kick = f'''<text x="540" y="{1592 - (len(caption.split(chr(10)))-1)*78 - 92}" text-anchor="middle"
        font-family="Noto Sans CJK SC" font-weight="700" font-size="34" fill="{accent}"
        letter-spacing="8">{kicker}</text>'''
    note = ""
    if topnote:
        note = f'''<text x="540" y="1720" text-anchor="middle" font-family="Noto Sans CJK SC"
        font-weight="500" font-size="30" fill="{P['dim']}" letter-spacing="2">{topnote}</text>'''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
{defs(bgextra)}
<rect width="{W}" height="{H}" fill="url(#sky)"/>
{body}
<rect width="{W}" height="{H}" fill="url(#vig)"/>
<rect width="{W}" height="{H}" filter="url(#grain)" opacity=".10" style="mix-blend-mode:overlay"/>
<rect x="0" y="0" width="{W}" height="230" fill="url(#fadeT)" opacity=".85"/>
<rect x="0" y="1340" width="{W}" height="580" fill="url(#fadeB)" opacity=".92"/>
<g>
  <rect x="56" y="66" width="196" height="62" rx="31" fill="{accent}" fill-opacity=".14"
        stroke="{accent}" stroke-opacity=".5"/>
  <text x="154" y="108" text-anchor="middle" font-family="Noto Sans CJK SC" font-weight="800"
        font-size="30" fill="{accent}" letter-spacing="2">{sid}</text>
  <text x="280" y="108" font-family="Noto Sans CJK SC" font-weight="600" font-size="30"
        fill="{P['mute']}" letter-spacing="1">{tc}  ·  {dur}</text>
  <text x="1024" y="108" text-anchor="end" font-family="Noto Sans CJK SC" font-weight="700"
        font-size="26" fill="{P['dim']}" letter-spacing="3">LARKTUN 云雀通 · 9:16</text>
</g>
{kick}
{cap}
{note}
</svg>'''
