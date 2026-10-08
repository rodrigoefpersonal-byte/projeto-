# A jornada de uma gota d'água

Motion graphics de 10 s (1920×1080, 24 fps) em flat design minimalista, só com formas vetoriais.
Paleta: azul-petróleo `#0B3C5D`, turquesa `#1FB5AD`, amarelo-sol `#FFD166`, branco-gelo `#F4F9F9`.

**Vídeo final:** [`out/gota-dagua.mp4`](out/gota-dagua.mp4) (H.264 + AAC, 240 quadros, loop perfeito).

| Tempo | O que acontece |
|---|---|
| 0–2 s | Gota turquesa surge do centro com escala elástica (ease-out-back), pulsa uma vez; ondas concêntricas se expandem. |
| 2–4 s | A gota se divide em três que orbitam em arco com rastros luminosos; push-in de câmera; fundo vira gradiente turquesa. |
| 4–6 s | Morphing das gotas em nuvens; o sol sobe pela lateral com raios girando; partículas com parallax. |
| 6–8 s | As nuvens "choram" em ritmo de 0,2 s; as linhas verticais de chuva formam um rio senoidal em duas camadas. |
| 8–10 s | O rio se curva em espiral e tudo converge ao centro, reformando a gota; zoom, brilho e o texto "Todo ciclo recomeça" (Poppins, fade + deslize). Fade out nos últimos 6 quadros. |

O último quadro é idêntico ao primeiro (fundo azul-petróleo), então o vídeo roda em loop sem corte.

## Áudio

`audio/make_audio.py` sintetiza a trilha (sem samples externos): pad ambiente em Ré maior, "plins" de gota
sincronizados com cada evento (surgimento, divisão, cada batida da chuva e respingo no rio, reforma da gota),
swell leve aos 6 s e acorde final suave aos 9 s.

## Como funciona

- `animation.js` — toda a animação como função pura do tempo (`GOTA.render(ctx, t)`) em Canvas 2D.
- `index.html` — player no navegador (play/pause e linha do tempo quadro a quadro).
- `render/render-frames.cjs` — exporta os 240 quadros em PNG com Chromium headless (Playwright).
- `build.sh` — renderiza quadros + áudio e codifica `out/gota-dagua.mp4` com ffmpeg.

```bash
# requisitos: node + playwright (com Chromium), python3 + numpy, ffmpeg
./build.sh
```

Para ver ao vivo, sirva a pasta (ex.: `npx serve .`) e abra `index.html`.

Fonte Poppins (SIL Open Font License, ver `fonts/OFL-Poppins.txt`).
