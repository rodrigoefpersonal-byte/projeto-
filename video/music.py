"""Procedural playful marimba loop (C major, 105 BPM) for the light part of a video.

Usage: python3 -I music.py <out.wav> <duration_s>
"""
import sys
import wave

import numpy as np

SR = 48000
BPM = 105
BEAT = 60 / BPM
rng = np.random.default_rng(4)


def note_hz(midi):
    return 440 * 2 ** ((midi - 69) / 12)


def marimba(freq, d=0.9, vel=1.0):
    n = int(SR * d)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * freq * t) * np.exp(-t * 6)
         + 0.35 * np.sin(2 * np.pi * freq * 3.93 * t) * np.exp(-t * 22)
         + 0.12 * np.sin(2 * np.pi * freq * 9.2 * t) * np.exp(-t * 45))
    atk = np.clip(t / 0.002, 0, 1)
    return x * atk * vel * 0.32


def pluck_bass(freq, d=0.5, vel=1.0):
    n = int(SR * d)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)
    return np.tanh(x * 1.2) * np.exp(-t * 7) * np.clip(t / 0.004, 0, 1) * vel * 0.38


def shaker(d=0.07, vel=1.0):
    n = int(SR * d)
    x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x]))  # crude high-pass
    t = np.arange(n) / SR
    return x * np.exp(-t * 60) * vel * 0.05


def clap(d=0.2, vel=1.0):
    n = int(SR * d)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x]))
    e = np.exp(-t * 30) * (1 + 0.6 * np.exp(-((t - 0.012) ** 2) / 1e-5))
    return x * e * vel * 0.09


def add(buf, sig, t):
    i = int(t * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


# chord progression C - Am - F - G (one bar each), arpeggio patterns
CHORDS = [[60, 64, 67, 72], [57, 60, 64, 69], [53, 57, 60, 65], [55, 59, 62, 67]]
BASS = [36, 33, 29, 31]
MELODY = [  # (beat offset within 4-bar phrase, midi, length beats)
    (0, 76, 1), (1, 79, 0.5), (1.5, 76, 0.5), (2, 74, 1), (3, 72, 1),
    (4, 72, 1), (5, 76, 0.5), (5.5, 72, 0.5), (6, 69, 2),
    (8, 69, 1), (9, 72, 0.5), (9.5, 77, 0.5), (10, 76, 1), (11, 74, 1),
    (12, 74, 0.5), (12.5, 76, 0.5), (13, 79, 1), (14, 77, 0.5), (14.5, 74, 0.5), (15, 71, 1),
]


def main():
    out, dur = sys.argv[1], float(sys.argv[2])
    L = np.zeros(int(SR * (dur + 2)))
    R = np.zeros_like(L)
    bars = int(dur / (4 * BEAT)) + 1
    for b in range(bars):
        t0 = b * 4 * BEAT
        ch = CHORDS[b % 4]
        # arpeggio 8ths
        pat = [0, 1, 2, 3, 2, 1, 2, 3]
        for k, idx in enumerate(pat):
            s = marimba(note_hz(ch[idx]), 0.6, 0.55 + 0.15 * (k % 2 == 0))
            pan = 0.35 + 0.3 * (idx / 3)
            add(L, s * (1 - pan), t0 + k * BEAT / 2)
            add(R, s * pan, t0 + k * BEAT / 2)
        # bass on 1 and 3 (+ pickup)
        for beat, oct_ in [(0, 0), (2, 0), (3.5, 12)]:
            s = pluck_bass(note_hz(BASS[b % 4] + oct_), 0.45, 0.9)
            add(L, s, t0 + beat * BEAT)
            add(R, s, t0 + beat * BEAT)
        # shaker 16ths, claps on 2 and 4 (from bar 2)
        for k in range(16):
            s = shaker(vel=1.0 if k % 2 else 0.55)
            add(L, s * 0.8, t0 + k * BEAT / 4)
            add(R, s * 1.2, t0 + k * BEAT / 4)
        if b >= 1:
            for beat in (1, 3):
                s = clap()
                add(L, s, t0 + beat * BEAT)
                add(R, s, t0 + beat * BEAT)
        # melody enters from bar 2 (phrase every 4 bars)
        if b >= 2:
            phrase_t0 = ((b - 2) // 4) * 16 * BEAT + 2 * 4 * BEAT
            for off, m, ln in MELODY:
                tt = phrase_t0 + off * BEAT
                if t0 <= tt < t0 + 4 * BEAT:
                    s = marimba(note_hz(m), 0.9, 0.85)
                    add(L, s * 0.55, tt)
                    add(R, s * 0.45, tt)
    n = int(SR * dur)
    st = np.stack([L[:n], R[:n]], 1)
    fade = int(SR * 0.4)
    st[-fade:] *= np.linspace(1, 0, fade)[:, None]
    st /= np.max(np.abs(st)) + 1e-9
    st *= 0.89
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    main()
