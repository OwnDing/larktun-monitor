import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from motion import install,apply_frame
sc=bpy.data.scenes['Larktun Film'];bpy.context.window.scene=sc;install()
for f in (361,379,409,424,840,811,826,480):
    sc.frame_set(f);apply_frame(sc);render(OUT/f'gates/F/ui_{f:04d}.png',sc.camera,32)
print('F CHECKS COMPLETE',flush=True)
