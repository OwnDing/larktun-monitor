"""V1-only, disposable camera/cutaway review. Never saves a .blend.

Run with the macOS Python that has Pillow:
    python3 blender/render_v1_framing.py
For a geometry/settings audit without rendering:
    python3 blender/render_v1_framing.py --preflight

The same file runs as a Blender worker in a separate process. All collection
links, visibility flags and the new camera die with that process. Existing mesh,
light, material, world, color-management and camera data are fingerprinted.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'renders/v1_framing'
SOURCE = ROOT / 'Larktun_Home.blend'
REFERENCE = ROOT / 'frames/S02.png'
BLENDER = '/Applications/Blender.app/Contents/MacOS/Blender'
ANGLES = (45, 135, 225, 315)
SCALES = (18, 25, 32)
LOOK_AT = (6.0, 4.6, 1.3)  # Drawing coordinates: east, south, up.
DISTANCE = 40.0
SIZE = (1080, 1920)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_hashes():
    return {str(p.relative_to(ROOT)): sha(p) for p in
            (SOURCE, ROOT / 'scene/layout.json', REFERENCE)}


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def worker(preflight):
    import bpy
    import numpy as np
    from array import array
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view

    assert Path(bpy.data.filepath).resolve() == SOURCE.resolve()
    sc = bpy.data.scenes['01 · House cutaway']
    bpy.context.window.scene = sc
    originals = list(bpy.data.objects)
    original_names = {o.name for o in originals}
    baseline_hidden = {o.name: o.hide_render for o in originals}
    original_collections = {o.name: [c.name for c in o.users_collection] for o in originals}
    hashes_before = source_hashes()
    log_path = OUT / ('_preflight.log' if preflight else 'framing.log')
    log_file = log_path.open('w')

    def log(event, **data):
        line = json.dumps(dict(event=event, **data), ensure_ascii=False)
        print(line, flush=True)
        log_file.write(line + '\n')
        log_file.flush()

    def scalar_rna(obj):
        result = {}
        for prop in obj.bl_rna.properties:
            if prop.identifier == 'rna_type' or prop.type not in {'BOOLEAN', 'INT', 'FLOAT', 'STRING', 'ENUM'}:
                continue
            try:
                v = getattr(obj, prop.identifier)
                result[prop.identifier] = list(v) if getattr(prop, 'is_array', False) else v
            except (TypeError, AttributeError):
                pass
        return result

    def nodes(tree):
        if not tree:
            return None
        result = {'nodes': [], 'links': []}
        for n in tree.nodes:
            sockets = []
            for s in n.inputs:
                if hasattr(s, 'default_value'):
                    v = s.default_value
                    if not isinstance(v, (str, bool, int, float)):
                        try:
                            v = list(v)
                        except TypeError:
                            v = getattr(v, 'name', str(v))
                    sockets.append([s.identifier, v])
            result['nodes'].append([n.name, scalar_rna(n), sockets])
        result['links'] = sorted([l.from_node.name, l.from_socket.identifier,
                                  l.to_node.name, l.to_socket.identifier] for l in tree.links)
        return result

    def digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()

    def immutable_state():
        geometry = hashlib.sha256()
        for o in sorted(originals, key=lambda o: o.name):
            geometry.update(json.dumps([o.name, o.type, list(o.location), list(o.rotation_euler),
                                       list(o.scale), list(o.rotation_quaternion),
                                       [m.name if m else None for m in getattr(o.data, 'materials', [])],
                                       [scalar_rna(m) for m in o.modifiers]], sort_keys=True, default=str).encode())
        for mesh in sorted(bpy.data.meshes, key=lambda m: m.name):
            geometry.update(mesh.name.encode())
            for items, attr, count, kind in ((mesh.vertices, 'co', 3, 'f'),
                                            (mesh.loops, 'vertex_index', 1, 'i'),
                                            (mesh.polygons, 'material_index', 1, 'i')):
                values = array(kind, [0]) * (len(items) * count)
                items.foreach_get(attr, values)
                geometry.update(values.tobytes())
        for curve in sorted(bpy.data.curves, key=lambda c: c.name):
            geometry.update(json.dumps([curve.name, scalar_rna(curve),
                [[s.type, [list(p.co) for p in s.points],
                  [[list(p.co), list(p.handle_left), list(p.handle_right)] for p in s.bezier_points]]
                 for s in curve.splines]], sort_keys=True, default=str).encode())
        lights = [[o.name, scalar_rna(o.data), nodes(o.data.node_tree),
                   list(o.location), list(o.rotation_euler), list(o.scale), o.hide_render]
                  for o in originals if o.type == 'LIGHT']
        materials = [[m.name, scalar_rna(m), nodes(m.node_tree)] for m in bpy.data.materials]
        world = [sc.world.name, scalar_rna(sc.world), nodes(sc.world.node_tree)]
        cameras = [[o.name, scalar_rna(o.data)] for o in originals if o.type == 'CAMERA']
        color = [scalar_rna(sc.view_settings), scalar_rna(sc.display_settings),
                 scalar_rna(sc.sequencer_colorspace_settings)]
        return {'model_geometry_and_original_transforms': geometry.hexdigest(),
                'lights': digest(lights), 'materials': digest(materials),
                'world': digest(world), 'color_management': digest(color),
                'original_cameras': digest(cameras)}

    invariants_before = immutable_state()
    layer = sc.view_layers['02 · FULL INTERIOR']
    for vl in sc.view_layers:
        vl.use = vl == layer
    bpy.context.window.view_layer = layer

    static_excluded = [
        '01a · Walls below 1.15 m',
        '01b · Full height walls — toggle for interiors',
        '01d · Ceilings — interiors only',
        '01e · Windows doors below cut',
        '01i · Upper cut-frame pieces / archive',
        '05 · Guides / non-rendering metadata',
    ]

    def set_exclusions(lc):
        for child in lc.children:
            child.exclude = child.name in static_excluded
            set_exclusions(child)

    set_exclusions(layer.layer_collection)
    layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    active = [o for o in originals if o.type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}
              and o.visible_get(view_layer=layer) and not o.hide_render]

    # Cache evaluated corners BEFORE direction-dependent hiding. Several curves
    # and cloth meshes use world-space vertices with object origins at (0,0,0).
    corners, centers = {}, {}
    for o in active:
        ev = o.evaluated_get(deps)
        if o.type in {'CURVE', 'FONT', 'SURFACE'}:
            # Blender curve bound_box can include the control-point radius of
            # 1 m even when the rendered bevel is only 2 mm. Measure a temporary
            # evaluated mesh, without converting or modifying the source object.
            mesh = ev.to_mesh()
            coords = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
            mesh.vertices.foreach_get('co', coords)
            coords = coords.reshape((-1, 3))
            lo, hi = coords.min(axis=0), coords.max(axis=0)
            pts = [ev.matrix_world @ Vector(v) for v in itertools.product(*zip(lo, hi))]
            ev.to_mesh_clear()
        else:
            pts = [ev.matrix_world @ Vector(v) for v in ev.bound_box]
        corners[o.name] = pts
        centers[o.name] = sum(pts, Vector()) / 8

    layout = json.loads((ROOT / 'scene/layout.json').read_text())
    rooms = {r['id']: r for r in layout['rooms']}
    walls = list(layout['walls']) + [dict(type='I', x0=8.52, y0=2.12, x1=9.6, y1=2.24)]
    focus = [rooms['R03'], rooms['R07']]

    def rect_distance(x, y, r):
        return math.hypot(max(r['x0'] - x, 0, x - r['x1']),
                          max(r['y0'] - y, 0, y - r['y1']))

    def nearest_room(x, y):
        return min(rooms, key=lambda rid: rect_distance(x, y, rooms[rid]))

    def nearest_wall(x, y):
        return min(range(len(walls)), key=lambda i: rect_distance(x, y, walls[i]))

    def ray_reaches_focus(x, y, sx, sy):
        # The room centre must lie on a foreground ray leading to the living /
        # dining footprint. This avoids removing a whole unrelated far corner.
        for r in focus:
            if r['x0'] < x < r['x1'] and r['y0'] < y < r['y1']:
                continue
            tx = sorted(((r['x0'] - x) / -sx, (r['x1'] - x) / -sx))
            ty = sorted(((r['y0'] - y) / -sy, (r['y1'] - y) / -sy))
            if max(tx[0], ty[0], 0.001) < min(tx[1], ty[1]):
                return True
        return False

    temp = bpy.data.collections.new('V1 · TEMPORARY directional visibility groups')
    sc.collection.children.link(temp)
    groups, members, assignment, wall_groups = {}, {}, {}, {}

    def add_group(key, ob):
        if key not in groups:
            c = bpy.data.collections.new('V1 · ' + key)
            temp.children.link(c)
            groups[key], members[key] = c, []
        groups[key].objects.link(ob)
        members[key].append(ob)
        assignment[ob.name] = key

    openings = {o['name']: o for o in layout['doors'] + layout['windows']}
    openings.update({
        '书房门 · corrected access': dict(x=9.6, y=2.27),
        '玄关至书房过道': dict(x=8.4, y=2.27),
        '公卫移门': dict(x=8.65, y=2.12),
        '走廊至入口过道': dict(x=8.7, y=3.2),
    })
    wall_fitting_words = ('Curtain', 'curtain', 'blind', 'Gallery frame', 'Print ',
                          'Abstract landscape', 'Oak skirting', 'Switch ', 'Rocker ',
                          'Outlet ', 'Recessed socket', 'Lamp wall plug', 'Bay ',
                          'Master bay', 'Balcony coping')
    for o in active:
        p = centers[o.name]
        x, y = p.x, -p.y
        n = o.name
        wi = None
        match = re.match(r'^W(\d\d) /', n)
        if match:
            wi = int(match.group(1))
        elif n.startswith('Structural beam'):
            add_group('Beam north' if y < LOOK_AT[1] else 'Beam south', o)
            continue
        elif n.startswith('C1 ') or n.startswith('D5 ') or n.startswith('R07 · 电视 65"'):
            wi = 14
        elif n.startswith(('C2 ', 'D4 ')):
            wi = 13
        elif n.startswith('C3 '):
            wi = 21
        elif any(c.startswith('01h ') for c in original_collections[n]):
            opening = next((op for name, op in sorted(openings.items(), key=lambda v: -len(v[0]))
                            if n.startswith(name + ' ')), None)
            wi = nearest_wall(opening['x'], opening['y']) if opening else nearest_wall(x, y)
        elif any(word in n for word in wall_fitting_words):
            wi = nearest_wall(x, y)
        elif n.startswith('Structural'):
            wi = nearest_wall(x, y)
        if wi is not None:
            w = walls[wi]
            horiz = w['x1'] - w['x0'] > w['y1'] - w['y0']
            probes = [(x, w['y0'] - .04), (x, w['y1'] + .04)] if horiz else [(w['x0'] - .04, y), (w['x1'] + .04, y)]
            adjacent = {rid for xx, yy in probes for rid, r in rooms.items()
                        if r['x0'] - .04 <= xx <= r['x1'] + .04 and r['y0'] - .04 <= yy <= r['y1'] + .04}
            # Doorway pieces / bay returns beyond a floor edge still belong to
            # the nearest room; their entire original mesh remains untouched.
            if not adjacent:
                adjacent = {nearest_room(x, y)}
            key = f'Wall W{wi:02d} [{"+".join(sorted(adjacent))}] / full wall and attached fittings'
            wall_groups[key] = (wi, adjacent)
            add_group(key, o)
            continue
        if n == 'Matte presentation ground':
            continue
        rid = next((c[:3] for c in original_collections[n] if re.match(r'R\d\d ·', c)), None)
        if rid is None and re.match(r'R\d\d[ ·]', n):
            rid = n[:3]
        if n.startswith(('D1 ', 'D2 ', 'D3 ')):
            rid = 'R06'
        if rid is None:
            rid = nearest_room(x, y)
        add_group(f'Room {rid} / furniture floor and loose details', o)

    asset_objects = {
        'C1': [o for o in active if o.name.startswith('C1 ')],
        'TV': [o for o in active if o.name.startswith('R07 · 电视 65"')],
        'dining_table': [o for o in active if o.name.startswith('R03 · 餐桌')],
        'sofa': [o for o in active if o.name.startswith('R07 · 三人沙发')],
        'D1': [o for o in active if o.name.startswith('D1 ')],
    }
    anchors = {
        'C1': 'C1 camera housing', 'TV': 'R07 · 电视 65" reflective screen',
        'dining_table': 'R03 · 餐桌 solid top',
        'sofa': 'R07 · 三人沙发 lower upholstery', 'D1': 'D1 硬盘录像机 NVR',
    }
    for key, name in anchors.items():
        assert name in corners, (key, name)
        assert asset_objects[key], key

    camera_data = bpy.data.cameras.new('V1_FRAMING disposable orthographic camera')
    camera = bpy.data.objects.new('V1_FRAMING disposable orthographic camera', camera_data)
    sc.collection.objects.link(camera)
    camera.rotation_mode = 'XYZ'
    camera_data.type = 'ORTHO'
    camera_data.sensor_fit = 'AUTO'
    camera_data.clip_start = 0.025
    camera_data.clip_end = 200
    sc.camera = camera
    sc.render.resolution_x, sc.render.resolution_y = SIZE
    sc.render.resolution_percentage = 100
    sc.render.pixel_aspect_x = sc.render.pixel_aspect_y = 1.0
    sc.cycles.samples = 32
    # GPU device selection is a machine preference, not a scene lighting edit.
    pref = bpy.context.preferences.addons['cycles'].preferences
    pref.compute_device_type = 'METAL'
    pref.get_devices()
    for device in pref.devices:
        device.use = device.type == 'METAL'
    assert sc.cycles.device == 'GPU'
    assert sc.render.image_settings.file_format == 'PNG'

    group_manifest = {}
    for key, objs in members.items():
        group_manifest[groups[key].name] = {
            'objects': sorted(o.name for o in objs),
            'original_collections': sorted({c for o in objs for c in original_collections[o.name]}),
        }
    write_json(OUT / 'visibility_groups.json', group_manifest)

    report = {
        'status': 'preflight' if preflight else 'rendering',
        'source_blend': str(SOURCE), 'source_scene': sc.name,
        'blender_version': bpy.app.version_string, 'resolution_px': list(SIZE),
        'samples': 32, 'unchanged_adaptive_threshold': sc.cycles.adaptive_threshold,
        'unchanged_exposure': sc.view_settings.exposure,
        'coordinate_system': 'Drawing (east, south, up) -> Blender (x, -y, z)',
        'look_at': list(LOOK_AT), 'look_at_blender': [6, -4.6, 1.3],
        'camera_distance_m': DISTANCE, 'sensor_fit': 'AUTO',
        'coverage_method': 'camera.data.view_frame(scene=scene), local X/Y spans, metres',
        'visibility_method': {
            'objects_in_frame': 'world_to_camera_view of each named physical anchor evaluated bounding-box centre; 0<=x,y<=1 and clip_start<=depth<=clip_end. Pure frustum test, independent of hiding/occlusion.',
            'render_enabled_in_frame': 'objects_in_frame AND the physical anchor remains enabled after directional cutaway. Does not claim absence of surface occlusion.',
            'bounds': 'Projection of all 8 evaluated bounding-box corners of every component; curves measured from temporary evaluated mesh to exclude control-point radius padding. partial_in_frame is conservative screen-rectangle overlap; fully_in_frame requires every corner inside.',
            'anchor_objects': anchors,
        },
        'cutaway_policy': {
            'geometry': 'Only continuous 01g/01h source meshes; no mesh edits or height cuts. Ceilings and archived split geometry excluded.',
            'near_rooms': 'Non-focus room centre must lie on a horizontal incoming ray reaching the R03/R07 footprint. R03 dining and R07 living always retained.',
            'walls': 'Near outside faces removed; living/dining near E/W boundary removed. Other partitions removed when both adjoining rooms are hidden or they sit in the foreground sweep. Shared far walls stay full height.',
            'attachments': 'C1 and TV follow W14; switches, skirting, window/door assemblies, artwork and curtain rods follow their host wall. Room floors and loose props follow their room.',
            'implementation': 'Temporary collection links plus matching object.hide_render flags (objects also have original collection links). All changes are discarded on process exit.',
            'static_excluded_collections': static_excluded,
            'membership_manifest': 'visibility_groups.json',
        },
        'source_sha256_before': hashes_before, 'invariants_before': invariants_before,
        'frames': [],
    }

    def adjacent_rooms(wi):
        w = walls[wi]
        x, y = (w['x0'] + w['x1']) / 2, (w['y0'] + w['y1']) / 2
        horiz = w['x1'] - w['x0'] > w['y1'] - w['y0']
        pts = [(x, w['y0'] - .04), (x, w['y1'] + .04)] if horiz else [(w['x0'] - .04, y), (w['x1'] + .04, y)]
        return {rid for xx, yy in pts for rid, r in rooms.items()
                if r['x0'] - .01 <= xx <= r['x1'] + .01 and r['y0'] - .01 <= yy <= r['y1'] + .01}

    def direction_cut(z_angle):
        east, south = z_angle in (45, 135), z_angle in (45, 315)
        sx, sy = (1 if east else -1), (1 if south else -1)
        hidden_rooms = {rid for rid, r in rooms.items() if rid not in {'R03', 'R07'}
                        and ray_reaches_focus((r['x0'] + r['x1']) / 2,
                                              (r['y0'] + r['y1']) / 2, sx, sy)}
        hidden_walls = {3 if east else 2, 1 if south else 0}
        hidden_walls |= {12, 13, 14} if east else {10, 11}
        # Parapets/coping only survive when their balcony survives.
        if 'R01' in hidden_rooms:
            hidden_walls |= {4, 5, 6}
        if 'R13' in hidden_rooms:
            hidden_walls |= {7, 8, 9}
        for wi in range(15, len(walls)):
            w = walls[wi]
            x, y = (w['x0'] + w['x1']) / 2, (w['y0'] + w['y1']) / 2
            adjacent = adjacent_rooms(wi)
            if adjacent and adjacent <= hidden_rooms:
                hidden_walls.add(wi)
            elif ray_reaches_focus(x, y, sx, sy) and adjacent & hidden_rooms:
                hidden_walls.add(wi)
        # A hidden neighbouring room must not leave its outer-wall fittings
        # suspended over a missing slab. Walls shared with retained rooms stay.
        hidden_keys = {f'Room {rid} / furniture floor and loose details' for rid in hidden_rooms}
        hidden_keys |= {key for key, (wi, adjacent) in wall_groups.items()
                        if wi in hidden_walls or (adjacent and adjacent <= hidden_rooms)}
        hidden_keys.add('Beam south' if south else 'Beam north')
        for o in originals:
            o.hide_render = baseline_hidden[o.name]
        for key, collection in groups.items():
            hide = key in hidden_keys
            collection.hide_render = hide
            for o in members[key]:
                o.hide_render = baseline_hidden[o.name] or hide
        real_hidden = []
        for rid in rooms:
            collection = next(c for c in bpy.data.collections if c.name.startswith(rid + ' ·'))
            collection.hide_render = rid in hidden_rooms
            if collection.hide_render:
                real_hidden.append(collection.name)
        layer.update()
        hidden_collections = sorted(static_excluded + real_hidden +
                                    [groups[k].name for k in hidden_keys if k in groups])
        return hidden_rooms, hidden_walls, hidden_collections

    def projected(key):
        anchor = bpy.data.objects[anchors[key]]
        centre = centers[anchor.name]
        p = world_to_camera_view(sc, camera, centre)
        inside = 0 <= p.x <= 1 and 0 <= p.y <= 1 and camera_data.clip_start <= p.z <= camera_data.clip_end
        pts = [world_to_camera_view(sc, camera, point)
               for o in asset_objects[key] for point in corners[o.name]]
        xmin, xmax = min(p.x for p in pts), max(p.x for p in pts)
        ymin, ymax = min(p.y for p in pts), max(p.y for p in pts)
        zmin, zmax = min(p.z for p in pts), max(p.z for p in pts)
        overlap = xmin <= 1 and xmax >= 0 and ymin <= 1 and ymax >= 0 and zmax >= camera_data.clip_start and zmin <= camera_data.clip_end
        fully = 0 <= xmin <= xmax <= 1 and 0 <= ymin <= ymax <= 1 and camera_data.clip_start <= zmin <= zmax <= camera_data.clip_end
        return {
            'in_frame': bool(inside), 'render_enabled': not anchor.hide_render,
            'render_enabled_in_frame': bool(inside and not anchor.hide_render),
            'partial_in_frame': bool(overlap), 'fully_in_frame': bool(fully),
            'anchor_object': anchor.name, 'anchor_world_blender_m': list(centre),
            'anchor_ndc': list(p), 'projected_bounds_ndc': [xmin, ymin, xmax, ymax],
            'projected_size_px': [(xmax - xmin) * SIZE[0], (ymax - ymin) * SIZE[1]],
            'cutaway_group': groups[assignment[anchor.name]].name,
            'components': [o.name for o in asset_objects[key]],
        }

    log('start', source_sha256=hashes_before, scene=sc.name,
        original_model_object_count=len(originals), continuous_review_objects=len(active))
    for angle in ANGLES:
        hidden_rooms, hidden_walls, hidden_collections = direction_cut(angle)
        camera.rotation_euler = (math.radians(54.7356), 0.0, math.radians(angle))
        target = Vector((LOOK_AT[0], -LOOK_AT[1], LOOK_AT[2]))
        camera.location = target + camera.rotation_euler.to_matrix() @ Vector((0, 0, DISTANCE))
        for scale in SCALES:
            camera_data.ortho_scale = scale
            layer.update()
            frustum = camera_data.view_frame(scene=sc)
            coverage = {'horizontal': max(p.x for p in frustum) - min(p.x for p in frustum),
                        'vertical': max(p.y for p in frustum) - min(p.y for p in frustum)}
            assert abs(coverage['horizontal'] - scale * 1080 / 1920) < 1e-5
            assert abs(coverage['vertical'] - scale) < 1e-5
            look_ndc = world_to_camera_view(sc, camera, target)
            assert abs(look_ndc.x - .5) < 1e-5 and abs(look_ndc.y - .5) < 1e-5
            objects = {key: projected(key) for key in anchors}
            name = f'V1_Z{angle}_S{scale}.png'
            entry = {
                'file': name, 'z_angle_deg': angle, 'ortho_scale': scale,
                'look_at': list(LOOK_AT), 'look_at_blender': list(target),
                'camera_location': list(camera.location),
                'camera_location_drawing': [camera.location.x, -camera.location.y, camera.location.z],
                'camera_rotation_euler_deg': [math.degrees(v) for v in camera.rotation_euler],
                'camera_rotation_euler_rad': list(camera.rotation_euler),
                'world_coverage_m': coverage,
                'hidden_collections': hidden_collections,
                'hidden_rooms': sorted(hidden_rooms),
                'hidden_wall_indices': sorted(hidden_walls),
                'objects_in_frame': {k: v['in_frame'] for k, v in objects.items()},
                'render_enabled_in_frame': {k: v['render_enabled_in_frame'] for k, v in objects.items()},
                'objects': objects,
            }
            log('frame_configuration', **entry)
            if not preflight:
                sc.render.filepath = str(OUT / name)
                start = time.monotonic()
                bpy.ops.render.render(write_still=True, layer=layer.name)
                assert (OUT / name).is_file()
                entry['render_seconds'] = round(time.monotonic() - start, 3)
                entry['png_sha256'] = sha(OUT / name)
                log('frame_complete', file=name, seconds=entry['render_seconds'])
            report['frames'].append(entry)

    invariants_after = immutable_state()
    assert invariants_before == invariants_after, (invariants_before, invariants_after)
    assert source_hashes() == hashes_before
    assert original_names == {o.name for o in bpy.data.objects if o != camera}
    report.update(invariants_after=invariants_after, invariants_unchanged=True,
                  source_sha256_after=source_hashes(), source_files_unchanged=True,
                  status='preflight_complete' if preflight else 'renders_complete')
    write_json(OUT / ('_preflight.json' if preflight else 'framing_report.json'), report)
    log('complete', frames=len(report['frames']), invariants_unchanged=True,
        source_files_unchanged=True, blend_saved=False)
    log_file.close()


def postprocess():
    from PIL import Image, ImageDraw, ImageFont
    reference = Image.open(REFERENCE).convert('RGB')
    assert reference.size == SIZE
    (OUT / 'overlay').mkdir(exist_ok=True)
    report = json.loads((OUT / 'framing_report.json').read_text())
    thumb_w, thumb_h, label_h, gap = 360, 640, 60, 16
    sheet = Image.new('RGB', (4 * thumb_w + 5 * gap, 3 * (thumb_h + label_h) + 4 * gap), '#e9e7e2')
    draw = ImageDraw.Draw(sheet)
    font_path = '/System/Library/Fonts/Supplemental/Arial.ttf'
    font = ImageFont.truetype(font_path, 24)
    small = ImageFont.truetype(font_path, 16)
    for row, scale in enumerate(SCALES):
        for col, angle in enumerate(ANGLES):
            name = f'V1_Z{angle}_S{scale}.png'
            with Image.open(OUT / name) as image:
                image.load()
                assert image.size == SIZE, (name, image.size)
                render = image.convert('RGB')
            overlay = Image.blend(render, reference, .5)
            overlay.save(OUT / 'overlay' / name)
            # Verify the delivered image, including exact 50% pixel arithmetic.
            with Image.open(OUT / 'overlay' / name) as check:
                assert check.size == SIZE and check.convert('RGB').tobytes() == overlay.tobytes()
            x, y = gap + col * (thumb_w + gap), gap + row * (thumb_h + label_h + gap)
            draw.rectangle((x, y, x + thumb_w, y + label_h), fill='#23313a')
            draw.text((x + 12, y + 7), f'Z {angle} deg   |   ortho_scale {scale}', fill='white', font=font)
            draw.text((x + 12, y + 36), f'{scale * .5625:g} m x {scale} m  |  1080 x 1920', fill='#cad4d8', font=small)
            sheet.paste(render.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (x, y + label_h))
    sheet.save(OUT / '_contact_sheet.png')
    assert len(report['frames']) == 12
    for frame in report['frames']:
        frame['overlay_file'] = 'overlay/' + frame['file']
        frame['overlay_sha256'] = sha(OUT / frame['overlay_file'])
    report.update(status='complete', contact_sheet='_contact_sheet.png',
                  contact_sheet_grid={'columns': list(ANGLES), 'rows': list(SCALES)},
                  overlay={'reference': 'frames/S02.png', 'reference_opacity': .5,
                           'render_opacity': .5, 'operation': 'Pillow Image.blend in RGB; no resizing or cropping'},
                  delivered_png_count=25, resolution_and_overlay_checks='PASS')
    report['script'] = str(Path(__file__).resolve().relative_to(ROOT))
    report['script_sha256'] = sha(Path(__file__))
    report['findings'] = {
        'Z45_and_Z135': 'C1 and TV project inside all three frames, but their near-side east host wall W14 is removed, so both assemblies are disabled.',
        'Z225': 'C1, TV, dining table and sofa remain enabled inside all three frames. D1 is outside at scales 18 and 25, inside at 32.',
        'Z315': 'All five physical anchors are inside and enabled at all three scales. This is a framing result; world_to_camera_view does not test occlusion.',
        'scale_coverage_m': {str(s): {'horizontal': s * .5625, 'vertical': s} for s in SCALES},
        'decision': 'No direction or scale selected or written back to layout.json.',
    }
    assert source_hashes() == report['source_sha256_before']
    write_json(OUT / 'framing_report.json', report)
    rows = []
    for f in report['frames']:
        values = ['true' if f['objects_in_frame'][k] else 'false'
                  for k in ('C1', 'TV', 'dining_table', 'sofa', 'D1')]
        disabled = ', '.join(k for k, v in f['objects'].items() if not v['render_enabled']) or '—'
        rows.append('| ' + ' | '.join([f"Z{f['z_angle_deg']} / S{f['ortho_scale']}"] + values + [disabled]) + ' |')
    note = '''# V1 构图验证

12 张原始渲染 + 12 张 S02 叠加图 + 1 张 4×3 拼版。
原始渲染及叠加图均为 **1080×1920**；Cycles 32 samples。

拼版 `_contact_sheet.png`：列为 Z45 / Z135 / Z225 / Z315，行为 scale 18 / 25 / 32。
`overlay/` 是同名渲染与 `frames/S02.png` 的 RGB 50% 混合，保持原尺寸。

## 投影与剖切结果

下表 true/false 使用 `world_to_camera_view` 判断实际物体包围盒中心是否在画幅内。
最后一列另外列出因剖切隐藏的目标。**投影在框内不等于参与渲染，也不证明没有遮挡。**
JSON 同时保留各组件投影范围、完整入框/部分入框判定、像素占幅和物体名称。

| 机位 / 尺度 | C1 | 电视 | 餐桌 | 沙发 | D1 | 剖切隐藏的目标 |
|---|---|---|---|---|---|---|
''' + '\n'.join(rows) + '''

Z45 / Z135 的 C1 和电视随近侧东墙隐藏。Z225 要到 scale 32 才将 D1 纳入画幅。
Z315 三档尺度的五个目标均在框内且保留参与渲染；scale 越大，目标占像素越小。

## 相机与剖切

- 看点采用图纸坐标 `(6.0, 4.6, 1.3)`，对应 Blender `(6.0, -4.6, 1.3)`。
- 相机直接赋值 Euler `(54.7356°, 0°, Z)`，由旋转后的局部 +Z 轴后退 40 m 定位。
- 实测水平/垂直覆盖：S18 = 10.125 / 18 m；S25 = 14.0625 / 25 m；S32 = 18 / 32 m。
- 使用完整 01g/01h 源几何；关闭天花板及旧版分段墙体。远侧墙维持全高 2.8 m。
- 房间按“中心处于通向客厅/餐厅的前景射线”隐藏。墙、门窗、开关、踢脚线、窗帘杆和挂墙设备按宿主墙联动隐藏。
- 临时 collection 的完整成员表在 `visibility_groups.json`，逐帧隐藏清单及相机实际参数在 `framing.log` 和 `framing_report.json`。

## 完整性与复现

`framing_report.json` 中记录 `.blend`、`layout.json`、S02 的前后 SHA-256；三者完全一致。
模型几何与原物体变换、灯光、材质、世界环境、原有相机、色彩管理的内存指纹也完全一致。
曝光维持主场景原值 0.3；只有新相机、临时可见性、输出尺寸/路径和采样发生变化。
脚本不会保存 Blender 项目，也不会回写最终方位或尺度。

从项目根目录运行：

```sh
python3 blender/render_v1_framing.py
```

只做几何预检：`python3 blender/render_v1_framing.py --preflight`。
只重建叠加图/拼版/本说明：`python3 blender/render_v1_framing.py --postprocess-only`。
需要当前 macOS 已安装的 Blender 以及带 Pillow 的 Python。
'''
    (OUT / 'README.md').write_text(note)
    print('COMPLETE: 12 renders + 12 exact 50% overlays + contact sheet; source files unchanged.', flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--preflight', action='store_true')
    p.add_argument('--blender-worker', action='store_true')
    p.add_argument('--postprocess-only', action='store_true')
    args = p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
    OUT.mkdir(parents=True, exist_ok=True)
    if args.blender_worker:
        worker(args.preflight)
    elif args.postprocess_only:
        postprocess()
    else:
        before = source_hashes()
        command = [BLENDER, '-b', str(SOURCE), '--python-exit-code', '1', '--python', str(Path(__file__).resolve()), '--', '--blender-worker']
        if args.preflight:
            command.append('--preflight')
        # Preserve Blender diagnostics without dumping every Cycles sample to the UI.
        with (OUT / ('_preflight_blender.log' if args.preflight else 'blender.log')).open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        assert source_hashes() == before, 'An immutable source file changed.'
        if result.returncode:
            raise RuntimeError(f'Blender exited {result.returncode}; inspect {log.name}')
        if not args.preflight:
            postprocess()
        else:
            print('Preflight complete. No images rendered; no .blend saved.')


if __name__ == '__main__':
    main()
