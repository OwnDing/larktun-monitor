"""Obstacle map of the furnished apartment with the tour's door states.

blender -b Larktun_Home.blend --python tour/plan_map.py -- out/tour/plan

Cells (5 cm) are classified as
  FLOOR  walkable: first surface below 2.05 m is floor, rug or threshold
  SOFT   low furniture a person walks around but the camera may skim (top <= 1.12 m)
  HARD   anything at camera height: walls, tall furniture, open leaves, glass, screens
Thin vertical parts (glass, door leaves, curtains) are caught by horizontal ray sweeps
at camera height.  The ground outside the front door is walkable for the approach.
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tour_scene as T  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else 'out/tour/plan')
os.makedirs(OUT, exist_ok=True)

FLOOR, SOFT, HARD = 0, 1, 2
HARD_TOP = 1.12
SWEEP_HEIGHTS = (1.25, 1.55, 1.85)
APPROACH = (6.8, 8.9, -3.6, 0.0)  # x0, x1, y0, y1: open ground north of the entry door and its threshold
# Thresholds of the balcony doors bridge a strip where neither room slab reaches.
THRESHOLD_GAPS = ((4.30, 7.80, 8.55, 8.90), (1.15, 2.85, -0.30, 0.10))


def in_box(x, y, box):
    return box[0] <= x <= box[1] and box[2] <= y <= box[3]

sc = bpy.context.scene
T.show_full_interior(sc)
T.open_doors()
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()

RES = 0.05
X0, X1, Y0, Y1 = -0.6, 13.8, -3.6, 10.6
NX, NY = int(round((X1 - X0) / RES)), int(round((Y1 - Y0) / RES))
cls = np.full((NY, NX), HARD, dtype=np.uint8)
hit_z = np.full((NY, NX), np.nan, dtype=np.float32)
down = Vector((0, 0, -1))
for j in range(NY):
    py = Y0 + (j + 0.5) * RES
    for i in range(NX):
        px = X0 + (i + 0.5) * RES
        ok, location, normal, _index, _obj, _m = sc.ray_cast(dg, Vector((px, -py, 2.05)), down, distance=3.0)
        if not ok:
            continue
        z = location.z
        hit_z[j, i] = z
        if normal.z < -0.1 or z > HARD_TOP:
            continue
        if z >= 0.05:
            cls[j, i] = SOFT
        elif z > -0.045 and normal.z > 0.5:  # floor finishes, rugs, thresholds, 3 cm slab steps
            cls[j, i] = FLOOR
        elif z < -0.2 and normal.z > 0.5 and any(in_box(px, py, b) for b in (APPROACH, *THRESHOLD_GAPS)):
            # Ground under a door threshold or outside the entry.  Solid walls never get here:
            # a ray starting inside one hits its downward-facing base.
            cls[j, i] = FLOOR


def mark(location):
    i = int(math.floor((location.x - X0) / RES))
    j = int(math.floor((-location.y - Y0) / RES))
    if 0 <= i < NX and 0 <= j < NY:
        cls[j, i] = HARD


def sweep(origin, direction, length):
    remaining = length
    while remaining > 0:
        ok, location, _n, _i, _o, _m = sc.ray_cast(dg, origin, direction, distance=remaining)
        if not ok:
            return
        mark(location)
        remaining -= (location - origin).length + 0.002
        origin = location + direction * 0.002


hits_before = int((cls == HARD).sum())
for z in SWEEP_HEIGHTS:
    for j in range(NY):
        sweep(Vector((X0, -(Y0 + (j + 0.5) * RES), z)), Vector((1, 0, 0)), X1 - X0)
    for i in range(NX):
        sweep(Vector((X0 + (i + 0.5) * RES, -Y0, z)), Vector((0, -1, 0)), Y1 - Y0)


def distance_to(mask, radius):
    """Distance (m) from every cell to the nearest True cell, capped at radius."""
    r = int(radius / RES)
    out = np.full(mask.shape, r * RES, dtype=np.float32)
    pad = np.pad(mask, r, constant_values=False)
    for dj in range(-r, r + 1):
        for di in range(-r, r + 1):
            d = math.hypot(di, dj)
            if d > r:
                continue
            shifted = pad[r + dj:r + dj + NY, r + di:r + di + NX]
            np.minimum(out, np.where(shifted, d * RES, r * RES), out=out)
    return out


clear_hard = distance_to(cls == HARD, 1.0)
clear_body = distance_to(cls != FLOOR, 0.6)
soft_depth = np.where(cls == SOFT, distance_to(cls == FLOOR, 0.6), 0).astype(np.float32)

np.save(os.path.join(OUT, 'cls.npy'), cls)
np.save(os.path.join(OUT, 'clear_hard.npy'), clear_hard)
np.save(os.path.join(OUT, 'clear_body.npy'), clear_body)
np.save(os.path.join(OUT, 'soft_depth.npy'), soft_depth)
np.save(os.path.join(OUT, 'hit_z.npy'), hit_z)


def bbox(o):
    ev = o.evaluated_get(dg)
    pts = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    return [round(min(p.x for p in pts), 3), round(max(p.x for p in pts), 3),
            round(min(-p.y for p in pts), 3), round(max(-p.y for p in pts), 3),
            round(min(p.z for p in pts), 3), round(max(p.z for p in pts), 3)]


objects = {}
for c in bpy.data.collections:
    if c.name[:1] == 'R' and ' · ' in c.name or c.name.startswith(('03 ', '04 ', '01h', '01f')):
        for o in c.objects:
            if o.type in {'MESH', 'CURVE', 'FONT'}:
                objects[o.name] = dict(collection=c.name, bbox=bbox(o))

meta = dict(res=RES, x0=X0, y0=Y0, nx=NX, ny=NY, ray_start_z=2.05, hard_top=HARD_TOP,
            sweep_heights=SWEEP_HEIGHTS, classes=dict(FLOOR=FLOOR, SOFT=SOFT, HARD=HARD),
            counts=dict(floor=int((cls == FLOOR).sum()), soft=int((cls == SOFT).sum()), hard=int((cls == HARD).sum()),
                        hard_added_by_sweeps=int((cls == HARD).sum()) - hits_before),
            door_state=dict(swing=T.SWING_DOORS, sliders=list(T.SLIDERS)))
with open(os.path.join(OUT, 'grid_meta.json'), 'w') as f:
    json.dump(meta, f, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, 'object_bboxes.json'), 'w') as f:
    json.dump(objects, f, ensure_ascii=False)
for stale in ('blocked.npy', 'clearance.npy'):
    if os.path.exists(os.path.join(OUT, stale)):
        os.remove(os.path.join(OUT, stale))
print('PLAN_MAP_DONE', json.dumps(meta, ensure_ascii=False))
