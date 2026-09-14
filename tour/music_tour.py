"""Original procedural score for the house tour: a light, cheerful ukulele tune locked to the walkthrough.

$FILM_PY tour/music_tour.py                 # score, mix, master -> out/tour/audio/tour_music.wav, then mux and check
$FILM_PY tour/music_tour.py --stage mux     # re-mux and re-check an existing master

112.5 BPM puts one beat on exactly 16 video frames, so bar b starts on frame 1 + 64 (b - 1): the walls start
rising on beat 2 of bar 9, the band comes in on bar 11 as the walk begins, and the last chord lands on bar 99
while the camera looks back from the south balcony. C major, light swing, no samples.
"""
import argparse
import hashlib
import itertools
import json
import subprocess
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import music_kit as M            # also puts film/ on sys.path
import sound_kit as K
from audio_dsp import (FFMPEG, SPF, SR, convolve, db, decode, echoes, filt, highpass, hz, limit, loudness, pan, place,
                       reverb_ir, smooth, true_peak, write_wav)
from validate_audio import FFPROBE, best_lag, font, packet_md5, spectrogram

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'out/tour'
AUDIO = OUT / 'audio'
SILENT = OUT / 'larktun_house_tour_1080p.mp4'
SCORED = OUT / 'larktun_house_tour_1080p_music.mp4'
MASTER = AUDIO / 'tour_music.wav'
MANIFEST = AUDIO / 'music_manifest.json'
META = json.loads((OUT / 'plan/camera_frames.json').read_text())
FRAMES = META['frame_count']
LENGTH = FRAMES * SPF
BPM = 112.5
BEAT = 16 * SPF                  # samples per beat = 16 video frames
SWING = .06                      # off-beat 8ths trail by 6 % of a beat (~32 ms)
TARGET_LUFS, CEILING_DBTP = -14., -1.

INTRO = ['Cmaj7', 'Fmaj7', 'Am7', 'Gsus4', 'Cmaj7', 'Fmaj7', 'Dm7', 'G']
RISE = ['F', 'G']
A = ['C', 'G', 'Am', 'F', 'C', 'G', 'F', 'G']
B = ['F', 'G', 'Em', 'Am', 'F', 'G', 'C', 'C']
D = ['Am', 'F', 'C', 'G', 'Am', 'F', 'Dm7', 'G']
BUILD = ['F', 'G', 'Em', 'Am', 'Dm7', 'Em', 'F', 'G']
FORM = [(1, 'intro', INTRO), (9, 'rise', RISE), (11, 'A1', A), (19, 'A2', A), (27, 'B1', B), (35, 'A3', A),
        (43, 'B2', B), (51, 'A4', A), (59, 'D1', D), (67, 'D2', D), (75, 'build', BUILD), (83, 'A5', A),
        (91, 'B3', B), (99, 'ending', ['C'])]
BASS_ROOT = {'C': 'C2', 'Cmaj7': 'C2', 'Dm7': 'D2', 'Em': 'E2', 'F': 'F2', 'Fmaj7': 'F2', 'G': 'G2', 'Gsus4': 'G2',
             'Am': 'A2', 'Am7': 'A2'}
TRIAD = {'C': 'CEG', 'Dm7': 'DFA', 'Em': 'EGB', 'F': 'FAC', 'G': 'GBD', 'Am': 'ACE'}
PAD = {'Cmaj7': ['C3', 'G3', 'B3', 'E4'], 'Fmaj7': ['F2', 'C3', 'A3', 'E4'], 'Am7': ['A2', 'E3', 'G3', 'C4'],
       'Gsus4': ['G2', 'D3', 'G3', 'C4'], 'Dm7': ['D3', 'A3', 'C4', 'F4'], 'C': ['C3', 'G3', 'C4', 'E4'],
       'F': ['F2', 'C3', 'A3', 'C4'], 'G': ['G2', 'D3', 'G3', 'B3'], 'Am': ['A2', 'E3', 'A3', 'C4'],
       'Em': ['E3', 'B3', 'E4', 'G4']}

# Melodies: (bar within the phrase, beat, beats held, note).
MEL_INTRO = [(0, 0, 1.5, 'E6'), (0, 1.5, .5, 'D6'), (0, 2, 2, 'G5'), (1, 0, 1.5, 'A5'), (1, 1.5, .5, 'C6'), (1, 2, 2, 'E6'),
             (2, 0, 1.5, 'E6'), (2, 1.5, .5, 'D6'), (2, 2, 2, 'C6'), (3, 0, 2, 'D6'), (3, 2, 2, 'G5'),
             (4, 0, 1.5, 'E6'), (4, 1.5, .5, 'D6'), (4, 2, 2, 'G5'), (5, 0, 1.5, 'A5'), (5, 1.5, .5, 'C6'), (5, 2, 2, 'F6'),
             (6, 0, 1.5, 'E6'), (6, 1.5, .5, 'D6'), (6, 2, 2, 'A5'), (7, 0, 2, 'B5'), (7, 2, 2, 'D6')]
MEL_A = [(0, 0, .5, 'G5'), (0, .5, .5, 'A5'), (0, 1, .5, 'G5'), (0, 1.5, 1.5, 'E5'), (0, 3, .5, 'D5'), (0, 3.5, .5, 'E5'),
         (1, 0, 1, 'D5'), (1, 1, .5, 'G5'), (1, 1.5, 2, 'B5'), (1, 3.5, .5, 'A5'),
         (2, 0, .5, 'C6'), (2, .5, .5, 'B5'), (2, 1, .5, 'A5'), (2, 1.5, 1.5, 'E5'), (2, 3, .5, 'E5'), (2, 3.5, .5, 'G5'),
         (3, 0, 1, 'A5'), (3, 1, .5, 'G5'), (3, 1.5, 2, 'F5'), (3, 3.5, .5, 'G5'),
         (4, 0, .5, 'G5'), (4, .5, .5, 'A5'), (4, 1, .5, 'G5'), (4, 1.5, 1.5, 'E5'), (4, 3, .5, 'D5'), (4, 3.5, .5, 'E5'),
         (5, 0, 1, 'D5'), (5, 1, .5, 'G5'), (5, 1.5, 1, 'B5'), (5, 2.5, .5, 'D6'), (5, 3, .5, 'B5'), (5, 3.5, .5, 'C6'),
         (6, 0, 1, 'A5'), (6, 1, .5, 'C6'), (6, 1.5, 1.5, 'A5'), (6, 3, .5, 'G5'), (6, 3.5, .5, 'F5'),
         (7, 0, 1.5, 'G5'), (7, 1.5, .5, 'A5'), (7, 2, 2, 'B5')]
MEL_B = [(0, 0, 1.5, 'A5'), (0, 1.5, .5, 'C6'), (0, 2, 1, 'A5'), (0, 3, 1, 'G5'),
         (1, 0, 1.5, 'B5'), (1, 1.5, .5, 'D6'), (1, 2, 1, 'B5'), (1, 3, 1, 'A5'),
         (2, 0, 1.5, 'G5'), (2, 1.5, .5, 'B5'), (2, 2, 1, 'E6'), (2, 3, .5, 'D6'), (2, 3.5, .5, 'B5'),
         (3, 0, 2.5, 'C6'), (3, 2.5, .5, 'B5'), (3, 3, .5, 'A5'), (3, 3.5, .5, 'G5'),
         (4, 0, 1.5, 'A5'), (4, 1.5, .5, 'C6'), (4, 2, 1, 'F6'), (4, 3, 1, 'E6'),
         (5, 0, 1.5, 'D6'), (5, 1.5, .5, 'B5'), (5, 2, 1, 'G5'), (5, 3, .5, 'A5'), (5, 3.5, .5, 'B5'),
         (6, 0, 1.5, 'E6'), (6, 1.5, .5, 'D6'), (6, 2, 1, 'C6'), (6, 3, .5, 'D6'), (6, 3.5, .5, 'E6'), (7, 0, 3, 'C6')]
MEL_D = [(0, 0, 2, 'E6'), (0, 2, 1, 'D6'), (0, 3, 1, 'C6'), (1, 0, 3, 'C6'), (1, 3, 1, 'A5'), (2, 0, 2, 'G5'), (2, 2, 2, 'E6'),
         (3, 0, 4, 'D6'), (4, 0, 2, 'E6'), (4, 2, 1, 'D6'), (4, 3, 1, 'C6'), (5, 0, 2, 'C6'), (5, 2, 2, 'A5'),
         (6, 0, 2, 'F6'), (6, 2, 1, 'E6'), (6, 3, 1, 'D6'), (7, 0, 4, 'D6')]

# Strum patterns: (beat, down-stroke, velocity).
ISLAND = [(0, True, 1.), (1, True, .8), (1.5, False, .6), (2.5, False, .65), (3, True, .85), (3.5, False, .6)]
DRIVE = [(k / 2, k % 2 == 0, (1., .6, .8, .6, .9, .6, .8, .65)[k]) for k in range(8)]
QUARTERS = [(k, True, (.8, .9, .85, 1.)[k]) for k in range(4)]
PICK = [1, 2, 3, 2, 0, 2, 3, 2]          # fingerpicked 8ths, by string (0 = 4th string)
KICK = {'light': [(0, 1.), (2, .8)], 'groove': [(0, 1.), (2, .85), (2.5, .55)], 'full': [(0, 1.), (1.5, .5), (2, .9), (2.5, .6)],
        'half': [(0, .9)], 'soft': [], 'rise': [(k, .55 + .15 * k) for k in range(4)]}

# Mix: loudness of each bus while it plays (K-weighted, gated), EQ, and reverb send.
TARGETS = {'marimba': -19., 'uke': -20., 'whistle': -20.5, 'bass': -21., 'kick': -22.5, 'glock': -23.5, 'clap': -25.,
           'fx': -26., 'snap': -27., 'pad': -27., 'perc': -28.}
EQ = {'uke': dict(hp=110), 'bass': dict(hp=32, lp=2500), 'kick': dict(hp=30), 'marimba': dict(hp=180),
      'whistle': dict(hp=350, lp=9000), 'glock': dict(hp=700), 'clap': dict(hp=250), 'snap': dict(hp=400),
      'perc': dict(hp=2500), 'pad': dict(hp=140, lp=5000), 'fx': dict(hp=200)}
SENDS = {'uke': .16, 'marimba': .22, 'whistle': .26, 'glock': .34, 'clap': .22, 'snap': .2, 'pad': .35, 'fx': .25,
         'perc': .08, 'kick': .02, 'bass': 0.}

BUS, COUNT, KICKS = {}, {}, []
SEED = itertools.count(1000)
HUMAN = np.random.default_rng(1125)


def at(bar, beat=0., swing=True):
    """First sample of a beat position; beats may run past 4. Off-beat 8ths (and 16ths between) are swung."""
    whole, frac = divmod(beat, 1.)
    if swing:
        frac = frac * (.5 + SWING) / .5 if frac <= .5 else .5 + SWING + (frac - .5) * (.5 - SWING) / .5
    return int(round(((bar - 1) * 4 + whole + frac) * BEAT))


def put(bus, sound, start, gain=0., position=0., human=.003):
    """Add a sound to a bus with up to +-3 ms of player timing (kick and bass stay on the grid)."""
    if sound.ndim == 1:
        sound = pan(sound, position)
    if bus not in BUS:
        BUS[bus], COUNT[bus] = np.zeros((2, LENGTH), np.float32), 0
    if human:
        start += int(round(HUMAN.uniform(-human, human) * SR))
    place(BUS[bus], sound, int(start), db(gain))
    COUNT[bus] += 1


def vdb(v):
    return 20 * np.log10(v)


def shift(note, semis):
    return hz(note) * 2 ** (semis / 12)


# ---------------------------------------------------------------- players

def strokes(bar, chord, pattern, vel=1.):
    for i, (beat, down, v) in enumerate(pattern):
        start = at(bar, beat)
        ring = (at(bar, pattern[i + 1][0] if i + 1 < len(pattern) else 4.) - start) / SR + .02
        sound, lead = M.strum(chord, ring, down, vel * v, 4 if down else 3, .016 if down else .011, next(SEED))
        put('uke', sound, start - lead)


def pick(bar, chord, vel):
    for k, string in enumerate(PICK):
        gap = next((j for j in range(1, 8 - k) if PICK[k + j] == string), 8 - k)
        start = at(bar, k / 2)
        ring = (at(bar, (k + gap) / 2) - start) / SR + .03
        v = vel * (1. if k % 4 == 0 else .8 if k % 2 == 0 else .7)
        put('uke', M.uke(M.UKE[chord][string], ring, v, next(SEED)), start, 0., -.22 + .15 * string)


def bassline(bar, chord, after, style, vel=1.):
    root = hz(BASS_ROOT[chord])
    if style == 'long':
        notes = [(0, 3.6, root, .8)]
    elif style == 'quarters':
        notes = [(k, .85, root, .8 + .06 * k) for k in range(4)]
    else:                                   # bounce, with a step-above approach into the next root
        notes = [(0, .95, root, 1.), (1.5, .45, root, .7), (2, .9, root * 2 ** (7 / 12), .85), (3, .45, root, .75),
                 (3.5, .45, hz(BASS_ROOT[after]) * 2 ** (2 / 12), .65)]
    for beat, beats, f, v in notes:
        start = at(bar, beat)
        put('bass', M.bass(f, (at(bar, beat + beats) - start) / SR, vel * v), start, human=0)


def group_clap():
    a, b = M.clap(next(SEED)), M.clap(next(SEED))
    k = K.secs(.008)
    out = np.zeros((2, len(a) + k))
    out[:, :len(a)] += pan(a, -.3)
    out[:, k:] += .8 * pan(b, .3)
    return out


def drums(bar, style, tamb=False):
    for beat, v in KICK[style]:
        start = at(bar, beat)
        KICKS.append(start)
        put('kick', K.kick(True), start, vdb(v), human=0)
    for beat in {'groove': (1, 3), 'full': (1, 3), 'half': (2,)}.get(style, ()):
        put('clap', group_clap(), at(bar, beat))
        if tamb or style == 'full':
            put('perc', M.tambourine(next(SEED)), at(bar, beat), -1., .3)
    if style == 'soft':
        for beat in (1, 3):
            put('snap', M.snap(next(SEED)), at(bar, beat), 0., .15)
    steps = {'full': 16, 'rise': 0}.get(style, 8)
    for k in range(steps):
        v = (.5, .3, .9, .35)[k % 4] if steps == 16 else (.55, .9)[k % 2]
        put('perc', K.shaker(next(SEED)), at(bar, k * 4 / steps), vdb(v) - (5 if style == 'soft' else 0), -.3)
    if style in ('groove', 'full'):
        for beat in (.5, 1.5, 2.5, 3.5):
            put('perc', K.hat(next(SEED)), at(bar, beat), -3., .25)


def band(first, chords, after, pattern, style, bass_style='bounce', vel=1., tamb=False):
    for i, chord in enumerate(chords):
        bar = first + i
        if pattern == 'pick':
            pick(bar, chord, vel)
        else:
            strokes(bar, chord, pattern, vel)
        bassline(bar, chord, chords[i + 1] if i + 1 < len(chords) else after, bass_style, .7 if bass_style == 'long' else 1.)
        drums(bar, style, tamb)


def pads(first, chords, gain=0., attack=.6):
    for i, chord in enumerate(chords):
        put('pad', K.pad(PAD[chord], 4 * BEAT / SR + 1., 1100, attack, 1., detune=6, seed=10 + first + i), at(first + i), gain)


def melody(bus, instrument, first, mel, semis=0, vel=1., ring=.6, long_only=False, position=0.):
    for b, beat, beats, note in mel:
        if long_only and beats < 1:
            continue
        start = at(first + b, beat)
        v = vel * (1. if beat % 1 == 0 else .85)
        length = (at(first + b, beat + beats) - start) / SR + ring
        put(bus, instrument(shift(note, semis), length, v, next(SEED)), start, vdb(v), position)


def whistle(first, mel, gain=0.):
    """One legato whistle take per phrase: notes that touch are tied, others leave a 40 ms breath."""
    origin = at(first)
    starts = [(at(first + b, beat) - origin) / SR for b, beat, _, _ in mel]
    phrase = []
    for i, (b, beat, beats, note) in enumerate(mel):
        end = (at(first + b, beat + beats) - origin) / SR
        end = starts[i + 1] if i + 1 < len(mel) and abs(starts[i + 1] - end) < .02 else end - .04
        phrase.append((starts[i], end - starts[i], note))
    x = pan(np.pad(M.whistle(phrase, next(SEED)), (0, K.secs(1.3))), 0.)
    put('whistle', x + echoes(x, .4, .2, 3, lp=3500), origin, gain, human=0)     # dotted-8th ping-pong


def arpeggio(bar, chord, vel):
    tones = sorted(hz(f'{pc}{octave}') for pc in TRIAD[chord] for octave in (4, 5, 6, 7))
    first = tones.index(hz(TRIAD[chord][0] + '4'))
    for k in range(8):
        put('marimba', M.marimba(tones[first + k], .5, vel, next(SEED)), at(bar, k / 2), vdb(vel), -.3 + .08 * k)


def roll(bar, beats, v0, v1):
    for k, beat in enumerate(beats):
        v = v0 + (v1 - v0) * k / (len(beats) - 1)
        put('clap', group_clap(), at(bar, beat, swing=False), vdb(v))


def lift_into(bar):
    """Reverse glockenspiel swell that stops on the downbeat, then a soft splash on it."""
    sound = M.swell(['C6', 'E6', 'G6'], 2 * BEAT / SR, next(SEED))
    put('fx', sound, at(bar) - sound.shape[1], human=0)
    put('fx', M.cymbal(2.6, next(SEED)), at(bar), human=0)


# ---------------------------------------------------------------- the tune

def score():
    pads(1, INTRO, -2., attack=1.6)                                     # 俯瞰: drone orbit and approach
    melody('glock', M.glock, 1, MEL_INTRO, vel=.8, ring=1.2)
    for i, chord in enumerate(INTRO[4:]):
        bar = 5 + i
        pick(bar, chord, .5 + .04 * i)
        bassline(bar, chord, None, 'long', .6)
        for beat in (1, 3):
            put('snap', M.snap(next(SEED)), at(bar, beat), -2., .15)
        if bar >= 7:
            for k in range(8):
                put('perc', K.shaker(next(SEED)), at(bar, k / 2), vdb((.45, .75)[k % 2]) - 4, -.3)

    pads(9, RISE)                                                       # walls rise on beat 2 of bar 9, door opens
    for i, chord in enumerate(RISE):
        strokes(9 + i, chord, QUARTERS, .6 + .2 * i)
        bassline(9 + i, chord, None, 'quarters', .7 + .15 * i)
    for k, note in enumerate(['G5', 'A5', 'C6', 'D6', 'E6', 'G6', 'A6', 'C7', 'D7']):
        v = .65 + .04 * k
        put('glock', M.glock(note, 1.4, v, next(SEED)), at(9, 1 + k / 2, swing=False), vdb(v), -.4 + .1 * k)
    drums(10, 'rise')
    roll(10, [2, 2.5, 3, 3.25, 3.5, 3.75], .35, .9)
    lift_into(11)

    band(11, A, 'C', ISLAND, 'light', vel=.85)                          # walk in: 玄关, 过道
    melody('marimba', M.marimba, 11, MEL_A)
    band(19, A, 'F', ISLAND, 'groove', vel=.9)                          # 书房 and the NVR shelf
    melody('marimba', M.marimba, 19, MEL_A)
    melody('glock', M.glock, 19, MEL_A, 12, .7, 1., long_only=True)
    band(27, B, 'C', ISLAND, 'groove', vel=.9, tamb=True)               # 储藏间 -> 儿童房
    whistle(27, MEL_B)
    band(35, A, 'F', ISLAND, 'groove')                                  # 儿童房 -> 客厅入口
    melody('marimba', M.marimba, 35, MEL_A)
    melody('glock', M.glock, 35, MEL_A, 12, .55, .8)
    band(43, B, 'C', ISLAND, 'full')                                    # 客厅入口, 餐厅
    whistle(43, MEL_B)
    melody('marimba', M.marimba, 43, MEL_B, -12, .8)
    band(51, A, 'Am', DRIVE, 'full', vel=.85)                           # 厨房, 生活阳台
    whistle(51, MEL_A)
    melody('marimba', M.marimba, 51, MEL_A, 0, .8)

    pads(59, D, -1.)                                                    # 主卧, 飘窗: the band steps back
    band(59, D, 'Am', 'pick', 'soft', 'long', .55)
    melody('glock', M.glock, 59, MEL_D, ring=1.4)
    pads(67, D)
    band(67, D, 'F', 'pick', 'soft', 'long', .6)
    melody('glock', M.glock, 67, MEL_D, ring=1.4)
    melody('marimba', M.marimba, 67, MEL_D, -12, .6, 1.)

    band(75, BUILD[:4], 'Dm7', ISLAND, 'half', 'long', .7)              # 主卫, then back towards the living room
    band(79, BUILD[4:], 'C', ISLAND, 'groove', vel=.85)
    for i, chord in enumerate(BUILD):
        arpeggio(75 + i, chord, .45 + .08 * i)
    roll(82, [2, 2.5, 3, 3.25, 3.5, 3.75], .4, 1.)
    lift_into(83)

    band(83, A, 'F', DRIVE, 'full', vel=.95)                            # 客厅
    melody('marimba', M.marimba, 83, MEL_A)
    melody('glock', M.glock, 83, MEL_A, 12, .6, .8)
    band(91, B, 'C', DRIVE, 'full', vel=.95)                            # 客厅 -> 南阳台
    whistle(91, MEL_B)
    melody('marimba', M.marimba, 91, MEL_B, -12, .85)
    melody('glock', M.glock, 91, MEL_B, 12, .6, 1., long_only=True)
    roll(98, [3, 3.25, 3.5, 3.75], .5, .95)

    sound, lead = M.strum('C', 3.5, True, 1., spread=.03, seed=next(SEED))   # bar 99: looking back from the balcony
    put('uke', sound, at(99) - lead)
    put('bass', M.bass('C2', 2.6), at(99), human=0)
    KICKS.append(at(99))
    put('kick', K.kick(True), at(99), human=0)
    put('fx', M.cymbal(2.6, next(SEED)), at(99), human=0)
    put('pad', K.pad(PAD['Cmaj7'], 3.2, 1100, .05, 1.5, detune=6, seed=99), at(99), -2.)
    put('marimba', M.marimba('C6', 1.6, 1., next(SEED)), at(99))
    for k, note in enumerate(['C6', 'E6', 'G6', 'C7']):
        put('glock', M.glock(note, 2.4, .8, next(SEED)), at(99, k / 2), vdb(.8), -.3 + .2 * k)


# ---------------------------------------------------------------- mix and master

def active_loudness(x):
    """Approximate BS.1770 loudness over 400 ms blocks within 25 dB of the loudest block (how loud a bus is while it plays)."""
    n = x.shape[1]
    f = np.fft.rfftfreq(n, 1 / SR)
    g = (highpass(f, 38) * (1 + (db(4) - 1) * highpass(f, 1500, 1))).astype(np.float32)
    p = np.square(np.fft.irfft(np.fft.rfft(x, axis=1) * g, n, axis=1)).sum(axis=0)
    block = int(.4 * SR)
    blocks = p[:n // block * block].reshape(-1, block).mean(axis=1)
    return float(10 * np.log10(blocks[blocks > blocks.max() * 10 ** -2.5].mean()) - .691)


def pump(depth=-2.5):
    """Gentle kick side-chain: a 5 ms dip that recovers over 155 ms."""
    g = np.ones(LENGTH, np.float32)
    t = np.arange(int(.16 * SR)) / SR
    dip = db(depth * smooth(t / .005) * (1 - smooth((t - .005) / .155))).astype(np.float32)
    for s in KICKS:
        e = min(LENGTH, s + len(dip))
        g[s:e] = np.minimum(g[s:e], dip[:e - s])
    return g


def reverb(x, ir, block=1 << 21):
    """Convolution in overlapping blocks, so a 212 s bus never needs one 2^24-sample FFT."""
    out = np.zeros(x.shape, np.float32)
    for a in range(0, x.shape[1], block):
        seg = x[:, a:a + block]
        if np.any(seg):
            b = min(x.shape[1], a + seg.shape[1] + ir.shape[1])
            out[:, a:b] += convolve(np.pad(seg, ((0, 0), (0, b - a - seg.shape[1]))), ir)
    return out


def mixdown():
    mix, send, report = np.zeros((2, LENGTH)), np.zeros((2, LENGTH), np.float32), {}
    squeeze = pump()
    for name in sorted(BUS):
        y = filt(BUS.pop(name), **EQ[name]).astype(np.float32)
        level = active_loudness(y)
        y *= np.float32(db(TARGETS[name] - level))
        if name in ('uke', 'pad'):
            y *= squeeze
        elif name == 'bass':
            y *= squeeze ** .6
        mix += y
        send += np.float32(SENDS[name]) * y
        report[name] = dict(cues=COUNT[name], active_lufs=round(level, 1), gain_db=round(TARGETS[name] - level, 1),
                            target_active_lufs=TARGETS[name], eq=EQ[name], reverb_send=SENDS[name])
    mix += reverb(send, reverb_ir(1.6, .9, .018, seed=112))
    return mix, report


def fades(x):
    """5 ms in; out with the picture over the last fade_out_s, reaching digital zero on the last sample."""
    k = int(round(META['fade_out_s'] * SR))
    x[:, -k:] *= smooth((k - 1 - np.arange(k)) / (k - 1))
    j = int(.005 * SR)
    x[:, :j] *= smooth(np.arange(j) / j)


def peak_dbtp(x, block=1 << 20, overlap=1 << 12):
    return 20 * np.log10(max(true_peak(x[:, max(0, a - overlap):a + block + overlap]) for a in range(0, x.shape[1], block)))


def master(mix):
    probe = AUDIO / 'measure.tmp.wav'
    gain, ceiling = db(TARGET_LUFS - active_loudness(mix.astype(np.float32))), CEILING_DBTP - .3
    for _ in range(8):
        out, curve = limit(mix * gain, db(ceiling))
        peak = peak_dbtp(out)
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


def frame_of(bar):
    return 1 + 64 * (bar - 1)


def render():
    started = time.time()
    score()
    print('CUES', sum(COUNT.values()), dict(COUNT), round(time.time() - started, 1), 's', flush=True)
    mix, buses = mixdown()
    fades(mix)
    out, curve, measured, peak = master(mix)
    assert np.all(out[:, -1] == 0)
    write_wav(MASTER, out)
    bars = [bar for bar, _, _ in FORM] + [(FRAMES - 1) // 64 + 2]
    manifest = dict(
        status='COMPLETE', generator='tour/music_tour.py + tour/music_kit.py (procedural, no samples; film/audio_dsp.py DSP)',
        video=str(SILENT.relative_to(ROOT)), frames=FRAMES, fps=META['fps'], sample_rate=SR, channels=2, samples=LENGTH,
        duration_seconds=round(LENGTH / SR, 4), tempo_bpm=BPM, beat_frames=16, bar_frames=64, bar_start_frame='1 + 64 (bar - 1)',
        swing_beats=SWING, key='C major', style='light, cheerful: ukulele, marimba, whistle, glockenspiel, bass, claps, shaker',
        form=[dict(section=name, bars=[bar, bars[i + 1] - 1], frames=[frame_of(bar), min(FRAMES, frame_of(bars[i + 1]) - 1)],
                   seconds=[round((frame_of(bar) - 1) / 30, 2), round(min(FRAMES, frame_of(bars[i + 1]) - 1) / 30, 2)], chords=chords)
              for i, (bar, name, chords) in enumerate(FORM)],
        picture_sync=dict(walls_rise_frames=META['rise_frames'], rise_starts_on='bar 9 beat 2 (frame 529)',
                          door_frames=META['door_frames'], walk_start_frame=META['walk_start_frame'], band_enters='bar 11 (frame 641)',
                          last_chord='bar 99 (frame 6273)', audio_fade_out_seconds=META['fade_out_s']),
        rooms=[dict(name=s['name'], frames=s['frames'], bar=round(1 + (s['frames'][0] - 1) / 64, 2)) for s in META['stations'][1:]],
        buses=buses,
        loudness=dict(target_integrated_lufs=TARGET_LUFS, integrated_lufs=measured['integrated_lufs'], lra_lu=measured['lra_lu'],
                      true_peak_dbtp_ffmpeg=measured['true_peak_dbtp'], true_peak_dbtp_4x_oversampled=round(float(peak), 2),
                      max_limiter_reduction_db=round(float(-20 * np.log10(curve.min() / curve.max())), 2)),
        files=dict(master=dict(path=str(MASTER.relative_to(ROOT)), format='WAV PCM 24-bit', sha256=sha(MASTER), bytes=MASTER.stat().st_size)))
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print('MASTER', json.dumps(manifest['loudness']), round(time.time() - started, 1), 's', flush=True)
    return manifest


# ---------------------------------------------------------------- mux and checks

def probe(path):
    return json.loads(subprocess.run([FFPROBE, '-v', 'error', '-count_packets', '-show_streams', '-show_format', '-of', 'json',
                                      str(path)], capture_output=True, text=True, check=True).stdout)


def mux():
    """Video packets are stream-copied from the silent cut, never re-encoded; AAC-LC 256 kbps as in film/mux_audio.py."""
    encoders = subprocess.run([FFMPEG, '-hide_banner', '-encoders'], capture_output=True, text=True, check=True).stdout
    codec = 'aac_at' if ' aac_at ' in encoders else 'aac'
    subprocess.run([FFMPEG, '-y', '-hide_banner', '-loglevel', 'warning', '-i', str(SILENT), '-i', str(MASTER),
                    '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', codec, '-b:a', '256k', '-ar', '48000', '-ac', '2',
                    '-metadata:s:a:0', 'title=Larktun house tour score', '-disposition:a:0', 'default',
                    '-movflags', '+faststart', str(SCORED)], check=True)
    return codec


def overview(master, steps, path):
    """Spectrogram of the master with the form, the rooms and the momentary loudness on one time axis."""
    width, left, top, spec_h = 2400, 90, 64, 520
    seconds = LENGTH / SR
    im = Image.new('RGB', (left + width + 20, top + spec_h + 230), (8, 12, 21))
    d = ImageDraw.Draw(im)
    d.text((left, 16), 'Larktun house tour · procedural score · 112.5 BPM (16 frames per beat) · form, rooms, momentary loudness',
           font=font(24), fill=(235, 240, 248))
    im.paste(Image.fromarray(spectrogram(master.mean(axis=0), 0, seconds, width, spec_h)), (left, top))
    xs = lambda t: left + t / seconds * width
    for f in (60, 250, 1000, 4000, 12000):
        d.text((8, top + spec_h * np.log(16000 / f) / np.log(16000 / 30) - 10), f'{f} Hz' if f < 1000 else f'{f // 1000} kHz',
               font=font(16), fill=(150, 160, 175))
    y0 = top + spec_h + 8
    for bar, name, _ in FORM:
        x = xs((frame_of(bar) - 1) / META['fps'])
        d.line((x, top, x, y0 + 26), fill=(245, 247, 250))
        d.text((x + 4, y0), name, font=font(18), fill=(245, 247, 250))
    for s in META['stations'][1:]:
        x = xs((s['frames'][0] - 1) / META['fps'])
        d.line((x, y0 + 32, x, y0 + 56), fill=(47, 224, 200))
        d.text((x + 3, y0 + 34), s['name'], font=font(15), fill=(47, 224, 200))
    base = y0 + 210
    d.text((8, base - 110), 'LUFS M', font=font(16), fill=(235, 240, 248))
    ref = base - 36 / 50 * 130
    d.line((left, ref, left + width, ref), fill=(90, 70, 70))
    d.text((left + width - 110, ref - 22), '−14 LUFS', font=font(16), fill=(200, 140, 140))
    pts = [(xs(t - .2), base - np.clip((m + 50) / 50, 0, 1) * 130) for t, m, _ in steps if 0 <= t - .2 <= seconds]
    d.line(pts, fill=(255, 120, 120), width=2)
    im.save(path)


def publish(manifest):
    codec = mux()
    silent, scored = probe(SILENT), probe(SCORED)
    video = [s for s in scored['streams'] if s['codec_type'] == 'video']
    audio = [s for s in scored['streams'] if s['codec_type'] == 'audio']
    assert len(video) == 1 and len(audio) == 1 and len(scored['streams']) == 2, scored['streams']
    v, a, v0 = video[0], audio[0], silent['streams'][0]
    same = ('codec_name', 'profile', 'width', 'height', 'r_frame_rate', 'pix_fmt', 'color_range', 'color_space', 'color_transfer',
            'color_primaries', 'nb_read_packets')
    assert all(v.get(k) == v0.get(k) for k in same), {k: (v.get(k), v0.get(k)) for k in same}
    assert int(v['nb_read_packets']) == FRAMES and (v['width'], v['height']) == (1920, 1080)
    assert a['codec_name'] == 'aac' and a['sample_rate'] == '48000' and a['channels'] == 2, a
    assert packet_md5(SILENT, 'v') == packet_md5(SCORED, 'v'), 'video packets differ from the silent cut'
    subprocess.run([FFMPEG, '-v', 'error', '-xerror', '-i', str(SCORED), '-f', 'null', '-'], check=True, capture_output=True)
    master, decoded = decode(MASTER), decode(SCORED)
    n = min(master.shape[1], decoded.shape[1])
    lags = [best_lag(master.mean(axis=0)[int(t * SR):int((t + 30) * SR)], decoded.mean(axis=0)[int(t * SR):int((t + 30) * SR)])
            for t in (25, 175)]
    snr = 10 * np.log10(np.sum(master[:, :n] ** 2) / np.sum((decoded[:, :n] - master[:, :n]) ** 2))
    tail = float(np.max(np.abs(decoded[:, LENGTH - 2048:n])))
    measured = loudness(SCORED)
    assert lags == [0, 0] and abs(decoded.shape[1] - LENGTH) <= 2048 and snr > 15 and tail < db(-40), (lags, decoded.shape, snr, tail)
    assert abs(measured['integrated_lufs'] - manifest['loudness']['integrated_lufs']) <= .5, measured
    overview(master, loudness(MASTER)['steps'], AUDIO / 'music_overview.png')
    manifest['mux'] = dict(
        path=str(SCORED.relative_to(ROOT)), sha256=sha(SCORED), bytes=SCORED.stat().st_size, audio_codec=codec,
        video_packets_identical_to=str(SILENT.relative_to(ROOT)), video_frames=int(v['nb_read_packets']),
        video=dict(codec=v['codec_name'], width=v['width'], height=v['height'], fps=v['r_frame_rate'], color=v.get('color_primaries')),
        audio=dict(codec=a['codec_name'], profile=a.get('profile'), bit_rate=a.get('bit_rate'), sample_rate=48000, channels=2,
                   start_time=a.get('start_time'), duration=a.get('duration')),
        decoded_vs_master=dict(lag_samples_at_25s_and_175s=lags, snr_db=round(float(snr), 1), decoded_samples=int(decoded.shape[1]),
                               last_2048_samples_peak_dbfs=round(20 * np.log10(max(tail, 1e-12)), 1)),
        loudness={k: val for k, val in measured.items() if k != 'steps'}, full_decode='ffmpeg -xerror: no errors',
        evidence=str((AUDIO / 'music_overview.png').relative_to(ROOT)))
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print('MUX', json.dumps({k: val for k, val in manifest['mux'].items() if k != 'sha256'}, ensure_ascii=False), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['all', 'render', 'mux'], default='all')
    stage = ap.parse_args().stage
    manifest = render() if stage in ('all', 'render') else json.loads(MANIFEST.read_text())
    if stage in ('all', 'mux'):
        publish(manifest)


if __name__ == '__main__':
    main()
