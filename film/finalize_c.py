import sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
sc=bpy.data.scenes['Larktun Film'];bpy.context.window.scene=sc
old=OUT/'gates/C/iteration_02';old.mkdir(exist_ok=True)
for p in (OUT/'gates/C').glob('*.png'):shutil.copy2(p,old/p.name)
shutil.copy2(OUT/'gates/C/histogram_report.json',old/'histogram_report.json')
# A neutral white presentation floor replaces the original cream gallery backdrop.
# This is not a room surface; the scene geometry and all physical room materials stay intact.
mat=bpy.data.materials['Gallery ground'];mat.diffuse_color=(1,1,1,1)
mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(1,1,1,1)
key=bpy.data.objects['LOOK_DARK key'];key.location=loc((3.2,3,4.3));key.rotation_euler=(loc((6,5.7,.9))-key.location).to_track_quat('-Z','Y').to_euler()
for name in ('DARK','DUSK','NIGHT'):
    vl=sc.view_layers['LOOK_'+name];bpy.context.window.view_layer=vl
    for l in sc.view_layers:l.use=l==vl
    sc.world=vl.world_override;sc.view_settings.exposure=vl['film_exposure']
    if name=='NIGHT':focus_cut('R12',45);cam=bpy.data.objects['V5 · Film camera']
    else:apply_v1_cut(225);cam=bpy.data.objects['V1 · Film locked living room']
    for ob in sc.objects:
        if ob.get('shot_prop') or ob.get('film_role') in ('remote_tower','remote_window'):ob.hide_render=True
    render(OUT/f'gates/C/LOOK_{name}.png',cam,32)
vl=sc.view_layers['LOOK_DUSK'];bpy.context.window.view_layer=vl
for l in sc.view_layers:l.use=l==vl
sc.world=vl.world_override;sc.view_settings.exposure=-.2;apply_v1_cut(225)
for ob in sc.objects:
    if ob.get('shot_prop') or ob.get('film_role') in ('remote_tower','remote_window'):ob.hide_render=True
sc.camera=bpy.data.objects['V1 · Film locked living room'];save('C')
settings={}
for vl in sc.view_layers:
    world=vl.world_override;bg=world.node_tree.nodes.get('Background')
    coll=bpy.data.collections[vl.name+' · fixed lights']
    settings[vl.name]=dict(world_color_linear=list(bg.inputs[0].default_value),world_strength=bg.inputs[1].default_value,exposure=vl['film_exposure'],lights=[dict(name=o.name,power_W=o.data.energy,position_drawing=draw(o.location),color_linear=list(o.data.color),shadow=o.data.use_shadow) for o in coll.objects])
dump(OUT/'gates/C/lighting_settings.json',settings)
print('C FINAL PREVIEWS COMPLETE',flush=True)
