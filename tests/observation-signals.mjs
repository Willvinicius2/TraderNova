import assert from 'node:assert/strict';
import {loadResearchModules} from '../scripts/research-modules.mjs';
const m=await loadResearchModules();
try{
 const p=m.paper,reward=m.presets.activePresets.T3.reward;
 const step=3600000,closedAt=Date.UTC(2025,0,1)+221*step,now=closedAt+5000,quote={bid:109,ask:109.1,timestamp:now};
 const snapshot={status:'ready',reason:'fixture',source:'kraken-spot',evaluatedAt:now,closedAt,readings:[{candidateId:'T3',state:'buy',signalTime:closedAt-step,entryReference:108,stop:100,target:124,evidence:['controlled test']}]};
 const s=p.observationOpportunity(snapshot,'T3','BTCUSD',quote,now);
 assert.ok(s);assert.equal(s.validated,false);assert.equal(s.kind,'observation');assert.equal(s.assetId,'BTCUSD');assert.equal(s.expiresAt,closedAt+3600000);assert.equal(s.quoteAt,quote.timestamp);
 assert.ok(s.stop<s.entry&&s.entry<s.target);assert.ok(Math.abs((s.target-s.entry)-(s.entry-s.stop)*reward)<1e-9);
 assert.equal(p.manualOpportunity(snapshot,'T3',quote,now),null,'No manual alert without approval');assert.deepEqual(p.strategyApprovals,[]);
 assert.equal(p.observationOpportunity({...snapshot,status:'blocked'},'T3','BTCUSD',quote,now),null);
 assert.equal(p.observationOpportunity(snapshot,'T3','BTCUSD',{...quote,timestamp:closedAt-1},now),null);
 assert.equal(p.observationOpportunity(snapshot,'T3','BTCUSD',{...quote,timestamp:closedAt+31000},closedAt+31000),null);
 assert.equal(p.observationOpportunity({...snapshot,readings:[{...snapshot.readings[0],state:'waiting'}]},'T3','BTCUSD',quote,now),null);
 const e=p.observationOpportunity(snapshot,'T3','ETHUSD',quote,now);assert.ok(e);assert.equal(e.assetId,'ETHUSD');assert.ok(e.id.startsWith('obs:ETHUSD:'));assert.notEqual(e.id,s.id,'Same close on another asset is a distinct signal');
 assert.equal(p.observationOpportunity(snapshot,'T3','SOLUSD',quote,now)?.assetId,'SOLUSD');
 const good=JSON.parse(JSON.stringify(s));
 assert.deepEqual(p.readObservationSignals([good],now),[good]);
 assert.equal(p.readObservationSignals([{...good,assetId:'SOLUSD'},{...good,id:'y',assetId:'ETHUSD'}],now).length,2);
 assert.deepEqual(p.readObservationSignals([{...good,assetId:'XAUUSD'}],now),[],'Assets without a live feed are rejected');
 assert.deepEqual(p.readObservationSignals([{...good,validated:true}],now),[]);
 assert.deepEqual(p.readObservationSignals([{...good,createdAt:now+60000}],now),[]);
 assert.deepEqual(p.readObservationSignals({a:1},now),[]);
 assert.equal(p.readObservationSignals(Array.from({length:250},(_,i)=>({...good,id:`x${i}`,createdAt:now-i})),now).length,200);
 console.log('Observation signals: unvalidated emission on BTC/ETH/SOL, freshness gates, no approval bypass and storage validation passed.');
}finally{await m.cleanup();}
