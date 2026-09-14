"""Procedural instruments and one-shot effects. Everything returns ~unity peak; levels live in the cue list."""
import numpy as np
from audio_dsp import (SR, env, filt, highpass, hz, lowpass, noise, pan, phase, saw, sine, smooth,
                       stft_shape, taxis)

TWO_PI = 2 * np.pi

def secs(seconds):
    return int(round(seconds * SR))

def norm(x):
    return x / max(1e-12, float(np.max(np.abs(x))))

def freq(note):
    return hz(note) if isinstance(note, str) else float(note)

# ---------------------------------------------------------------- music

def pad(notes, dur, cutoff=900., attack=1.2, release=1., detune=7., voices=3, seed=0, glass=0.):
    """Detuned band-limited saws, decorrelated per channel, gently low-passed."""
    n = secs(dur)
    rng = np.random.default_rng(seed)
    out = np.zeros((2, n))
    for note in notes:
        f0 = freq(note)
        for v in range(voices):
            for ch in range(2):
                cents = (v - (voices - 1) / 2) * detune + rng.uniform(-2.5, 2.5)
                out[ch] += saw(f0 * 2 ** (cents / 1200), n, rng.uniform())
        if glass:
            out += glass * voices * sine(2 * f0, n, rng.uniform())
    return norm(filt(out, lp=cutoff, hp=38)) * env(n, attack, None, release)

def glass(note, dur):
    """Cold motif voice: soft FM glass with a slow vibrato."""
    n = secs(dur)
    t = taxis(n)
    f = freq(note) * (1 + .0022 * np.sin(TWO_PI * 4.4 * t) * smooth(t / .7))
    pc = phase(f, n)
    y = np.sin(TWO_PI * pc + (1.0 * np.exp(-t / .2) + .1) * np.sin(TWO_PI * 3.5 * pc))
    y += .2 * np.sin(2 * TWO_PI * pc) * np.exp(-t / .7)
    return norm(y) * env(n, .035, 1.7, .3)

def epiano(note, dur, vel=1.):
    """Warm FM electric piano for arpeggios and the warm motif."""
    n = secs(dur)
    t = taxis(n)
    pc = phase(freq(note), n)
    y = np.sin(TWO_PI * pc + (1.5 * vel * np.exp(-t / .32) + .12) * np.sin(TWO_PI * pc))
    y += .22 * vel * np.sin(14 * TWO_PI * pc) * np.exp(-t / .01)
    return norm(y) * env(n, .002, .95, .12)

def bass(note, dur):
    n = secs(dur)
    t = taxis(n)
    p = phase(freq(note), n)
    y = np.sin(TWO_PI * p) + .3 * np.sin(2 * TWO_PI * p) + .12 * np.sin(3 * TWO_PI * p) * np.exp(-t / .25)
    return norm(np.tanh(1.2 * y)) * env(n, .006, 1.2, .15)

def music_box(note, dur=1.6):
    n = secs(dur)
    t = taxis(n)
    f = freq(note)
    y = (np.sin(TWO_PI * f * t) * np.exp(-t / 1.0) + .28 * np.sin(TWO_PI * 3.95 * f * t) * np.exp(-t / .2)
         + .08 * np.sin(TWO_PI * 9.2 * f * t) * np.exp(-t / .06))
    return norm(y) * env(n, .0015, None, .12)

def kick(warm=False, dur=.5):
    """Cold 'heartbeat' kick or rounder lo-fi kick. Saturation adds harmonics phones can reproduce."""
    n = secs(dur)
    t = taxis(n)
    sweep = 52 + 70 * np.exp(-t / .04) if warm else 47 + 95 * np.exp(-t / .028)
    y = np.tanh((1.7 if warm else 1.8) * np.sin(TWO_PI * phase(sweep, n)) * np.exp(-t / (.3 if warm else .2)))
    y += (.12 if warm else .2) * filt(noise(n, 5), bp=(1700 if warm else 3000, 1.2)) * np.exp(-t / .004)
    return norm(y) * env(n, .001, None, .06)

def snare(dur=.35, seed=9):
    n = secs(dur)
    t = taxis(n)
    tone = np.sin(TWO_PI * phase(190 + 40 * np.exp(-t / .02), n)) * np.exp(-t / .05)
    hiss = filt(noise(n, seed), hp=900, lp=6500) * np.exp(-t / .09)
    return norm(.55 * tone + hiss) * env(n, .001, None, .04)

def hat(seed=0, dur=.1):
    n = secs(dur)
    return norm(filt(noise(n, 20 + seed), hp=7000, lp=14000) * np.exp(-taxis(n) / .02)) * env(n, .0005, None, .02)

def shaker(seed=0, dur=.12):
    n = secs(dur)
    t = taxis(n)
    shape = smooth(t / .012) * np.exp(-np.maximum(0, t - .012) / .035)
    return norm(filt(noise(n, 40 + seed), bp=(6500, 1.4)) * shape) * env(n, 0, None, .02)

# ---------------------------------------------------------------- beds and drones

def hum(notes, dur, seed=0, bright=.2, cutoff=700.):
    """Warm, slightly detuned sine/saw hum (the cyan '嗡')."""
    n = secs(dur)
    rng = np.random.default_rng(seed)
    out = np.zeros((2, n))
    for note in notes:
        for ch in range(2):
            f = freq(note) * 2 ** (rng.uniform(-4, 4) / 1200)
            out[ch] += sine(f, n, rng.uniform()) + bright * saw(f * 1.002, n, rng.uniform())
    return norm(filt(out, lp=cutoff, hp=40))

def mains_hum(dur, seed=3):
    """Very low device hum tuned to A1 (55 Hz) with harmonics that survive small speakers."""
    n = secs(dur)
    t = taxis(n)
    rng = np.random.default_rng(seed)
    flicker = 1 + .06 * np.sin(TWO_PI * .37 * t) + .03 * np.sin(TWO_PI * 1.9 * t + 1)
    y = sum(a * np.sin(TWO_PI * 55 * k * t + rng.uniform(0, TWO_PI))
            for k, a in [(1, 1.), (2, .7), (3, .3), (4, .22), (6, .09), (8, .05)])
    return norm(y * flicker)

def fan(dur, seed=91):
    """Server-room fans: decorrelated pink body, a mid band, faint beating whine, blade-pass flutter."""
    n = secs(dur)
    t = taxis(n)
    out = []
    for ch in range(2):
        body = norm(filt(noise(n, seed + ch, 'pink'), hp=90, lp=4200))
        body += .3 * norm(filt(noise(n, seed + 10 + ch), bp=(1300, 1.5)))
        whine = .045 * np.sin(TWO_PI * (880 + ch * 3.1) * t) + .014 * np.sin(TWO_PI * 1760.4 * t)
        out.append((body + whine) * (1 + .05 * np.sin(TWO_PI * 23.3 * t + ch)))
    return norm(np.stack(out))

def crackle(dur, seed=101, rate=9.):
    """Sparse vinyl ticks with a faint hiss floor (not normalised: absolute texture)."""
    n = secs(dur)
    rng = np.random.default_rng(seed)
    x = np.zeros((2, n))
    for p in rng.integers(0, n - 400, int(rate * dur)):
        length = rng.integers(20, 160)
        x[rng.integers(0, 2), p:p + length] += (rng.uniform(.2, 1) * rng.choice([-1, 1])
                                                * np.exp(-np.arange(length) / rng.uniform(4, 30)))
    hiss = np.stack([filt(noise(n, seed + c), hp=1500, lp=7000) for c in (1, 2)]) * .015
    return filt(x, hp=700, lp=8000) + hiss

# ---------------------------------------------------------------- one-shots

def beep(note='D6', dur=.13):
    n = secs(dur)
    p = phase(freq(note), n)
    return norm(filt(np.sin(TWO_PI * p) + .12 * np.sin(3 * TWO_PI * p), lp=5000)) * env(n, .004, None, .05)

def ding(dur=1.6):
    """The only sound inside the 9-frame cut: a short crystal A6 (5th of D minor, 3rd of F major)."""
    n = secs(dur)
    t = taxis(n)
    f = hz('A6')
    parts = [(1., 1., .24), (.5, .32, .34), (2., .16, .11), (2.76, .2, .085), (5.4, .09, .045)]
    y = sum(a * np.sin(TWO_PI * r * f * t) * np.exp(-t / tau) for r, a, tau in parts)
    y += .25 * filt(noise(n, 77), hp=4000) * np.exp(-t / .0025)
    return norm(y) * env(n, .0008, None, .2)

def coin(index, seed):
    """Two quick coin-on-coin strikes of inharmonic modes; pitch creeps up with each month."""
    n = secs(.55)
    t = taxis(n)
    rng = np.random.default_rng(seed)
    f0 = 2900 * 2 ** (index * .5 / 12) * rng.uniform(.985, 1.015)
    modes = [(1., 1., .26), (1.46, .6, .17), (2.31, .42, .11), (3.02, .28, .075), (4.17, .18, .05)]
    def strike(offset, gain, detune):
        tt = np.maximum(0, t - offset)
        return gain * (t >= offset) * sum(a * np.sin(TWO_PI * r * f0 * detune * tt) * np.exp(-tt / tau)
                                          for r, a, tau in modes)
    y = strike(0, 1., 1.) + strike(rng.uniform(.018, .03), .45, 1.031)
    y += .5 * filt(noise(n, seed + 500), hp=5000) * np.exp(-t / .002)
    return norm(y) * env(n, .0004, None, .05)

def ka(seed=31):
    """Dry, harsh paywall click: two band-passed bursts and a tiny thump, no reverb."""
    n = secs(.12)
    t = taxis(n)
    def burst(offset, gain, centre, tau, s):
        return gain * (t >= offset) * filt(noise(n, s), bp=(centre, 2.5)) * np.exp(-np.maximum(0, t - offset) / tau)
    y = burst(0, 1., 2300, .006, seed) + burst(.011, .65, 1500, .008, seed + 1)
    y += .35 * np.sin(TWO_PI * 120 * t) * np.exp(-t / .018)
    return norm(y) * env(n, .0003, None, .02)

def latch(seed=41):
    n = secs(.25)
    t = taxis(n)
    y = sum(a * np.sin(TWO_PI * f * t) * np.exp(-t / tau) for f, a, tau in [(1450, 1, .05), (2230, .6, .035), (3890, .4, .02)])
    y += .8 * filt(noise(n, seed), hp=2500) * np.exp(-t / .003)
    return norm(y) * env(n, .0004, None, .04)

def denied(seed=51):
    """Finger tap plus a decaying haptic wobble matching the UI shake (1.4 rad/frame over 16 frames)."""
    n = secs(.6)
    t = taxis(n)
    tap = np.sin(TWO_PI * phase(190 + 60 * np.exp(-t / .01), n)) * np.exp(-t / .03)
    tap += .4 * filt(noise(n, seed), lp=1500) * np.exp(-t / .008)
    buzz = sum(a * np.sin(TWO_PI * f * t) for f, a in [(150, 1.), (450, .33), (750, .2)])
    buzz *= np.abs(np.sin(TWO_PI * 6.68 * t)) * np.clip(1 - t / .533, 0, 1)
    return norm(tap + .55 * filt(buzz, lp=1800)) * env(n, .0005, None, .05)

def paper(dur=.9, seed=61):
    """Bill unfolding: dense crinkle grains that slow down as the leaves settle."""
    n = secs(dur)
    t = taxis(n)
    rng = np.random.default_rng(seed)
    speed = np.exp(-t / .25)
    grains = np.zeros(n)
    weights = speed[:n - 2000] / speed[:n - 2000].sum()
    for p in np.sort(rng.choice(n - 2000, 140, p=weights, replace=False)):
        length = rng.integers(200, 900)
        grains[p:p + length] += rng.uniform(.3, 1) * np.exp(-np.arange(length) / rng.uniform(60, 250))
    y = filt(noise(n, seed) * grains, hp=1200, lp=9000) + .3 * filt(noise(n, seed + 1), bp=(2500, .7)) * speed
    return norm(y) * env(n, .01, None, .1)

def clack(note, seed):
    """Card '咔哒': two tight transients with a small pitched body."""
    n = secs(.25)
    t = taxis(n)
    f = freq(note)
    def hit(offset, gain, centre, tau, s, body_tau):
        tt = np.maximum(0, t - offset)
        return gain * (t >= offset) * (filt(noise(n, s), bp=(centre, 1.8)) * np.exp(-tt / tau)
                                       + .8 * np.sin(TWO_PI * f * tt) * np.exp(-tt / body_tau))
    y = hit(0, 1., 3600, .003, seed, .03) + hit(.024, .7, 2300, .004, seed + 1, .04)
    return norm(y) * env(n, .0003, None, .04)

def blip(note, dur=.45, fm=.6):
    n = secs(dur)
    t = taxis(n)
    f = freq(note)
    y = np.sin(TWO_PI * f * t + fm * np.exp(-t / .05) * np.sin(2 * TWO_PI * f * t))
    y += .2 * np.sin(2 * TWO_PI * f * t) * np.exp(-t / .08)
    return norm(y) * env(n, .002, .16, .06)

def soft_tap(seed=71):
    n = secs(.18)
    t = taxis(n)
    y = np.sin(TWO_PI * phase(620 - 180 * (1 - np.exp(-t / .01)), n)) * np.exp(-t / .022)
    y += .35 * filt(noise(n, seed), lp=2200) * np.exp(-t / .004)
    return norm(y) * env(n, .0005, None, .03)

def red_pulse(dur=.95):
    """Dissonant D3/Eb3 pulse, peak in the middle, matched to the S04 red-frame flash."""
    n = secs(dur)
    shape = (.5 - .5 * np.cos(TWO_PI * taxis(n) / dur)) ** 3
    y = filt(.5 * saw(hz('D3'), n) + .5 * saw(hz('Eb3'), n), lp=900) + .6 * (sine(hz('D3'), n) + sine(hz('Eb3'), n))
    return norm(y * shape)

# ---------------------------------------------------------------- moving noise and tones

def sweep(dur, f_start, f_end, seed, width=.8, curve=None, attack=.25, release=.35, pan_from=0., pan_to=0.,
          floor=.03, color='white'):
    """Band of noise gliding between two centre frequencies (the '嘶' data streams, whooshes)."""
    n = secs(dur)
    curve = curve or (lambda u: u)
    def gains(t, f):
        centre = f_start * (f_end / f_start) ** curve(np.clip(t / dur, 0, 1))
        d = np.log2(np.maximum(f, 20) / centre) / width
        return np.exp(-.5 * d * d) + floor * highpass(f, 200) * lowpass(f, 9000)
    y = norm(stft_shape(noise(n, seed, color), gains)) * env(n, attack, None, release)
    return pan(y, pan_from + (pan_to - pan_from) * smooth(taxis(n) / dur))

def glide(dur, f_from, f_to, curve=None):
    n = secs(dur)
    u = np.clip(taxis(n) / dur, 0, 1)
    p = phase(f_from * (f_to / f_from) ** (curve or (lambda v: v))(u), n)
    return norm(np.sin(TWO_PI * p) + .25 * np.sin(2 * TWO_PI * p + .5))

def riser(dur, seed=121):
    """Tension into the cut: widening noise band and an accelerating tremolo glide, hard-stopped by the gate."""
    n = secs(dur)
    t = taxis(n)
    u = t / dur
    band = np.stack([norm(stft_shape(noise(n, seed + c), lambda tt, f: np.exp(-.5 * (np.log2(np.maximum(f, 20)
                     / (350 * 20 ** np.clip(tt / dur, 0, 1))) / 1.2) ** 2))) for c in (0, 1)])
    rate = 4 + 14 * u ** 1.5
    tremolo = 1 - .35 * (.5 + .5 * np.sin(TWO_PI * np.cumsum(rate) / SR))
    tone = glide(dur, hz('A3'), hz('A4'), lambda v: v ** 1.7) * tremolo
    return (band * .8 + .45 * tone) * 10 ** (-26 * (1 - u) / 20) * smooth(t / .08)

def sparkles(dur, freqs, count, seed, decay=.35, spread=.5, onset_power=1., fade_power=1.):
    """Cloud of tiny sine grains (shattered stream, bird reveal)."""
    n = secs(dur)
    rng = np.random.default_rng(seed)
    out = np.zeros((2, n))
    for _ in range(count):
        start = int(rng.uniform() ** onset_power * (n - 2000))
        length = min(n - start, secs(4 * decay))
        tt = taxis(length)
        f = rng.choice(freqs) * 2 ** (rng.uniform(-8, 8) / 1200)
        grain = np.sin(TWO_PI * f * tt) * np.exp(-tt / decay) * smooth(tt / .002) * smooth((length / SR - tt) / .02)
        amp = rng.uniform(.3, 1) * (1 - start / n) ** fade_power
        out[:, start:start + length] += amp * pan(grain, rng.uniform(-spread, spread))
    return out

def chatter(dur, seed, rate=14.):
    """Sparse drive-seek ticks for the remote tower (absolute level, not normalised)."""
    n = secs(dur)
    rng = np.random.default_rng(seed)
    out = np.zeros((2, n))
    for _ in range(int(rate * dur)):
        start = rng.integers(0, n - 1600)
        length = rng.integers(160, 1400)
        tt = taxis(length)
        if rng.uniform() < .8:
            grain = filt(noise(length, int(rng.integers(1 << 30))), bp=(rng.uniform(1800, 6000), 2.)) * np.exp(-tt / rng.uniform(.0015, .004))
        else:
            grain = .5 * np.sin(TWO_PI * rng.uniform(2500, 5200) * tt) * np.exp(-tt / rng.uniform(.004, .012))
        grain = grain * smooth((length - np.arange(length)) / 48.)    # 1 ms close: no truncation click
        out[:, start:start + length] += rng.uniform(.2, 1) * pan(grain, rng.uniform(-.7, .7))
    return out
