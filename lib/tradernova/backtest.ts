import {atr,ema,type Candle} from './domain';
export type Trade = {entryTime:number;exitTime:number;direction:'Compra'|'Venda';entry:number;exit:number;r:number;reason:string};
export type TestReport = {id:string;assetId:string;createdAt:number;source:'synthetic';strategy:'BASELINE_EMA_CROSS_V1';bars:number;costR:number;reward:number;trades:Trade[];netR:number;maxDrawdownR:number;winRate:number|null;profitFactor:number|null;curve:number[]};
// Engineering baseline only. This is NOT S1, which also requires H1 context.
// Decisions use closed bars; execution is at the following open. All bars are synthetic.
export function backtest(bars:Candle[],assetId:string,costR=.1,reward=2):TestReport {
 if(bars.length<60||bars.some((b,i)=>![b.open,b.high,b.low,b.close,b.time].every(Number.isFinite)||b.high<Math.max(b.open,b.close)||b.low>Math.min(b.open,b.close)||(i>0&&b.time<=bars[i-1].time)))throw new Error('Candles inválidos ou insuficientes.');
 if(!Number.isFinite(costR)||costR<0||costR>2||!Number.isFinite(reward)||reward<1||reward>5)throw new Error('Custos ou alvo inválidos.');
 const closes=bars.map(b=>b.close),fast=ema(closes,9),slow=ema(closes,21),ranges=atr(bars);
 const trades:Trade[]=[],curve=[0];let i=23;
 while(i<bars.length-1){
 const prev=i-2,signal=i-1;
 const up=fast[prev]!<=slow[prev]!&&fast[signal]!>slow[signal]!;
 const down=fast[prev]!>=slow[prev]!&&fast[signal]!<slow[signal]!;
 const distance=ranges[signal]! * 1.5;
 if((!up&&!down)||!(distance>0)){i++;continue;}
 const side=up?1:-1,entry=bars[i].open,stop=entry-distance*side,target=entry+reward*distance*side;
 let exit=entry,exitIndex=i,reason='Fim da amostra';
 for(let j=i;j<bars.length;j++){
  const b=bars[j];exitIndex=j;
  // Stop wins ambiguous OHLC bars; gaps are executed at the worse opening price.
  const stopHit=up?b.low<=stop:b.high>=stop,targetHit=up?b.high>=target:b.low<=target;
  if(stopHit){exit=up?Math.min(b.open,stop):Math.max(b.open,stop);reason=targetHit?'Stop · barra ambígua':'Stop';break;}
  if(targetHit){exit=target;reason='Alvo';break;}
  exit=b.close;if(j-i>=7){reason='Tempo · 8 candles';break;}
 }
 const r=((exit-entry)*side)/distance-costR;
 trades.push({entryTime:bars[i].time,exitTime:bars[exitIndex].time,direction:up?'Compra':'Venda',entry,exit,r,reason});curve.push(curve[curve.length-1]+r);i=exitIndex+1;
 }
 let peak=0,dd=0;for(const p of curve){peak=Math.max(peak,p);dd=Math.max(dd,peak-p);}
 const gains=trades.reduce((a,t)=>a+Math.max(t.r,0),0),losses=-trades.reduce((a,t)=>a+Math.min(t.r,0),0);
 return {id:crypto.randomUUID(),assetId,createdAt:Date.now(),source:'synthetic',strategy:'BASELINE_EMA_CROSS_V1',bars:bars.length,costR,reward,trades,netR:curve[curve.length-1],maxDrawdownR:dd,winRate:trades.length?100*trades.filter(t=>t.r>0).length/trades.length:null,profitFactor:losses?gains/losses:null,curve};
}
