"""Map SFX cues from script time to narration time using meta.json 'warp' pairs (narration_t, script_t).
Usage: python3 -I retime_sfx.py <part>"""
import json, sys
import numpy as np
P = sys.argv[1]
meta = json.load(open(f'{P}/meta.json'))
cues = json.load(open(f'{P}/sfx-script.json'))
pairs = meta.get('warp')
def inv(o):
    if not pairs: return o
    new = [p[0] for p in pairs]; old = [p[1] for p in pairs]
    return float(np.interp(o, old, new)) if o <= old[-1] else new[-1] + (o - old[-1])
json.dump([{**c, 't': round(inv(c['t']), 3)} for c in cues], open(f'{P}/sfx.json', 'w'), indent=0)
