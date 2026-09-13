import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from motion import install,apply_frame
sc=bpy.data.scenes['Larktun Film'];bpy.context.window.scene=sc;install()
# Barely luminous dark architectural surface keeps the abstract tower readable.
mat=bpy.data.materials['FILM remote architecture graphite'];b=mat.node_tree.nodes.get('Principled BSDF');b.inputs['Emission Color'].default_value=linear('141A25');b.inputs['Emission Strength'].default_value=2
frame=bpy.data.objects['S04 / pulsing red frame']
for p in frame.data.splines[0].bezier_points:p.handle_left_type=p.handle_right_type='VECTOR'
outer=bpy.data.objects['S09 CYAN / private tunnel'];mat=outer.active_material.copy();mat.name='S09 translucent tunnel envelope';outer.data.materials.clear();outer.data.materials.append(mat)
b=mat.node_tree.nodes.get('Principled BSDF');b.inputs['Alpha'].default_value=.13
for n in mat.node_tree.nodes:
    if n.type=='MATH' and n.operation=='MULTIPLY':n.inputs[1].default_value=1.2
core=bpy.data.objects.new('S09 CYAN / moving light core',outer.data.copy());bpy.data.collections['FILM · Data flow geometry'].objects.link(core);core.data.bevel_depth=.035;core.data.materials.clear();core.data.materials.append(bpy.data.materials['FLOW CYAN / 2FE0C8']);core['film_shots']='S09';core['film_role']='tunnel_core'
for shot,f in [('S03',181),('S04',271)]:
    sc.frame_set(f);apply_frame(sc);render(OUT/f'gates/E/{shot}_{f:04d}.png',sc.camera,32)
for shot,f in [('S04',340),('S09',770)]:
    sc.frame_set(f);apply_frame(sc);render(OUT/f'gates/E/motion_checks/{shot}_{f:04d}.png',sc.camera,32)
sc.frame_set(91);apply_frame(sc);save('E')
print('E POLISH COMPLETE',flush=True)
