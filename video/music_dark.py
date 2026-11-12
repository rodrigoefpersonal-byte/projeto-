"""Dark suspense bed: low drone, slow heartbeat and a creeping rise.
Usage: python3 -I music_dark.py <out.wav> <duration_s> [peak_time_s]"""
import sys, wave
import numpy as np
SR = 48000
out, dur = sys.argv[1], float(sys.argv[2])
peak = float(sys.argv[3]) if len(sys.argv) > 3 else dur * 0.8
n = int(SR * dur); t = np.arange(n) / SR
def pad(f, g, wob):
    ph = 2 * np.pi * np.cumsum(f * (1 + wob * np.sin(2 * np.pi * 0.11 * t))) / SR
    return g * (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.18 * np.sin(3 * ph))
rise = np.clip(t / peak, 0, 1) ** 1.6
L = pad(55.0, 0.5, 0.004) + pad(82.4, 0.3, 0.006) + pad(110.0, 0.16, 0.008) + rise * (pad(116.5, 0.25, 0.01) + pad(220.0, 0.08, 0.02))
tremolo = 0.75 + 0.25 * np.sin(2 * np.pi * (0.3 + 0.7 * rise) * t)
L = L * tremolo
hb = np.zeros(n)
period = 1.05 - 0.25 * rise
tt = 0.5
while tt < dur - 0.4:
    for off, g in ((0.0, 1.0), (0.22, 0.7)):
        i = int((tt + off) * SR); m = min(int(0.3 * SR), n - i)
        if m > 0:
            k = np.arange(m) / SR
            hb[i:i + m] += g * np.sin(2 * np.pi * np.cumsum(48 + 30 * np.exp(-k * 28)) / SR) * np.exp(-k * 14)
    tt += float(np.interp(tt, t, period))
mix = L * 0.55 + hb * 0.5 * (0.4 + 0.6 * rise)
mix *= np.minimum(1, t / 2.0) * np.minimum(1, (dur - t) / 2.0)
mix = mix / (np.sqrt(np.mean(mix ** 2)) + 1e-9) * 10 ** (-26 / 20)
st = np.stack([mix, np.roll(mix, 40)], 1)
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(st, -1, 1) * 32767).astype('<i2').tobytes())
print('ok', out)
