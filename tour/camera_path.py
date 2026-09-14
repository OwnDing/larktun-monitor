"""Human-paced camera for the Larktun walkthrough.

python tour/camera_path.py
  reads  out/tour/plan/{grid_meta.json, cls, clear_hard, clear_body, soft_depth}.npy and tour/route_def.py
  writes out/tour/plan/camera_frames.json  per-frame camera in drawing coordinates (degrees, mm)
         out/tour/plan/path.json           input for draw_plan.py --path
         out/tour/plan/path_report.json    per-leg clearance and timing

Pure NumPy.  build_tour.py converts to Blender and keys the camera.
"""
import heapq
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import route_def as R  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'out/tour/plan'
FPS = R.FPS
DT = 1.0 / FPS
FLOOR, SOFT, HARD = 0, 1, 2

MIN_HARD = 0.20        # map distance to walls, glass, tall furniture, open leaves
MAX_SOFT_DEPTH = 0.15  # how far the camera may skim over low furniture
A_ACC, A_DEC, A_LAT = 0.6, 0.55, 0.35
DOORWAY_SPEED = 0.40   # m/s where clearance is at its minimum
LOOK_AHEAD = 1.3
TURN_BEFORE_LEG = 0.5  # seconds a stop spends turning toward the way out


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def gaussian_smooth(x, sigma):
    r = max(1, int(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    pad = np.concatenate([np.full(r, x[0]), x, np.full(r, x[-1])])
    return np.convolve(pad, k, mode='valid')


def resample(p, ds):
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    n = max(2, int(math.ceil(s[-1] / ds)) + 1)
    t = np.linspace(0.0, s[-1], n)
    return np.stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])], 1)


def dedupe(points):
    out = [points[0]]
    for q in points[1:]:
        if math.dist(q, out[-1]) > 1e-3:
            out.append(q)
    return out


def unit(v):
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


class Maps:
    def __init__(self):
        meta = json.loads((PLAN / 'grid_meta.json').read_text())
        self.res, self.x0, self.y0 = meta['res'], meta['x0'], meta['y0']
        self.cls = np.load(PLAN / 'cls.npy')
        self.hard = np.load(PLAN / 'clear_hard.npy').astype(np.float64)
        self.body = np.load(PLAN / 'clear_body.npy').astype(np.float64)
        self.depth = np.load(PLAN / 'soft_depth.npy').astype(np.float64)
        self.ny, self.nx = self.cls.shape
        self.grad = {k: np.gradient(getattr(self, k), self.res) for k in ('hard', 'body', 'depth')}

    def sample(self, arr, pts):
        pts = np.atleast_2d(pts)
        fx = (pts[:, 0] - self.x0) / self.res - 0.5
        fy = (pts[:, 1] - self.y0) / self.res - 0.5
        i0 = np.clip(np.floor(fx).astype(int), 0, self.nx - 2)
        j0 = np.clip(np.floor(fy).astype(int), 0, self.ny - 2)
        tx, ty = np.clip(fx - i0, 0, 1), np.clip(fy - j0, 0, 1)
        top = arr[j0, i0] * (1 - tx) + arr[j0, i0 + 1] * tx
        bottom = arr[j0 + 1, i0] * (1 - tx) + arr[j0 + 1, i0 + 1] * tx
        return top * (1 - ty) + bottom * ty

    def gradient(self, key, pts):
        gy, gx = self.grad[key]
        return np.stack([self.sample(gx, pts), self.sample(gy, pts)], 1)

    def cell(self, p):
        return (int(np.clip(math.floor((p[1] - self.y0) / self.res), 0, self.ny - 1)),
                int(np.clip(math.floor((p[0] - self.x0) / self.res), 0, self.nx - 1)))

    def center(self, cell):
        return (self.x0 + (cell[1] + 0.5) * self.res, self.y0 + (cell[0] + 0.5) * self.res)

    def cost_grid(self):
        hard_pen = 5.0 * np.clip((0.55 - self.hard) / 0.35, 0, 1) ** 2
        soft_pen = np.where(self.cls == SOFT, 12.0 + 80.0 * self.depth, 3.0 * np.clip((0.28 - self.body) / 0.28, 0, 1))
        cost = 1.0 + hard_pen + soft_pen
        cost[(self.hard < MIN_HARD) | (self.depth > 0.25)] = np.inf
        return cost


def astar(maps, flat_cost, a, b):
    start, goal = maps.cell(a), maps.cell(b)
    ny, nx = maps.ny, maps.nx
    inf = float('inf')
    g = {start: 0.0}
    came = {}
    heap = [(0.0, start)]
    closed = set()
    steps = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
             (-1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)), (1, 1, math.sqrt(2))]
    while heap:
        _, cur = heapq.heappop(heap)
        if cur == goal:
            break
        if cur in closed:
            continue
        closed.add(cur)
        c0 = flat_cost[cur[0] * nx + cur[1]]
        for dj, di, w in steps:
            nb = (cur[0] + dj, cur[1] + di)
            if not (0 <= nb[0] < ny and 0 <= nb[1] < nx):
                continue
            c1 = flat_cost[nb[0] * nx + nb[1]]
            if c1 == inf:
                if nb != goal:
                    continue
                c1 = 50.0
            ng = g[cur] + w * 0.5 * ((c0 if c0 != inf else 50.0) + c1)
            if ng < g.get(nb, inf):
                g[nb] = ng
                came[nb] = cur
                heapq.heappush(heap, (ng + math.hypot(nb[0] - goal[0], nb[1] - goal[1]), nb))
    else:
        raise RuntimeError(f'no walkable path from {a} to {b}')
    cells = [goal]
    while cells[-1] != start:
        cells.append(came[cells[-1]])
    pts = [maps.center(c) for c in reversed(cells)]
    pts[0], pts[-1] = tuple(a), tuple(b)
    return pts


def segment_ok(maps, a, b):
    pts = np.linspace(a, b, max(2, int(math.dist(a, b) / 0.02) + 1))
    return maps.sample(maps.hard, pts).min() >= MIN_HARD + 0.03 and maps.sample(maps.depth, pts).max() <= 0.08


def relax(maps, p, iters=600):
    """Elastic band: smooth like a walked line, pushed off walls and furniture; ends pinned."""
    p = resample(p, 0.04)
    for it in range(iters):
        lap = np.zeros_like(p)
        lap[1:-1] = p[:-2] + p[2:] - 2 * p[1:-1]
        push = np.clip((0.42 - maps.sample(maps.hard, p)) / 0.22, 0, 1.5)[:, None] * unit(maps.gradient('hard', p))
        push += 0.5 * np.clip((0.26 - maps.sample(maps.body, p)) / 0.26, 0, 1)[:, None] * unit(maps.gradient('body', p))
        push -= np.clip(maps.sample(maps.depth, p) / 0.08, 0, 1.5)[:, None] * unit(maps.gradient('depth', p))
        step = 0.2 * lap + 0.01 * push
        step[0] = step[-1] = 0
        p = p + step
        if it % 30 == 29:
            p = resample(p, 0.04)
    return resample(p, 0.02)


def leg_path(maps, flat_cost, points, failures):
    points = dedupe(points)
    raw, used_astar = [points[0]], False
    for a, b in zip(points[:-1], points[1:]):
        if segment_ok(maps, a, b):
            raw.append(b)
            continue
        try:
            raw.extend(astar(maps, flat_cost, a, b)[1:])
            used_astar = True
        except RuntimeError as ex:  # keep going so one run reports every blocked hop
            failures.append(str(ex))
            raw.append(b)
    return relax(maps, np.array(dedupe(raw), float)), used_astar


def leg_timing(maps, p, v_max):
    d = np.diff(p, axis=0)
    ds = np.linalg.norm(d, axis=1)
    s = np.concatenate([[0.0], np.cumsum(ds)])
    heading = np.arctan2(d[:, 1], d[:, 0])
    kappa = np.zeros(len(p))
    kappa[1:-1] = np.abs((np.diff(heading) + math.pi) % (2 * math.pi) - math.pi) / np.maximum(0.5 * (ds[:-1] + ds[1:]), 1e-4)
    kappa = gaussian_smooth(kappa, 6)
    v = np.minimum(np.full(len(p), v_max), np.sqrt(A_LAT / np.maximum(kappa, 1e-6)))
    narrow = DOORWAY_SPEED + 1.5 * (maps.sample(maps.hard, p) - MIN_HARD)
    v = np.minimum(v, np.clip(narrow, DOORWAY_SPEED, v_max))
    v[0] = v[-1] = 0.0
    for i in range(1, len(p)):
        v[i] = min(v[i], math.sqrt(v[i - 1] ** 2 + 2 * A_ACC * ds[i - 1]))
    for i in range(len(p) - 2, -1, -1):
        v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + 2 * A_DEC * ds[i]))
    t = np.concatenate([[0.0], np.cumsum(ds / np.maximum(0.5 * (v[:-1] + v[1:]), 0.02))])
    n = max(2, int(round(t[-1] * FPS)) + 1)
    sf = gaussian_smooth(np.interp(np.linspace(0, t[-1], n), t, s), 4.0)
    sf[0], sf[-1] = 0.0, s[-1]
    return sf, s


def point_along(p, s, q):
    """Point at arc length q; beyond the end, extend along the final direction."""
    if q <= s[-1]:
        return np.array([np.interp(q, s, p[:, 0]), np.interp(q, s, p[:, 1])])
    tail = p[-1] - p[max(0, len(p) - 6)]
    return p[-1] + tail / max(np.linalg.norm(tail), 1e-9) * (q - s[-1])


def hermite(times, values, tq):
    values = np.asarray(values, float)
    m = np.zeros_like(values)
    for k in range(1, len(times) - 1):
        m[k] = (values[k + 1] - values[k - 1]) / (times[k + 1] - times[k - 1])
    out = []
    for t in tq:
        k = int(np.clip(np.searchsorted(times, t, side='right') - 1, 0, len(times) - 2))
        h = times[k + 1] - times[k]
        u = (t - times[k]) / h
        out.append((2 * u ** 3 - 3 * u ** 2 + 1) * values[k] + (u ** 3 - 2 * u ** 2 + u) * h * m[k]
                   + (-2 * u ** 3 + 3 * u ** 2) * values[k + 1] + (u ** 3 - u ** 2) * h * m[k + 1])
    return np.array(out)


def overview():
    o = R.ORBIT
    keys = []
    for t in np.linspace(o['t'][0], o['t'][1], 13):
        u = (t - o['t'][0]) / (o['t'][1] - o['t'][0])
        e = u * u * (2 - u)  # from rest, arriving with speed to continue into the approach
        az = math.radians(o['az'][0] + (o['az'][1] - o['az'][0]) * e)
        radius = o['radius'][0] + (o['radius'][1] - o['radius'][0]) * e
        cam = (R.ORBIT_CENTER[0] + radius * math.cos(az), R.ORBIT_CENTER[1] + radius * math.sin(az),
               o['height'][0] + (o['height'][1] - o['height'][0]) * e)
        look = tuple(a + (b - a) * e for a, b in zip(*o['look']))
        keys.append((t, cam, look, o['lens'][0] + (o['lens'][1] - o['lens'][0]) * e))
    keys += R.APPROACH_KEYS
    times = np.array([k[0] for k in keys])
    tf = np.arange(int(round(times[-1] * FPS))) / FPS
    cam = hermite(times, [k[1] for k in keys], tf)
    look = hermite(times, [k[2] for k in keys], tf)
    lens = hermite(times, [[k[3]] for k in keys], tf)[:, 0]
    return tf, cam, look, lens


def value_noise(t, freq, seed):
    rng = np.random.default_rng(seed)
    knots = rng.uniform(-1, 1, int(t[-1] * freq) + 4)
    x = t * freq
    i = np.floor(x).astype(int)
    f = x - i
    w = f * f * (3 - 2 * f)
    return knots[i] * (1 - w) + knots[i + 1] * w


def fractal(t, freq, seed):
    return 0.62 * value_noise(t, freq, seed) + 0.28 * value_noise(t, freq * 2.13, seed + 1) + 0.10 * value_noise(t, freq * 4.37, seed + 2)


def main():
    maps = Maps()
    flat_cost = maps.cost_grid().ravel().tolist()
    seq = R.SEQUENCE
    assert seq[0]['type'] == 'stop' and all(seq[i]['type'] != seq[i + 1]['type'] for i in range(len(seq) - 1))

    # Plan every leg first so each stop can turn toward the way out before walking.
    legs, failures = {}, []
    for i, item in enumerate(seq):
        if item['type'] == 'leg':
            pts = [seq[i - 1]['at'], *item['via'], seq[i + 1]['at']]
            path, used_astar = leg_path(maps, flat_cost, pts, failures)
            legs[i] = dict(path=path, used_astar=used_astar)
    for failure in failures:
        print('BLOCKED', failure)

    tf, cam_o, look_o, lens_o = overview()
    n_over = len(tf)
    positions, speeds, targets, labels = [], [], [], []
    stations, report = [], []
    eye = R.EYE

    for i, item in enumerate(seq):
        if item['type'] == 'stop':
            dwell = list(item['dwell'])
            if i + 1 < len(seq) and dwell:
                nxt = legs[i + 1]['path']
                s_next = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(nxt, axis=0), axis=1))])
                ahead = point_along(nxt, s_next, LOOK_AHEAD)
                dwell.append((TURN_BEFORE_LEG, (ahead[0], ahead[1], eye - 0.12)))
            start = n_over + len(positions)
            for seconds, target in dwell:
                for _ in range(int(round(seconds * FPS))):
                    positions.append(item['at'])
                    speeds.append(0.0)
                    targets.append(target)
                    labels.append(item['name'])
            stations.append(dict(name=item['name'], x=item['at'][0], y=item['at'][1],
                                 frames=[start + 1, n_over + len(positions)]))
            continue
        p = legs[i]['path']
        sf, s = leg_timing(maps, p, item['speed'])
        cues = sorted(item['look'], key=lambda c: c[0])
        total = s[-1]
        for k in range(1, len(sf)):
            q = sf[k]
            xy = point_along(p, s, q)
            cue = [c for c in cues if c[0] <= q / total + 1e-9][-1][1]
            if cue == 'path':
                ahead = point_along(p, s, q + LOOK_AHEAD)
                cue = (ahead[0], ahead[1], eye - 0.12)
            positions.append(tuple(xy))
            speeds.append((sf[k] - sf[k - 1]) * FPS)
            targets.append(cue)
            labels.append(seq[i + 1]['name'])
        ch = maps.sample(maps.hard, p)
        dep = maps.sample(maps.depth, p)
        report.append(dict(to=seq[i + 1]['name'], length_m=round(float(total), 2), seconds=round((len(sf) - 1) / FPS, 2),
                           used_astar=legs[i]['used_astar'],
                           min_hard=round(float(ch.min()), 3), min_hard_at=[round(float(v), 2) for v in p[int(ch.argmin())]],
                           max_soft_depth=round(float(dep.max()), 3), max_soft_at=[round(float(v), 2) for v in p[int(dep.argmax())]]))

    pos = np.array(positions, float)
    speed = gaussian_smooth(np.array(speeds, float), 3.0)
    n_walk = len(pos)
    t_walk = (n_over + np.arange(n_walk)) / FPS

    # Gaze: aim at each frame's target, then follow with a critically damped spring.
    last_cam, last_look = cam_o[-1], look_o[-1]
    yaw = math.atan2(last_look[1] - last_cam[1], last_look[0] - last_cam[0])
    pitch = math.atan2(last_look[2] - last_cam[2], math.hypot(last_look[0] - last_cam[0], last_look[1] - last_cam[1]))
    # A person pans at up to ~40°/s and eases into and out of a turn.
    vy = vp = 0.0
    wy, wp = 2.2, 2.6
    max_rate, max_accel = math.radians(42), math.radians(120)
    goal_yaw, goal_pitch = yaw, pitch
    yaws, pitches = np.zeros(n_walk), np.zeros(n_walk)
    for k in range(n_walk):
        tx, ty, tz = targets[k]
        dx, dy = tx - pos[k, 0], ty - pos[k, 1]
        dist = math.hypot(dx, dy)
        if dist > 0.25:
            goal_yaw = math.atan2(dy, dx)
            goal_pitch = float(np.clip(math.atan2(tz - eye, dist), math.radians(-35), math.radians(15)))
        gy = yaw + wrap(goal_yaw - yaw)
        for _ in range(4):
            h = DT / 4
            ay = float(np.clip(wy * wy * (gy - yaw) - 2 * wy * vy, -max_accel, max_accel))
            vy = float(np.clip(vy + ay * h, -max_rate, max_rate))
            yaw += vy * h
            ap = float(np.clip(wp * wp * (goal_pitch - pitch) - 2 * wp * vp, -max_accel, max_accel))
            vp = float(np.clip(vp + ap * h, -max_rate, max_rate))
            pitch += vp * h
        yaws[k], pitches[k] = yaw, pitch

    # Drone frames: steady look-at.
    d = look_o - cam_o
    yaw_o = np.unwrap(np.arctan2(d[:, 1], d[:, 0]))
    pitch_o = np.arctan2(d[:, 2], np.hypot(d[:, 0], d[:, 1]))
    yaws = np.unwrap(np.concatenate([yaw_o, yaws]))
    pitches = np.concatenate([pitch_o, pitches])
    xyz = np.concatenate([cam_o, np.column_stack([pos, np.full(n_walk, eye)])])
    lens = np.concatenate([lens_o, np.full(n_walk, R.LENS)])
    speed = np.concatenate([np.zeros(n_over), speed])
    t = np.arange(len(xyz)) / FPS

    # Operator's hand: step bob and sway while walking, breathing and drift when standing.
    handheld = smoothstep((t - R.HANDHELD_RAMP[0]) / (R.HANDHELD_RAMP[1] - R.HANDHELD_RAMP[0]))
    walking = gaussian_smooth(np.clip(speed / 0.30, 0, 1), 6.0)
    phase = np.cumsum((1.5 + 0.8 * np.clip(speed / 0.6, 0, 1.3)) * DT)
    dz = handheld * (-0.0065 * walking * np.cos(2 * math.pi * phase) + 0.0016 * np.sin(2 * math.pi * 0.21 * t + 1.3))
    lateral = handheld * (0.0040 * walking * np.sin(math.pi * phase) + 0.0015 * fractal(t, 0.25, 11))
    roll = handheld * (0.30 * walking * np.sin(math.pi * phase + 0.5) + 0.20 * fractal(t, 0.30, 21))
    yaw_j = handheld * (0.30 * fractal(t, 0.35, 31) + 0.10 * walking * np.sin(math.pi * phase + 1.2))
    pitch_j = handheld * (0.22 * fractal(t, 0.45, 41) + 0.12 * walking * np.sin(2 * math.pi * phase + 0.3))
    xyz[:, 0] += -np.sin(yaws) * lateral
    xyz[:, 1] += np.cos(yaws) * lateral
    xyz[:, 2] += dz

    n = len(xyz)
    frame = lambda seconds: int(round(seconds * FPS)) + 1  # noqa: E731
    out = dict(
        fps=FPS, frame_count=n, duration_s=round(n / FPS, 2), eye=eye,
        coordinates='drawing (x east, y south, z up); yaw 0 = +x, 90 = +y; pitch up positive; roll clockwise positive',
        rise_frames=[frame(R.RISE[0]), frame(R.RISE[1])], door_frames=[frame(R.DOOR_OPEN[0]), frame(R.DOOR_OPEN[1])],
        walk_start_frame=n_over + 1, fade_in_s=R.FADE_IN, fade_out_s=R.FADE_OUT,
        stations=stations,
        frames=[[round(float(xyz[k, 0]), 4), round(float(xyz[k, 1]), 4), round(float(xyz[k, 2]), 4),
                 round(math.degrees(yaws[k]) + float(yaw_j[k]), 3), round(math.degrees(pitches[k]) + float(pitch_j[k]), 3),
                 round(float(roll[k]), 3), round(float(lens[k]), 2)] for k in range(n)],
        labels=['俯瞰'] * n_over + labels,
    )
    (PLAN / 'camera_frames.json').write_text(json.dumps(out, ensure_ascii=False))

    first = frame(R.APPROACH_KEYS[1][0]) - 1
    warnings = [dict(x=r['min_hard_at'][0], y=r['min_hard_at'][1]) for r in report if r['min_hard'] < MIN_HARD]
    warnings += [dict(x=r['max_soft_at'][0], y=r['max_soft_at'][1]) for r in report if r['max_soft_depth'] > MAX_SOFT_DEPTH]
    (PLAN / 'path.json').write_text(json.dumps(dict(fps=FPS, first_frame=first, points=xyz[first:, :2].round(3).tolist(),
                                                    stations=stations, warnings=warnings), ensure_ascii=False))
    yaw_rate = np.abs(np.diff(np.degrees(yaws[n_over:]) + yaw_j[n_over:])) * FPS
    pitch_rate = np.abs(np.diff(np.degrees(pitches[n_over:]) + pitch_j[n_over:])) * FPS
    motion = dict(max_walk_speed=round(float(speed.max()), 2), max_yaw_deg_s=round(float(yaw_rate.max()), 1),
                  p95_yaw_deg_s=round(float(np.percentile(yaw_rate, 95)), 1), max_pitch_deg_s=round(float(pitch_rate.max()), 1))
    summary = dict(frames=n, duration_s=round(n / FPS, 1), overview_s=round(n_over / FPS, 1),
                   walk_s=round(n_walk / FPS, 1), motion=motion, legs=report, warnings=len(warnings))
    (PLAN / 'path_report.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print(json.dumps(dict(frames=n, duration_s=summary['duration_s'], warnings=len(warnings), **motion), ensure_ascii=False))
    for r in report:
        flag = ' <-- check' if r['min_hard'] < MIN_HARD or r['max_soft_depth'] > MAX_SOFT_DEPTH else ''
        print(f"{r['to']:<12s} {r['length_m']:5.2f} m {r['seconds']:5.1f} s  min_hard {r['min_hard']:.2f} {r['min_hard_at']}"
              f"  soft {r['max_soft_depth']:.2f} {r['max_soft_at']}  astar={r['used_astar']}{flag}")


if __name__ == '__main__':
    main()
