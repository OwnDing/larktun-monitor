import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from motion import install,apply_frame,point_on_curve
sc=bpy.data.scenes['Larktun Film'];bpy.context.window.scene=sc;install()
# Place C1's physical indicator on its visible upper quadrant. Same C1, fixed camera.
sc.frame_set(1);apply_frame(sc);layer=bpy.context.view_layer;layer.update()
normal=bpy.data.objects['V1a · Film hook'].rotation_euler.to_matrix()@Vector((0,0,1))
led=bpy.data.objects['C1 LED'];led.location=center(bpy.data.objects['C1 camera housing'])+normal*.083
for ob in bpy.data.collections['FILM · Pulse rings'].objects:
    if ob.name.startswith('S01'):ob.location=led.location+normal*.65
# A faint local path with ONE round-trip reassurance point, not large GN packets.
line=bpy.data.objects['S12 CYAN / local reassurance'];line.data.bevel_depth=.006
line.data.materials.clear();line.data.materials.append(material('S12 faint local line','2FE0C8',.5,.8))
for ob in sc.objects:
    if ob.name.startswith('S12 CYAN') and ob!=line:
        ob['film_retired']=True;ob['film_shots']='RETIRED';ob.hide_render=True
coll=collection('FILM · Sleeping child');ns=helpers(coll)
point=ns['sphere']('S12 reassurance point',10.62,5.04,2.2,.023,.023,.023,material('S12 point emission','2FE0C8',.3,8))
point['film_shots']='S12';point['film_role']='night_dot'
for f in range(991,1081):
    t=abs(((f-991)%24)/12-1);point.location=point_on_curve(line,max(.0001,min(.9999,t)));point.keyframe_insert('location',frame=f)
# Soft quilt over the lower sleeping body; the head and separate arms remain visible.
verts=[];faces=[];NX=24;NY=20
for j in range(NY+1):
    y=5.90+j/NY*.77
    for i in range(NX+1):
        x=11.43+i/NX*1.0;z=.71+.20*math.exp(-((x-11.87)/.33)**2)+.015*math.sin(x*37+y*26)
        verts.append(loc((x,y,z)))
for j in range(NY):
    for i in range(NX):a=j*(NX+1)+i;faces.append((a,a+1,a+NX+2,a+NX+1))
me=bpy.data.meshes.new('Sleeping quilt surface');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('S12 softly draped quilt',me);coll.objects.link(ob);me.materials.append(bpy.data.materials['linen']);ob['film_shots']='S12';ob['film_role']='sleeping_child';ob['film_room']='R12'
for p in me.polygons:p.use_smooth=True
sol=ob.modifiers.new('Physical quilt thickness','SOLIDIFY');sol.thickness=.014
# Emissive tower windows get their own restrained reflected red light.
for i,pos in enumerate([(14.1,13.8,3.8),(17.7,14.0,7.2)]):
    d=bpy.data.lights.new(f'Remote red window bounce {i}','POINT');d.energy=16;d.color=linear('FF4B4B')[:3];d.shadow_soft_size=1.5;d.use_shadow=False
    ob=bpy.data.objects.new(d.name,d);collection('FILM · Moving flow lights').objects.link(ob);ob.location=loc(pos);ob['film_shots']='S03 S04 S07';ob['film_role']='remote_bounce'
# Compare all 90 camera and complete body pose samples.
records=[];pairs=[]
def snapshot(f):
    sc.frame_set(f);apply_frame(sc);bpy.context.view_layer.update();cam=sc.camera
    return dict(frame=f,camera=cam.name,matrix=[float(v) for row in cam.matrix_world for v in row],rotation_deg=[math.degrees(v) for v in cam.rotation_euler],scale=cam.data.ortho_scale,body_poses={pid:[float(v) for bone in bpy.data.objects[pid+' seated rig'].pose.bones for row in bone.matrix for v in row] for pid in ('P1','P2','P3')})
first=[snapshot(f) for f in range(91,181)]
second=[snapshot(f) for f in range(631,721)]
for a,b in zip(first,second):
    delta=max(abs(x-y) for x,y in zip(a['matrix'],b['matrix']));pose=max(abs(x-y) for pid in a['body_poses'] for x,y in zip(a['body_poses'][pid],b['body_poses'][pid]))
    pairs.append(dict(S02_frame=a['frame'],S08_frame=b['frame'],same_camera=a['camera']==b['camera'],camera_matrix_max_abs_delta=delta,ortho_scale_delta=abs(a['scale']-b['scale']),body_pose_max_abs_delta=pose))
assert all(p['same_camera'] and p['camera_matrix_max_abs_delta']==0 and p['ortho_scale_delta']==0 and p['body_pose_max_abs_delta']<1e-5 for p in pairs),max(p['body_pose_max_abs_delta'] for p in pairs)
dump(OUT/'gates/E/S02_S08_camera_alignment.json',dict(status='PASS',pairs=pairs,look_at=[6,4.6,1.3],resolution=[1080,1920],note='Rendered overlays will be added after G. These are actual camera world matrices and complete evaluated skeletal pose matrices, not copied metadata.'))
# Required first frames updated for refined hook/tower/night.
report=json.loads((OUT/'gates/E/timeline_report.json').read_text())
for shot,f in [('S01',1),('S03',181),('S04',271),('S07',541),('S12',991)]:
    sc.frame_set(f);apply_frame(sc);render(OUT/f'gates/E/{shot}_{f:04d}.png',sc.camera,32)
for shot,f in [('S01',20),('S04',340),('S07',547),('S07',560),('S09',770),('S12',1030)]:
    sc.frame_set(f);apply_frame(sc);render(OUT/f'gates/E/motion_checks/{shot}_{f:04d}.png',sc.camera,32)
sc.frame_set(91);apply_frame(sc);save('E');report['status']='PASS';report['pending_graphics']=['S05/S10 phone UI in F','S06 money, S11 split screen, S13 cards, S14 original bird and final fade in H'];dump(OUT/'gates/E/timeline_report.json',report)
print('E PASS / 90 aligned camera and body pairs',flush=True)
