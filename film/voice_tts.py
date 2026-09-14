"""Stage I voice-over: Mandarin narration of every caption, generated locally and fitted inside its caption window.

Runs in the isolated voice environment (film/voice_requirements.txt), from the repository root:
    .venv-voice/bin/python film/voice_tts.py            # out/audio/voice/Sxx.wav + voice_manifest.json
    .venv-voice/bin/python film/voice_tts.py --check    # transcribe the narration inside the delivered sub MP4
TTS: Kokoro-82M v1.1-zh (Apache-2.0) through sherpa-onnx. QA: SenseVoice-small ASR, pinyin syllable agreement.
Model archives, hashes and licences: assets/voice/provenance.json.
"""
from pathlib import Path
import argparse, hashlib, json, re
import numpy as np
import sherpa_onnx as so
from pypinyin import Style, lazy_pinyin
from audio_dsp import FPS, SR, decode, fs, write_wav

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'out'
VOICE = OUT / 'audio/voice'
ASSETS = ROOT / 'assets/voice'
KOKORO = ASSETS / 'kokoro-multi-lang-v1_1'
SENSEVOICE = ASSETS / 'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17'
# zm_029: lowest-pitched of the clean voices (median F0 ~106 Hz, 10-90% range 91-126 Hz), calm and unsentimental;
# the only audition voice with zero toneless syllable errors on all fourteen lines.
SPEAKER, SPEAKER_NAME = 68, 'zm_029'
BASE_SPEED, MAX_SPEED = .95, 1.3        # slightly slower than the model's natural pace, per the script's narration note
CAPTIONS = {c['shot']: c for c in json.loads((OUT / 'caption_manifest.json').read_text())['captions']}
# (shot, spoken text, first frame of the file, last frame the speech may occupy). Every window lies inside the frames
# where that caption is on screen; wording follows the narration column of 01-创意与分镜脚本.md.
NARRATION = [
    ('S01', '你家客厅的画面。', 6, 88),
    ('S02', '每一秒，都在离开你家。', 92, 178),
    ('S03', '最后，存在谁的硬盘上？', 182, 268),
    ('S04', '别人的机房里，有一格是你家。', 272, 358),
    ('S05', '想回看昨天？先交月费。', 362, 448),
    ('S06', '三台摄像头，乘十二个月。', 452, 538),        # caption '×3 台摄像头' with the ×12 months graphic
    ('S07', '可它，本来就不用出门。', 552, 628),          # after the 541-549 silence that only the ding may break
    ('S08', '录像，存回你自己家。', 632, 718),
    ('S09', '云雀通，只打一条回家的路。', 722, 808),
    ('S10', '点开，就是家里。', 812, 898),
    ('S11', '同一个画面，两条完全不同的路。', 902, 988),
    ('S12', '画面，从没离开过你。', 992, 1078),
    ('S13', '装完就能用。', 1082, 1138),                  # S13 carries only the corner caption and three cards
    ('S14', '云雀通。', 1151, 1183),                      # the 1.2 s logo hold cannot carry the whole slogan
]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def engine():
    k = KOKORO
    model = so.OfflineTtsModelConfig(kokoro=so.OfflineTtsKokoroModelConfig(
        model=str(k / 'model.onnx'), voices=str(k / 'voices.bin'), tokens=str(k / 'tokens.txt'),
        data_dir=str(k / 'espeak-ng-data'), dict_dir=str(k / 'dict'),
        lexicon=f"{k / 'lexicon-us-en.txt'},{k / 'lexicon-zh.txt'}"), num_threads=6)
    rules = ','.join(str(k / f) for f in ('phone-zh.fst', 'date-zh.fst', 'number-zh.fst'))
    return so.OfflineTts(so.OfflineTtsConfig(model=model, rule_fsts=rules, max_num_sentences=1))

def recognizer():
    return so.OfflineRecognizer.from_sense_voice(model=str(SENSEVOICE / 'model.int8.onnx'), tokens=str(SENSEVOICE / 'tokens.txt'),
                                                 num_threads=6, language='zh', use_itn=False)

def transcribe(asr, samples, rate):
    stream = asr.create_stream()
    stream.accept_waveform(rate, np.asarray(samples, dtype=np.float32))
    asr.decode_stream(stream)
    return stream.result.text

def edit_rate(ref, hyp):
    row = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        prev, row[0] = row[0], i
        for j, h in enumerate(hyp, 1):
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + (r != h))
    return row[-1] / max(1, len(ref))

def score(text, heard):
    """ASR agreement by characters, by toneless pinyin (pronunciation) and by toned pinyin.

    Homophones the recogniser may pick instead (家/佳, 它/他, 雀/却) only affect the character rate.
    """
    ref, hyp = (re.sub(r'[^一-鿿]', '', s) for s in (text, heard))
    return dict(asr_text=hyp, cer=round(edit_rate(ref, hyp), 3),
                syllable_error=round(edit_rate(lazy_pinyin(ref), lazy_pinyin(hyp)), 3),
                tone_syllable_error=round(edit_rate(lazy_pinyin(ref, style=Style.TONE3), lazy_pinyin(hyp, style=Style.TONE3)), 3))

def trim(x, rate, pre=.03, post=.05):
    """Cut leading/trailing silence (-40 dB re. peak), keep a short breath either side, 10 ms fades."""
    idx = np.nonzero(np.abs(x) > np.abs(x).max() * .01)[0]
    y = x[max(0, idx[0] - int(pre * rate)):idx[-1] + int(post * rate)].copy()
    fade = int(.01 * rate)
    y[:fade] *= np.linspace(0, 1, fade)
    y[-fade:] *= np.linspace(1, 0, fade)
    return y

def upsample2(x):
    """Exact band-limited 2x resampling (24 kHz model output -> 48 kHz film audio)."""
    pad = 2048
    xp = np.pad(x, (pad, pad))
    m = len(xp)
    spectrum = np.fft.rfft(xp)
    up = np.zeros(m + 1, dtype=complex)
    up[:len(spectrum)] = spectrum
    if m % 2 == 0:
        up[len(spectrum) - 1] *= .5
    return np.fft.irfft(up, 2 * m)[2 * pad:-2 * pad] * 2

def synthesize(tts, text, window, speaker=SPEAKER):
    """Generate at the base pace; if the line overruns its window, regenerate slightly faster (never above MAX_SPEED)."""
    speed = BASE_SPEED
    for _ in range(5):
        audio = tts.generate(text, sid=speaker, speed=speed)
        x = trim(np.asarray(audio.samples, dtype=np.float64), audio.sample_rate)
        seconds = len(x) / audio.sample_rate
        if seconds <= window:
            return x, audio.sample_rate, speed
        speed = speed * seconds / window * 1.02
        assert speed <= MAX_SPEED, (text, speed)
    raise RuntimeError(f'{text}: cannot fit {window:.2f} s')

def generate():
    tts, asr = engine(), recognizer()
    VOICE.mkdir(parents=True, exist_ok=True)
    provenance = json.loads((ASSETS / 'provenance.json').read_text())
    lines = []
    for shot, text, start, last in NARRATION:
        caption = CAPTIONS[shot]
        assert caption['visible_start'] <= start and last <= caption['end'], shot
        window = (last + 1 - start) / FPS
        x, rate, speed = synthesize(tts, text, window)
        assert rate * 2 == SR, rate
        agreement = score(text, transcribe(asr, x, rate))
        path = VOICE / f'{shot}.wav'
        write_wav(path, upsample2(x)[None, :], float32=True)
        seconds = len(x) / rate
        lines.append(dict(shot=shot, text=text, caption_lines=caption['lines'], caption_corner=caption['corner'],
                          caption_frames=[caption['visible_start'], caption['end']], start_frame=start, last_allowed_frame=last,
                          seconds=round(seconds, 3), ends_at_frame=round(start + seconds * FPS, 2), speed=round(speed, 3),
                          **agreement, file=str(path.relative_to(ROOT)), sha256=sha(path)))
        print(shot, text, f'{seconds:.2f}s/{window:.2f}s', f'speed {speed:.3f}', agreement, flush=True)
    manifest = dict(status='COMPLETE', sample_rate=SR, speaker=dict(id=SPEAKER, name=SPEAKER_NAME), base_speed=BASE_SPEED,
                    tts=dict(engine=f'sherpa-onnx {so.__version__}', **provenance['kokoro']),
                    qa=dict(engine=f'sherpa-onnx {so.__version__}', metric='ASR agreement: characters, toneless and toned pinyin syllables',
                            **provenance['sensevoice']),
                    lines=lines)
    (VOICE / 'voice_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    wrong = [l['shot'] for l in lines if l['syllable_error'] > 0]
    assert not wrong, f'ASR heard different syllables in {wrong}'

def check(path):
    """Transcribe each narration window of the delivered film (voice over music and effects)."""
    asr = recognizer()
    lines = json.loads((VOICE / 'voice_manifest.json').read_text())['lines']
    mix = decode(path).mean(axis=0)
    rows = []
    for line in lines:
        segment = mix[fs(line['start_frame']):fs(line['last_allowed_frame'] + 1)]
        rows.append(dict(shot=line['shot'], text=line['text'], frames=[line['start_frame'], line['last_allowed_frame']],
                         **score(line['text'], transcribe(asr, segment, SR))))
        print(rows[-1], flush=True)
    report = dict(status='PASS' if all(r['syllable_error'] == 0 for r in rows) else 'REVIEW', source=str(Path(path).relative_to(ROOT)),
                  metric='SenseVoice transcript of the final mix inside each narration window; syllable_error ignores tones',
                  lines=rows)
    (OUT / 'gates/I/voice_asr_mix.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(report['status'], flush=True)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--check', action='store_true')
    check(OUT / 'larktun_01_sub_audio.mp4') if p.parse_args().check else generate()
