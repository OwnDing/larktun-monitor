"""Shared Blender helpers. Coordinates in this package are east/south/up metres."""
import ast
import bpy
import hashlib
import itertools
import json
import math
import random
from pathlib import Path
from mathutils import Vector, Euler, Matrix
from bpy_extras.object_utils import world_to_camera_view
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'out'
HOME = ROOT / 'Larktun_Home.blend'
FILM = ROOT / 'Larktun_Film.blend'
STATE = ROOT / 'film/production_state.json'


def dump(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def loc(p): return Vector((p[0], -p[1], p[2]))
def draw(p): return [p[0], -p[1], p[2]]


def collection(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def helpers(coll):
    # Reuse only function definitions from the house's modelling library.
    # No top-level construction, scene reset, material setup or save is executed.
    ns = dict(bpy=bpy, math=math, json=json, random=random, Vector=Vector,
              Euler=Euler, Path=Path, sin=math.sin, cos=math.cos, pi=math.pi,
              sqrt=math.sqrt, SC=bpy.context.scene, C=coll, RNG=random.Random(91313))
    ns['M'] = {m.name: m for m in bpy.data.materials}
    for key, name in {'screen':'Standby screen · deep charcoal',
                      'led':'LED · mint status','warm':'Lamp · warm diffuser',
                      'glass':'Clear glazing · physical transmission',
                      'frosted':'Privacy satin glass','mirror':'Silver mirror',
                      'sheer':'Sheer curtain · woven linen'}.items():
        if name in bpy.data.materials: ns['M'][key] = bpy.data.materials[name]
    tree = ast.parse((ROOT / 'blender/build_home.py').read_text())
    defs = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)], type_ignores=[])
    exec(compile(defs, 'house_function_library', 'exec'), ns)
    return ns


def linear(h):
    a = [int(h.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in a)+(1,)


def material(name, color, rough=.7, emit=0, metal=0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = linear(color); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = linear(color)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Emission Color'].default_value = linear(color)
    b.inputs['Emission Strength'].default_value = emit
    return m


def bezier(name, points, radius, mat, coll, cyclic=False):
    data = bpy.data.curves.new(name, 'CURVE'); data.dimensions='3D'
    data.resolution_u=16; data.bevel_depth=radius; data.bevel_resolution=4
    sp=data.splines.new('BEZIER'); sp.bezier_points.add(len(points)-1)
    for v,p in zip(sp.bezier_points,points):
        v.co=loc(p); v.handle_left_type=v.handle_right_type='AUTO'
    sp.use_cyclic_u=cyclic
    o=bpy.data.objects.new(name,data); coll.objects.link(o); data.materials.append(mat)
    return o


def iso_camera(name, target, angle, scale, distance=40):
    assert angle in (45,135,225,315)
    o=bpy.data.objects.get(name)
    if o is None:
        d=bpy.data.cameras.new(name); o=bpy.data.objects.new(name,d)
        collection('FILM · Cameras').objects.link(o)
    o.rotation_mode='XYZ'
    o.rotation_euler=(math.radians(54.7356),0,math.radians(angle))
    o.location=loc(target)+o.rotation_euler.to_matrix()@Vector((0,0,distance))
    o.data.type='ORTHO'; o.data.ortho_scale=scale
    o.data.clip_start=.015; o.data.clip_end=250; o.data.sensor_fit='AUTO'
    o['look_at_drawing']=list(target); o['rot_z_deg']=angle
    return o


def full_layer():
    sc=bpy.context.scene
    layer=sc.view_layers.get('02 · FULL INTERIOR') or sc.view_layers[0]
    for vl in sc.view_layers: vl.use=vl==layer
    bpy.context.window.view_layer=layer
    excluded=('01a ', '01b ', '01d ', '01e ', '01i ', '05 · Guides')
    def walk(lc):
        for ch in lc.children:
            ch.exclude=ch.name.startswith(excluded); walk(ch)
    walk(layer.layer_collection); layer.update()
    return layer


def bounds(o):
    if o.hide_render or o.name not in bpy.context.view_layer.objects:
        return [o.matrix_world@Vector(p) for p in o.bound_box]
    dg=bpy.context.evaluated_depsgraph_get(); ev=o.evaluated_get(dg)
    if o.type in {'CURVE','FONT','SURFACE'}:
        mesh=ev.to_mesh(); vs=np.empty(len(mesh.vertices)*3,dtype=np.float32)
        mesh.vertices.foreach_get('co',vs); vs=vs.reshape((-1,3))
        lo,hi=vs.min(axis=0),vs.max(axis=0)
        points=[ev.matrix_world@Vector(v) for v in itertools.product(*zip(lo,hi))]
        ev.to_mesh_clear(); return points
    return [ev.matrix_world@Vector(p) for p in ev.bound_box]


def center(o): return sum(bounds(o),Vector())/8


def projection(camera, objects):
    if not isinstance(objects,(list,tuple)): objects=[objects]
    sc=bpy.context.scene
    points=[p for o in objects for p in bounds(o)]
    c=sum(points,Vector())/len(points); ndc=world_to_camera_view(sc,camera,c)
    ps=[world_to_camera_view(sc,camera,p) for p in points]
    lo=[min(p[i] for p in ps) for i in range(3)]; hi=[max(p[i] for p in ps) for i in range(3)]
    enabled=all(not o.hide_render and o.name in bpy.context.view_layer.objects and all(not c.hide_render for c in o.users_collection) for o in objects)
    return dict(in_frame=bool(0<=ndc.x<=1 and 0<=ndc.y<=1 and 0<ndc.z<camera.data.clip_end),
                render_enabled=enabled, fully_in_frame=bool(0<=lo[0]<=hi[0]<=1 and 0<=lo[1]<=hi[1]<=1 and lo[2]>0),
                projected_bounds_ndc=[lo[0],lo[1],hi[0],hi[1]],anchor_ndc=list(ndc),
                size_px=[(hi[0]-lo[0])*1080,(hi[1]-lo[1])*1920],
                objects=[o.name for o in objects])


def apply_v1_cut(angle=225):
    """Replay audited directional masks; added film assets use film_room tags."""
    report=json.loads((ROOT/'renders/v1_framing/framing_report.json').read_text())
    groups=json.loads((ROOT/'renders/v1_framing/visibility_groups.json').read_text())
    frame=next(f for f in report['frames'] if f['z_angle_deg']==angle)
    hidden={n for g in frame['hidden_collections'] if g in groups for n in groups[g]['objects']}
    for o in bpy.context.scene.objects:
        if o.type in {'CAMERA','LIGHT'}: continue
        if 'film_base_hide' not in o: o['film_base_hide']=o.hide_render
        o.hide_render=bool(o.get('film_retired') or o.get('film_base_hide') or o.name in hidden)
        if o.get('film_room'):
            o.hide_render=bool(o.get('film_retired') or o['film_room'] in frame['hidden_rooms'])
        if o.get('film_role')=='physical_cable': o.hide_render=False
    bpy.context.view_layer.update()
    return frame['hidden_collections']


def focus_cut(room_id, angle):
    """Full-height directional cut relative to the selected room, not the origin."""
    layout=json.loads((ROOT/'scene/layout.json').read_text());r=next(r for r in layout['rooms'] if r['id']==room_id)
    east=angle in (45,135);south=angle in (45,315);sx=1 if east else -1;sy=1 if south else -1
    hidden_rooms=set()
    for other in layout['rooms']:
        if other['id']==room_id:continue
        x=(other['x0']+other['x1'])/2;y=(other['y0']+other['y1'])/2
        tx=sorted(((r['x0']-x)/-sx,(r['x1']-x)/-sx));ty=sorted(((r['y0']-y)/-sy,(r['y1']-y)/-sy))
        if max(tx[0],ty[0],.001)<min(tx[1],ty[1]):hidden_rooms.add(other['id'])
    walls=layout['walls']+[dict(x0=8.52,y0=2.12,x1=9.6,y1=2.24)]
    hidden_walls=set()
    for i,w in enumerate(walls):
        horizontal=w['x1']-w['x0']>w['y1']-w['y0']
        if horizontal:
            if (south and w['y0']>=r['y1']-.05) or (not south and w['y1']<=r['y0']+.15):hidden_walls.add(i)
        elif (east and w['x0']>=r['x1']-.05) or (not east and w['x1']<=r['x0']+.15):hidden_walls.add(i)
    manifest=json.loads((ROOT/'renders/v1_framing/visibility_groups.json').read_text())
    hidden=set();hidden_cols=[]
    import re
    for name,g in manifest.items():
        wall=re.search(r'Wall W(\d+)',name);room=re.search(r'Room (R\d+)',name)
        hide=(wall and int(wall.group(1)) in hidden_walls) or (room and room.group(1) in hidden_rooms)
        if hide:hidden.update(g['objects']);hidden_cols.append(name)
    for ob in bpy.context.scene.objects:
        if ob.type in {'CAMERA','LIGHT'}:continue
        if 'film_base_hide' not in ob:ob['film_base_hide']=ob.hide_render
        ob.hide_render=bool(ob.get('film_retired') or ob.get('film_base_hide') or ob.name in hidden)
        if ob.get('film_room'):ob.hide_render=bool(ob.get('film_retired') or ob['film_room'] in hidden_rooms)
    bpy.context.view_layer.update()
    return sorted(hidden_cols)


def save(stage):
    assert sha(HOME)==json.loads(STATE.read_text())['source_home_sha256']
    bpy.context.scene['film_stage']=stage
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(FILM),compress=True)
    state=json.loads(STATE.read_text()); state.update(stage=stage,status='awaiting_gate')
    dump(STATE,state)


def render(path, camera=None, samples=32):
    import time
    sc=bpy.context.scene
    if camera: sc.camera=camera
    sc.render.resolution_x=1080; sc.render.resolution_y=1920; sc.render.resolution_percentage=100
    sc.render.pixel_aspect_x=sc.render.pixel_aspect_y=1
    sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGBA'
    sc.render.image_settings.color_depth='16'
    if sc.render.engine=='CYCLES':
        sc.cycles.samples=samples
        pref=bpy.context.preferences.addons['cycles'].preferences; pref.compute_device_type='METAL'; pref.get_devices()
        for d in pref.devices: d.use=d.type=='METAL'
    else: sc.eevee.taa_render_samples=samples
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    sc.render.filepath=str(path)
    t=time.monotonic();bpy.ops.render.render(write_still=True,layer=bpy.context.view_layer.name)
    return time.monotonic()-t


def activate_look(name):
    sc=bpy.context.scene;vl=sc.view_layers['LOOK_'+name]
    bpy.context.window.view_layer=vl
    for layer in sc.view_layers:layer.use=layer==vl
    sc.world=vl.world_override;sc.view_settings.exposure=vl['film_exposure']
    if sc.compositing_node_group:
        for n in sc.compositing_node_group.nodes:
            if n.type=='R_LAYERS':n.layer=vl.name
    return vl
