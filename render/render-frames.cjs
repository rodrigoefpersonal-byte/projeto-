#!/usr/bin/env node
// Renderiza os 240 quadros da animação como PNG usando Chromium headless.
// Uso: node render/render-frames.cjs [pasta-de-saida] [--only=0,60,120]
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.resolve(process.argv[2] && !process.argv[2].startsWith('--') ? process.argv[2] : path.join(ROOT, 'frames'));
const onlyArg = process.argv.find((a) => a.startsWith('--only='));
const ONLY = onlyArg ? onlyArg.slice(7).split(',').map(Number) : null;

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2' };

function serve() {
  const server = http.createServer((req, res) => {
    const p = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
    if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) {
      res.writeHead(404);
      return res.end();
    }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
    fs.createReadStream(p).pipe(res);
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const server = await serve();
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(`http://127.0.0.1:${server.address().port}/index.html?capture`);
  await page.evaluate(() => window.fontsReady);
  const total = await page.evaluate(() => window.GOTA.TOTAL_FRAMES);
  const frames = ONLY || [...Array(total).keys()];
  for (const f of frames) {
    const dataUrl = await page.evaluate((i) => {
      window.renderFrame(i);
      return document.getElementById('c').toDataURL('image/png');
    }, f);
    const file = path.join(OUT, `frame_${String(f).padStart(4, '0')}.png`);
    fs.writeFileSync(file, Buffer.from(dataUrl.split(',')[1], 'base64'));
    if (f % 24 === 0) process.stdout.write(`quadro ${f}/${total}\n`);
  }
  await browser.close();
  server.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
