// Render Bit lab looks: node shoot.js outdir "mat=std&expr=normal" "mat=gloss&expr=happy" ...
const { chromium } = require('playwright'); const path = require('path'); const http = require('http'); const fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..'); const NM = process.env.THREE_DIR;
(async () => {
  const [outdir, ...looks] = process.argv.slice(2); fs.mkdirSync(outdir, { recursive: true });
  const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'application/javascript' : 'application/octet-stream' }); r.end(d); }); }).listen(0);
  const port = srv.address().port;
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  for (const look of looks) {
    const p = await b.newPage({ viewport: { width: 900, height: 1100 } });
    p.on('pageerror', e => console.log('ERR', e.message));
    if (NM) await p.route('https://cdn.jsdelivr.net/npm/three@0.160.1/**', r => { const rel = r.request().url().split('three@0.160.1/')[1]; r.fulfill({ path: path.join(NM, rel), contentType: 'application/javascript' }); });
    await p.goto(`http://localhost:${port}/brand/bit/lab/index.html?${look}`);
    await p.waitForFunction('window.READY === true', null, { timeout: 180000 });
    const out = path.join(outdir, look.replace(/[=&]/g, '_') + '.png'); await p.screenshot({ path: out }); console.log(out); await p.close();
  }
  await b.close(); srv.close();
})();
