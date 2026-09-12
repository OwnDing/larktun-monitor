"""Read-only checks on the actual saved .blend, not construction globals."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sc=bpy.context.scene
original_layer=bpy.context.window.view_layer if bpy.context.window else None
if bpy.context.window:
    # Excluded objects do not have evaluated world matrices in the cutaway depsgraph.
    bpy.context.window.view_layer=sc.view_layers['02 · FULL INTERIOR']
    bpy.context.view_layer.update()
issues=[]
for o in bpy.data.objects:
    if not all(math.isfinite(v) for row in o.matrix_world for v in row): issues.append('Non-finite transform: '+o.name)
    if o.type=='MESH' and not len(o.data.vertices): issues.append('Empty mesh: '+o.name)
missing=[]
for im in bpy.data.images:
    if im.source=='FILE' and not im.packed_file and im.filepath and not Path(bpy.path.abspath(im.filepath)).exists(): missing.append(im.filepath)
if missing: issues.append('Missing textures')
security=sorted(o.get('camera_id') for o in bpy.data.objects if o.get('larktun_role')=='security_camera')
devices=sorted(o.get('device_id') for o in bpy.data.objects if o.get('larktun_role')=='network_device')
if security!=['C1','C2','C3']: issues.append('Security camera inventory mismatch')
if devices!=['D1','D2','D3','D4','D5']: issues.append('Network device inventory mismatch')
if any(m.type=='CLOTH' for o in bpy.data.objects for m in o.modifiers): issues.append('Unapplied live cloth remains')
if sc.frame_end!=1: issues.append('Unexpected animation timeline')
if len(sc.view_layers)!=2: issues.append('Missing cutaway/full view layer')
duvets=[{'name':o.name,'construction':o.get('construction')} for o in bpy.data.objects if o.name.endswith('soft duvet')]
source_json=json.loads(bpy.data.texts['SOURCE_LAYOUT.json'].as_string())
walls=[o for o in bpy.data.objects if o.name.startswith('W') and '/ continuous full height' in o.name]
max_wall_z=max((o.matrix_world@Vector(c)).z for o in walls for c in o.bound_box)
if abs(max_wall_z-2.8)>.001: issues.append('Full wall height mismatch')
report={'status':'PASS' if not issues else 'FAIL','blender_version':bpy.app.version_string,
        'saved_file':bpy.data.filepath,'objects':len(bpy.data.objects),'materials':len(bpy.data.materials),
        'security_cameras':security,'network_devices':devices,'missing_external_assets':missing,
        'view_layers':[l.name for l in sc.view_layers],'full_wall_height_m':round(max_wall_z,4),
        'units':sc.unit_settings.system,'cloth_applied':duvets,'timeline':[sc.frame_start,sc.frame_end],
        'review_cameras':len([o for o in bpy.data.objects if o.type=='CAMERA' and o.name.startswith('REVIEW_')]),
        'issues':issues,'scope':'Saved-file integrity and asset checks; composition checked separately in rendered PNGs'}
(ROOT/'blender/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
if original_layer: bpy.context.window.view_layer=original_layer
if issues: raise RuntimeError('; '.join(issues))
