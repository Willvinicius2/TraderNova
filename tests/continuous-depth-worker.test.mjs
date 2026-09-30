import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {sequenceStep,cacheCanAppend,isChunkFull,LIMITS,queueDiff,run} from '../scripts/continuous-depth-worker.mjs';

test('sequence accepts exact next range, ignores old duplicate, flags gap and malformed ranges',()=>{
 assert.deepEqual(sequenceStep({U:10,u:12},9),{kind:'apply',lastU:12});
 assert.deepEqual(sequenceStep({U:10,u:12},12),{kind:'duplicate'});
 assert.deepEqual(sequenceStep({U:14,u:15},12),{kind:'gap'});
 assert.deepEqual(sequenceStep({U:4,u:3},2),{kind:'invalid'});
});
test('flush thresholds and cache capacity are inclusive and bounded',()=>{
 assert.equal(isChunkFull(LIMITS.chunkBytes,0),true);
 assert.equal(isChunkFull(1,LIMITS.flushMs),true);
 assert.equal(cacheCanAppend(LIMITS.rawCacheBytes-4,4),true);
 assert.equal(cacheCanAppend(LIMITS.rawCacheBytes-4,5),false);
});
test('append cache accounting preserves old raw chunks and refuses overflow',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'depth-cache-'));
 try{
  const old=path.join(dir,'depth-old.json.gz');fs.writeFileSync(old,Buffer.alloc(6));
  const existing=fs.statSync(old).size;
  assert.equal(cacheCanAppend(existing,LIMITS.rawCacheBytes-existing),true);
  assert.equal(cacheCanAppend(existing,LIMITS.rawCacheBytes-existing+1),false);
  assert.equal(fs.existsSync(old),true);
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
});


test('queued diffs retain their wire receive timestamp through snapshot replay',()=>{
 const receivedAt='2026-09-30T03:20:01.234Z';
 const queued=queueDiff({U:11,u:13},receivedAt);
 assert.equal(queued.receivedAt,receivedAt);
 assert.deepEqual(queued.payload,{U:11,u:13});
});

test('an existing live-worker lock preserves lock and status sentinels',async()=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'depth-lock-'));
 try{
  const cache=path.join(root,'research','cache','validation');fs.mkdirSync(cache,{recursive:true});
  const lock=path.join(cache,'depth-worker.lock'),status=path.join(cache,'depth-worker-status.json');
  fs.writeFileSync(lock,'live-owner-sentinel');fs.writeFileSync(status,'live-status-sentinel');
  const result=await run({root,WebSocketImpl:undefined,fetchImpl:undefined});
  assert.equal(result.state,'failed');
  assert.equal(fs.readFileSync(lock,'utf8'),'live-owner-sentinel');
  assert.equal(fs.readFileSync(status,'utf8'),'live-status-sentinel');
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});
