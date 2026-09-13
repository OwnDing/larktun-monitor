"""Reconcile legacy drawing annotations with the already-built film scene."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'scene/layout.json'
x=json.loads(path.read_text())
x['meta']['iso_rotation_euler_deg']=[54.7356,0,225]
x['meta']['film_resolution']=[1080,1920]
x['meta']['film_fps']=30
x['meta']['film_frame_range']=[1,1200]
directions={45:'东南上空',135:'东北上空',225:'西北上空',315:'西南上空'}
for c in x['film_cameras']:
    c['azimuth']=directions[c['rot_z_deg']]
    c['ortho_scale']=c['scale']
    if c['id']=='V2':
        c['shots']=['S03','S04','S07']
        c['scale_keyframes']=[{'frame':181,'value':42},{'frame':271,'value':42},
                              {'frame':360,'value':12},{'frame':541,'value':42}]
    if c['id']=='V1a':c['scale_keyframes']=[{'frame':1,'value':1.6},{'frame':90,'value':18}]
x.setdefault('source_house_cable_guides',x['cables'])
x['cables']=[dict(src=c['id'].split('_')[0],dst=c['id'].split('_')[1],
    path=[p[:2] for p in c['path']],physical_cable_id=c['id'],
    note='Plan-view projection of the film cable. Full 3D Bezier control points are in physical_cables.')
    for c in x['physical_cables']]
x.setdefault('source_storyboard_blocking_S12',x['blocking']['S12'])
x['blocking']['S12']=[dict(person='P3',rig='P3 sleeping rig',anchor='rig root',
    x=11.96,y=6.6,z=.73,rotation_matrix_blender=[[0,1,0],[0,0,1],[1,0,0]],
    pose='MakeHuman side-lying pose with flexed knees and a separate geometric quilt')]
notes={
    'P1':'本片穿一套有体积的家居服，坐餐桌，S02/S08 使用完全相同的轻微头部 idle；未制作旧备注中的通勤服与户外人物。',
    'P2':'本片穿一套有体积的家居服，坐餐桌，S02/S08 使用完全相同的轻微头部 idle；S12 采用儿童独自熟睡，没有哄睡动作。',
    'P3':'餐桌旁的儿童与 S12 熟睡儿童使用同一 MakeHuman 体型；S12 使用独立侧卧骨架副本和实体被子。',
    'P4':'文档可选角色，本片未使用。'}
for person in x['people']:
    person.setdefault('source_storyboard_note',person['note'])
    person['note']=notes[person['id']]
    person['enabled_in_film']=person['id']!='P4'
path.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
print('Film camera labels, cable plan projections and actual S12 blocking reconciled.')
