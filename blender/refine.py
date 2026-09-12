# Final tactile detail and a one-time baked cloth relaxation.
from mathutils.bvhtree import BVHTree
C=DETAIL

# Wall artwork uses real frames, recessed mounts and vector-like geometry.
# Every piece is original geometry; no external copyrighted texture files.
def artwork(x,y,z,w,h,axis='x',theme='landscape'):
    before=set(C.objects)
    box('Gallery frame',-.025,-w/2,-h/2,.035,w,h,'oak',.008)
    box('Print recessed mounting board',.014,-w/2+.028,-h/2+.028,.003,w-.056,h-.056,'paper',.001)
    # Muted overlapping landscape bands, arranged flat inside the mount.
    for j in range(3):
        verts=[(.018,-w*.40,-h*.37+j*h*.14)]
        for i in range(41):
            t=i/40; yy=-w*.40+t*w*.80; zz=-h*.19+j*h*.12+sin(t*pi*1.5+j)*h*.11
            verts.append((.018,yy,zz))
        verts.append((.018,w*.4,-h*.37+j*h*.14))
        mesh('Abstract landscape print',verts,[tuple(range(len(verts)))],['sage','rust','blue'][j])
    # Flat paper sun on the artwork plane.
    pts=[(.019,w*.18+cos(a)*h*.075,h*.24+sin(a)*h*.075) for a in [2*pi*i/48 for i in range(48)]]
    mesh('Print sun disc',pts,[tuple(range(48))],'terracotta')
    obs=set(C.objects)-before
    if axis=='y': rotate_group(obs,(0,0,0),90)
    for o in obs:
        o.location+=loc((x,y,z))
        for old in list(o.users_collection): old.objects.unlink(o)
        UPFIX.objects.link(o)

artwork(3.746,6.90,1.74,1.10,.72)
artwork(11.92,4.94,1.68,.72,.61,'y')
artwork(6.872,1.17,1.63,.57,.71)

# Correct towel rails to actual vanity-front mountings, including end brackets.
for rid, x, oldy, newy, z in [('R08',.68,4.02,3.966,.62),('R05',8.58,1.90,1.783,.57)]:
    rail=next((o for o in bpy.data.objects if o.name==rid+' towel rail'),None)
    if rail:
        rail.location+=loc((0,newy-oldy,z-.85))
        for xx in (x,x+.32): rod(rid+' towel-rail mounting bracket',(xx,newy-.04,z),(xx,newy,z),.013,'brass')
    towel=next((o for o in bpy.data.objects if o.name==rid+' hung hand towel'),None)
    if towel: towel.location+=loc((0,newy-oldy,z-.85))

# Nearfield contact detail: plug leads, outlet trim and sofa stitching.
curve('Living floor lamp mains cable',[(4.0,4.49,.025),(3.91,4.54,.023),(3.76,4.55,.02),(3.74,4.55,.30)],.0026,'dark')
box('Lamp wall plug',3.736,4.536,.275,.027,.027,.047,'white',.004)
for rid,y0,length in [('R07',4.85 if ARGS.strict_plan else 5.93,2.45 if ARGS.strict_plan else 2.18)]:
    x=3.78 if rid=='R07' else 9.75
    curve('Upholstery lower seam',[(x+.95,y0+.14,.27),(x+.95,y0+length-.14,.27)],.0015,'blue')

COLLISION=col('TEMP cloth collisions')
bed_duvets=[o for o in bpy.data.objects if o.type=='MESH' and o.name.endswith('soft duvet')]
for mattress in [o for o in bpy.data.objects if o.type=='MESH' and o.name.endswith('mattress') and not 'piping' in o.name]:
    COLLISION.objects.link(mattress)
    mod=mattress.modifiers.new('Cloth collision mattress','COLLISION')
    mattress.collision.thickness_outer=.009
for duvet in bed_duvets:
    verts=duvet.data.vertices
    xs=[v.co.x for v in verts]; ys=[-v.co.y for v in verts]
    x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys)
    pin=duvet.vertex_groups.new(name='Fold gently held at head of mattress')
    for v in verts:
        u=(v.co.x-x0)/(x1-x0); vv=(-v.co.y-y0)/(y1-y0)
        v.co.z=.625+.009*sin(u*15+vv*19)
        if vv<.035: pin.add([v.index],1,'REPLACE')
    mod=duvet.modifiers.new('One-time cloth relaxation','CLOTH')
    bpy.context.view_layer.objects.active=duvet
    bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0)
    st=mod.settings; st.quality=5; st.mass=.32
    st.tension_stiffness=45; st.compression_stiffness=45; st.shear_stiffness=30; st.bending_stiffness=.6
    st.vertex_group_mass=pin.name; st.pin_stiffness=1
    mod.collision_settings.collection=COLLISION
    mod.collision_settings.distance_min=.008
    mod.collision_settings.use_self_collision=False
    mod.point_cache.frame_start=1; mod.point_cache.frame_end=22

SC.frame_end=22
for frame in range(1,23):
    SC.frame_set(frame)
    bpy.context.view_layer.update()
    if frame%5==0: print('Relaxing bed linen',frame,'/22',flush=True)
for duvet in bed_duvets:
    bpy.context.view_layer.objects.active=duvet
    bpy.ops.object.modifier_apply(modifier='One-time cloth relaxation')
    duvet['construction']='22-frame Blender Cloth relaxation against mattress, applied to static mesh'
    xs=[v.co.x for v in duvet.data.vertices]; ys=[-v.co.y for v in duvet.data.vertices]
    xlo,xhi,ylo,yhi=min(xs),max(xs),min(ys),max(ys)
    for v in duvet.data.vertices:
        u=(v.co.x-xlo)/(xhi-xlo); t=(-v.co.y-ylo)/(yhi-ylo)
        crease=.011*sin(u*31+t*12)*math.exp(-((t-.7)/.28)**2)
        crease+=.006*sin(u*19-t*26)*sin(pi*u)
        v.co.z+=crease*sin(pi*max(0,min(1,t)))
    # Layer other blankets on the relaxed duvet, avoiding interpenetrating fabrics.
    bvh=BVHTree.FromObject(duvet,bpy.context.evaluated_depsgraph_get())
    prefix=duvet.name.removesuffix('soft duvet')
    for suffix in ('foot throw','folded top edge'):
        ob=bpy.data.objects.get(prefix+suffix)
        if not ob: continue
        for v in ob.data.vertices:
            sample=v.co.copy(); sample.z=1.5
            hit,normal,idx,dist=bvh.ray_cast(sample,Vector((0,0,-1)),2)
            if hit: v.co.z=hit.z+.026+.002*sin(v.co.x*30+v.co.y*14)
for mattress in list(COLLISION.objects):
    for mod in list(mattress.modifiers):
        if mod.type=='COLLISION': mattress.modifiers.remove(mod)
bpy.data.collections.remove(COLLISION)
SC.frame_set(1); SC.frame_end=1

def lettering(name,body,xyz,size,mat='ink',angle=0):
    d=bpy.data.curves.new(name,'FONT'); d.body=body; d.size=size; d.space_line=1.2; d.extrude=0
    ob=bpy.data.objects.new(name,d); DETAIL.objects.link(ob); ob.location=loc(xyz)
    ob.rotation_euler.z=math.radians(angle); d.materials.append(M[mat]); return ob
lettering('Art book title','STILL\nLIFE',(5.255,5.913,.436),.038,angle=7)
lettering('Bill heading','HOME / SEPTEMBER',(5.23,6.237,.407),.006)

verts=[]; faces=[]
for i in range(18000):
    x=4.76+RNG.random()*2.38; y=4.96+RNG.random()*2.58; h=RNG.uniform(.003,.007)
    a=RNG.random()*2*pi; dx=cos(a)*.0007; dy=sin(a)*.0007; k=len(verts)
    verts.extend([(x-dx,y-dy,.027),(x+dx,y+dy,.027),(x+.001,y,.027+h)])
    faces.append((k,k+1,k+2))
pile=mesh('Living rug · individual short pile fibres',verts,faces,'rug')
rotate_group([pile],(5.95,6.25,0),2)
print('Static cloth baked and intersections reduced',flush=True)
