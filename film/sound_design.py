"""Stage I: frame-locked procedural score, effects and loudness master for the 40-second film.

Implements out/audio_cue_sheet.md at 48 kHz, where video frame f starts at sample (f-1)*1600.
Cold material (and every reverb or echo tail it owns) is gated off before frame 541, only the
ding sounds in 541-549, warm material starts at frame 550, and frames 1186-1200 are digital silence.
Music: 90 BPM, one beat = 20 frames (beats on frames 1+20k); D minor before the cut, F major after.
"""
from pathlib import Path
import hashlib, json, time
import numpy as np
import sound_kit as K
from audio_dsp import (FPS, LENGTH, SPF, SR, convolve, db, decode, echoes, env, filt, fs, hz, limit, loudness, noise,
                       pan, place, reverb_ir, smooth, taxis, tape, true_peak, write_wav)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'out'
AUDIO = OUT / 'audio'
TIMING = json.loads((OUT / 'graphics_timing.json').read_text())
CUT, RESUME, BLACK = fs(541), fs(550), fs(1186)
TARGET_LUFS, CEILING_DBTP = -14., -1.
SHOTS = [('S01', 1, 90), ('S02', 91, 180), ('S03', 181, 270), ('S04', 271, 360), ('S05', 361, 450),
         ('S06', 451, 540), ('S07', 541, 630), ('S08', 631, 720), ('S09', 721, 810), ('S10', 811, 900),
         ('S11', 901, 990), ('S12', 991, 1080), ('S13', 1081, 1140), ('S14', 1141, 1200)]
# (T60 at 200 Hz, T60 at 8 kHz, pre-delay) per stem and section; ambience stays dry.
REVERBS = {('music', 'cold'): (3.2, 1.6, .025), ('music', 'warm'): (1.9, 1.0, .012),
           ('sfx', 'cold'): (.9, .5, .006), ('sfx', 'warm'): (1.1, .6, .008), ('ding', 'silence'): (1.1, .8, .01),
           ('voice', 'cold'): (.45, .3, .006), ('voice', 'warm'): (.45, .3, .006)}
STEMS = ('music', 'sfx', 'ambience', 'ding', 'voice')
VOICE_DIR = AUDIO / 'voice'
VOICE_GAIN = 7.
DUCK = {'music': -9., 'ambience': -8., 'sfx': -6.}     # dB while a narration line speaks; no line overlaps the ding
# Cues kept as matched-filter probes for sample-exact sync verification (first 40 ms; narration lines 250 ms).
SYNC_PREFIXES = ('S01 LED', 'S05 ', 'S06 coin', 'S07 cyan pulse ding', 'S07 warm roll F3', 'S08 disk LED', 'S10 tap',
                 'S10 connected', 'S13 card', 'S14 final soft kick', 'VO ')
BUS, SEND, CUES, PROBES = {}, {}, [], {}

def section_of(frame):
    return 'cold' if frame < 541 else 'silence' if frame < 550 else 'warm'

def cue(stem, name, frame, sound, gain=0., position=0., send=0.):
    """Place a sound so its first sample is the first sample of `frame` (fractional frames allowed)."""
    section = 'silence' if stem == 'ding' else section_of(frame)
    assert section != 'silence' or (stem == 'ding' and frame == 541), f'{name}: nothing but the ding may start in 541-549'
    if sound.ndim == 1:
        sound = pan(sound, position)
    key = (stem, section)
    if key not in BUS:
        BUS[key], SEND[key] = np.zeros((2, LENGTH)), np.zeros((2, LENGTH))
    start = fs(frame)
    place(BUS[key], sound, start, db(gain))
    if send:
        place(SEND[key], sound, start, db(gain) * send)
    CUES.append(dict(stem=stem, section=section, name=name, frame=frame, onset_sample=start,
                     onset_seconds=round(start / SR, 5), gain_db=round(float(gain), 2), pan=position, reverb_send=send))
    if name.startswith(SYNC_PREFIXES):
        key = f'{len(CUES) - 1:03d}'
        PROBES[key] = (sound[:, :K.secs(.25 if stem == 'voice' else .04)] * db(gain)).astype(np.float32)
        CUES[-1]['sync_probe'] = key

def automation(start_frame, n, keys):
    """Per-sample gain for a sound starting at `start_frame`, from (frame, dB) keys, linear in dB."""
    frames = start_frame + np.arange(n) / SPF
    return db(np.interp(frames, [k for k, _ in keys], [v for _, v in keys]))

def with_tail(mono, seconds, position=0.):
    return pan(np.concatenate([mono, np.zeros(K.secs(seconds))]), position)

# ---------------------------------------------------------------- 1-540: cold

def cold():
    n = K.secs(4.4)
    hum = K.mains_hum(4.4) * automation(1, n, [(1, -8), (90, 0), (100, 0), (131, -30)]) * env(n, .25, None, .05)
    cue('ambience', 'S01 device hum A1', 1, hum, -25)
    for f in (22, 64):
        cue('sfx', 'S01 LED peak beep', f, K.beep('D6'), -17, 0, .5)

    chords = [(91, 221, ['D2', 'A2', 'E3', 'A3'], 700, -16, 2.), (221, 301, ['Bb1', 'F2', 'A2', 'E3'], 800, -14.5, .5),
              (301, 381, ['G1', 'D2', 'Bb2', 'A3'], 900, -13.5, .5), (381, 461, ['A1', 'E2', 'D3', 'E3'], 1000, -12.5, .5),
              (461, 541, ['A1', 'E2', 'G2', 'C#3', 'Bb3'], 1300, -12, .5)]
    for i, (a, b, notes, cutoff, gain, attack) in enumerate(chords):
        cue('music', 'cold pad ' + '/'.join(notes), a, K.pad(notes, (b - a) / FPS + 1., cutoff, attack, 1., seed=10 + i),
            gain, 0, .35)
    motif = [(141, 'A4'), (181, 'D5'), (221, 'E5'), (261, 'F5'), (301, 'A4'), (341, 'D5'), (381, 'E5'), (421, 'F5'),
             (461, 'E5'), (501, 'C#5')]
    for i, (f, note) in enumerate(motif):
        tone = with_tail(K.glass(note, 2.4), 2.2, .15 if i % 2 else -.15)
        cue('music', f'cold motif {note}', f, tone + echoes(tone, .5, .3, 4), -17, 0, .6)
    for f in [101, 141, 181, 221, 261] + list(range(301, 541, 20)):
        level = float(np.interp(f, [101, 521], [-14, -10.5]))
        cue('music', 'cold heartbeat lub', f, K.kick(), level, 0, .1)
        cue('music', 'cold heartbeat dub', f + 5, K.kick(), level - 4.5, 0, .1)

    for f, p0, p1 in [(91, 0, .45), (131, 0, .45), (171, .05, .4)]:
        cue('sfx', 'S02 red stream hiss', f, K.sweep(1.6, 600, 6500, f, curve=lambda u: u ** 1.3, pan_from=p0, pan_to=p1),
            -20, 0, .2)
    cue('sfx', 'S02 red stream bed', 91, K.sweep(3.1, 2500, 2500, 200, width=2., attack=.3, release=.4, pan_from=.2, pan_to=.2), -32)
    for base, gain in [(181, -21), (221, -22), (261, -23), (301, -25), (341, -26)]:
        for k, (p0, p1) in enumerate([(-.5, -.1), (0, 0), (.5, .1)]):
            cue('sfx', 'S03-S04 converging red streams', base + 4 * k,
                K.sweep(1.5, 500, 6000, base * 10 + k, curve=lambda u: u ** 1.2, pan_from=p0, pan_to=p1), gain, 0, .2)
    cue('sfx', 'S03-S04 tower drive chatter', 181, K.chatter(6., 181, 12.) * env(K.secs(6.), .4, None, .3), -21, 0, .3)
    n = K.secs(7.)
    cue('ambience', 'S03-S04 tower drone', 181, K.hum(['D2', 'A2'], 7., seed=5, bright=.35, cutoff=500) * env(n, .8, None, 1.), -24)
    n = K.secs(9.1)
    fans = K.fan(9.1) * automation(271, n, [(271, -40), (285, -30), (360, -19), (370, -24), (540, -22)])
    cue('ambience', 'S04-S06 server fans', 271, fans, -2)
    for peak in (293.5, 338.5):   # S04 frame flash: 4+12*(.5-.5cos(2pi(f-271)/45))^6
        cue('sfx', 'S04 red frame pulse', peak - .95 * FPS / 2, K.red_pulse(.95), -14, .15, .4)

    cue('sfx', 'S05 lock lands', 379, K.latch(), -15, 0, .15)
    cue('sfx', 'S05 paywall 咔', 397, K.ka(), -7)
    cue('sfx', 'S05 tap denied', 421, K.denied(), -11, 0, .08)
    cue('sfx', 'S06 bill unfolds', 451, K.paper(), -16, -.1, .1)
    for i, f in enumerate(TIMING['coin_frames']):
        cue('sfx', f'S06 coin stack {i + 1}', f, K.coin(i, 600 + i), -10 + 2 * i / 11, -.55 + 1.1 * i / 11, .18)
    cue('music', 'S06 riser into the cut', 497, K.riser((541 - 497) / FPS + .2), -12, 0, .25)

def the_cut():
    cue('ding', 'S07 cyan pulse ding (only sound in 541-549)', 541, K.ding(), -5, 0, .35)

# ---------------------------------------------------------------- 550-1185: warm

def warm():
    quieter = {550: -2, 981: -4, 1061: -2}    # the post-cut bloom and the sleeping-child bars (991-1080) sit lower
    for k, note in enumerate(['F3', 'C4', 'G4', 'A4', 'C5']):
        cue('music', f'S07 warm roll {note}', 550 + k * .9, K.epiano(note, 2.6, .8), -15, -.2 + .1 * k, .45)
    chords = [(550, 581, ['F2', 'C3', 'G3', 'A3'], .3), (581, 661, ['F2', 'C3', 'E3', 'G3', 'A3'], .5),
              (661, 741, ['A2', 'C3', 'E3', 'G3'], .5), (741, 821, ['Bb2', 'D3', 'F3', 'A3', 'C4'], .5),
              (821, 861, ['C3', 'F3', 'G3', 'C4'], .4), (861, 901, ['C3', 'E3', 'G3', 'C4'], .3),
              (901, 981, ['D3', 'F3', 'A3', 'C4', 'E4'], .4), (981, 1061, ['Bb2', 'D3', 'F3', 'A3', 'C4'], .8),
              (1061, 1101, ['G2', 'Bb2', 'D3', 'F3', 'A3'], .5), (1101, 1141, ['C3', 'F3', 'G3', 'Bb3', 'D4'], .4)]
    for i, (a, b, notes, attack) in enumerate(chords):
        cue('music', 'warm pad ' + '/'.join(notes), a, K.pad(notes, (b - a) / FPS + .9, 1400, attack, .9, detune=6, seed=40 + i),
            -16 + quieter.get(a, 0), 0, .3)
    for f, note, dur in [(581, 'F1', 2.5), (661, 'A1', 1.), (701, 'A1', .6), (741, 'Bb1', 1.), (781, 'Bb1', .6),
                         (821, 'C2', 1.), (861, 'C2', .6), (901, 'D2', .9), (931, 'D2', .3), (941, 'D2', .6),
                         (971, 'C2', .3), (981, 'Bb1', 2.6), (1061, 'G1', 1.2), (1101, 'C2', .6), (1121, 'C2', .6)]:
        cue('music', f'warm bass {note}', f, K.bass(note, dur), -15 + 1.25 * quieter.get(f, 0))
    arps = [(581, 10, ['F3', 'C4', 'E4', 'G4', 'A4', 'G4', 'E4', 'C4']), (661, 10, ['A3', 'C4', 'E4', 'G4', 'C5', 'G4', 'E4', 'C4']),
            (741, 10, ['Bb3', 'D4', 'F4', 'A4', 'C5', 'A4', 'F4', 'D4']), (821, 10, ['C4', 'F4', 'G4', 'C5', 'C4', 'E4', 'G4', 'C5']),
            (901, 5, ['D4', 'F4', 'A4', 'C5', 'E5', 'C5', 'A4', 'F4'] * 2), (981, 20, ['Bb3', 'D4', 'F4', 'A4']),
            (1061, 10, ['G3', 'Bb3', 'D4', 'F4', 'A4', 'F4', 'D4', 'Bb3']), (1101, 5, ['C4', 'F4', 'G4', 'Bb4', 'D5', 'F5', 'G5', 'Bb5'])]
    for start, step, notes in arps:
        for k, note in enumerate(notes):
            cue('music', f'warm arpeggio {note}', start + k * step, K.epiano(note, .9, .55 if k % 2 else .75),
                -19 + {981: -7, 1061: -3}.get(start, 0), .25 if k % 2 else -.25, .3)
    lead = [(581, 'C5', 1.6), (621, 'F5', 1.6), (661, 'G5', 1.6), (701, 'A5', 2.2), (741, 'C5', 1.6), (781, 'F5', 1.6),
            (821, 'G5', 1.6), (861, 'A5', 1.4), (881, 'C6', 1.8), (901, 'C5', 1.), (921, 'F5', 1.), (941, 'G5', 1.), (961, 'A5', 1.2)]
    for f, note, dur in lead:
        tone = with_tail(K.epiano(note, dur, 1.), 1.6)
        cue('music', f'warm motif {note}', f, tone + echoes(tone, .5, .22, 3, lp=3500), -15, 0, .4)
    for f, note in [(1001, 'C6'), (1021, 'F6'), (1041, 'G6'), (1061, 'A6')]:
        tone = with_tail(K.music_box(note, 1.8), 1.6, .1)
        cue('music', f'S12 lullaby motif {note}', f, tone + echoes(tone, .5, .25, 3, lp=5000), -19, 0, .55)

    for f in (661, 701, 741, 781, 821, 861):
        cue('music', 'warm resting heartbeat', f, K.kick(True), -17, 0, .05)
    for k, f in enumerate(range(741, 901, 10)):
        cue('music', 'warm shaker', f, K.shaker(k), -29 if k % 2 == 0 else -25, .3)
    for f in (901, 931, 941):
        cue('music', 'S11 kick', f, K.kick(True), -11, 0, .05)
    for f in (921, 961):
        cue('music', 'S11 snare', f, K.snare(), -15, 0, .15)
    for k, f in enumerate(range(901, 981, 10)):
        cue('music', 'S11 hat', f, K.hat(k), -22 if k % 2 == 0 else -20, .2)
    cue('music', 'S11-S12 soft kick', 981, K.kick(True), -21, 0, .05)
    cue('music', 'S12 soft kick', 1061, K.kick(True), -22, 0, .05)
    for f in (1081, 1101, 1121):
        cue('music', 'S13 kick', f, K.kick(True), -12.5, 0, .05)
    cue('music', 'S13 snare', 1101, K.snare(), -15, 0, .15)
    for k, f in enumerate(range(1081, 1141, 5)):
        cue('music', 'S13 hat', f, K.hat(100 + k), -21 if k % 2 == 0 else -24, .2)
    for f, gain in [(1126, -21), (1131, -19), (1136, -17)]:
        cue('music', 'S13 snare fill', f, K.snare(seed=f), gain, 0, .15)

    cue('music', 'S14 final pad Fmaj9', 1141, K.pad(['F2', 'C3', 'E3', 'G3', 'A3', 'C4'], 1.7, 1500, .08, .5, detune=6, seed=77),
        -21, 0, .6)
    for k, note in enumerate(['F3', 'A3', 'C4', 'E4', 'G4', 'A4']):
        cue('music', f'S14 final roll {note}', 1141 + k * .75, K.epiano(note, 1.5, .9), -21, -.25 + .1 * k, .6)
    cue('music', 'S14 final motif A5', 1141, K.epiano('A5', 1.5, 1.), -20, 0, .6)
    cue('music', 'S14 final bass F1', 1141, K.bass('F1', 1.5), -19)
    cue('music', 'S14 final soft kick', 1141, K.kick(True), -19, 0, .1)

def warm_fx():
    cue('sfx', 'S07 shards dissolve', 551, K.sparkles(2.3, [2350, 2710, 3130, 3620, 4180, 4830, 5580], 26, 551, decay=.12,
                                                     spread=.6, onset_power=1.3, fade_power=1.5), -24, 0, .5)
    n = K.secs(3.3)
    halo = (3 + 2 * (.5 + .5 * np.sin(taxis(n) * 2.1))) / 5     # S08 local halo energy, normalised
    cue('sfx', 'S08 cyan hum', 631, K.hum(['F2', 'C3', 'F3'], 3.3, seed=8, bright=.25, cutoff=900) * halo * env(n, .25, None, .5),
        -21, 0, .2)
    for base in (631, 671, 711):
        for k, (p0, p1) in enumerate([(-.5, -.2), (.1, -.1), (.45, 0)]):
            cue('sfx', 'S08 cyan stream flows down', base + 6 * k,
                K.sweep(1.3, 2600, 380, base * 10 + k, width=.7, color='pink', pan_from=p0, pan_to=p1), -24, 0, .25)
    for f, note in [(631, 'F5'), (638, 'A5'), (645, 'C6')]:    # D1 disk LEDs switch on at 631 + 7i
        cue('sfx', f'S08 disk LED {note}', f, K.blip(note), -15, -.15, .35)

    grow = lambda u: 1 - (1 - u) ** 3                           # S09 bevel_factor_end ease-out over 721-756
    cue('sfx', 'S09 tunnel grows', 721, K.sweep(1.25, 250, 2800, 721, width=.9, curve=grow, attack=.06, release=.3,
                                                pan_from=-.3, pan_to=.5, color='pink'), -15, 0, .3)
    n = K.secs(1.25)
    cue('sfx', 'S09 tunnel tone', 721, pan(K.glide(1.25, hz('F3'), hz('C5'), grow) * env(n, .08, None, .35), .2), -24, 0, .3)
    cue('sfx', 'S09 tunnel connects', 757, K.blip('F5'), -19, .4, .45)
    cue('sfx', 'S09 tunnel connects', 760, K.blip('C6'), -21, .5, .45)
    n = K.secs(1.9)
    packets = 1 - .25 * (.5 + .5 * np.cos(2 * np.pi * taxis(n) / (10 / FPS)))
    cue('sfx', 'S09 light core hum', 757, K.hum(['F3', 'C4'], 1.9, seed=9, bright=.15, cutoff=1200) * packets * env(n, .15, None, .5),
        -23, 0, .2)

    cue('sfx', 'S10 tap', 811, K.soft_tap(), -14, 0, .15)
    cue('sfx', 'S10 live view expands', 811, K.sweep(.6, 450, 3200, 811, width=1., attack=.08, release=.25, color='pink'), -21, 0, .2)
    cue('sfx', 'S10 connected', 826, K.blip('C6'), -15, 0, .4)
    cue('sfx', 'S10 connected', 829, K.blip('F6'), -17, 0, .4)

    detour = lambda u: np.interp(u.ravel(), [0, 1 / 3, 2 / 3, 1], [0, .846, .31, 1]).reshape(u.shape)
    for f in (901, 937, 973):                                    # red path: one lap per 36 frames, left
        cue('sfx', 'S11 red cloud detour (left)', f, K.sweep(1.2 if f < 973 else .6, 700, 3000, f, width=.6, curve=detour,
            attack=.1, release=.3 if f < 973 else .15, pan_from=-.8, pan_to=-.8), -18, 0, .2)
    for f in (936, 972):
        cue('sfx', 'S11 red arrives late (left)', f, pan(K.blip('Eb4', .3, 1.2), -.8), -22, 0, .2)
    for f in range(901, 991, 15):                                # cyan path: one lap per 15 frames, right
        cue('sfx', 'S11 cyan direct path (right)', f, K.sweep(.5, 900, 5000, f, width=.5, attack=.05, release=.12,
                                                             pan_from=.8, pan_to=.8), -21, 0, .15)
        cue('sfx', 'S11 cyan arrives (right)', f + 14, pan(K.blip('F6', .25), .8), -22 if f + 14 < 990 else -26, 0, .15)

    n = K.secs(3.05)
    dot = np.abs(((taxis(n) * FPS) % 24) / 12 - 1)               # S12 point: 1 at the lamp end, 0 at camera C3
    cue('sfx', 'S12 night reassurance hum', 991, K.hum(['A3', 'C4', 'F4'], 3.05, seed=12, bright=.1, cutoff=800)
        * (.75 + .25 * (1 - dot)) * env(n, .4, None, .4), -24, 0, .3)
    air = np.stack([filt(noise(n, 991 + c, 'pink'), lp=900, hp=60) for c in (0, 1)]) / 3
    cue('ambience', 'S12 night air', 991, air * env(n, .3, None, .3), -30)
    for f, note in zip(TIMING['card_start_frames'], ['G5', 'A5', 'C6']):
        cue('sfx', f'S13 card 咔哒 {note}', f, K.clack(note, f), -10, 0, .18)
    cue('sfx', 'S14 bird reveal sparkle', 1141, K.sparkles(1.3, [hz('F6'), hz('A6'), hz('C7'), hz('F7')], 22, 1141, decay=.3,
                                                          spread=.4, onset_power=1.8), -22, 0, .5)
    n = K.secs((1186 - 550) / FPS)
    cue('ambience', 'warm vinyl texture', 550, K.crackle(n / SR) * env(n, 1., None, .5), -20)

# ---------------------------------------------------------------- caption narration

def moving_mean(x, n):
    c = np.concatenate(([0.], np.cumsum(x)))
    i = np.arange(len(x))
    lo, hi = np.maximum(0, i - n // 2), np.minimum(len(x), i + n // 2 + 1)
    return (c[hi] - c[lo]) / (hi - lo)

def voice_chain(x):
    """Rumble cut, slight low-mid dip and presence lift, 2:1 levelling above -12 dB re. the loudest syllable, fixed RMS."""
    y = filt(x, hp=85)
    y = y + .25 * filt(y, bp=(3200, 1.2)) - .15 * filt(y, bp=(300, 1.))
    level = 10 * np.log10(moving_mean(y * y, int(.02 * SR)) + 1e-12)
    y = y * moving_mean(db(-np.maximum(0, level - (level.max() - 12)) / 2), int(.03 * SR))
    active = moving_mean(y * y, int(.05 * SR)) > np.max(y * y) * 10 ** -3.5
    return y * db(-20) / np.sqrt(np.mean(y[active] ** 2))

def narration():
    """Caption voice-over from film/voice_tts.py: each line starts on its planned frame inside its caption window.

    Returns the speaking interval (first, last sample) of every line for ducking.
    """
    path = VOICE_DIR / 'voice_manifest.json'
    if not path.exists():
        return []
    intervals = []
    for line in json.loads(path.read_text())['lines']:
        x = voice_chain(decode(ROOT / line['file'], channels=1)[0])
        cue('voice', f"VO {line['shot']} {line['text']}", line['start_frame'], x,
            VOICE_GAIN - (1.5 if line['shot'] == 'S12' else 0), 0, .1)     # the sleeping-child line stays softer
        active = np.nonzero(np.abs(x) > np.abs(x).max() * .02)[0]
        intervals.append((fs(line['start_frame']) + int(active[0]), fs(line['start_frame']) + int(active[-1])))
    return intervals

def duck_curve(intervals, attack=.12, release=.4):
    """1 while a line speaks, raised-cosine ramps before and after it.

    A line ending just before frame 541 releases early, so the cold bed and riser surge back before the hard cut.
    """
    d = np.zeros(LENGTH)
    for a, b in intervals:
        rel = release if b >= CUT else max(.08, min(release, (CUT - b) / SR - .12))
        lo, hi = max(0, a - int(attack * SR)), min(LENGTH, b + int(rel * SR))
        seg = np.ones(hi - lo)
        seg[:a - lo] = smooth(np.arange(a - lo) / max(1, a - lo))
        seg[b - lo:] = smooth((hi - np.arange(b, hi)) / max(1, hi - b))
        d[lo:hi] = np.maximum(d[lo:hi], seg)
    return d

# ---------------------------------------------------------------- mix and master

def section_gate(section):
    g = np.ones(LENGTH)
    if section == 'cold':
        k = int(.004 * SR)
        g[CUT:] = 0.
        g[CUT - k:CUT] = smooth(np.arange(k, 0, -1) / k)
    elif section == 'warm':
        k = int(.001 * SR)
        g[:RESUME] = 0.
        g[RESUME:RESUME + k] = smooth(np.arange(k) / k)
    else:
        g[:CUT] = 0.
    tail = int(39. * SR)
    g[tail:BLACK] *= smooth((BLACK - np.arange(tail, BLACK)) / (BLACK - tail))
    g[BLACK:] = 0.
    return g

def mixdown(intervals):
    stems = {name: np.zeros((2, LENGTH)) for name in STEMS}
    for (stem, section), dry in BUS.items():
        y = dry.copy()
        if (stem, section) in REVERBS:
            low, high, pre = REVERBS[(stem, section)]
            y += convolve(SEND[(stem, section)], reverb_ir(low, high, pre, seed=sum(map(ord, stem + section))))
        if (stem, section) == ('music', 'warm'):
            y = filt(tape(y), lp=7800, order=1)
        stems[stem] += filt(y, hp=28) * section_gate(section)
    if intervals:
        # Duck the bed under narration and carve a little of the music's 2.5 kHz band where speech intelligibility lives.
        # The carve is a 40 s FFT filter, so it is re-gated: nothing may ring into frames 541-549 or the black tail.
        d = duck_curve(intervals)
        carve = filt(stems['music'], bp=(2500, .9)) * (section_gate('cold') + section_gate('warm'))
        stems['music'] = (stems['music'] - .35 * carve * d) * db(DUCK['music'] * d)
        for name in ('sfx', 'ambience'):
            stems[name] *= db(DUCK[name] * d)
    return stems

def master(mix):
    gain, ceiling = 1., CEILING_DBTP - .3
    probe = AUDIO / 'measure.tmp.wav'
    for _ in range(8):
        out, curve = limit(mix * gain, db(ceiling))
        peak = 20 * np.log10(true_peak(out))
        if peak > CEILING_DBTP - .05:
            ceiling -= peak - CEILING_DBTP + .1
            continue
        write_wav(probe, out, float32=True)
        measured = loudness(probe)
        if abs(measured['integrated_lufs'] - TARGET_LUFS) <= .1:
            break
        gain *= db(TARGET_LUFS - measured['integrated_lufs'])
    probe.unlink()
    assert abs(measured['integrated_lufs'] - TARGET_LUFS) <= .3 and peak <= CEILING_DBTP, (measured, peak)
    return out, gain * curve, measured, peak

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def shot_loudness(steps):
    """Per shot: loudest 400 ms momentary value inside the shot, and the 3 s short-term value at the shot's end."""
    rows = []
    for shot, a, b in SHOTS:
        inside = [m for t, m, s in steps if (a - 1) / FPS + .4 <= t <= b / FPS + 1e-6]
        end = min(steps, key=lambda row: abs(row[0] - b / FPS))
        rows.append(dict(shot=shot, frames=[a, b], momentary_max_lufs=round(max(inside), 1),
                         short_term_at_end_lufs=round(end[2], 1)))
    return rows

def main():
    started = time.time()
    cold()
    the_cut()
    warm()
    warm_fx()
    intervals = narration()
    print('CUES PLACED', len(CUES), 'narration lines', len(intervals), round(time.time() - started, 1), 's', flush=True)
    stems = mixdown(intervals)
    out, curve, measured, peak = master(sum(stems.values()))
    assert all(np.all(stems[s][:, CUT:RESUME] == 0) for s in STEMS if s != 'ding'), 'bed leaked into 541-549'
    assert np.all(stems['ding'][:, :CUT] == 0) and np.all(out[:, BLACK:] == 0)
    files = {'master': AUDIO / 'larktun_01_mix.wav', **{s: AUDIO / f'stems/{s}.wav' for s in STEMS},
             'sync_probes': AUDIO / 'sync_probes.npz'}
    write_wav(files['master'], out)
    for s in STEMS:
        write_wav(files[s], stems[s] * curve, float32=True)
    np.savez_compressed(files['sync_probes'], **PROBES)
    manifest = dict(
        status='COMPLETE', generator='film/sound_design.py (procedural music and effects; narration from film/voice_tts.py)',
        sample_rate=SR, channels=2,
        samples=LENGTH, duration_seconds=LENGTH / SR, master_format='WAV PCM 24-bit', stem_format='WAV float32, sum equals master',
        frame_to_sample='(frame - 1) * 1600', tempo_bpm=90, beat_frames='1 + 20k', keys=dict(frames_1_540='D minor', frames_550_1185='F major'),
        loudness=dict(target_integrated_lufs=TARGET_LUFS, integrated_lufs=measured['integrated_lufs'], lra_lu=measured['lra_lu'],
                      true_peak_dbtp_ffmpeg=measured['true_peak_dbtp'], true_peak_dbtp_4x_oversampled=round(peak, 2),
                      max_limiter_reduction_db=round(float(-20 * np.log10(curve.min() / curve.max())), 2),
                      per_shot=shot_loudness(measured['steps'])),
        silence=dict(cut_frames=[541, 549], cut_samples=[CUT, RESUME], only_stem_inside='ding', cold_fade_out_ms=4,
                     black_frames=[1186, 1200], black_samples=[BLACK, LENGTH], final_fade_seconds=[39.0, 39.5]),
        narration=dict(source=str((VOICE_DIR / 'voice_manifest.json').relative_to(ROOT)), lines=len(intervals),
                       speech_samples=intervals, ducking_db=DUCK, duck_attack_s=.12,
                       duck_release_s='0.4 (the S06 line releases early so the bed is back before frame 541)',
                       music_presence_carve='-35% of the 2.5 kHz band while a line speaks') if intervals else None,
        cues=CUES, files={k: dict(path=str(v.relative_to(ROOT)), sha256=sha(v), bytes=v.stat().st_size) for k, v in files.items()})
    (AUDIO / 'sound_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print('MASTER', json.dumps({k: v for k, v in manifest['loudness'].items() if k != 'per_shot'}), flush=True)
    print('DONE', round(time.time() - started, 1), 's', flush=True)

if __name__ == '__main__':
    main()
