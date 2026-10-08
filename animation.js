/*
 * "A jornada de uma gota d'água" — motion graphics, 10 s, 1920x1080, 24 fps.
 *
 * Toda a animação é uma função pura do tempo: render(ctx, t) desenha o quadro
 * no instante t (segundos). Isso permite tanto a reprodução ao vivo no
 * navegador quanto a exportação quadro a quadro (render/render-frames.cjs).
 */
(function (global) {
  'use strict';

  const W = 1920;
  const H = 1080;
  const FPS = 24;
  const DURATION = 10;
  const TOTAL_FRAMES = FPS * DURATION;
  const CX = W / 2;
  const CY = H / 2;
  const TAU = Math.PI * 2;

  // ---------------------------------------------------------------- paleta
  const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const PETROL = hex('#0B3C5D');
  const TURQ = hex('#1FB5AD');
  const SUN = hex('#FFD166');
  const ICE = hex('#F4F9F9');
  const mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
  const rgba = (c, a = 1) =>
    `rgba(${Math.round(c[0])},${Math.round(c[1])},${Math.round(c[2])},${a})`;

  // ---------------------------------------------------------------- easing
  const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
  const lerp = (a, b, t) => a + (b - a) * t;
  const seg = (t, a, b) => clamp01((t - a) / (b - a));
  const inOut = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
  const outCubic = (x) => 1 - Math.pow(1 - x, 3);
  const outBack = (x, s = 1.9) => {
    const c3 = s + 1;
    return 1 + c3 * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2);
  };
  const lerpAngle = (a, b, t) => {
    let d = (b - a) % TAU;
    if (d > Math.PI) d -= TAU;
    if (d < -Math.PI) d += TAU;
    return a + d * t;
  };

  // gerador pseudoaleatório determinístico (mulberry32)
  function rng(seed) {
    return function () {
      seed |= 0;
      seed = (seed + 0x6d2b79f5) | 0;
      let r = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r;
      return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
    };
  }

  // ---------------------------------------------------------------- formas
  // Gota e nuvem são amostradas com o mesmo número de pontos, na mesma ordem
  // (a partir do topo, sentido horário), para que o morphing seja um simples
  // lerp ponto a ponto.
  const N = 220;

  // Gota de "raio" unitário: ponta em y≈-2, corpo redondo centrado em y≈0.
  const DROP_UNIT = (() => {
    const pts = [];
    for (let i = 0; i < N; i++) {
      const s = (i / N) * TAU;
      const x = 1.32 * Math.sin(s) * Math.pow(Math.sin(s / 2), 1.15);
      const y = -1.42 * Math.cos(s) - 0.52;
      pts.push([x, y]);
    }
    return pts;
  })();

  // Nuvem: união de círculos com base achatada, obtida por ray-casting polar.
  const CLOUD_UNIT = (() => {
    const circles = [
      [-118, 18, 52],
      [-62, -28, 70],
      [12, -62, 86],
      [86, -20, 68],
      [138, 20, 46],
      [-70, 34, 50],
      [0, 30, 58],
      [72, 34, 50],
    ];
    const bottom = 62;
    const pts = [];
    for (let i = 0; i < N; i++) {
      const th = -Math.PI / 2 + (i / N) * TAU;
      const dx = Math.cos(th);
      const dy = Math.sin(th);
      let r = 0;
      for (const [cx, cy, cr] of circles) {
        const b = dx * cx + dy * cy;
        const disc = b * b - (cx * cx + cy * cy) + cr * cr;
        if (disc >= 0) r = Math.max(r, b + Math.sqrt(disc));
      }
      if (dy > 0.001) r = Math.min(r, bottom / dy);
      pts.push([dx * r, dy * r + 4]);
    }
    return pts;
  })();

  function shapePoints(m, R, cloudScale, rot) {
    const c = Math.cos(rot);
    const s = Math.sin(rot);
    const out = new Array(N);
    for (let i = 0; i < N; i++) {
      const dx = DROP_UNIT[i][0] * R;
      const dy = DROP_UNIT[i][1] * R;
      const rx = dx * c - dy * s;
      const ry = dx * s + dy * c;
      out[i] = [
        lerp(rx, CLOUD_UNIT[i][0] * cloudScale, m),
        lerp(ry, CLOUD_UNIT[i][1] * cloudScale, m),
      ];
    }
    return out;
  }

  function tracePath(ctx, pts, x, y) {
    ctx.beginPath();
    ctx.moveTo(x + pts[0][0], y + pts[0][1]);
    for (let i = 1; i < pts.length; i++) ctx.lineTo(x + pts[i][0], y + pts[i][1]);
    ctx.closePath();
  }

  /**
   * Desenha um "blob" que vai da gota (m=0) à nuvem (m=1).
   * R: raio da gota; cloudScale: escala da nuvem; rot: rotação da gota.
   */
  function drawBlob(ctx, o) {
    const { x, y, m = 0, R, cloudScale = 1, rot = 0, alpha = 1, glow = 0.6 } = o;
    if (alpha <= 0.001 || (R <= 0.01 && m < 0.001)) return;
    const pts = shapePoints(m, R, cloudScale, rot);
    const ext = lerp(R * 2, 150 * cloudScale, m);

    const dropTop = mix(TURQ, ICE, 0.45);
    const dropBot = mix(TURQ, PETROL, 0.12);
    const cloudTop = ICE;
    const cloudBot = mix(ICE, TURQ, 0.22);
    const g = ctx.createLinearGradient(x - ext * 0.4, y - ext, x + ext * 0.3, y + ext * 0.7);
    g.addColorStop(0, rgba(mix(dropTop, cloudTop, m), alpha));
    g.addColorStop(1, rgba(mix(dropBot, cloudBot, m), alpha));

    ctx.save();
    ctx.shadowColor = rgba(mix(TURQ, ICE, 0.3 + 0.5 * m), 0.55 * glow * alpha);
    ctx.shadowBlur = lerp(R * 0.9, 60 * cloudScale, m);
    tracePath(ctx, pts, x, y);
    ctx.fillStyle = g;
    ctx.fill();
    ctx.restore();

    // brilho especular da gota (some durante o morphing)
    const hl = (1 - m) * alpha;
    if (hl > 0.01 && R > 2) {
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(rot);
      ctx.strokeStyle = rgba(ICE, 0.75 * hl);
      ctx.lineCap = 'round';
      ctx.lineWidth = Math.max(1, R * 0.13);
      ctx.beginPath();
      ctx.arc(0, 0, R * 0.62, Math.PI * 1.02, Math.PI * 1.38);
      ctx.stroke();
      ctx.fillStyle = rgba(ICE, 0.8 * hl);
      ctx.beginPath();
      ctx.arc(-R * 0.18, -R * 0.66, R * 0.07, 0, TAU);
      ctx.fill();
      ctx.restore();
    }
  }

  // ---------------------------------------------------------------- cena
  const DROP_R = 78; // gota principal
  const SMALL_R = 44; // gotas menores
  const ORBIT_R = 250;
  const CLOUDS = [
    { x: 560, y: 300, s: 0.92 },
    { x: 960, y: 230, s: 1.1 },
    { x: 1360, y: 320, s: 0.88 },
  ];

  const orbitTheta = (t) => 2.5 * (t - 2) + 0.35 * Math.pow(Math.max(0, t - 2), 2);

  function orbitPos(i, t) {
    const spread = inOut(seg(t, 2.0, 2.9));
    const a = -Math.PI / 2 + (i * TAU) / 3 + orbitTheta(t);
    const r = ORBIT_R * spread;
    // leve elipse: as gotas descrevem arcos, não um círculo perfeito
    return [CX + Math.cos(a) * r * 1.12, CY + Math.sin(a) * r * 0.86];
  }

  // cada gota vai para a nuvem mais próxima no início da transição
  const CLOUD_OF = (() => {
    const xs = [0, 1, 2].map((i) => ({ i, x: orbitPos(i, 3.6)[0] }));
    xs.sort((a, b) => a.x - b.x);
    const map = [];
    xs.forEach((o, k) => (map[o.i] = k));
    return map;
  })();

  // posição das gotas/nuvens 2–8 s (antes da convergência final)
  function smallPos(i, t) {
    const p = orbitPos(i, t);
    const c = CLOUDS[CLOUD_OF[i]];
    const k = inOut(seg(t, 3.6, 4.9));
    const bob = Math.sin(t * 1.6 + i * 2.1) * 6 * seg(t, 4.6, 5.4);
    return [lerp(p[0], c.x, k), lerp(p[1], c.y, k) + bob];
  }

  function smallRot(i, t) {
    const a = smallPos(i, t);
    const b = smallPos(i, t - 0.03);
    const vx = a[0] - b[0];
    const vy = a[1] - b[1];
    const aligned = Math.atan2(vy, vx) - Math.PI / 2; // ponta oposta ao movimento
    const w = seg(t, 2.0, 2.45) * (1 - inOut(seg(t, 4.15, 5.0)));
    return lerpAngle(0, aligned, w);
  }

  // ---------------------------------------------------------------- chuva
  const BEAT = 0.2;
  const RAIN_START = 6.0;
  const RAIN_BEATS = 9;
  const COLS = [-58, 0, 58];
  const FALL_V0 = 520;
  const FALL_G = 2600;

  const RAIN = (() => {
    const drops = [];
    for (let k = 0; k < RAIN_BEATS; k++) {
      for (let c = 0; c < 3; c++) {
        const cl = CLOUDS[c];
        const col = COLS[(k + c) % 3] * cl.s;
        drops.push({ t0: RAIN_START + k * BEAT, x: cl.x + col, y0: cl.y + 62 * cl.s, cloud: c });
      }
    }
    return drops;
  })();

  // ---------------------------------------------------------------- rio
  const RIVER_SPAN = W + 800;
  const RIVER_X0 = -400;
  const ARC_SPAN = Math.PI * 1.6;
  const RIVER_H = 150;

  function riverLevel(t, layer) {
    const rise = inOut(seg(t, 6.25 + layer * 0.15, 7.5));
    return lerp(H + RIVER_H + 60, layer === 0 ? 990 : 955, rise);
  }

  function riverWave(u, t, layer) {
    const x = u * RIVER_SPAN;
    if (layer === 0) {
      return 17 * Math.sin((x / 520) * TAU - t * 2.3) + 7 * Math.sin((x / 230) * TAU + t * 1.7 + 1.3);
    }
    return 14 * Math.sin((x / 610) * TAU + t * 1.9 + 2.0) + 6 * Math.sin((x / 290) * TAU - t * 2.6);
  }

  // fator de curvatura/convergência do rio (8–10 s)
  function riverCurl(t) {
    return { b: inOut(seg(t, 8.0, 8.7)), c: inOut(seg(t, 8.25, 9.2)) };
  }

  // superfície do rio (camada da frente) num x, ainda reto — usada pela chuva
  function riverSurfaceY(x, t) {
    const u = (x - RIVER_X0) / RIVER_SPAN;
    return riverLevel(t, 0) - RIVER_H - riverWave(u, t, 0);
  }

  function rainState(d, t) {
    // tempo de queda até tocar a superfície (resolvido por iteração)
    let tau = 0.5;
    for (let it = 0; it < 6; it++) {
      const target = riverSurfaceY(d.x, d.t0 + tau) - d.y0;
      tau = (-FALL_V0 + Math.sqrt(FALL_V0 * FALL_V0 + 2 * FALL_G * Math.max(0, target))) / FALL_G;
    }
    return { land: d.t0 + tau, tau };
  }

  function ribbon(t, layer) {
    const { b, c } = riverCurl(t);
    const level = riverLevel(t, layer);
    const R0 = level - CY;
    const Rarc = R0 * (1 - c);
    const spin = c * 2.4 + layer * 0.25 * c;
    const h = RIVER_H * (1 - c) * lerp(1, 0.6, b) * (layer === 0 ? 1 : 0.92);
    const waveAmp = 1 - c;
    const M = 160;
    const top = [];
    const bot = [];
    for (let j = 0; j <= M; j++) {
      const u = j / M;
      const sx = RIVER_X0 + u * RIVER_SPAN;
      const sy = level;
      const phi = Math.PI / 2 - (u - 0.5) * ARC_SPAN + spin;
      const ax = CX + Math.cos(phi) * Rarc;
      const ay = CY + Math.sin(phi) * Rarc;
      const px = lerp(sx, ax, b);
      const py = lerp(sy, ay, b);
      // normal: "para cima" no rio reto, "para o centro" no rio curvado
      let nx = lerp(0, -Math.cos(phi), b);
      let ny = lerp(-1, -Math.sin(phi), b);
      const nl = Math.hypot(nx, ny) || 1;
      nx /= nl;
      ny /= nl;
      // pontas afinadas quando o rio se curva (sem cortes retos)
      const e = Math.min(u, 1 - u) / 0.14;
      const taper = e >= 1 ? 1 : Math.sin((e * Math.PI) / 2);
      const w = riverWave(u, t, layer) * waveAmp * taper;
      const hh = h * taper;
      top.push([px + nx * (hh + w), py + ny * (hh + w)]);
      bot.push([px - nx * hh, py - ny * hh]);
    }
    return { top, bot, c };
  }

  function drawRiver(ctx, t, layer) {
    if (t < 6.2 || t > 9.6) return;
    const { top, bot, c } = ribbon(t, layer);
    const alpha = 1 - seg(t, 8.9, 9.35);
    if (alpha <= 0) return;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.beginPath();
    ctx.moveTo(top[0][0], top[0][1]);
    for (let i = 1; i < top.length; i++) ctx.lineTo(top[i][0], top[i][1]);
    for (let i = bot.length - 1; i >= 0; i--) ctx.lineTo(bot[i][0], bot[i][1]);
    ctx.closePath();
    const g = ctx.createLinearGradient(0, CY - 200, 0, H);
    if (layer === 0) {
      g.addColorStop(0, rgba(mix(TURQ, ICE, 0.12), 0.95));
      g.addColorStop(1, rgba(mix(TURQ, PETROL, 0.55), 0.95));
    } else {
      g.addColorStop(0, rgba(mix(TURQ, ICE, 0.45), 0.45));
      g.addColorStop(1, rgba(mix(TURQ, PETROL, 0.3), 0.45));
    }
    ctx.fillStyle = g;
    ctx.fill();
    // linha de espuma na crista
    ctx.beginPath();
    ctx.moveTo(top[0][0], top[0][1]);
    for (let i = 1; i < top.length; i++) ctx.lineTo(top[i][0], top[i][1]);
    ctx.strokeStyle = rgba(ICE, layer === 0 ? 0.55 : 0.3);
    ctx.lineWidth = lerp(3, 1.5, c);
    ctx.stroke();
    ctx.restore();
  }

  function drawRain(ctx, t) {
    if (t < RAIN_START || t > 8.6) return;
    ctx.save();
    ctx.lineCap = 'round';
    for (const d of RAIN) {
      if (t < d.t0) continue;
      const { land } = rainState(d, t);
      const tt = t - d.t0;
      if (t < land) {
        const y = d.y0 + FALL_V0 * tt + 0.5 * FALL_G * tt * tt;
        const v = FALL_V0 + FALL_G * tt;
        const len = 70 + v * 0.11;
        const grow = seg(tt, 0, 0.08);
        const g = ctx.createLinearGradient(d.x, y - len, d.x, y);
        g.addColorStop(0, rgba(ICE, 0));
        g.addColorStop(1, rgba(ICE, 0.9));
        ctx.strokeStyle = g;
        ctx.lineWidth = 3.5;
        ctx.beginPath();
        ctx.moveTo(d.x, y - len * grow);
        ctx.lineTo(d.x, y);
        ctx.stroke();
        ctx.fillStyle = rgba(ICE, 0.95);
        ctx.beginPath();
        ctx.arc(d.x, y, 4.2 * (0.4 + 0.6 * grow), 0, TAU);
        ctx.fill();
      } else {
        // respingo: anel elíptico que se expande na superfície
        const p = seg(t, land, land + 0.42);
        if (p >= 1) continue;
        const sy = riverSurfaceY(d.x, land);
        ctx.strokeStyle = rgba(ICE, 0.7 * (1 - p));
        ctx.lineWidth = 2.5 * (1 - p) + 0.5;
        ctx.beginPath();
        ctx.ellipse(d.x, sy, 6 + 46 * outCubic(p), 3 + 10 * outCubic(p), 0, 0, TAU);
        ctx.stroke();
      }
    }
    ctx.restore();
  }

  // ---------------------------------------------------------------- sol
  function sunState(t) {
    const rise = inOut(seg(t, 4.0, 5.7));
    const conv = inOut(seg(t, 8.0, 9.0));
    let x = lerp(1800, 1610, rise);
    let y = lerp(H + 200, 250, rise);
    x = lerp(x, CX, conv);
    y = lerp(y, CY, conv);
    const s = 1 - conv;
    return { x, y, s, on: t > 4.0 && s > 0.001 };
  }

  function drawSun(ctx, t) {
    const sun = sunState(t);
    if (!sun.on) return;
    const { x, y, s } = sun;
    const r = 88 * s;
    ctx.save();
    const halo = ctx.createRadialGradient(x, y, r * 0.5, x, y, r * 3.4);
    halo.addColorStop(0, rgba(SUN, 0.38));
    halo.addColorStop(1, rgba(SUN, 0));
    ctx.fillStyle = halo;
    ctx.beginPath();
    ctx.arc(x, y, r * 3.4, 0, TAU);
    ctx.fill();

    const rot = t * 0.32;
    ctx.lineCap = 'round';
    ctx.strokeStyle = rgba(SUN, 0.92);
    for (let k = 0; k < 12; k++) {
      const a = rot + (k * TAU) / 12;
      const long = k % 2 === 0;
      const r1 = r * 1.3;
      const r2 = r * (long ? 1.78 : 1.58);
      ctx.lineWidth = (long ? 11 : 8) * s;
      ctx.beginPath();
      ctx.moveTo(x + Math.cos(a) * r1, y + Math.sin(a) * r1);
      ctx.lineTo(x + Math.cos(a) * r2, y + Math.sin(a) * r2);
      ctx.stroke();
    }
    const body = ctx.createRadialGradient(x - r * 0.3, y - r * 0.3, r * 0.1, x, y, r);
    body.addColorStop(0, rgba(mix(SUN, ICE, 0.45)));
    body.addColorStop(1, rgba(SUN));
    ctx.fillStyle = body;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, TAU);
    ctx.fill();
    ctx.restore();
  }

  // ---------------------------------------------------------------- partículas
  const PARTICLES = (() => {
    const r = rng(20261008);
    const arr = [];
    for (let i = 0; i < 90; i++) {
      const d = 0.2 + 0.8 * r();
      arr.push({
        x: r() * W,
        y: r() * H,
        d,
        ph: r() * TAU,
        warm: r() < 0.35,
      });
    }
    return arr;
  })();

  function cameraPan(t) {
    return -70 * Math.sin(Math.PI * seg(t, 4.0, 9.0));
  }

  function drawParticles(ctx, t, front) {
    const env = inOut(seg(t, 4.0, 4.9)) * (1 - inOut(seg(t, 8.5, 9.3)));
    if (env <= 0) return;
    const pan = cameraPan(t);
    ctx.save();
    for (const p of PARTICLES) {
      if ((p.d > 0.7) !== front) continue;
      const span = H + 80;
      let y = (p.y - (18 + 60 * p.d) * (t - 4)) % span;
      if (y < 0) y += span;
      y -= 40;
      let x = p.x + pan * p.d * 2.2 + 14 * Math.sin(t * 0.8 + p.ph);
      x = ((x % (W + 80)) + W + 80) % (W + 80) - 40;
      const tw = 0.55 + 0.45 * Math.sin(t * 3.1 + p.ph * 3);
      const a = env * tw * (0.3 + 0.5 * p.d);
      const rad = 1.2 + 3.2 * p.d;
      const col = p.warm ? SUN : ICE;
      ctx.fillStyle = rgba(col, a * 0.18);
      ctx.beginPath();
      ctx.arc(x, y, rad * 3.2, 0, TAU);
      ctx.fill();
      ctx.fillStyle = rgba(col, a);
      ctx.beginPath();
      ctx.arc(x, y, rad, 0, TAU);
      ctx.fill();
    }
    ctx.restore();
  }

  // ---------------------------------------------------------------- render
  function background(ctx, t) {
    const g = inOut(seg(t, 2.2, 4.0)) * (1 - inOut(seg(t, 8.4, 9.6)));
    const top = mix(PETROL, mix(PETROL, TURQ, 0.62), g);
    const bot = mix(PETROL, mix(PETROL, TURQ, 0.18), g);
    const grad = ctx.createLinearGradient(0, 0, 0, H);
    grad.addColorStop(0, rgba(top));
    grad.addColorStop(1, rgba(bot));
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);
  }

  function cameraScale(t) {
    return (
      1 +
      0.07 * inOut(seg(t, 2.0, 4.0)) -
      0.07 * inOut(seg(t, 4.0, 5.6)) +
      0.13 * inOut(seg(t, 8.6, 10.0))
    );
  }

  function drawRipples(ctx, t) {
    const starts = [0.3, 0.55, 0.8, 1.3, 1.5];
    ctx.save();
    for (const s of starts) {
      const p = seg(t, s, s + 1.25);
      if (p <= 0 || p >= 1) continue;
      const r = lerp(DROP_R * 1.1, 560, outCubic(p));
      ctx.strokeStyle = rgba(mix(TURQ, ICE, 0.25), 0.65 * Math.pow(1 - p, 1.6));
      ctx.lineWidth = lerp(4, 1, p);
      ctx.beginPath();
      ctx.arc(CX, CY, r, 0, TAU);
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawTrails(ctx, t) {
    const env = seg(t, 2.05, 2.45) * (1 - inOut(seg(t, 4.1, 4.9)));
    if (env <= 0) return;
    ctx.save();
    ctx.lineCap = 'round';
    ctx.shadowColor = rgba(mix(TURQ, ICE, 0.5), 0.9);
    ctx.shadowBlur = 14;
    const K = 26;
    const dt = 0.024;
    for (let i = 0; i < 3; i++) {
      let prev = smallPos(i, t);
      for (let k = 1; k <= K; k++) {
        const tk = t - k * dt;
        if (tk < 2.0) break;
        const p = smallPos(i, tk);
        const f = 1 - k / K;
        ctx.strokeStyle = rgba(ICE, 0.8 * f * env);
        ctx.lineWidth = 0.6 + 2.6 * f;
        ctx.beginPath();
        ctx.moveTo(prev[0], prev[1]);
        ctx.lineTo(p[0], p[1]);
        ctx.stroke();
        prev = p;
      }
    }
    ctx.restore();
  }

  // gotas menores / nuvens, incluindo a convergência final
  function drawSmall(ctx, t) {
    if (t < 2.0) return;
    const conv = inOut(seg(t, 8.0, 9.0));
    if (conv >= 1) return;
    const cry = t >= RAIN_START && t < RAIN_START + RAIN_BEATS * BEAT + 0.2;
    for (let i = 0; i < 3; i++) {
      const ci = CLOUD_OF[i];
      const cl = CLOUDS[ci];
      let [x, y] = smallPos(i, t);
      let m = inOut(seg(t, 4.1, 5.2)) * (1 - inOut(seg(t, 8.0, 8.75)));
      const R = lerp(DROP_R, SMALL_R, inOut(seg(t, 2.0, 2.6))) * (1 - conv * 0.6);
      let rot = smallRot(i, t);
      let cs = cl.s * (1 - conv * 0.75);
      // nuvem "chorando": leve compressão a cada batida da chuva
      let squash = 0;
      if (cry) {
        const ph = ((t - RAIN_START) / BEAT) % 1;
        squash = Math.exp(-ph * 7) * 0.05;
      }
      x = lerp(x, CX, conv);
      y = lerp(y, CY, conv);
      ctx.save();
      ctx.translate(x, y);
      ctx.scale(1 + squash, 1 - squash);
      drawBlob(ctx, { x: 0, y: 0, m, R, cloudScale: cs, rot, alpha: 1 - seg(t, 8.6, 9.0) });
      ctx.restore();
    }
  }

  function mainDrop(t) {
    // 0–2 s: surge com escala elástica e pulsa uma vez
    if (t < 2.0) {
      let s = outBack(seg(t, 0, 0.9));
      s *= 1 + 0.12 * Math.sin(Math.PI * seg(t, 1.15, 1.7));
      const y = CY - 7 * Math.sin((Math.PI * t) / 2) * Math.sin(Math.PI * seg(t, 0, 2));
      return { s, y };
    }
    // 8.7–10 s: reforma no centro
    if (t >= 8.65) {
      const s = outBack(seg(t, 8.65, 9.35), 1.5);
      return { s, y: CY };
    }
    return null;
  }

  function drawFinalGlow(ctx, t) {
    const p = seg(t, 9.0, 9.8);
    if (p <= 0) return;
    const k = Math.sin(Math.PI * Math.min(1, p * 1.25)) * 0.6 + 0.4 * outCubic(p);
    const halo = ctx.createRadialGradient(CX, CY, DROP_R * 0.6, CX, CY, DROP_R * 4.2);
    halo.addColorStop(0, rgba(mix(SUN, ICE, 0.4), 0.42 * k));
    halo.addColorStop(0.45, rgba(TURQ, 0.18 * k));
    halo.addColorStop(1, rgba(TURQ, 0));
    ctx.fillStyle = halo;
    ctx.beginPath();
    ctx.arc(CX, CY, DROP_R * 4.2, 0, TAU);
    ctx.fill();
  }

  function drawSparkle(ctx, t) {
    const p = seg(t, 9.15, 9.7);
    if (p <= 0 || p >= 1) return;
    const a = Math.sin(Math.PI * p);
    const x = CX - DROP_R * 0.42;
    const y = CY - DROP_R * 0.62;
    const r = 30 * a;
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(p * 1.2);
    ctx.fillStyle = rgba(ICE, 0.95 * a);
    ctx.beginPath();
    for (let k = 0; k < 8; k++) {
      const ang = (k * TAU) / 8;
      const rr = k % 2 === 0 ? r : r * 0.18;
      ctx.lineTo(Math.cos(ang) * rr, Math.sin(ang) * rr);
    }
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  function drawText(ctx, t) {
    const p = outCubic(seg(t, 9.0, 9.6));
    if (p <= 0) return;
    ctx.save();
    ctx.globalAlpha = p;
    ctx.fillStyle = rgba(ICE);
    ctx.font = '500 64px Poppins, "Montserrat", "Helvetica Neue", Arial, sans-serif';
    if ('letterSpacing' in ctx) ctx.letterSpacing = '3px';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.shadowColor = rgba(PETROL, 0.5);
    ctx.shadowBlur = 18;
    ctx.fillText('Todo ciclo recomeça', CX, 828 + 34 * (1 - p));
    ctx.restore();
  }

  function render(ctx, t) {
    t = ((t % DURATION) + DURATION) % DURATION;
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    background(ctx, t);
    drawParticles(ctx, t, false);

    // câmera (push-in / zoom / pan suave)
    const cs = cameraScale(t);
    ctx.save();
    ctx.translate(CX, CY);
    ctx.scale(cs, cs);
    ctx.translate(-CX + cameraPan(t), -CY);

    drawRipples(ctx, t);
    drawSun(ctx, t);
    drawRiver(ctx, t, 1);
    drawTrails(ctx, t);
    drawRain(ctx, t);
    drawSmall(ctx, t);
    drawRiver(ctx, t, 0);
    drawFinalGlow(ctx, t);
    const md = mainDrop(t);
    if (md && md.s > 0.001) {
      drawBlob(ctx, { x: CX, y: md.y, R: DROP_R * md.s, glow: 1 + seg(t, 9.0, 9.5) * 0.8 });
    }
    drawSparkle(ctx, t);
    ctx.restore();

    drawParticles(ctx, t, true);
    drawText(ctx, t);

    // fade out nos últimos 6 quadros: o último quadro casa com o primeiro
    const frame = Math.round(t * FPS);
    const fo = clamp01((frame - (TOTAL_FRAMES - 7)) / 6);
    if (fo > 0) {
      ctx.fillStyle = rgba(PETROL, fo);
      ctx.fillRect(0, 0, W, H);
    }
    ctx.restore();
  }

  global.GOTA = { W, H, FPS, DURATION, TOTAL_FRAMES, render };
})(typeof window !== 'undefined' ? window : globalThis);
