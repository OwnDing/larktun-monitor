"""Render the walkthrough from Larktun_Tour.blend.

blender -b Larktun_Tour.blend --python tour/render_tour.py -- --mode final
blender -b Larktun_Tour.blend --python tour/render_tour.py -- --mode preview [--step 2]
blender -b Larktun_Tour.blend --python tour/render_tour.py -- --mode still --frames 540,600

Frames already on disk are kept, so an interrupted render resumes where it stopped.
EEVEE modes switch on transparent shadows for the rising-wall frames only.
Progress is written next to the frame folder.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import bpy

ROOT = Path(bpy.data.filepath).resolve().parent
OUTPUT = {'final': 'out/tour/frames', 'preview': 'out/tour/preview_frames', 'still': 'out/tour/stills'}


def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=sorted(OUTPUT), default='final')
    ap.add_argument('--start', type=int)
    ap.add_argument('--end', type=int)
    ap.add_argument('--step', type=int, default=1)
    ap.add_argument('--frames', help='comma separated frames for --mode still')
    ap.add_argument('--samples', type=int)
    return ap.parse_args(argv)


def setup_preview(scene):
    scene.render.engine = 'BLENDER_WORKBENCH'
    shading = scene.display.shading
    shading.light = 'STUDIO'
    shading.color_type = 'MATERIAL'
    shading.show_shadows = True
    shading.show_cavity = True
    scene.display.render_aa = '8'
    scene.render.resolution_percentage = 50
    scene.render.use_motion_blur = False
    scene.render.image_settings.file_format = 'JPEG'
    scene.render.image_settings.quality = 90


def rising(scene, frame):
    first, last = scene.get('tour_rise_frames', (0, -1))
    return first <= frame <= last + 1


def transparent_shadows(on):
    for m in bpy.data.materials:
        if m.name.endswith(' · tour cut'):
            m.use_transparent_shadow = on


def segments(scene, start, end, eevee):
    """Frame ranges with a constant shadow mode; Workbench needs no split."""
    if not eevee:
        return [(start, end, False)]
    first, last = scene.get('tour_rise_frames', (0, -1))
    parts = [(start, min(end, first - 1), False), (max(start, first), min(end, last + 1), True),
             (max(start, last + 2), end, False)]
    return [p for p in parts if p[0] <= p[1]]


def main():
    args = parse_args()
    scene = bpy.context.scene
    if args.mode == 'preview':
        setup_preview(scene)
    if args.samples:
        scene.eevee.taa_render_samples = args.samples
    eevee = scene.render.engine == 'BLENDER_EEVEE'
    out_dir = ROOT / OUTPUT[args.mode]
    out_dir.mkdir(parents=True, exist_ok=True)
    scene.render.use_overwrite = False
    scene.render.use_placeholder = False
    ext = '.jpg' if scene.render.image_settings.file_format == 'JPEG' else '.png'

    if args.mode == 'still':
        for f in [int(v) for v in args.frames.split(',')]:
            transparent_shadows(eevee and rising(scene, f))
            scene.frame_set(f)
            scene.render.filepath = str(out_dir / f'{f:04d}')
            t = time.monotonic()
            bpy.ops.render.render(write_still=True)
            print('STILL', f, round(time.monotonic() - t, 2), flush=True)
        return

    start, end = args.start or scene.frame_start, args.end or scene.frame_end
    scene.frame_step = args.step
    scene.render.filepath = str(out_dir) + '/'
    for f in out_dir.glob('*' + ext):
        if f.stat().st_size == 0:
            f.unlink()
    todo = [f for f in range(start, end + 1, args.step) if not (out_dir / f'{f:04d}{ext}').exists()]
    progress = out_dir.parent / f'render_progress_{args.mode}.json'
    started = time.monotonic()
    state = dict(rendered=0)

    def after_frame(sc, *_):
        state['rendered'] += 1
        elapsed = time.monotonic() - started
        per = elapsed / state['rendered']
        progress.write_text(json.dumps(dict(mode=args.mode, frame=sc.frame_current, rendered=state['rendered'],
                                            to_render=len(todo), seconds_per_frame=round(per, 2),
                                            elapsed_min=round(elapsed / 60, 1),
                                            eta_min=round(per * (len(todo) - state['rendered']) / 60, 1))))

    bpy.app.handlers.render_post.append(after_frame)
    print('RENDER', args.mode, 'frames to render:', len(todo), flush=True)
    for first, last, shadows in segments(scene, start, end, eevee):
        if not any(first <= f <= last for f in todo):
            continue
        transparent_shadows(shadows)
        scene.frame_start, scene.frame_end = first, last
        bpy.ops.render.render(animation=True)
    print('RENDER_DONE', args.mode, json.loads(progress.read_text()) if progress.exists() else {}, flush=True)


if __name__ == '__main__':
    main()
