import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
import ts from 'typescript';
const require=createRequire(import.meta.url),temp=await fs.mkdtemp(path.join(os.tmpdir(),'tradernova-research-'));
const near=(a,b,message)=>assert.ok(Math.abs(a-b)<1e-8,`${message}: ${a} vs ${b}`);
try{
 for(const name of ['domain','indicators','research','research-storage']){
  const source=await fs.readFile(new URL(`../lib/tradernova/${name}.ts`,import.meta.url),'utf8');
  const js=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText.replaceAll("'./domain'","'./domain.mjs'").replaceAll("'./indicators'","'./indicators.mjs'").replaceAll("'zod'",JSON.stringify(pathToFileURL(require.resolve('zod')).href));
  await fs.writeFile(path.join(temp,`${name}.mjs`),js);
 }
 const d=await import(pathToFileURL(path.join(temp,'domain.mjs'))),ind=await import(pathToFileURL(path.join(temp,'indicators.mjs'))),r=await import(pathToFileURL(path.join(temp,'research.mjs'))),storage=await import(pathToFileURL(path.join(temp,'research-storage.mjs')));
 const start=Date.UTC(2026,7,1),flat=Array.from({length:260},(_,i)=>({time:start+i*60000,open:100,high:102,low:98,close:100,volume:1}));
 const readings=Object.fromEntries(ind.indicatorReadings(flat).map(v=>[v.id,v.values]));
 assert.equal(Object.keys(readings).length,10);
 for(const id of ['ema20','ema50','ema200','sma20'])near(readings[id][0],100,id);
 near(readings.rsi14[0],50,'Flat RSI');near(readings.atr14[0],4,'ATR constant range');near(readings.atrp14[0],4,'ATR percentage');
 assert.deepEqual(readings.macd,[0,0,0]);assert.deepEqual(readings.bollinger,[100,100,100]);assert.deepEqual(readings.donchian,[98,102]);
 assert.ok(ind.indicatorReadings([]).every(v=>v.values===null));
 assert.equal(ind.macd(Array(33).fill(100)),null,'MACD signal waits for its complete warmup');
 const linear=Array.from({length:60},(_,i)=>i+1),m=ind.macd(linear);
 near(m.line,7,'Linear-series MACD');near(m.signal,7,'Linear-series signal');near(m.histogram,0,'Linear-series histogram');
 const b=ind.bands([1,2,3,4],4);near(b.middle,2.5,'Bollinger mean');near(b.upper,2.5+Math.sqrt(5),'Population standard deviation');
 assert.equal(ind.closedCandles(flat,1,start+200*60000).length,200);
 assert.equal(ind.countGaps(flat.filter((_,i)=>i!==40),1),1);
 const breakout=flat.map(b=>({...b}));breakout[220]={...breakout[220],open:100,high:109,close:108};
 assert.deepEqual(ind.channelBefore(breakout,220),{upper:102,lower:98});
 assert.equal(r.candidateSignals(breakout,'T3')[220],1,'Decision candle must not raise its own breakout threshold');
 const bars=d.createCandles(d.assets.find(a=>a.id==='BTCUSD'),720,15);
 const options={candidateId:'T1',assetId:'BTCUSD',source:'synthetic',interval:15,costR:0,reward:2,stopAtr:1.5,maxHold:8,asOf:bars.at(-1).time+15*60000,sampleHash:'controlled-test-fixture'};
 near(ind.indicatorReadings(bars).find(v=>v.id==='ema20').values[0],d.ema(bars.map(b=>b.close),20).at(-1),'Chart/indicator EMA identity');
 for(const candidate of r.researchCandidates){
  const signals=r.candidateSignals(bars,candidate.id),prefix=bars.slice(0,400);
  assert.deepEqual(r.candidateSignals(prefix,candidate.id),signals.slice(0,400),`${candidate.id}: future bars cannot change past signals`);
  const report=r.runResearch(bars,{...options,candidateId:candidate.id,stopAtr:candidate.stopAtr,maxHold:candidate.hold});
  assert.ok(report.trades.length>0,`${candidate.id}: fixture exercises actual entries`);
  for(const t of report.trades){
   assert.equal(t.entryTime,t.signalTime+15*60000,'Entry follows a closed signal candle');
   assert.ok(t.exitTime>=t.entryTime);
   assert.equal(t.entry,bars.find(b=>b.time===t.entryTime).open,'Execution uses the next open');
  }
  const charged=r.runResearch(bars,{...options,candidateId:candidate.id,stopAtr:candidate.stopAtr,maxHold:candidate.hold,costR:.1});
  assert.equal(charged.trades.length,report.trades.length,'Costs do not change entry signals');
  near(charged.netR,report.netR-.1*report.trades.length,'Every closed trade pays the configured cost');
  near(report.netR,report.trades.reduce((s,t)=>s+t.r,0),'Trade/equity reconciliation');
  assert.equal(report.validated,false);
  assert.deepEqual(storage.parseResearchReports(JSON.parse(JSON.stringify([report]))),[report],'Result history survives serialization');
  assert.deepEqual(storage.parseResearchReports([{...report,validated:true},report]),[report],'Invalid history record does not discard valid experiments');
 }
 const empty=r.runResearch(flat,{...options,interval:1,asOf:flat.at(-1).time+60000});
 assert.equal(empty.trades.length,0);assert.equal(empty.winRate,null);assert.equal(empty.expectancyR,null);assert.equal(empty.profitFactor,null);assert.equal(empty.netR,0);
 const caseOptions={...options,candidateId:'T3',interval:1,asOf:flat.at(-1).time+60000};
 const ambiguous=breakout.map(b=>({...b}));ambiguous[221]={...ambiguous[221],open:108,high:140,low:50,close:108};
 const stop=r.runResearch(ambiguous,caseOptions).trades[0];
 assert.equal(stop.entryTime,ambiguous[221].time);near(stop.r,-1,'Stop takes precedence when both exits occur in one candle');assert.equal(stop.reason,'Stop · candle ambíguo');
 const gap=breakout.map(b=>({...b}));gap[221]={...gap[221],open:108,high:109,low:107,close:108};gap[222]={...gap[222],open:90,high:91,low:89,close:90};
 const gapTrade=r.runResearch(gap,caseOptions).trades[0];assert.equal(gapTrade.exit,90);assert.ok(gapTrade.r<-1,'A gap through the stop executes at the worse open');
 for(const bad of [{costR:-1},{reward:0},{stopAtr:0},{maxHold:1.5},{interval:2},{candidateId:'S1'},{asOf:options.asOf-1}])assert.throws(()=>r.runResearch(bars,{...options,...bad}));
 assert.throws(()=>r.runResearch(bars.filter((_,i)=>i!==300),options),/lacunas/);
 assert.throws(()=>r.runResearch(bars.slice(0,240),options),/260/);
 console.log('Calibration/research checks passed: 10 readings, numerical reference values, warmup, chart identity, closed candles, gaps, all three causal strategies, next-open entries, costs, reconciled results, ambiguous stops, adverse gaps and isolated persistent history.');
}finally{await fs.rm(temp,{recursive:true,force:true});}
