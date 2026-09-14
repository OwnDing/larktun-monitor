"""Build Larktun_Tour.blend: the furnished house with a keyed walkthrough camera.

blender -b Larktun_Home.blend --python tour/build_tour.py -- \
    [--frames out/tour/plan/camera_frames.json] [--save Larktun_Tour.blend] [--samples 32]

Larktun_Home.blend is only read.  This sets up a single TOUR view layer, the tour's
door states, an entry door that swings open, walls that grow from the 1.15 m cutaway
to full height with ceilings closing, the per-frame camera and EEVEE output.
"""
import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tour_scene as T  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CUT_ONLY = ('01a · Walls below 1.15 m', '01e · Windows doors below cut')
FULL_ONLY = ('01d · Ceilings — interiors only', '01f · Upper frames curtains hardware',
             '01g · Continuous full walls / interiors', '01h · Continuous doors windows curtains / interiors',
             '04a · Wall mounted security hardware')
NOT_RENDERED = ('01b · Full height walls — toggle for interiors', '01i · Upper cut-frame pieces / archive',
                '05 · Guides / non-rendering metadata')
CUT_START, CUT_END, CUT_OFF = 1.15, 2.95, 100.0
EXPOSURE_CUTAWAY, EXPOSURE_INTERIOR = 0.3, 0.5
PREFS = bpy.context.preferences.edit


def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', default=str(ROOT / 'out/tour/plan/camera_frames.json'))
    ap.add_argument('--save', default=str(ROOT / 'Larktun_Tour.blend'))
    ap.add_argument('--samples', type=int, default=32)
    return ap.parse_args(argv)


def key(owner, path, frame, value, interpolation, index=-1):
    PREFS.keyframe_new_interpolation_type = interpolation
    owner.keyframe_insert(path, index=index, frame=frame)


def tour_layer(scene):
    layer = scene.view_layers.new('TOUR')

    def walk(lc):
        lc.exclude = lc.name in NOT_RENDERED
        for child in lc.children:
            walk(child)
    for child in layer.layer_collection.children:
        walk(child)
    for other in [v for v in scene.view_layers if v != layer]:
        scene.view_layers.remove(other)
    return layer


def collection_objects(names):
    return [o for name in names for o in bpy.data.collections[name].all_objects]


def rising_cut_group():
    """Shader wrapper: transparent above cut_z; hollow wall insides read as solid caps."""
    ng = bpy.data.node_groups.new('TOUR · rising cut', 'ShaderNodeTree')
    ng.interface.new_socket('Shader', in_out='INPUT', socket_type='NodeSocketShader')
    ng.interface.new_socket('Cap Color', in_out='INPUT', socket_type='NodeSocketColor')
    ng.interface.new_socket('Shader', in_out='OUTPUT', socket_type='NodeSocketShader')
    n, link = ng.nodes, ng.links
    gin, gout = n.new('NodeGroupInput'), n.new('NodeGroupOutput')
    geo = n.new('ShaderNodeNewGeometry')
    xyz = n.new('ShaderNodeSeparateXYZ')
    link.new(geo.outputs['Position'], xyz.inputs[0])
    cut = n.new('ShaderNodeValue')
    cut.name = cut.label = 'cut_z'
    cut.outputs[0].default_value = CUT_OFF
    below = n.new('ShaderNodeMath')
    below.operation = 'LESS_THAN'
    link.new(xyz.outputs['Z'], below.inputs[0])
    link.new(cut.outputs[0], below.inputs[1])
    rising = n.new('ShaderNodeMath')
    rising.operation = 'LESS_THAN'
    rising.inputs[1].default_value = CUT_END + 0.5
    link.new(cut.outputs[0], rising.inputs[0])
    cap_mask = n.new('ShaderNodeMath')
    cap_mask.operation = 'MULTIPLY'
    link.new(geo.outputs['Backfacing'], cap_mask.inputs[0])
    link.new(rising.outputs[0], cap_mask.inputs[1])
    up = n.new('ShaderNodeCombineXYZ')
    up.inputs['Z'].default_value = 1.0
    cap = n.new('ShaderNodeBsdfDiffuse')
    link.new(gin.outputs['Cap Color'], cap.inputs['Color'])
    link.new(up.outputs[0], cap.inputs['Normal'])
    capped = n.new('ShaderNodeMixShader')
    link.new(cap_mask.outputs[0], capped.inputs[0])
    link.new(gin.outputs['Shader'], capped.inputs[1])
    link.new(cap.outputs[0], capped.inputs[2])
    clear = n.new('ShaderNodeBsdfTransparent')
    out = n.new('ShaderNodeMixShader')
    link.new(below.outputs[0], out.inputs[0])
    link.new(clear.outputs[0], out.inputs[1])
    link.new(capped.outputs[0], out.inputs[2])
    link.new(out.outputs[0], gout.inputs['Shader'])
    return ng


def cut_copy(material, group):
    copy = material.copy()
    copy.name = material.name + ' · tour cut'
    nt = copy.node_tree
    output = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial' and n.is_active_output)
    source = output.inputs['Surface'].links[0].from_socket
    wrap = nt.nodes.new('ShaderNodeGroup')
    wrap.node_tree = group
    wrap.inputs['Cap Color'].default_value = (*material.diffuse_color[:3], 1.0)
    nt.links.new(source, wrap.inputs['Shader'])
    nt.links.new(wrap.outputs['Shader'], output.inputs['Surface'])
    copy.surface_render_method = 'DITHERED'
    # Correct clipped shadows cost ~6x render time; render_tour.py enables them for the rise frames only.
    copy.use_transparent_shadow = False
    return copy


def apply_cut_materials(objects, group):
    copies = {}
    for o in objects:
        shared = o.data is not None and o.data.users > 1
        for slot in o.material_slots:
            if slot.material is None:
                continue
            if slot.material.name not in copies:
                copies[slot.material.name] = cut_copy(slot.material, group)
            if shared:
                slot.link = 'OBJECT'
            slot.material = copies[slot.material.name]
    return copies


def key_rise(group, scene, rise):
    sock = group.nodes['cut_z'].outputs[0]
    for frame, value, interpolation in ((1, CUT_START, 'CONSTANT'), (rise[0], CUT_START, 'BEZIER'),
                                        (rise[1], CUT_END, 'CONSTANT'), (rise[1] + 1, CUT_OFF, 'CONSTANT')):
        sock.default_value = value
        key(sock, 'default_value', frame, value, interpolation)
    vs = scene.view_settings
    for frame, value in ((rise[0], EXPOSURE_CUTAWAY), (rise[1], EXPOSURE_INTERIOR)):
        vs.exposure = value
        key(vs, 'exposure', frame, value, 'BEZIER')


def key_visibility(cut_objects, full_objects, rise_start):
    keyed = 0
    for objects, hidden_before in ((cut_objects, False), (full_objects, True)):
        for o in objects:
            if o.hide_render:  # pocketed door panes stay hidden throughout
                continue
            for frame, hidden in ((1, hidden_before), (rise_start, not hidden_before)):
                o.hide_render = hidden
                key(o, 'hide_render', frame, hidden, 'CONSTANT')
            keyed += 1
    return keyed


def animate_entry_door(scene, frames):
    cfg = T.SWING_DOORS['入户门']
    hinge = bpy.data.objects.new('TOUR · entry door hinge', None)
    scene.collection.objects.link(hinge)
    hinge.location = T.B(*cfg['pivot'])
    hinge.empty_display_size = 0.3
    rest_inverse = hinge.matrix_basis.inverted()
    parts = T.swing_parts('入户门')
    for o in parts:
        o.parent = hinge
        o.matrix_parent_inverse = rest_inverse
    for frame, deg in ((frames[0], 0.0), (frames[1], cfg['open_deg'])):
        hinge.rotation_euler.z = math.radians(deg)
        key(hinge, 'rotation_euler', frame, deg, 'BEZIER', index=2)
    return len(parts)


def key_camera(scene, data):
    cam_data = bpy.data.cameras.new('TOUR · handheld camera')
    cam_data.sensor_fit = 'HORIZONTAL'
    cam_data.sensor_width = 36.0
    cam_data.clip_end = 400.0
    cam = bpy.data.objects.new('TOUR · handheld camera', cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    previous = None
    for k, (x, y, z, yaw, pitch, roll, lens) in enumerate(data['frames']):
        frame = k + 1
        m = (Matrix.Rotation(math.radians(-yaw - 90.0), 3, 'Z') @ Matrix.Rotation(math.radians(90.0 + pitch), 3, 'X')
             @ Matrix.Rotation(math.radians(roll), 3, 'Z'))
        euler = m.to_euler('XYZ', previous) if previous else m.to_euler('XYZ')
        previous = euler
        cam.location = T.B(x, y, z)
        cam.rotation_euler = euler
        cam_data.lens = lens
        key(cam, 'location', frame, None, 'LINEAR')
        key(cam, 'rotation_euler', frame, None, 'LINEAR')
        key(cam_data, 'lens', frame, lens, 'LINEAR')
    # Far drone views need less depth precision near the lens than the walk does.
    walk = data['walk_start_frame']
    for frame, value in ((1, 0.25), (max(2, walk - 90), 0.25), (walk - 30, 0.04)):
        cam_data.clip_start = value
        key(cam_data, 'clip_start', frame, value, 'LINEAR')
    return cam


def configure_output(scene, frame_count, samples):
    applied = T.configure_eevee(scene, samples)
    r = scene.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100
    r.fps = 30
    scene.frame_start, scene.frame_end = 1, frame_count
    r.use_motion_blur = True
    r.motion_blur_shutter = 0.3  # daylight phone footage: short shutter, light blur on pans
    r.image_settings.file_format = 'PNG'
    r.image_settings.color_mode = 'RGB'
    r.image_settings.color_depth = '8'
    r.image_settings.compression = 15
    r.filepath = '//out/tour/frames/'
    r.use_file_extension = True
    r.use_overwrite = False
    r.use_placeholder = False
    return applied


def main():
    args = parse_args()
    frames_path = Path(args.frames)
    data = json.loads(frames_path.read_text())
    scene = bpy.context.scene
    scene.name = 'Larktun House Tour'
    tour_layer(scene)

    T.open_sliders(suffixes=(T.FULL_SUFFIX, T.LOWER_SUFFIX))
    T.open_swing_doors(angles={'入户门': 0.0}, suffixes=(T.FULL_SUFFIX, T.LOWER_SUFFIX))
    door_parts = animate_entry_door(scene, data['door_frames'])

    cut_objects = collection_objects(CUT_ONLY)
    full_objects = collection_objects(FULL_ONLY)
    group = rising_cut_group()
    copies = apply_cut_materials(full_objects, group)
    key_rise(group, scene, data['rise_frames'])
    keyed = key_visibility(cut_objects, full_objects, data['rise_frames'][0])

    key_camera(scene, data)
    applied = configure_output(scene, data['frame_count'], args.samples)
    PREFS.keyframe_new_interpolation_type = 'BEZIER'

    scene['tour_rise_frames'] = data['rise_frames']
    scene['tour_source'] = 'Larktun_Home.blend'
    scene['tour_frames'] = os.path.relpath(frames_path, ROOT)
    scene['tour_frames_sha256'] = hashlib.sha256(frames_path.read_bytes()).hexdigest()
    scene['coordinate_map'] = 'Drawing (x east, y south, z up) -> Blender (x, -y, z)'
    save = Path(args.save).resolve()
    assert save.name != 'Larktun_Home.blend', 'refusing to overwrite the house source'
    bpy.ops.wm.save_as_mainfile(filepath=str(save), compress=True)
    print('BUILD_TOUR_DONE', json.dumps(dict(save=str(save), frames=data['frame_count'], entry_door_parts=door_parts,
                                             cut_materials=len(copies), visibility_keyed=keyed, eevee=applied),
                                        ensure_ascii=False))


if __name__ == '__main__':
    main()
