"""Overlay the obstacle map, and optionally the camera path, on the top-down render.

python tour/draw_plan.py [--path out/tour/plan/path.json] [--out file.png]

renders/02_俯视平面.png is REVIEW_02: orthographic, 16.4 m across 2200 px,
centred on drawing point (6.6, 4.38), north up.  The canvas is extended north so
the approach to the entry door is visible.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PX_PER_M = 2200 / 16.4
CX, CY = 6.6, 4.38
TOP_PAD = 260
FONT = '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'


def to_px(x, y):
    return 1100 + (x - CX) * PX_PER_M, 825 + TOP_PAD + (y - CY) * PX_PER_M


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def overlay(plan_dir):
    meta = json.loads((plan_dir / 'grid_meta.json').read_text())
    cls = np.load(plan_dir / 'cls.npy')
    hard = np.load(plan_dir / 'clear_hard.npy')
    render = Image.open(ROOT / 'renders/02_俯视平面.png').convert('RGB')
    base = Image.new('RGB', (render.width, render.height + TOP_PAD), render.getpixel((5, 5)))
    base.paste(render, (0, TOP_PAD))
    w, h = base.size
    ys, xs = np.mgrid[0:h, 0:w]
    gx = np.floor((CX + (xs - 1100) / PX_PER_M - meta['x0']) / meta['res']).astype(int)
    gy = np.floor((CY + (ys - 825 - TOP_PAD) / PX_PER_M - meta['y0']) / meta['res']).astype(int)
    inside = (gx >= 0) & (gx < meta['nx']) & (gy >= 0) & (gy < meta['ny'])
    gx, gy = gx.clip(0, meta['nx'] - 1), gy.clip(0, meta['ny'] - 1)
    c = np.where(inside, cls[gy, gx], 2)
    ch = np.where(inside, hard[gy, gx], 0)
    img = np.asarray(base).astype(np.float32)
    layers = [((c == 2), (120, 25, 25), 0.40),
              ((c == 1), (40, 70, 190), 0.30),
              ((c == 0) & (ch < 0.25), (235, 140, 20), 0.32),
              ((c == 0) & (ch >= 0.25), (40, 150, 70), 0.15)]
    for mask, color, alpha in layers:
        img[mask] = img[mask] * (1 - alpha) + np.array(color, np.float32) * alpha
    out = Image.fromarray(img.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(out)
    f = font(22)
    for x in range(-1, 15):
        px, _ = to_px(x, 0)
        d.line([(px, 0), (px, h)], fill=(60, 60, 200), width=1)
        d.text((px + 3, 4), str(x), fill=(40, 40, 160), font=f)
    for y in range(-3, 12):
        _, py = to_px(0, y)
        d.line([(0, py), (w, py)], fill=(60, 60, 200), width=1)
        d.text((4, py + 2), str(y), fill=(40, 40, 160), font=f)
    return out


def draw_path(img, path):
    d = ImageDraw.Draw(img)
    fps = int(path.get('fps', 30))
    pts = [to_px(x, y) for x, y in path['points']]
    d.line(pts, fill=(20, 90, 230), width=5)
    f = font(24)
    for i in range(0, len(pts), fps * 10):
        x, y = pts[i]
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(255, 255, 255), outline=(20, 90, 230), width=3)
        d.text((x + 9, y - 30), f"{(i + path.get('first_frame', 0)) // fps}s", fill=(10, 40, 140), font=f)
    for s in path.get('stations', []):
        x, y = to_px(s['x'], s['y'])
        d.rectangle([x - 9, y - 9, x + 9, y + 9], fill=(230, 40, 90))
        d.text((x + 12, y + 4), s['name'], fill=(160, 0, 60), font=f)
    for a in path.get('warnings', []):
        x, y = to_px(a['x'], a['y'])
        d.ellipse([x - 16, y - 16, x + 16, y + 16], outline=(255, 0, 0), width=5)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan-dir', default=str(ROOT / 'out/tour/plan'))
    ap.add_argument('--path')
    ap.add_argument('--out')
    args = ap.parse_args()
    plan_dir = Path(args.plan_dir)
    img = overlay(plan_dir)
    if args.path:
        img = draw_path(img, json.loads(Path(args.path).read_text()))
    out = Path(args.out) if args.out else plan_dir / ('path_overlay.png' if args.path else 'walkable_overlay.png')
    img.save(out)
    print(out)


if __name__ == '__main__':
    main()
