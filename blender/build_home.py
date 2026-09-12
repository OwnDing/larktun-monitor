"""Detailed, self-contained apartment. Run with Blender 5.x, not system Python.
All modelling coordinates follow scene/layout.json: x east, y south, z up.
Original drawing files are read-only. No video or renderable character proxies.
"""
import bpy, math, json, random, os, sys, argparse
from mathutils import Vector, Euler
from pathlib import Path
from math import sin, cos, pi, sqrt

ROOT = Path(__file__).resolve().parents[1]
L = json.loads((ROOT / 'scene/layout.json').read_text())
RNG = random.Random(91307)
P = argparse.ArgumentParser()
P.add_argument('--render', default='')
P.add_argument('--resolution', type=int, default=1600)
P.add_argument('--samples', type=int, default=64)
P.add_argument('--strict-plan', action='store_true')
ARGS = P.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
SC.unit_settings.system = 'METRIC'
SC.unit_settings.length_unit = 'METERS'
SC.render.engine = 'CYCLES'
SC.cycles.samples = ARGS.samples
SC.cycles.use_denoising = True
SC.cycles.adaptive_threshold = .03
SC.cycles.max_bounces = 8
SC.cycles.transmission_bounces = 6
SC.render.image_settings.file_format = 'PNG'
SC.render.image_settings.color_mode = 'RGB'
SC.render.resolution_percentage = 100
SC.render.film_transparent = False
SC.view_settings.view_transform = 'AgX'
SC.view_settings.look = 'AgX - Medium High Contrast'
SC.view_settings.exposure = .3
SC.render.fps = 24
SC.frame_end = 1
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'
    prefs.get_devices()
    for d in prefs.devices: d.use = d.type == 'METAL'
    SC.cycles.device = 'GPU'
except Exception as ex: print('GPU unavailable:', ex)

def col(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or SC.collection).children.link(c)
    return c

ARCH = col('01 · ARCHITECTURE')
LOW = col('01a · Walls below 1.15 m', ARCH)
UP = col('01b · Full height walls — toggle for interiors', ARCH)
FLOORS = col('01c · Floors and skirting', ARCH)
CEILING = col('01d · Ceilings — interiors only', ARCH)
GLAZE = col('01e · Windows doors below cut', ARCH)
UPFIX = col('01f · Upper frames curtains hardware', ARCH)
FULLWALL = col('01g · Continuous full walls / interiors', ARCH)
FULLFRAME = col('01h · Continuous doors windows curtains / interiors', ARCH)
CUTFRAMEUP = col('01i · Upper cut-frame pieces / archive', ARCH)
FURN = col('02 · FURNITURE / room collections')
ROOM = {r['id']: col(r['id']+' · '+r['name'], FURN) for r in L['rooms']}
DETAIL = col('03 · SMALL DETAILS / fittings and lived-in props')
NET = col('04 · CAMERAS & NETWORK / C1–C3 D1–D5')
GUIDES = col('05 · Guides / non-rendering metadata')
LIGHTS = col('06 · LIGHTING')
CAMS = col('07 · CAMERAS / still reviews + future views')
STAGE = col('08 · Presentation ground')
C = DETAIL

def loc(p): return Vector((p[0], -p[1], p[2]))
def rgba(h):
    h=h.lstrip('#'); a=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in a)+(1,)

def material(name, color, rough=.5, metal=0, texture=None, emit=0):
    m=bpy.data.materials.new(name); m.diffuse_color=rgba(color); m.use_nodes=True
    nt=m.node_tree; n=nt.nodes; link=nt.links
    b=n.get('Principled BSDF'); b.inputs['Base Color'].default_value=rgba(color)
    b.inputs['Roughness'].default_value=rough; b.inputs['Metallic'].default_value=metal
    if emit:
        b.inputs['Emission Color'].default_value=rgba(color); b.inputs['Emission Strength'].default_value=emit
    if texture:
        tex=n.new('ShaderNodeTexCoord'); noise=n.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value=1; noise.inputs['Detail'].default_value=3
        vm=n.new('ShaderNodeVectorMath'); vm.operation='MULTIPLY'
        vm.inputs[1].default_value={'wood':(3,95,8),'fabric':(230,230,230),'wall':(5,5,5),'stone':(10,10,10),'rug':(360,360,360)}[texture]
        link.new(tex.outputs['Object'],vm.inputs[0]); link.new(vm.outputs[0],noise.inputs['Vector'])
        ramp=n.new('ShaderNodeValToRGB'); base=rgba(color)
        amount=.28 if texture=='wood' else (.022 if texture=='wall' else .13)
        ramp.color_ramp.elements[0].position=.15; ramp.color_ramp.elements[1].position=.85
        ramp.color_ramp.elements[0].color=tuple(v*(1-amount) for v in base[:3])+(1,)
        ramp.color_ramp.elements[1].color=tuple(min(1,v*(1+amount)) for v in base[:3])+(1,)
        link.new(noise.outputs['Fac'],ramp.inputs[0]); link.new(ramp.outputs[0],b.inputs['Base Color'])
        bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.22
        bump.inputs['Distance'].default_value={'wood':.0008,'fabric':.0012,'wall':.00025,'stone':.0006,'rug':.003}[texture]
        link.new(noise.outputs['Fac'],bump.inputs['Height']); link.new(bump.outputs['Normal'],b.inputs['Normal'])
        rr=n.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value=max(.1,rough-.08); rr.inputs['To Max'].default_value=min(1,rough+.08)
        link.new(noise.outputs['Fac'],rr.inputs[0]); link.new(rr.outputs[0],b.inputs['Roughness'])
        if texture in ('fabric','rug'): b.inputs['Sheen Weight'].default_value=.24
    return m

M={}
for key, color, rough, metal, tex in [
 ('plaster','E8E3D7',.86,0,'wall'),('cut','EEE9DE',.76,0,None),('white','F4F0E6',.38,0,None),
 ('oak','B68A5C',.42,0,'wood'),('oak_light','CDA77B',.48,0,'wood'),('walnut','72523D',.38,0,'wood'),
 ('sage','859184',.6,0,None),('dark','252C2D',.35,0,None),('rubber','191C1C',.85,0,None),
 ('brass','BBA16C',.27,.78,None),('steel','B4BABC',.25,.85,None),('chrome','C4CDCD',.16,.93,None),
 ('linen','DDD3BD',.89,0,'fabric'),('blue','667D88',.85,0,'fabric'),('green_fab','76866B',.91,0,'fabric'),
 ('rust','AE7255',.88,0,'fabric'),('cream_fab','EFE7D6',.86,0,'fabric'),('rug','CCC3AB',.94,0,'rug'),
 ('tile','C7C8C0',.38,0,'stone'),('tile_warm','D8D1C1',.44,0,'stone'),('grout','9B998D',.87,0,None),
 ('stone','E1DECE',.32,0,'stone'),('ceramic','E9E8DD',.23,0,None),('terracotta','AA684B',.76,0,'stone'),
 ('leaf','496548',.54,0,None),('leaf_light','718657',.49,0,None),('soil','352E22',1,0,None),
 ('paper','EEE8D6',.88,0,None),('ink','374347',.63,0,None),('water','372720',.2,0,None),
 ('blanket','B4B8A4',.93,0,'fabric'),('child_blanket','C69470',.9,0,'fabric')]:
    M[key]=material(key,color,rough,metal,tex)
M['led']=material('LED · mint status','57DBC4',.35,0,emit=2)
M['warm']=material('Lamp · warm diffuser','FFE0A4',.5,0,emit=3)
M['screen']=material('Standby screen · deep charcoal','182C35',.19,.14)
M['glass']=material('Clear glazing · physical transmission','EFF4EE',.055)
M['glass'].node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=1
M['glass'].node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value=1.46
M['frosted']=material('Privacy satin glass','E6EBDD',.38)
M['frosted'].node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=.78
M['mirror']=material('Silver mirror','F2F5F2',.055,1)
M['sheer']=material('Sheer curtain · woven linen','E8E3D5',.9,texture='fabric')
bs=M['sheer'].node_tree.nodes.get('Principled BSDF'); bs.inputs['Transmission Weight'].default_value=.24

def mesh(name, verts, faces, mat=None, collection=None, smooth=False):
    me=bpy.data.meshes.new(name); me.from_pydata([loc(p) for p in verts],[],[tuple(reversed(f)) for f in faces]); me.update()
    o=bpy.data.objects.new(name,me); (collection or C).objects.link(o)
    if mat: me.materials.append(M.get(mat,mat) if isinstance(mat,str) else mat)
    if smooth:
        for f in me.polygons: f.use_smooth=True
    return o

def bevel(o,w=.006,segments=3):
    mod=o.modifiers.new('Manufactured edge radius','BEVEL'); mod.width=w; mod.segments=segments
    mod.harden_normals=True
    norm=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL'); norm.keep_sharp=True; norm.weight=30
    return o

def box(name,x,y,z,w,d,h,mat='oak',b=.006,collection=None):
    if min(w,d,h)<=0: return None
    v=[(i*w/2,j*d/2,k*h/2) for k in (-1,1) for j in (-1,1) for i in (-1,1)]
    f=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
    o=mesh(name,v,[tuple(reversed(a)) for a in f],mat,collection); o.location=loc((x+w/2,y+d/2,z+h/2))
    if b: bevel(o,min(b,min(w,d,h)*.42),3)
    return o

def rotate_group(obs, pivot, deg):
    p=loc(pivot); rot=Euler((0,0,-math.radians(deg))).to_matrix()
    for o in obs:
        o.location=p+rot@(o.location-p); o.rotation_euler.rotate(Euler((0,0,-math.radians(deg))))

def curve(name,pts,r=.007,mat='steel',closed=False,collection=None):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.resolution_u=2
    sp=cu.splines.new('POLY'); sp.points.add(len(pts)-1)
    for p,co in zip(sp.points,pts): p.co=(*loc(co),1)
    sp.use_cyclic_u=closed; cu.bevel_depth=r; cu.bevel_resolution=3
    o=bpy.data.objects.new(name,cu); (collection or C).objects.link(o)
    cu.materials.append(M.get(mat,mat) if isinstance(mat,str) else mat)
    return o

def rod(name,a,b,r=.015,mat='steel',r2=None,collection=None):
    av,bv=Vector(a),Vector(b); direction=bv-av; n=32
    verts=[]
    q=direction.to_track_quat('Z','Y')
    for z,rad in [(0,r),(direction.length,r if r2 is None else r2)]:
        for i in range(n): verts.append(tuple(av+q@Vector((rad*cos(2*pi*i/n),rad*sin(2*pi*i/n),z))))
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,verts,faces,mat,collection,True)

def cyl(name,x,y,z,r,h,mat='ceramic',r2=None,collection=None): return rod(name,(x,y,z),(x,y,z+h),r,mat,r2,collection)

def ring(name,center,r1,r2,mat='steel',axis='z',collection=None):
    x,y,z=center
    if axis=='z': pts=[(x+r1*cos(i*pi/32),y+r1*sin(i*pi/32),z) for i in range(64)]
    elif axis=='y': pts=[(x+r1*cos(i*pi/32),y,z+r1*sin(i*pi/32)) for i in range(64)]
    else: pts=[(x,y+r1*cos(i*pi/32),z+r1*sin(i*pi/32)) for i in range(64)]
    return curve(name,pts,r2,mat,True,collection)

def lathe(name, x,y,z,profile,mat='ceramic',n=48,collection=None):
    verts=[(x+r*cos(i*2*pi/n),y+r*sin(i*2*pi/n),z+h) for r,h in profile for i in range(n)]
    faces=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(profile)-1) for i in range(n)]
    return mesh(name,verts,faces,mat,collection,True)

def sphere(name,x,y,z,sx,sy,sz,mat='ceramic',collection=None):
    n,m=32,16; v=[]
    for j in range(m+1):
        t=pi*j/m
        for i in range(n):
            a=2*pi*i/n; v.append((sx*sin(t)*cos(a),sy*sin(t)*sin(a),sz*cos(t)))
    f=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(m) for i in range(n)]
    o=mesh(name,v,[tuple(reversed(a)) for a in f],mat,collection,True); o.location=loc((x,y,z)); return o

def pillow(name,x,y,z,w,d,h,mat='linen',tilt=(0,0,0)):
    n,m=64,24; v=[]
    def sp(a,p): return (1 if a>=0 else -1)*abs(a)**p
    for j in range(m+1):
        t=-pi/2+pi*j/m
        for i in range(n):
            a=2*pi*i/n; xx=w/2*sp(cos(t),.55)*sp(cos(a),.36); yy=d/2*sp(cos(t),.55)*sp(sin(a),.36)
            zz=h/2*sp(sin(t),.65)
            zz+=.004*sin(xx*60+yy*19)*sin(yy*50)*abs(sin(t))
            if zz>0: zz-=h*.12*math.exp(-((xx/w+.05)**2+(yy/d-.1)**2)*22)
            v.append((xx,yy,zz))
    f=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(m) for i in range(n)]
    o=mesh(name,v,f,mat,smooth=True); o.location=loc((x,y,z)); o.rotation_euler=tuple(math.radians(a) for a in tilt)
    pts=[(w/2*sp(cos(a),.36),d/2*sp(sin(a),.36),0) for a in [2*pi*i/n for i in range(n)]]
    seam=curve(name+' · stitched welt',pts,.0019,mat,True); seam.location=o.location; seam.rotation_euler=o.rotation_euler
    return o

def cup(x,y,z,mat='ceramic',name='Mug'):
    lathe(name,x,y,z,[(.028,0),(.031,.003),(.037,.073),(.036,.08),(.031,.081),(.029,.012),(0,.012)],mat)
    pts=[(x+.033+.023*sin(t),y,z+.044+.026*cos(t)) for t in [pi*i/24 for i in range(25)]]
    curve(name+' handle',pts,.006,mat); cyl(name+' tea',x,y,z+.065,.030,.001,'water')

def bottle(x,y,z,height=.22,mat='glass',name='Bottle'):
    r=height*.18
    lathe(name,x,y,z,[(0,0),(r,.006),(r,height*.65),(r*.7,height*.78),(r*.39,height*.84),(r*.39,height)],mat)
    cyl(name+' cap',x,y,z+height,r*.44,.018,'dark')
    cyl(name+' paper label',x,y,z+height*.22,r*1.008,height*.28,'paper')

def plant(x,y,z=0,size=1,name='Plant'):
    r=.17*size; h=.30*size
    lathe(name+' pot',x,y,z,[(0,0),(r*.7,0),(r,h),(r*1.03,h+.012),(r*.9,h+.012),(r*.86,h-.06)],'terracotta')
    cyl(name+' soil',x,y,z+h-.024,r*.88,.012,'soil')
    for k in range(12):
        a=k*2.4; length=(.37+RNG.random()*.34)*size; end=(x+cos(a)*length*.60,y+sin(a)*length*.60,z+h+length)
        curve(name+' stem',[(x,y,z+h-.03),(x+cos(a)*length*.25,y+sin(a)*length*.25,z+h+length*.55),end],.006*size,'leaf')
        verts=[]; faces=[]
        for j in range(15):
            t=j/14; width=sin(pi*t)**.7*.12*size
            serr=1-.12*(sin(t*9*pi)**10)
            for side in (-1,0,1):
                radial=(t-.24)*.43*size
                verts.append((end[0]+cos(a)*radial-sin(a)*side*width*serr,end[1]+sin(a)*radial+cos(a)*side*width*serr,end[2]-.17*size*t+.07*size*sin(pi*t)-abs(side)*.035*size))
        for j in range(14):
            for s in range(2): faces.append((j*3+s,j*3+s+1,(j+1)*3+s+1,(j+1)*3+s))
        leaf=mesh(name+' leaf',verts,faces,'leaf' if k%3 else 'leaf_light',smooth=True)
        solid=leaf.modifiers.new('Leaf thickness','SOLIDIFY'); solid.thickness=.0007

def faucet(x,y,z,axis='n'):
    cyl('Tap escutcheon',x,y,z,.034,.015,'chrome')
    pts=[(x,y,z+.01),(x,y,z+.18)]
    pts += [(x,y+.065-.065*cos(t),z+.18+.065*sin(t)) for t in [pi*i/16 for i in range(17)]]
    pts += [(x,y+.13,z+.145)]
    curve('Arched mixer spout',pts,.014,'chrome')
    rod('Tap lever',(x+.025,y,z+.04),(x+.075,y,z+.1),.009,'chrome')

def basin(x,y,z,w=.55,d=.36):
    # Open ceramic bowl, actual hollow mesh, no black painted sink cuboid.
    rings=[(.44,.40,.025),(.5,.5,.105),(.47,.47,.12),(.39,.39,.09),(.22,.22,.006)]
    n=64; verts=[]
    for rx,ry,h in rings:
        for i in range(n):
            a=2*pi*i/n; verts.append((x+w*rx*cos(a),y+d*ry*sin(a),z+h))
    f=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(rings)-1) for i in range(n)]
    f.append(tuple((len(rings)-1)*n+i for i in range(n)))
    mesh('Open glazed wash basin',verts,f,'ceramic',smooth=True)
    cyl('Basin drain',x,y,z+.009,.023,.004,'chrome')

def lamp(x,y,z=0,h=1.6,shade=.18,name='Floor lamp'):
    cyl(name+' weighted base',x,y,z,.145 if h>1 else .075,.025,'brass')
    cyl(name+' stem',x,y,z+.025,.011,h-.19,'brass')
    lathe(name+' linen shade',x,y,z+h-.28,[(shade,.0),(shade*.99,.01),(shade*.62,.29),(shade*.57,.29),(shade*.94,.01)],'cream_fab')
    sphere(name+' warm bulb',x,y,z+h-.17,.032,.032,.042,'warm')
    return

def book(x,y,z,w=.15,d=.21,h=.025,color=None,name='Book',angle=0):
    mat=color or RNG.choice(['sage','rust','blue','linen','walnut'])
    before=set(C.objects)
    box(name+' pages',x+.004,y+.003,z+.002,w-.008,d-.006,h-.004,'paper',.001)
    box(name+' lower cover',x,y,z,w,d,.002,mat,.0005); box(name+' upper cover',x,y,z+h-.002,w,d,.002,mat,.0005)
    box(name+' spine',x,y,z,.005,d,h,mat,.001)
    if angle: rotate_group(set(C.objects)-before,(x+w/2,y+d/2,z),angle)

def rug(x,y,w,d,name='Woven rug',mat='rug',angle=0):
    before=set(C.objects)
    box(name,x,y,.011,w,d,.016,mat,.008)
    for side in (0,1):
        for i in range(int(d/.016)):
            xx=x+side*w; yy=y+.01+i*.016
            curve(name+' knotted fringe',[(xx,yy,.018),(xx+(-1 if not side else 1)*.038,yy+.007*sin(i),.011)],.0014,'linen')
    for edge in (.035,.05):
        curve(name+' woven border',[(x+edge,y+edge,.029),(x+w-edge,y+edge,.029),(x+w-edge,y+d-edge,.029),(x+edge,y+d-edge,.029)],.0018,'linen',True)
    if angle: rotate_group(set(C.objects)-before,(x+w/2,y+d/2,0),angle)

def table(name,x,y,w,d,h,mat='oak',coffee=False):
    box(name+' solid top',x,y,h-.045,w,d,.045,mat,.022)
    box(name+' underside apron',x+.055,y+.055,h-.11,w-.11,d-.11,.075,mat,.01)
    for i in (.09,w-.09):
        for j in (.09,d-.09): rod(name+' tapered leg',(x+i,y+j,.015),(x+i,y+j,h-.05),.021 if coffee else .025,mat,.033)

def chair(x,y,w=.46,d=.46,h=.85,angle=0,name='Dining chair',fabric='linen'):
    before=set(C.objects)
    for i in (.055,w-.055):
        for j in (.045,d-.045): rod(name+' splayed oak leg',(x+i+(-.027 if i<w/2 else .027),y+j+(-.02 if j<d/2 else .02),.015),(x+i,y+j,.45),.019,'oak',.026)
    box(name+' seat frame',x,y,.405,w,d,.042,'oak',.026)
    pillow(name+' seat pad',x+w/2,y+d/2,.465,w-.018,d-.018,.087,fabric)
    for i in (.025,w-.025): rod(name+' back upright',(x+i,y+.05,.43),(x+i,y+.015,h-.06),.022,'oak')
    back=box(name+' curved backrest',x-.015,y-.014,h-.19,w+.03,.065,.155,'oak',.026)
    pillow(name+' back upholstery',x+w/2,y+.038,h-.122,w-.045,.055,.115,fabric)
    rotate_group(set(C.objects)-before,(x+w/2,y+d/2,0),angle)

def cabinet(name,x,y,w,d,h,face='s',mat='oak_light',base=.08,drawers=False):
    box(name+' recessed plinth',x+.035,y+.035,0,w-.07,d-.07,base,'dark',.003)
    box(name+' carcass',x,y,base,w,d,h-base,mat,.004)
    length=w if face in ('n','s') else d
    count=max(1,round(length/.48))
    for k in range(count):
        s=k*length/count+.003; seg=length/count-.006
        levels=3 if drawers else 1
        for j in range(levels):
            zh=base+j*(h-base-.02)/levels; hh=(h-base-.02)/levels-.004
            if face in ('n','s'):
                yy=y+d-.009 if face=='s' else y-.011
                box(name+' front',x+s,yy,zh,seg,.020,hh,mat,.003)
                handle_y=yy+(.032 if face=='s' else -.012)
                rod(name+' handle',(x+s+seg*.3,handle_y,zh+hh-.06),(x+s+seg*.7,handle_y,zh+hh-.06),.006,'brass')
            else:
                xx=x-.011 if face=='w' else x+w-.009
                box(name+' front',xx,y+s,zh,.020,seg,hh,mat,.003)
                handle_x=xx+(-.015 if face=='w' else .036)
                rod(name+' handle',(handle_x,y+s+seg*.3,zh+hh-.06),(handle_x,y+s+seg*.7,zh+hh-.06),.006,'brass')

def blanket(name,x,y,z,w,d,mat):
    # Dense, relaxed cloth mesh. Edge fall and fold ridges are actual geometry.
    nu,nv=58,66; verts=[]
    for j in range(nv+1):
        v=j/nv; yy=y+v*d
        for i in range(nu+1):
            u=i/nu; xx=x+u*w; e=min(u,1-u)
            edgefall=max(0,(.12-e)/.12)**.72*.25
            foot=max(0,(v-.88)/.12)**.8*.18
            fold=.015*sin(u*32+v*18)+.009*sin(v*43-u*13)+.005*sin(u*90+v*59)
            puff=.033*sin(pi*u)*sin(pi*v)
            verts.append((xx,yy,z+fold+puff-edgefall-foot))
    faces=[(j*(nu+1)+i,j*(nu+1)+i+1,(j+1)*(nu+1)+i+1,(j+1)*(nu+1)+i) for j in range(nv) for i in range(nu)]
    o=mesh(name,verts,faces,mat,smooth=True)
    sol=o.modifiers.new('Sewn cloth thickness','SOLIDIFY'); sol.thickness=.009
    sub=o.modifiers.new('Fine fabric folds','SUBSURF'); sub.levels=1; sub.render_levels=1
    o['construction']='Dense draped textile surface; relaxed geometry, no live animation dependency'
    return o

def bed(x,y,w,d,name='Bed',child=False):
    fabric='child_blanket' if child else 'blanket'
    for xx in (.10,w-.10):
        for yy in (.12,d-.12): cyl(name+' oak foot',x+xx,y+yy,.015,.033,.13,'oak')
    box(name+' upholstered base',x-.025,y-.01,.12,w+.05,d+.04,.16,'linen',.055)
    box(name+' headboard oak frame',x-.055,y-.055,.14,w+.11,.10,.95,'oak_light',.035)
    pillow(name+' upholstered headboard',x+w/2,y+.025,.73,w-.02,.09,.65,'linen')
    box(name+' mattress',x,y,.285,w,d,.22,'cream_fab',.075)
    curve(name+' mattress piping',[(x+.06,y+.06,.47),(x+w-.06,y+.06,.47),(x+w-.06,y+d-.06,.47),(x+.06,y+d-.06,.47)],.003,'linen',True)
    for i in range(1 if child else 2):
        pw=.72 if not child else .7
        px=x+w/2 if child else x+w*(.25+.5*i)
        pillow(name+' indented pillow',px,y+.34,.58,pw,.44,.16,'cream_fab',(0,0,(-5 if i==0 else 8)))
    blanket(name+' soft duvet',x-.12,y+.58,.57,w+.24,d-.39,fabric)
    blanket(name+' folded top edge',x-.06,y+.52,.605,w+.12,.26,'cream_fab')
    blanket(name+' foot throw',x-.10,y+d-.5,.65,w+.20,.35,'blue' if not child else 'linen')

for module in ('architecture.py','furniture.py','wet_rooms.py','details.py','refine.py','finish_scene.py'):
    print('BUILDING',module,flush=True)
    exec(compile((ROOT/'blender'/module).read_text(),str(ROOT/'blender'/module),'exec'),globals())
