import assert from 'node:assert/strict';
import {loadResearchModules} from '../scripts/research-modules.mjs';
const m=await loadResearchModules();
try{
 const {v4}=m,step=3600000,start=Date.UTC(2023,0,2);
 let seed=7;const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
 // Choppy series with volatility cycles so both families trade.
 let price=100;
 const bars=Array.from({length:3200},(_,i)=>{
  const vol=.004+.003*Math.sin(i/150),open=price;price=Math.max(5,price*(1+(random()-.5)*vol*2+.002*Math.sin(i/9)));
  const close=price;return {time:start+i*step,open,close,high:Math.max(open,close)*(1+vol*random()*.5),low:Math.min(open,close)*(1-vol*random()*.5),volume:10};
 });
 assert.equal(v4.v4Variants.length,8);assert.equal(new Set(v4.v4Variants.map(v=>v.id)).size,8);
 const options=v=>({variant:v,from:bars[800].time,to:bars[3000].time,initialCapital:10000,riskPct:.5,feeBps:10,slippageBps:2,spread:0,sides:'both',maxLeverage:1,minStopCostMultiple:3});
 const trend=v4.h4Trend(bars);
 for(const n of [700,901,1203,2999])assert.deepEqual(v4.h4Trend(bars.slice(0,n)),trend.slice(0,n),'H4 never sees an unfinished candle');
 for(let i=1;i<bars.length;i++)if((bars[i].time+step)%(4*step)!==0)assert.equal(trend[i],trend[i-1],'H4 state changes only at a complete H4 close');
 const counts={};
 for(const v of v4.v4Variants){
  const signals=v4.v4Signals(bars,v,'both');
  assert.deepEqual(v4.v4Signals(bars.slice(0,1500),v,'both'),signals.slice(0,1500),`${v.id}: signals are causal`);
  assert.ok(v4.v4Signals(bars,v,'long').every((s,i)=>s===Math.max(0,signals[i])),'Long-only drops sells only');
  const run=v4.runV4(bars,options(v));
  assert.deepEqual(run,v4.runV4(bars.slice(0,3000),options(v)),`${v.id}: future candles cannot alter the window`);
  const future=bars.map((b,i)=>i<3000?b:{...b,open:b.open*3,close:b.close*3,high:b.high*3,low:b.low*3});
  assert.deepEqual(v4.runV4(future,options(v)),run);
  assert.ok(Math.abs(run.net-run.trades.reduce((s,t)=>s+t.net,0))<1e-6);
  for(let i=1;i<run.trades.length;i++)assert.ok(run.trades[i].entryTime>=run.trades[i-1].exitCandleTime+7*step,'Six full hours of cooldown');
  let equity=10000;
  for(const t of run.trades){
   assert.ok(t.signalTime>=bars[800].time&&t.entryTime===t.signalTime+step,'Next-open entry inside the window');
   assert.ok(t.quantity*t.entry*1.001<=equity+1e-6,'No leverage on spot');equity+=t.net;
   assert.ok(t.exitCandleTime-t.entryTime<v.hold*step,'Holding limit');
  }
  counts[v.id]=run.trades.length;
  // Costs can only hurt: the old FX screen credited costs on mirrored shorts.
  const free=v4.runV4(bars,{...options(v),feeBps:0,slippageBps:0,minStopCostMultiple:0}),costly=v4.runV4(bars,{...options(v),feeBps:0,slippageBps:0,spread:.05,minStopCostMultiple:0});
  assert.equal(free.trades.length,costly.trades.length);
  free.trades.forEach((t,k)=>{if(t.reason===costly.trades[k].reason&&t.exitCandleTime===costly.trades[k].exitCandleTime)assert.ok(costly.trades[k].net/costly.trades[k].quantity<t.net/t.quantity,`${v.id} ${t.side>0?'buy':'sell'}: spread lowers result`);});
 }
 assert.ok(Object.values(counts).every(n=>n>0),`Fixture exercises every variant: ${JSON.stringify(counts)}`);
 // Mirror image: sells are the exact reflection of buys.
 const mirror=bars.map(b=>({...b,open:300-b.open,close:300-b.close,high:300-b.low,low:300-b.high}));
 const r1=v4.v4Variants.find(v=>v.id==='R1-E0X0'),direct=v4.v4Signals(bars,r1,'both'),reflected=v4.v4Signals(mirror,r1,'both');
 assert.ok(direct.filter((s,i)=>s!==-reflected[i]).length<=2,'Reflection swaps buys and sells');
 assert.ok(direct.includes(1)&&direct.includes(-1));
 // Handmade R1 trade: close below band with RSI ≤ 30, re-entry, exit after the mean is reclaimed.
 const flat=Array.from({length:900},(_,i)=>({time:start+i*step,open:100,close:100+(i%2?.05:-.05),high:100.3,low:99.7,volume:1}));
 for(let k=0;k<6;k++){const p=99.6-k*.5;flat[840+k]={...flat[840+k],open:p+.5,close:p,high:p+.6,low:p-.1};}
 flat[846]={...flat[846],open:96.9,close:98.9,high:99,low:96.8};
 for(let k=847;k<900;k++)flat[k]={...flat[k],open:99+(k-847)*.2,close:99.2+(k-847)*.2,high:99.4+(k-847)*.2,low:98.9+(k-847)*.2};
 const sig=v4.v4Signals(flat,r1,'long');assert.equal(sig[846],1,'Re-entry candle signals a buy');
 const one=v4.runV4(flat,{...options(r1),from:flat[750].time,to:flat[890].time,sides:'long'});
 assert.equal(one.trades[0].entryTime,flat[847].time);assert.equal(one.trades[0].reason,'Média de 20');assert.ok(one.trades[0].net>0);
 // Signals never cross a source gap.
 const gapped=flat.filter((_,i)=>i!==847);
 assert.equal(v4.runV4(gapped,{...options(r1),from:flat[750].time,to:flat[890].time,sides:'long'}).trades.filter(t=>t.signalTime===flat[846].time).length,0);
 assert.equal(v4.missingHours(gapped,flat[750].time,flat[890].time,'24x7'),1);
 const friday=Date.UTC(2024,0,5,20),weekend=Array.from({length:80},(_,i)=>({time:friday-10*step+i*step,open:1,close:1,high:1,low:1,volume:0})).filter(b=>b.time<friday||b.time>=friday+51*step);
 assert.equal(v4.missingHours(weekend,weekend[0].time,weekend.at(-1).time+step,'fx'),0,'FX weekly closure is not missing data');
 assert.equal(v4.missingHours(weekend,weekend[0].time,weekend.at(-1).time+step,'24x7'),51);
 assert.equal(v4.trailingRank([1,2,3,4,5,2.5],5,5),.4);assert.equal(v4.trailingRank([1,2,3,4,5,2.5],4,4),1);
 assert.equal(v4.trailingRank([null,2,3,4,5,2.5],5,5),null);
 assert.throws(()=>v4.runV4(bars,{...options(r1),variant:{...r1,stopAtr:1}}),'Only frozen variants run');
 assert.ok(Math.abs(v4.tStatistic([1,2,3])-2*Math.sqrt(3))<1e-9);
 console.log(`V4: causal R1/V1 signals and fills, cost sign, reflection, gaps, FX closure and frozen variants checked; fixture trades ${JSON.stringify(counts)}.`);
}finally{await m.cleanup();}
