import type {Candle} from './domain';
import {missingHours,runV4,v4Variants,type V4Options,type V4Result} from './research-v4';

// Prospective forward test (#31): the frozen variant replayed only on candles that closed after it was frozen.
export const forwardCriteria={minDays:30,minTrades:10};
export type ForwardOptions=Omit<V4Options,'variant'|'from'|'to'>&{variantId:string;startedAt:number;now:number;worstValidationDrawdownPct:number;calendar:'24x7'|'fx'};
export type ForwardReport={variantId:string;startedAt:number;evaluatedUntil:number;days:number;result:V4Result;missingHours:number;reasons:string[];complete:boolean;passed:boolean;validated:false};

export function forwardV4(bars:Candle[],o:ForwardOptions):ForwardReport{
 const hour=3600000,variant=v4Variants.find(v=>v.id===o.variantId);
 if(!variant)throw new Error('Variante v4 desconhecida.');
 if(!Number.isFinite(o.startedAt)||!Number.isFinite(o.now)||!(o.worstValidationDrawdownPct>0))throw new Error('Parâmetros do forward test inválidos.');
 const from=Math.ceil(o.startedAt/hour)*hour,closed=bars.filter(b=>b.time+hour<=o.now),until=closed.length?closed.at(-1)!.time+hour:from;
 if(until-from<hour*24)throw new Error('Menos de um dia de candles fechados após o início.');
 const {worstValidationDrawdownPct,calendar}=o;
 const result=runV4(closed,{variant,from,to:until,initialCapital:o.initialCapital,riskPct:o.riskPct,feeBps:o.feeBps,slippageBps:o.slippageBps,spread:o.spread,sides:o.sides,maxLeverage:o.maxLeverage,minStopCostMultiple:o.minStopCostMultiple},calendar),days=(until-from)/(24*hour),gaps=missingHours(closed,from,until,calendar);
 const reasons=[
  days<forwardCriteria.minDays&&`${days.toFixed(1)} de ${forwardCriteria.minDays} dias`,
  result.trades.length<forwardCriteria.minTrades&&`${result.trades.length} de ${forwardCriteria.minTrades} operações`,
  result.maxDrawdownPct>worstValidationDrawdownPct&&`drawdown ${result.maxDrawdownPct.toFixed(2)}% acima do pior da validação (${worstValidationDrawdownPct.toFixed(2)}%)`,
  gaps/((until-from)/hour)>(calendar==='fx'?.03:.005)&&`${gaps} horas sem candle, acima do limite do protocolo`,
 ].filter((r):r is string=>Boolean(r));
 return {variantId:o.variantId,startedAt:from,evaluatedUntil:until,days,result,missingHours:gaps,reasons,complete:days>=forwardCriteria.minDays&&result.trades.length>=forwardCriteria.minTrades,passed:reasons.length===0,validated:false};
}
