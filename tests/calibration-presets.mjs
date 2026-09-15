import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {loadResearchModules} from '../scripts/research-modules.mjs';
const m=await loadResearchModules();
try{
 const bars=m.domain.createCandles(m.domain.assets.find(a=>a.id==='BTCUSD'),1000,60).map((b,i)=>({...b,time:Date.UTC(2025,0,1)+i*3600000}));
 const options={interval:60,from:bars[650].time,to:bars[900].time,initialCapital:10000,riskPct:.5,feeBps:10,slippageBps:2};
 for(const candidateId of ['T1','T2','T3']){
  const variants=m.calibration.calibrationVariants(candidateId);assert.equal(variants.length,9);assert.equal(new Set(variants.map(v=>v.id)).size,9);
  const original=m.historical.runHistorical(bars,{...options,candidateId});
  const parameterized=m.historical.runHistorical(bars,{...options,candidateId,parameters:m.calibration.originalParameters(candidateId)});
  assert.deepEqual(parameterized.trades,original.trades,'Original preset must be numerically identical to v1');assert.deepEqual(parameterized.curve,original.curve);
  for(const p of variants){
   assert.ok(m.calibration.validParameters(p,candidateId));const signals=m.calibration.calibratedSignals(bars,p);
   assert.deepEqual(m.calibration.calibratedSignals(bars.slice(0,750),p),signals.slice(0,750),'Calibration cannot see future bars');
   assert.ok(signals.every(s=>s===0||s===1));
   if(p.trendFilter)assert.ok(signals.slice(0,223).every(s=>s===0),'EMA200 slope requires complete history');
  }
  assert.throws(()=>m.historical.runHistorical(bars,{...options,candidateId,parameters:{...variants[0],reward:20}}));
 }
 const report=JSON.parse(await fs.readFile(new URL('../public/research/calibration.json',import.meta.url),'utf8'));
 const frozen=JSON.parse(await fs.readFile(new URL('../research/calibration-selection.json',import.meta.url),'utf8'));
 assert.equal(report.trials.length,27);assert.equal(report.results.length,9);
 for(const chosen of frozen.selection){
  const trials=frozen.trials.filter(t=>t.candidateId===chosen.candidateId),base=trials.find(t=>t.parameters.id===`${chosen.candidateId}-E0X0`);
  const ranked=trials.filter(t=>t.adequate).sort((a,b)=>b.score-a.score||a.parameters.id.localeCompare(b.parameters.id));
  const expected=ranked[0]&&ranked[0].score>base.score?ranked[0]:base;
  assert.equal(chosen.parameters.id,expected.parameters.id,'Preset determined only by frozen development trials');
  assert.ok(trials.every(t=>t.cells.every(c=>c.options.to<=Date.UTC(2025,8,1))));
  const rows=report.results.filter(r=>r.candidateId===chosen.candidateId);
  const improve=rows.filter(r=>r.validation.returnPct>r.baselineValidation.returnPct).length>=2&&rows.reduce((s,r)=>s+r.validation.returnPct-r.baselineValidation.returnPct,0)>0;
  const expectedAdopt=chosen.developmentAdequate&&chosen.developmentScore>chosen.baselineScore&&improve;
  for(const r of rows){assert.equal(r.adopted,expectedAdopt);assert.equal(r.validated,false);assert.ok(r.reasons.length>0,'Every current candidate still fails approval criteria');assert.deepEqual(r.final.options.parameters,r.stress.options.parameters,'Stress changes execution costs, never entry filters');}
 }
 const begin=Date.UTC(2025,2,1),session=m.paper.newPaperSession('T3',begin-1000);
 const snapshot={status:'ready',source:'kraken-spot',evaluatedAt:begin+1000,closedAt:begin,reason:'fixture',readings:[{candidateId:'T3',state:'buy',signalTime:begin-3600000,entryReference:100,stop:95,target:115,evidence:[]}]};
 const quote={bid:101,ask:101.1,timestamp:begin+1000};
 const position=m.paper.advancePaperSession(session,snapshot,quote,begin+1000).position;
 assert.ok(position);assert.ok(Math.abs(position.target-116.1)<1e-9,'Forward target uses calibrated 3R');assert.equal(position.expiresAt-position.entryAt,72*3600000);
 const legacy={...session,presetId:'T3-E0X0'};assert.equal(m.paper.advancePaperSession(legacy,snapshot,quote,begin+1000).position,null,'Archived rules cannot silently generate calibrated entries');
 assert.equal(m.paper.canAlertForManualTrade('T3',begin,[{candidateId:'T3',presetId:'T3-E0X0',assetId:'BTCUSD',source:'kraken-spot',interval:60,status:'validated',forwardPassed:true,approvedAt:begin-1,expiresAt:begin+1000}]),false,'Approval is bound to exact preset revision');
 console.log('Calibration checks passed: original parity, 27 causal presets, frozen development selection, validation adoption, fixed stress signals, forward target/expiry, legacy sessions and revision-bound approvals.');
}finally{await m.cleanup();}
