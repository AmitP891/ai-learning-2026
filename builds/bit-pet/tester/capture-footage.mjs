import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, mkdtempSync } from 'node:fs';
const FILE='file:///home/claude/ai-learning-2026/builds/bit-pet/opus/index.html';
const PORT=9555;
const prof=mkdtempSync('/tmp/bpprof-');
const chrome=spawn('google-chrome',['--headless=new',`--remote-debugging-port=${PORT}`,`--user-data-dir=${prof}`,'--no-first-run','--disable-background-networking','--disable-component-update','--disable-sync','--no-sandbox','--autoplay-policy=no-user-gesture-required','--allow-file-access-from-files','about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let ws,id=0;const pend=new Map();const errs=[];
for(let i=0;i<60;i++){try{const l=await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();const p=l.find(t=>t.type==='page');if(p){ws=new WebSocket(p.webSocketDebuggerUrl);break;}}catch{} await sleep(200);}
await new Promise(r=>ws.onopen=r);
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pend.has(m.id)){pend.get(m.id)(m);pend.delete(m.id);} if(m.method==='Runtime.exceptionThrown')errs.push(JSON.stringify(m.params.exceptionDetails.exception?.description));};
const send=(method,params={})=>new Promise(r=>{const i=++id;pend.set(i,r);ws.send(JSON.stringify({id:i,method,params}));});
const ev=async x=>(await send('Runtime.evaluate',{expression:x,awaitPromise:true,returnByValue:true})).result?.result?.value;
await send('Runtime.enable');await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride',{width:1152,height:1600,deviceScaleFactor:1,mobile:false});
await send('Page.addScriptToEvaluateOnNewDocument',{source:"(()=>{const n=Date.now.bind(Date);window.__off=0;Date.now=()=>n()+window.__off;document.addEventListener('DOMContentLoaded',()=>{document.documentElement.style.zoom=1.6;});})()"});
const load=async()=>{await send('Page.navigate',{url:FILE});await sleep(1200);};
async function setSave(o){await ev(`localStorage.setItem('bitpet.save.v1',${JSON.stringify(JSON.stringify(o))})`);}
let castDir=null,castN=0,castT=[];
ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.method==='Page.screencastFrame'){send('Page.screencastFrameAck',{sessionId:m.params.sessionId});if(castDir){writeFileSync(`${castDir}/${String(castN).padStart(4,'0')}.jpg`,Buffer.from(m.params.data,'base64'));castT.push(m.params.metadata.timestamp);castN++;}}});
async function rec(name,sec,during){
  const dir=`frames/${name}`;mkdirSync(dir,{recursive:true});
  castDir=dir;castN=0;castT=[];
  await send('Page.startScreencast',{format:'jpeg',quality:90,everyNthFrame:1,maxWidth:1152,maxHeight:1600});
  const job=during?during():null;
  await sleep(sec*1000); if(job)await job;
  await send('Page.stopScreencast');castDir=null;
  writeFileSync(`${dir}/times.json`,JSON.stringify(castT));
  console.log(name,castN,'frames',(castN/(castT.at(-1)-castT[0])).toFixed(1),'fps');
}
async function click(x,y){for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x,y,button:'left',clickCount:1});}
async function clickSel(sel){const r=await ev(`(()=>{const b=document.querySelector(${JSON.stringify(sel)}).getBoundingClientRect();return [b.x+b.width/2,b.y+b.height/2]})()`);await click(r[0],r[1]);}
const now=Date.now();
const st=(b,f,s,c,extra={})=>Object.assign({v:1,battery:b,fun:f,sleep:s,clean:c,asleep:false,lowPower:false,t:Date.now(),born:now-86400000*2},extra);
// A: happy idle
await load();await setSave(st(100,100,90,90));await load();await ev("document.getElementById('bannerOk')?.click()");
await rec('A_happy',5);
// B: feed cookie
await setSave(st(40,60,90,90));await load();await ev("document.getElementById('bannerOk')?.click()");
await rec('B_feed',7,async()=>{await sleep(600);await clickSel('#bFeed');await sleep(900);await clickSel('[data-snack=cookie]');await sleep(2600);await clickSel('#bFeed');await sleep(800);await clickSel('[data-snack=byte]');});
// C: play game
await setSave(st(90,30,90,90));await load();await ev("document.getElementById('bannerOk')?.click()");
await rec('C_play',12,async()=>{await sleep(500);await clickSel('#bPlay');const end=Date.now()+10500;while(Date.now()<end){await sleep(650);const t=await ev("(()=>{const h=window.__bitpet;const ts=h.targets();if(!ts.length)return null;const p=h.toClient(ts[0].x,ts[0].y);return [p.x,p.y]})()");if(t)await click(t[0],t[1]);}});
// D: bugs crawling then debug
await setSave(st(80,80,80,12));await load();await ev("document.getElementById('bannerOk')?.click()");
await sleep(4000);
await rec('D_bugs',9,async()=>{await sleep(4000);await clickSel('#bDebug');const end=Date.now()+4500;while(Date.now()<end){await sleep(250);const t=await ev("(()=>{const h=window.__bitpet;const bs=h.bugs();if(!bs.length)return null;const p=h.toClient(bs[0].x,bs[0].y);return [p.x,p.y]})()");if(t)await click(t[0],t[1]);}});
// E: sleep
await setSave(st(90,90,30,90));await load();await ev("document.getElementById('bannerOk')?.click()");
await rec('E_sleep',6,async()=>{await sleep(700);await clickSel('#bSleep');});
// F: welcome-back banner on load after 24h, from 1h-check bars
await setSave(st(100,100,74,64,{t:Date.now()-24*3600000}));
await load();
await rec('F_banner_load',6);
// G: open tab wakes after computer sleep (the fixed case)
await setSave(st(100,100,74,64));await load();await ev("document.getElementById('bannerOk')?.click()");
await rec('G_banner_wake',7,async()=>{await sleep(1500);await ev("window.__off=24*3600000");});
console.log('errors',errs);
chrome.kill();process.exit(0);
