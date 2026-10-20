import {atr,ema,type Candle} from './domain';
import {rsiSeries} from './research';

/** Protocol v4 families. Rules are frozen in research/v4-protocol.json before any result. */
export type V4FamilyId='R1'|'V1';
export type V4Variant={id:string;familyId:V4FamilyId;entry:'E0'|'E1';stopAtr:number;reward:number|null;exitAtMean:boolean;hold:number;trailAtr:number;trailActivationR:number;cooldownBars:number};
export const v4Families=[
 {id:'R1',name:'Reversão à média Bollinger + RSI',family:'Reversão',rules:'Compra: o candle anterior fechou abaixo da banda inferior (20, 2σ) com RSI 14 ≤ 30 e o candle atual fecha de volta dentro da banda, acima da abertura. Venda simétrica (banda superior, RSI ≥ 70). E1 exige o lado da EMA 200. Saída na abertura seguinte ao primeiro fechamento além da média de 20, stop ATR ou limite de tempo.'},
 {id:'V1',name:'Compressão de volatilidade + H4',family:'Regime',rules:'Regime de compressão: largura de Bollinger do candle anterior no quintil inferior das 500 larguras H1 anteriores. Compra: fechamento acima da banda superior com tendência H4 concluída de alta (EMA 20 > EMA 50, fechamento > EMA 50, EMA 50 subindo). Venda simétrica. E1 exige também ATR% do candle anterior abaixo da mediana das 500 anteriores. Opera somente nesse regime.'},
] as const;
const cooldownBars=6;
export const v4Variants:V4Variant[]=[
 ...(['E0','E1'] as const).flatMap(entry=>[{x:'X0',stopAtr:2,hold:24},{x:'X1',stopAtr:3,hold:48}].map(({x,...exit})=>({id:`R1-${entry}${x}`,familyId:'R1' as const,entry,...exit,reward:null,exitAtMean:true,trailAtr:0,trailActivationR:0,cooldownBars}))),
 ...(['E0','E1'] as const).flatMap(entry=>[{x:'X0',stopAtr:2,reward:3,hold:48,trailAtr:0,trailActivationR:0},{x:'X1',stopAtr:2,reward:5,hold:120,trailAtr:3,trailActivationR:1}].map(({x,...exit})=>({id:`V1-${entry}${x}`,familyId:'V1' as const,entry,...exit,exitAtMean:false,cooldownBars}))),
];
export const v4Warmup=700;
const hour=3600000;

/** Population-σ Bollinger per bar, same definition as indicators.bands. */
export function bollingerSeries(close:number[],period=20,multiple=2){
 return close.map((_,i)=>{
  if(i<period-1)return null;
  const sample=close.slice(i-period+1,i+1),mean=sample.reduce((a,b)=>a+b,0)/period,sd=Math.sqrt(sample.reduce((a,b)=>a+(b-mean)**2,0)/period);
  return {lower:mean-multiple*sd,middle:mean,upper:mean+multiple*sd};
 });
}
/** Share of the `lookback` previous values strictly below values[i]; null until all are known. */
export function trailingRank(values:(number|null)[],i:number,lookback=500){
 if(i<lookback||values[i]==null)return null;
 let below=0;
 for(let j=i-lookback;j<i;j++){const v=values[j];if(v==null)return null;if(v<values[i]!)below++;}
 return below/lookback;
}
/** Symmetric H4 trend from complete hourly groups; each H1 bar only sees H4 candles already closed. */
export function h4Trend(bars:Candle[]):(1|-1|0)[]{
 const four=4*hour,groups:number[]=[],index:number[]=[];
 let bucket=-1,count=0,lastTime=-1;
 for(const b of bars){
  const slot=Math.floor(b.time/four)*four;
  if(slot!==bucket){bucket=slot;count=0;lastTime=-1;}
  if((count===0&&b.time===slot)||(count>0&&b.time-lastTime===hour)){count++;lastTime=b.time;}else{count=0;lastTime=-1;}
  if(count===4&&b.time+hour===slot+four)groups.push(b.close);
  index.push(groups.length-1);
 }
 const fast=ema(groups,20),slow=ema(groups,50);
 return index.map(i=>i<52?0:groups[i]>slow[i]!&&fast[i]!>slow[i]!&&slow[i]!>slow[i-3]!?1:groups[i]<slow[i]!&&fast[i]!<slow[i]!&&slow[i]!<slow[i-3]!?-1:0);
}

/** Signals on closed H1 candles; the caller enters at the next open. */
export function v4Signals(bars:Candle[],v:V4Variant,sides:'long'|'both'):(1|-1|0)[]{
 const close=bars.map(b=>b.close),bb=bollingerSeries(close),strength=rsiSeries(bars),e200=ema(close,200),range=atr(bars);
 const width=bb.map(b=>b&&b.middle>0?(b.upper-b.lower)/b.middle:null),atrPct=range.map((r,i)=>r==null?null:r/close[i]);
 const trend=v.familyId==='V1'?h4Trend(bars):[];
 return bars.map((b,i)=>{
  if(i<v4Warmup||b.time-bars[i-1].time!==hour)return 0;
  const band=bb[i]!,prior=bb[i-1]!,previous=bars[i-1];
  let side:1|-1|0=0;
  if(v.familyId==='R1'){
   if(previous.close<prior.lower&&strength[i-1]!<=30&&b.close>band.lower&&b.close>b.open&&(v.entry==='E0'||b.close>e200[i]!))side=1;
   else if(previous.close>prior.upper&&strength[i-1]!>=70&&b.close<band.upper&&b.close<b.open&&(v.entry==='E0'||b.close<e200[i]!))side=-1;
  }else{
   const compressed=(trailingRank(width,i-1)??1)<=.2&&(v.entry==='E0'||(trailingRank(atrPct,i-1)??1)<.5);
   if(compressed&&b.close>band.upper&&trend[i]===1)side=1;
   else if(compressed&&b.close<band.lower&&trend[i]===-1)side=-1;
  }
  return sides==='long'&&side===-1?0:side;
 });
}

export type V4Options={variant:V4Variant;from:number;to:number;initialCapital:number;riskPct:number;feeBps:number;slippageBps:number;spread:number;sides:'long'|'both';maxLeverage:number;minStopCostMultiple:number};
export type V4Trade={side:1|-1;signalTime:number;entryTime:number;exitCandleTime:number;entry:number;exit:number;quantity:number;stop:number;target:number|null;fees:number;net:number;returnOnEquityPct:number;reason:string};
export type V4Result={options:V4Options;trades:V4Trade[];net:number;returnPct:number;maxDrawdownPct:number;profitFactor:number|null;winRate:number|null;exposurePct:number;bars:number;missingHours:number;validated:false};

/** Gaps are kept, never interpolated. Hours inside an FX weekly closure or 25/12, 01/01 are not missing. */
export function missingHours(bars:Candle[],from:number,to:number,calendar:'24x7'|'fx'){
 const closed=(t:number)=>{const d=new Date(t),day=d.getUTCDay(),h=d.getUTCHours(),md=`${d.getUTCMonth()+1}-${d.getUTCDate()}`;return calendar==='fx'&&(day===6||(day===5&&h>=20)||(day===0&&h<23)||md==='12-25'||md==='1-1');};
 const inside=bars.filter(b=>b.time>=from&&b.time<to);let missing=0;
 for(let t=from,k=0;t<to;t+=hour){while(k<inside.length&&inside[k].time<t)k++;if(!(inside[k]?.time===t)&&!closed(t))missing++;}
 return missing;
}

/** One position at a time, next-open fills, stop wins ambiguous candles, adverse gaps fill at the open.
 * Slippage (bps) and half the spread (price units) worsen every fill; fees apply to both notionals.
 * Drawdown is measured on closes including estimated exit costs, not intrabar.
 */
export function runV4(bars:Candle[],o:V4Options,calendar:'24x7'|'fx'='24x7'):V4Result{
 if(bars.some((b,i)=>![b.time,b.open,b.high,b.low,b.close].every(Number.isFinite)||b.low<=0||b.high<Math.max(b.open,b.close)||b.low>Math.min(b.open,b.close)||b.time%hour!==0||(i>0&&b.time<=bars[i-1].time)))throw new Error('Candle inválido.');
 const {variant:v,from,to,initialCapital,riskPct,feeBps,slippageBps,spread,sides,maxLeverage,minStopCostMultiple}=o;
 if(!v4Variants.some(c=>JSON.stringify(c)===JSON.stringify(v))||![from,to,initialCapital,riskPct,feeBps,slippageBps,spread,maxLeverage,minStopCostMultiple].every(Number.isFinite)||from>=to||from%hour||to%hour||riskPct<=0||riskPct>1||spread<0||maxLeverage<=0)throw new Error('Parâmetros v4 inválidos.');
 const first=bars.findIndex(b=>b.time>=from),end=bars.findIndex(b=>b.time>=to),last=(end<0?bars.length:end)-1;
 if(first<v4Warmup||last<first||bars[last].time+hour<to-7*24*hour)throw new Error('Janela incompleta ou sem aquecimento suficiente.');
 const signals=v4Signals(bars,v,sides),ranges=atr(bars),mean=bollingerSeries(bars.map(b=>b.close)),fee=feeBps/10000,slip=slippageBps/10000;
 const fill=(raw:number,side:number,opening:boolean)=>{const worse=opening?side:-side;return raw*(1+worse*slip)+worse*spread/2;};
 const trades:V4Trade[]=[];let equity=initialCapital,peak=equity,dd=0,exposed=0,cooldownUntil=0;
 const mark=(value:number)=>{peak=Math.max(peak,value);dd=Math.max(dd,100*(peak-value)/peak);};
 for(let i=first;i<=last;){
  const side=signals[i-1],contiguous=bars[i].time-bars[i-1].time===hour;
  if(i===first||!side||!contiguous||bars[i].time<cooldownUntil){mark(equity);i++;continue;}
  const raw=bars[i].open,distance=(ranges[i-1]??0)*v.stopAtr,entry=fill(raw,side,true),stop=raw-side*distance,target=v.reward===null?null:raw+side*v.reward*distance;
  const roundTrip=2*(raw*(slip+fee))+spread;
  if(!(distance>0)||stop<=0||distance<minStopCostMultiple*roundTrip){mark(equity);i++;continue;}
  const unitRisk=Math.abs(entry-fill(stop,side,false))+fee*(entry+stop),before=equity;
  const quantity=Math.min(before*riskPct/100/unitRisk,before*maxLeverage/(entry*(1+fee))),entryFee=quantity*entry*fee;
  let j=i,rawExit=raw,reason='Fim da janela',active=stop,best=raw,leaveAtOpen=false;
  for(;j<=last;j++){
   const b=bars[j];exposed++;
   if(leaveAtOpen){rawExit=b.open;reason='Média de 20';break;}
   const favourable=(p:number)=>side===1?p>=target!:p<=target!,stopHit=side===1?b.low<=active:b.high>=active;
   if(target!==null&&favourable(b.open)){rawExit=target;reason='Alvo · gap de abertura';break;}
   if(stopHit){rawExit=side===1?Math.min(b.open,active):Math.max(b.open,active);reason=target!==null&&favourable(side===1?b.high:b.low)?'Stop · candle ambíguo':active!==stop?'Stop protegido':'Stop';break;}
   if(target!==null&&favourable(side===1?b.high:b.low)){rawExit=target;reason='Alvo';break;}
   rawExit=b.close;
   if(b.time-bars[i].time+hour>=v.hold*hour){reason='Limite de tempo';break;}
   if(j===last)break;
   mark(before+quantity*side*(fill(b.close,side,false)-entry)-entryFee-quantity*b.close*fee);
   if(v.exitAtMean&&(b.close-mean[j]!.middle)*side>=0)leaveAtOpen=true;
   best=side===1?Math.max(best,b.close):Math.min(best,b.close);
   if(v.trailAtr&&(best-raw)*side>=v.trailActivationR*distance){
    const trail=best-side*v.trailAtr*(ranges[j]??0),capped=side===1?Math.min(trail,b.close):Math.max(trail,b.close);
    active=side===1?Math.max(active,capped):Math.min(active,capped);
   }
  }
  j=Math.min(j,last);
  const exit=fill(rawExit,side,false),exitFee=quantity*exit*fee,net=quantity*side*(exit-entry)-entryFee-exitFee;
  equity+=net;
  trades.push({side,signalTime:bars[i-1].time,entryTime:bars[i].time,exitCandleTime:bars[j].time,entry,exit,quantity,stop,target,fees:entryFee+exitFee,net,returnOnEquityPct:100*net/before,reason});
  cooldownUntil=bars[j].time+hour*(1+v.cooldownBars);
  mark(equity);i=j+1;
 }
 const gains=trades.reduce((s,t)=>s+Math.max(0,t.net),0),losses=-trades.reduce((s,t)=>s+Math.min(0,t.net),0);
 return {options:o,trades,net:equity-initialCapital,returnPct:100*(equity/initialCapital-1),maxDrawdownPct:dd,profitFactor:losses?gains/losses:null,winRate:trades.length?100*trades.filter(t=>t.net>0).length/trades.length:null,exposurePct:100*exposed/(last-first+1),bars:last-first+1,missingHours:missingHours(bars,from,to,calendar),validated:false};
}

/** One-sample t statistic of per-trade return on equity. */
export function tStatistic(returns:number[]){
 const n=returns.length;if(n<2)return null;
 const m=returns.reduce((a,b)=>a+b,0)/n,sd=Math.sqrt(returns.reduce((a,b)=>a+(b-m)**2,0)/(n-1));
 return sd>0?m/(sd/Math.sqrt(n)):null;
}
