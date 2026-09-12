# -*- coding: utf-8 -*-
"""整户等距剖面总览 —— 让人一眼看清 3D 里长什么样"""
import math, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import layout_data as L

S, OX, OY = 68, 640, 320
W, H = 1680, 1180
C30 = math.cos(math.radians(30))
def iso(x,y,z): return (OX + (x-y)*C30*S, OY + ((x+y)*0.5 - z)*S)
E=[]
def a(s): E.append(s)
def sh(hexc,k):
    h=hexc.lstrip("#"); r,g,b=(int(h[i:i+2],16) for i in (0,2,4))
    f=lambda c: c*k if k<=1 else c+(255-c)*(k-1)
    return "#%02x%02x%02x"%tuple(max(0,min(255,int(f(c)))) for c in (r,g,b))
def poly(pts3, fill, op=1, stroke="none", sw=0):
    p=" ".join(f"{q[0]:.1f},{q[1]:.1f}" for q in (iso(*c) for c in pts3))
    a(f'<polygon points="{p}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>')
def box(x,y,z,dx,dy,dz,col,op=1,edge=None):
    T_,Lf,Rt = sh(col,1.0), sh(col,.78), sh(col,.58)
    e = f'{edge}' if edge else "none"
    for c,f in (([(x,y,z+dz),(x+dx,y,z+dz),(x+dx,y+dy,z+dz),(x,y+dy,z+dz)],T_),
                ([(x,y+dy,z),(x+dx,y+dy,z),(x+dx,y+dy,z+dz),(x,y+dy,z+dz)],Lf),
                ([(x+dx,y,z),(x+dx,y+dy,z),(x+dx,y+dy,z+dz),(x+dx,y,z+dz)],Rt)):
        poly(c,f,op,e,1 if edge else 0)
def txt(x,y,s,size=14,fill="#1B2029",w=600,anc="middle",ls=0,op=1):
    a(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anc}" font-family="Noto Sans CJK SC" font-weight="{w}" '
      f'font-size="{size}" fill="{fill}" fill-opacity="{op}" letter-spacing="{ls}">{s}</text>')

TINT = dict(live="#E8C89A", rest="#CBBEDC", wet="#A9CBD8", work="#B4CDA8", util="#CFCBC2")
FCOL = dict(sofa="#5C6B93", armchair="#5C6B93", sofabed="#5C6B93",
            bed="#D8CDBE", nightstand="#9A7B58", wardrobe="#A98A64", cabinet="#A98A64",
            shelf="#A98A64", counter="#CFCFC9", upper="#DDDDD7", desk="#B08C62",
            table="#B08C62", chair="#8E7350", fridge="#D4D8DE", stove="#BFC4CB",
            sink="#E7ECEF", toilet="#EFF3F5", shower="#CDE0E8", tv="#23293A",
            rug="#8E7F9E", plant="#5F8A5F", lamp="#E8C86A", box="#B9BEC6",
            mirror="#BBD3DD", bench="#9A7B58", rail="#9AA2AC")

a(f'<rect width="{W}" height="{H}" fill="#F6F4EF"/>')
a('<defs><filter id="sh" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="9"/></filter></defs>')

items=[]  # (sortkey, z, callable)
WALL_H = 1.15          # 剖切高度：墙只留 1.15 m，方便看进去

# 房间地面
for rid,name,x0,y0,x1,y1,tint in L.ROOMS:
    items.append((x0+y0-100, 0, lambda x0=x0,y0=y0,x1=x1,y1=y1,t=tint:
                  poly([(x0,y0,0),(x1,y0,0),(x1,y1,0),(x0,y1,0)], sh(TINT[t],1.12))))
# 地面阴影
a(f'<ellipse cx="{iso(6.6,4.3,0)[0]:.0f}" cy="{iso(6.6,4.3,0)[1]+20:.0f}" rx="640" ry="330" fill="#C9C3B8" opacity=".45" filter="url(#sh)"/>')

for kind,x0,y0,x1,y1 in L.WALLS:
    h = WALL_H if kind!="P" else 0.95
    col = "#E4DFD5" if kind=="E" else ("#EDE9E0" if kind=="I" else "#C9CEd6".upper())
    items.append((x0+y0, 0, lambda x0=x0,y0=y0,x1=x1,y1=y1,h=h,col=col:
                  box(x0,y0,0,x1-x0,y1-y0,h,col,edge="#B9B3A7")))

for room,name,x0,y0,dx,dy,dz,kind in L.FURN:
    col = FCOL.get(kind,"#B9BEC6")
    h = max(dz, 0.02) if kind!="rug" else 0.015
    h = min(h, WALL_H+0.55)
    items.append((x0+y0, 0, lambda x0=x0,y0=y0,dx=dx,dy=dy,h=h,col=col:
                  box(x0,y0,0,dx,dy,h,col)))

for cid,name,x,y,z,yaw,fov,cover in L.CAMERAS:
    items.append((x+y, z, lambda x=x,y=y,z=z: box(x-0.11,y-0.08,z,0.22,0.16,0.14,"#E8EAEE")))
    items.append((x+y+0.01, z, lambda x=x,y=y,z=z,cid=cid: (
        a(f'<circle cx="{iso(x,y,z)[0]:.1f}" cy="{iso(x,y,z)[1]:.1f}" r="9" fill="#D6323A"/>'),
        a(f'<circle cx="{iso(x,y,z)[0]:.1f}" cy="{iso(x,y,z)[1]:.1f}" r="17" fill="none" stroke="#D6323A" stroke-width="1.6" stroke-opacity=".5"/>'))))
for did,name,room,x,y,z,dx,dy,dz in L.DEVICES:
    items.append((x+y, z, lambda x=x,y=y,z=z,dx=dx,dy=dy,dz=dz: box(x-dx/2,y-dy/2,z,dx,dy,dz,"#0C8C7E")))

items.sort(key=lambda t:(t[0], t[1]))
for _,_,fn in items: fn()

# 房间名标注（引线）
LBL = [("厨房",1.8,1.6,2.6,-240,-40),("餐厅",5.2,1.6,2.6,60,-170),("玄关",7.6,1.2,2.6,120,-120),
       ("公卫",9.0,1.6,2.6,190,-70),("书房",11.4,1.6,2.6,270,-60),("客厅",6.0,5.9,2.6,80,-70),
       ("主卫",1.8,4.0,2.6,-270,-20),("主卧",1.8,6.7,2.6,-290,40),("走廊",9.0,6.0,2.6,150,-30),
       ("储藏",11.4,4.0,2.6,290,-60),("儿童房",11.4,6.7,2.6,250,90),
       ("南阳台",6.0,9.4,2.0,-120,120),("生活阳台",1.8,-0.7,2.2,-330,-10)]
for name,x,y,z,ox_,oy_ in LBL:
    p=iso(x,y,z); q=(p[0]+ox_, p[1]+oy_)
    a(f'<line x1="{p[0]:.1f}" y1="{p[1]:.1f}" x2="{q[0]:.1f}" y2="{q[1]:.1f}" stroke="#9AA0AA" stroke-width="1.2"/>')
    a(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="3.5" fill="#9AA0AA"/>')
    w = len(name)*15+26
    a(f'<rect x="{q[0]-w/2:.1f}" y="{q[1]-16:.1f}" width="{w}" height="30" rx="15" fill="#FFFFFF" stroke="#DCD6CA"/>')
    txt(q[0], q[1]+5, name, 15, "#1B2029", 700)

# 方位角标
for name,x,y in (("北",7.2,-5.6),("南",6.0,14.2),("西",-5.2,3.4),("东",18.4,5.2)):
    p=iso(x,y,0)
    a(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="17" fill="#EAE6DD" stroke="#C8C2B6"/>')
    txt(p[0],p[1]+5,name,14,"#6A7280",700)

txt(70, 74, "整户等距剖面总览 · 墙体剖切至 1.15 m", 26, "#171C25", 900, "start", 1)
txt(70, 104, "视角：东南上空俯视 · Blender 相机 rotation_euler = (54.7356°, 0, 45°) · 全片统一用这一个方位", 14, "#5C6675", 400, "start")
lg=[("#D6323A","监控摄像头 C1–C3"),("#0C8C7E","网络 / 存储设备 D1–D5")]
for i,(c,t) in enumerate(lg):
    a(f'<circle cx="{1290}" cy="{72+i*28}" r="8" fill="{c}"/>')
    txt(1308, 77+i*28, t, 14, "#3A4250", 500, "start")

svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'+"\n".join(E)+'</svg>'
out=pathlib.Path(__file__).parent/"out"; out.mkdir(exist_ok=True)
(out/"等距总览.svg").write_text(svg,encoding="utf-8"); print("iso svg ok")
