# -*- coding: utf-8 -*-
"""分镜 S01–S07"""
import math, random
from iso import Art, P, shade, W, H, frame_svg
import comp as C

random.seed(7)
S, OX, OY = 112, 520, 700

def A(s=S, ox=OX, oy=OY): return Art(s, ox, oy)

def stars(n=70, y0=120, y1=760, op=.55):
    o=[]
    for _ in range(n):
        x=random.uniform(0,W); y=random.uniform(y0,y1); r=random.uniform(.8,2.6)
        o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#CFE0FF" opacity="{random.uniform(.15,op):.2f}"/>')
    return "".join(o)

def noisefield(cx, cy, w, h, n=150, col="#43506E", op=.5):
    o=[f'<g opacity="{op}">']
    for _ in range(n):
        x=cx+random.uniform(-w/2,w/2); y=cy+random.uniform(-h/2,h/2)
        o.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{random.uniform(2,7):.1f}" height="2.4" fill="{col}" opacity="{random.uniform(.2,.9):.2f}"/>')
    o.append('</g>'); return "".join(o)

# ============================== S01 ==============================
def s01():
    a = A(165, 330, 776)
    a.add(f'<ellipse cx="700" cy="700" rx="640" ry="560" fill="{P["bg2"]}" opacity=".45" filter="url(#soft)"/>')
    C.room(a, 0, 0, 3.6, 2.8, 2.6, wall="#232833", floor="#2E241A", win=True)
    a.add(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#05070E" opacity=".58"/>')
    C.sofa(a, .30, 1.75)
    C.table(a, 1.62, 1.60, .9, .55)
    C.person(a, .95, 1.45, 0, .60, "#262E3F")
    C.person(a, 1.48, 1.45, 0, .56, "#262E3F")
    C.plant(a, 3.30, 2.35, .9)
    a.add(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#05070E" opacity=".42"/>')
    C.cam_cone(a, 2.82, .24, 2.30, P['risk'], .09, 3.6, 1.6)
    C.cam(a, 2.58, .05, 2.12, sc=2.6)
    b = .22*2.6
    px, py = a.p(2.60+b*.2, .05+b*1.3, 2.15+b*.72)
    for r, o, sw in ((60,.42,4),(104,.24,3.2),(158,.13,2.6),(224,.07,2.2)):
        a.add(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{r}" fill="none" stroke="{P["risk"]}" stroke-opacity="{o}" stroke-width="{sw}"/>')
    a.add(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="150" fill="{P["risk"]}" opacity=".10" filter="url(#soft)"/>')
    body = a.out() + f"""
<g transform="translate({px+118:.0f},{py-92:.0f})">
  <rect x="0" y="-44" width="284" height="76" rx="38" fill="{P['bg0']}" stroke="{P['risk']}" stroke-width="2"/>
  <circle cx="44" cy="-6" r="11" fill="{P['risk']}" filter="url(#glowS)"/>
  <text x="76" y="8" font-family="Noto Sans CJK SC" font-weight="800" font-size="34"
        fill="{P['risk']}" letter-spacing="3">REC 24h</text>
</g>"""
    return frame_svg(body, "S01", "0:00\u20130:03", "3s", "你家客厅的画面", "", P['risk'],
                     topnote="镜头：全黑中只有一颗红点呼吸 \u2192 缓慢 dolly-out 露出客厅（焦点由浅到深，画面始终压暗）")

# ============================== S02 ==============================
def s02():
    a = A(128, 512, 760)
    C.room(a, 0, 0, 5.0, 3.8, 2.7)
    C.rug(a, .6, 1.5, 2.4, 1.6, "#2E3A57")
    C.sofa(a, .7, 2.55)
    C.table(a, 2.05, 1.35, 1.25, .75, .48)
    C.chair(a, 2.15, .85); C.chair(a, 3.05, .85)
    C.plant(a, 4.55, .55, 1.15)
    C.tv(a, 1.0, .12, 1.5, .82, .52)
    C.person(a, 2.35, 1.05, 0, .92, "#5C7BD6")
    C.person(a, 3.15, 1.05, 0, .88, "#C4676B")
    C.person(a, 2.75, 2.25, 0, .70, "#E0B45C")
    C.cam_cone(a, 4.32, .2, 2.32, P['cool'], .13, 3.6, 1.5)
    C.cam(a, 4.2, .05, 2.2, sc=1.15)
    # 红色数据外流：穿出屋顶
    p0 = (4.35, .3, 2.3)
    C.stream(a, p0, (2.6, -3.4, 7.2), P['risk'], 12, -80, 1, glow="glowR")
    C.packets(a, p0, (2.6, -3.4, 7.2), P['risk'], -80, 8, 20)
    body = stars(40, 110, 480, .40) + a.out() + f'''
<g opacity=".95">
  <rect x="612" y="300" width="392" height="72" rx="36" fill="{P['risk']}" fill-opacity=".13" stroke="{P['risk']}" stroke-opacity=".55"/>
  <text x="808" y="348" text-anchor="middle" font-family="Noto Sans CJK SC" font-weight="800" font-size="32"
        fill="{P['risk']}" letter-spacing="2">上传中 · 1080P 24h</text>
</g>'''
    return frame_svg(body, "S02", "0:03–0:06", "3s", "每一秒\n都在离开你家", "", P['risk'],
                     topnote="镜头：固定机位，红色数据流从镜头射出、穿过天花板出画（粒子沿路径流动）")

# ============================== S03 ==============================
def _hut(a, x, y, sc=1.0, col="#2C3550", lit="#FFB65C"):
    w, d, h = .9*sc, .8*sc, .55*sc
    a.box(x, y, 0, w, d, h, col)
    a.poly([(x,y,h),(x+w,y,h),(x+w/2,y+d/2,h+.42*sc)], shade(col,1.25))
    a.poly([(x,y,h),(x,y+d,h),(x+w/2,y+d/2,h+.42*sc)], shade(col,1.05))
    a.poly([(x,y+d,h),(x+w,y+d,h),(x+w/2,y+d/2,h+.42*sc)], shade(col,.85))
    a.poly([(x+w*.28,y+d+.002,h*.28),(x+w*.62,y+d+.002,h*.28),(x+w*.62,y+d+.002,h*.62),(x+w*.28,y+d+.002,h*.62)], lit, .85)

def s03():
    a = A(68, 560, 1096)
    for i in range(-11, 12):
        p0, p1 = a.p(i*1.4, -15, 0), a.p(i*1.4, 15, 0)
        a.add(f'<line x1="{p0[0]:.0f}" y1="{p0[1]:.0f}" x2="{p1[0]:.0f}" y2="{p1[1]:.0f}" stroke="{P["bg3"]}" stroke-opacity=".30" stroke-width="1"/>')
        p0, p1 = a.p(-15, i*1.4, 0), a.p(15, i*1.4, 0)
        a.add(f'<line x1="{p0[0]:.0f}" y1="{p0[1]:.0f}" x2="{p1[0]:.0f}" y2="{p1[1]:.0f}" stroke="{P["bg3"]}" stroke-opacity=".30" stroke-width="1"/>')
    tx, ty, TS = -3.2, -6.4, 3.4
    cxx, cyy = a.p(tx+TS/2, ty+TS/2, 0)
    a.add(f'<ellipse cx="{cxx:.0f}" cy="{cyy:.0f}" rx="360" ry="170" fill="{P["risk"]}" opacity=".12" filter="url(#soft)"/>')
    a.box(tx, ty, 0, TS, TS, 7.4, "#19203200"[:7], edge="#2E3A56")
    for i in range(6):
        z = .9 + i*1.12
        a.poly([(tx,ty+TS+.004,z),(tx+TS,ty+TS+.004,z),(tx+TS,ty+TS+.004,z+.22),(tx,ty+TS+.004,z+.22)], P['risk'], .42)
        a.poly([(tx+TS+.004,ty,z),(tx+TS+.004,ty+TS,z),(tx+TS+.004,ty+TS,z+.22),(tx+TS+.004,ty,z+.22)], P['risk'], .22)
    a.box(tx+.55, ty+.55, 7.4, TS-1.1, TS-1.1, .55, "#242D44")
    tip = (tx+TS/2, ty+TS/2, 7.9)
    tp = a.p(*tip)
    a.add(f'<circle cx="{tp[0]:.0f}" cy="{tp[1]:.0f}" r="150" fill="{P["risk"]}" opacity=".13" filter="url(#soft)"/>')
    hs = [(5.4,-.6,1.30,-320),(2.0,-2.6,1.10,-250),(-1.0,-4.0,0.95,-170),(3.2,2.0,1.25,-430),
          (-4.6,-1.6,1.00,-150),(0.6,2.0,1.15,-330),(6.4,2.2,1.05,-480),(-3.2,1.4,0.95,-250)]
    for hx, hy, sc, bow in hs:
        _hut(a, hx, hy, sc)
        C.stream(a, (hx+.45*sc, hy+.4*sc, .95*sc), tip, P['risk'], 4.2*sc, bow, .78, glow="glowS")
    tt = a.p(tx+TS/2, ty+TS/2, 8.35)
    body = stars(80, 100, 620, .45) + a.out() + f"""
<g transform="translate({tt[0]:.0f},{tt[1]-54:.0f})">
  <rect x="-214" y="-44" width="428" height="80" rx="40" fill="{P['bg0']}" stroke="{P['risk']}" stroke-width="2"/>
  <text x="0" y="10" text-anchor="middle" font-family="Noto Sans CJK SC" font-weight="800"
        font-size="36" fill="{P['risk']}" letter-spacing="4">某处机房 · 不是你家</text>
</g>"""
    return frame_svg(body, "S03", "0:06\u20130:09", "3s", "最后存在\n谁的硬盘上？", "", P['risk'],
                     topnote="镜头：继续升高成俯瞰，数十户人家的红流拖着尾迹汇聚到一座无品牌机房塔（慢速环绕）")

# ============================== S04 ==============================
def s04():
    a = A(104, 520, 640)
    a.add(f'<ellipse cx="540" cy="900" rx="700" ry="420" fill="{P["brand2"]}" opacity=".07" filter="url(#soft)"/>')
    for r in range(3):                    # 三排机柜，由远及近
        y = r*2.3
        for cnum in range(4):
            x = cnum*1.25 - .6
            a.box(x, y, 0, 1.0, 1.0, 3.0, "#1B2334", edge="#2B3752")
            for k in range(7):            # 每格一块小屏（+y 立面）
                z = .18+k*.38
                warm = (r*4+cnum+k) % 5 == 0
                col = "#F0B270" if warm else "#2E6C9E"
                a.poly([(x+.12,y+1.0+.004,z),(x+.88,y+1.0+.004,z),(x+.88,y+1.0+.004,z+.26),(x+.12,y+1.0+.004,z+.26)],
                       col, .75 if warm else .40)
    # 高亮“你家”那一格
    hx, hy, hz = -0.6+1.25*2, 2*2.3, .18+4*.38
    a.poly([(hx+.12,hy+1.0+.02,hz),(hx+.88,hy+1.0+.02,hz),(hx+.88,hy+1.0+.02,hz+.26),(hx+.12,hy+1.0+.02,hz+.26)],
           "#FFD9A8", .95)
    a.poly([(hx+.06,hy+1.0+.03,hz-.05),(hx+.94,hy+1.0+.03,hz-.05),(hx+.94,hy+1.0+.03,hz+.31),(hx+.06,hy+1.0+.03,hz+.31)],
           "none", stroke=P['risk'], sw=4)
    lx, ly = a.p(hx+.5, hy+1.0+.03, hz+.55)
    a.add(f'<line x1="{lx:.0f}" y1="{ly:.0f}" x2="{lx+150:.0f}" y2="{ly-170:.0f}" stroke="{P["risk"]}" stroke-width="3"/>')
    a.add(f'<rect x="{lx+140:.0f}" y="{ly-232:.0f}" width="300" height="76" rx="16" fill="{P["risk"]}" fill-opacity=".16" stroke="{P["risk"]}"/>')
    a.add(f'<text x="{lx+290:.0f}" y="{ly-182:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" '
          f'font-weight="800" font-size="36" fill="#FFB9B9" letter-spacing="2">你家 · 客厅</text>')
    body = a.out()
    return frame_svg(body, "S04", "0:09–0:12", "3s", "别人的机房里\n有一格是你家", "", P['risk'],
                     topnote="镜头：穿行于机柜之间（camera dolly-in），每一格小屏都在播放一户人家的画面")

# ============================== S05 ==============================
def s05():
    random.seed(3)
    bg = f'<rect width="{W}" height="{H}" fill="{P["bg0"]}" opacity=".45"/>' + noisefield(540, 780, 1000, 900, 120, "#2B344E", .35)
    inner = f'''
  <rect width="312" height="652" rx="30" fill="#0B1120"/>
  <rect x="0" y="0" width="312" height="92" fill="#111A2C"/>
  {C.txt(24, 58, "云录像回看", 28, "#E6ECF7", 800)}
  <g opacity=".35">
    <rect x="22" y="112" width="268" height="150" rx="12" fill="#1B2438"/>
    <path d="M40,240 L84,196 L120,222 L172,164 L214,200 L272,150" stroke="#3A4A6B" stroke-width="3" fill="none"/>
    <rect x="22" y="276" width="268" height="16" rx="8" fill="#1B2438"/>
    <rect x="22" y="276" width="70" height="16" rx="8" fill="#33405C"/>
    {C.txt(22, 322, "09-11  14:20", 18, "#4E5C7A", 600)}
    {C.txt(290, 322, "已过期", 18, "#4E5C7A", 600, "end")}
  </g>
  <g>
    <rect x="0" y="120" width="312" height="200" fill="#0B1120" opacity=".72"/>
    <g transform="translate(156,196)">
      <rect x="-30" y="-16" width="60" height="46" rx="10" fill="none" stroke="{P['risk']}" stroke-width="4"/>
      <path d="M-16,-16 v-14 a16,16 0 0 1 32,0 v14" fill="none" stroke="{P['risk']}" stroke-width="4"/>
      <circle cx="0" cy="6" r="5" fill="{P['risk']}"/>
    </g>
    {C.txt(156, 268, "该时段录像已加密存储", 21, "#93A1BC", 600, "center")}
  </g>
  <rect x="22" y="372" width="268" height="122" rx="16" fill="#161F33" stroke="#2A344E" stroke-width="1.5"/>
  {C.txt(44, 416, "7 天云录像", 26, "#E6ECF7", 800)}
  {C.txt(44, 456, "解锁历史回看 / 事件标记", 18, "#7E8CA8", 500)}
  {C.txt(288, 440, "¥ XX /月", 30, P['risk'], 900, "end")}
  <rect x="22" y="516" width="268" height="60" rx="30" fill="{P['risk']}"/>
  {C.txt(156, 556, "立即开通", 27, "#12070A", 900, "center")}
  {C.txt(156, 616, "取消订阅后历史录像将不可查看", 16, "#5A6784", 500, "center")}
'''
    ph = C.phone(540, 806, 536, -4, inner=inner)
    finger = f'''<g transform="translate(796,1262) rotate(-30)">
  <path d="M0,0 q22,-26 46,-10 q26,-14 44,8 q28,-6 34,22 l8,52 q6,44 -34,60 l-54,20 q-36,10 -54,-22 L-8,84 q-14,-26 12,-38 z"
        fill="#E9C39B" stroke="#C79B72" stroke-width="3"/>
</g>
<g opacity=".9">
  <circle cx="556" cy="1176" r="60" fill="none" stroke="{P['risk']}" stroke-width="4" opacity=".7"/>
  <circle cx="556" cy="1176" r="104" fill="none" stroke="{P['risk']}" stroke-width="3" opacity=".38"/>
  <circle cx="556" cy="1176" r="150" fill="none" stroke="{P['risk']}" stroke-width="2.4" opacity=".18"/>
</g>'''
    return frame_svg(bg + ph + finger, "S05", "0:12–0:15", "3s", "想回看昨天？\n先交月费", "", P['risk'],
                     topnote="镜头：手机屏怼脸特写，时间轴被锁 → 弹出付费墙，手指点击被弹回（UI 元素做轻微 Z 轴层次）")

# ============================== S06 ==============================
def s06():
    a = A(82, 286, 1130)
    a.box(-1.6, -2.4, -.40, 10.4, 4.6, .40, "#131B2C", edge="#26314B")
    for i in range(12):
        x = i*.74
        n = i + 1
        for k in range(n):
            a.box(x, 1.05, .22*k, .62, .62, .22, P['gold'] if k % 2 == 0 else shade(P['gold'], .86))
        tp = a.p(x+.31, 1.36, 0)
        a.add(f'<text x="{tp[0]:.0f}" y="{tp[1]+34:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" '
              f'font-weight="700" font-size="20" fill="{P["dim"]}">{n}月</text>')
    for i in range(3):
        C.cam(a, -1.15, -2.10+i*1.20, .0, sc=1.85)
    lp = a.p(-.55, .05, 1.55)
    a.add(f'<text x="{lp[0]:.0f}" y="{lp[1]:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" '
          f'font-weight="900" font-size="66" fill="{P["risk"]}" letter-spacing="1">×3 台</text>')
    top = a.p(11*.74+.31, 1.36, 12*.22)
    body = a.out() + f"""
<g>
  <line x1="{top[0]:.0f}" y1="{top[1]-30:.0f}" x2="{min(top[0]+120,980):.0f}" y2="{top[1]-150:.0f}" stroke="{P['gold']}" stroke-width="3"/>
  <text x="{min(top[0]+130,900):.0f}" y="{top[1]-166:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC"
        font-weight="900" font-size="66" fill="{P['gold']}" letter-spacing="1">×12 个月</text>
  <text x="{min(top[0]+130,900):.0f}" y="{top[1]-112:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC"
        font-weight="700" font-size="30" fill="{P['mute']}" letter-spacing="3">年年交，一直交</text>
</g>"""
    return frame_svg(body, "S06", "0:15\u20130:18", "3s", "×3 台摄像头", "云 存 储 月 费", P['gold'],
                     topnote="镜头：低角度侧推，金币柱按月份一根根叠高（每根间隔 3 帧 + 轻微 Q 弹），红色摄像头在前景压阵")

# ============================== S07 ==============================
def s07():
    a = A(132, 540, 1330)
    a.add(f'<ellipse cx="540" cy="1150" rx="620" ry="320" fill="{P["brand"]}" opacity=".09" filter="url(#soft)"/>')
    _hut(a, -1.5, -1.35, 3.0, "#3B4C75", "#FFC061")
    C.cam(a, .70, -1.55, 1.78, led=P['brand'], sc=2.0)
    px, py = a.p(.95, -1.15, 1.98)
    cx, cy = 566, 660
    a.add(f'<path d="M{px:.0f},{py:.0f} Q{px-40:.0f},{(py+cy)/2:.0f} {cx:.0f},{cy:.0f}" '
          f'stroke="{P["risk"]}" stroke-width="13" fill="none" stroke-linecap="round" filter="url(#glowS)"/>')
    a.add(f'<path d="M{cx:.0f},{cy:.0f} C{cx+40:.0f},{cy-150:.0f} {cx+30:.0f},{cy-260:.0f} {cx+120:.0f},{cy-430:.0f}" '
          f'stroke="{P["risk"]}" stroke-width="12" stroke-opacity=".22" fill="none" stroke-linecap="round" stroke-dasharray="14 22"/>')
    a.add(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="32" fill="{P["brand"]}" filter="url(#glowR)"/>')
    for r, o, sw in ((90,.62,8),(158,.34,5.5),(236,.17,4),(324,.08,3)):
        a.add(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r}" fill="none" stroke="{P["brand"]}" stroke-opacity="{o}" stroke-width="{sw}"/>')
    random.seed(11)
    for _ in range(32):
        ang = random.uniform(-2.7, -.4); d = random.uniform(80, 420)
        x, y = cx+math.cos(ang)*d, cy+math.sin(ang)*d*.92
        s = random.uniform(9, 22)
        a.add(f'<rect x="{x:.0f}" y="{y:.0f}" width="{s:.0f}" height="{s:.0f}" rx="3" fill="{P["risk"]}" '
              f'opacity="{random.uniform(.10,.55):.2f}" transform="rotate({random.uniform(0,90):.0f} {x:.0f} {y:.0f})"/>')
    body = stars(50, 120, 560, .35) + a.out()
    return frame_svg(body, "S07", "0:18\u20130:21", "3s", "可它\n本来就不用出门", "转 折", P['brand'],
                     topnote="镜头：硬切 + 声音留白。青色脉冲炸开截断红流，上半段碎裂消散（0.2s 完成，冲击感来自骤停）")
