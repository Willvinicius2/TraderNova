import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import ts from 'typescript';
const temp=await fs.mkdtemp(path.join(os.tmpdir(),'tradernova-test-'));
try{
 for(const name of ['domain','backtest','integrations']){
  const src=await fs.readFile(new URL(`../lib/tradernova/${name}.ts`,import.meta.url),'utf8');
  const js=ts.transpileModule(src,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText.replace("'./domain'","'./domain.mjs'");
  await fs.writeFile(path.join(temp,`${name}.mjs`),js);
 }
 const d=await import(pathToFileURL(path.join(temp,'domain.mjs'))),b=await import(pathToFileURL(path.join(temp,'backtest.mjs'))),i=await import(pathToFileURL(path.join(temp,'integrations.mjs')));
 assert.deepEqual(d.ema([1,2,3,4,5],3),[null,null,2,3,4]);
 const candles=d.createCandles(d.assets[0],600);assert.deepEqual(candles,d.createCandles(d.assets[0],600));
 const altered=[...candles.slice(0,200),...candles.slice(200).map(c=>({...c,close:c.close*10}))];
 assert.deepEqual(d.ema(candles.map(c=>c.close),20).slice(0,200),d.ema(altered.map(c=>c.close),20).slice(0,200));
 assert.deepEqual(d.atr(candles).slice(0,200),d.atr(altered).slice(0,200));
 const a=b.backtest(candles,'XAUUSD',0,2),costly=b.backtest(candles,'XAUUSD',.2,2);
 assert.ok(a.trades.length>0);assert.equal(a.trades.length,costly.trades.length);
 assert.ok(Math.abs(a.netR-costly.netR-a.trades.length*.2)<1e-8);
 const fast=d.ema(candles.map(c=>c.close),9),slow=d.ema(candles.map(c=>c.close),21);
 for(const t of a.trades){const index=candles.findIndex(c=>c.time===t.entryTime);assert.equal(t.entry,candles[index].open);assert.ok(index>=23);assert.ok((fast[index-2]<=slow[index-2]&&fast[index-1]>slow[index-1])||(fast[index-2]>=slow[index-2]&&fast[index-1]<slow[index-1]));assert.ok(t.exitTime>=t.entryTime);}
 // Force both levels inside the first trade's candle: conservative stop must win.
 const firstIndex=candles.findIndex(c=>c.time===a.trades[0].entryTime),ambiguous=candles.map(c=>({...c}));
 ambiguous[firstIndex].high=candles[firstIndex].open*2;ambiguous[firstIndex].low=candles[firstIndex].open*.5;
 const amb=b.backtest(ambiguous,'XAUUSD',0,2);assert.equal(amb.trades[0].reason,'Stop · barra ambígua');assert.ok(Math.abs(amb.trades[0].r+1)<1e-8);
 const gap=candles.map(c=>({...c}));gap[firstIndex].high=gap[firstIndex].open;gap[firstIndex].low=gap[firstIndex].open;gap[firstIndex].close=gap[firstIndex].open;
 const first=gap[firstIndex].open,side=a.trades[0].direction==='Compra'?1:-1;
 gap[firstIndex+1]={...gap[firstIndex+1],open:first*(side===1?.8:1.2),close:first*(side===1?.8:1.2),high:first*(side===1?.8:1.2),low:first*(side===1?.8:1.2)};
 const g=b.backtest(gap,'XAUUSD',0,2);assert.ok(g.trades[0].r< -1);assert.equal(g.trades[0].exit,gap[firstIndex+1].open);
 assert.throws(()=>b.backtest(candles,'XAUUSD',NaN,2));assert.throws(()=>b.backtest([...candles].reverse(),'XAUUSD'));
 const s=d.makeSignal(d.assets[0],'Compra');assert.equal(d.signalState(s,s.expiresAt),'Expirado');assert.ok(s.stop<s.entry&&s.target>s.entry);
 const sell=d.makeSignal(d.assets[0],'Venda');assert.ok(sell.target<sell.entry&&sell.stop>sell.entry);
 const snapshot={instrument_id:'test',observed_at:new Date(100000).toISOString(),received_at:new Date(100100).toISOString(),bid:100,ask:101,source:'fixture',mode:'live'};
 assert.equal(i.isUsableSnapshot(snapshot,105000),true);assert.equal(i.isUsableSnapshot(snapshot,200000),false);assert.equal(i.isUsableSnapshot({...snapshot,mode:'demo'},105000),false);assert.equal(i.isUsableSnapshot({...snapshot,ask:99},105000),false);
 assert.equal(i.hasProAccess({plan:'pro',status:'active',expires_at:null,provider:'apple'}),false);assert.equal(i.hasProAccess({plan:'pro',status:'active',expires_at:'2000-01-01',provider:'apple'}),false);
 console.log(`Core checks passed: EMA/ATR causality, deterministic fixture, ${a.trades.length} next-bar trades, costs, ambiguous stops, gaps, invalid data, signal expiry, stale feeds, entitlements.`);
}finally{await fs.rm(temp,{recursive:true,force:true});}
