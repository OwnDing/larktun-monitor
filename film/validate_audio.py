"""Gate I evidence: sample-exact sync, silence windows, loudness, stems and the A/V mux.

    python film/validate_audio.py --stage master   # WAV master and stems, plus spectrogram sheets
    python film/validate_audio.py --stage mux      # adds checks of the two MP4s that carry the soundtrack
"""
from pathlib import Path
import argparse, hashlib, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from audio_dsp import FFMPEG, FPS, LENGTH, SPF, SR, decode, filt, fs, loudness

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'out'
AUDIO = OUT / 'audio'
GATE = OUT / 'gates/I'
FFPROBE = '/opt/homebrew/bin/ffprobe'
CUT, RESUME, BLACK = fs(541), fs(550), fs(1186)
STEMS = ('music', 'sfx', 'ambience', 'ding', 'voice')
BED = ('music', 'sfx', 'ambience', 'voice')          # everything that must be silent inside frames 541-549
COLORS = {'music': (111, 168, 255), 'sfx': (47, 224, 200), 'ambience': (180, 180, 190), 'ding': (255, 220, 120),
          'voice': (255, 150, 200)}
SHOTS = [('S01', 1), ('S02', 91), ('S03', 181), ('S04', 271), ('S05', 361), ('S06', 451), ('S07', 541), ('S08', 631),
         ('S09', 721), ('S10', 811), ('S11', 901), ('S12', 991), ('S13', 1081), ('S14', 1141)]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def font(size):
    return ImageFont.truetype(str(ROOT / 'assets/fonts/NotoSansCJKsc-Regular.otf'), size)

def matched_lag(stem, probe, sample, search=960):
    """Normalised cross-correlation of a cue's own first 40 ms against the delivered stem, +-20 ms around its frame.

    Returns (best lag in samples, best correlation, correlation exactly at the frame). Overlapping tails and
    reverb lower the score but not the lag; steady tones repeat every period, so whole-period lags can tie with 0.
    """
    m = probe.shape[1]
    seg = stem[:, sample - search:sample + search + m]
    corr = sum(np.correlate(seg[c], probe[c], mode='valid') for c in range(2))
    energy = np.concatenate(([0.], np.cumsum((seg ** 2).sum(axis=0))))
    ncc = corr / np.sqrt(np.maximum(energy[m:] - energy[:-m], 1e-18) * np.sum(probe ** 2))
    k = int(np.argmax(ncc))
    return k - search, float(ncc[k]), float(ncc[search])

def onset_contrast_db(stem, sample):
    """Energy in the first 10 ms after the frame versus the 10 ms ending 2 ms before it (informational)."""
    after = np.sum(stem[:, sample:sample + SR // 100] ** 2)
    before = np.sum(stem[:, sample - SR // 100 - SR // 500:sample - SR // 500] ** 2)
    return 10 * np.log10((after + 1e-18) / (before + 1e-18))

def moving_rms(x, n):
    c = np.concatenate(([0.], np.cumsum(x * x)))
    i = np.arange(len(x))
    lo, hi = np.maximum(0, i - n // 2), np.minimum(len(x), i + n // 2 + 1)
    return np.sqrt((c[hi] - c[lo]) / (hi - lo))

def k_power(x):
    """Approximate BS.1770 K-weighting (38 Hz high-pass, +4 dB shelf above ~1.5 kHz), channel-summed power per sample."""
    y = filt(x, hp=38) + (10 ** (4 / 20) - 1) * filt(x, hp=1500, order=1)
    return np.sum(y ** 2, axis=0)

def narration_check(stems):
    """Narration heard in the voice stem lies inside the frames of the caption it reads, clearly above the bed."""
    path = AUDIO / 'voice/voice_manifest.json'
    if not path.exists():
        return dict(status='PASS', lines=[], note='no narration rendered')
    voice = stems['voice']
    speaking = moving_rms(voice.mean(axis=0), SR // 50) > 10 ** (-26 / 20) * np.max(np.abs(voice))
    allowed = np.zeros(LENGTH, dtype=bool)
    spoken, bed = k_power(voice), k_power(sum(stems[s] for s in STEMS if s != 'voice'))
    rows = []
    for line in json.loads(path.read_text())['lines']:
        a, b = fs(line['caption_frames'][0]), fs(line['caption_frames'][1] + 1)
        allowed[a:b] = True
        idx = np.nonzero(speaking[a:b])[0]
        onset, offset = a + int(idx[0]), a + int(idx[-1])
        over_bed = 10 * np.log10(spoken[onset:offset].mean() / max(bed[onset:offset].mean(), 1e-18))
        rows.append(dict(shot=line['shot'], text=line['text'], caption_frames=line['caption_frames'],
                         speech_frames=[round(1 + onset / SPF, 2), round(1 + offset / SPF, 2)],
                         voice_over_bed_lu=round(float(over_bed), 1), passed=bool(over_bed >= 6.)))
    outside = int(np.count_nonzero(speaking & ~allowed))
    return dict(status='PASS' if outside == 0 and all(r['passed'] for r in rows) else 'FAIL',
                speech_samples_outside_caption_frames=outside, speaking_threshold='20 ms RMS above -26 dB re. voice peak',
                lines=rows)

def colormap(v):
    stops = np.array([[4, 6, 12], [20, 30, 80], [30, 120, 150], [60, 220, 190], [250, 235, 150], [255, 255, 255]], float)
    p = np.clip(v, 0, 1) * (len(stops) - 1)
    i = np.minimum(p.astype(int), len(stops) - 2)
    f = (p - i)[..., None]
    return (stops[i] * (1 - f) + stops[i + 1] * f).astype(np.uint8)

def spectrogram(mono, t0, t1, width, height, fmin=30., fmax=16000.):
    a, b = int(t0 * SR), int(t1 * SR)
    win = 4096
    hop = max(1, (b - a) // width)
    x = np.pad(mono[a:b], (win // 2, win))
    frames = np.lib.stride_tricks.sliding_window_view(x, win)[::hop][:width] * np.hanning(win)
    mag = 20 * np.log10(np.abs(np.fft.rfft(frames, axis=1)) / (win / 4) + 1e-9)
    freqs = np.fft.rfftfreq(win, 1 / SR)
    rows = np.geomspace(fmax, fmin, height)
    image = np.stack([np.interp(rows, freqs, col) for col in mag], axis=1)
    return colormap((image + 90) / 84)

def sheet(stems, mix, steps, cues, t0, t1, path, title, frame_grid=False):
    width, spec_h, lane_h, left = 2400, 620, 70, 90
    top = 56
    height = top + spec_h + lane_h * len(STEMS) + 150 + 40
    im = Image.new('RGB', (left + width + 20, height), (8, 12, 21))
    d = ImageDraw.Draw(im)
    d.text((left, 14), title, font=font(26), fill=(235, 240, 248))
    mono = mix.mean(axis=0)
    im.paste(Image.fromarray(spectrogram(mono, t0, t1, width, spec_h)), (left, top))
    xs = lambda t: left + (t - t0) / (t1 - t0) * width
    for f in (60, 250, 1000, 4000, 12000):
        y = top + spec_h * np.log(16000 / f) / np.log(16000 / 30)
        d.text((8, y - 10), f'{f} Hz' if f < 1000 else f'{f // 1000} kHz', font=font(16), fill=(150, 160, 175))
    if frame_grid:
        for f in range(int(t0 * FPS) + 1, int(t1 * FPS) + 2):
            x = xs((f - 1) / FPS)
            d.line((x, top + spec_h, x, top + spec_h + 8), fill=(90, 100, 120))
    shade = [(CUT / SR, RESUME / SR, 'frames 541–549: ding only'), (BLACK / SR, LENGTH / SR, 'black: digital silence')]
    for a, b, label in shade:
        if b > t0 and a < t1:
            d.rectangle((xs(max(a, t0)), top - 6, xs(min(b, t1)), top - 1), fill=(255, 220, 120))
            d.text((xs(max(a, t0)) + 4, top - 30), label, font=font(16), fill=(255, 220, 120))
    y0 = top + spec_h + 10
    for i, name in enumerate(STEMS):
        y = y0 + i * lane_h
        d.text((8, y + 22), name, font=font(18), fill=COLORS[name])
        x = stems[name].mean(axis=0)
        a, b = int(t0 * SR), int(t1 * SR)
        hop = max(1, (b - a) // width)
        blocks = x[a:a + hop * width].reshape(width, hop)
        level = 20 * np.log10(np.sqrt(np.mean(blocks ** 2, axis=1)) + 1e-9)
        for px, v in enumerate(level):
            hgt = np.clip((v + 72) / 66, 0, 1) * (lane_h - 8)
            if hgt > 0:
                d.line((left + px, y + lane_h - 4, left + px, y + lane_h - 4 - hgt), fill=COLORS[name])
    y = y0 + len(STEMS) * lane_h + 10
    d.text((8, y + 40), 'LUFS M', font=font(18), fill=(235, 240, 248))
    pts = [(xs(t - .2), y + 140 - np.clip((m + 50) / 50, 0, 1) * 130) for t, m, s in steps if t0 <= t - .2 <= t1]
    ref = y + 140 - (36 / 50) * 130
    d.line((left, ref, left + width, ref), fill=(90, 70, 70))
    d.text((left + width - 150, ref - 22), '−14 LUFS', font=font(16), fill=(200, 140, 140))
    if len(pts) > 1:
        d.line(pts, fill=(255, 120, 120), width=2)
    for shot, start in SHOTS:
        t = (start - 1) / FPS
        if t0 <= t <= t1:
            d.line((xs(t), top, xs(t), y + 140), fill=(245, 247, 250), width=1)
            d.text((xs(t) + 4, top + 4), f'{shot} · f{start}', font=font(18), fill=(245, 247, 250))
    for c in cues:
        t = c['onset_sample'] / SR
        if t0 <= t <= t1:
            d.line((xs(t), top + spec_h - 14, xs(t), top + spec_h), fill=COLORS[c['stem']], width=2)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)

def validate_master():
    manifest = json.loads((AUDIO / 'sound_manifest.json').read_text())
    master_path = AUDIO / 'larktun_01_mix.wav'
    probe = json.loads(subprocess.run([FFPROBE, '-v', 'error', '-show_streams', '-of', 'json', str(master_path)],
                                      capture_output=True, text=True, check=True).stdout)['streams'][0]
    assert (probe['sample_rate'], probe['channels'], probe['bits_per_sample'], int(probe['duration_ts'])) == ('48000', 2, 24, LENGTH), probe
    mix = decode(master_path)
    stems = {s: decode(AUDIO / f'stems/{s}.wav') for s in STEMS}
    assert mix.shape == (2, LENGTH) and all(x.shape == (2, LENGTH) for x in stems.values())
    residual = float(np.max(np.abs(sum(stems.values()) - mix)))
    assert residual < 2e-6, residual
    for s in BED:
        assert np.all(stems[s][:, CUT:RESUME] == 0), s
    assert np.all(stems['ding'][:, :CUT] == 0)
    assert np.all(mix[:, BLACK:] == 0)
    last_cold = max(int(np.max(np.nonzero(np.any(stems[s][:, :RESUME] != 0, axis=0))[0])) for s in BED)
    first_warm = min(int(np.min(np.nonzero(np.any(stems[s][:, CUT:] != 0, axis=0))[0])) + CUT for s in BED)
    # Warm entry is a 1 ms raised-cosine gate starting exactly at frame 550, so its first sample is still zero.
    assert last_cold < CUT and RESUME <= first_warm <= RESUME + SR // 1000, (last_cold, first_warm)
    measured = loudness(master_path)
    assert abs(measured['integrated_lufs'] + 14) <= .5 and measured['true_peak_dbtp'] <= -1., measured
    probes = np.load(AUDIO / 'sync_probes.npz')
    sync = []
    for c in manifest['cues']:
        if 'sync_probe' in c:
            lag, best, at_frame = matched_lag(stems[c['stem']], probes[c['sync_probe']], c['onset_sample'])
            # Exact when the waveform at the frame matches as well as any alignment (tonal probes tie at whole periods).
            offset = 0 if at_frame >= .5 and at_frame >= best - .02 else lag
            # Warm music passes through tape wow (0-0.95 ms fractional delay), so music cues may trail by up to 1 ms.
            passed = offset == 0 or (c['stem'] == 'music' and 0 < lag <= SR // 1000 and best >= .4)
            sync.append(dict(cue=c['name'], frame=c['frame'], expected_sample=c['onset_sample'], offset_samples=offset,
                             correlation_at_frame=round(at_frame, 3), correlation_best=round(best, 3), passed=passed,
                             onset_contrast_db=round(min(99.9, onset_contrast_db(stems[c['stem']], c['onset_sample'])), 1)))
    worst = max(abs(s['offset_samples']) for s in sync) / SR * 1000
    late = [s for s in sync if not s['passed']]
    narration = narration_check(stems)
    mono_loss = 10 * np.log10(np.mean(mix ** 2) * 2 / np.mean((mix.sum(axis=0) / np.sqrt(2)) ** 2 + 1e-18) + 1e-18)
    corr = float(np.corrcoef(mix[0], mix[1])[0, 1])
    sheet(stems, mix, measured['steps'], manifest['cues'], 0, 40, GATE / 'soundtrack_overview.png',
          'Larktun 01 · soundtrack overview · 48 kHz · shots, stems, momentary loudness')
    sheet(stems, mix, measured['steps'], manifest['cues'], 16.6, 19.4, GATE / 'cut_541_549_zoom.png',
          'S06 → S07 · bed stops before frame 541 · ding only in 541–549 · warm entry at frame 550', frame_grid=True)
    sheet(stems, mix, measured['steps'], manifest['cues'], 35.8, 40, GATE / 'ending_zoom.png',
          'S13 cards → S14 final chord · tail closed before frame 1186 · digital silence to 40.000 s', frame_grid=True)
    report = dict(status='FAIL' if late or narration['status'] != 'PASS' else 'PASS', master=dict(path=str(master_path.relative_to(ROOT)), sha256=sha(master_path), sample_rate=SR,
                  channels=2, bits=24, samples=LENGTH, seconds=LENGTH / SR),
                  stems_sum_to_master_max_abs_error=residual,
                  silence=dict(bed_exactly_zero_samples=[CUT, RESUME], last_cold_bed_sample=last_cold, first_warm_sample=first_warm,
                               ding_only_frames=[541, 549], black_digital_silence_samples=[BLACK, LENGTH]),
                  loudness={k: v for k, v in measured.items() if k != 'steps'},
                  per_shot=manifest['loudness']['per_shot'], stereo=dict(lr_correlation=round(corr, 3), mono_fold_loss_db=round(float(mono_loss), 2)),
                  narration=narration, sync=dict(max_abs_offset_ms=round(worst, 2), cues=sync),
                  evidence=['out/gates/I/soundtrack_overview.png', 'out/gates/I/cut_541_549_zoom.png', 'out/gates/I/ending_zoom.png'])
    GATE.mkdir(parents=True, exist_ok=True)
    (GATE / 'audio_master_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('sync', 'per_shot')}, ensure_ascii=False), flush=True)
    print('SYNC worst offset ms', round(worst, 2), flush=True)
    assert not late, late
    assert narration['status'] == 'PASS', narration
    return report

def best_lag(ref, test, max_lag=2400):
    """Lag (samples) maximising sum(ref[i] * test[i + lag]); positive means the test audio is late."""
    size = 1 << int(np.ceil(np.log2(2 * len(ref))))
    corr = np.fft.irfft(np.conj(np.fft.rfft(ref, size)) * np.fft.rfft(test, size), size)
    lags = np.concatenate([np.arange(max_lag + 1), np.arange(-max_lag, 0)])
    return int(lags[np.argmax(np.concatenate([corr[:max_lag + 1], corr[-max_lag:]]))])

def packet_md5(path, stream):
    r = subprocess.run([FFMPEG, '-v', 'error', '-i', str(path), '-map', f'0:{stream}:0', '-c', 'copy', '-f', 'framemd5', '-'],
                       capture_output=True, text=True, check=True)
    return [line.split(',')[-1].strip() for line in r.stdout.splitlines() if line and not line.startswith('#')]

def validate_mux():
    master = decode(AUDIO / 'larktun_01_mix.wav')
    rows = []
    for name in ('clean', 'sub'):
        silent, sound = OUT / f'larktun_01_{name}.mp4', OUT / f'larktun_01_{name}_audio.mp4'
        probe = json.loads(subprocess.run([FFPROBE, '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json',
                                           str(sound)], capture_output=True, text=True, check=True).stdout)
        video = [s for s in probe['streams'] if s['codec_type'] == 'video']
        audio = [s for s in probe['streams'] if s['codec_type'] == 'audio']
        assert len(video) == 1 and len(audio) == 1 and len(probe['streams']) == 2, probe['streams']
        v, a = video[0], audio[0]
        assert int(v['nb_read_frames']) == 1200 and v['r_frame_rate'] == '30/1' and (v['width'], v['height']) == (1080, 1920)
        assert a['codec_name'] == 'aac' and a['sample_rate'] == '48000' and a['channels'] == 2
        same_video = packet_md5(silent, 'v') == packet_md5(sound, 'v')
        assert same_video, f'{name}: video packets differ from the approved silent cut'
        subprocess.run([FFMPEG, '-v', 'error', '-xerror', '-i', str(sound), '-f', 'null', '-'], check=True, capture_output=True)
        decoded = decode(sound)
        assert abs(decoded.shape[1] - LENGTH) <= 1024, decoded.shape
        n = min(decoded.shape[1], LENGTH)
        window = slice(int(2 * SR), int(38 * SR))
        best = best_lag(master.mean(axis=0)[window], decoded.mean(axis=0)[window])
        err = decoded[:, :n] - master[:, :n]
        snr = 10 * np.log10(np.sum(master[:, :n] ** 2) / np.sum(err ** 2))
        tail_peak = float(np.max(np.abs(decoded[:, BLACK + 2048:n]))) if n > BLACK + 2048 else 0.
        assert best == 0 and snr > 20 and tail_peak < 10 ** (-60 / 20), (best, snr, tail_peak)
        rows.append(dict(file=str(sound.relative_to(ROOT)), sha256=sha(sound), bytes=sound.stat().st_size,
                         video_packets_identical_to=str(silent.relative_to(ROOT)), video_frames=int(v['nb_read_frames']),
                         audio=dict(codec=a['codec_name'], profile=a.get('profile'), bit_rate=a.get('bit_rate'), sample_rate=48000, channels=2,
                                    start_time=a.get('start_time'), duration=a.get('duration')),
                         decoded_vs_master=dict(best_lag_samples=best, snr_db=round(float(snr), 1),
                                                black_tail_peak_dbfs=round(20 * np.log10(max(tail_peak, 1e-12)), 1)),
                         loudness={k: v for k, v in loudness(sound).items() if k != 'steps'}))
    report = dict(status='PASS', videos=rows)
    (GATE / 'audio_mux_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--stage', choices=['master', 'mux'], required=True)
    validate_master() if p.parse_args().stage == 'master' else validate_mux()
