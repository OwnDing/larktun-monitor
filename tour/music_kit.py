"""Instruments for the house-tour score: ukulele, marimba, glockenspiel, whistle, plucked bass, hand percussion.

Built on film/audio_dsp.py (48 kHz, zero-phase FFT filters) like film/sound_kit.py. No samples.
Every sound returns ~unity peak; levels live in tour/music_tour.py.
"""
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'film'))
from audio_dsp import SR, convolve, env, filt, noise, pan, phase, reverb_ir, smooth, stft_shape, taxis  # noqa: E402
from sound_kit import freq, norm, secs  # noqa: E402

TWO_PI = 2 * np.pi

# Re-entrant ukulele (strings G4 C4 E4 A4): the sounding note on each string, 4th string first.
UKE = {
    'C': ('G4', 'C4', 'E4', 'C5'), 'Cmaj7': ('G4', 'C4', 'E4', 'B4'), 'Dm7': ('A4', 'D4', 'F4', 'C5'),
    'Em': ('G4', 'E4', 'G4', 'B4'), 'F': ('A4', 'C4', 'F4', 'A4'), 'Fmaj7': ('A4', 'E4', 'F4', 'C5'),
    'G': ('G4', 'D4', 'G4', 'B4'), 'Gsus4': ('G4', 'D4', 'G4', 'C5'), 'Am': ('A4', 'C4', 'E4', 'A4'),
    'Am7': ('G4', 'C4', 'E4', 'A4'),
}


def moving_mean(x, n):
    c = np.concatenate(([0.], np.cumsum(x)))
    i = np.arange(len(x))
    lo, hi = np.maximum(0, i - n // 2), np.minimum(len(x), i + n // 2 + 1)
    return (c[hi] - c[lo]) / (hi - lo)


@lru_cache(maxsize=None)
def _string(f0, bright, seed):
    """3 s of one plucked nylon string, exactly in tune.

    Karplus-Strong: a filtered noise burst with a pluck-position comb circulates through a two-point
    averaging loop of N + 0.5 samples, the nearest period not longer than SR / f0; reading the result
    back slightly slower lands it on f0. Higher strings ring shorter.
    """
    n = secs(3.)
    size = int(SR / f0 - .5)
    rate = f0 * (size + .5) / SR
    m = int(n * rate) + 2
    t60 = 2.3 * (262. / f0) ** .4
    gain = .5 * min(.99995, 10 ** (-3 / (t60 * f0)) / np.cos(np.pi * f0 / SR))
    rng = np.random.default_rng(seed)
    burst = filt(rng.uniform(-1, 1, size), lp=(1600, 2800, 5000)[bright], order=1)
    burst -= np.roll(burst, int(round(.19 * size)))       # plucked about a fifth of the way along
    burst -= burst.mean()
    y = np.zeros(m + 1)                                     # y[i + 1] is sample i; y[0] is sample -1
    y[1:size + 1] = burst
    for k in range(size, m, size):
        e = min(k + size, m)
        y[k + 1:e + 1] = gain * (y[k + 1 - size:e + 1 - size] + y[k - size:e - size])
    x = np.interp(np.arange(n) * rate, np.arange(m), y[1:])
    k = secs(.02)
    x[:k] += .04 * filt(noise(k, seed + 7), hp=2500, lp=9000) * np.exp(-taxis(k) / .002)   # nail contact
    body = filt(x, hp=95) + .45 * filt(x, bp=(240., 2.2)) + .3 * filt(x, bp=(510., 2.8))
    return norm(body).astype(np.float32)


def uke(note, dur, vel=1., seed=0):
    """One ukulele string ringing for `dur` seconds (until it is struck again), then damped in 25 ms."""
    x = _string(round(freq(note), 3), 2 if vel > .8 else 1 if vel > .55 else 0, seed % 4)
    n = min(secs(dur), len(x))
    return vel * x[:n] * env(n, 0, None, .025)


def strum(chord, dur, down=True, vel=1., strings=4, spread=.016, seed=0):
    """One stroke across the voicing, centred on the beat. Returns (stereo sound, samples before the beat).

    Down-strokes start on the 4th string, up-strokes on the 1st and catch only `strings` strings.
    Every string rings until `dur` seconds after the beat.
    """
    order = ([0, 1, 2, 3] if down else [3, 2, 1, 0])[:strings]
    rng = np.random.default_rng(seed)
    times = np.concatenate(([0.], np.cumsum(spread * rng.uniform(.75, 1.25, len(order) - 1))))
    lead = times[-1] / 2
    out = np.zeros((2, secs(lead + dur + .03)))
    for i, s in enumerate(order):
        tone = uke(UKE[chord][s], dur + lead - times[i], vel * rng.uniform(.82, 1.) * (1 - .07 * i), seed + s)
        a = secs(times[i])
        out[:, a:a + len(tone)] += pan(tone, -.22 + .15 * s)
    return out, secs(lead)


def marimba(note, dur=1.2, vel=1., seed=0):
    """Rosewood bar over its resonator: fundamental, the tuned 4th and 10th partials, a yarn-mallet thump."""
    n = secs(dur)
    t = taxis(n)
    f = freq(note)
    tau = float(np.clip(.5 * (440. / f) ** .6, .16, 1.))
    y = np.sin(TWO_PI * f * t) * np.exp(-t / tau)
    y += .3 * vel * np.sin(TWO_PI * 3.99 * f * t + .5) * np.exp(-t / (.2 * tau))
    y += .09 * vel * np.sin(TWO_PI * 9.9 * f * t + 1.3) * np.exp(-t / (.07 * tau))
    k = min(n, secs(.03))
    y[:k] += .25 * vel * filt(noise(k, seed), lp=2 * f + 500, order=1) * np.exp(-t[:k] / .004)
    return norm(y) * env(n, .002, None, .05)


def glock(note, dur=2., vel=1., seed=0):
    """Steel bar: long fundamental, the inharmonic 2.76 and 5.40 bar modes, a hard-mallet tick."""
    n = secs(dur)
    t = taxis(n)
    f = freq(note)
    y = np.sin(TWO_PI * f * t) * np.exp(-t / 1.)
    y += .25 * vel * np.sin(TWO_PI * 2.76 * f * t + .7) * np.exp(-t / .25)
    y += .08 * vel * np.sin(TWO_PI * 5.40 * f * t + 1.9) * np.exp(-t / .08)
    k = min(n, secs(.01))
    y[:k] += .3 * vel * filt(noise(k, seed), hp=2500, lp=11000) * np.exp(-t[:k] / .0012)
    return norm(y) * env(n, .0006, None, .06)


def whistle(phrase, seed=0):
    """A whistled phrase [(start_s, dur_s, note), ...] starting at 0 s, as one breathy sine.

    Notes that follow without a gap glide into each other in 50 ms with a slight re-articulation;
    detached notes scoop up from 3-6 % of an octave below. Vibrato blooms on held notes.
    """
    rng = np.random.default_rng(seed)
    n = secs(max(s + d for s, d, _ in phrase) + .15)
    t = taxis(n)
    pitch, level, bloom = np.zeros(n), np.zeros(n), np.zeros(n)
    for i, (s, d, note) in enumerate(phrase):
        a, b = secs(s), min(n, secs(s + d))
        target = np.log2(freq(note))
        tied = i > 0 and s - sum(phrase[i - 1][:2]) < .02
        start = pitch[a - 1] if tied else target - rng.uniform(.03, .06)
        u = taxis(b - a)
        pitch[a:b] = target + (start - target) * (1 - smooth(u / (.05 if tied else .07)))
        pitch[b:] = target
        level[a:b] = 1 - .12 * u / max(d, 1e-3)
        if tied:
            level[a:a + secs(.012)] = .72
        bloom[a:b] = smooth((u - .18) / .3) if d > .3 else 0.
    drift = np.cumsum(rng.standard_normal(n)) / SR
    wobble = filt(rng.standard_normal(n), lp=3, order=1)
    wobble *= (2 / 1200) / max(1e-9, np.std(wobble))
    curve = 2 ** (pitch + bloom * (16 / 1200) * np.sin(TWO_PI * 5.4 * t + 2 * drift) + wobble)
    p = phase(curve, n)
    tone = np.sin(TWO_PI * p) + .025 * np.sin(2 * TWO_PI * p + .3)
    centre = lambda tt: 2 ** np.interp(tt, t, pitch)
    breath = stft_shape(noise(n, seed + 1), lambda tt, f: np.exp(-.5 * (np.log2(np.maximum(f, 20) / centre(tt)) / .12) ** 2))
    shape = moving_mean(level, secs(.03))
    return norm((tone + .06 * norm(breath)) * shape)


def bass(note, dur, vel=1.):
    """Finger-plucked bass: round sine body, 2nd/3rd harmonics that settle quickly (heard on phones), a thumb thump."""
    n = secs(dur)
    t = taxis(n)
    p = phase(freq(note), n)
    y = (np.sin(TWO_PI * p) + (.3 + .4 * np.exp(-t / .08)) * np.sin(2 * TWO_PI * p)
         + .3 * np.exp(-t / .05) * np.sin(3 * TWO_PI * p))
    y = np.tanh(1.2 * y)
    k = min(n, secs(.02))
    y[:k] += .2 * filt(noise(k, 3), lp=800) * np.exp(-t[:k] / .005)
    return vel * norm(y) * env(n, .003, 1.1, .04)


def clap(seed=0):
    """Hand clap: three quick flams of band-passed noise and a longer body burst."""
    n = secs(.32)
    t = taxis(n)
    rng = np.random.default_rng(seed)
    shape, at = np.zeros(n), 0.
    for k in range(4):
        tt = t - at
        shape += (tt >= 0) * np.exp(-np.maximum(tt, 0) / (.05 if k == 3 else .0035)) * (1. if k == 3 else .8)
        at += rng.uniform(.006, .011)
    body = (filt(noise(n, seed), bp=(1200., 1.1)) + .5 * filt(noise(n, seed + 1), bp=(2300., 1.6))
            + .12 * filt(noise(n, seed + 2), hp=5000))
    return norm(body * shape) * env(n, 0, None, .03)


def snap(seed=0):
    """Finger snap: a bright 12 ms crack with a short pitched knock."""
    n = secs(.16)
    t = taxis(n)
    y = filt(noise(n, seed), bp=(2800., 2.)) * np.exp(-t / .012)
    y += .45 * np.sin(TWO_PI * 1750 * t) * np.exp(-t / .008)
    y += .35 * filt(noise(n, seed + 1), hp=6000) * np.exp(-t / .0015)
    return norm(y) * env(n, .0002, None, .03)


def tambourine(seed=0, dur=.22):
    """Jingle hit: detuned metallic partials over band noise, with the shimmer of loose jingles."""
    n = secs(dur)
    t = taxis(n)
    rng = np.random.default_rng(seed)
    jingles = sum(np.sin(TWO_PI * f * t + rng.uniform(0, TWO_PI)) * np.exp(-t / rng.uniform(.04, .1))
                  for f in rng.uniform(5000, 11000, 16)) / 4
    hiss = filt(noise(n, seed), bp=(8000., 1.4)) * np.exp(-t / .05)
    return norm((jingles + hiss) * (1 + .35 * np.sin(TWO_PI * 38 * t) * np.exp(-t / .06))) * env(n, .001, None, .04)


def cymbal(dur=2.6, seed=0):
    """Soft splash, decorrelated per channel: dense inharmonic partials and bright noise with a long decay."""
    n = secs(dur)
    t = taxis(n)
    out = []
    for ch in range(2):
        rng = np.random.default_rng(seed + ch)
        partials = sum(np.sin(TWO_PI * f * t + rng.uniform(0, TWO_PI)) * np.exp(-t / rng.uniform(.3, 1.))
                       for f in rng.uniform(2500, 11000, 36)) / 6
        wash = filt(noise(n, seed + 10 + ch), hp=3500, lp=12000) * np.exp(-t / .8)
        out.append((partials + wash) * (1 + 1.5 * np.exp(-t / .02)))
    return norm(np.stack(out)) * env(n, .002, None, .3)


def swell(notes, dur, seed=0):
    """Reversed reverb of a glockenspiel chord: grows into the downbeat and stops on it."""
    n = secs(dur)
    dry = sum(pan(glock(note, dur), -.35 + .7 * k / max(1, len(notes) - 1)) for k, note in enumerate(notes))
    wet = convolve(dry, reverb_ir(2.6, 1.6, 0., seed))
    return norm((.25 * dry + wet)[:, ::-1] * smooth(taxis(n) / dur) ** 1.5) * env(n, 0, None, .004)
