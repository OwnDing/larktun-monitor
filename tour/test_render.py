"""EEVEE look and timing probe for the walkthrough.

blender -b Larktun_Home.blend --python tour/test_render.py -- OUTPUT_DIR
"""
import json
import os
import sys
import time

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tour_scene as T  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(argv[0] if argv else 'out/tour/tests')
os.makedirs(OUT, exist_ok=True)

sc = bpy.context.scene
applied = T.configure_eevee(sc, samples=32)
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
sc.render.image_settings.file_format = 'JPEG'
sc.render.image_settings.quality = 92
cam = T.make_camera(sc, 'TOUR_TEST', lens=22)
report = dict(eevee=applied, renders=[])


def shot(name, pos, target, samples=32, lens=22.0, exposure=0.3):
    sc.eevee.taa_render_samples = samples
    cam.data.lens = lens
    sc.view_settings.exposure = exposure
    T.look_at(cam, pos, target)
    sc.render.filepath = os.path.join(OUT, name + '.jpg')
    t = time.monotonic()
    bpy.ops.render.render(write_still=True)
    dt = time.monotonic() - t
    report['renders'].append(dict(name=name, samples=samples, lens=lens, seconds=round(dt, 2)))
    print('RENDERED', name, samples, round(dt, 2), flush=True)


shot('a_overview_se', (22.5, 21.5, 15.5), (6.6, 4.3, 0.2), lens=32)
shot('b_front_door_cutaway', (7.8, -4.2, 1.55), (7.8, 0.0, 1.25), lens=22)
T.show_full_interior(sc)
T.open_doors()
shot('c_front_door_full', (7.8, -4.2, 1.55), (7.8, 0.0, 1.25), lens=22, exposure=0.5)
shot('d_entry_hall', (7.7, 0.9, 1.5), (7.6, 4.0, 1.2), exposure=0.5)
shot('e_living_from_junction', (7.75, 3.8, 1.5), (4.5, 6.8, 0.9), exposure=0.5)
shot('e_living_from_junction_repeat', (7.75, 3.8, 1.5), (4.5, 6.8, 0.9), exposure=0.5)
shot('e_living_16spp', (7.75, 3.8, 1.5), (4.5, 6.8, 0.9), samples=16, exposure=0.5)
shot('e_living_64spp', (7.75, 3.8, 1.5), (4.5, 6.8, 0.9), samples=64, exposure=0.5)
shot('f_dining_to_kitchen', (4.4, 2.6, 1.5), (1.0, 1.2, 1.0), exposure=0.5)
shot('g_master_bath', (0.45, 5.35, 1.5), (2.6, 3.9, 1.0), exposure=0.5)
shot('h_kids_room', (9.95, 7.55, 1.5), (12.3, 5.7, 0.8), exposure=0.5)
shot('i_study', (9.9, 2.75, 1.5), (12.5, 0.9, 1.0), exposure=0.5)

with open(os.path.join(OUT, 'timing.json'), 'w') as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print('TEST_RENDER_DONE', json.dumps(report), flush=True)
