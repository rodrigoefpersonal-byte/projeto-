"""Estimate word timings from a script (for previews before the real narration exists).
Usage: python3 -I fake_words.py <script.json> <words.json>"""
import json, sys
chunks = json.load(open(sys.argv[1]))
out = []
for a, b, text in chunks:
    ws = text.split()
    wt = [len(w) + 2 + (6 if w.endswith('…') else 3 if w[-1] in '.!?:' else 1 if w[-1] == ',' else 0) for w in ws]
    tot = sum(wt); t = a
    for w, k in zip(ws, wt):
        d = (b - a) * k / tot
        out.append({"text": w, "type": "word", "start": round(t, 3), "end": round(t + d * 0.8, 3)})
        t += d
json.dump({"words": out}, open(sys.argv[2], 'w'), ensure_ascii=False)
for w in out: print(f"{w['start']:.2f} {w['text']}", end=' | ')
