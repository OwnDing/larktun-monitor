"""Mux the mastered soundtrack into both approved cuts. Video packets are stream-copied, never re-encoded."""
from pathlib import Path
import json, subprocess
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'out'
FFMPEG = '/opt/homebrew/bin/ffmpeg'
assert json.loads((OUT / 'audio/sound_manifest.json').read_text())['status'] == 'COMPLETE'
master = OUT / 'audio/larktun_01_mix.wav'
encoders = subprocess.run([FFMPEG, '-hide_banner', '-encoders'], capture_output=True, text=True, check=True).stdout
# Apple's AAC encoder where available; FFmpeg's native AAC otherwise. Both write an edit list for encoder priming.
codec = 'aac_at' if ' aac_at ' in encoders else 'aac'
for name in ('clean', 'sub'):
    subprocess.run([FFMPEG, '-y', '-hide_banner', '-loglevel', 'warning',
                    '-i', str(OUT / f'larktun_01_{name}.mp4'), '-i', str(master),
                    '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy',
                    '-c:a', codec, '-b:a', '256k', '-ar', '48000', '-ac', '2',
                    '-metadata:s:a:0', 'title=Larktun 01 soundtrack', '-disposition:a:0', 'default',
                    '-movflags', '+faststart', str(OUT / f'larktun_01_{name}_audio.mp4')], check=True)
    print('Muxed', name, 'with', codec, flush=True)
