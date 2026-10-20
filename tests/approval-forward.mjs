import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {loadResearchModules} from '../scripts/research-modules.mjs';
const m=await loadResearchModules();
try{
 const {approvals:a,forward:f}=m,day=86400000,hour=3600000;
 // Register on disk is valid and approves nothing.
 const register=a.approvalRegisterSchema.parse(JSON.parse(await fs.readFile(new URL('../research/approval-register.json',import.meta.url),'utf8')));
 assert.equal(a.approvedCount(register),0,'Nenhuma estratégia aprovada');
 const h='a'.repeat(64),entry={strategyId:'R1',version:'v4',variantId:'R1-E0X0',instruments:['BTCUSD','ETHUSD'],protocol:{file:'research/v4-protocol.json',sha256:h},selectionSha256:h,engineSha256:h,historical:{passed:true,report:'public/research/v4-crypto.json'},contract:{confirmed:true,reference:'#25',costsWithinStress:true},forward:{startedAt:0,endedAt:31*day,days:31,trades:12,maxDrawdownPct:3,worstValidationDrawdownPct:6,parity:true,violations:0},riskPctPerTrade:.5,status:'approved',decidedAt:1,decidedBy:'Will',reason:'teste'};
 assert.doesNotThrow(()=>a.approvalEntrySchema.parse(entry));
 for(const broken of [{historical:{passed:false,report:'x'}},{contract:{confirmed:false,reference:'',costsWithinStress:true}},{contract:{confirmed:true,reference:'',costsWithinStress:false}},{forward:{...entry.forward,days:29}},{forward:{...entry.forward,trades:9}},{forward:{...entry.forward,maxDrawdownPct:7}},{forward:{...entry.forward,parity:false}},{forward:{...entry.forward,violations:1}}])
  assert.throws(()=>a.approvalEntrySchema.parse({...entry,...broken}),`Gate missing: ${JSON.stringify(broken)}`);
 assert.doesNotThrow(()=>a.approvalEntrySchema.parse({...entry,status:'suspended',forward:{...entry.forward,days:3}}),'A pending entry may be recorded as suspended');
 assert.throws(()=>a.approvalRegisterSchema.parse({...register,entries:[entry,entry]}),'Same strategy and version once');
 const two={...register,entries:[entry,{...entry,strategyId:'V1',variantId:'V1-E0X0',instruments:['BTCUSD','EURUSD']},{...entry,strategyId:'R1',version:'v5'}]};
 assert.equal(a.approvedCount(two),2,'Families count once across versions and assets');
 assert.equal(a.jointRiskCheck(two,[],{strategyId:'R1',instrument:'SOLUSD'},0).allowed,false,'Not approved for this asset');
 assert.deepEqual(a.jointRiskCheck(two,[],{strategyId:'R1',instrument:'BTCUSD'},0),{allowed:true,riskPct:.5,reasons:[]});
 assert.equal(a.jointRiskCheck(two,[{strategyId:'R1',instrument:'BTCUSD',riskPct:.5}],{strategyId:'R1',instrument:'BTCUSD'},0).allowed,false,'One position per strategy and asset');
 const crowded=a.jointRiskCheck(two,[{strategyId:'R1',instrument:'BTCUSD',riskPct:.5},{strategyId:'X',instrument:'ETHUSD',riskPct:.5}],{strategyId:'V1',instrument:'BTCUSD'},0);
 assert.ok(!crowded.allowed&&crowded.reasons.some(r=>r.includes('cripto')),'Crypto cluster capped at 1%');
 assert.ok(a.jointRiskCheck(two,[{strategyId:'R1',instrument:'BTCUSD',riskPct:.5}],{strategyId:'V1',instrument:'EURUSD'},0).allowed,'Different cluster allowed');
 assert.ok(!a.jointRiskCheck(two,[],{strategyId:'V1',instrument:'EURUSD'},2.1).allowed,'Daily floor with buffer');
 assert.ok(!a.jointRiskCheck(two,[{strategyId:'a',instrument:'X1',riskPct:.6},{strategyId:'b',instrument:'X2',riskPct:.6}],{strategyId:'V1',instrument:'EURUSD'},0).allowed,'Total open risk capped at 1.5%');
 // Forward test: only candles closed after the start; criteria from the protocol.
 const start=Date.UTC(2026,8,1);let seed=3,price=100;const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
 const bars=Array.from({length:2000},(_,i)=>{const open=price;price*=1+(random()-.5)*.012+.003*Math.sin(i/8);return {time:start+i*hour,open,close:price,high:Math.max(open,price)*1.002,low:Math.min(open,price)*.998,volume:1};});
 const opts={variantId:'R1-E0X0',startedAt:bars[800].time-1,now:bars[1999].time+hour,initialCapital:10000,riskPct:.5,feeBps:10,slippageBps:2,spread:0,sides:'long',maxLeverage:1,minStopCostMultiple:3,worstValidationDrawdownPct:8,calendar:'24x7'};
 const report=f.forwardV4(bars,opts);
 assert.equal(report.startedAt,bars[800].time,'Start rounds up to the next full hour');
 assert.ok(report.result.trades.every(t=>t.signalTime>=report.startedAt),'No signal before the forward start');
 const partial=f.forwardV4(bars,{...opts,now:bars[1500].time+hour}).result.trades.filter(t=>t.reason!=='Fim da janela');
 assert.deepEqual(partial,report.result.trades.slice(0,partial.length),'An earlier report is a prefix of the later one');
 const early=f.forwardV4(bars,{...opts,now:bars[1000].time+hour+1});
 assert.ok(!early.complete&&early.reasons.some(r=>r.includes('dias')),'Fewer than 30 days is incomplete');
 assert.ok(report.days>=30&&report.result.trades.length>0);
 assert.equal(report.passed,report.reasons.length===0);
 assert.ok(f.forwardV4(bars,{...opts,worstValidationDrawdownPct:1e-9}).reasons.some(r=>r.includes('drawdown'))||report.result.maxDrawdownPct===0);
 assert.throws(()=>f.forwardV4(bars,{...opts,variantId:'R9'}));
 assert.throws(()=>f.forwardV4(bars,{...opts,now:bars[810].time}),'Needs at least a day after the start');
 console.log(`Approval register and forward test checks passed: gates enforced, families counted once, joint risk caps, prospective-only replay (${report.result.trades.length} fixture trades in ${report.days.toFixed(0)} days).`);
}finally{await m.cleanup();}
