import {atr,ema,type Candle} from './domain';
import {candidateSignals,researchCandidates,rsiSeries,type CandidateId} from './research';
export type StrategyParameters={id:string;candidateId:CandidateId;entryProfile:'original'|'trend-cost'|'patient-trend-cost';stopAtr:number;hold:number;reward:number;trendFilter:boolean;minStopFraction:number};
export function calibrationVariants(candidateId:CandidateId):StrategyParameters[]{
 const c=researchCandidates.find(c=>c.id===candidateId)!;
 const exits=[{stopAtr:c.stopAtr,hold:c.hold,reward:2},{stopAtr:2,hold:24,reward:2},{stopAtr:3,hold:72,reward:3}];
 return (['original','trend-cost','patient-trend-cost'] as const).flatMap((entryProfile,e)=>exits.map((exit,x)=>({id:`${candidateId}-E${e}X${x}`,candidateId,entryProfile,...exit,trendFilter:e>0,minStopFraction:e>0?.0072:0})));
}
export function originalParameters(candidateId:CandidateId){return calibrationVariants(candidateId)[0];}
export function presetDescription(p:StrategyParameters){return `Stop ${p.stopAtr} × ATR · alvo ${p.reward}R · até ${p.hold} horas${p.trendFilter?' · tendência EMA 200 e filtro de custos':''}`;}
export function validParameters(p:StrategyParameters,candidateId:CandidateId){return calibrationVariants(candidateId).some(v=>Object.keys(v).every(k=>v[k as keyof StrategyParameters]===p[k as keyof StrategyParameters]));}
export function calibratedSignals(bars:Candle[],p:StrategyParameters):(1|0)[]{
 const values=bars.map(b=>b.close),e20=ema(values,20),e50=ema(values,50),e200=ema(values,200),ranges=atr(bars),rsi=rsiSeries(bars),original=candidateSignals(bars,p.candidateId);
 return bars.map((b,i)=>{
  if(i<53)return 0;
  let signal=original[i]===1;
  if(p.entryProfile==='patient-trend-cost'){
   if(p.candidateId==='T1')signal=e20[i-1]!<=e50[i-1]!&&e20[i]!>e50[i]!;
   if(p.candidateId==='T2')signal=signal&&rsi[i]!<=60;
   if(p.candidateId==='T3')signal=i>=55&&b.close>Math.max(...bars.slice(i-55,i).map(b=>b.high))&&b.close>e50[i]!;
  }
  if(!signal)return 0;
  if(p.trendFilter&&(i<223||b.close<=e200[i]!||e50[i]!<=e200[i]!||e200[i]!<=e200[i-24]!))return 0;
  if((ranges[i]??0)*p.stopAtr/b.close<p.minStopFraction)return 0;
  return 1;
 });
}
