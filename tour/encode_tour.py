"""Encode rendered tour frames to MP4 and make a contact sheet.

python3 tour/encode_tour.py --mode final     # out/tour/frames/*.png   -> out/tour/larktun_house_tour_1080p.mp4
python3 tour/encode_tour.py --mode preview   # out/tour/preview_frames -> out/tour/larktun_house_tour_preview.mp4

H.264, yuv420p, BT.709 matrix and tags, fade from and to black.
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODES = {
    'final': dict(frames='out/tour/frames', ext='png', out='out/tour/larktun_house_tour_1080p.mp4', crf='17'),
    'preview': dict(frames='out/tour/preview_frames', ext='jpg', out='out/tour/larktun_house_tour_preview.mp4', crf='23'),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=sorted(MODES), default='final')
    ap.add_argument('--step', type=int, default=1, help='frame step the preview was rendered with')
    args = ap.parse_args()
    cfg = MODES[args.mode]
    frames_dir = ROOT / cfg['frames']
    numbers = sorted(int(p.stem) for p in frames_dir.glob('*.' + cfg['ext']))
    meta = json.loads((ROOT / 'out/tour/plan/camera_frames.json').read_text())
    expected = list(range(1, meta['frame_count'] + 1, args.step))
    missing = sorted(set(expected) - set(numbers))
    if missing:
        raise SystemExit(f'{len(missing)} frames missing, first {missing[:10]}')
    fps = meta['fps'] / args.step
    duration = len(expected) / fps
    fade_in, fade_out = meta['fade_in_s'], meta['fade_out_s']
    # setparams: without it the encoder inherits the PNGs' sRGB transfer tag instead of BT.709.
    vf = (f'fade=t=in:st=0:d={fade_in},fade=t=out:st={duration - fade_out:.3f}:d={fade_out},'
          'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,'
          'setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709')
    out = ROOT / cfg['out']
    subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-framerate', f'{fps:g}',
                    '-pattern_type', 'glob', '-i', str(frames_dir / ('*.' + cfg['ext'])),
                    '-vf', vf, '-r', '30', '-c:v', 'libx264', '-preset', 'slow', '-crf', cfg['crf'],
                    '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                    '-movflags', '+faststart', str(out)], check=True)
    sheet = out.with_name(out.stem + '_contact.jpg')
    subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', str(out),
                    '-vf', 'fps=1/5,scale=320:-2,tile=6x7:padding=4:color=white', '-frames:v', '1', str(sheet)], check=True)
    print(out)
    print(sheet)


if __name__ == '__main__':
    main()
