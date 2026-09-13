"""Read-only evidence from completed render plates and encoded deliverables."""
from pathlib import Path
import argparse, hashlib, json, math, struct, subprocess, time
import numpy as np
from PIL import Image
from contact_sheets import grid

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out'
FFMPEG='/opt/homebrew/bin/ffmpeg'
FFPROBE='/opt/homebrew/bin/ffprobe'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text())
def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def png_header(path):
    with Path(path).open('rb') as stream:head=stream.read(33)
    assert head[:8]==b'\x89PNG\r\n\x1a\n' and head[12:16]==b'IHDR',path
    w,h,depth,color,compression,filtering,interlace=struct.unpack('>IIBBBBB',head[16:29])
    return dict(width=w,height=h,bit_depth=depth,color_type=color)

def validate_render():
    progress=load(OUT/'render_progress.json');manifest=load(OUT/'frames_manifest.json')
    assert progress['status']=='complete' and progress['last_completed_frame']==1200
    assert set(manifest)==set(map(str,range(1,1201)))
    expected=[OUT/f'frames/{frame:04d}.png' for frame in range(1,1201)]
    assert set((OUT/'frames').glob('*.png'))==set(expected)
    errors=[];same_camera_positions={};format_counts={}
    for frame,path in enumerate(expected,1):
        header=png_header(path);entry=manifest[str(frame)]
        if header!=dict(width=1080,height=1920,bit_depth=16,color_type=6):errors.append([frame,'PNG format',header])
        with Image.open(path) as im:im.verify()
        if sha(path)!=entry['sha256']:errors.append([frame,'SHA-256 mismatch'])
        rx,ry,rz=entry['rotation_euler_deg']
        if abs(rx-54.7356)>1e-5 or abs(ry)>1e-5 or min(abs(rz-z) for z in (45,135,225,315))>1e-5:
            errors.append([frame,'camera Euler',entry['rotation_euler_deg']])
        baseline=same_camera_positions.setdefault(entry['camera'],entry['location'])
        if baseline!=entry['location']:errors.append([frame,'camera moved'])
        key=str(header);format_counts[key]=format_counts.get(key,0)+1
    assert not errors,errors
    prior=load(OUT/'gates/E/S02_S08_camera_alignment.json')
    assert prior['status']=='PASS' and len(prior['pairs'])==90
    dest=OUT/'gates/G/alignment';dest.mkdir(parents=True,exist_ok=True)
    pairs=[]
    for offset in range(90):
        af,bf=91+offset,631+offset;a,b=manifest[str(af)],manifest[str(bf)]
        keys=('camera','location','rotation_euler_deg','ortho_scale','view_layer')
        same=all(a[k]==b[k] for k in keys)
        assert same,(af,bf)
        ai=Image.open(OUT/f'frames/{af:04d}.png').convert('RGB')
        bi=Image.open(OUT/f'frames/{bf:04d}.png').convert('RGB')
        overlay=dest/f'S02_{af:04d}_S08_{bf:04d}.png'
        Image.blend(ai,bi,.5).save(overlay,compress_level=3)
        pairs.append(dict(S02_frame=af,S08_frame=bf,camera_and_look_identical=same,
                          body_pose_max_abs_delta=prior['pairs'][offset]['body_pose_max_abs_delta'],
                          overlay=str(overlay.relative_to(ROOT)),overlay_sha256=sha(overlay)))
    paths=[];labels=[]
    for offset in (0,44,89):
        af,bf=91+offset,631+offset
        paths.extend([OUT/f'frames/{af:04d}.png',OUT/f'frames/{bf:04d}.png',dest/f'S02_{af:04d}_S08_{bf:04d}.png'])
        labels.extend([f'S02 f{af}',f'S08 f{bf}','50% overlay'])
    grid(paths,labels,OUT/'gates/G/S02_S08_overlay_contact_sheet.png',3,360,640)
    dump(OUT/'gates/G/S02_S08_rendered_alignment.json',dict(status='PASS',paired_frames=90,
         comparison='Actual rendered-camera metadata is exactly equal in all 90 pairs. Full skeletal-pose matrices independently checked in E. Every rendered pair has a 50% overlay; image pixels intentionally differ because the flow color, direction and local illumination change.',
         camera=manifest['91'],look_at_drawing=[6,4.6,1.3],world_coverage_m=[10.125,18],pairs=pairs))
    selected=list(range(50,1201,50))
    grid([OUT/f'frames/{f:04d}.png' for f in selected],[f'RAW f{f}' for f in selected],OUT/'gates/F/fullfilm_contact_sheet.png')
    luminance=[]
    for f in selected:
        arr=np.asarray(Image.open(OUT/f'frames/{f:04d}.png').convert('RGB'),dtype=np.float32)/255
        y=arr@np.array([.2126,.7152,.0722],dtype=np.float32)
        luminance.append(dict(frame=f,look=manifest[str(f)]['view_layer'],low_0_to_025_fraction=float((y<=.25).mean()),median=float(np.median(y))))
    assert sha(ROOT/'Larktun_Home.blend')==load(ROOT/'film/production_state.json')['source_home_sha256']
    report=dict(status='PASS',frame_count=1200,resolution=[1080,1920],png_bit_depth=16,png_color_mode='RGBA',
                full_png_crc_and_sha256_checked=True,errors=errors,render_seconds=progress['elapsed_seconds'],
                original_home_unchanged=True,paired_rendered_camera_frames=90,
                selected_every_50_frames=selected,selected_luminance=luminance,
                note='Gate C thresholds apply to its calibrated look frames. This final-frame sample includes emissive effects and tightly cropped UI, which have different histograms.')
    dump(OUT/'gates/G/render_validation.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='selected_luminance'},ensure_ascii=False),flush=True)

def decode_black_tail(path):
    proc=subprocess.Popen([FFMPEG,'-v','error','-threads','4','-i',str(path),'-vf','select=gte(n\\,1185)',
            '-fps_mode','passthrough','-pix_fmt','rgb24','-f','rawvideo','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    size=1080*1920*3;maximum=0;frames=0
    while True:
        buf=proc.stdout.read(size)
        if not buf:break
        assert len(buf)==size
        maximum=max(maximum,max(buf));frames+=1
    error=proc.stderr.read().decode();assert proc.wait()==0,error
    assert frames==15 and maximum==0,(frames,maximum)
    return dict(decoded_black_frames=frames,maximum_rgb_channel_value=maximum)

def validate_videos():
    from compose_film import CAPTIONS,base_caption,font,caption_frame
    composition=load(OUT/'composite_manifest.json')
    assert composition['status']=='COMPLETE'
    by_frame={entry['frame']:entry for entry in composition['frames']}
    logo_hold_hashes={by_frame[f]['clean_sha256'] for f in range(1150,1186)}
    assert len(logo_hold_hashes)==1 and by_frame[1149]['clean_sha256'] not in logo_hold_hashes
    reports=[]
    for name in ('clean','sub'):
        path=OUT/f'larktun_01_{name}.mp4'
        result=subprocess.run([FFPROBE,'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,check=True)
        probe=json.loads(result.stdout);streams=probe['streams']
        assert len(streams)==1 and streams[0]['codec_type']=='video',streams
        s=streams[0]
        assert (s['width'],s['height'])==(1080,1920)
        assert s['r_frame_rate']=='30/1' and s['avg_frame_rate']=='30/1'
        assert int(s['nb_read_frames'])==1200 and abs(float(s['duration'])-40)<1e-6
        assert s['codec_name']=='h264' and s['pix_fmt']=='yuv420p'
        assert all(s.get(k)=='bt709' for k in ('color_space','color_transfer','color_primaries'))
        subprocess.run([FFMPEG,'-v','error','-xerror','-threads','4','-i',str(path),'-f','null','-'],check=True,capture_output=True)
        black=decode_black_tail(path)
        reports.append(dict(file=str(path.relative_to(ROOT)),sha256=sha(path),bytes=path.stat().st_size,
            resolution=[s['width'],s['height']],fps=s['r_frame_rate'],duration_seconds=float(s['duration']),
            decoded_frame_count=int(s['nb_read_frames']),audio_streams=0,full_null_decode='PASS',**black))
        dump(OUT/f'gates/H/ffprobe_{name}.json',probe)
    captions=[]
    for entry in CAPTIONS['captions']:
        bounds=base_caption(entry['shot']).getbbox()
        assert bounds is None or (bounds[0]>=60 and bounds[2]<=1020 and bounds[1]>=0 and bounds[3]<=1600),bounds
        captions.append(dict(shot=entry['shot'],pixel_bounds=bounds,
            line_baselines=[1560-(len(entry['lines'])-1-i)*102 for i in range(len(entry['lines']))]))
    assert all(caption_frame(f).getbbox() is None for f in range(1186,1201))
    report=dict(status='PASS',videos=reports,caption_geometry=captions,
         subtitle_font='Noto Sans CJK SC Black',subtitle_font_size_px=74,outline_px=14,
         final_line_baseline_y=1560,caption_burn='FFmpeg overlay of independent raster plates; no libass in installed build.',
         no_audio_created_or_muxed=True,logo_hold_clean_frames=[1150,1185],logo_hold_duration_seconds=1.2,
         original_home_sha256=sha(ROOT/'Larktun_Home.blend'),
         sound_sheet='out/audio_cue_sheet.md',silence_cue_frames=[541,549])
    dump(OUT/'gates/H/delivery_validation.json',report)
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',required=True,choices=['G','H']);a=p.parse_args()
    validate_render() if a.stage=='G' else validate_videos()
