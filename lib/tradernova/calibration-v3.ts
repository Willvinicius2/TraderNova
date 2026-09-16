import {atr,ema,type Candle} from './domain';
import {candidateSignals,rsiSeries,type CandidateId} from './research';
import type {StrategyParameters} from './calibration';

export function v3Variants(candidateId:CandidateId):StrategyParameters[]{
 const exits=[{stopAtr:2.5,reward:3,hold:72,trailAtr:0,breakEvenR:0},{stopAtr:2.5,reward:4,hold:168,trailAtr:3,breakEvenR:0},{stopAtr:3,reward:3,hold:120,trailAtr:3.5,breakEvenR:1.5}];
 return (['h4-confirmed','h4-reclaim'] as const).flatMap((entryProfile,e)=>exits.map((exit,x)=>({id:`${candidateId}-V3-E${e}X${x}`,candidateId,entryProfile,...exit,trendFilter:true,minStopFraction:.0072,trailActivationR:1,cooldownBars:6})));
}

/** Map each H1 close only to H4 candles already completed at that instant. */
export function higherTrend(bars:Candle[]):boolean[]{
 const four=4*3600000,groups:{time:number;close:number}[]=[],index:number[]=[];
 let bucket=-1,count=0,lastTime=-1;
 for(const b of bars){
  const slot=Math.floor(b.time/four)*four;
  if(slot!==bucket){bucket=slot;count=0;lastTime=-1;}
  if((count===0&&b.time===slot)||(count>0&&b.time-lastTime===3600000)){count++;lastTime=b.time;}else{count=0;lastTime=-1;}
  if(count===4&&b.time+3600000===slot+four)groups.push({time:slot+four,close:b.close});
  index.push(groups.length-1);
 }
 const close=groups.map(b=>b.close),fast=ema(close,20),slow=ema(close,50);
 return index.map(i=>i>=52&&close[i]>slow[i]!&&fast[i]!>slow[i]!&&slow[i]!>slow[i-3]!);
}

export function v3Signals(bars:Candle[],p:StrategyParameters):(1|0)[]{
 const close=bars.map(b=>b.close),e20=ema(close,20),e50=ema(close,50),e200=ema(close,200),range=atr(bars),strength=rsiSeries(bars),h4=higherTrend(bars),original=candidateSignals(bars,p.candidateId);
 return bars.map((b,i)=>{
  if(i<223||b.time-bars[i-1].time!==3600000||!h4[i]||b.close<=e200[i]!||e50[i]!<=e200[i]!||e200[i]!<=e200[i-24]!||(range[i]??0)*p.stopAtr/b.close<p.minStopFraction)return 0;
  let signal=original[i]===1;
  if(p.entryProfile==='h4-reclaim'){
   const previous=bars[i-1];
   if(p.candidateId==='T1')signal=previous.close<=e20[i-1]!&&b.close>e20[i]!&&e20[i]!>e50[i]!&&b.close>b.open;
   if(p.candidateId==='T2')signal=previous.close<=e20[i-1]!&&b.low<=e20[i]!&&b.close>e20[i]!&&b.close>b.open&&e20[i]!>e50[i]!&&strength[i]!>=45&&strength[i]!<=65;
   if(p.candidateId==='T3'){
    const level=Math.max(...bars.slice(i-21,i-1).map(b=>b.high));
    signal=previous.close>level&&Math.abs(b.low-level)<=.5*(range[i-1]??0)&&b.close>level&&b.close>b.open;
   }
  }
  return signal?1:0;
 });
}

/** Current close is known. Returned stop is effective on the next candle/quote. */
export function nextProtectedStop(p:StrategyParameters,oldStop:number,entryReference:number,initialDistance:number,peakClose:number,close:number,range:number,breakEvenPrice:number){
 let next=oldStop;
 if(p.trailAtr&&peakClose>=entryReference+initialDistance*(p.trailActivationR??1))next=Math.max(next,peakClose-p.trailAtr*range);
 if(p.breakEvenR&&peakClose>=entryReference+initialDistance*p.breakEvenR)next=Math.max(next,breakEvenPrice);
 return Math.max(oldStop,Math.min(next,close));
}
