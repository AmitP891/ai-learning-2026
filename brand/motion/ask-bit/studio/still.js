// Render one still of the studio: node still.js out.png [shot] [w h]
const { chromium } = require('playwright'); const path = require('path'); const http = require('http'); const fs = require('fs');
const ROOT = path.resolve(__dirname, '../../../..');
const NM = process.env.THREE_DIR;          // optional local three@0.160.1 (offline); otherwise CDN
(async () => {
  const [out, shot = 'wide', w = 1080, h = 1920] = process.argv.slice(2);
  const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'application/javascript' : 'application/octet-stream' }); r.end(d); }); }).listen(0);
  const port = srv.address().port;
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: +w, height: +h } });
  p.on('pageerror', e => console.log('ERR', e.message)); p.on('console', m => { if (m.type() === 'error') console.log('console', m.text()); });
  if (NM) await p.route('https://cdn.jsdelivr.net/npm/three@0.160.1/**', r => { const rel = r.request().url().split('three@0.160.1/')[1]; r.fulfill({ path: path.join(NM, rel), contentType: 'application/javascript' }); });
  await p.goto(`http://localhost:${port}/brand/motion/ask-bit/studio/index.html?w=${w}&h=${h}`);
  await p.waitForFunction('window.READY === true', null, { timeout: 120000 });
  await p.evaluate(s => window.setState({ t: 1.3, shot: [s], bitLevel: 0, glLevel: 0 }), shot);
  await p.screenshot({ path: out }); await b.close(); srv.close(); console.log(out);
})();
