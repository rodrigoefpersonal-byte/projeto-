// Renders a scene.html into frames piped to ffmpeg (or stills for review).
// Usage:
//   node render.js p1 stills 0.5,3,8          -> build/p1-still-<t>.jpg
//   node render.js p1 video [start] [end]      -> build/p1-silent.mp4
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const ROOT = __dirname;
const [part, mode, a1, a2] = process.argv.slice(2);
const FPS = 30;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2', '.json': 'application/json' };

const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', m => { if (m.type() === 'error') console.error('[page]', m.text()); });
  page.on('pageerror', e => console.error('[pageerror]', e.message));
  await page.goto(`http://127.0.0.1:${port}/${part}/scene.html`);
  await page.waitForFunction(() => window.ready === true, null, { timeout: 60000 });
  const words = JSON.parse(fs.readFileSync(path.join(ROOT, part, 'words.json'), 'utf8')).words;
  const meta = JSON.parse(fs.readFileSync(path.join(ROOT, part, 'meta.json'), 'utf8'));
  await page.evaluate(w => window.setup(w), words);
  fs.mkdirSync(path.join(ROOT, 'build'), { recursive: true });

  if (mode === 'stills') {
    for (const t of a1.split(',').map(Number)) {
      const url = await page.evaluate(t => window.renderFrame(t), t);
      fs.writeFileSync(path.join(ROOT, 'build', `${part}-still-${t.toFixed(2)}.jpg`), Buffer.from(url.split(',')[1], 'base64'));
    }
  } else {
    const start = Number(a1 ?? 0), end = Number(a2 ?? meta.duration);
    const outFile = path.join(ROOT, 'build', `${part}-silent.mp4`);
    const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', outFile], { stdio: ['pipe', 'inherit', 'inherit'] });
    const n = Math.round((end - start) * FPS); const t0 = Date.now();
    for (let i = 0; i < n; i++) {
      const t = start + i / FPS;
      const url = await page.evaluate(t => window.renderFrame(t), t);
      const buf = Buffer.from(url.split(',')[1], 'base64');
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 150 === 0) console.log(`frame ${i}/${n} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    console.log('done', outFile);
  }
  await browser.close(); server.close();
})().catch(e => { console.error(e); process.exit(1); });
