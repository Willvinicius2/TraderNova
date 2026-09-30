// Continuous read-only Binance L2 depth capture. No features, signals, orders, PnL or approvals.
import fs from 'node:fs';
import path from 'node:path';
import {gzipSync} from 'node:zlib';
import {createHash, randomUUID} from 'node:crypto';
import {pathToFileURL} from 'node:url';

export const LIMITS=Object.freeze({rawCacheBytes:256*1024*1024, chunkBytes:1024*1024, flushMs:60_000, maxEventBytes:512*1024, maxSnapshotBytes:512*1024, maxBufferBytes:2*1024*1024, stopPollMs:5_000, statusMs:30_000, minBackoffMs:2_000, maxBackoffMs:60_000, maxFailures:3});
export const STREAM_URL='wss://stream.binance.com:9443/ws/btcusdt@depth@100ms';
export const SNAPSHOT_URL='https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=1000';
export function sequenceStep(event,lastU){
 if(!Number.isSafeInteger(event?.U)||!Number.isSafeInteger(event?.u)||event.U<0||event.u<event.U) return {kind:'invalid'};
 if(event.u<=lastU) return {kind:'duplicate'};
 if(event.U>lastU+1) return {kind:'gap'};
 return {kind:'apply',lastU:event.u};
}
export function cacheCanAppend(existingBytes,appendBytes){return Number.isSafeInteger(existingBytes)&&Number.isSafeInteger(appendBytes)&&existingBytes>=0&&appendBytes>=0&&existingBytes+appendBytes<=LIMITS.rawCacheBytes;}
export function isChunkFull(bufferBytes,elapsedMs){return bufferBytes>=LIMITS.chunkBytes||elapsedMs>=LIMITS.flushMs;}
export function queueDiff(payload,receivedAt){return {payload,receivedAt};}
export function encodedEvent(payload,receivedAt=new Date().toISOString()){
 if(payload?.e!=='depthUpdate'||payload?.s!=='BTCUSDT')throw Error('Unexpected depth payload');
 const step=sequenceStep(payload,0); if(step.kind==='invalid')throw Error('Invalid U/u sequence fields');
 const exchangeTime=Number.isSafeInteger(payload.E)?payload.E:null;
 return {received_at:receivedAt,sequence:{U:payload.U,u:payload.u,pu:Number.isSafeInteger(payload.pu)?payload.pu:null},clock_age_ms:exchangeTime===null?null:Date.parse(receivedAt)-exchangeTime,payload};
}
function atomicJson(file,value){const tmp=`${file}.${process.pid}.tmp`;fs.writeFileSync(tmp,JSON.stringify(value,null,2)+'\n',{flag:'w'});fs.renameSync(tmp,file);}
function rawSize(dir){return fs.readdirSync(dir,{withFileTypes:true}).filter(x=>x.isFile()&&x.name.startsWith('depth-')&&x.name.endsWith('.json.gz')).reduce((n,x)=>n+fs.statSync(path.join(dir,x.name)).size,0);}
function acquireLock(file){const fd=fs.openSync(file,'wx',0o600);fs.writeSync(fd,JSON.stringify({pid:process.pid,startedAt:new Date().toISOString()}));return fd;}
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));

export async function run({root=process.cwd(),WebSocketImpl=globalThis.WebSocket,fetchImpl=globalThis.fetch,now=()=>Date.now()}={}){
 const cache=path.resolve(root,'research/cache/validation');fs.mkdirSync(cache,{recursive:true});
 const lockPath=path.join(cache,'depth-worker.lock'),statusPath=path.join(cache,'depth-worker-status.json'),stopPath=path.join(cache,'STOP'),ledgerPath=path.join(cache,'controller-state.json');
 const startedAt=new Date(now()).toISOString(),runId=randomUUID();let lockFd=null,ws=null,stop=false,ended=false,active=false;
 let status={runId,state:'starting',startedAt,endedAt:null,lastHeartbeatAt:startedAt,lastChunkAt:null,chunks:0,events:0,duplicates:0,consecutiveFailures:0,lastSequence:null,error:null,validated:false,ordersSent:0};
 let items=[],bufferBytes=0,chunkStarted=now(),chunkIndex=0,lastU=null,streamGeneration=0,snapshotCheckpoint=null,chunkConnectionId=null;
 const onSignal=()=>{stop=true;try{ws?.close(1000,'stop requested');}catch{}};
 process.once('SIGTERM',onSignal);process.once('SIGINT',onSignal);
 const update=()=>{status.lastHeartbeatAt=new Date(now()).toISOString();atomicJson(statusPath,status);};
 const fail=e=>{status.state='failed';status.error=String(e?.message||e);ended=true;};
 const flush=()=>{
  if(!items.length)return;
  const payload={schema:1,runId,chunk:chunkIndex++,connectionId:chunkConnectionId,symbol:'BTCUSDT',startedAt:items[0].received_at,endedAt:items.at(-1).received_at,sequenceStart:items[0].sequence,sequenceEnd:items.at(-1).sequence,snapshot:snapshotCheckpoint,events:items};
  const raw=Buffer.from(JSON.stringify(payload));if(raw.length>LIMITS.maxBufferBytes)throw Error('Chunk exceeds bounded memory limit');
  const compressed=gzipSync(raw,{level:1});const used=rawSize(cache);
  if(!cacheCanAppend(used,compressed.length))throw Error('Raw cache capacity reached; no old chunks deleted');
  const name=`depth-${startedAt.replace(/[:.]/g,'-')}-${String(payload.chunk).padStart(8,'0')}-${createHash('sha256').update(compressed).digest('hex').slice(0,12)}.json.gz`;
  const out=path.join(cache,name),tmp=out+'.tmp';let fd;try{fd=fs.openSync(tmp,'wx',0o600);fs.writeFileSync(fd,compressed);fs.fsyncSync(fd);fs.closeSync(fd);fd=null;fs.renameSync(tmp,out);}catch(e){if(fd!==undefined&&fd!==null)try{fs.closeSync(fd);}catch{};try{fs.unlinkSync(tmp);}catch{};throw e;}
  status.chunks++;status.lastChunkAt=new Date(now()).toISOString();snapshotCheckpoint=null;chunkConnectionId=null;items=[];bufferBytes=0;chunkStarted=now();update();
 };
 const push=(event,receivedAt=new Date(now()).toISOString(),connectionId=streamGeneration)=>{
  const encoded=encodedEvent(event,receivedAt);const size=Buffer.byteLength(JSON.stringify(encoded));
  if(size>LIMITS.maxEventBytes)throw Error('Depth event exceeds bounded memory limit');
  const snapshotBytes=snapshotCheckpoint?Buffer.byteLength(JSON.stringify(snapshotCheckpoint)):0;if(bufferBytes+size+snapshotBytes>LIMITS.maxBufferBytes)flush();
  if(chunkConnectionId!==null&&chunkConnectionId!==connectionId)throw Error('Chunk cannot span WebSocket connections');chunkConnectionId=connectionId;items.push(encoded);bufferBytes+=size;status.events++;status.lastSequence=event.u;
  if(isChunkFull(bufferBytes,now()-chunkStarted))flush();
 };
 const snapshot=async()=>{
  const response=await fetchImpl(SNAPSHOT_URL,{signal:AbortSignal.timeout(10_000)});
  if(!response.ok)throw Error(`Snapshot HTTP ${response.status}`);
  const value=await response.json();
  if(!Number.isSafeInteger(value.lastUpdateId)||!Array.isArray(value.bids)||!Array.isArray(value.asks))throw Error('Invalid depth snapshot');
  return {value,receivedAt:new Date(now()).toISOString()};
 };
 const connect=async()=>{
  if(typeof WebSocketImpl!=='function')throw Error('Node 22 global WebSocket is required');
  const generation=++streamGeneration;const queued=[];let queueBytes=0,opened=false,resolveOpen,rejectOpen,openTimeout;
  const opening=new Promise((resolve,reject)=>{resolveOpen=resolve;rejectOpen=reject;});
  ws=new WebSocketImpl(STREAM_URL);
  ws.addEventListener('open',()=>{opened=true;resolveOpen();});
  ws.addEventListener('error',()=>{if(!opened)rejectOpen(Error('Public WebSocket connection failed'));});
  ws.addEventListener('close',()=>{if(!opened)rejectOpen(Error('WebSocket closed before opening'));});
  ws.addEventListener('message',ev=>{
   if(generation!==streamGeneration||stop||ended)return;
   try{const text=typeof ev.data==='string'?ev.data:Buffer.from(ev.data).toString('utf8');const n=Buffer.byteLength(text);if(n>LIMITS.maxEventBytes)throw Error('Incoming event too large');if(lastU===null||!active){if(queueBytes+n>LIMITS.maxBufferBytes)throw Error('Snapshot synchronization buffer full');queued.push(queueDiff(JSON.parse(text),new Date(now()).toISOString()));queueBytes+=n;return;}
    const payload=JSON.parse(text),receivedAt=new Date(now()).toISOString();const step=sequenceStep(payload,lastU);if(step.kind==='invalid')throw Error('Invalid diff sequence');if(step.kind==='duplicate'){status.duplicates++;return;}if(step.kind==='gap')throw Error(`Sequence gap after ${lastU}: received ${payload.U}-${payload.u}`);push(payload,receivedAt,generation);lastU=step.lastU;status.lastSequence=lastU;
   }catch(e){status.error=String(e?.message||e);status.state='reconnecting';try{ws?.close(4000,'sequence or buffer error');}catch{}}
  });
  try{await Promise.race([opening,new Promise((_,reject)=>{openTimeout=setTimeout(()=>reject(Error('WebSocket open timeout')),10_000);})]);}finally{clearTimeout(openTimeout);}
  const snapshotResult=await snapshot(),snap=snapshotResult.value;let cursor=snap.lastUpdateId;
  for(const queuedEvent of queued){const event=queuedEvent.payload;const step=sequenceStep(event,cursor);if(step.kind==='invalid')throw Error('Invalid queued diff');if(step.kind==='duplicate')continue;if(step.kind==='gap')throw Error(`Snapshot sequence gap at ${cursor}: ${event.U}-${event.u}`);cursor=step.lastU;}
  lastU=cursor;active=true;snapshotCheckpoint={lastUpdateId:snap.lastUpdateId,bids:snap.bids,asks:snap.asks,received_at:snapshotResult.receivedAt};if(Buffer.byteLength(JSON.stringify(snapshotCheckpoint))>LIMITS.maxSnapshotBytes)throw Error('Depth snapshot exceeds bounded memory limit');chunkConnectionId=generation;status.lastSequence=lastU;status.state='capturing';status.error=null;
  // Replay queued diffs from the snapshot. Keep exact wire payloads; snapshot itself is checkpoint metadata.
  cursor=snap.lastUpdateId;
  for(const queuedEvent of queued){const event=queuedEvent.payload,step=sequenceStep(event,cursor);if(step.kind==='apply'){push(event,queuedEvent.receivedAt,generation);cursor=step.lastU;}}
  lastU=cursor;
  return true;
 };
 try{
  lockFd=acquireLock(lockPath);
  if(fs.existsSync(stopPath))throw Error('STOP marker present');
  if(fs.existsSync(ledgerPath)&&JSON.parse(fs.readFileSync(ledgerPath,'utf8')).active)throw Error('Development attempt active; capture prohibited');
  if(!WebSocketImpl||!fetchImpl)throw Error('WebSocket/fetch runtime unavailable');
  status.state='capturing';update();
  let heartbeat=setInterval(()=>{try{if(fs.existsSync(stopPath)){stop=true;ws?.close(1000,'STOP marker');}if(items.length&&now()-chunkStarted>=LIMITS.flushMs)flush();update();}catch(e){fail(e);}},LIMITS.statusMs);heartbeat.unref?.();
  let stopPoll=setInterval(()=>{if(fs.existsSync(stopPath)){stop=true;try{ws?.close(1000,'STOP marker');}catch{}}},LIMITS.stopPollMs);stopPoll.unref?.();
  try{
   let backoff=LIMITS.minBackoffMs;
   while(!stop&&!ended){try{await connect();backoff=LIMITS.minBackoffMs;const stableSince=now();let stableReset=false;while(!stop&&!ended&&ws?.readyState===WebSocketImpl.OPEN){await wait(250);if(!stableReset&&now()-stableSince>=10_000){status.consecutiveFailures=0;stableReset=true;update();}if(status.error){const error=status.error;status.error=null;throw Error(error);}}if(status.error){const error=status.error;status.error=null;throw Error(error);}if(!stop&&!ended)throw Error('WebSocket disconnected');}
    catch(e){if(stop)break;try{flush();}catch(flushError){fail(flushError);break;}active=false;lastU=null;streamGeneration++;try{ws?.close();}catch{};ws=null;status.consecutiveFailures++;status.state='reconnecting';status.error=String(e?.message||e);update();if(status.consecutiveFailures>=LIMITS.maxFailures){fail(Error(`Three consecutive stream failures: ${status.error}`));break;}await wait(backoff);backoff=Math.min(LIMITS.maxBackoffMs,Math.max(LIMITS.minBackoffMs,backoff*2));}
   }
  }finally{clearInterval(heartbeat);clearInterval(stopPoll);}
  if(stop&&!ended)status.state='stopped';
 }catch(e){fail(e);}
 finally{
  streamGeneration++;try{ws?.close(1000,'worker shutdown');}catch{};
  if(lockFd!==null){try{flush();}catch(e){fail(e);}
   status.endedAt=new Date(now()).toISOString();if(status.state==='starting')status.state='failed';if(status.state==='capturing')status.state=stop?'stopped':'failed';try{update();}catch{}
  }
  process.removeListener('SIGTERM',onSignal);process.removeListener('SIGINT',onSignal);
  if(lockFd!==null){fs.closeSync(lockFd);try{fs.unlinkSync(lockPath);}catch{}}
 }
 return status;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){const rootArg=process.argv.indexOf('--root');const root=rootArg>=0?process.argv[rootArg+1]:process.cwd();const result=await run({root});console.log(JSON.stringify(result));if(result.state==='failed')process.exitCode=1;}
