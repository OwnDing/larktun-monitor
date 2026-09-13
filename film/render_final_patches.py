"""Production-setting S05 safe-area and six-frame S07 light-scope corrections."""
import sys,time,argparse,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from motion import install,apply_frame
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args(args)
sc=bpy.data.scenes['Larktun Film'];bpy.context.window.scene=sc;install()
sc.render.engine='BLENDER_EEVEE';sc.eevee.use_raytracing=True;sc.eevee.use_fast_gi=True;sc.eevee.fast_gi_distance=.35
sc.view_settings.view_transform='AgX';sc.render.fps=30
dest=OUT/('gates/G/final_corrections' if a.apply else 'gates/G/S05_caption_safezone');dest.mkdir(parents=True,exist_ok=True)
assert sha(HOME)==json.loads(STATE.read_text())['source_home_sha256']
if not a.apply:
    sc.frame_set(424);apply_frame(sc);render(dest/'preview_0424.png',sc.camera,64)
    print('S05 safe-area preview complete',flush=True)
else:
    progress=json.loads((OUT/'render_progress.json').read_text())
    assert progress['status']=='complete' and progress['last_completed_frame']==1200, 'Main render must finish first.'
    metadata=json.loads((OUT/'frames_manifest.json').read_text());assert len(metadata)==1200
    old_dir=dest/'before';old_dir.mkdir(exist_ok=True)
    t0=time.monotonic();rows=[]
    frames=list(range(361,451))+list(range(541,547))
    for index,f in enumerate(frames,1):
        path=OUT/f'frames/{f:04d}.png';old=metadata[str(f)]
        assert sha(path)==old['sha256']
        shutil.copy2(path,old_dir/path.name)
        t=time.monotonic();sc.frame_set(f);apply_frame(sc);render(path,sc.camera,64)
        new=dict(camera=sc.camera.name,location=list(sc.camera.location),rotation_euler_deg=[math.degrees(v) for v in sc.camera.rotation_euler],ortho_scale=sc.camera.data.ortho_scale,view_layer=bpy.context.view_layer.name,seconds=time.monotonic()-t,sha256=sha(path))
        assert all(new[k]==old[k] for k in ('camera','location','rotation_euler_deg','ortho_scale','view_layer'))
        metadata[str(f)]=new;rows.append(dict(frame=f,before_sha256=old['sha256'],after_sha256=new['sha256']))
        if index%10==0 or index==len(frames):print('FINAL PATCH',index,'/',len(frames),flush=True)
    elapsed=time.monotonic()-t0
    dump(OUT/'frames_manifest.json',metadata)
    progress['elapsed_seconds']+=elapsed;progress['final_patch_seconds']=elapsed;progress['final_patch_frames']=len(frames)
    dump(OUT/'render_progress.json',progress)
    report=dict(status='PASS',reason='S05: move the animated paywall group upward by 48 SVG units so locked y=1560 captions do not cover the CTA. S07: keep the first six frames from enabling unrelated S08/S09 path-fill lights. Original source SVG, copy, price placeholder and cameras unchanged; the three base light banks and their settings are unchanged.',
        ranges=[dict(shot='S05',start=361,end=450),dict(shot='S07',start=541,end=546)],seconds=elapsed,resolution=[1080,1920],samples=64,raytracing=True,
        original_svg_sha256=sha(OUT/'ui/S05_original.svg'),camera_unchanged=True,
        helper_copy='The same small helper sentence is moved above the CTA and set to 14 SVG units, leaving the fixed narrative caption below the button.',
        source_sequence_sha256={str(f):sha(OUT/f'ui/frames/S05/{f:04d}.png') for f in range(1,91)},replacements=rows)
    dump(dest/'patch_report.json',report)
    print('All 96 correction frames complete',elapsed,flush=True)
