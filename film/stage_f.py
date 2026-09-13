"""Attach the extracted animated UI as real image sequences on independent screens."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from motion import install,apply_frame
sc=bpy.data.scenes['Larktun Film'];bpy.context.window.scene=sc
for name,start,count in [('S05',361,90),('S10',811,90),('PAYMENT',451,1)]:
    mat=material('FILM UI '+name,'FFFFFF',.4,2.5);mat.use_fake_user=True;nt=mat.node_tree;
    for old in list(nt.nodes):
        if old.type=='TEX_IMAGE':nt.nodes.remove(old)
    b=nt.nodes.get('Principled BSDF')
    tex=nt.nodes.new('ShaderNodeTexImage');tex.name='Original storyboard SVG / animated screen';tex.image=bpy.data.images.load(str(OUT/f'ui/frames/{name}/0001.png'))
    tex.image.filepath='//out/ui/frames/'+name+'/0001.png'
    if count>1:
        tex.image.source='SEQUENCE';tex.image_user.frame_duration=count;tex.image_user.frame_start=start;tex.image_user.use_auto_refresh=True
    nt.links.new(tex.outputs['Color'],b.inputs['Base Color']);nt.links.new(tex.outputs['Color'],b.inputs['Emission Color']);b.inputs['Emission Strength'].default_value=2.5
    mat['source_svg']='src/scenes_a.py:s05:inner' if name=='S05' else 'src/scenes_b.py:s10:inner' if name=='S10' else 'Original generic payment notification; price placeholder'
for name in ('SHOT PHONE · Phone screen','S06 PHONE · Phone screen'):
    ob=bpy.data.objects[name];me=ob.data;uv=me.uv_layers.active or me.uv_layers.new(name='Phone screen UV')
    lo=[min(v.co[i] for v in me.vertices) for i in range(2)];hi=[max(v.co[i] for v in me.vertices) for i in range(2)]
    for poly in me.polygons:
        for idx in poly.loop_indices:
            v=me.vertices[me.loops[idx].vertex_index].co;xy=[(v[i]-lo[i])/(hi[i]-lo[i]) for i in range(2)]
            if name.startswith('SHOT'):xy=[1-a for a in xy]
            uv.data[idx].uv=xy
install();sc.frame_set(409);apply_frame(sc);save('F')
report={'stage':'F','status':'visual_review','screen_resolution':[1080,2200],'emission_strength':2.5,'source_sequence_frames':{'S05':90,'S10':90,'PAYMENT':1},'previews':[]}
for f in (361,379,409,424,840,811,826,480):
    sc.frame_set(f);apply_frame(sc);seconds=render(OUT/f'gates/F/ui_{f:04d}.png',sc.camera,32)
    report['previews'].append(dict(frame=f,render_seconds=seconds))
dump(OUT/'gates/F/ui_report.json',report)
print('F UI PREVIEWS COMPLETE',flush=True)
