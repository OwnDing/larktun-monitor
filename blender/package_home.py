"""Add packed references and an easy one-click interior scene; geometry unchanged."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sc=bpy.context.scene
for filename in ('平面布置图.svg','等距总览.svg'):
    key='REFERENCE · '+filename
    tx=bpy.data.texts.get(key) or bpy.data.texts.new(key); tx.clear(); tx.write((ROOT/'scene'/filename).read_text())
for filename in ('平面布置图.png','等距总览.png'):
    key='REFERENCE · '+filename
    if not bpy.data.images.get(key):
        im=bpy.data.images.load(str(ROOT/'scene'/filename)); im.name=key; im.pack(); im.use_fake_user=True
for key,path in [('START HERE · HOUSE_README.md',ROOT/'HOUSE_README.md'),('finish_scene.py',ROOT/'blender/finish_scene.py')]:
    tx=bpy.data.texts.get(key) or bpy.data.texts.new(key); tx.clear(); tx.write(path.read_text())
sc.name='01 · House cutaway'
if not bpy.data.scenes.get('02 · House interiors'):
    inside=sc.copy(); inside.name='02 · House interiors'
    inside.camera=bpy.data.objects['REVIEW_03 · Living room']
    inside.view_layers.remove(inside.view_layers[0]); inside.view_layers[0].use=True
    inside.view_settings.exposure=.5
bpy.context.window.scene=sc
bpy.context.window.view_layer=sc.view_layers[0]
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Larktun_Home.blend'),compress=True)
print('Packed reference drawings and interior scene. Geometry unchanged.')
