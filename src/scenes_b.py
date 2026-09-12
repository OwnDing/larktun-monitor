# -*- coding: utf-8 -*-
"""分镜 S08–S14"""
import math, random
from iso import Art, P, shade, W, H, frame_svg
import comp as C
from scenes_a import stars, noisefield, _hut, A, S, OX, OY

def mini(fn, sx, sy, s=70):
    a = Art(s, sx, sy); fn(a); return a.out()

# ============================== S08 ==============================
def s08():
    a = A(118, 505, 790)
    # 家庭防护穹顶
    a.add(f'<ellipse cx="520" cy="760" rx="520" ry="430" fill="{P["brand"]}" opacity=".07" filter="url(#soft)"/>')
    C.room(a, 0, 0, 5.0, 3.8, 2.7, warm=1)
    C.rug(a, .6, 1.5, 2.4, 1.6, "#2E3A57")
    C.sofa(a, .7, 2.55)
    C.table(a, 2.05, 1.35, 1.25, .75, .48)
    C.chair(a, 2.15, .85); C.chair(a, 3.05, .85)
    C.plant(a, 4.55, .55, 1.15)
    C.tv(a, 1.0, .12, 1.5, .82, .52)
    C.shelf(a, 2.75, .10, 1.15, 1.25)
    # 家里的录像机 / NAS
    gx0, gy0 = a.p(3.25, .45, .95)
    a.add(f'<ellipse cx="{gx0:.0f}" cy="{gy0:.0f}" rx="230" ry="170" fill="{P["brand"]}" opacity=".17" filter="url(#soft)"/>')
    C.nvr(a, 2.85, .18, 1.25*2/3+.02, sc=1.25)
    C.nas(a, 3.95, 3.05, 0, sc=1.0)
    C.router(a, 3.15, 3.15, 0, sc=1.0)
    # 三台摄像头 → 录像机（青色，留在屋里）
    hub = (3.28, .50, .96)
    C.cam(a, 4.2, .05, 2.2, led=P['brand'], sc=1.05)
    C.cam(a, .18, 2.35, 2.25, led=P['brand'], sc=1.0)
    C.cam(a, 1.15, .05, 2.3, led=P['brand'], sc=.95)
    for src, bow in (((4.35,.3,2.25), 30), ((.4,2.5,2.25), 110), ((1.3,.3,2.3), 24)):
        C.stream(a, src, hub, P['brand'], 6, bow, .95, glow="glowS")
        C.packets(a, src, hub, P['brand'], bow, 5, 11)
    lp = a.p(3.28, .50, 1.35)
    a.add(f'<line x1="{lp[0]:.0f}" y1="{lp[1]:.0f}" x2="{min(lp[0]+120,682):.0f}" y2="{lp[1]-130:.0f}" stroke="{P["brand"]}" stroke-width="3"/>')
    a.add(f'<rect x="{min(lp[0]+110,672):.0f}" y="{lp[1]-186:.0f}" width="336" height="72" rx="16" fill="{P["bg0"]}" stroke="{P["brand"]}" stroke-width="2"/>')
    a.add(f'<text x="{min(lp[0]+278,840):.0f}" y="{lp[1]-138:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" '
          f'font-weight="800" font-size="34" fill="{P["brand"]}" letter-spacing="1">你家的录像机</text>')
    body = a.out() + f'''
<g>
  <rect x="560" y="292" width="454" height="74" rx="37" fill="{P['brand']}" fill-opacity=".13" stroke="{P['brand']}" stroke-opacity=".55"/>
  <text x="787" y="341" text-anchor="middle" font-family="Noto Sans CJK SC" font-weight="800" font-size="32"
        fill="{P['brand']}" letter-spacing="2">本地录制 · 不出户</text>
</g>'''
    return frame_svg(body, "S08", "0:21–0:24", "3s", "录像\n存回你自己家", "", P['brand'],
                     topnote="镜头：与 S02 同机位同构图（重要！形成 A/B 记忆点）。红流变青流，全部向下汇入家里的录像机")

# ============================== S09 ==============================
def s09():
    random.seed(5)
    bg = noisefield(540, 940, 1120, 620, 240, "#3A4663", .45)
    a = Art(100, 336, 1176)
    C.room(a, 0, 0, 4.2, 3.2, 2.4, warm=1)
    C.sofa(a, .55, 2.05); C.table(a, 1.85, 1.15, 1.0, .62, .44)
    C.tv(a, .85, .12, 1.2, .66, .46)
    C.nvr(a, 2.75, .25, .0, sc=1.0)
    C.cam(a, 3.5, .05, 2.0, led=P['brand'], sc=.95)
    C.stream(a, (3.6,.28,2.05), (3.05,.5,.16), P['brand'], 5, 26, .9, glow="glowS")
    house = a.out()
    # 远端用户
    b = Art(98, 840, 548)
    b.box(-1.3, -1.3, -.34, 2.6, 2.6, .34, "#161F33", edge="#2A344E")
    C.table(b, -.8, -.5, 1.3, .8, .5, "#3A4663")
    C.person_phone(b, .15, .55, 0, .95, "#4C6CC4")
    far = b.out()
    # 隧道
    t = Art(1, 0, 0)
    C.tunnel(t, (330/1, 0, 0), (0,0,0))  # 占位，实际用屏幕坐标
    tun = ""
    A0, B0 = (494, 1006), (840, 664)
    mx, my = (A0[0]+B0[0])/2 + 30, (A0[1]+B0[1])/2 - 236
    d = f"M{A0[0]},{A0[1]} Q{mx:.0f},{my:.0f} {B0[0]},{B0[1]}"
    tun += f'<path d="{d}" stroke="{P["brand"]}" stroke-width="84" stroke-opacity=".09" fill="none" stroke-linecap="round" filter="url(#glowR)"/>'
    tun += f'<path d="{d}" stroke="{P["brand"]}" stroke-width="44" stroke-opacity=".18" fill="none" stroke-linecap="round"/>'
    tun += f'<path d="{d}" stroke="{P["brand"]}" stroke-width="44" stroke-opacity=".5" fill="none" stroke-linecap="round" stroke-dasharray="2 30"/>'
    tun += f'<path d="{d}" stroke="{P["brand"]}" stroke-width="11" fill="none" stroke-linecap="round" filter="url(#glowS)"/>'
    for i in range(1, 10):
        tt = i/10
        x = (1-tt)**2*A0[0] + 2*(1-tt)*tt*mx + tt*tt*B0[0]
        y = (1-tt)**2*A0[1] + 2*(1-tt)*tt*my + tt*tt*B0[1]
        tun += f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="13" ry="25" fill="none" stroke="{P["brand"]}" stroke-width="2.6" stroke-opacity=".6"/>'
    badge = f'''<g transform="translate(660,672)">
  <rect x="-176" y="-42" width="352" height="84" rx="42" fill="{P['bg0']}" stroke="{P['brand']}" stroke-width="2"/>
  <circle cx="-128" cy="0" r="20" fill="{P['brand']}" fill-opacity=".18" stroke="{P['brand']}" stroke-width="2"/>
  <path d="M-136,-2 l6,7 l12,-14" stroke="{P['brand']}" stroke-width="4" fill="none" stroke-linecap="round"/>
  <text x="-92" y="12" font-family="Noto Sans CJK SC" font-weight="800" font-size="34" fill="{P['brand']}" letter-spacing="1">端到端加密</text>
</g>'''
    lbl = f'''<text x="1006" y="1268" text-anchor="end" font-family="Noto Sans CJK SC" font-weight="700" font-size="28"
      fill="{P['dim']}" letter-spacing="8">公 共 互 联 网</text>'''
    return frame_svg(bg + house + far + tun + badge + lbl, "S09", "0:24–0:27", "3s",
                     "云雀通\n只打一条回家的路", "", P['brand'],
                     topnote="镜头：拉远成“两座孤岛”，青色隧道从家中录像机生长出去、穿过灰暗噪点海接到你手上")

# ============================== S10 ==============================
def s10():
    def row(y, name, sub, on=True, sel=False):
        c = P['brand'] if on else P['dim']
        bgc = "#17243B" if sel else "#111A2C"
        st = P['brand'] if sel else "#232E47"
        return (f'<rect x="18" y="{y}" width="276" height="74" rx="16" fill="{bgc}" stroke="{st}" stroke-width="{2 if sel else 1.2}"/>'
                f'<circle cx="50" cy="{y+37}" r="7" fill="{c}"/>'
                + C.txt(76, y+34, name, 24, "#E6ECF7", 800)
                + C.txt(76, y+60, sub, 17, "#7E8CA8", 500)
                + C.txt(278, y+44, "在线" if on else "离线", 18, c, 700, "end"))
    inner = f'''
  <rect width="312" height="652" rx="30" fill="#0A101E"/>
  <rect x="0" y="0" width="312" height="86" fill="#0E1728"/>
  {C.txt(20, 54, "我的设备", 28, "#E6ECF7", 900)}
  <circle cx="286" cy="46" r="6" fill="{P['brand']}"/>
  {row(100, "家里 · 录像机", "192.168.1.20 · NVR", True, True)}
  {row(186, "客厅摄像头", "IPC-01", True)}
  {row(272, "玄关摄像头", "IPC-02", True)}
  <g transform="translate(18,366)">
    <rect width="276" height="196" rx="16" fill="#0D1627" stroke="{P['brand']}" stroke-width="2"/>
    <rect x="10" y="10" width="256" height="144" rx="10" fill="#20293C"/>
    <g transform="translate(10,10)">
      <rect width="256" height="144" rx="10" fill="#2A2016"/>
      <rect y="96" width="256" height="48" fill="#7A5A38"/>
      <rect x="22" y="52" width="92" height="48" rx="8" fill="#47567C"/>
      <rect x="128" y="66" width="62" height="34" rx="6" fill="#8C6844"/>
      <circle cx="212" cy="40" r="20" fill="#FFC65C" opacity=".5"/>
      <circle cx="30" cy="18" r="6" fill="{P['risk']}"/>
      <text x="46" y="24" font-family="Noto Sans CJK SC" font-weight="800" font-size="15" fill="#FFD9D9">LIVE</text>
      <text x="246" y="136" text-anchor="end" font-family="Noto Sans CJK SC" font-weight="600" font-size="14" fill="#E6D3B8">客厅 · 实时</text>
    </g>
    {C.txt(14, 182, "已连接 · 延迟 18ms", 19, P['brand'], 700)}
    {C.txt(262, 182, "点对点", 19, "#7E8CA8", 600, "end")}
  </g>
  {C.txt(156, 604, "无需公网 IP · 无需端口映射", 17, "#5A6784", 600, "center")}
'''
    bg = f'<ellipse cx="540" cy="800" rx="520" ry="560" fill="{P["brand"]}" opacity=".08" filter="url(#soft)"/>'
    ring = "".join(f'<ellipse cx="540" cy="820" rx="{r}" ry="{r*1.25}" fill="none" stroke="{P["brand"]}" stroke-opacity="{o}" stroke-width="2"/>'
                   for r, o in ((250,.20),(330,.12),(410,.07)))
    return frame_svg(bg + ring + C.phone(540, 812, 536, -3, inner=inner), "S10", "0:27–0:30", "3s",
                     "点开，就是家里", "", P['brand'],
                     topnote="镜头：手机 UI 特写。手指点“家里 · 录像机” → 实时画面 0.5s 内铺开（转场用画面从中心展开）")

# ============================== S11 ==============================
def s11():
    def cam_i(a): C.cam(a, 0, 0, 0, led=P['risk'], sc=1.5)
    def cam_i2(a): C.cam(a, 0, 0, 0, led=P['brand'], sc=1.5)
    def tower_i(a):
        a.box(0, 0, 0, 1.0, 1.0, 2.4, "#1A2133", edge="#303C58")
        for i in range(4):
            a.poly([(0,1.002,.3+i*.5),(1,1.002,.3+i*.5),(1,1.002,.45+i*.5),(0,1.002,.45+i*.5)], P['risk'], .45)
    def nvr_i(a): C.nvr(a, 0, 0, 0, sc=1.5)
    def ph_i(a, col):
        a.box(0, 0, 0, .1, .62, 1.2, "#222B3D", edge="#3B4760")
        a.poly([(.102,.06,.08),(.102,.56,.08),(.102,.56,1.12),(.102,.06,1.12)], col, .55)
    def ph_r(a): ph_i(a, P['risk'])
    def ph_b(a): ph_i(a, P['brand'])

    up = (f'<rect x="56" y="330" width="968" height="392" rx="28" fill="{P["risk"]}" fill-opacity=".05" stroke="{P["risk"]}" stroke-opacity=".25"/>'
          + mini(cam_i, 200, 612, 74) + mini(tower_i, 540, 560, 74) + mini(ph_r, 880, 616, 74))
    up += (f'<path d="M232,566 Q380,404 500,520" stroke="{P["risk"]}" stroke-width="7" fill="none" stroke-linecap="round" filter="url(#glowS)"/>'
           f'<path d="M584,520 Q724,404 856,566" stroke="{P["risk"]}" stroke-width="7" fill="none" stroke-linecap="round" filter="url(#glowS)"/>')
    up += (f'<text x="540" y="392" text-anchor="middle" font-family="Noto Sans CJK SC" font-weight="800" font-size="34" '
           f'fill="{P["risk"]}" letter-spacing="3">厂商云 · 画面经手第三方</text>'
           f'<text x="540" y="690" text-anchor="middle" font-family="Noto Sans CJK SC" font-weight="700" font-size="30" '
           f'fill="{P["mute"]}" letter-spacing="2">月月付费 · 回看受限 · 依赖对方在线</text>')

    dn = (f'<rect x="56" y="836" width="968" height="392" rx="28" fill="{P["brand"]}" fill-opacity=".06" stroke="{P["brand"]}" stroke-opacity=".3"/>'
          + mini(cam_i2, 196, 1116, 74) + mini(nvr_i, 404, 1108, 74) + mini(ph_b, 880, 1122, 74))
    dn += f'<path d="M228,1072 Q300,1006 372,1064" stroke="{P["brand"]}" stroke-width="7" fill="none" stroke-linecap="round" filter="url(#glowS)"/>'
    dn += (f'<path d="M500,1058 Q690,952 852,1064" stroke="{P["brand"]}" stroke-width="40" stroke-opacity=".16" fill="none" stroke-linecap="round"/>'
           f'<path d="M500,1058 Q690,952 852,1064" stroke="{P["brand"]}" stroke-width="40" stroke-opacity=".45" fill="none" stroke-linecap="round" stroke-dasharray="2 28"/>'
           f'<path d="M500,1058 Q690,952 852,1064" stroke="{P["brand"]}" stroke-width="9" fill="none" stroke-linecap="round" filter="url(#glowS)"/>')
    dn += (f'<text x="540" y="898" text-anchor="middle" font-family="Noto Sans CJK SC" font-weight="800" font-size="34" '
           f'fill="{P["brand"]}" letter-spacing="3">云雀通 · 端到端直连回家</text>'
           f'<text x="540" y="1196" text-anchor="middle" font-family="Noto Sans CJK SC" font-weight="700" font-size="30" '
           f'fill="{P["mute"]}" letter-spacing="2">零云存储月费 · 想看多久看多久</text>')
    vs = (f'<circle cx="540" cy="780" r="46" fill="{P["bg0"]}" stroke="{P["dim"]}" stroke-width="2"/>'
          f'<text x="540" y="795" text-anchor="middle" font-family="Noto Sans CJK SC" font-weight="900" '
          f'font-size="36" fill="{P["mute"]}">VS</text>')
    return frame_svg(up + dn + vs, "S11", "0:30–0:33", "3s", "同一个画面\n两条完全不同的路", "", P['brand'],
                     topnote="镜头：上下分屏。上路径先走一遍（红），下路径再走一遍（青），下半段明显更短更快")

# ============================== S12 ==============================
def s12():
    a = A(112, 430, 840)
    a.add(f'<ellipse cx="430" cy="900" rx="420" ry="330" fill="{P["gold"]}" opacity=".10" filter="url(#soft)"/>')
    C.room(a, 0, 0, 4.0, 3.2, 2.5, wall="#3A3A46", floor="#6E5238", warm=1)
    C.rug(a, .5, 1.5, 1.9, 1.3, "#3A3352")
    C.crib(a, .45, 1.75)
    C.shelf(a, 2.4, .10, .95, 1.0)
    C.plant(a, 3.6, .5, .95)
    # 夜灯
    gx, gy = a.p(2.9, .5, 1.06)
    a.add(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="16" fill="{P["gold"]}" filter="url(#glowR)"/>')
    a.add(f'<ellipse cx="{gx:.0f}" cy="{gy+40:.0f}" rx="190" ry="130" fill="{P["gold"]}" opacity=".13" filter="url(#soft)"/>')
    C.cam(a, 3.3, .05, 2.05, led=P['brand'], sc=1.0)
    C.nvr(a, 2.5, .25, 1.0*2/3, sc=.9)
    house = a.out()
    # 远端：出差的你
    b = Art(74, 862, 540)
    b.box(-1.1, -1.1, -.3, 2.2, 2.2, .3, "#141C2E", edge="#26314B")
    C.person_phone(b, .1, .35, 0, .9, "#43598F")
    far = b.out()
    d = "M520,900 Q700,600 862,512"
    tun = (f'<path d="{d}" stroke="{P["brand"]}" stroke-width="26" stroke-opacity=".13" fill="none" stroke-linecap="round" filter="url(#glowR)"/>'
           f'<path d="{d}" stroke="{P["brand"]}" stroke-width="5" fill="none" stroke-linecap="round" stroke-dasharray="3 16" filter="url(#glowS)"/>')
    return frame_svg(stars(90, 100, 720, .5) + house + tun + far, "S12", "0:33–0:36", "3s",
                     "画面\n从没离开过你", "", P['brand'],
                     topnote="镜头：夜景，暖黄夜灯 + 冷月光。只有一条细细的青线在家与你之间呼吸式明灭")

# ============================== S13 ==============================
def s13():
    items = [
        ("无需公网 IP", "运营商给你什么网都能用", "ip"),
        ("免端口映射", "不用登路由器，不用 DDNS", "port"),
        ("全平台客户端", "iOS / Android / Win / macOS / Linux", "plat"),
    ]
    out = []
    for i, (t1, t2, kind) in enumerate(items):
        y = 470 + i*300
        out.append(f'<rect x="72" y="{y}" width="936" height="236" rx="30" fill="#101827" stroke="#22304C" stroke-width="2"/>')
        a = Art(58, 232, y+168)
        if kind == "ip":
            a.box(-1.0, -1.0, 0, 2.0, 2.0, .3, "#1B2740", edge="#33415F")
            a.box(-.45, -.45, .3, .9, .9, .9, P['brandDim'], edge=P['brand'])
            cx, cy = a.p(0, 0, 1.5)
            out.append(a.out() + f'<text x="{cx:.0f}" y="{cy+4:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" '
                                 f'font-weight="900" font-size="30" fill="{P["brand"]}">IP</text>')
        elif kind == "port":
            a.box(-1.0, -1.0, 0, 2.0, 2.0, .3, "#1B2740", edge="#33415F")
            C.router(a, -.5, -.4, .3, sc=1.7)
            cx, cy = a.p(0, 0, 1.5)
            out.append(a.out() + f'<g transform="translate({cx:.0f},{cy-6:.0f})">'
                                 f'<circle r="26" fill="none" stroke="{P["brand"]}" stroke-width="5"/>'
                                 f'<line x1="-18" y1="18" x2="18" y2="-18" stroke="{P["brand"]}" stroke-width="5" stroke-linecap="round"/></g>')
        else:
            a.box(-1.0, -1.0, 0, 2.0, 2.0, .3, "#1B2740", edge="#33415F")
            a.box(-.75, -.2, .3, 1.5, .1, .9, "#28344E", edge=P['brand'])
            a.box(-.1, .25, .3, .1, .5, .55, "#28344E", edge=P['brand'])
            out.append(a.out())
        out.append(f'<text x="420" y="{y+108}" font-family="Noto Sans CJK SC" font-weight="900" font-size="52" '
                   f'fill="{P["ink"]}" letter-spacing="1">{t1}</text>')
        out.append(f'<text x="420" y="{y+164}" font-family="Noto Sans CJK SC" font-weight="500" font-size="30" '
                   f'fill="{P["mute"]}" letter-spacing="1">{t2}</text>')
    head = (f'<text x="540" y="368" text-anchor="middle" font-family="Noto Sans CJK SC" font-weight="700" '
            f'font-size="34" fill="{P["brand"]}" letter-spacing="10">装 完 就 能 用</text>')
    return frame_svg(head + "".join(out), "S13", "0:36–0:38", "2s", "", "", P['brand'],
                     topnote="镜头：三张卡片自下而上依次弹入（每张间隔 6 帧），配合“咔哒”音效")

# ============================== S14 ==============================
def s14():
    d = "M120,1180 Q540,640 960,1180"
    tun = (f'<path d="{d}" stroke="{P["brand"]}" stroke-width="120" stroke-opacity=".05" fill="none" stroke-linecap="round" filter="url(#glowR)"/>'
           f'<path d="{d}" stroke="{P["brand"]}" stroke-width="3" stroke-opacity=".35" fill="none" stroke-dasharray="4 22"/>')
    bird = f'''<g transform="translate(540,626)">
  <circle r="176" fill="{P['brand']}" fill-opacity=".06"/>
  <circle r="176" fill="none" stroke="{P['brand']}" stroke-opacity=".26" stroke-width="2"/>
  <circle r="224" fill="none" stroke="{P['brand']}" stroke-opacity=".09" stroke-width="1.5"/>
  <g filter="url(#glowS)" transform="translate(-6,16) scale(1.06)">
    <path d="M-96,36 L-140,8 L-106,2 Z" fill="{P['brandDim']}"/>
    <path d="M-96,36 C-52,22 -18,4 20,-22 C42,-38 58,-42 76,-40 L100,-33 L76,-23
             C60,-15 48,-3 34,15 C10,45 -48,54 -96,36 Z" fill="{P['brand']}"/>
    <path d="M4,-8 C-14,-44 -18,-76 -6,-106 C22,-74 46,-44 54,-13 C38,-5 18,-3 4,-8 Z"
          fill="#8FF6E7"/>
    <path d="M4,-8 C-8,-38 -12,-66 -6,-106 C6,-70 14,-38 20,-12 Z" fill="{P['brand2']}" opacity=".85"/>
    <circle cx="72" cy="-31" r="7" fill="{P['bg0']}"/>
  </g>
</g>'''
    txt = f'''
<text x="540" y="906" text-anchor="middle" font-family="Noto Sans CJK SC" font-weight="900"
      font-size="106" fill="{P['ink']}" letter-spacing="4">云雀通 Larktun</text>
<text x="540" y="984" text-anchor="middle" font-family="Noto Sans CJK SC" font-weight="600"
      font-size="42" fill="{P['brand']}" letter-spacing="12">把回家的路，握在自己手里</text>
<g transform="translate(540,1108)">
  <rect x="-300" y="-42" width="600" height="84" rx="42" fill="{P['bg1']}" stroke="#28354F"/>
  <text x="0" y="12" text-anchor="middle" font-family="Noto Sans CJK SC" font-weight="700"
        font-size="34" fill="{P['mute']}" letter-spacing="3">docs.larktun.com</text>
</g>
<text x="540" y="1252" text-anchor="middle" font-family="Noto Sans CJK SC" font-weight="500"
      font-size="27" fill="{P['dim']}" letter-spacing="3">零信任组网 · 远程访问 NAS / 录像机 / 内网服务</text>'''
    return frame_svg(stars(60, 120, 560, .4) + tun + bird + txt, "S14", "0:38–0:40", "2s", "", "", P['brand'],
                     topnote="镜头：隧道汇聚成雀鸟标志，Logo 定格 1.2s 后字幕淡入（留 0.5s 黑场收尾）")
