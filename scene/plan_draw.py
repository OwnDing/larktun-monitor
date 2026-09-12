# -*- coding: utf-8 -*-
"""平面布置图绘制 —— 输出 SVG / PNG"""
import math, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import layout_data as L

S   = 100                      # px / m
OX, OY = 172, 254              # 画布内 (x=-0.24, y=-1.42) 的位置
W, H = 1980, 1520
def px(x): return OX + (x + 0.24) * S
def py(y): return OY + (y + 1.42) * S

C = dict(
 bg="#F6F4EF", paper="#FFFFFF",
 wallE="#20252E", wallI="#39404E", rail="#98A1B0",
 beam="#B9C0CB",
 furn="#59627340", furnL="#5A6373", furnF="#FFFFFF",
 ink="#171C25", ink2="#5C6675", ink3="#96A0AF",
 dim="#9AA4B2",
 cam="#D6323A", camF="#D6323A",
 dev="#0C8C7E",
 film="#2159C7",
 tint=dict(live="#FFF4E4", rest="#F1EEFA", wet="#E6F2F6", work="#EDF4EA", util="#F1F0EC"),
)
E=[]
def a(s): E.append(s)
def T(x,y,s,size=15,fill=None,w=500,anc="middle",ls=0,fam="Noto Sans CJK SC",op=1):
    a(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anc}" font-family="{fam}" font-weight="{w}" '
      f'font-size="{size}" fill="{fill or C["ink"]}" fill-opacity="{op}" letter-spacing="{ls}">{s}</text>')
def R(x,y,w,h,fill="none",stroke="none",sw=1,rx=0,op=1,extra=""):
    a(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" '
      f'fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')
def Rm(x0,y0,x1,y1,**k):  # 米坐标矩形
    R(px(x0),py(y0),(x1-x0)*S,(y1-y0)*S,**k)
def Ln(x1,y1,x2,y2,stroke=None,sw=1,dash=None,cap="butt",op=1):
    d=f'stroke-dasharray="{dash}"' if dash else ""
    a(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke or C["ink2"]}" '
      f'stroke-width="{sw}" stroke-opacity="{op}" stroke-linecap="{cap}" {d}/>')
def Lm(x1,y1,x2,y2,**k): Ln(px(x1),py(y1),px(x2),py(y2),**k)

# ───────────────────────── 开口（门 + 窗）归一化 ─────────────────────────
OPEN=[]
for nm,x,y,w,o,sw,tp in L.DOORS:   OPEN.append((x,y,w,o,tp,sw,nm))
for nm,x,y,w,o,tp in L.WINDOWS:    OPEN.append((x,y,w,o,tp,"-",nm))

def wall_pieces(kind,x0,y0,x1,y1):
    horiz = (x1-x0) >= (y1-y0)
    cuts=[]
    for (ox,oy,ow,o,tp,sw,nm) in OPEN:
        if horiz and o=="h" and (y0-0.03) <= oy <= (y1+0.03) and ox >= x0-0.03 and ox+ow <= x1+0.03:
            cuts.append((ox,ox+ow))
        if (not horiz) and o=="v" and (x0-0.03) <= ox <= (x1+0.03) and oy >= y0-0.03 and oy+ow <= y1+0.03:
            cuts.append((oy,oy+ow))
    cuts.sort()
    lo,hi = (x0,x1) if horiz else (y0,y1)
    segs=[]; c=lo
    for s,e in cuts:
        if s>c: segs.append((c,s))
        c=max(c,e)
    if c<hi: segs.append((c,hi))
    return [((s,y0,e,y1) if horiz else (x0,s,x1,e)) for s,e in segs]

# ───────────────────────── 家具符号 ─────────────────────────
def furn(kind,x0,y0,dx,dy):
    X,Y,Wd,Ht = px(x0),py(y0),dx*S,dy*S
    st=C["furnL"]
    def box(rx=2,fill=C["furnF"],sw=1.4): R(X,Y,Wd,Ht,fill=fill,stroke=st,sw=sw,rx=rx)
    cx,cy=X+Wd/2,Y+Ht/2
    if kind in ("box","counter","cabinet","shelf","wardrobe","nightstand","bench","desk","table","fridge","sofabed"):
        box()
        if kind=="counter":
            for i in range(1,max(2,int(max(dx,dy)/0.6))):
                if dx>=dy: Ln(X+Wd*i/max(2,int(dx/0.6)),Y,X+Wd*i/max(2,int(dx/0.6)),Y+Ht,st,.8,op=.5)
                else: Ln(X,Y+Ht*i/max(2,int(dy/0.6)),X+Wd,Y+Ht*i/max(2,int(dy/0.6)),st,.8,op=.5)
        if kind in ("wardrobe","shelf","cabinet"):
            if dx>=dy: Ln(X,Y+Ht*.72,X+Wd,Y+Ht*.72,st,.8,op=.45)
            else: Ln(X+Wd*.72,Y,X+Wd*.72,Y+Ht,st,.8,op=.45)
        if kind=="fridge": Ln(X,Y+Ht/2,X+Wd,Y+Ht/2,st,1,op=.6)
        if kind=="sofabed":
            R(X+3,Y+3,Wd-6,Ht-6,fill="none",stroke=st,sw=.8,rx=3,op=.5)
        if kind=="desk": Ln(X+2,Y+Ht-6,X+Wd-2,Y+Ht-6,st,.8,op=.4)
    elif kind=="upper":
        R(X,Y,Wd,Ht,fill="none",stroke=st,sw=1,rx=0,extra='stroke-dasharray="5 4" stroke-opacity=".55"')
    elif kind=="sofa":
        box(rx=5)
        if dy>=dx:  # 靠西墙，朝东
            R(X,Y,Wd*.28,Ht,fill="#EDEFF3",stroke=st,sw=1,rx=4)
            for i in (1,2): Ln(X+Wd*.28,Y+Ht*i/3,X+Wd,Y+Ht*i/3,st,.9,op=.5)
        else:
            R(X,Y,Wd,Ht*.28,fill="#EDEFF3",stroke=st,sw=1,rx=4)
            for i in (1,2): Ln(X+Wd*i/3,Y+Ht*.28,X+Wd*i/3,Y+Ht,st,.9,op=.5)
    elif kind=="armchair":
        box(rx=6); R(X+Wd*.06,Y+Ht*.06,Wd*.88,Ht*.88,fill="none",stroke=st,sw=.9,rx=5,op=.5)
    elif kind=="chair":
        box(rx=4); Ln(X+2,Y+Ht*.22,X+Wd-2,Y+Ht*.22,st,1,op=.5)
    elif kind=="bed":
        box(rx=3)
        Ln(X,Y+Ht*.26,X+Wd,Y+Ht*.26,st,1.1,op=.65)              # 枕头线
        R(X+Wd*.08,Y+Ht*.05,Wd*.36,Ht*.17,fill="#EDEFF3",stroke=st,sw=.9,rx=3)
        if dx>1.5*S/S: R(X+Wd*.56,Y+Ht*.05,Wd*.36,Ht*.17,fill="#EDEFF3",stroke=st,sw=.9,rx=3)
        R(X+3,Y+Ht*.30,Wd-6,Ht*.66,fill="none",stroke=st,sw=.8,rx=3,op=.45)
    elif kind=="rug":
        R(X,Y,Wd,Ht,fill="#EFEAE1",stroke=st,sw=1,rx=2,op=.75,extra='stroke-dasharray="6 5" stroke-opacity=".5"')
    elif kind=="tv":
        R(X,Y,max(Wd,4),Ht,fill="#2B313C",stroke="none",rx=1)
    elif kind=="sink":
        box(rx=3)
        a(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{min(Wd,Ht)*.30:.1f}" ry="{min(Wd,Ht)*.24:.1f}" fill="none" stroke="{st}" stroke-width="1.1"/>')
    elif kind=="stove":
        box(rx=3)
        for fx,fy in ((.3,.32),(.7,.32),(.3,.72),(.7,.72)):
            a(f'<circle cx="{X+Wd*fx:.1f}" cy="{Y+Ht*fy:.1f}" r="{min(Wd,Ht)*.13:.1f}" fill="none" stroke="{st}" stroke-width="1.1"/>')
    elif kind=="toilet":
        a(f'<rect x="{X:.1f}" y="{Y:.1f}" width="{Wd:.1f}" height="{Ht*.32:.1f}" rx="3" fill="{C["furnF"]}" stroke="{st}" stroke-width="1.3"/>')
        a(f'<ellipse cx="{cx:.1f}" cy="{Y+Ht*.63:.1f}" rx="{Wd*.44:.1f}" ry="{Ht*.32:.1f}" fill="{C["furnF"]}" stroke="{st}" stroke-width="1.3"/>')
    elif kind=="shower":
        box(rx=2)
        Ln(X,Y,X+Wd,Y+Ht,st,.9,op=.35); Ln(X+Wd,Y,X,Y+Ht,st,.9,op=.35)
        a(f'<circle cx="{X+Wd*.82:.1f}" cy="{Y+Ht*.18:.1f}" r="{min(Wd,Ht)*.11:.1f}" fill="none" stroke="{st}" stroke-width="1.2"/>')
    elif kind=="plant":
        a(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{min(Wd,Ht)*.48:.1f}" fill="#E7EFE4" stroke="#7C9C7A" stroke-width="1.2"/>')
        for k in range(6):
            an=k*60*math.pi/180
            Ln(cx,cy,cx+math.cos(an)*min(Wd,Ht)*.42,cy+math.sin(an)*min(Wd,Ht)*.42,"#7C9C7A",1,op=.7)
    elif kind=="lamp":
        a(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{min(Wd,Ht)*.46:.1f}" fill="none" stroke="{st}" stroke-width="1.1" stroke-dasharray="4 3"/>')
        a(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{min(Wd,Ht)*.16:.1f}" fill="{st}" fill-opacity=".45"/>')
    elif kind=="mirror":
        R(X,Y,max(Wd,3),Ht,fill="#CFE0E8",stroke=st,sw=1)
    elif kind=="rail":
        Ln(X,Y+Ht/2,X+Wd,Y+Ht/2,st,2,dash="2 5")
    else:
        box()

# ───────────────────────── 绘制开始 ─────────────────────────
R(0,0,W,H,fill=C["bg"])
# 图纸边框
R(40,40,W-80,H-80,fill="none",stroke="#DCD8D0",sw=1.5)

# 房间底色
for rid,name,x0,y0,x1,y1,tint in L.ROOMS:
    Rm(x0,y0,x1,y1,fill=C["tint"][tint])
# 阳台地面纹理
for rid in ("R01","R13"):
    r=[x for x in L.ROOMS if x[0]==rid][0]
    n=int((r[4]-r[2])/0.45)
    for i in range(1,n):
        xx=r[2]+i*(r[4]-r[2])/n
        Lm(xx,r[3],xx,r[5],stroke="#D9D6CE",sw=1)

# 梁（虚线）
for x0,y0,x1,y1 in L.BEAMS:
    Rm(x0,y0,x1,y1,fill=C["beam"],op=.35)
    Lm(x0,(y0+y1)/2,x1,(y0+y1)/2,stroke=C["beam"],sw=1.2,dash="9 6")

# 家具
FURN_NOLABEL = {"rug","upper","rail","lamp","mirror","tv","chair","nightstand","plant"}
for room,name,x0,y0,dx,dy,dz,kind in L.FURN:
    furn(kind,x0,y0,dx,dy)
for room,name,x0,y0,dx,dy,dz,kind in L.FURN:
    if kind in FURN_NOLABEL or dx*dy < 0.28: continue
    cx,cy = px(x0+dx/2), py(y0+dy/2)
    lbl = name.split("（")[0]
    vert = dy > dx*1.9
    if vert:
        a(f'<g transform="rotate(-90 {cx:.1f} {cy:.1f})">'); T(cx,cy+3.5,lbl,10.5,C["ink2"],600); a('</g>')
    else:
        T(cx,cy+3.5,lbl,10.5,C["ink2"],600)

# 墙体
for kind,x0,y0,x1,y1 in L.WALLS:
    col = C["wallE"] if kind=="E" else (C["rail"] if kind=="P" else C["wallI"])
    for sx0,sy0,sx1,sy1 in wall_pieces(kind,x0,y0,x1,y1):
        Rm(sx0,sy0,sx1,sy1,fill=col)

# 门
for nm,x,y,w,o,swg,tp in L.DOORS:
    th = 0.24 if tp=="entry" or nm in("客厅推拉门","阳台推拉门") else 0.12
    if o=="h":
        y0 = y-th if y>0.5 else y
        if nm=="客厅推拉门": y0=8.60
        if nm=="阳台推拉门": y0=-0.24
        if nm=="入户门":     y0=-0.24
        Rm(x,y0,x+w,y0+th,fill=C["paper"])
        Lm(x,y0,x,y0+th,stroke=C["wallI"],sw=1.2); Lm(x+w,y0,x+w,y0+th,stroke=C["wallI"],sw=1.2)
        if tp=="slide":
            Lm(x+0.02,y0+th*.30,x+w*.55,y0+th*.30,stroke=C["ink2"],sw=3)
            Lm(x+w*.45,y0+th*.70,x+w-0.02,y0+th*.70,stroke=C["ink2"],sw=3)
        else:
            hx = x if swg in("se","ne") else x+w
            sgn = 1 if swg in("se","ne") else -1
            dwn = 1 if swg in("se","sw") else -1
            Lm(hx,y0+th/2, hx+sgn*w, y0+th/2, stroke=C["ink2"],sw=2.2)
            a(f'<path d="M{px(hx+sgn*w):.1f},{py(y0+th/2):.1f} A{w*S:.1f},{w*S:.1f} 0 0 {1 if sgn*dwn>0 else 0} '
              f'{px(hx):.1f},{py(y0+th/2+dwn*w):.1f}" fill="none" stroke="{C["ink3"]}" stroke-width="1" stroke-dasharray="4 3"/>')
    else:
        x0 = x if x<0.5 or True else x
        Rm(x0,y,x0+th,y+w,fill=C["paper"])
        Lm(x0,y,x0+th,y,stroke=C["wallI"],sw=1.2); Lm(x0,y+w,x0+th,y+w,stroke=C["wallI"],sw=1.2)
        if tp=="slide":
            Lm(x0+th*.30,y+0.02,x0+th*.30,y+w*.55,stroke=C["ink2"],sw=3)
            Lm(x0+th*.70,y+w*.45,x0+th*.70,y+w-0.02,stroke=C["ink2"],sw=3)
        elif tp=="arch":
            Lm(x0+th/2,y,x0+th/2,y+w,stroke=C["beam"],sw=2,dash="8 5")
        else:
            hy = y if swg in("se","sw") else y+w
            sgn = 1 if swg in("se","sw") else -1
            rgt = 1 if swg in("se","ne") else -1
            Lm(x0+th/2,hy, x0+th/2, hy+sgn*w, stroke=C["ink2"],sw=2.2)
            a(f'<path d="M{px(x0+th/2):.1f},{py(hy+sgn*w):.1f} A{w*S:.1f},{w*S:.1f} 0 0 {1 if sgn*rgt<0 else 0} '
              f'{px(x0+th/2+rgt*w):.1f},{py(hy):.1f}" fill="none" stroke="{C["ink3"]}" stroke-width="1" stroke-dasharray="4 3"/>')

# 窗
for nm,x,y,w,o,tp in L.WINDOWS:
    th = 0.24 if tp!="bay" else 0.24
    if o=="h":
        y0 = -0.24 if y<0 else 8.60
        if y<-1: y0 = -1.42; th=0.12
        Rm(x,y0,x+w,y0+th,fill=C["paper"])
        for f in (0.18,0.5,0.82):
            Lm(x,y0+th*f,x+w,y0+th*f,stroke=C["ink2"],sw=1.1 if f!=0.5 else 1.6)
        Lm(x,y0,x,y0+th,stroke=C["wallE"],sw=1.4); Lm(x+w,y0,x+w,y0+th,stroke=C["wallE"],sw=1.4)
        if tp=="bay":
            d=0.45
            Rm(x,y0+th,x+w,y0+th+d,fill=C["paper"],stroke=C["wallE"],sw=1.6)
            for f in (0.3,0.7): Lm(x,y0+th+d*f,x+w,y0+th+d*f,stroke=C["ink3"],sw=.9,dash="5 4")
    else:
        x0 = -0.24 if x<0 else 13.20
        Rm(x0,y,x0+th,y+w,fill=C["paper"])
        for f in (0.18,0.5,0.82):
            Lm(x0+th*f,y,x0+th*f,y+w,stroke=C["ink2"],sw=1.1 if f!=0.5 else 1.6)
        Lm(x0,y,x0+th,y,stroke=C["wallE"],sw=1.4); Lm(x0,y+w,x0+th,y+w,stroke=C["wallE"],sw=1.4)

# ── 监控摄像头 + 视野 ──
for cid,name,x,y,z,yaw,fov,cover in L.CAMERAS:
    cx,cy = px(x),py(y)
    a0=math.radians(-yaw+fov/2); a1=math.radians(-yaw-fov/2); rr=3.2*S
    p0=(cx+math.cos(a0)*rr, cy+math.sin(a0)*rr); p1=(cx+math.cos(a1)*rr, cy+math.sin(a1)*rr)
    a(f'<path d="M{cx:.1f},{cy:.1f} L{p0[0]:.1f},{p0[1]:.1f} A{rr:.1f},{rr:.1f} 0 0 0 {p1[0]:.1f},{p1[1]:.1f} Z" '
      f'fill="{C["cam"]}" fill-opacity=".07" stroke="{C["cam"]}" stroke-width="1" stroke-opacity=".38" stroke-dasharray="7 6"/>')
    a(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="11" fill="{C["cam"]}"/>')
    a(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="17" fill="none" stroke="{C["cam"]}" stroke-width="1.6" stroke-opacity=".5"/>')
    T(cx,cy+4.5,cid,12,"#FFFFFF",800)

# ── 网线 ──
for src,dst,pts in L.CABLES:
    d="M"+" L".join(f"{px(x):.1f},{py(y):.1f}" for x,y in pts)
    a(f'<path d="{d}" fill="none" stroke="{C["dev"]}" stroke-width="1.6" stroke-opacity=".55" stroke-dasharray="7 5"/>')

# ── 设备 ──
for did,name,room,x,y,z,dx,dy,dz in L.DEVICES:
    cx,cy=px(x),py(y)
    R(cx-10,cy-10,20,20,fill=C["dev"],rx=4)
    T(cx,cy+4.5,did,11,"#FFFFFF",800)

# ── 影片机位（标看点 + 相机方位箭头）──
AZ = {"东南上空":(1,1), "东北上空":(1,-1), "西北上空":(-1,-1), "西南上空":(-1,1), "屋内朝南":(0,-1)}
for vid,name,x,y,z,az,zang,sc,tp,shots in L.FILM_CAMS:
    cx,cy = px(x),py(y)
    ux,uy = AZ[az]; n=math.hypot(ux,uy) or 1; ux,uy = ux/n, uy/n
    sx,sy = cx+ux*74, cy+uy*74
    Ln(sx,sy,cx+ux*20,cy+uy*20, C["film"], 2, dash="7 5")
    ang=math.atan2(-uy,-ux)
    tip=(cx+ux*20, cy+uy*20)
    a('<polygon points="'+" ".join(f"{tip[0]+math.cos(ang+o)*(0 if o==0 else 15):.1f},{tip[1]+math.sin(ang+o)*(0 if o==0 else 15):.1f}"
        for o in (0, 2.55, -2.55))+f'" fill="{C["film"]}"/>')
    dash = "" if tp=="ISO" else ' stroke-dasharray="4 3"'
    a(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="15" fill="#FFFFFF" stroke="{C["film"]}" stroke-width="2.2"{dash}/>')
    T(sx,sy+5,vid,13,C["film"],800)
    a(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="{C["film"]}" fill-opacity=".8"/>')
    a(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="11" fill="none" stroke="{C["film"]}" stroke-width="1.2" stroke-opacity=".45"/>')

# ── 人物站位（S02/S08）──
for pid,x,y,yaw in L.BLOCKING["S02_S08"]:
    ph=[p for p in L.PEOPLE if p[0]==pid][0]
    cx,cy=px(x),py(y); r = 13 if pid!="P4" else 8
    a(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="#FFFFFF" stroke="#8A5A2B" stroke-width="2.4"/>')
    an=math.radians(-yaw)
    Ln(cx,cy,cx+math.cos(an)*(r+9),cy+math.sin(an)*(r+9),"#8A5A2B",2,cap="round")
    if pid!="P4": T(cx,cy+4,pid,10,"#8A5A2B",800)

# ── 房间名 + 面积 ──
for rid,name,x0,y0,x1,y1,tint in L.ROOMS:
    cx,cy=px((x0+x1)/2),py((y0+y1)/2)
    dy_ = -14
    if rid=="R07": cy=py(6.95)
    if rid=="R03": cy=py(2.62)
    if rid=="R02": cy=py(1.95)
    if rid=="R09": cy=py(7.55)
    if rid=="R12": cy=py(7.35)
    if rid=="R06": cy=py(2.62)
    if rid=="R10": cy=py(5.40)
    if rid=="R04": cy=py(2.92)
    if rid=="R01": cy=py(-0.28)
    if rid=="R13": cy=py(9.98)
    if rid=="R05": cy=py(2.92)
    if rid=="R08": cy=py(4.55)
    if rid=="R11": cy=py(4.55)
    ar=(x1-x0)*(y1-y0)
    if rid=="R10":
        a(f'<g transform="rotate(-90 {cx:.1f} {cy:.1f})">')
        T(cx,cy-4,name,17,C["ink"],700); T(cx,cy+15,f"{ar:.1f} ㎡",13,C["ink3"],500)
        a('</g>')
    else:
        T(cx,cy+dy_,name,18 if ar>8 else 15,C["ink"],700,ls=1)
        T(cx,cy+dy_+21,f"{(x1-x0):.2f} × {(y1-y0):.2f}　{ar:.1f} ㎡",12.5,C["ink3"],500)

# ── 尺寸链 ──
def dimchain(vals, fixed, axis, off, label=True):
    for i in range(len(vals)-1):
        v0,v1 = vals[i],vals[i+1]
        if axis=="x":
            y=py(fixed)+off
            Ln(px(v0),y,px(v1),y,C["dim"],1.1)
            for v in (v0,v1): Ln(px(v),y-6,px(v),y+6,C["dim"],1.1)
            if label: T((px(v0)+px(v1))/2, y-9, f"{round((v1-v0)*1000):.0f}", 13, C["ink2"],600)
        else:
            x=px(fixed)+off
            Ln(x,py(v0),x,py(v1),C["dim"],1.1)
            for v in (v0,v1): Ln(x-6,py(v),x+6,py(v),C["dim"],1.1)
            if label:
                mx,my=x,(py(v0)+py(v1))/2
                a(f'<g transform="rotate(-90 {mx:.1f} {my:.1f})">')
                T(mx,my-9,f"{round((v1-v0)*1000):.0f}",13,C["ink2"],600); a('</g>')
dimchain([0,3.6,6.9,8.4,9.6,13.2], -1.42, "x", -32)
dimchain([0,13.2], -1.42, "x", -66, label=False)
dimchain([0,3.2,4.8,8.6], -0.24, "y", -34)
dimchain([0,8.6], -0.24, "y", -78)
T(px(6.6), py(-1.42)-70, "套 内 13200", 13, C["ink3"], 700)

# ── 指北针 ──
nx,ny = px(12.2), py(-1.05)
a(f'<circle cx="{nx}" cy="{ny}" r="30" fill="#FFFFFF" stroke="{C["ink3"]}" stroke-width="1.2"/>')
a(f'<polygon points="{nx},{ny-22} {nx-9},{ny+12} {nx},{ny+4} {nx+9},{ny+12}" fill="{C["ink"]}"/>')
T(nx,ny+27,"N",13,C["ink"],800)

# ── 标题 ──
T(90, 104, "云雀通宣传片 01 · 拍摄用户型平面布置图", 30, C["ink"], 900, "start", 1)
T(90, 134, "三室两厅两卫 · 边套南北通透 · 套内 113.5 ㎡（建面约 135 ㎡）· 层高 2800 · 比例 1:100", 15, C["ink2"], 500, "start", .5)

# ═══════════════ 右侧图例面板 ═══════════════
PX0, PY0, PW = 1584, 200, 336
R(PX0, PY0, PW, 1218, fill="#FFFFFF", stroke="#E3DFD7", sw=1.2, rx=4)
yy = PY0 + 42
T(PX0+22, yy, "图　例", 17, C["ink"], 800, "start", 3); yy+=30
def legend(sym, txt, sub=""):
    global yy
    sym(PX0+34, yy)
    T(PX0+62, yy+5, txt, 14, C["ink"], 600, "start")
    if sub: T(PX0+62, yy+23, sub, 11.5, C["ink3"], 400, "start")
    yy += 40 if sub else 30
legend(lambda x,y: R(x-12,y-7,24,13,fill=C["wallE"]), "承重 / 外墙 240")
legend(lambda x,y: R(x-12,y-5,24,9,fill=C["wallI"]), "内隔墙 120")
legend(lambda x,y: R(x-12,y-4,24,7,fill=C["rail"]),  "阳台栏板")
legend(lambda x,y: (R(x-12,y-6,24,11,fill=C["beam"],op=.35), Ln(x-12,y,x+12,y,C["beam"],1.2,dash="9 6")), "结构梁", "开敞处，梁下净高 2550")
legend(lambda x,y: (Ln(x-12,y,x+12,y,C["ink2"],2.2), Ln(x-12,y,x-12,y+12,C["ink3"],1)), "平开门")
legend(lambda x,y: (Ln(x-12,y-3,x+1,y-3,C["ink2"],3), Ln(x-1,y+3,x+12,y+3,C["ink2"],3)), "推拉门")
legend(lambda x,y: [Ln(x-12,y+k,x+12,y+k,C["ink2"],1.1 if k else 1.6) for k in (-5,0,5)], "窗 / 飘窗")
yy += 8
legend(lambda x,y: (a(f'<circle cx="{x}" cy="{y}" r="10" fill="{C["cam"]}"/>'),
                    a(f'<circle cx="{x}" cy="{y}" r="15" fill="none" stroke="{C["cam"]}" stroke-width="1.4" stroke-opacity=".5"/>')),
       "监控摄像头 C1–C3", "含水平视野锥（示意 3.2 m 半径）")
legend(lambda x,y: R(x-9,y-9,18,18,fill=C["dev"],rx=3), "网络 / 存储设备 D1–D5")
legend(lambda x,y: Ln(x-12,y,x+12,y,C["dev"],1.6,dash="7 5"), "网线走向")
legend(lambda x,y: (a(f'<circle cx="{x}" cy="{y}" r="11" fill="#FFF" stroke="{C["film"]}" stroke-width="2"/>'),
                    a(f'<polygon points="{x+22},{y} {x+11},{y-7} {x+11},{y+7}" fill="{C["film"]}"/>')),
       "影片机位 V1–V6", "圆=相机方位　箭头指向看点")
legend(lambda x,y: (a(f'<circle cx="{x}" cy="{y}" r="11" fill="#FFF" stroke="#8A5A2B" stroke-width="2.4"/>'),
                    Ln(x,y,x+20,y,"#8A5A2B",2)), "人物站位（S02 / S08）")

yy += 16
Ln(PX0+22, yy, PX0+PW-22, yy, "#E3DFD7", 1.2); yy += 32
T(PX0+22, yy, "摄 像 头", 16, C["ink"], 800, "start", 3); yy += 26
for cid,name,x,y_,z,yaw,fov,cover in L.CAMERAS:
    a(f'<circle cx="{PX0+32}" cy="{yy-4}" r="8" fill="{C["cam"]}"/>')
    T(PX0+32,yy,cid,10,"#FFF",800)
    T(PX0+50, yy, name, 13.5, C["ink"], 600, "start")
    T(PX0+50, yy+18, f"({x:.2f}, {y_:.2f}, {z:.2f})　朝向 {yaw}°　FOV {fov}°", 11, C["ink3"], 400, "start")
    T(PX0+50, yy+34, cover, 11, C["ink3"], 400, "start")
    yy += 54
yy += 6
Ln(PX0+22, yy, PX0+PW-22, yy, "#E3DFD7", 1.2); yy += 32
T(PX0+22, yy, "设 备", 16, C["ink"], 800, "start", 3); yy += 26
for did,name,room,x,y_,z,dx,dy,dz in L.DEVICES:
    R(PX0+24, yy-12, 16, 16, fill=C["dev"], rx=3); T(PX0+32, yy, did, 10, "#FFF", 800)
    T(PX0+50, yy, name, 13, C["ink"], 600, "start")
    T(PX0+50, yy+17, f"({x:.2f}, {y_:.2f}, {z:.2f})", 11, C["ink3"], 400, "start")
    yy += 38
yy += 6
Ln(PX0+22, yy, PX0+PW-22, yy, "#E3DFD7", 1.2); yy += 30
T(PX0+22, yy, "坐 标 系", 16, C["ink"], 800, "start", 3); yy += 24
for line in ["原点 (0,0) = 套内西北角",
             "+x 向东 0 → 13.20　+y 向南 0 → 8.60",
             "+z 向上，层高 2.80　梁下 2.55",
             "Blender：(x, −y, z)",
             "相机 rotation_euler = (54.7356°, 0, 45°)"]:
    T(PX0+22, yy, line, 11.5, C["ink2"], 400, "start"); yy += 19

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
       + "\n".join(E) + '</svg>')
out = pathlib.Path(__file__).parent / "out"
out.mkdir(exist_ok=True)
(out/"平面布置图.svg").write_text(svg, encoding="utf-8")
print("svg written")
