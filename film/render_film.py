"""Measured benchmark and resumable one-process 1200-frame Eevee render."""
import sys,time,argparse,statistics
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from motion import install,apply_frame
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['benchmark','render'],default='benchmark');p.add_argument('--approved-over-two-hours',action='store_true');p.add_argument('--resume',action='store_true');a=p.parse_args(args)
sc=bpy.data.scenes['Larktun Film'];bpy.context.window.scene=sc;install()
sc.render.engine='BLENDER_EEVEE';sc.render.fps=30;sc.frame_start=1;sc.frame_end=1200
sc.eevee.use_raytracing=True;sc.eevee.use_fast_gi=True;sc.eevee.fast_gi_distance=.35;sc.eevee.taa_render_samples=64
sc.view_settings.view_transform='AgX';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='16'
sc.render.resolution_x=1080;sc.render.resolution_y=1920;sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=sc.render.pixel_aspect_y=1
state=json.loads(STATE.read_text());assert sha(HOME)==state['source_home_sha256']
assert json.loads((OUT/'gates/C/histogram_report.json').read_text())['status']=='PASS'
shots=json.loads(sc['film_timeline'])
if a.mode=='benchmark':
    frames=[20,135,225,340,424,495,552,675,770,840,945,1030,1110,1155]
    rows=[]
    for f in frames:
        shot,start,end,vid,look=next(s for s in shots if s[1]<=f<=s[2]);t=time.monotonic();sc.frame_set(f);apply_frame(sc)
        render(OUT/f'gates/G/benchmark/{f:04d}.png',sc.camera,64);seconds=time.monotonic()-t
        rows.append(dict(shot=shot,frame=f,seconds_including_state_update=seconds,shot_frames=end-start+1))
        print('BENCHMARK',shot,f,round(seconds,3),flush=True)
    base=sum(r['seconds_including_state_update']*r['shot_frames'] for r in rows);estimate=base*1.25
    report=dict(status='approval_required' if estimate>7200 else 'within_two_hours',engine=sc.render.engine,blender_version=bpy.app.version_string,resolution=[1080,1920],samples=64,raytracing=True,fast_gi_distance=.35,frame_count=1200,method='One actual production-setting frame per shot, weighted by shot duration; includes frame/depsgraph update; 25% reserve.',measurements=rows,weighted_seconds=base,estimated_seconds_with_25_percent_reserve=estimate,estimated_minutes=estimate/60,full_render_started=False)
    dump(OUT/'gates/G/render_estimate.json',report);sc.frame_set(91);apply_frame(sc)
    # Persist final render settings without declaring phase G complete.
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(FILM),compress=True)
    print('ESTIMATED_MINUTES',estimate/60,flush=True)
else:
    estimate=json.loads((OUT/'gates/G/render_estimate.json').read_text())
    assert set('ABCDEF')<=set(state['completed_stages'])
    assert estimate['estimated_seconds_with_25_percent_reserve']<=7200 or a.approved_over_two_hours,'User approval required above two hours.'
    dest=OUT/'frames';dest.mkdir(exist_ok=True,parents=True);starttime=time.monotonic();progress=[]
    previous_metadata=json.loads((OUT/'frames_manifest.json').read_text()) if a.resume and (OUT/'frames_manifest.json').exists() else {}
    prior_elapsed=json.loads((OUT/'render_progress.json').read_text())['elapsed_seconds'] if a.resume and (OUT/'render_progress.json').exists() else 0
    metadata={};rendered=[];skipped=[]
    for frame in range(1,1201):
        path=dest/f'{frame:04d}.png';t=time.monotonic();sc.frame_set(frame);apply_frame(sc)
        old=previous_metadata.get(str(frame))
        verified_existing=bool(a.resume and old and path.exists() and sha(path)==old['sha256'])
        if verified_existing:skipped.append(frame)
        else:render(path,sc.camera,64);rendered.append(frame)
        duration=time.monotonic()-t
        metadata[str(frame)]=old if verified_existing else dict(camera=sc.camera.name,location=list(sc.camera.location),rotation_euler_deg=[math.degrees(v) for v in sc.camera.rotation_euler],ortho_scale=sc.camera.data.ortho_scale,view_layer=bpy.context.view_layer.name,seconds=duration,sha256=sha(path))
        if frame%10==0 or frame==1:
            elapsed=prior_elapsed+time.monotonic()-starttime
            dump(OUT/'render_progress.json',dict(status='rendering',last_completed_frame=frame,total_frames=1200,elapsed_seconds=elapsed,rendered_this_run=len(rendered),skipped_existing=len(skipped)))
            print('FILM FRAME',frame,'/1200; elapsed',round(elapsed,1),'s',flush=True)
        if frame%90==0 or frame==1200:dump(OUT/'frames_manifest.json',metadata)
    elapsed=prior_elapsed+time.monotonic()-starttime
    dump(OUT/'render_progress.json',dict(status='complete',last_completed_frame=1200,total_frames=1200,elapsed_seconds=elapsed,rendered_this_run=len(rendered),skipped_existing=len(skipped)))
    dump(OUT/'frames_manifest.json',metadata)
    print('ALL 1200 FRAMES COMPLETE',elapsed,flush=True)
