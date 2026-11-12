"""Narration with edge-tts, one sentence at a time, with controlled suspense pauses + word timings.

Usage: python -I tts_edge.py <script.json> <out.wav> <words.json> [voice] [rate] [pitch] [extra_pause_before]
  extra_pause_before: "6:1.0,7:0.4" adds seconds of silence before paragraph index 6 and 7
Needs HTTPS_PROXY in the environment (the sandbox reaches the service through it).
"""
import asyncio
import json
import os
import re
import subprocess
import sys

import numpy as np

script_path, out_wav, out_words = sys.argv[1:4]
voice = sys.argv[4] if len(sys.argv) > 4 else "pt-BR-AntonioNeural"
rate = sys.argv[5] if len(sys.argv) > 5 else "-8%"
pitch = sys.argv[6] if len(sys.argv) > 6 else "-4Hz"
extra = {}
if len(sys.argv) > 7 and sys.argv[7]:
    for kv in sys.argv[7].split(","):
        k, v = kv.split(":")
        extra[int(k)] = float(v)

import edge_tts

SR = 24000
chunks = json.load(open(script_path))
proxy = os.environ.get("HTTPS_PROXY")
tmp = out_wav + ".parts"
os.makedirs(tmp, exist_ok=True)


def trim(a, thr=0.008):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a
    return a[max(0, idx[0] - int(0.015 * SR)): min(len(a), idx[-1] + int(0.05 * SR))]


async def synth(text, path):
    spoken = text.replace("…", "...").replace('"', "")
    for attempt in range(3):
        try:
            await edge_tts.Communicate(spoken, voice, rate=rate, pitch=pitch, proxy=proxy).save(path)
            return
        except Exception as e:  # network hiccup
            if attempt == 2:
                raise
            await asyncio.sleep(1.5)


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


async def main():
    pieces, words, t = [np.zeros(int(0.35 * SR), np.float32)], [], 0.35
    k = 0
    for ci, (_, _, text) in enumerate(chunks):
        sents = [s.strip() for s in re.findall(r"[^.!?…]+[.!?…]*", text) if s.strip()]
        if ci > 0:
            gap = 0.95 + extra.get(ci, 0.0)
            pieces.append(np.zeros(int(gap * SR), np.float32)); t += gap
        for si, sent in enumerate(sents):
            p = f"{tmp}/s{k:03d}.mp3"; k += 1
            await synth(sent, p)
            a = trim(load(p))
            d = len(a) / SR
            ws = sent.split()
            wt = [len(w.strip(".,!?:…")) + 1.5 + (2 if w.endswith((",", "…")) else 0) for w in ws]
            tot, acc = sum(wt), 0.0
            for w, x in zip(ws, wt):
                words.append({"text": w, "type": "word", "start": round(t + d * acc / tot, 3), "end": round(t + d * (acc + x) / tot - 0.03, 3)})
                acc += x
            pieces.append(a); t += d
            if si < len(sents) - 1:
                gap = 0.62 if sent.endswith("…") else (0.34 if sent.endswith(("?", "!")) else 0.3)
                pieces.append(np.zeros(int(gap * SR), np.float32)); t += gap
        print(f"paragraph {ci + 1}/{len(chunks)} -> {t:.1f}s", flush=True)
    full = np.concatenate(pieces)
    import wave
    full = full / (np.max(np.abs(full)) + 1e-9) * 0.9
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((full * 32767).astype("<i2").tobytes())
    json.dump({"words": words}, open(out_words, "w"), ensure_ascii=False)
    print("total", round(len(full) / SR, 2), "s,", len(words), "words")

asyncio.run(main())
