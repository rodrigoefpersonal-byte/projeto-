#!/usr/bin/env bash
# Mix narration + music bed (ducked under the voice) + SFX and mux with the rendered video.
# Usage: ./mix.sh p1
set -euo pipefail
cd "$(dirname "$0")"
P=${1:-p1}
DUR=$(python3 -c "import json;print(json.load(open('$P/meta.json'))['duration'])")

ffmpeg -y -v error \
  -i assets/narracao-$P.mp3 \
  -i build/$P-marimba.wav \
  -i assets/musica-$P.mp3 \
  -i build/$P-sfx.wav \
  -i build/$P-silent.mp4 \
  -filter_complex "
    [0:a]aresample=48000,volume=5.8dB,highpass=f=70,acompressor=threshold=0.1:ratio=3:attack=5:release=120:makeup=1.5,apad=whole_dur=${DUR},asplit=2[nar][sc];
    [1:a]aresample=48000,volume=-15.7dB,afade=t=out:st=30.2:d=0.7[m1];
    [2:a]aresample=48000,atrim=start=48:end=71.5,asetpts=PTS-STARTPTS,volume=10.5dB,afade=t=in:d=0.3,afade=t=out:st=20.5:d=2.5,adelay=30660|30660[m2];
    [m1][m2]amix=inputs=2:normalize=0:duration=longest[bed];
    [bed][sc]sidechaincompress=threshold=0.04:ratio=5:attack=25:release=400:makeup=1[duck];
    [3:a]aresample=48000,volume=-5dB[fx];
    [nar][duck][fx]amix=inputs=3:normalize=0:duration=first,atrim=0:${DUR},loudnorm=I=-14:TP=-1.5:LRA=11[out]" \
  -map 4:v -map "[out]" -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart -t "$DUR" \
  build/$P-final.mp4
echo "ok build/$P-final.mp4"
