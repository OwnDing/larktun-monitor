"""Deterministic NumPy DSP for the procedural soundtrack. No samples, no external audio.

Filters are zero-phase FFT magnitude shapes, so transients stay exactly on their frame.
Time-varying filters use a WOLA STFT. Everything is seeded and reproducible.
"""
from pathlib import Path
import re, struct, subprocess, wave
import numpy as np

SR = 48000
FPS = 30
SPF = SR // FPS            # 1600 samples per video frame
LENGTH = 1200 * SPF        # exactly 40.000 s
FFMPEG = '/opt/homebrew/bin/ffmpeg'

def fs(frame):
    """First sample of a 1-based video frame: frame f starts at (f-1)/30 s."""
    return round((frame - 1) * SPF)

def hz(note):
    """'A4', 'Bb3', 'F#5' -> equal temperament, A4 = 440 Hz."""
    semis = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}[note[0]]
    rest = note[1:]
    while rest[0] in '#b':
        semis += 1 if rest[0] == '#' else -1
        rest = rest[1:]
    return 440.0 * 2 ** ((12 * (int(rest) + 1) + semis - 69) / 12)

def taxis(n):
    return np.arange(n) / SR

def smooth(u):
    """Raised-cosine 0..1 ramp."""
    return .5 - .5 * np.cos(np.pi * np.clip(u, 0, 1))

def env(n, attack=.003, tau=None, release=.01, hold=0.):
    """Raised-cosine attack, optional exponential decay after hold, raised-cosine release at the end."""
    t = taxis(n)
    e = smooth(t / attack) if attack > 0 else np.ones(n)
    if tau:
        e = e * np.exp(-np.maximum(0, t - attack - hold) / tau)
    if release > 0:
        e = e * smooth((n / SR - t) / release)
    return e

def pan(x, position):
    """Constant-power pan of a mono signal; position -1 left .. +1 right, scalar or per-sample."""
    angle = (np.asarray(position, dtype=float) + 1) * np.pi / 4
    return np.stack([x * np.cos(angle), x * np.sin(angle)])

def place(bus, sound, start, gain=1.):
    """Add a stereo sound into a bus at a sample offset, truncated to the bus."""
    a, b = max(0, start), min(bus.shape[1], start + sound.shape[1])
    if b > a:
        bus[:, a:b] += gain * sound[:, a - start:b - start]

def db(value):
    return 10 ** (value / 20)

# ---------------------------------------------------------------- oscillators

def phase(freq, n, start=0.):
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    return start + np.concatenate(([0.], np.cumsum(f[:-1]))) / SR

def sine(freq, n, start=0.):
    return np.sin(2 * np.pi * phase(freq, n, start))

def saw(freq, n, start=0.):
    """PolyBLEP band-limited sawtooth."""
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    p = phase(f, n, start) % 1.0
    dt = f / SR
    y = 2 * p - 1
    m = p < dt
    u = p[m] / dt[m]
    y[m] -= u + u - u * u - 1
    m = p > 1 - dt
    u = (p[m] - 1) / dt[m]
    y[m] -= u * u + u + u + 1
    return y

def noise(n, seed, color='white'):
    x = np.random.default_rng(seed).standard_normal(n)
    if color == 'white':
        return x
    spectrum = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    spectrum /= np.sqrt(f) if color == 'pink' else f
    y = np.fft.irfft(spectrum, n)
    return y / np.std(y)

# ---------------------------------------------------------------- filters

def lowpass(f, fc, order=2):
    return 1 / np.sqrt(1 + (f / fc) ** (2 * order))

def highpass(f, fc, order=2):
    return 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-6)) ** (2 * order))

def bandpass(f, fc, q):
    r = np.maximum(f, 1e-6) / fc
    return 1 / np.sqrt(1 + (q * (r - 1 / r)) ** 2)

def filt(x, lp=None, hp=None, bp=None, order=2, tilt=0., pad=.05):
    """Zero-phase static filter. bp=(centre, q). tilt = dB per octave around 1 kHz."""
    k = int(pad * SR)
    y = np.pad(x, [(0, 0)] * (x.ndim - 1) + [(k, k)])
    n = y.shape[-1]
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.ones_like(f)
    if lp:
        g *= lowpass(f, lp, order)
    if hp:
        g *= highpass(f, hp, order)
    if bp:
        g *= bandpass(f, *bp)
    if tilt:
        g *= db(tilt * np.clip(np.log2(np.maximum(f, 20) / 1000), -6, 4.5))
    return np.fft.irfft(np.fft.rfft(y, axis=-1) * g, n, axis=-1)[..., k:k + x.shape[-1]]

def stft_shape(x, gains, win=2048, hop=512):
    """Time-varying zero-phase magnitude shaping of a mono signal.

    gains(times_s[:, None], freqs_hz[None, :]) -> (frames, bins) magnitudes.
    """
    n = len(x)
    w = np.sqrt(np.hanning(win + 1)[:-1])
    xp = np.pad(x, (win, win + hop - (n % hop)))
    frames = np.lib.stride_tricks.sliding_window_view(xp, win)[::hop] * w
    times = (np.arange(len(frames)) * hop + win / 2 - win) / SR
    freqs = np.fft.rfftfreq(win, 1 / SR)
    spec = np.fft.rfft(frames, axis=1) * gains(times[:, None], freqs[None, :])
    out = np.fft.irfft(spec, win, axis=1) * w
    y = np.zeros(len(xp) + win)
    norm = np.zeros_like(y)
    step = win // hop
    for k in range(step):
        block = out[k::step].ravel()
        y[k * hop:k * hop + len(block)] += block
        norm[k * hop:k * hop + len(block)] += np.tile(w * w, len(block) // win)
    return (y / np.maximum(norm, 1e-9))[win:win + n]

# ---------------------------------------------------------------- space and colour

def reverb_ir(t60_low, t60_high, predelay=.015, seed=11, air=9000., build=.02):
    """Stereo, decorrelated, frequency-dependent exponential decay (T60 at 200 Hz / 8 kHz)."""
    n = int(max(t60_low, t60_high) * SR)
    lo, hi = np.log2(200), np.log2(8000)
    def t60(f):
        return t60_low + (t60_high - t60_low) * np.clip((np.log2(np.maximum(f, 20)) - lo) / (hi - lo), 0, 1)
    rng = np.random.default_rng(seed)
    chans = []
    for _ in range(2):
        tail = stft_shape(rng.standard_normal(n),
                          lambda t, f: 10 ** (-3 * np.maximum(t, 0) / t60(f)) * lowpass(f, air, 1))
        tail *= smooth(taxis(n) / build)
        chans.append(np.concatenate([np.zeros(int(predelay * SR)), tail]))
    ir = np.stack(chans)
    return ir / np.sqrt(np.sum(ir ** 2) / 2)

def convolve(x, ir):
    """Channel-wise FFT convolution; output keeps the input length."""
    n = x.shape[1]
    size = 1 << int(np.ceil(np.log2(n + ir.shape[1])))
    return np.fft.irfft(np.fft.rfft(x, size, axis=1) * np.fft.rfft(ir, size, axis=1), size, axis=1)[:, :n]

def echoes(x, delay, feedback, taps=5, lp=4500.):
    """Ping-pong echoes only (no dry); every repeat is darker than the previous one."""
    d = int(round(delay * SR))
    y = np.zeros_like(x)
    tap = x.copy()
    for k in range(1, taps + 1):
        if k * d >= x.shape[1]:
            break
        tap = filt(tap, lp=lp, order=1)
        src = tap[::-1] if k % 2 else tap
        y[:, k * d:] += feedback ** k * src[:, :x.shape[1] - k * d]
    return y

def tape(x, wow_ms=.9, wow_hz=.5, flutter_ms=.05, flutter_hz=6.1, drive=1.3):
    """Gentle lo-fi: wow/flutter by fractional delay, then soft saturation."""
    n = x.shape[1]
    t = taxis(n)
    delay = (wow_ms * (.5 + .5 * np.sin(2 * np.pi * wow_hz * t))
             + flutter_ms * (.5 + .5 * np.sin(2 * np.pi * flutter_hz * t + 1.3))) * SR / 1000
    base = np.arange(n, dtype=float)
    y = np.stack([np.interp(base - delay, base, ch) for ch in x])
    return np.tanh(drive * y) / drive

# ---------------------------------------------------------------- mastering and I/O

def sliding_max(a, w):
    """out[i] = max(a[i:i+w]) in O(n) (van Herk / Gil-Werman)."""
    n = len(a)
    b = np.concatenate([a, np.full((-n) % w + w, -np.inf)]).reshape(-1, w)
    pre = np.maximum.accumulate(b, axis=1).ravel()
    suf = np.maximum.accumulate(b[:, ::-1], axis=1)[:, ::-1].ravel()
    return np.maximum(suf[:n], pre[w - 1:w - 1 + n])

def limit(x, ceiling, window=.04):
    """Smooth look-ahead peak limiter. Gain never exceeds the need at any sample; zeros stay zero."""
    w = int(window * SR)
    need = np.minimum(1., ceiling / np.maximum(np.max(np.abs(x), axis=0), 1e-12))
    g = -sliding_max(-need, w)
    c = np.concatenate(([0.], np.cumsum(g)))
    i = np.arange(len(g))
    lo = np.maximum(0, i - w + 1)
    gain = (c[i + 1] - c[lo]) / (i + 1 - lo)
    return x * gain, gain

def true_peak(x, factor=4):
    n = x.shape[1]
    spectrum = np.fft.rfft(x, axis=1)
    up = np.zeros((x.shape[0], n * factor // 2 + 1), dtype=complex)
    up[:, :spectrum.shape[1]] = spectrum
    return float(np.max(np.abs(np.fft.irfft(up, n * factor, axis=1) * factor)))

def write_wav(path, x, float32=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if float32:
        data = np.ascontiguousarray(x.T.astype('<f4')).tobytes()
        ch = x.shape[0]
        fmt = struct.pack('<HHIIHH', 3, ch, SR, SR * ch * 4, ch * 4, 32)
        body = (b'WAVE' + b'fmt ' + struct.pack('<I', 16) + fmt + b'fact' + struct.pack('<II', 4, x.shape[1])
                + b'data' + struct.pack('<I', len(data)) + data)
        path.write_bytes(b'RIFF' + struct.pack('<I', len(body)) + body)
        return
    peak = float(np.max(np.abs(x)))
    assert peak <= 1.0, f'{path}: PCM export would clip ({peak})'
    ints = np.ascontiguousarray(np.round(x.T * (2 ** 23 - 1)).astype('<i4'))
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(x.shape[0])
        out.setsampwidth(3)
        out.setframerate(SR)
        out.writeframes(ints.view(np.uint8).reshape(-1, 4)[:, :3].tobytes())

def decode(path, channels=2):
    """Decode any audio (incl. an MP4 audio track, honouring its edit list) to float (channels, n)."""
    r = subprocess.run([FFMPEG, '-v', 'error', '-i', str(path), '-map', '0:a:0', '-f', 'f32le',
                        '-ac', str(channels), '-ar', str(SR), '-'], capture_output=True, check=True)
    return np.frombuffer(r.stdout, '<f4').reshape(-1, channels).T.astype(float)

def loudness(path):
    """EBU R128 integrated loudness, LRA and true peak via FFmpeg's ebur128, plus the 10 Hz short-term log."""
    r = subprocess.run([FFMPEG, '-hide_banner', '-nostats', '-v', 'verbose', '-i', str(path), '-af',
                        'ebur128=peak=true:framelog=verbose', '-f', 'null', '-'],
                       capture_output=True, text=True, check=True)
    log = r.stderr
    summary = log[log.rindex('Summary:'):]
    grab = lambda label: float(re.search(label + r':\s+(-?[\d.]+|-inf)', summary).group(1))
    steps = [tuple(map(float, row)) for row in
             re.findall(r't:\s*([\d.]+)\s+TARGET.*?M:\s*(-?[\d.]+|-inf)\s+S:\s*(-?[\d.]+|-inf)', log)]
    return dict(integrated_lufs=grab('I'), lra_lu=grab('LRA'), true_peak_dbtp=grab('Peak'), steps=steps)
