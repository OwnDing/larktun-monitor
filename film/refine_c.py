import sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
sc=bpy.data.scenes['Larktun Film'];bpy.context.window.scene=sc
old=OUT/'gates/C/iteration_01';old.mkdir(exist_ok=True)
for p in (OUT/'gates/C').glob('*.png'):shutil.copy2(p,old/p.name)
shutil.copy2(OUT/'gates/C/histogram_report.json',old/'histogram_report.json')
for vl in sc.view_layers:
    def walk(lc):
        for ch in lc.children:
            if ch.name.startswith('LOOK_'):ch.exclude=not ch.name.startswith(vl.name+' ')
            walk(ch)
    walk(vl.layer_collection)
world=bpy.data.worlds['LOOK_DUSK world'];world.node_tree.nodes.get('Background').inputs[0].default_value=(1,1,1,1)
key=bpy.data.objects['LOOK_NIGHT key'];key.location=loc((11.6,8.48,2.15));key.rotation_euler=(loc((11.6,6.2,.65))-key.location).to_track_quat('-Z','Y').to_euler()
bpy.data.lights['LOOK_NIGHT child night lamp'].use_shadow=False
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
sc.camera=bpy.data.objects['V1 · Film locked living room'];save('C')
print('C REFINE COMPLETE',flush=True)
