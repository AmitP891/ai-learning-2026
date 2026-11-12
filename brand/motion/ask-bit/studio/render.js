// Render a timeline of studio states to video frames.
// node render.js states.json out_video_noaudio.mp4 [w h]
const { chromium } = require('playwright'); const path = require('path'); const http = require('http'); const fs = require('fs'); const { spawn } = require('child_process');
const ROOT = path.resolve(__dirname, '../../../..'); const NM = process.env.THREE_DIR;
(async () => {
  const [statesFile, out, w = 1080, h = 1920] = process.argv.slice(2);
  const states = JSON.parse(fs.readFileSync(statesFile, 'utf8'));
  const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); r.end(d); }); }).listen(0);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: +w, height: +h } });
  p.on('pageerror', e => console.log('ERR', e.message));
  if (NM) await p.route('https://cdn.jsdelivr.net/npm/three@0.160.1/**', r => { const rel = r.request().url().split('three@0.160.1/')[1]; r.fulfill({ path: path.join(NM, rel), contentType: 'application/javascript' }); });
  await p.goto(`http://localhost:${srv.address().port}/brand/motion/ask-bit/studio/index.html?w=${w}&h=${h}${process.env.QS ? '&' + process.env.QS : ''}`);
  await p.waitForFunction('window.READY === true', null, { timeout: 120000 });
  await p.evaluate(() => document.fonts.ready);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', '30', '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = 0; i < states.length; i++) {
    await p.evaluate(s => window.setState(s), states[i]);
    const buf = await p.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 30 === 0) console.log(`frame ${i}/${states.length} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close(); srv.close(); console.log(out);
})();
