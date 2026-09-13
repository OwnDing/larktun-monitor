"""Read-only geometric occlusion evidence for the five physical cable routes."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

sc=bpy.data.scenes['Larktun Film'];bpy.context.window.scene=sc
full_layer();apply_v1_cut(225);sc.render.resolution_x=1080;sc.render.resolution_y=1920
cam=bpy.data.objects['V1 · Film locked living room'];sc.camera=cam
direction=cam.rotation_euler.to_matrix()@Vector((0,0,-1))
dg=bpy.context.evaluated_depsgraph_get()

def visible(point, target_name):
    origin=point-direction*40;remaining=40.005
    for _ in range(70):
        hit,pos,normal,index,ob,mat=sc.ray_cast(dg,origin,direction,distance=remaining)
        if not hit: return True,None
        if ob.name==target_name: return True,ob.name
        original=ob.original
        skip=original.hide_render or original.get('film_retired')
        if not skip:
            skip=all(m and ('glazing' in m.name.lower() or 'glass' in m.name.lower()) for m in original.data.materials) if hasattr(original.data,'materials') and len(original.data.materials) else False
        if not skip: return False,original.name
        travel=(pos-origin).length+.0001;remaining-=travel;origin=pos+direction*.0001
        if remaining<=0:return True,None
    return False,'ray traversal limit'

result={}
for name in ('C1_D1','C2_D1','C3_D1','D1_D3','D3_D4'):
    ob=bpy.data.objects['CABLE · '+name];bp=ob.data.splines[0].bezier_points
    samples=[];blocks={}
    for a,b in zip(bp,bp[1:]):
        for t in np.linspace(0,1,25):
            t=float(t)
            p=(1-t)**3*a.co+3*(1-t)**2*t*a.handle_right+3*(1-t)*t*t*b.handle_left+t**3*b.co
            p=ob.matrix_world@p;ndc=world_to_camera_view(sc,cam,p)
            inside=0<=ndc.x<=1 and 0<=ndc.y<=1 and ndc.z>0
            vis,block=visible(p,ob.name) if inside else (False,'outside frame')
            if not vis:blocks[block]=blocks.get(block,0)+1
            samples.append({'ndc':list(ndc),'visible':bool(vis)})
    result[name]={'samples':len(samples),'visible_samples':sum(s['visible'] for s in samples),
                  'visible_fraction':sum(s['visible'] for s in samples)/len(samples),
                  'occluders':blocks,'screen_samples':samples}
report=json.loads((OUT/'gates/A/framing_report.json').read_text())
report['cable_occlusion']=result
report['occlusion_method']='Orthographic rays to 25 samples per Bezier segment; skip render-hidden objects and clear glazing; opaque geometry blocks. A visible fraction does not imply the full route is unobstructed.'
report['objects']={k:projection(cam,[bpy.data.objects[n] for n in v['objects']]) for k,v in report['objects'].items()}
report['objects_in_frame']={k:v['in_frame'] for k,v in report['objects'].items()}
report['status']='awaiting_visual_signoff'
dump(OUT/'gates/A/framing_report.json',report)
for k,v in result.items():print(k,round(v['visible_fraction'],3),v['occluders'])
assert sha(HOME)==json.loads(STATE.read_text())['source_home_sha256']
