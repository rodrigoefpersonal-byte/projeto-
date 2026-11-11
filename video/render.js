const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const HTML = process.env.HTML || 'cena.html', OUT = process.env.OUT || 'frames';
const only = process.argv[2] ? process.argv[2].split(',').map(Number) : null;
(async () => {
  const logo = fs.readFileSync(path.join(__dirname, '..', 'perfil', 'logo.png')).toString('base64');
  const html = fs.readFileSync(path.join(__dirname, HTML), 'utf8').replace('__LOGO__', 'data:image/png;base64,' + logo);
  const out = path.join(__dirname, OUT); fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.setContent(html, { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  const total = await p.evaluate(() => window.TOTAL);
  const list = only || [...Array(total).keys()];
  for (const f of list) {
    await p.evaluate(f => window.render(f), f);
    await p.screenshot({ path: path.join(out, String(f).padStart(4, '0') + '.png') });
  }
  await b.close();
  console.log('frames:', list.length);
})();
