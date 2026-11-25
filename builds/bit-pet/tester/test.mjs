// Tester bot: drives index.html in headless Chrome via CDP.
import { spawn } from 'node:child_process';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const FILE = process.argv[2];
const OUT = process.argv[3];
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PORT = 9400 + Math.floor(Math.random() * 300);
const prof = mkdtempSync(join(OUT, 'prof-'));
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${prof}`,
  '--no-first-run', '--autoplay-policy=no-user-gesture-required', '--window-size=420,900', 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));

let ws, id = 0; const pending = new Map(); const problems = []; const results = [];
async function connect() {
  for (let i = 0; i < 50; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
      const page = list.find(t => t.type === 'page');
      if (page) { ws = new WebSocket(page.webSocketDebuggerUrl); break; }
    } catch {}
    await sleep(200);
  }
  await new Promise(r => ws.onopen = r);
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
    if (m.method === 'Runtime.exceptionThrown') problems.push('EXCEPTION: ' + JSON.stringify(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text));
    if (m.method === 'Runtime.consoleAPICalled' && ['error', 'warning', 'assert'].includes(m.params.type)) problems.push('CONSOLE ' + m.params.type + ': ' + m.params.args.map(a => a.value ?? a.description).join(' '));
    if (m.method === 'Log.entryAdded' && ['error', 'warning'].includes(m.params.entry.level)) problems.push('LOG ' + m.params.entry.level + ': ' + m.params.entry.text);
  };
}
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
async function ev(expr) {
  const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.result?.exceptionDetails) throw new Error('eval failed: ' + expr + ' -> ' + r.result.exceptionDetails.exception?.description);
  return r.result?.result?.value;
}
async function tap(x, y) { // stage coords
  const p = await ev(`__bitpet.toClient(${x},${y})`);
  for (const type of ['mousePressed', 'mouseReleased']) await send('Input.dispatchMouseEvent', { type, x: p.x, y: p.y, button: 'left', clickCount: 1 });
}
async function clickEl(sel) {
  const p = await ev(`(()=>{const r=document.querySelector('${sel}').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
  for (const type of ['mousePressed', 'mouseReleased']) await send('Input.dispatchMouseEvent', { type, x: p.x, y: p.y, button: 'left', clickCount: 1 });
}
function check(name, ok, detail = '') { results.push({ name, ok: !!ok, detail }); }
async function setSave(obj) { await ev(`localStorage.setItem('bitpet.save.v1', JSON.stringify(Object.assign(JSON.parse(localStorage.getItem('bitpet.save.v1')), ${JSON.stringify(obj)}, {t: Date.now() - ${obj.ago || 0}})))`); }
async function reload() { await send('Page.reload'); await sleep(1200); }
const st = () => ev('__bitpet.state()');

await connect();
await send('Runtime.enable'); await send('Log.enable'); await send('Page.enable');
await send('Page.navigate', { url: 'file://' + FILE }); await sleep(1500);

// 1. fresh load
check('Fresh load shows welcome banner', await ev(`!document.getElementById('banner').hidden && document.getElementById('bannerTitle').textContent`) === 'Meet Bit!');
let s = await st();
check('Fresh needs are 80', ['battery', 'fun', 'sleep', 'clean'].every(k => Math.round(s[k]) === 80), JSON.stringify(s));
check('Fresh mood is happy', await ev('__bitpet.mood()') === 'happy');

// 2. FEED each snack (live external save edit, no reload)
for (const [snack, gain] of [['byte', 15], ['cookie', 25], ['usb', 45]]) {
  await setSave({ battery: 20, lowPower: false, asleep: false }); await sleep(1300);
  const before = (await st()).battery;
  await clickEl('#bFeed'); await sleep(150);
  const open = await ev(`document.getElementById('snacks').classList.contains('open')`);
  await clickEl(`.snack[data-snack=${snack}]`); await sleep(1600);
  const after = (await st()).battery;
  check(`FEED ${snack}: menu opens and battery +${gain}`, open && Math.abs(after - before - gain) < 0.5, `before ${before.toFixed(1)} after ${after.toFixed(1)}`);
}
await setSave({ battery: 99 }); await sleep(1300);
await clickEl('#bFeed'); await sleep(100); await clickEl('.snack[data-snack=byte]'); await sleep(300);
check('FEED when full is refused', /full/i.test(await ev('__bitpet.speech()')), await ev('__bitpet.speech()'));

// 3. PLAY
await setSave({ battery: 80, fun: 20, sleep: 80, clean: 80 }); await sleep(1300);
const fun0 = (await st()).fun;
await clickEl('#bPlay'); await sleep(200);
check('PLAY starts mini-game', await ev('__bitpet.mode()') === 'play');
check('Other buttons disabled during PLAY', await ev(`['bFeed','bSleep','bDebug'].every(i=>document.getElementById(i).disabled)`));
let caught = 0; const t0 = Date.now();
while (Date.now() - t0 < 9000) {
  const tg = await ev('__bitpet.targets()');
  if (tg.length) { await tap(tg[0].x, tg[0].y); caught++; }
  await sleep(250);
}
await sleep(2000);
s = await st();
check('PLAY ends after ~10s', await ev('__bitpet.mode()') === 'idle');
check('PLAY raises fun', s.fun > fun0 + 14, `fun ${fun0.toFixed(1)} -> ${s.fun.toFixed(1)}, taps ${caught}, msg "${await ev('__bitpet.speech()')}"`);

// 4. SLEEP
await setSave({ sleep: 95, fun: 80 }); await sleep(1300);
await clickEl('#bSleep'); await sleep(200);
check('SLEEP refused when not sleepy', !(await st()).asleep);
await setSave({ sleep: 40 }); await sleep(1300);
await clickEl('#bSleep'); await sleep(3500);
s = await st();
check('SLEEP puts Bit to sleep, button says WAKE', s.asleep && await ev(`document.getElementById('bSleep').textContent`) === 'WAKE');
check('Asleep mood + Feed/Play/Debug disabled', await ev('__bitpet.mood()') === 'asleep' && await ev(`['bFeed','bPlay','bDebug'].every(i=>document.getElementById(i).disabled)`));
check('Sleep need rises while asleep', s.sleep > 40, s.sleep.toFixed(3));
await clickEl('#bSleep'); await sleep(200);
check('WAKE wakes Bit', !(await st()).asleep);
// catch-up while asleep: 1 hour asleep from sleep 40 -> should wake when sleep hits 100 (30 min)
await setSave({ sleep: 40, asleep: true, battery: 80, fun: 80, clean: 80, ago: 3600e3 }); await sleep(1500);
s = await st();
check('Catch-up: asleep 1h auto-wakes at full sleep', !s.asleep && s.sleep > 90, JSON.stringify(s));

// 5. DEBUG
await setSave({ clean: 10, battery: 80, fun: 80, sleep: 80, asleep: false }); await reload();
const nb = (await ev('__bitpet.bugs()')).length;
check('Purple glitch bugs appear when Clean low', nb >= 3, `bugs ${nb}`);
check('Mood buggy at low clean', await ev('__bitpet.mood()') === 'buggy');
await clickEl('#bDebug'); await sleep(200);
check('DEBUG enters debug mode', await ev('__bitpet.mode()') === 'debug');
for (let i = 0; i < 10; i++) { const b = await ev('__bitpet.bugs()'); if (!b.length) break; await tap(b[0].x, b[0].y); await sleep(120); }
s = await st();
check('Zapping all bugs -> Clean 100, back to idle', Math.round(s.clean) === 100 && await ev('__bitpet.mode()') === 'idle', `clean ${s.clean}`);
await sleep(2000);
check('No bugs after debug', (await ev('__bitpet.bugs()')).length === 0);
await clickEl('#bDebug'); await sleep(200);
const nb2 = (await ev('__bitpet.bugs()')).length;
for (let i = 0; i < 6; i++) { const b = await ev('__bitpet.bugs()'); if (!b.length) break; await tap(b[0].x, b[0].y); await sleep(120); }
check('DEBUG with no bugs: scan finds stray bits, zappable', nb2 === 2 && await ev('__bitpet.mode()') === 'idle');

// 6. moods
for (const [vals, mood] of [[{ battery: 10 }, 'hungry'], [{ fun: 10 }, 'bored'], [{ sleep: 10 }, 'sleepy'], [{ battery: 10, fun: 10, sleep: 10, clean: 10 }, 'sad']]) {
  await setSave(Object.assign({ battery: 80, fun: 80, sleep: 80, clean: 80 }, vals)); await sleep(1400);
  const m = await ev('__bitpet.mood()');
  check(`Mood ${mood}`, m === mood, `got ${m}, says "${await ev('__bitpet.speech()')}"`);
}

// 7. 24h catch-up via reload
await setSave({ battery: 80, fun: 80, sleep: 80, clean: 80, asleep: false, lowPower: false, ago: 24 * 3600e3 });
await reload();
s = await st();
const bt = await ev(`document.getElementById('bannerTitle').textContent + ' | ' + document.getElementById('bannerText').textContent`);
check('24h gap: "You were gone" banner', /You were gone 1 day/.test(bt) && !(await ev(`document.getElementById('banner').hidden`)), bt);
check('24h gap: all needs 0 -> low power mode', s.lowPower && ['battery', 'fun', 'sleep', 'clean'].every(k => s[k] === 0), JSON.stringify(s));
check('Low power: only FEED enabled', await ev(`!bFeed.disabled && bPlay.disabled && bSleep.disabled && bDebug.disabled`));
await clickEl('#bFeed'); await sleep(100); await clickEl('.snack[data-snack=usb]'); await sleep(1600);
s = await st();
check('Feeding wakes Bit from low power', !s.lowPower && s.battery > 40, JSON.stringify(s));

// 7b. 7-hour gap -> message wording
await setSave({ battery: 90, fun: 90, sleep: 90, clean: 90, lowPower: false, ago: 7 * 3600e3 + 5000 }); await reload();
check('7h gap wording', /You were gone 7 hours/.test(await ev(`bannerTitle.textContent`)), await ev(`bannerTitle.textContent`));

// 8. persistence over reload, corrupt save
await setSave({ battery: 55.5, fun: 44, ago: 0 }); await reload();
s = await st();
check('State persists across reload', Math.abs(s.battery - 55.5) < 0.2 && Math.abs(s.fun - 44) < 0.2, JSON.stringify(s));
await ev(`localStorage.setItem('bitpet.save.v1','{not json')`); await reload();
check('Corrupt save recovers to fresh pet', Math.round((await st()).battery) === 80);

// 9. live decay sanity: 1 minute fake gap without reload
await setSave({ battery: 50, fun: 50, sleep: 50, clean: 50, ago: 3600e3 }); await sleep(1500);
s = await st();
check('1h awake decay: battery fastest', Math.abs(s.battery - 40) < 0.3 && Math.abs(s.fun - 43) < 0.3 && Math.abs(s.sleep - 45) < 0.3 && Math.abs(s.clean - 46) < 0.3, JSON.stringify(s));

// 10. mobile layout
await send('Emulation.setDeviceMetricsOverride', { width: 375, height: 740, deviceScaleFactor: 2, mobile: true });
await send('Emulation.setTouchEmulationEnabled', { enabled: true });
await reload();
const lay = await ev(`({sw:document.documentElement.scrollWidth, iw:innerWidth, sh:document.documentElement.scrollHeight, ih:innerHeight, btnBottom: bDebug.getBoundingClientRect().bottom})`);
check('Mobile: no horizontal scroll', lay.sw <= lay.iw, JSON.stringify(lay));
check('Mobile: action buttons visible without scrolling', lay.btnBottom <= lay.ih, JSON.stringify(lay));
await setSave({ battery: 25, fun: 70, clean: 30, ago: 0 }); await sleep(2500);
const shot = await send('Page.captureScreenshot', { format: 'png' });
writeFileSync(join(OUT, 'mobile.png'), Buffer.from(shot.result.data, 'base64'));
// touch tap through to pet
await setSave({ clean: 90, fun: 60, ago: 0 }); await sleep(2500);
const fb = (await st()).fun;
const tp = await ev('__bitpet.toClient(150,200)');
await send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: tp.x, y: tp.y }] });
await send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
await sleep(300);
check('Mobile: touch on Bit pets him (+fun)', (await st()).fun > fb + 1);

// sleeping screenshot
await setSave({ sleep: 30, asleep: true, ago: 0 }); await sleep(4000);
writeFileSync(join(OUT, 'asleep.png'), Buffer.from((await send('Page.captureScreenshot', { format: 'png' })).result.data, 'base64'));
await setSave({ battery: 0, fun: 0, sleep: 0, clean: 0, asleep: false, lowPower: true, ago: 0 }); await sleep(1500);
writeFileSync(join(OUT, 'lowpower.png'), Buffer.from((await send('Page.captureScreenshot', { format: 'png' })).result.data, 'base64'));

check('No console errors/warnings/exceptions', problems.length === 0, problems.join(' || '));
for (const r of results) console.log((r.ok ? 'PASS' : 'FAIL') + '  ' + r.name + (r.ok && !process.env.V ? '' : '   [' + r.detail + ']'));
console.log(`\n${results.filter(r => r.ok).length}/${results.length} passed`);
chrome.kill(); process.exit(0);
