"""Stage B: 60 real portrait camera trials plus V1a, with explicit selection."""
import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
sc=bpy.data.scenes['Larktun Film'];bpy.context.window.scene=sc;layer=full_layer()
sc.render.engine='BLENDER_EEVEE';sc.eevee.use_raytracing=True  # Blender 5.2 engine identifier.
sc.eevee.use_fast_gi=True;sc.eevee.fast_gi_distance=.35
sc.render.resolution_x=1080;sc.render.resolution_y=1920;sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=sc.render.pixel_aspect_y=1

props=collection('FILM · Shot-specific staging');ns=helpers(props)
tower=collection('FILM · Original abstract remote tower')
dark=material('FILM remote architecture graphite','141A25',.8)
panel=material('FILM remote architecture panels','262D39',.62,.0,.3)
for name,p,size in [('central',(14.5,14.5,0),(3.2,3.2,9.8)),('offset wing',(17.6,15.4,0),(1.1,2.3,7.4)),
                     ('base',(14.2,14.2,-.12),(4.8,3.8,.18))]:
    ob=ns['box']('REMOTE · '+name,*p,*size,dark,.06,tower);ob['film_role']='remote_tower'
for row in range(7):
    for col in range(3):
        ob=ns['box'](f'REMOTE · blank window {row}-{col}',14.68+col*.95,14.47,.52+row*1.25,.72,.025,.72,panel,.012,tower)
        ob['film_role']='remote_window';ob['window_row']=row;ob['window_col']=col

phone_originals=[o for o in sc.objects if o.name in ('Phone rounded body','Phone screen','Phone earpiece')]
assert len(phone_originals)==3
old=center(bpy.data.objects['Phone rounded body'])
close_parent=bpy.data.objects.new('SHOT PHONE · close-up display stand',None);props.objects.link(close_parent)
close_parent.location=loc((5.4085,6.3265,.485));close_parent.rotation_euler=(Euler((math.radians(54.7356),0,math.radians(225))).to_matrix()@Matrix.Rotation(math.pi,3,'Z')).to_euler()
close_parts=[];dining_parts=[]
for src in phone_originals:
    ob=src.copy();ob.data=src.data.copy();ob.name='SHOT PHONE · '+src.name;props.objects.link(ob)
    ob.matrix_world=Matrix.Translation(-old)@src.matrix_world;ob.parent=close_parent
    ob['shot_prop']='phone_close';ob['film_base_hide']=False;ob['film_role']='phone_close'
    close_parts.append(ob)
    dupe=src.copy();dupe.data=src.data.copy();dupe.name='S06 PHONE · '+src.name;props.objects.link(dupe)
    dupe.matrix_world=Matrix.Translation(loc((5.55,1.60,.769))-old)@src.matrix_world
    dupe['shot_prop']='dining_phone';dupe['film_base_hide']=False;dining_parts.append(dupe)
ns['box']('SHOT PHONE · stand base',5.35,6.27,.403,.12,.12,.013,'dark',.008,props)['shot_prop']='phone_close'
stand=ns['box']('SHOT PHONE · stand support',5.423,6.343,.417,.013,.022,.048,'dark',.005,props);stand['shot_prop']='phone_close'
bill_originals=[o for o in sc.objects if o.name.startswith(('Casual folded bill','Bill printed rule'))]
bill_c=center(bpy.data.objects['Casual folded bill'])
for src in bill_originals:
    ob=src.copy();ob.data=src.data.copy();ob.name='S06 PAPER · '+src.name;props.objects.link(ob)
    ob.matrix_world=Matrix.Translation(loc((5.89,1.60,.756)))@Matrix.Diagonal((1.6,1.6,1,1))@Matrix.Translation(-bill_c)@src.matrix_world
    ob['shot_prop']='dining_phone';ob['film_base_hide']=False;dining_parts.append(ob)
layer.update()
phone_screen=next(o for o in close_parts if o.name.endswith('Phone screen'))
phone_target=center(phone_screen)-Euler((math.radians(54.7356),0,math.radians(225))).to_matrix()@Vector((0,.010,0))
target_by_id={'V2':(16.1,16.0,3.0),'V3':(5.3,1.6,.78),'V4':draw(phone_target),
              'V5':(11.7,6.2,1.1),'V6':(6.8,8.3,1.15)}
scales={'V2':(42,52,62),'V3':(3.1,3.8,4.5),'V4':(.16,.18,.22),'V5':(7.5,9.5,11.5),'V6':(15,19,23)}
target_objs={
 'V2':{'C1':bpy.data.objects['C1 camera housing'],'C2':bpy.data.objects['C2 camera housing'],'C3':bpy.data.objects['C3 camera housing'],
       'house_roof_extent':[bpy.data.objects['R03 ceiling'],bpy.data.objects['R07 ceiling'],bpy.data.objects['R12 ceiling'],bpy.data.objects['R09 ceiling']],
       'remote_tower':bpy.data.objects['REMOTE · central']},
 'V3':{'dining_table':bpy.data.objects['R03 · 餐桌 solid top'],'bill':bpy.data.objects['S06 PAPER · Casual folded bill'],
       'phone':bpy.data.objects['S06 PHONE · Phone screen']},
 'V4':{'phone_screen':phone_screen,'phone_body':next(o for o in close_parts if o.name.endswith('Phone rounded body'))},
 'V5':{'bed':bpy.data.objects['R12 · 儿童床 1.2m mattress'],'C3':bpy.data.objects['C3 camera housing'],
       'night_lamp':next(o for o in sc.objects if o.name.startswith('Child night lamp') and 'shade' in o.name.lower())},
 'V6':{'south_window':next(o for o in sc.objects if o.name.startswith('客厅推拉门') and 'continuous full height' in o.name and 'glass' in o.name),
       'TV_cabinet':bpy.data.objects['FILM TV cabinet / top'],'D1':next(o for o in sc.objects if o.get('device_id')=='D1' and o.get('larktun_role')=='network_device')},
}

def visibility(vid,angle):
    hidden=focus_cut('R12' if vid=='V5' else 'R03',angle) if vid in ('V3','V5') else apply_v1_cut(angle)
    for ob in tower.objects:ob.hide_render=vid!='V2'
    for ob in props.objects:
        prop=ob.get('shot_prop')
        if prop:ob.hide_render=(prop=='phone_close' and vid!='V4') or (prop=='dining_phone' and vid!='V3')
    for ob in phone_originals:ob.hide_render=vid=='V4'
    if vid=='V2':
        # Overview retains all room contents and floor plates. Only near exterior
        # wall faces and ceiling are cut. Roof extents are measured from ceilings,
        # which remain excluded from rendering as required.
        for ob in sc.objects:
            if ob.type in {'CAMERA','LIGHT'} or ob.get('shot_prop'):continue
            if not ob.get('film_retired') and not ob.get('film_base_hide'):ob.hide_render=False
        manifest=json.loads((ROOT/'renders/v1_framing/visibility_groups.json').read_text())
        near={3 if angle in (45,135) else 2,1 if angle in (45,315) else 0}
        import re
        hidden=[]
        for name,g in manifest.items():
            match=re.search(r'Wall W(\d+)',name)
            if match and int(match.group(1)) in near:
                hidden.append(name)
                for n in g['objects']:
                    if n in bpy.data.objects:bpy.data.objects[n].hide_render=True
    layer.update();return hidden

report={'gate':'B','status':'candidate_review','resolution':[1080,1920],
        'method':'Direct Euler assignment; world_to_camera_view, in_frame and render_enabled reported separately.',
        'candidates':[],'selected':{}}
for vid in ('V2','V3','V4','V5','V6'):
    camera=iso_camera(vid+' · Film camera',target_by_id[vid],225,scales[vid][1]);sc.camera=camera
    for angle in (45,135,225,315):
        hidden=visibility(vid,angle)
        for scale in scales[vid]:
            iso_camera(camera.name,target_by_id[vid],angle,scale);layer.update()
            file=f'{vid}_Z{angle}_S{scale:g}.png'
            data={k:projection(camera,v) for k,v in target_objs[vid].items()}
            if vid=='V2':
                data['house_roof_extent']['render_enabled']=False
                data['house_roof_extent']['note']='Ceiling geometry is a non-rendering footprint measurement, not a physical roof added to the model.'
            entry={'camera_id':vid,'z_angle_deg':angle,'ortho_scale':scale,'look_at':list(target_by_id[vid]),
                   'camera_location':list(camera.location),'camera_rotation_euler_deg':[math.degrees(v) for v in camera.rotation_euler],
                   'world_coverage_m':{'horizontal':scale*.5625,'vertical':scale},'hidden_collections':hidden,'objects':data,'file':file}
            entry['render_seconds']=render(OUT/'gates/B/candidates'/file,camera,16)
            report['candidates'].append(entry)
            dump(OUT/'gates/B/framing_report.json',report)
            print('B CANDIDATE',file,flush=True)

# These choices are validated in the candidates and then visually inspected.
choices={'V2':(225,42),'V3':(225,3.8),'V4':(225,.18),'V5':(45,7.5),'V6':(225,15)}
reasons={
 'V2':'NW retains camera mounts and frames the whole home beneath the original remote tower. The fixed aim also supports the S04 scale-only push to the tower.',
 'V3':'NW shows the dining tabletop, original-paper bill copy and original-phone copy together with useful margins.',
 'V4':'NW faces the same physical phone geometry on a small angled coffee-table stand. At scale .18, the screen occupies more than half of the image area.',
 'V5':'SE retains the north wall supporting C3 and the child headboard, and frames the bed and night lamp together.',
 'V6':'NW retains the full south glazing and exposes the open cabinet face containing D1. Scale 15 leaves room for the outgoing tunnel.',
}
for vid,(angle,scale) in choices.items():
    chosen=next(f for f in report['candidates'] if f['camera_id']==vid and f['z_angle_deg']==angle and f['ortho_scale']==scale)
    chosen['reason']=reasons[vid];report['selected'][vid]=chosen
    iso_camera(vid+' · Film camera',target_by_id[vid],angle,scale)
v1a=iso_camera('V1a · Film hook',(8.34,3.52,2.35),225,1.6)
visibility('V1a',225);sc.camera=v1a;layer.update()
report['V1a']={'look_at':[8.34,3.52,2.35],'z_angle_deg':225,'ortho_scale':1.6,
               'camera_location':list(v1a.location),'camera_rotation_euler_deg':[math.degrees(v) for v in v1a.rotation_euler],
               'objects':{'C1':projection(v1a,bpy.data.objects['C1 camera housing'])}}
render(OUT/'gates/B/V1a_start.png',v1a,32)
v1a.data.ortho_scale=18;layer.update()
report['V1a']['end_at_scale_18']={k:projection(v1a,bpy.data.objects[n]) for k,n in {'C1':'C1 camera housing','sofa':'R07 · 三人沙发 lower upholstery','TV':'R07 · 电视 65" reflective screen'}.items()}
render(OUT/'gates/B/V1a_end.png',v1a,32);v1a.data.ortho_scale=1.6
layout=json.loads((ROOT/'scene/layout.json').read_text())
for v in layout['film_cameras']:
    if v['id'] in choices:
        angle,scale=choices[v['id']];v.update(type='ISO',rot_x_deg=54.7356,rot_z_deg=angle,look_at=list(target_by_id[v['id']]),scale=scale,ortho_scale=scale)
layout['film_cameras'].append(dict(id='V1a',name='C1 钩子特写',type='ISO',look_at=[8.34,3.52,2.35],rot_x_deg=54.7356,rot_z_deg=225,scale=1.6,scale_end=18,shots=['S01']))
dump(ROOT/'scene/layout.json',layout)
visibility('V1',225);sc.camera=bpy.data.objects['V1 · Film locked living room']
save('B');dump(OUT/'gates/B/framing_report.json',report)
print('STAGE B CANDIDATES COMPLETE',flush=True)
