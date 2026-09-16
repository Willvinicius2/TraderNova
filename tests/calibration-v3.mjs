import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {loadResearchModules} from '../scripts/research-modules.mjs';
const m=await loadResearchModules();
try{
 const step=3600000,start=Date.UTC(2023,0,1);
 const bars=Array.from({length:1200},(_,i)=>{const close=100+i*.06+3*Math.sin(i/7);return {time:start+i*step,open:close-.1,high:close+.7,low:close-.7,close,volume:10};});
 const h4=m.v3.higherTrend(bars);
 for(const n of [223,600,601,602,603,604,999])assert.deepEqual(m.v3.higherTrend(bars.slice(0,n)),h4.slice(0,n),'H4 must never see a future or unfinished candle');
 for(let i=1;i<bars.length;i++)if((bars[i].time+step)%(4*step)!==0)assert.equal(h4[i],h4[i-1],'H4 state changes only at a complete H4 close');
 for(const id of ['T1','T2','T3'])for(const p of m.v3.v3Variants(id)){
  assert.ok(m.calibration.validParameters(p,id));
  assert.ok(!m.calibration.validParameters({...p,unexpected:true},id));
  const signals=m.calibration.calibratedSignals(bars,p);
  assert.deepEqual(m.calibration.calibratedSignals(bars.slice(0,901),p),signals.slice(0,901));
  assert.ok(signals.every(s=>s===0||s===1));
  const opts={candidateId:id,interval:60,from:bars[650].time,to:bars[1100].time,initialCapital:10000,riskPct:.5,feeBps:10,slippageBps:2,parameters:p};
  const run=m.historical.runHistorical(bars,opts);
  assert.deepEqual(run,m.historical.runHistorical(bars.slice(0,1100),opts),'Future candles must not change exits or sizing');
  for(let i=1;i<run.trades.length;i++)assert.ok(run.trades[i].entryTime>=run.trades[i-1].exitCandleTime+7*step,'Six full hours after the exit candle close');
  for(const t of run.trades)assert.ok(t.exitStop===undefined||t.exitStop>=t.stop,'Protected stop never loosens risk');
 }
 const trail=m.v3.v3Variants('T3').find(p=>p.trailAtr===3),protect=m.v3.v3Variants('T3').find(p=>p.breakEvenR===1.5);
 assert.equal(m.v3.nextProtectedStop(trail,90,100,10,109,109,2,101),90,'Inactive before 1R');
 assert.equal(m.v3.nextProtectedStop(trail,90,100,10,112,112,2,101),106);
 assert.equal(m.v3.nextProtectedStop(trail,106,100,10,112,108,5,101),106,'Volatility cannot lower existing stop');
 assert.equal(m.v3.nextProtectedStop(protect,90,100,10,116,116,20,101),101,'Breakeven covers costs');
 assert.equal(m.v3.nextProtectedStop(protect,90,100,10,116,99,20,101),99,'A new stop cannot claim a past fill above current close');
 const haltStart=Date.UTC(2023,2,1),halt=Array.from({length:800},(_,i)=>({...bars[0],time:haltStart+i*step})).filter(b=>b.time!==Date.UTC(2023,2,24,13));
 assert.throws(()=>m.historical.validateHistory(halt,60));
 assert.doesNotThrow(()=>m.historical.validateHistory(halt,60,'binance-spot-halt-2023-03-24'));
 assert.throws(()=>m.historical.validateHistory(halt.filter((_,i)=>i!==700),60,'binance-spot-halt-2023-03-24'),'Other gaps stay rejected');
 assert.throws(()=>m.historical.validateHistory(halt,60,'invented-exception'));
 // Nonempty integration fixture: the entry candle trades below the stop raised
 // at its close, but that protective stop can only fill on the following bar.
 const base=Date.UTC(2024,0,1),k=699;
 const sample=Array.from({length:715},(_,j)=>({time:base+j*step,open:100+j*.2,close:100+j*.2+.1,high:100+j*.2+.6,low:100+j*.2-.6,volume:10}));
 const level=Math.max(...sample.slice(k-21,k-1).map(b=>b.high));
 sample[k-1]={...sample[k-1],open:level+.05,close:level+.2,high:level+.3,low:level-.4};
 const previousAtr=m.domain.atr(sample)[k-1];
 sample[k]={...sample[k],open:level+.1,close:level+.25,high:level+.4,low:level-.25*previousAtr};
 const p=m.v3.v3Variants('T3').find(p=>p.entryProfile==='h4-reclaim'&&p.trailAtr===3);
 assert.equal(m.v3.v3Signals(sample,p)[k],1);
 const deep=sample.map(b=>({...b}));deep[k].low=level-10*previousAtr;
 assert.equal(m.v3.v3Signals(deep,p)[k],0,'Reject deep penetration, not just an upper bound');
 const rawEntry=sample[k].close,distance=p.stopAtr*m.domain.atr(sample)[k];
 sample[k+1]={...sample[k+1],open:rawEntry,low:rawEntry-.9*distance,high:rawEntry+2.05*distance,close:rawEntry+2*distance};
 const raised=sample[k+1].close-p.trailAtr*m.domain.atr(sample)[k+1];
 assert.ok(sample[k+1].low>rawEntry-distance&&sample[k+1].low<raised);
 sample[k+2]={...sample[k+2],open:sample[k+1].close,low:raised-.01*distance,high:rawEntry+2.2*distance,close:raised+.2*distance};
 const result=m.historical.runHistorical(sample,{candidateId:'T3',interval:60,from:base+(k-1)*step,to:base+715*step,initialCapital:10000,riskPct:.5,feeBps:10,slippageBps:2,parameters:p});
 assert.ok(result.trades.length>0);assert.equal(result.trades[0].entryTime,sample[k+1].time);assert.equal(result.trades[0].exitCandleTime,sample[k+2].time);assert.equal(result.trades[0].reason,'Stop protegido');
 assert.ok(Math.abs(result.trades[0].exit-raised*.9998)<1e-9);
 const frozenBytes=await fs.readFile(new URL('../research/calibration-v3-selection.json',import.meta.url));
 const frozen=JSON.parse(frozenBytes),report=JSON.parse(await fs.readFile(new URL('../public/research/calibration-v3.json',import.meta.url)));
 assert.equal(report.selectionHash,createHash('sha256').update(frozenBytes).digest('hex'));assert.equal(report.trials.length,21);
 for(const chosen of frozen.selection){
  const trials=frozen.trials.filter(t=>t.candidateId===chosen.candidateId),control=trials.find(t=>t.parameters.id===report.protocol.control[chosen.candidateId]);
  const ranked=trials.filter(t=>t.adequate).sort((a,b)=>b.score-a.score||a.parameters.id.localeCompare(b.parameters.id));
  assert.equal(chosen.parameters.id,ranked[0]&&ranked[0].score>control.score?ranked[0].parameters.id:control.parameters.id);
  assert.ok(trials.every(t=>t.cells.every(c=>c.options.to<=Date.UTC(2025,0,1))));
  const rows=report.results.filter(r=>r.candidateId===chosen.candidateId);
  const adopted=chosen.developmentAdequate&&chosen.developmentScore>chosen.baselineScore&&rows.filter(r=>r.validation.returnPct>r.baselineValidation.returnPct).length>=2&&rows.reduce((s,r)=>s+r.validation.returnPct-r.baselineValidation.returnPct,0)>0&&rows.filter(r=>r.validation.net>0).length>=2;
  for(const row of rows){assert.equal(row.adopted,adopted);assert.equal(row.validated,false);assert.deepEqual(row.final.options.parameters,row.stress.options.parameters);}
 }
 console.log('V3: causal H4/signals/exits, cooldown, protective stops, canonical presets and exact documented halt checks passed.');
}finally{await m.cleanup();}
