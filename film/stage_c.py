"""Three independent, fixed light banks and per-View-Layer World overrides."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
sc=bpy.data.scenes['Larktun Film'];bpy.context.window.scene=sc
sc.render.engine='BLENDER_EEVEE';sc.eevee.use_raytracing=True;sc.eevee.use_fast_gi=True;sc.eevee.fast_gi_distance=.35
sc.eevee.taa_render_samples=64
try:sc.eevee.shadow_pool_size='1024'
except TypeError:pass
sc.view_settings.view_transform='AgX'
# Film-only sofa colour, preserving the source fabric's procedural weave.
sofa=bpy.data.materials['blue']
base=linear('3E4C6D');sofa.diffuse_color=base
for node in sofa.node_tree.nodes:
    if node.type=='BSDF_PRINCIPLED':node.inputs['Base Color'].default_value=base
    if node.type=='VALTORGB':
        node.color_ramp.elements[0].color=tuple(v*.87 for v in base[:3])+(1,)
        node.color_ramp.elements[1].color=tuple(v*1.13 for v in base[:3])+(1,)

def light(coll,name,kind,power,color,position,target=None,size=1):
    d=bpy.data.lights.new(name,kind);d.energy=power;d.color=linear(color)[:3]
    if kind=='AREA':d.shape='DISK';d.size=size
    else:d.shadow_soft_size=size
    ob=bpy.data.objects.new(name,d);coll.objects.link(ob);ob.location=loc(position)
    if target:ob.rotation_euler=(loc(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob

def kelvin(k):
    # Tanner-Helland temperature-to-sRGB approximation, used only for fixture colour.
    t=k/100
    r=255 if t<=66 else 329.698727446*(t-60)**-.1332047592
    g=99.4708025861*math.log(t)-161.1195681661 if t<=66 else 288.1221695283*(t-60)**-.0755148492
    b=255 if t>=66 else (0 if t<=19 else 138.5177312231*math.log(t-10)-305.0447927307)
    return ''.join(f'{min(255,max(0,round(v))):02X}' for v in (r,g,b))
looks={
 'DARK':dict(strength=.08,world='05070E',exposure=-.6,key=80,color='BCCCE6',pos=(1,-3,8),aim=(6,4,1)),
 'DUSK':dict(strength=.12,world='D4DDE8',exposure=-.2,key=220,color=kelvin(3400),pos=(-1,3.7,4.2),aim=(6,4.5,.8)),
 'NIGHT':dict(strength=.06,world='101829',exposure=0,key=45,color='3A5580',pos=(14.6,6,3.1),aim=(11.6,6.3,.65)),
}
for name,cfg in looks.items():
    coll=collection('LOOK_'+name+' · fixed lights')
    light(coll,'LOOK_'+name+' key','AREA',cfg['key'],cfg['color'],cfg['pos'],cfg['aim'],4 if name!='NIGHT' else 2)
    if name=='DUSK':
        for room,pos,target,power,size in [('dining',(5.3,1.6,2.15),(5.3,1.6,.6),50,.35),('living',(6.1,6.5,2.65),(6,6,.5),65,1.8),('foyer',(7.5,1.5,2.65),(7.5,1.5,.5),40,1),('child',(11.5,6.2,2.65),(11.5,6.2,.5),45,1.2)]:
            light(coll,'LOOK_DUSK '+room+' practical','AREA',power,kelvin(2700),pos,target,size)
    if name=='NIGHT':
        lamp=next(o for o in sc.objects if o.name.startswith('Child night lamp') and 'shade' in o.name.lower())
        p=draw(center(lamp));p[2]+=.02
        light(coll,'LOOK_NIGHT child night lamp','POINT',25,'FFC061',p,size=.15)
    world=bpy.data.worlds.new('LOOK_'+name+' world');world.use_nodes=True
    bg=world.node_tree.nodes.get('Background');bg.inputs[0].default_value=linear(cfg['world']);bg.inputs[1].default_value=cfg['strength']
    layer=sc.view_layers.new('LOOK_'+name);layer.world_override=world;layer['film_exposure']=cfg['exposure']
    def exclude(lc):
        for ch in lc.children:
            ch.exclude=ch.name.startswith(('01a ','01b ','01d ','01e ','01i ','05 ·','06 · LIGHTING')) or (ch.name.startswith('LOOK_') and ch.name!=coll.name)
            exclude(ch)
    exclude(layer.layer_collection)
for layer in list(sc.view_layers):
    if not layer.name.startswith('LOOK_'):sc.view_layers.remove(layer)
# Existing warm diffuser is kept at a modest neutral level; only fixtures illuminate rooms.
# Separate night-lamp diffuser avoids warm lamps in other rooms glowing at night.
for name in ('LED · mint status',):
    if name in bpy.data.materials:
        n=bpy.data.materials[name].node_tree.nodes.get('Principled BSDF')
        if n:n.inputs['Emission Color'].default_value=linear('2FE0C8')

def activate(name):
    vl=sc.view_layers['LOOK_'+name];bpy.context.window.view_layer=vl
    for l in sc.view_layers:l.use=l==vl
    sc.view_settings.exposure=vl['film_exposure'];sc.world=vl.world_override
    return vl
results={}
for name in looks:
    layer=activate(name)
    if name=='NIGHT':focus_cut('R12',45);cam=bpy.data.objects['V5 · Film camera']
    else:apply_v1_cut(225);cam=bpy.data.objects['V1 · Film locked living room']
    for ob in sc.objects:
        if ob.get('shot_prop') or ob.get('film_role') in ('remote_tower','remote_window'):ob.hide_render=True
    seconds=render(OUT/'gates/C'/('LOOK_'+name+'.png'),cam,32)
    results[name]=dict(**looks[name],view_layer=layer.name,render_seconds=seconds)
activate('DUSK');apply_v1_cut(225);sc.camera=bpy.data.objects['V1 · Film locked living room']
for ob in sc.objects:
    if ob.get('shot_prop') or ob.get('film_role') in ('remote_tower','remote_window'):ob.hide_render=True
save('C');dump(OUT/'gates/C/lighting_settings.json',results)
print('C PREVIEWS COMPLETE',flush=True)
