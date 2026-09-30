// Bounded read-only capture. Not a historical dataset, executor or trading service.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const root=fileURLToPath(new URL('../',import.meta.url));
const url='wss://stream.binance.com:9443/ws/btcusdt@depth@100ms';
const snapshotUrl='https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=1000';
const cache=path.join(root,'research/cache/validation');
fs.mkdirSync(cache,{recursive:true});
if(fs.existsSync(path.join(cache,'STOP')))throw Error('STOP marker present');
const ledger=path.join(cache,'controller-state.json');
if(fs.existsSync(ledger)&&JSON.parse(fs.readFileSync(ledger,'utf8')).active)throw Error('Development attempt active; do not overlap compute');
const lock=path.join(cache,'depth-pilot.lock');
const fd=fs.openSync(lock,'wx');
const capture={startedAt:new Date().toISOString(),symbol:'BTCUSDT',url,snapshotUrl,events:[],snapshot:null,validated:false,ordersSent:0};
let bytes=0,ws,timer,captureTimer;
const abort=new AbortController();
try {
 await new Promise((resolve,reject)=>{
  timer=setTimeout(()=>{abort.abort();reject(Error('Capture deadline exceeded'));},25000);
  ws=new WebSocket(url);
  ws.addEventListener('error',()=>reject(Error('Public WebSocket connection failed')));
  ws.addEventListener('message',event=>{
   const raw=String(event.data);bytes+=Buffer.byteLength(raw);
   if(bytes>1_800_000){reject(Error('Capture byte limit exceeded'));return;}
   try{capture.events.push({receivedAt:new Date().toISOString(),payload:JSON.parse(raw)});}catch{reject(Error('Invalid public payload'));}
  });
  ws.addEventListener('open',async()=>{
   try {
    const res=await fetch(snapshotUrl,{signal:AbortSignal.any([abort.signal,AbortSignal.timeout(10000)])});
    if(!res.ok)throw Error(`Snapshot HTTP ${res.status}`);
    const raw=await res.text();bytes+=Buffer.byteLength(raw);
    if(bytes>1_800_000)throw Error('Snapshot byte limit exceeded');
    capture.snapshot={receivedAt:new Date().toISOString(),payload:JSON.parse(raw)};
    captureTimer=setTimeout(resolve,10000);
   }catch(e){reject(e);}
  });
 });
 const snap=capture.snapshot.payload;
 if(!Number.isSafeInteger(snap.lastUpdateId)||!Array.isArray(snap.bids)||!Array.isArray(snap.asks))throw Error('Snapshot schema invalid');
 let last=snap.lastUpdateId,applied=0;
 for(const {payload:e} of capture.events){
  if(e.e!=='depthUpdate'||e.s!=='BTCUSDT'||!Number.isSafeInteger(e.U)||!Number.isSafeInteger(e.u))throw Error('Diff schema invalid');
  if(e.u<=last)continue;
  if(e.U>last+1||e.u<last+1)throw Error('Sequence gap; discard pilot for feature generation');
  last=e.u;applied++;
 }
 capture.sequenceChecked=applied>0;
 capture.appliedEvents=applied;
 capture.limitation='Pilot only: no reconstructed features, fills, costs, signals, continuous coverage or performance.';
}catch(e){capture.sequenceChecked=false;capture.failure=String(e.message||e);}
finally{
 abort.abort();clearTimeout(timer);clearTimeout(captureTimer);ws?.close();capture.endedAt=new Date().toISOString();
 const body=JSON.stringify(capture)+'\n';
 const out=path.join(cache,`depth-pilot-${Date.now()}.json`);
 fs.writeFileSync(out,body,{flag:'wx'});
 fs.closeSync(fd);fs.unlinkSync(lock);
 console.log(JSON.stringify({path:out,sha256:createHash('sha256').update(body).digest('hex'),events:capture.events.length,sequenceChecked:capture.sequenceChecked,failure:capture.failure??null,validated:false}));
}
