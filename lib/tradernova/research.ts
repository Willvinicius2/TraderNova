import {atr,ema,type Candle,type AssetId} from './domain';
import {channelBefore,countGaps} from './indicators';
export const researchCandidates=[
 {id:'T1',name:'Cruzamento EMA 9/21',family:'Tendência',summary:'Uma referência simples para comparar com estratégias mais complexas.',rules:'Compra quando EMA 9 cruza acima da EMA 21 no fechamento; venda no cruzamento inverso. Entrada somente na abertura seguinte.',stopAtr:1.5,hold:8,risks:'Pode sofrer entradas falsas e custos repetidos em mercado lateral.',references:[{name:'Fidelity · Médias móveis',url:'https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/ema'}]},
 {id:'T2',name:'Pullback EMA 20/50 + RSI',family:'Continuação',summary:'Testa uma retomada após retração dentro de uma tendência.',rules:'Compra: EMA 20 > EMA 50; EMA 50 acima do valor de 3 candles atrás; mínima toca EMA 20, fechamento acima dela e acima da abertura; RSI 14 entre 50 e 65. Venda simétrica, RSI entre 35 e 50. Entrada na abertura seguinte. Esta versão usa um único período; não equivale à hipótese S1 com filtro H1.',stopAtr:1.5,hold:12,risks:'Tendência pode terminar durante a retração. Regras e faixas de RSI são hipóteses locais, ainda sem otimização.',references:[{name:'Fidelity · EMA',url:'https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/ema'},{name:'Fidelity · RSI',url:'https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/RSI'}]},
 {id:'T3',name:'Rompimento Donchian 20',family:'Rompimento',summary:'Testa expansão além dos extremos conhecidos do mercado.',rules:'Compra: fechamento supera a máxima dos 20 candles anteriores e fica acima da EMA 50. Venda: fecha abaixo da mínima dos 20 anteriores e da EMA 50. O candle do sinal nunca participa do canal. Entrada na abertura seguinte.',stopAtr:2,hold:20,risks:'Rompimentos falsos e gaps podem superar o stop previsto. Não inclui confirmação por reteste.',references:[{name:'TradingView · Donchian',url:'https://www.tradingview.com/support/solutions/43000502253-donchian-channels-dc/'},{name:'Fidelity · ATR',url:'https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/atr'}]},
] as const;
export type CandidateId=typeof researchCandidates[number]['id'];
/** Wilder RSI in one pass; identical seeding to domain.rsi. */
export function rsiSeries(bars:Candle[],period=14):(number|null)[]{
 let gain=0,loss=0;
 return bars.map((b,i)=>{
  if(i===0)return null;
  const d=b.close-bars[i-1].close;
  if(i<=period){gain+=Math.max(d,0)/period;loss+=Math.max(-d,0)/period;}
  else{gain=(gain*(period-1)+Math.max(d,0))/period;loss=(loss*(period-1)+Math.max(-d,0))/period;}
  return i<period?null:loss===0?(gain===0?50:100):100-100/(1+gain/loss);
 });
}
export type ResearchTrade={signalTime:number;entryTime:number;exitTime:number;side:'Compra'|'Venda';entry:number;exit:number;stop:number;target:number;r:number;reason:string};
export type ResearchReport={version:1;id:string;createdAt:number;candidateId:CandidateId;assetId:AssetId;source:'kraken-spot'|'synthetic';interval:number;start:number;end:number;warmup:number;costR:number;reward:number;stopAtr:number;maxHold:number;bars:Candle[];trades:ResearchTrade[];curve:number[];netR:number;maxDrawdownR:number;winRate:number|null;profitFactor:number|null;expectancyR:number|null;sampleHash:string;validated:false};
export function candidateSignals(bars:Candle[],id:CandidateId):(1|-1|0)[]{
 const close=bars.map(b=>b.close),e9=ema(close,9),e21=ema(close,21),e20=ema(close,20),e50=ema(close,50),strengths=id==='T2'?rsiSeries(bars):[];
 return bars.map((b,i)=>{
  if(i<53)return 0;
  if(id==='T1')return e9[i-1]!<=e21[i-1]!&&e9[i]!>e21[i]!?1:e9[i-1]!>=e21[i-1]!&&e9[i]!<e21[i]!?-1:0;
  if(id==='T2'){
   const strength=strengths[i]!;
   if(e20[i]!>e50[i]!&&e50[i]!>e50[i-3]!&&b.low<=e20[i]!&&b.close>e20[i]!&&b.close>b.open&&strength>=50&&strength<=65)return 1;
   if(e20[i]!<e50[i]!&&e50[i]!<e50[i-3]!&&b.high>=e20[i]!&&b.close<e20[i]!&&b.close<b.open&&strength>=35&&strength<=50)return -1;
   return 0;
  }
  const c=channelBefore(bars,i)!;
  return b.close>c.upper&&b.close>e50[i]!?1:b.close<c.lower&&b.close<e50[i]!?-1:0;
 });
}
export function runResearch(bars:Candle[],options:{candidateId:CandidateId;assetId:AssetId;source:'kraken-spot'|'synthetic';interval:number;costR:number;reward:number;stopAtr:number;maxHold:number;asOf:number;sampleHash:string}):ResearchReport{
 const {candidateId,assetId,source,interval,costR,reward,stopAtr,maxHold,asOf,sampleHash}=options;
 if(!researchCandidates.some(s=>s.id===candidateId)||![1,5,15,60].includes(interval))throw new Error('Estratégia ou período inválido.');
 if(!Number.isFinite(costR)||costR<0||costR>2||!Number.isFinite(reward)||reward<1||reward>5||!Number.isFinite(stopAtr)||stopAtr<.5||stopAtr>5||!Number.isInteger(maxHold)||maxHold<1||maxHold>100)throw new Error('Revise custos, alvo, stop e duração.');
 if(!Number.isFinite(asOf)||!['kraken-spot','synthetic'].includes(source)||bars.length<260||bars.some((b,i)=>![b.time,b.open,b.high,b.low,b.close,b.volume].every(Number.isFinite)||b.low<=0||b.volume<0||b.high<Math.max(b.open,b.close)||b.low>Math.min(b.open,b.close)||b.time+interval*60000>asOf||b.time%(interval*60000)!==0||(i>0&&b.time<=bars[i-1].time)))throw new Error('São necessários ao menos 260 candles válidos e fechados.');
 if(countGaps(bars,interval))throw new Error('O histórico tem lacunas. Escolha outro período ou aguarde a recomposição dos dados.');
 const signals=candidateSignals(bars,candidateId),ranges=atr(bars),trades:ResearchTrade[]=[],curve=[0],warmup=200;let i=warmup;
 while(i<bars.length){
  const side=signals[i-1],distance=(ranges[i-1]??0)*stopAtr;if(!side||distance<=0){i++;continue;}
  const entry=bars[i].open,stop=entry-side*distance,target=entry+side*distance*reward;
  if(stop<=0||target<=0){i++;continue;}
  let exit=entry,j=i,reason='Fim da amostra';
  for(;j<bars.length;j++){
   const b=bars[j],stopHit=side===1?b.low<=stop:b.high>=stop,targetHit=side===1?b.high>=target:b.low<=target;
   if(side===1?b.open>=target:b.open<=target){exit=target;reason='Alvo · gap de abertura';break;}
   if(stopHit){exit=side===1?Math.min(b.open,stop):Math.max(b.open,stop);reason=targetHit?'Stop · candle ambíguo':'Stop';break;}
   if(targetHit){exit=target;reason='Alvo';break;}
   exit=b.close;if(j-i+1>=maxHold){reason='Limite de candles';break;}
  }
  j=Math.min(j,bars.length-1);const r=(exit-entry)*side/distance-costR;
  trades.push({signalTime:bars[i-1].time,entryTime:bars[i].time,exitTime:bars[j].time,side:side===1?'Compra':'Venda',entry,exit,stop,target,r,reason});curve.push(curve.at(-1)!+r);i=j+1;
 }
 let peak=0,dd=0;for(const v of curve){peak=Math.max(peak,v);dd=Math.max(dd,peak-v);}
 const gains=trades.reduce((s,t)=>s+Math.max(0,t.r),0),loss=-trades.reduce((s,t)=>s+Math.min(0,t.r),0),netR=curve.at(-1)!;
 return {version:1,id:crypto.randomUUID(),createdAt:Date.now(),candidateId,assetId,source,interval,start:bars[warmup].time,end:bars.at(-1)!.time+interval*60000,warmup,costR,reward,stopAtr,maxHold,bars,trades,curve,netR,maxDrawdownR:dd,winRate:trades.length?100*trades.filter(t=>t.r>0).length/trades.length:null,profitFactor:loss>0?gains/loss:null,expectancyR:trades.length?netR/trades.length:null,sampleHash,validated:false};
}
