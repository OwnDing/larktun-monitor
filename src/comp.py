# -*- coding: utf-8 -*-
"""可复用等距组件：剖面屋 / 摄像头 / 人物 / 录像机 / 云塔 / 手机 / 数据流"""
import math
from iso import Art, P, shade, pts, TOPK, LK, RK, C30, S30

# ---------------- 剖面屋 ----------------
def room(a, ox, oy, w, d, h, t=0.35, wall=None, floor=None, win=True, warm=0.0):
    """两面后墙 + 地板的等距剖面房间。ox,oy 为房间内侧原点(x,y)。"""
    wall = wall or P['wall']; floor = floor or P['floor']
    # 后墙 A：沿 x 轴（投影在左上），内表面朝 +y
    a.box(ox - t, oy - t, 0, w + t, t, h, wall)
    # 后墙 B：沿 y 轴，内表面朝 +x
    a.box(ox - t, oy, 0, t, d, h, shade(wall, .94))
    # 地板
    a.slab(ox, oy, 0, w, d, shade(floor, .92))
    # 地板木纹
    n = int(w / .55)
    for i in range(1, n):
        x = ox + i * (w / n)
        a.add(f'<line x1="{a.p(x,oy,0)[0]:.1f}" y1="{a.p(x,oy,0)[1]:.1f}" '
              f'x2="{a.p(x,oy+d,0)[0]:.1f}" y2="{a.p(x,oy+d,0)[1]:.1f}" '
              f'stroke="{shade(floor,.78)}" stroke-width="1.1" stroke-opacity=".55"/>')
    # 踢脚线
    a.poly([(ox,oy,0),(ox+w,oy,0),(ox+w,oy,.12),(ox,oy,.12)], shade(wall,.72))
    if win:
        wx, ww, wh, wz = ox + w*0.52, w*0.32, h*0.44, h*0.34
        col = P['cool'] if warm < .5 else P['gold']
        a.poly([(wx,oy-.002,wz),(wx+ww,oy-.002,wz),(wx+ww,oy-.002,wz+wh),(wx,oy-.002,wz+wh)],
               shade(col,.55), op=.9)
        a.poly([(wx,oy-.004,wz),(wx+ww,oy-.004,wz),(wx+ww,oy-.004,wz+wh),(wx,oy-.004,wz+wh)],
               "none", stroke=shade(wall,.6), sw=3)
        a.add(f'<line x1="{a.p(wx+ww/2,oy-.006,wz)[0]:.1f}" y1="{a.p(wx+ww/2,oy-.006,wz)[1]:.1f}" '
              f'x2="{a.p(wx+ww/2,oy-.006,wz+wh)[0]:.1f}" y2="{a.p(wx+ww/2,oy-.006,wz+wh)[1]:.1f}" '
              f'stroke="{shade(wall,.6)}" stroke-width="3"/>')
    return a

def rug(a, x, y, w, d, col="#2D3A57", op=.9):
    a.slab(x, y, .006, w, d, col, op)
    a.poly([(x,y,.008),(x+w,y,.008),(x+w,y+d,.008),(x,y+d,.008)], "none",
           stroke=shade(col,1.25), sw=2, extra='stroke-opacity=".6"')

# ---------------- 家具 ----------------
def sofa(a, x, y, fw=1.9, fd=.85):
    a.shadow(x+fw/2, y+fd/2, fw*.55, fd*.7, .40)
    a.box(x, y, 0, fw, fd, .30, "#3E4C6D")           # 座
    a.box(x, y, .30, fw, fd*.55, .16, "#4A5A80")     # 垫
    a.box(x, y-.16, 0, fw, .18, .72, "#465578")      # 靠背
    a.box(x-.14, y-.16, 0, .16, fd+.16, .52, "#3A4869")
    a.box(x+fw-.02, y-.16, 0, .16, fd+.16, .52, "#3A4869")

def table(a, x, y, w=1.0, d=.6, h=.42, col=None):
    col = col or P['wood']
    a.shadow(x+w/2, y+d/2, w*.5, d*.7, .35)
    for cx, cy in ((x+.06,y+.06),(x+w-.14,y+.06),(x+.06,y+d-.14),(x+w-.14,y+d-.14)):
        a.box(cx, cy, 0, .08, .08, h-.06, shade(col,.7))
    a.box(x, y, h-.06, w, d, .06, col)

def chair(a, x, y, col=None):
    col = col or P['woodD']
    a.box(x, y, 0, .40, .40, .40, col)
    a.box(x, y-.06, .40, .40, .07, .42, shade(col,1.08))

def tv(a, x, y, w=1.35, h=.78, z=.55):
    a.box(x, y-.06, z-.04, w, .10, h+.08, "#161C2A")
    a.poly([(x+.05,y-.09,z),(x+w-.05,y-.09,z),(x+w-.05,y-.09,z+h-.06),(x+.05,y-.09,z+h-.06)],
           "#0B1220")
    a.box(x+w/2-.06, y-.02, 0, .12, .12, z-.04, "#222B3D")

def shelf(a, x, y, w=1.2, h=1.1):
    a.box(x, y-.02, 0, w, .34, h, "#5A4632")
    for i in (1,2):
        a.poly([(x+.02,y+.30,h*i/3),(x+w-.02,y+.30,h*i/3),(x+w-.02,y+.30,h*i/3+.03),(x+.02,y+.30,h*i/3+.03)],
               "#6C563E")

def plant(a, x, y, s=1.0):
    a.shadow(x, y, .28*s, .28*s, .35)
    a.box(x-.13*s, y-.13*s, 0, .26*s, .26*s, .26*s, "#8A6C52")
    cx, cy = a.p(x, y, .26*s)
    for ang, ln in ((-58,.62),(-25,.50),(14,.56),(48,.44),(-90,.66)):
        r = math.radians(ang); L = ln*s*a.s
        a.add(f'<path d="M{cx:.1f},{cy:.1f} q{math.cos(r)*L*.45:.1f},{math.sin(r)*L*.55-L*.35:.1f} '
              f'{math.cos(r)*L:.1f},{math.sin(r)*L-L*.5:.1f}" stroke="#3E8F6B" stroke-width="{7*a.s/70:.1f}" '
              f'fill="none" stroke-linecap="round"/>')

def crib(a, x, y):
    a.shadow(x+.45, y+.35, .5, .45, .35)
    a.box(x, y, 0, .92, .62, .34, "#C8B49A")
    a.box(x+.05, y+.05, .34, .82, .52, .10, "#E7DCCB")
    for i in range(6):
        a.box(x+.05+i*.15, y-.02, .34, .045, .045, .34, "#D9C7AE")

# ---------------- 摄像头 ----------------
def cam(a, x, y, z, led=None, on=True, face="y", sc=1.0):
    """吸顶/壁装小方摄像头；face='y' 朝 +y（向左下），'x' 朝 +x（向右下）"""
    led = led or P['risk']
    b = .22*sc
    a.box(x, y, z, b*1.5, b, b, "#E8EAEF")                  # 机身
    a.box(x+b*.45, y+b*.9, z+b*.15, b*.55, b*.5, b*.6, "#20283A")   # 镜头罩
    lx, ly, lz = (x+b*1.15, y+b*1.35, z+b*.45)
    cx, cy = a.p(lx, ly, lz)
    r = 9*a.s/70*sc
    a.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r*1.9:.1f}" fill="#0C1220"/>')
    a.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="#1B4A6B"/>')
    a.add(f'<circle cx="{cx-r*.3:.1f}" cy="{cy-r*.3:.1f}" r="{r*.35:.1f}" fill="#BFE8FF" opacity=".8"/>')
    if on:
        ex, ey = a.p(x+b*.2, y+b*1.3, z+b*.72)
        a.add(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{5.5*a.s/70*sc:.1f}" fill="{led}" filter="url(#glowR)"/>')
    # 支架
    a.box(x+b*.6, y-b*.25, z-b*.28, b*.3, b*.3, b*.3, "#C9CFDA")
    return a

def cam_cone(a, x, y, z, col=None, op=.16, length=2.6, spread=1.0):
    """摄像头视野锥（朝 +y 斜下）"""
    col = col or P['cool']
    o = a.p(x, y, z)
    p1 = a.p(x - spread*.9, y + length, 0)
    p2 = a.p(x + spread*1.5, y + length*.7, 0)
    a.add(f'<polygon points="{o[0]:.1f},{o[1]:.1f} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" '
          f'fill="{col}" fill-opacity="{op}" filter="url(#soft6)"/>')

# ---------------- 人物 ----------------
def person(a, x, y, z=0, h=1.0, col="#5C7BD6", skin="#E9C39B", lean=0):
    """朝屏幕的简化人形（等距微缩风）"""
    fx, fy = a.p(x, y, z)
    u = a.s * h / 70.0          # 单位
    a.shadow(x, y, .22*h, .22*h, .38)
    hh = 100*u                  # 身高像素
    bw = 30*u
    a.add(f'''<g transform="translate({fx:.1f},{fy:.1f})">
  <path d="M{-bw/2:.1f},0 L{-bw*.44:.1f},{-hh*.52:.1f} Q{-bw*.5:.1f},{-hh*.62:.1f} {-bw*.28:.1f},{-hh*.64:.1f}
           L{bw*.28:.1f},{-hh*.64:.1f} Q{bw*.5:.1f},{-hh*.62:.1f} {bw*.44:.1f},{-hh*.52:.1f}
           L{bw/2:.1f},0 Z" fill="{col}"/>
  <path d="M{-bw*.28:.1f},{-hh*.64:.1f} L{bw*.28:.1f},{-hh*.64:.1f} L{bw*.30:.1f},{-hh*.50:.1f} L{-bw*.30:.1f},{-hh*.50:.1f} Z"
        fill="{shade(col,1.18)}" opacity=".55"/>
  <circle cx="0" cy="{-hh*.79:.1f}" r="{hh*.145:.1f}" fill="{skin}"/>
  <path d="M{-hh*.145:.1f},{-hh*.82:.1f} a{hh*.145:.1f},{hh*.145:.1f} 0 0 1 {hh*.29:.1f},0 z" fill="#2B2320"/>
</g>''')
    return a

def person_phone(a, x, y, z=0, h=1.0, col="#5C7BD6", glow=None):
    person(a, x, y, z, h, col)
    fx, fy = a.p(x, y, z)
    u = a.s * h / 70.0; hh = 100*u
    g = glow or P['brand']
    a.add(f'''<g transform="translate({fx:.1f},{fy:.1f})">
  <rect x="{hh*.11:.1f}" y="{-hh*.60:.1f}" width="{hh*.15:.1f}" height="{hh*.23:.1f}" rx="{hh*.03:.1f}"
        fill="#10192B" stroke="{g}" stroke-width="{max(1.2,hh*.012):.1f}"/>
  <rect x="{hh*.125:.1f}" y="{-hh*.585:.1f}" width="{hh*.12:.1f}" height="{hh*.20:.1f}" rx="{hh*.02:.1f}"
        fill="{g}" opacity=".55" filter="url(#glowS)"/>
</g>''')

# ---------------- 设备 ----------------
def nas(a, x, y, z=0, on=True, sc=1.0, col=None):
    col = col or "#2A3346"
    w, d, h = .56*sc, .42*sc, .48*sc
    a.shadow(x+w/2, y+d/2, w*.6, d*.8, .42)
    a.box(x, y, z, w, d, h, col, edge=shade(col,1.35))
    for i in range(4):     # 硬盘槽（在 +y 立面）
        zz = z + h - .07*sc - i*.10*sc
        a.poly([(x+.05*sc,y+d+.002,zz),(x+w-.05*sc,y+d+.002,zz),
                (x+w-.05*sc,y+d+.002,zz+.06*sc),(x+.05*sc,y+d+.002,zz+.06*sc)],
               shade(col,.62))
        if on:
            px, py = a.p(x+w-.09*sc, y+d+.004, zz+.03*sc)
            a.add(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{4.2*a.s/70*sc:.1f}" fill="{P["brand"]}" filter="url(#glowS)"/>')
    return a

def nvr(a, x, y, z=0, sc=1.0):
    """硬盘录像机：扁平一体机"""
    w, d, h = .78*sc, .50*sc, .16*sc
    a.shadow(x+w/2, y+d/2, w*.6, d*.8, .40)
    a.box(x, y, z, w, d, h, "#232B3C", edge="#3C4761")
    for i in range(3):
        px, py = a.p(x+.10*sc+i*.09*sc, y+d+.004, z+h*.5)
        a.add(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{4*a.s/70*sc:.1f}" '
              f'fill="{P["brand"] if i<2 else P["gold"]}" filter="url(#glowS)"/>')

def router(a, x, y, z=0, sc=1.0):
    w, d, h = .40*sc, .32*sc, .09*sc
    a.shadow(x+w/2, y+d/2, w*.6, d*.8, .35)
    a.box(x, y, z, w, d, h, "#2E3848", edge="#49556F")
    for i, (ax, hh) in enumerate(((.06,.30),(.20,.36),(.34,.30))):
        p0 = a.p(x+ax*sc, y+.05*sc, z+h); p1 = a.p(x+ax*sc-.05*sc, y+.05*sc, z+h+hh*sc)
        a.add(f'<line x1="{p0[0]:.1f}" y1="{p0[1]:.1f}" x2="{p1[0]:.1f}" y2="{p1[1]:.1f}" '
              f'stroke="#49556F" stroke-width="{5*a.s/70:.1f}" stroke-linecap="round"/>')

# ---------------- 数据流 ----------------
def stream(a, p0, p1, col=None, w=6, bow=-140, op=1.0, dash=None, glow="glowR", arrow=False):
    """p0/p1 为 (x,y,z) 三维点；bow 为屏幕空间弯曲量(负=向上凸)"""
    col = col or P['risk']
    A, B = a.p(*p0), a.p(*p1)
    mx, my = (A[0]+B[0])/2, (A[1]+B[1])/2 + bow
    d = f"M{A[0]:.1f},{A[1]:.1f} Q{mx:.1f},{my:.1f} {B[0]:.1f},{B[1]:.1f}"
    a.add(f'<path d="{d}" stroke="{col}" stroke-width="{w*2.4:.1f}" stroke-opacity="{op*.22}" '
          f'fill="none" stroke-linecap="round" filter="url(#{glow})"/>')
    ds = f'stroke-dasharray="{dash}"' if dash else ""
    a.add(f'<path d="{d}" stroke="{col}" stroke-width="{w}" stroke-opacity="{op}" fill="none" '
          f'stroke-linecap="round" {ds}/>')
    if arrow:
        import math as _m
        ang = _m.atan2(B[1]-my, B[0]-mx)
        s = w*2.6
        a.add(f'<polygon points="{B[0]:.1f},{B[1]:.1f} '
              f'{B[0]-s*_m.cos(ang-.45):.1f},{B[1]-s*_m.sin(ang-.45):.1f} '
              f'{B[0]-s*_m.cos(ang+.45):.1f},{B[1]-s*_m.sin(ang+.45):.1f}" fill="{col}"/>')
    return (A, B, (mx, my))

def packets(a, p0, p1, col=None, bow=-140, n=6, r=7, op=1.0):
    """沿流动路径撒数据包方块"""
    col = col or P['risk']
    A, B = a.p(*p0), a.p(*p1)
    mx, my = (A[0]+B[0])/2, (A[1]+B[1])/2 + bow
    for i in range(n):
        t = (i+.5)/n
        x = (1-t)**2*A[0] + 2*(1-t)*t*mx + t*t*B[0]
        y = (1-t)**2*A[1] + 2*(1-t)*t*my + t*t*B[1]
        s = r*(.7+.6*math.sin(math.pi*t))
        a.add(f'<rect x="{x-s/2:.1f}" y="{y-s/2:.1f}" width="{s:.1f}" height="{s:.1f}" rx="{s*.25:.1f}" '
              f'fill="{col}" fill-opacity="{op}" transform="rotate(45 {x:.1f} {y:.1f})" filter="url(#glowS)"/>')

def tunnel(a, p0, p1, col=None, bow=-120, rw=34):
    """加密隧道：外发光管 + 内芯 + 环箍"""
    col = col or P['brand']
    A, B = a.p(*p0), a.p(*p1)
    mx, my = (A[0]+B[0])/2, (A[1]+B[1])/2 + bow
    d = f"M{A[0]:.1f},{A[1]:.1f} Q{mx:.1f},{my:.1f} {B[0]:.1f},{B[1]:.1f}"
    a.add(f'<path d="{d}" stroke="{col}" stroke-width="{rw*2.3:.1f}" stroke-opacity=".10" fill="none" '
          f'stroke-linecap="round" filter="url(#glowR)"/>')
    a.add(f'<path d="{d}" stroke="{col}" stroke-width="{rw:.1f}" stroke-opacity=".20" fill="none" stroke-linecap="round"/>')
    a.add(f'<path d="{d}" stroke="{col}" stroke-width="{rw:.1f}" stroke-opacity=".55" fill="none" '
          f'stroke-linecap="round" stroke-dasharray="2 26"/>')
    a.add(f'<path d="{d}" stroke="{col}" stroke-width="{rw*.24:.1f}" fill="none" stroke-linecap="round" filter="url(#glowS)"/>')
    for i in range(1, 9):
        t = i/9
        x = (1-t)**2*A[0] + 2*(1-t)*t*mx + t*t*B[0]
        y = (1-t)**2*A[1] + 2*(1-t)*t*my + t*t*B[1]
        a.add(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rw*.30:.1f}" ry="{rw*.56:.1f}" fill="none" '
              f'stroke="{col}" stroke-width="2.4" stroke-opacity=".55"/>')
    return (A, B)

# ---------------- 屏幕空间 UI ----------------
def phone(cx, cy, w=330, tilt=-7, body="#0E1526", bezel="#28324A", inner=""):
    k = (w - 18) / 312.0
    h = 18 + 652 * k
    return f'''<g transform="translate({cx},{cy}) rotate({tilt})">
  <rect x="{-w/2-10}" y="{-h/2-10}" width="{w+20}" height="{h+20}" rx="{w*.16}" fill="#000" opacity=".6" filter="url(#soft)"/>
  <rect x="{-w/2}" y="{-h/2}" width="{w}" height="{h}" rx="{w*.14}" fill="{bezel}"/>
  <rect x="{-w/2+9}" y="{-h/2+9}" width="{w-18}" height="{h-18}" rx="{w*.115}" fill="{body}"/>
  <g transform="translate({-w/2+9},{-h/2+9}) scale({k:.4f})">{inner}</g>
  <rect x="{-w*.10}" y="{-h/2+16}" width="{w*.20}" height="{w*.055}" rx="{w*.028}" fill="#05070E"/>
\u003c/g>'''

def card(x, y, w, h, fill="#121A2C", stroke="#2A344E", r=18, op=1.0, sw=1.6):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" fill-opacity="{op}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>')

def txt(x, y, s, size=26, fill=None, weight=700, anchor="start", ls=0, op=1.0):
    fill = fill or P['ink']
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Noto Sans CJK SC" '
            f'font-weight="{weight}" font-size="{size}" fill="{fill}" fill-opacity="{op}" letter-spacing="{ls}">{s}</text>')
