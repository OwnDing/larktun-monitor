import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from characters import build_family
sc=bpy.data.scenes['Larktun Film'];bpy.context.window.scene=sc;layer=full_layer()
# Rebuild anatomically weighted garments with a higher neckline. No source-home edits.
for pid in ('P1','P2','P3'):
    for ob in list(bpy.data.collections['FILM · '+pid+' MakeHuman character'].objects): bpy.data.objects.remove(ob,do_unlink=True)
build_family()
parent=bpy.data.objects['SHOT PHONE · close-up display stand']
rot=Euler((math.radians(54.7356),0,math.radians(225)))
parent.rotation_euler=(rot.to_matrix()@Matrix.Rotation(math.pi,3,'Z')).to_euler()
stand=bpy.data.objects['SHOT PHONE · stand support']
# Replace the support with a short rear strut below the tilted handset.
ns=helpers(bpy.data.collections['FILM · Shot-specific staging'])
bpy.data.objects.remove(stand,do_unlink=True)
ns['box']('SHOT PHONE · stand support',5.423,6.343,.417,.013,.022,.048,'dark',.004)['shot_prop']='phone_close'
layer.update()
phone=bpy.data.objects['SHOT PHONE · Phone screen'];target=draw(center(phone)-rot.to_matrix()@Vector((0,.010,0)))
report=json.loads((OUT/'gates/B/framing_report.json').read_text())
for e in report['candidates']:
    if e['camera_id'] not in ('V3','V4'):continue
    vid=e['camera_id'];angle=e['z_angle_deg'];scale=e['ortho_scale']
    if vid=='V3':focus_cut('R03',angle)
    else:apply_v1_cut(angle)
    for ob in sc.objects:
        if ob.get('film_role') in ('remote_tower','remote_window'):ob.hide_render=True
        prop=ob.get('shot_prop')
        if prop:ob.hide_render=(prop=='phone_close' and vid!='V4') or (prop=='dining_phone' and vid!='V3')
        if ob.name in ('Phone rounded body','Phone screen','Phone earpiece'):ob.hide_render=vid=='V4'
    if vid=='V4':e['look_at']=target
    cam=iso_camera(vid+' · Film camera',e['look_at'],angle,scale);sc.camera=cam;layer.update()
    for key,val in e['objects'].items():e['objects'][key]=projection(cam,[bpy.data.objects[n] for n in val['objects']])
    e['camera_location']=list(cam.location);e['render_seconds']=render(OUT/'gates/B/candidates'/e['file'],cam,16)
choices={'V2':(225,42),'V3':(225,3.8),'V4':(225,.18),'V5':(45,7.5),'V6':(225,15)}
for vid,(ang,scale) in choices.items():
    chosen=next(e for e in report['candidates'] if e['camera_id']==vid and e['z_angle_deg']==ang and e['ortho_scale']==scale)
    reason=report['selected'][vid]['reason']
    if vid=='V6':reason='NW exposes the open TV cabinet and keeps the south glazing in the shot; scale 15 leaves an outgoing-tunnel corridor.'
    chosen['reason']=reason;report['selected'][vid]=chosen
    iso_camera(vid+' · Film camera',chosen['look_at'],ang,scale)
# South glazing target: all four actual door glass panes, not the first unrelated upper glazing part.
apply_v1_cut(225);layer.update()
cam=bpy.data.objects['V6 · Film camera']
glazing=[o for o in sc.objects if o.name.startswith('阳台推拉门') and 'glass' in o.name and 'continuous full height' in o.name and 8.5<draw(center(o))[1]<9.1]
print('SOUTH GLASS',[(o.name,draw(center(o))) for o in glazing],flush=True)
if glazing:
    report['selected']['V6']['objects']['south_window']=projection(cam,glazing)
for vid,e in report['selected'].items():
    for n,o in e['objects'].items():
        if n=='house_roof_extent':continue
        assert o['in_frame'],(vid,n,'out of frame')
area=report['selected']['V4']['objects']['phone_screen']['size_px']
report['phone_screen_frame_area_ratio']=area[0]*area[1]/(1080*1920)
assert report['phone_screen_frame_area_ratio']>.5
report['status']='PASS';report['notes']=['V4 uses the existing handset geometry on a shot-specific tilted stand on the coffee table.','S02 and S08 retain the same flat phone and same family blocking.','Higher garment neckline closes exposed shoulder gaps.','Trials retain source daylight only; production lighting is not approved by these previews.']
dump(OUT/'gates/B/framing_report.json',report)
layout=json.loads((ROOT/'scene/layout.json').read_text())
for v in layout['film_cameras']:
    if v['id'] in choices:
        e=report['selected'][v['id']];v.update(rot_z_deg=e['z_angle_deg'],look_at=e['look_at'],scale=e['ortho_scale'],ortho_scale=e['ortho_scale'])
dump(ROOT/'scene/layout.json',layout)
for ob in sc.objects:
    if ob.get('shot_prop') or ob.get('film_role') in ('remote_tower','remote_window'):ob.hide_render=True
sc.camera=bpy.data.objects['V1 · Film locked living room'];save('B')
state=json.loads(STATE.read_text());state.update(completed_stages=['A','B'],status='passed');dump(STATE,state)
print('B PASS',report['phone_screen_frame_area_ratio'],flush=True)
