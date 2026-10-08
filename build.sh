#!/usr/bin/env bash
# Gera out/gota-dagua.mp4: renderiza os quadros, sintetiza o áudio e codifica.
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p out
rm -rf frames

if ! node -e "require('playwright')" 2>/dev/null; then
  export NODE_PATH="${NODE_PATH:-$(npm root -g)}"
fi

node render/render-frames.cjs frames
python3 audio/make_audio.py audio/trilha.wav

ffmpeg -y -loglevel error \
  -framerate 24 -i frames/frame_%04d.png \
  -i audio/trilha.wav \
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -profile:v high -tune animation \
  -r 24 -g 24 -movflags +faststart \
  -c:a aac -b:a 192k -shortest \
  out/gota-dagua.mp4

echo "pronto: out/gota-dagua.mp4"
