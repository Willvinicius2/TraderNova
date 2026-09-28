import type {Candle} from './domain';
import type {MarketEntry, Ticker} from './live-market';

export const pairRules = {id:'N1', window:120, entryZ:2, stopZ:3, maxHours:24, interval:60} as const;
export type PairModel = {alpha:number; beta:number; sigma:number; z:number; previousZ:number; side:1|-1|0};
export type PairSignal = {
 version:1; id:string; strategy:'N1'; mode:'research'|'demo'; validated:false;
 createdAt:number; expiresAt:number; candleTime:number; source:string;
 model:PairModel; ethEntry:number; btcEntry:number; entryZ:number;
 ethSide:'Compra'|'Venda'; btcSide:'Compra'|'Venda'; targetZ:0; stopZ:number;
 maxHoldUntil:number; decision?:'Revisado'|'Ignorado'; note?:string;
};
const step=3600000;
/** OLS is fit only to the 120 bars BEFORE i. Both crossing values use this same model. */
export function pairModel(btc:Candle[],eth:Candle[],i:number):PairModel|null {
 if(i<pairRules.window||!btc[i]||!eth[i])return null;
 const start=i-pairRules.window;
 for(let j=start;j<=i;j++)if(btc[j].time!==eth[j].time||!Number.isFinite(btc[j].close)||!Number.isFinite(eth[j].close)||btc[j].close<=0||eth[j].close<=0||(j>start&&btc[j].time-btc[j-1].time!==step))return null;
 const x=btc.slice(start,i).map(b=>Math.log(b.close)),y=eth.slice(start,i).map(b=>Math.log(b.close));
 const mx=x.reduce((a,b)=>a+b,0)/x.length,my=y.reduce((a,b)=>a+b,0)/y.length;
 const variance=x.reduce((v,n)=>v+(n-mx)**2,0);if(variance<1e-12)return null;
 const beta=x.reduce((v,n,j)=>v+(n-mx)*(y[j]-my),0)/variance,alpha=my-beta*mx;
 const sigma=Math.sqrt(y.reduce((v,n,j)=>v+(n-alpha-beta*x[j])**2,0)/(y.length-2));
 if(beta<.1||beta>5||sigma<1e-6||![alpha,beta,sigma].every(Number.isFinite))return null;
 const residual=(j:number)=>(Math.log(eth[j].close)-alpha-beta*Math.log(btc[j].close))/sigma;
 const z=residual(i),previousZ=residual(i-1);
 const side=previousZ<=-2&&z>-2&&z<0?1:previousZ>=2&&z<2&&z>0?-1:0;
 return {alpha,beta,sigma,z,previousZ,side};
}
export function quoteIsFresh(q:Ticker|undefined,now:number,closedAt:number):q is Ticker {
 return !!q&&[q.bid,q.ask,q.timestamp].every(Number.isFinite)&&q.bid>0&&q.ask>=q.bid&&q.timestamp>=closedAt&&q.timestamp<=now+5000&&now-q.timestamp<=30000;
}
export function scanPair(btc:MarketEntry|undefined,eth:MarketEntry|undefined,now:number):{reason:string;model:PairModel|null;signal:PairSignal|null} {
 const blocked=(reason:string)=>({reason,model:null,signal:null});
 if(!Number.isFinite(now)||!btc||!eth)return blocked('Aguardando os históricos de BTC e ETH.');
 if([btc,eth].some(e=>!Number.isFinite(e.receivedAt)||now-e.receivedAt>90000||e.receivedAt>now+5000))return blocked('Aguardando atualização das duas fontes.');
 const closedAt=Math.floor(now/step)*step;
 const a=btc.bars.filter(b=>b.time+step<=now).slice(-121),b=eth.bars.filter(b=>b.time+step<=now).slice(-121);
 if(a.length<121||b.length<121||a.at(-1)!.time!==closedAt-step||b.at(-1)!.time!==closedAt-step)return blocked('Aguardando 121 fechamentos H1 sincronizados.');
 const model=pairModel(a,b,120);if(!model)return blocked('Histórico com lacunas ou relação estatística inadequada.');
 const result=(reason:string,signal:PairSignal|null=null)=>({reason,model,signal});
 if(!model.side)return result('Regra verificada. Aguardando retorno do desvio para dentro de ±2.');
 if(now-closedAt>60000)return result('Condição histórica encontrada; janela de entrada encerrada.');
 if(!quoteIsFresh(btc.ticker,now,closedAt)||!quoteIsFresh(eth.ticker,now,closedAt))return result('Condição encontrada. Aguardando cotações recentes das duas pernas.');
 const ethEntry=model.side===1?eth.ticker.ask:eth.ticker.bid,btcEntry=model.side===1?btc.ticker.bid:btc.ticker.ask;
 const entryZ=(Math.log(ethEntry)-model.alpha-model.beta*Math.log(btcEntry))/model.sigma;
 if(model.side===1?(entryZ<=-2||entryZ>=0):(entryZ>=2||entryZ<=0))return result('O preço atual já saiu da faixa de entrada.');
 return result('Hipótese experimental encontrada.',{
  version:1,id:`N1-${closedAt}`,strategy:'N1',mode:'research',validated:false,
  createdAt:now,expiresAt:closedAt+60000,candleTime:closedAt-step,source:'Kraken Spot · proxy de pesquisa',
  model,ethEntry,btcEntry,entryZ,ethSide:model.side===1?'Compra':'Venda',btcSide:model.side===1?'Venda':'Compra',
  targetZ:0,stopZ:-model.side*3,maxHoldUntil:closedAt+24*step,
 });
}
export function demoPairSignal(now:number):PairSignal {
 const beta=1.2,sigma=.015,btcEntry=60000,ethEntry=2500,entryZ=-1.5;
 return {version:1,id:`DEMO-N1-${now}`,strategy:'N1',mode:'demo',validated:false,createdAt:now,expiresAt:now+60000,candleTime:now-step,source:'Dados artificiais · teste da interface',model:{alpha:Math.log(ethEntry)-beta*Math.log(btcEntry)-entryZ*sigma,beta,sigma,z:-1.5,previousZ:-2.2,side:1},ethEntry,btcEntry,entryZ,ethSide:'Compra',btcSide:'Venda',targetZ:0,stopZ:-3,maxHoldUntil:now+24*step};
}
export const pairStorageKey='tradernova-pair-signals-v1';
export function readPairSignals(raw:unknown):PairSignal[] {
 if(!Array.isArray(raw))return [];
 return raw.slice(0,100).filter((s):s is PairSignal=>{
  if(!s||typeof s!=='object')return false;
  const m=s.model;
  return s.version===1&&s.strategy==='N1'&&s.validated===false&&['demo','research'].includes(s.mode)&&typeof s.id==='string'&&s.id.length<100&&typeof s.source==='string'&&s.source.length<120&&
   [s.createdAt,s.expiresAt,s.candleTime,s.ethEntry,s.btcEntry,s.entryZ,s.stopZ,s.maxHoldUntil].every(Number.isFinite)&&s.ethEntry>0&&s.btcEntry>0&&s.expiresAt>s.createdAt&&s.expiresAt-s.createdAt<=60000&&
   m&&[m.alpha,m.beta,m.sigma,m.z,m.previousZ].every(Number.isFinite)&&m.beta>=.1&&m.beta<=5&&m.sigma>=1e-6&&[1,-1].includes(m.side)&&s.stopZ===-m.side*3&&s.targetZ===0&&
   s.ethSide===(m.side===1?'Compra':'Venda')&&s.btcSide===(m.side===1?'Venda':'Compra')&&
   (s.decision===undefined||['Revisado','Ignorado'].includes(s.decision))&&(s.note===undefined||(typeof s.note==='string'&&s.note.length<=500));
 });
}
