import { spawn } from 'node:child_process'; import { mkdtempSync } from 'node:fs'; import { join } from 'node:path';
const PORT=9799, OUT=process.argv[3]; const prof=mkdtempSync(join(OUT,'p-'));
const ch=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new',`--remote-debugging-port=${PORT}`,`--user-data-dir=${prof}`,'about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms)); let ws,id=0; const P=new Map();
for(let i=0;i<50;i++){try{const l=await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();const p=l.find(t=>t.type==='page');if(p){ws=new WebSocket(p.webSocketDebuggerUrl);break;}}catch{} await sleep(200);}
await new Promise(r=>ws.onopen=r); ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&P.has(m.id)){P.get(m.id)(m);P.delete(m.id);}};
const send=(method,params={})=>new Promise(r=>{const i=++id;P.set(i,r);ws.send(JSON.stringify({id:i,method,params}));});
const ev=async e=>(await send('Runtime.evaluate',{expression:e,returnByValue:true})).result.result.value;
await send('Emulation.setDeviceMetricsOverride',{width:375,height:740,deviceScaleFactor:2,mobile:true});
await send('Emulation.setTouchEmulationEnabled',{enabled:true});
await send('Page.navigate',{url:'file://'+process.argv[2]}); await sleep(1500);
await ev(`window.__log=[];document.addEventListener('pointerdown',e=>__log.push(e.pointerType+' '+e.target.id),true)`);
const tp=await ev('__bitpet.toClient(150,200)'); console.log(tp, await ev(`document.elementFromPoint(${tp.x},${tp.y}).id`));
const f0=(await ev('__bitpet.state()')).fun;
await send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:tp.x,y:tp.y}]});
await send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]}); await sleep(300);
console.log(await ev('__log'), f0, (await ev('__bitpet.state()')).fun);
ch.kill(); process.exit(0);
