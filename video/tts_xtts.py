"""Narration with XTTS-v2 (open model, expressive, follows a reference voice) + word timings.

The reference clip sets the voice; each paragraph of script.json is spoken in small
groups of sentences (very short sentences are merged so the model stays stable).
Word times inside a group are spread by word length.

NOTE: XTTS-v2 weights are under the Coqui Public Model License (non-commercial use).

Usage: python -I tts_xtts.py <model_dir> <ref.wav> <script.json> <out.wav> <words.json> [speeds]
"""
import json
import os
import re
import sys

import numpy as np
import soundfile as sf
import torch
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

model_dir, ref, script_path, out_wav, out_words = sys.argv[1:6]
chunks = json.load(open(script_path))
speeds = [float(s) for s in sys.argv[6].split(",")] if len(sys.argv) > 6 else [1.05] * len(chunks)
torch.set_num_threads(os.cpu_count() or 4)
torch.manual_seed(7)

cfg = XttsConfig()
cfg.load_json(f"{model_dir}/config.json")
model = Xtts.init_from_config(cfg)
model.load_checkpoint(cfg, checkpoint_dir=model_dir, eval=True)
lat, spk = model.get_conditioning_latents(audio_path=[ref])
SR = 24000
PAUSE_GROUP, PAUSE_PARA = 0.22, 0.45


def trim(a, thr=0.01):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a
    return a[max(0, idx[0] - int(0.02 * SR)): min(len(a), idx[-1] + int(0.08 * SR))]


def groups(text):
    sents = [s.strip() for s in re.findall(r"[^.!?…]+[.!?…]*", text) if s.strip()]
    out, cur = [], ""
    for s in sents:
        cur = (cur + " " + s).strip()
        if len(cur) >= 28:
            out.append(cur)
            cur = ""
    if cur:
        if out and len(cur) < 28:
            out[-1] += " " + cur
        else:
            out.append(cur)
    return out


pieces, words, t = [np.zeros(int(0.25 * SR), np.float32)], [], 0.25
for ci, (_, _, text) in enumerate(chunks):
    gs = groups(text)
    for gi, g in enumerate(gs):
        res = model.inference(g, "pt", lat, spk, temperature=0.72, speed=speeds[ci], repetition_penalty=5.0, enable_text_splitting=False)
        audio = trim(np.asarray(res["wav"], np.float32))
        dur = len(audio) / SR
        ws = g.split()
        wt = [len(w.strip(".,!?:…")) + 1.5 + (2 if w.endswith((",", "…")) else 0) for w in ws]
        tot, acc = sum(wt), 0.0
        for w, x in zip(ws, wt):
            st = t + dur * acc / tot
            acc += x
            words.append({"text": w, "type": "word", "start": round(st, 3), "end": round(t + dur * acc / tot - 0.03, 3)})
        pieces.append(audio)
        t += dur
        gap = PAUSE_PARA if gi == len(gs) - 1 else PAUSE_GROUP
        pieces.append(np.zeros(int(gap * SR), np.float32))
        t += gap
    print(f"paragraph {ci + 1}/{len(chunks)} -> {t:.1f}s", flush=True)

full = np.concatenate(pieces)
full = full / (np.max(np.abs(full)) + 1e-9) * 0.9
sf.write(out_wav, full, SR)
json.dump({"words": words}, open(out_words, "w"), ensure_ascii=False)
print("total", round(len(full) / SR, 2), "s,", len(words), "words")
