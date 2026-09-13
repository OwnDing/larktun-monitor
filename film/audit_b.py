"""Recheck all B projections from the correct target IDs and evaluated visibility."""
import sys,ast
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from characters import build_family
sc=bpy.data.scenes['Larktun Film'];bpy.context.window.scene=sc;layer=full_layer()
for pid in ('P1','P2','P3'):
    for ob in list(bpy.data.collections['FILM · '+pid+' MakeHuman character'].objects):bpy.data.objects.remove(ob,do_unlink=True)
build_family()
props=bpy.data.collections['FILM · Shot-specific staging'];tower=bpy.data.collections['FILM · Original abstract remote tower']
phone_originals=[bpy.data.objects[n] for n in ('Phone rounded body','Phone screen','Phone earpiece')]
defs=[n for n in ast.parse((ROOT/'film/stage_b.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='visibility']
exec(compile(ast.Module(body=defs,type_ignores=[]),'visibility','exec'))
report=json.loads((OUT/'gates/B/framing_report.json').read_text())
south=[o for o in sc.objects if o.name.startswith('客厅推拉门') and 'glass / continuous full height' in o.name]
assert len(south)==4
for entry in report['candidates']:
    vid=entry['camera_id'];visibility(vid,entry['z_angle_deg'])
    cam=iso_camera(vid+' · Film camera',entry['look_at'],entry['z_angle_deg'],entry['ortho_scale']);layer.update()
    for name,v in entry['objects'].items():
        obs=south if name=='south_window' else [bpy.data.objects[n] for n in v['objects']]
        entry['objects'][name]=projection(cam,obs)
    selected=report['selected'][vid]
    if selected['file']==entry['file']:
        entry['reason']=selected['reason'];report['selected'][vid]=entry
        assert all(v['in_frame'] and v['render_enabled'] for n,v in entry['objects'].items() if n!='house_roof_extent'),(vid,entry['objects'])
        if vid in ('V3','V6'):entry['render_seconds']=render(OUT/'gates/B/candidates'/entry['file'],cam,32)
for vid,entry in report['selected'].items():iso_camera(vid+' · Film camera',entry['look_at'],entry['z_angle_deg'],entry['ortho_scale'])
visibility('V1a',225);cam=bpy.data.objects['V1a · Film hook'];cam.data.ortho_scale=1.6;layer.update()
report['V1a']['objects']['C1']=projection(cam,bpy.data.objects['C1 camera housing'])
cam.data.ortho_scale=18;layer.update()
report['V1a']['end_at_scale_18']={n:projection(cam,bpy.data.objects[o]) for n,o in {'C1':'C1 camera housing','TV':'R07 · 电视 65" reflective screen','sofa':'R07 · 三人沙发 lower upholstery'}.items()}
render(OUT/'gates/B/V1a_end.png',cam,32);cam.data.ortho_scale=1.6
visibility('V1',225);sc.camera=bpy.data.objects['V1 · Film locked living room'];save('B')
report['status']='PASS';report['notes'].append('The north utility balcony door was initially mistaken for the south living-room slider. All 60 projections have been recomputed using all four correct living-room glass panes. Hidden/excluded bounds use source transforms to avoid stale evaluated data. Hair uses a continuous anatomical scalp shell, replacing the segmented helper mesh.')
dump(OUT/'gates/B/framing_report.json',report)
state=json.loads(STATE.read_text());state.update(completed_stages=['A','B'],status='passed');dump(STATE,state)
print('GATE B PASS',flush=True)
