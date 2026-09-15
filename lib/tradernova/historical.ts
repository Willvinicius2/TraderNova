import {atr,type Candle} from './domain';
import {candidateSignals,researchCandidates,type CandidateId} from './research';
import {calibratedSignals,validParameters,type StrategyParameters} from './calibration';

export type HistoricalOptions={candidateId:CandidateId;interval:number;from:number;to:number;initialCapital:number;riskPct:number;feeBps:number;slippageBps:number;parameters?:StrategyParameters};
export type HistoricalTrade={signalTime:number;entryTime:number;exitCandleTime:number;entry:number;exit:number;quantity:number;stop:number;target:number;fees:number;net:number;returnOnEquityPct:number;reason:string};
export type HistoricalResult={options:HistoricalOptions;trades:HistoricalTrade[];curve:{time:number;equity:number}[];net:number;returnPct:number;maxDrawdownPct:number;profitFactor:number|null;winRate:number|null;expectancy:number|null;fees:number;exposurePct:number;buyHoldReturnPct:number;endCapital:number;bars:number;validated:false};

/** Reject incomplete or mismatched data; never invent missing candles. */
export function validateHistory(bars:Candle[],interval:number){
 const step=interval*60000;
 if(![15,60].includes(interval)||bars.length<260)throw new Error('Histórico insuficiente ou período inválido.');
 for(let i=0;i<bars.length;i++){
  const b=bars[i];
  if(![b.time,b.open,b.high,b.low,b.close,b.volume].every(Number.isFinite)||b.time%step!==0||b.low<=0||b.high<Math.max(b.open,b.close)||b.low>Math.min(b.open,b.close)||b.volume<0||(i>0&&b.time-bars[i-1].time!==step))throw new Error(`Candle inválido ou lacuna no índice ${i}.`);
 }
}

/** One spot position, long only, next-open execution, fractional units, no leverage.
 * Slippage worsens both fills; fees apply to both actual notionals. Candle-close
 * equity includes an estimated liquidation fee/slippage, not intrabar drawdown.
 */
export function runHistorical(bars:Candle[],options:HistoricalOptions):HistoricalResult{
 validateHistory(bars,options.interval);
 const c=researchCandidates.find(c=>c.id===options.candidateId);
 const parameters=options.parameters;
 if(parameters&&(!validParameters(parameters,options.candidateId)||options.interval!==60))throw new Error('Preset calibrado inválido.');
 const {from,to,interval,initialCapital,riskPct,feeBps,slippageBps}=options,step=interval*60000;
 if(!c||![from,to,initialCapital,riskPct,feeBps,slippageBps].every(Number.isFinite)||from>=to||from%step!==0||to%step!==0||initialCapital<=0||riskPct<=0||riskPct>1||feeBps<0||feeBps>100||slippageBps<0||slippageBps>100)throw new Error('Parâmetros históricos inválidos.');
 const first=bars.findIndex(b=>b.time===from),last=bars.findIndex(b=>b.time===to-step);
 if(first<(parameters?.trendFilter?600:200)||last<first||to>Date.now())throw new Error('Janela incompleta, futura ou sem aquecimento suficiente.');
 const signals=parameters?calibratedSignals(bars,parameters):candidateSignals(bars,c.id),ranges=atr(bars),fee=feeBps/10000,slip=slippageBps/10000;
 const stopAtr=parameters?.stopAtr??c.stopAtr,reward=parameters?.reward??2,hold=parameters?.hold??c.hold;
 const trades:HistoricalTrade[]=[],curve=[{time:from,equity:initialCapital}];
 let cash=initialCapital,peak=initialCapital,dd=0,exposed=0;
 function mark(time:number,equity:number){peak=Math.max(peak,equity);dd=Math.max(dd,100*(peak-equity)/peak);curve.push({time,equity});}
 for(let i=first;i<=last;){
  // The first signal must itself close inside this evaluation window.
  if(i===first||signals[i-1]!==1){mark(bars[i].time+step,cash);i++;continue;}
  const rawEntry=bars[i].open,distance=(ranges[i-1]??0)*stopAtr,stop=rawEntry-distance,target=rawEntry+reward*distance;
  if(distance<=0||stop<=0){mark(bars[i].time+step,cash);i++;continue;}
  const entry=rawEntry*(1+slip),stopFill=stop*(1-slip),unitRisk=entry-stopFill+fee*(entry+stopFill);
  const before=cash,quantity=Math.min(before*riskPct/100/unitRisk,before/(entry*(1+fee))),entryFee=quantity*entry*fee;
  cash-=quantity*entry+entryFee;
  let j=i,rawExit=entry,reason='Fim da janela';
  for(;j<=last;j++){
   const b=bars[j],stopHit=b.low<=stop,targetHit=b.high>=target;
   exposed++;
   if(b.open>=target){rawExit=target;reason='Alvo · gap de abertura';break;}
   if(stopHit){rawExit=Math.min(b.open,stop);reason=targetHit?'Stop · candle ambíguo':'Stop';break;}
   if(targetHit){rawExit=target;reason='Alvo';break;}
   rawExit=b.close;
   if(j-i+1>=hold){reason='Limite de candles';break;}
   if(j===last)break;
   mark(b.time+step,cash+quantity*b.close*(1-slip)*(1-fee));
  }
  const exit=rawExit*(1-slip),exitFee=quantity*exit*fee;
  cash+=quantity*exit-exitFee;
  const net=cash-before;
  trades.push({signalTime:bars[i-1].time,entryTime:bars[i].time,exitCandleTime:bars[j].time,entry,exit,quantity,stop,target,fees:entryFee+exitFee,net,returnOnEquityPct:100*net/before,reason});
  mark(bars[j].time+step,cash);i=j+1;
 }
 const gains=trades.reduce((s,t)=>s+Math.max(0,t.net),0),losses=-trades.reduce((s,t)=>s+Math.min(0,t.net),0);
 const buyQty=initialCapital/(bars[first].open*(1+slip)*(1+fee));
 return {options,trades,curve,net:cash-initialCapital,returnPct:100*(cash/initialCapital-1),maxDrawdownPct:dd,profitFactor:losses?gains/losses:null,winRate:trades.length?100*trades.filter(t=>t.net>0).length/trades.length:null,expectancy:trades.length?(cash-initialCapital)/trades.length:null,fees:trades.reduce((s,t)=>s+t.fees,0),exposurePct:100*exposed/(last-first+1),buyHoldReturnPct:100*(buyQty*bars[last].close*(1-slip)*(1-fee)/initialCapital-1),endCapital:cash,bars:last-first+1,validated:false};
}

export function screeningReasons(validation:HistoricalResult,final:HistoricalResult,stress:HistoricalResult):string[]{
 const reasons:string[]=[];
 for(const [name,r] of [['Validação',validation],['Avaliação final',final]] as const){
  if(r.trades.length<100)reasons.push(`${name}: menos de 100 operações`);
  if(r.net<=0)reasons.push(`${name}: resultado líquido não positivo`);
  if(r.profitFactor===null||r.profitFactor<1.2)reasons.push(`${name}: fator de lucro inferior a 1,20 ou indefinido`);
  if(r.maxDrawdownPct>15)reasons.push(`${name}: drawdown superior a 15%`);
 }
 if(stress.net<=0)reasons.push('Custos elevados: resultado final não positivo');
 return reasons;
}
