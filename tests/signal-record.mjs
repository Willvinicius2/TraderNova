import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import ts from 'typescript';
const temp=await fs.mkdtemp(path.join(os.tmpdir(),'tradernova-signal-test-'));
try{
 const src=await fs.readFile(new URL('../lib/tradernova/signal-record.ts',import.meta.url),'utf8');
 await fs.writeFile(path.join(temp,'signal-record.mjs'),ts.transpileModule(src,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText.replace("from 'zod'",`from '${pathToFileURL(path.resolve('node_modules/zod/index.js')).href}'`));
 const s=await import(pathToFileURL(path.join(temp,'signal-record.mjs')));
 const parts={strategyId:'T1',strategyVersion:'E0X0',provider:'kraken-spot',instrument:'BTCUSD',timeframeMinutes:60,side:'buy',signalTime:1789948800000};
 const key=s.signalDedupKey(parts);
 assert.equal(key,'T1@E0X0|kraken-spot|BTCUSD|60|buy|1789948800000');
 const id=s.newPublicSignalId();
 assert.ok(s.isPublicSignalId(id));
 // O ID público precisa passar na validação de deep link do mobile (letras, números e hífen).
 assert.match(id,/^[a-zA-Z0-9-]{1,100}$/);
 assert.equal(s.isPublicSignalId('T1:T1-E0X0:1789948800000'),false);
 assert.equal(s.isPublicSignalId(key),false);
 const record={publicId:id,dedupKey:key,...parts,generatedAt:1789948800500,expiresAt:1789948830000,entryReference:100,stop:95,target:110,evidence:['Teste identificado.'],mode:'test',invalidatedAt:null,invalidationReason:null};
 assert.equal(s.signalRecordSchema.safeParse(record).success,true);
 assert.equal(s.signalRecordSchema.safeParse({...record,stop:105}).success,false,'stop acima da entrada em compra');
 assert.equal(s.signalRecordSchema.safeParse({...record,expiresAt:record.generatedAt}).success,false);
 assert.equal(s.resolveSignalView('nao-e-uuid',record,0).state,'invalid-id');
 assert.equal(s.resolveSignalView(id,record,0,false).state,'unauthorized');
 assert.equal(s.resolveSignalView(s.newPublicSignalId(),null,0).state,'not-found');
 assert.equal(s.resolveSignalView(id.toUpperCase(),record,record.generatedAt).state,'active');
 assert.equal(s.resolveSignalView(id,record,record.expiresAt).state,'expired');
 assert.equal(s.resolveSignalView(id,{...record,invalidatedAt:record.generatedAt+1,invalidationReason:'Fonte atrasada.'},record.generatedAt).state,'invalidated');
 const store=s.createMemorySignalStore();
 const first=await store.insertIfAbsent(record);assert.equal(first.created,true);
 const dup=await store.insertIfAbsent({...record,publicId:s.newPublicSignalId()});
 assert.equal(dup.created,false);assert.equal(dup.record.publicId,id,'duplicata devolve o sinal original');
 assert.equal((await store.get(id)).dedupKey,key);
 assert.equal(await store.get(s.newPublicSignalId()),null,'ID desconhecido não cria sinal');
 assert.equal(await store.get('T1:T1-E0X0:1789948800000'),null);
 console.log('Signal record checks passed: opaque UUID ids, separate dedup key, five view states, idempotent store.');
}finally{await fs.rm(temp,{recursive:true,force:true});}
