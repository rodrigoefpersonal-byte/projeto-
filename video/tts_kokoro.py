"""Narration with Kokoro (free, Apache-2.0) + word timings for captions.

Each paragraph of script.json is spoken sentence by sentence, so sentence
boundaries are exact; word times inside a sentence are spread by word length.

Usage: python -I tts_kokoro.py <model_dir> <script.json> <out.wav> <words.json> [voice] [speeds]
  speeds: comma-separated speed per paragraph (default 1.05 for all)
"""
import json
import re
import sys

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

model_dir, script_path, out_wav, out_words = sys.argv[1:5]
voice = sys.argv[5] if len(sys.argv) > 5 else "pm_santa"
chunks = json.load(open(script_path))
speeds = [float(s) for s in sys.argv[6].split(",")] if len(sys.argv) > 6 else [1.05] * len(chunks)

k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
SR = 24000
PAUSE_SENT, PAUSE_ELLIPSIS, PAUSE_PARA = 0.28, 0.45, 0.55


def trim(a, thr=0.012):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a
    s, e = max(0, idx[0] - int(0.02 * SR)), min(len(a), idx[-1] + int(0.06 * SR))
    return a[s:e]


pieces, words, t = [], [], 0.25
pieces.append(np.zeros(int(0.25 * SR), np.float32))
for ci, (_, _, text) in enumerate(chunks):
    # split into sentences, keeping the closing punctuation (… counts as a break)
    sents = [s.strip() for s in re.findall(r"[^.!?…]+[.!?…]*", text) if s.strip()]
    for si, sent in enumerate(sents):
        spoken = sent.replace("…", ",") if not sent.endswith("…") else sent[:-1] + "."
        audio, sr = k.create(spoken, voice=voice, speed=speeds[ci], lang="pt-br")
        assert sr == SR
        audio = trim(np.asarray(audio, np.float32))
        dur = len(audio) / SR
        ws = sent.split()
        wt = [len(w.strip(".,!?:…")) + 1.5 + (2 if w.endswith(",") else 0) for w in ws]
        tot, acc = sum(wt), 0.0
        for w, x in zip(ws, wt):
            st = t + dur * acc / tot
            acc += x
            words.append({"text": w, "type": "word", "start": round(st, 3), "end": round(t + dur * acc / tot - 0.03, 3)})
        pieces.append(audio)
        t += dur
        gap = PAUSE_ELLIPSIS if sent.endswith("…") else PAUSE_SENT
        if si == len(sents) - 1:
            gap = PAUSE_PARA
        pieces.append(np.zeros(int(gap * SR), np.float32))
        t += gap
    print(f"paragraph {ci + 1}/{len(chunks)} -> {t:.1f}s", flush=True)

full = np.concatenate(pieces)
full = full / (np.max(np.abs(full)) + 1e-9) * 0.9
sf.write(out_wav, full, SR)
json.dump({"words": words}, open(out_words, "w"), ensure_ascii=False)
print("total", round(len(full) / SR, 2), "s,", len(words), "words")
