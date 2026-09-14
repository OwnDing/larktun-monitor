"""Scene helpers shared by the Larktun walkthrough scripts.

Drawing coordinates: x east, y south, z up.  Blender = (x, -y, z).
Helpers only change the in-memory scene; Larktun_Home.blend is never saved by them.
"""
import math

import bpy
from mathutils import Matrix, Vector

CUT_LAYER = '01 · CUTAWAY'
FULL_LAYER = '02 · FULL INTERIOR'
FULL_SUFFIX = ' / continuous full height'
LOWER_SUFFIX = ' / lower'  # the same parts cut at 1.15 m for the dollhouse view
SWING_KINDS = {'door leaf', 'hinge', 'lock escutcheon', 'lever', 'keyhole'}

# Hinge axis in drawing coordinates and the Blender Z rotation applied to the leaf.
# Entry door: hinge on the west jamb, opens inward.  Master bedroom door: its hinge
# knuckles sit on the living-room side and a bedside table blocks the other swing.
SWING_DOORS = {
    '入户门': dict(pivot=(7.337, 0.022), open_deg=-80.0),
    '主卧门': dict(pivot=(3.622, 5.007), open_deg=70.0),
    # Built open at 70°, where leaf and sofa bed leave no way into the room; 100° folds it toward the wall.
    '书房门 · corrected access': dict(pivot=(9.6, 2.27), open_deg=30.0),
}

# Two-pane sliders the camera passes through are pocketed (panes hidden inside the
# wall).  The wider sliders keep their panes, stacked on a parallel track.
SLIDERS = {
    '厨房推拉门': dict(axis='v', mode='pocket'),
    '公卫移门': dict(axis='h', mode='pocket'),
    '储藏门': dict(axis='v', mode='pocket'),
    '阳台推拉门': dict(axis='h', mode='stack', moves={1: -0.80}, depth=0.035, hide_verticals=(1,)),
    '客厅推拉门': dict(axis='h', mode='stack', moves={1: -0.84, 2: 0.85}, depth=0.035, hide_verticals=(2,)),
}


def B(x, y, z=0.0):
    return Vector((x, -y, z))


def layer_flags(layer):
    flags = {}

    def walk(lc):
        flags[lc.name] = lc.exclude
        for child in lc.children:
            walk(child)
    walk(layer.layer_collection)
    return flags


def apply_flags(layer, flags):
    root = layer.layer_collection.name

    def walk(lc):
        if lc.name != root and lc.name in flags:
            lc.exclude = flags[lc.name]
        for child in lc.children:
            walk(child)
    walk(layer.layer_collection)


def show_full_interior(scene):
    """Switch the rendering layer to continuous walls, ceilings and upper fittings."""
    layer = scene.view_layers[CUT_LAYER]
    apply_flags(layer, layer_flags(scene.view_layers[FULL_LAYER]))
    return layer


def door_parts(door, kinds, suffix=FULL_SUFFIX):
    out = []
    for o in bpy.data.objects:
        if not o.name.startswith(door + ' ') or suffix not in o.name:
            continue
        if o.name.split(suffix)[0][len(door) + 1:] in kinds:
            out.append(o)
    return out


def rotation_about(pivot_plan, degrees):
    p = B(*pivot_plan)
    return Matrix.Translation(p) @ Matrix.Rotation(math.radians(degrees), 4, 'Z') @ Matrix.Translation(-p)


def rotate_about(objects, pivot_plan, degrees):
    # matrix_basis, not matrix_world: objects from excluded layers carry a stale world matrix.
    m = rotation_about(pivot_plan, degrees)
    for o in objects:
        o.matrix_basis = m @ o.matrix_basis


def hide(o):
    o.hide_render = True
    o.hide_viewport = True


def along(o, axis):
    t = o.matrix_basis.translation
    return t.x if axis == 'h' else -t.y


def open_slider(door, cfg, suffix):
    axis = cfg['axis']

    def ordered(kind):
        return sorted(door_parts(door, {kind}, suffix), key=lambda o: along(o, axis))
    glass, handles, verticals = ordered('glass'), ordered('handle'), ordered('frame vertical')
    assert glass and len(glass) == len(handles), (door, suffix, len(glass), len(handles))
    if cfg['mode'] == 'pocket':
        for o in glass + handles + verticals[1:-1]:
            hide(o)
        return
    for index, shift in cfg['moves'].items():
        depth = cfg['depth']
        delta = Vector((shift, -depth, 0)) if axis == 'h' else Vector((depth, -shift, 0))
        for o in (glass[index], handles[index]):
            o.matrix_basis = Matrix.Translation(delta) @ o.matrix_basis
    for index in cfg['hide_verticals']:
        hide(verticals[index])


def open_sliders(suffixes=(FULL_SUFFIX,)):
    for suffix in suffixes:
        for door, cfg in SLIDERS.items():
            open_slider(door, cfg, suffix)


def swing_parts(door, suffix=FULL_SUFFIX):
    return door_parts(door, SWING_KINDS, suffix)


def open_swing_doors(angles=None, suffixes=(FULL_SUFFIX,)):
    for door, cfg in SWING_DOORS.items():
        deg = cfg['open_deg'] if angles is None else angles.get(door, cfg['open_deg'])
        if deg:
            for suffix in suffixes:
                rotate_about(swing_parts(door, suffix), cfg['pivot'], deg)


def open_doors(angles=None, suffixes=(FULL_SUFFIX,)):
    open_sliders(suffixes)
    open_swing_doors(angles, suffixes)


def configure_eevee(scene, samples=32):
    scene.render.engine = 'BLENDER_EEVEE'
    e = scene.eevee
    e.taa_render_samples = samples
    applied = {}
    for key, value in [('use_raytracing', True), ('use_fast_gi', True), ('fast_gi_method', 'GLOBAL_ILLUMINATION'),
                       ('fast_gi_distance', 0.35), ('use_shadows', True), ('shadow_pool_size', '2048')]:
        try:
            setattr(e, key, value)
            applied[key] = value
        except Exception as ex:  # property names move between Blender releases
            applied[key] = f'unavailable: {ex}'
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX'
    return applied


def make_camera(scene, name='TOUR_CAM', lens=22.0):
    data = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_fit = 'HORIZONTAL'
    data.sensor_width = 36.0
    data.clip_start = 0.04
    data.clip_end = 400.0
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, data)
    if ob.name not in scene.collection.objects:
        scene.collection.objects.link(ob)
    scene.camera = ob
    return ob


def look_at(ob, pos_plan, target_plan):
    p = B(*pos_plan)
    ob.location = p
    ob.rotation_euler = (B(*target_plan) - p).to_track_quat('-Z', 'Y').to_euler()
