"""Check the keyed camera: clearance to geometry and close-up framing.

blender -b Larktun_Tour.blend --python tour/check_tour.py -- [--step 2] [--limit 0.15] [--view-limit 0.8]

Clearance: 48 rays leave the evaluated camera position; the nearest hit within 0.6 m
is recorded.  Framing: five rays around the view axis measure what the shot looks
at; a stretch of at least half a second nearer than --view-limit means the camera is
staring at a wall or a piece of furniture.  Writes out/tour/plan/check_report.json.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(bpy.data.filepath).resolve().parent
VIEW_OFFSETS = ((0.0, 0.0), (0.27, 0.0), (-0.27, 0.0), (0.0, 0.15), (0.0, -0.15))  # about ±15° across, ±8.5° up/down


def directions(n=48):
    golden = math.pi * (3 - math.sqrt(5))
    out = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        out.append(Vector((r * math.cos(i * golden), r * math.sin(i * golden), z)))
    return out


def view_distance(scene, dg, camera):
    basis = camera.matrix_world.to_3x3()
    origin = camera.matrix_world.translation
    forward, right, up = -(basis @ Vector((0, 0, 1))), basis @ Vector((1, 0, 0)), basis @ Vector((0, 1, 0))
    hits = []
    for dx, dy in VIEW_OFFSETS:
        ok, location, _n, _i, _o, _m = scene.ray_cast(dg, origin, (forward + right * dx + up * dy).normalized(), distance=50.0)
        hits.append((location - origin).length if ok else 50.0)
    return sorted(hits)[len(hits) // 2]


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--step', type=int, default=1)
    ap.add_argument('--limit', type=float, default=0.15)
    ap.add_argument('--view-limit', type=float, default=0.8)
    args = ap.parse_args(argv)

    scene = bpy.context.scene
    frames = json.loads((ROOT / scene['tour_frames']).read_text())
    labels = frames['labels']
    rays = directions()
    close, series, close_views = [], [], []
    run = []
    checked = list(range(frames['walk_start_frame'] - 60, scene.frame_end + 1, args.step))
    for f in checked:
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        camera = scene.camera.evaluated_get(dg)
        origin = camera.matrix_world.translation.copy()
        nearest, hit_name = 0.6, ''
        for d in rays:
            ok, location, _n, _i, obj, _m = scene.ray_cast(dg, origin, d, distance=0.6)
            if ok and (location - origin).length < nearest:
                nearest, hit_name = (location - origin).length, obj.name
        series.append(round(nearest, 3))
        if nearest < args.limit:
            close.append(dict(frame=f, label=labels[f - 1], distance=round(nearest, 3), object=hit_name,
                              drawing_xy=[round(origin.x, 2), round(-origin.y, 2)]))
        view = view_distance(scene, dg, camera)
        if view < args.view_limit:
            run.append((f, view))
        if run and (view >= args.view_limit or f == checked[-1]):
            if (run[-1][0] - run[0][0] + args.step) >= frames['fps'] // 2:
                close_views.append(dict(frames=[run[0][0], run[-1][0]], seconds=round((run[-1][0] - run[0][0]) / frames['fps'], 2),
                                        label=labels[run[0][0] - 1], nearest_view_m=round(min(v for _, v in run), 2)))
            run = []
    report = dict(frames_checked=len(series), step=args.step, limit_m=args.limit, min_distance_m=min(series),
                  frames_under_limit=len(close), under_limit=close[:200],
                  view_limit_m=args.view_limit, close_up_stretches=close_views)
    out = ROOT / 'out/tour/plan/check_report.json'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1))
    summary = {k: v for k, v in report.items() if k not in ('under_limit', 'close_up_stretches')}
    summary['close_up_stretches'] = len(close_views)
    print('CHECK_TOUR_DONE', json.dumps(summary, ensure_ascii=False))
    for c in close[:20]:
        print('  close', c)
    for v in close_views:
        print('  stare', v)


if __name__ == '__main__':
    main()
