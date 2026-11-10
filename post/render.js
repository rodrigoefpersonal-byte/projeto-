const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
  const svg = fs.readFileSync(path.join(__dirname, 'post1.svg'), 'utf8');
  await p.setContent(`<html><body style="margin:0">${svg}</body></html>`);
  await p.screenshot({ path: path.join(__dirname, 'post1.png'), clip: { x: 0, y: 0, width: 1080, height: 1350 } });
  await b.close();
})();
