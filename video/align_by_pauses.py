"""Word timings for a human recording of a known script, without a speech-to-text model.

The script's sentences are matched to the natural pauses of the recording: a dynamic
program picks, for each sentence boundary, the pause that best fits the time expected from
sentence length (and prefers longer pauses). Words inside a sentence are spread by length.

Usage: python -I align_by_pauses.py <audio> <script.json> <out_words.json>
"""
import json
import re
import subprocess
import sys

import numpy as np

audio, script_path, out_path = sys.argv[1:4]
SR, H = 16000, 160
a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", audio, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                 capture_output=True, check=True).stdout, dtype=np.float32)
e = 20 * np.log10(np.sqrt((a[: len(a) // H * H].reshape(-1, H) ** 2).mean(1)) + 1e-9)
voiced = e > -38
idx = np.where(voiced)[0]
t0, t1 = idx[0] * 0.01, (idx[-1] + 1) * 0.01

pauses, i = [], idx[0]
while i < idx[-1]:
    if not voiced[i]:
        j = i
        while j < len(voiced) and not voiced[j]:
            j += 1
        if (j - i) * 0.01 >= 0.18:
            pauses.append((i * 0.01, j * 0.01))
        i = j
    else:
        i += 1

chunks = json.load(open(script_path))
sents = []
for _, _, text in chunks:
    sents += [s.strip() for s in re.findall(r"[^.!?…]+[.!?…]*", text) if s.strip()]
n = len(sents)
w = np.array([len(re.sub(r"\W", "", s)) for s in sents], float)
avg_pause = 0.45
rate = (t1 - t0 - avg_pause * (n - 1)) / w.sum()
exp = [t0 + rate * w[: k + 1].sum() + avg_pause * (k + 0.5) for k in range(n - 1)]
m = len(pauses)
nw = np.array([len(x.split()) for x in sents], float)


def rate_pen(k, d):
    r = nw[k] / max(d, 0.15)
    if r > 5.0:
        return ((r - 5.0) / 0.7) ** 2
    if r < 1.9:
        return ((1.9 - r) / 0.4) ** 2
    return 0.0


INF = 1e18
cost = np.full((n - 1, m), INF)
back = np.full((n - 1, m), -1, int)
for k in range(n - 1):
    for j in range(m):
        mid = (pauses[j][0] + pauses[j][1]) / 2
        c = ((mid - exp[k]) / 2.5) ** 2 - 1.0 * min(pauses[j][1] - pauses[j][0], 1.0)
        if k == 0:
            cost[k, j] = c + rate_pen(0, pauses[j][0] - t0)
        else:
            best, bj = INF, -1
            for jp in range(j):
                if cost[k - 1, jp] >= INF:
                    continue
                v = cost[k - 1, jp] + rate_pen(k, pauses[j][0] - pauses[jp][1])
                if v < best:
                    best, bj = v, jp
            if bj >= 0:
                cost[k, j], back[k, j] = best + c, bj
final = [cost[n - 2, j] + rate_pen(n - 1, t1 - pauses[j][1]) if cost[n - 2, j] < INF else INF for j in range(m)]
j = int(np.argmin(final))
chosen = [j]
for k in range(n - 2, 0, -1):
    j = back[k, j]
    chosen.append(j)
chosen = chosen[::-1]

bounds = [(t0, None)]
for j in chosen:
    bounds[-1] = (bounds[-1][0], pauses[j][0])
    bounds.append((pauses[j][1], None))
bounds[-1] = (bounds[-1][0], t1)

words, flags = [], []
for s, (st, en) in zip(sents, bounds):
    ws = s.split()
    wt = [len(x.strip(".,!?:…")) + 1.5 for x in ws]
    tot, acc = sum(wt), 0.0
    for x, k in zip(ws, wt):
        words.append({"text": x, "type": "word", "start": round(st + (en - st) * acc / tot, 3),
                      "end": round(st + (en - st) * (acc + k) / tot - 0.03, 3)})
        acc += k
    rps = len(ws) / max(en - st, 0.1)
    if rps > 5.2 or rps < 1.4:
        flags.append(f"{st:6.1f}s {rps:.1f} palavras/s  {s[:50]}")
json.dump({"words": words}, open(out_path, "w"), ensure_ascii=False)
print(f"{n} frases, {m} pausas candidatas, fala de {t0:.1f}s a {t1:.1f}s, {len(words)} palavras")
print("frases fora do ritmo normal:" if flags else "todas as frases em ritmo normal")
for f in flags:
    print("  ", f)
