import {atr,ema,rsi,type Candle} from './domain';
export type IndicatorReading={id:string;name:string;values:number[]|null;labels?:string[];unit:'price'|'number'|'percent';description:string;minimum:number};
export function macd(values:number[],fast=12,slow=26,signal=9){
 const f=ema(values,fast),s=ema(values,slow),line=values.map((_,i)=>f[i]===null||s[i]===null?null:f[i]!-s[i]!);
 const compact=line.filter((n):n is number=>n!==null),signalValues=ema(compact,signal),current=line.at(-1)??null,sig=signalValues.at(-1)??null;
 return current===null||sig===null?null:{line:current,signal:sig,histogram:current-sig};
}
export function bands(values:number[],period=20,multiple=2){
 if(values.length<period)return null;const sample=values.slice(-period),mean=sample.reduce((a,b)=>a+b,0)/period,sd=Math.sqrt(sample.reduce((a,b)=>a+(b-mean)**2,0)/period);
 return {lower:mean-multiple*sd,middle:mean,upper:mean+multiple*sd};
}
/** The channel excludes the decision candle to avoid a moving breakout threshold. */
export function channelBefore(bars:Candle[],index:number,period=20){
 if(index<period)return null;const sample=bars.slice(index-period,index);return {upper:Math.max(...sample.map(b=>b.high)),lower:Math.min(...sample.map(b=>b.low))};
}
export function indicatorReadings(bars:Candle[]):IndicatorReading[]{
 const prices=bars.map(b=>b.close),last=prices.at(-1),range=atr(bars).at(-1)??null,osc=rsi(bars),bb=bands(prices),dc=channelBefore(bars,bars.length-1),m=macd(prices);
 const scalar=(value:number|null|undefined)=>value==null||!Number.isFinite(value)?null:[value];
 return [
  ...[20,50,200].map(period=>({id:`ema${period}`,name:`EMA ${period}`,values:scalar(ema(prices,period).at(-1)),unit:'price' as const,description:'Média exponencial do fechamento',minimum:period})),
  {id:'sma20',name:'SMA 20',values:scalar(bb?.middle),unit:'price',description:'Média simples dos fechamentos',minimum:20},
  {id:'rsi14',name:'RSI 14',values:scalar(osc),unit:'number',description:'Momento · suavização de Wilder',minimum:15},
  {id:'atr14',name:'ATR 14',values:scalar(range),unit:'price',description:'Amplitude · suavização de Wilder',minimum:14},
  {id:'atrp14',name:'ATR % 14',values:scalar(range!==null&&last?range/last*100:null),unit:'percent',description:'ATR em relação ao fechamento',minimum:14},
  {id:'macd',name:'MACD 12/26/9',values:m?[m.line,m.signal,m.histogram]:null,labels:['Linha','Sinal','Histograma'],unit:'number',description:'EMA rápida − lenta e sinal',minimum:34},
  {id:'bollinger',name:'Bollinger 20 · 2σ',values:bb?[bb.lower,bb.middle,bb.upper]:null,labels:['Inferior','Média','Superior'],unit:'price',description:'Desvio padrão populacional',minimum:20},
  {id:'donchian',name:'Donchian 20',values:dc?[dc.lower,dc.upper]:null,labels:['Mínima','Máxima'],unit:'price',description:'Extremos dos 20 candles anteriores',minimum:21},
 ];
}
export function closedCandles<T extends Candle>(bars:T[],interval:number,now=Date.now()):T[]{return bars.filter(b=>b.time+interval*60000<=now);}
export function countGaps(bars:Candle[],interval:number){return bars.reduce((sum,b,i)=>sum+(i?Math.max(0,Math.round((b.time-bars[i-1].time)/(interval*60000))-1):0),0);}
