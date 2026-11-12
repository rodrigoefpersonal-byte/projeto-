"""Procedural sound effects (whoosh, boom, snap, pop) mixed onto a timeline.

Usage: python3 -I sfx.py <cues.json> <out.wav> <duration_s>
cues.json: [{"t": 5.3, "type": "boom", "gain": 0.8}, ...]
"""
import json
import sys
import wave

import numpy as np

SR = 48000
rng = np.random.default_rng(1)


def env(n, attack, decay):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-np.maximum(0, t - attack) / decay)


def lowpass(x, cutoff):
    # one-pole low-pass with time-varying cutoff (array or scalar)
    cutoff = np.broadcast_to(cutoff, x.shape)
    y = np.zeros_like(x)
    prev = 0.0
    k = 1 - np.exp(-2 * np.pi * cutoff / SR)
    for i in range(len(x)):
        prev += k[i] * (x[i] - prev)
        y[i] = prev
    return y


def whoosh(d=0.55):
    n = int(SR * d)
    t = np.linspace(0, 1, n)
    noise = rng.standard_normal(n)
    cut = 300 + 5200 * np.sin(np.pi * t) ** 2
    x = lowpass(noise, cut) - lowpass(noise, cut * 0.35)
    return x * np.sin(np.pi * t) ** 1.5 * 1.6


def boom(d=1.6):
    n = int(SR * d)
    t = np.arange(n) / SR
    f = 32 + 58 * np.exp(-t * 6)
    ph = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(ph) * env(n, 0.004, 0.55)
    click = lowpass(rng.standard_normal(n), 1800) * env(n, 0.001, 0.03) * 0.9
    return np.tanh((sub + click) * 1.8) * 0.9


def snap(d=0.35):
    n = int(SR * d)
    x = rng.standard_normal(n) * env(n, 0.0005, 0.018)
    x2 = rng.standard_normal(n) * env(n, 0.0005, 0.05) * 0.4
    hp = x - lowpass(x, 1500)
    return (hp + (x2 - lowpass(x2, 600))) * 1.4


def pop(d=0.12):
    n = int(SR * d)
    t = np.arange(n) / SR
    f = 900 * np.exp(-t * 18) + 380
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.03) * 0.6


def tick(d=0.06):
    n = int(SR * d)
    x = rng.standard_normal(n) * env(n, 0.0003, 0.006)
    return (x - lowpass(x, 3000)) * 0.8


GEN = {"whoosh": whoosh, "boom": boom, "snap": snap, "pop": pop, "tick": tick}


def thud(d=0.5):
    n = int(SR * d)
    t = np.arange(n) / SR
    f = 52 + 40 * np.exp(-t * 30)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.16)
    knock = lowpass(rng.standard_normal(n), 420) * env(n, 0.001, 0.05) * 1.4
    return np.tanh((sub * 1.6 + knock) * 1.2) * 0.95


def heart(d=0.6):
    out = np.zeros(int(SR * d))
    for off, g in ((0.0, 1.0), (0.2, 0.75)):
        h = thud(0.35) * g * 0.9
        i = int(off * SR)
        out[i:i + len(h)] += h[: len(out) - i]
    return out


def creak(d=2.6):
    n = int(SR * d)
    t = np.arange(n) / SR
    f = 260 + 140 * np.sin(2 * np.pi * 0.37 * t) + 90 * t
    carrier = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(4.02 * np.pi * np.cumsum(f) / SR)
    am = 0.55 + 0.45 * np.sin(2 * np.pi * 9 * t + 3 * np.sin(2 * np.pi * 0.8 * t))
    return carrier * am * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.8 * 0.35


def whisper(d=2.4):
    n = int(SR * d)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    band = lowpass(x, 5200) - lowpass(x, 1800)
    syl = 0.5 + 0.5 * np.sin(2 * np.pi * 3.3 * t + 1.2)
    return band * syl * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5 * 1.8


GEN.update({"thud": thud, "heart": heart, "creak": creak, "whisper": whisper})


def main():
    cues = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    dur = float(sys.argv[3])
    mix = np.zeros(int(SR * dur) + SR)
    cache = {}
    for c in cues:
        kind = c["type"]
        if kind not in cache:
            cache[kind] = GEN[kind]()
        s = cache[kind] * c.get("gain", 1.0)
        i = int(c["t"] * SR)
        mix[i:i + len(s)] += s[: max(0, len(mix) - i)]
    mix = mix[: int(SR * dur)]
    mix = np.clip(mix, -1, 1)
    st = np.stack([mix, mix], 1)
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    main()
