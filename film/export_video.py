"""Encode the complete independent post plates into two silent 40-second films."""
from pathlib import Path
import json,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out'
FFMPEG='/opt/homebrew/bin/ffmpeg'
assert json.loads((OUT/'composite_manifest.json').read_text())['status']=='COMPLETE'
for sequence in ('composite_frames/clean','caption_frames'):
    assert all((OUT/sequence/f'{f:04d}.png').exists() for f in range(1,1201)),sequence
shared=['-frames:v','1200','-an','-c:v','libx264','-threads','4','-preset','medium','-crf','18','-pix_fmt','yuv420p',
        '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',
        '-force_key_frames','0,3,6,9,12,15,18,21,24,27,30,33,36,38,39.5','-movflags','+faststart']
color_filter='scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p,setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709'
subprocess.run([FFMPEG,'-y','-hide_banner','-loglevel','warning','-framerate','30','-start_number','1',
    '-i',str(OUT/'composite_frames/clean/%04d.png'),
    '-vf',color_filter,
    *shared,str(OUT/'larktun_01_clean.mp4')],check=True)
print('Encoded clean silent film',flush=True)
subprocess.run([FFMPEG,'-y','-hide_banner','-loglevel','warning','-framerate','30','-start_number','1',
    '-i',str(OUT/'composite_frames/clean/%04d.png'),
    '-framerate','30','-start_number','1','-i',str(OUT/'caption_frames/%04d.png'),
    '-filter_complex','[0:v]format=rgba[base];[base][1:v]overlay=0:0:format=rgb:shortest=1,'+color_filter+'[v]',
    '-map','[v]',*shared,str(OUT/'larktun_01_sub.mp4')],check=True)
print('Encoded subtitled silent film',flush=True)
