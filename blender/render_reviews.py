"""Render selected still reviews from the saved, editable Blender project."""
import bpy, argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--shots',default='01,02,03,04,05,06,07,08,09')
p.add_argument('--size',type=int,default=1800)
p.add_argument('--samples',type=int,default=96)
p.add_argument('--cpu',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
sc=bpy.context.scene
if not bpy.data.filepath: bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Larktun_Home.blend')); sc=bpy.context.scene
if not a.cpu:
    pref=bpy.context.preferences.addons['cycles'].preferences; pref.compute_device_type='METAL'; pref.get_devices()
    for d in pref.devices: d.use=d.type=='METAL'
sc.cycles.device='CPU' if a.cpu else 'GPU'
sc.cycles.samples=a.samples
sc.cycles.use_denoising=True
sc.cycles.adaptive_threshold=.02
sc.render.resolution_percentage=100
labels={'01':'01_整户等距','02':'02_俯视平面','03':'03_客厅','04':'04_厨房','05':'05_主卧','06':'06_儿童房','07':'07_茶几细节','08':'08_书房与网络设备','09':'09_主卫'}
for num in a.shots.split(','):
    sc.camera=next(o for o in bpy.data.objects if o.type=='CAMERA' and o.name.startswith('REVIEW_'+num+' '))
    layer=sc.view_layers[0] if num in ('01','02') else sc.view_layers[1]
    for l in sc.view_layers: l.use=l==layer
    if bpy.context.window: bpy.context.window.view_layer=layer
    sc.view_settings.exposure=.3 if num in ('01','02') else .5
    sc.render.resolution_x=a.size; sc.render.resolution_y=round(a.size*(.75 if num in ('01','02') else .6667))
    sc.render.filepath=str(ROOT/'renders'/(labels[num]+'.png'))
    print('RENDERING',num,sc.render.filepath,flush=True)
    bpy.ops.render.render(write_still=True,layer=layer.name)
print('REVIEW RENDERS COMPLETE',flush=True)
