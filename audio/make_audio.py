#!/usr/bin/env python3
"""Sintetiza a trilha de 10 s da animação (48 kHz, estéreo, WAV 16 bits).

- pad ambiente suave (Ré maior com 9ª) do início ao fim;
- "plins" de gota sincronizados com os eventos visuais;
- swell leve chegando aos 6 s (início da chuva);
- acorde final suave aos 9 s.

Uso: python3 audio/make_audio.py [saida.wav]
"""
import sys
import wave

import numpy as np

SR = 48000
DUR = 10.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(20261008)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env_adsr(length, a, r):
    e = np.ones(length)
    na = max(1, int(a * SR))
    nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def place(buf, sig, start, gain=1.0, pan=0.0):
    i = int(start * SR)
    j = min(N, i + len(sig))
    if j <= i:
        return
    left = np.cos((pan + 1) * np.pi / 4)
    right = np.sin((pan + 1) * np.pi / 4)
    buf[0, i:j] += sig[: j - i] * gain * left
    buf[1, i:j] += sig[: j - i] * gain * right


def lowpass(x, cutoff):
    """Passa-baixas de um polo; cutoff pode ser escalar ou um vetor por amostra."""
    cutoff = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    a = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def plin(freq, dur=0.55):
    """Gota d'água: senoide com glissando ascendente rápido e decaimento curto."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = freq * (1 + 0.55 * (1 - np.exp(-tt / 0.025)))
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) * np.exp(-tt / 0.085)
    ring = 0.35 * np.sin(2 * np.pi * freq * 2.01 * tt) * np.exp(-tt / 0.16)
    click = 0.15 * rng.standard_normal(n) * np.exp(-tt / 0.003)
    s = body + ring + click
    s[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    return s


def soft_tone(freq, dur, attack=0.08, decay=1.2):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    s = (
        np.sin(2 * np.pi * freq * tt)
        + 0.3 * np.sin(2 * np.pi * freq * 2 * tt) * np.exp(-tt / 0.5)
        + 0.12 * np.sin(2 * np.pi * freq * 3 * tt) * np.exp(-tt / 0.3)
    )
    e = np.minimum(1, tt / attack) * np.exp(-tt / decay)
    return s * e


dry = np.zeros((2, N))

# ---------------------------------------------------------------- pad
pad_notes = [midi(50), midi(57), midi(62), midi(66), midi(69), midi(76)]
pad = np.zeros(N)
for k, f in enumerate(pad_notes):
    for det in (-0.12, 0.12):
        ff = f * 2 ** (det / 12)
        pad += np.sin(2 * np.pi * ff * t + k) * (0.9 if k < 2 else 0.55)
pad += 0.25 * lowpass(rng.standard_normal(N), 700)
lfo = 0.85 + 0.15 * np.sin(2 * np.pi * 0.2 * t)
# swell: cresce até os 6 s e volta suavemente
swell = 0.55 + 0.6 * np.exp(-((t - 6.0) / 0.9) ** 2) * (t < 6.0) + 0.6 * np.exp(-((t - 6.0) / 1.4) ** 2) * (t >= 6.0)
pad_env = np.clip(t / 0.6, 0, 1) * np.clip((DUR - t) / 0.4, 0, 1)
pad = lowpass(pad, 900 + 1800 * np.exp(-((t - 6.0) / 1.0) ** 2)) * lfo * swell * pad_env
dry[0] += pad * 0.055
dry[1] += np.roll(pad, 240) * 0.055

# swell de ruído "ar/água" aos 6 s
noise = rng.standard_normal(N)
cut = 300 + 3200 * np.exp(-((t - 6.0) / 0.8) ** 2)
air = lowpass(lowpass(noise, cut), cut) * np.exp(-((t - 5.95) / 0.75) ** 2)
dry[0] += air * 0.11
dry[1] += np.roll(air, 600) * 0.11

# ---------------------------------------------------------------- plins
# (tempo, nota MIDI, ganho, pan)
events = [
    (0.10, 86, 0.55, 0.0),   # a gota surge
    (1.18, 81, 0.35, 0.0),   # pulso
    (2.03, 88, 0.40, -0.4),  # divisão em três
    (2.16, 85, 0.38, 0.4),
    (2.29, 81, 0.36, 0.0),
    (4.25, 93, 0.16, -0.5),  # morph para nuvens (brilho suave)
    (4.45, 90, 0.16, 0.5),
    (4.65, 88, 0.16, 0.0),
]
# chuva: 9 batidas a cada 0,2 s a partir dos 6 s (pentatônica de Ré)
rain_scale = [86, 83, 81, 78, 81, 83, 86, 88, 90]
for k, note in enumerate(rain_scale):
    events.append((6.0 + k * 0.2, note, 0.42, [-0.5, 0.0, 0.5][k % 3]))
    # respingo mais grave quando a gota toca o rio (~0,45 s depois)
    events.append((6.45 + k * 0.2, note - 12, 0.18, [-0.5, 0.0, 0.5][k % 3]))
events.append((8.72, 86, 0.5, 0.0))  # a gota se reforma

for when, note, gain, pan in events:
    place(dry, plin(midi(note)), when, gain, pan)

# ---------------------------------------------------------------- acorde final (9 s)
for k, note in enumerate([62, 66, 69, 73, 76]):
    place(dry, soft_tone(midi(note), 1.2, attack=0.06 + 0.02 * k, decay=1.1), 9.0 + 0.025 * k, 0.12, (k - 2) * 0.25)
place(dry, soft_tone(midi(50), 1.2, attack=0.1, decay=1.4), 9.0, 0.14, 0.0)

# ---------------------------------------------------------------- reverb
ir_len = int(2.0 * SR)
ir_t = np.arange(ir_len) / SR
wet = np.zeros_like(dry)
for ch in range(2):
    ir = rng.standard_normal(ir_len) * np.exp(-ir_t / 0.45)
    ir = lowpass(ir, 5000)
    ir /= np.sqrt(np.sum(ir ** 2))
    size = 1 << int(np.ceil(np.log2(N + ir_len)))
    conv = np.fft.irfft(np.fft.rfft(dry[ch], size) * np.fft.rfft(ir, size), size)[:N]
    wet[ch] = conv
mixed = dry * 0.8 + wet * 0.35

# fade de saída casando com o fade visual dos últimos 6 quadros (0,25 s)
fade = np.clip((DUR - t) / 0.25, 0, 1) ** 1.5
mixed *= fade
mixed[:, : int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))

peak = np.max(np.abs(mixed))
mixed *= 0.89 / peak  # cerca de -1 dBFS

out = sys.argv[1] if len(sys.argv) > 1 else "audio/trilha.wav"
pcm = (np.clip(mixed.T, -1, 1) * 32767).astype("<i2")
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("ok:", out)
