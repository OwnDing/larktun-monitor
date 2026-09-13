"""Build the 1200-frame, fourteen-shot timeline and inspect every first frame."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from motion import point_on_curve
sc=bpy.data.scenes['Larktun Film'];bpy.context.window.scene=sc;activate_look('DUSK');apply_v1_cut(225)
shots=[('S01',1,90,'V1a','DARK'),('S02',91,180,'V1','DUSK'),('S03',181,270,'V2','DARK'),('S04',271,360,'V2','DARK'),('S05',361,450,'V4','DUSK'),('S06',451,540,'V3','DUSK'),('S07',541,630,'V2','DARK'),('S08',631,720,'V1','DUSK'),('S09',721,810,'V6','DUSK'),('S10',811,900,'V4','DUSK'),('S11',901,990,'V1','DUSK'),('S12',991,1080,'V5','NIGHT'),('S13',1081,1140,'V1','DUSK'),('S14',1141,1200,'V1','DARK')]
camnames={'V1':'V1 · Film locked living room','V1a':'V1a · Film hook',**{f'V{i}':f'V{i} · Film camera' for i in range(2,7)}}
sc.timeline_markers.clear()
for shot,start,end,cam,look in shots:
    m=sc.timeline_markers.new(shot,frame=start);m.camera=bpy.data.objects[camnames[cam]]
sc['film_timeline']=json.dumps(shots);sc['film_camera_names']=json.dumps(camnames)
# Baked cubic ease-out on ortho_scale. Camera location and Euler angles never move.
camera=bpy.data.objects[camnames['V1a']]
for f in range(1,91):
    t=(f-1)/89;camera.data.ortho_scale=1.6+16.4*(1-(1-t)**3);camera.data.keyframe_insert('ortho_scale',frame=f)
camera=bpy.data.objects[camnames['V2']]
for f in list(range(181,361))+[541,630]:
    t=max(0,min(1,(f-271)/89));camera.data.ortho_scale=42-30*(t*t*(3-2*t)) if f<541 else 42
    camera.data.keyframe_insert('ortho_scale',frame=f)
# Deterministic family head idle; exact repeated phase in S02/S08.
for i,pid in enumerate(('P1','P2','P3')):
    arm=bpy.data.objects[pid+' seated rig'];head=arm.pose.bones['head'];base=head.matrix_basis.copy()
    for f in list(range(91,181))+list(range(631,721)):
        local=(f-91 if f<181 else f-631)
        head.matrix_basis=base@Matrix.Rotation(math.radians(2)*math.sin(local/30*1.7+i*.8),4,'Z')
        head.keyframe_insert('rotation_quaternion',frame=f);head.keyframe_insert('location',frame=f);head.keyframe_insert('scale',frame=f)
    head.matrix_basis=base;head.keyframe_insert('rotation_quaternion',frame=181);head.keyframe_insert('rotation_quaternion',frame=721)
# D1 top status repeaters receive distinct materials for ordered disk activation.
for i in range(3):
    ob=bpy.data.objects[f'D1 top status repeater {i}'];ob.data.materials.clear();ob.data.materials.append(material(f'D1 disk LED {i}','2FE0C8',.3,1))
# Float torus planes toward their camera without changing the projected centre.
for ob in bpy.data.collections['FILM · Pulse rings'].objects:
    if ob.name.startswith('S01'):ob.location+=Euler((math.radians(54.7356),0,math.radians(225))).to_matrix()@Vector((0,0,.75))
# Original abstract tower windows and a real thumbnail of this same home.
coll=bpy.data.collections['FILM · Original abstract remote tower'];ns=helpers(coll)
for ob in coll.objects:
    if ob.get('film_role')=='remote_window':
        mat=material(ob.name+' red activity','FF4B4B',.45,2);ob.data.materials.clear();ob.data.materials.append(mat)
preview=bpy.data.images.load(str(OUT/'gates/D/S02_0135.png'));preview.pack()
mat=bpy.data.materials.new('S04 / this home preview');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links;b=n.get('Principled BSDF');t=n.new('ShaderNodeTexImage');t.image=preview
l.new(t.outputs['Color'],b.inputs['Emission Color']);b.inputs['Emission Strength'].default_value=2.5;l.new(t.outputs['Color'],b.inputs['Base Color'])
# Window has a landscape crop, matching a surveillance thumbnail.
points=[(15.3,14.415,3.1),(16.9,14.415,3.1),(16.9,14.415,4.3),(15.3,14.415,4.3)]
me=bpy.data.meshes.new('S04 household thumbnail mesh');me.from_pydata([loc(p) for p in points],[],[(0,1,2,3)]);me.update();ob=bpy.data.objects.new('S04 / this home window',me);coll.objects.link(ob);me.materials.append(mat)
uv=me.uv_layers.new(name='Window crop UV');coords=[(.05,.24),(.95,.24),(.95,.70),(.05,.70)]
for i,c in enumerate(coords):uv.data[i].uv=c
ob['film_shots']='S04';ob['film_role']='home_preview'
frame=bezier('S04 / pulsing red frame',points+[points[0]],.025,material('S04 frame emission','FF4B4B',.4,16),coll);frame['film_shots']='S04';frame['film_role']='home_preview'
# Upper-path fragments break away after frame 547.
fragcoll=collection('FILM · S07 shattered outbound stream');ns=helpers(fragcoll);rng=random.Random(707)
for i in range(42):
    curve=bpy.data.objects[f'REMOTE RED / C{i%3+1}'];p=point_on_curve(curve,.52+(i//3)/14*.47)
    ob=ns['box'](f'S07 fragment {i}',*draw(p),.09,.075,.22,material(f'S07 fragment material {i}','FF4B4B',.5,16),.012)
    ob['film_shots']='S07';ob['film_role']='shard';ob['shard_origin']=list(ob.location);ob['shard_drift']=[rng.uniform(-1.4,1.4),rng.uniform(-1.4,1.4),rng.uniform(.5,2.2)]
    for f,t in [(548,0),(560,.13),(630,1)]:
        ob.location=p+Vector(ob['shard_drift'])*t;ob.rotation_euler=(t*rng.uniform(-2,2),t*rng.uniform(-2,2),t*rng.uniform(-3,3));ob.keyframe_insert('location',frame=f);ob.keyframe_insert('rotation_euler',frame=f)
        ob.scale=(1-t*.96,)*3;ob.keyframe_insert('scale',frame=f)
        b=ob.active_material.node_tree.nodes.get('Principled BSDF');b.inputs['Emission Strength'].default_value=16*(1-t);b.inputs['Emission Strength'].keyframe_insert('default_value',frame=f)
# One complete MakeHuman child, lying on their side with naturally flexed joints.
source=bpy.data.objects['P3 seated rig'];sleepcoll=collection('FILM · Sleeping child')
arm=source.copy();arm.data=source.data.copy();arm.animation_data_clear();arm.name='P3 sleeping rig';sleepcoll.objects.link(arm)
rotation=Matrix(((0,1,0),(0,0,1),(1,0,0))).to_4x4()
arm.matrix_world=Matrix.Translation(loc((11.96,6.6,.73)))@rotation
arm['film_room']='R12';arm['film_shots']='S12';arm['film_role']='sleeping_child'
for src in source.children:
    ob=src.copy();ob.data=src.data.copy();ob.name='S12 '+src.name;sleepcoll.objects.link(ob);ob.parent=arm
    for mod in ob.modifiers:
        if mod.type=='ARMATURE':mod.object=arm
    ob['film_room']='R12';ob['film_shots']='S12';ob['film_role']='sleeping_child'
# A folded bill is two physical hinged leaves, each with actual ink strokes.
props=bpy.data.collections['FILM · Shot-specific staging'];ns=helpers(props)
for ob in list(props.objects):
    if ob.name.startswith('S06 PAPER'):ob['film_retired']=True
for side in (-1,1):
    pivot=bpy.data.objects.new(f'S06 paper hinge {side}',None);props.objects.link(pivot);pivot.location=loc((5.89,1.6,.754));pivot['film_shots']='S06';pivot['film_role']='bill_fold'
    me=bpy.data.meshes.new('Paper leaf');me.from_pydata([(-.14,0,0),(.14,0,0),(.14,side*.20,0),(-.14,side*.20,0)],[],[(0,1,2,3)]);me.update()
    leaf=bpy.data.objects.new(f'S06 folded leaf {side}',me);props.objects.link(leaf);leaf.parent=pivot;me.materials.append(bpy.data.materials['paper']);leaf['film_shots']='S06';leaf['film_role']='bill_fold'
    sol=leaf.modifiers.new('Paper thickness','SOLIDIFY');sol.thickness=.0005
    for j in range(6):
        curve=bezier(f'S06 bill ink {side} {j}',[(-.112,-side*(.028+j*.026),.001),(.08 if j%3 else .11,-side*(.028+j*.026),.001)],.0007,bpy.data.materials['dark'],props)
        curve.parent=pivot;curve['film_shots']='S06';curve['film_role']='bill_fold'
    for f in range(451,476):
        t=(f-451)/24;pivot.rotation_euler.x=side*math.radians(58)*(1-t)**3;pivot.keyframe_insert('rotation_euler',frame=f)
# Pulse glow across the home is light, not an opaque sphere hiding the interior.
d=bpy.data.lights.new('S08 local halo','POINT');d.color=linear('2FE0C8')[:3];d.energy=4;d.shadow_soft_size=3;d.use_shadow=False
o=bpy.data.objects.new(d.name,d);collection('FILM · Moving flow lights').objects.link(o);o.location=loc((6.8,5.3,1.4));o['film_shots']='S08';o['film_role']='local_halo'
# Bookkeeping and embedded trusted scene controller.
text=bpy.data.texts.new('RUN_FILM_TIMELINE.py');text.from_string("import bpy, sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path(bpy.data.filepath).parent/'film'))\nfrom motion import install\ninstall()\n");text.use_module=True
from motion import install,apply_frame
install();sc.frame_set(91);apply_frame(sc);save('E')
report={'gate':'E','status':'first_frame_review','timeline':[dict(shot=s,start=a,end=b,camera=c,look=l) for s,a,b,c,l in shots],'first_frames':[]}
for shot,start,end,camera,look in shots:
    sc.frame_set(start);apply_frame(sc);seconds=render(OUT/f'gates/E/{shot}_{start:04d}.png',sc.camera,32)
    report['first_frames'].append(dict(shot=shot,frame=start,render_seconds=seconds,camera_location=list(sc.camera.location),camera_rotation_euler_deg=[math.degrees(v) for v in sc.camera.rotation_euler],ortho_scale=sc.camera.data.ortho_scale))
dump(OUT/'gates/E/timeline_report.json',report)
print('E FIRST FRAMES COMPLETE',flush=True)
