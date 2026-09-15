import type {AssetId,Candle} from './domain';
export const livePairs = {BTCUSD:{ws:'BTC/USD',rest:'XBTUSD'},ETHUSD:{ws:'ETH/USD',rest:'ETHUSD'},SOLUSD:{ws:'SOL/USD',rest:'SOLUSD'}} as const;
export type LiveAssetId=keyof typeof livePairs;
export const liveAssetIds=Object.keys(livePairs) as LiveAssetId[];
export const liveIntervals=[1,5,15,60] as const;
export function isLiveAsset(id:string):id is LiveAssetId{return Object.prototype.hasOwnProperty.call(livePairs,id);}
export function assetFromSymbol(symbol:string):LiveAssetId|undefined{return liveAssetIds.find(id=>livePairs[id].ws===symbol);}
export type MarketCandle=Candle&{trades:number;vwap?:number};
export type Ticker={bid:number;ask:number;changePct:number;timestamp:number};
export type MarketEntry={bars:MarketCandle[];receivedAt:number;hasUpdate:boolean;historyReceivedAt?:number;wsReceivedAt?:number;transport?:'ws'|'rest';ticker?:Ticker;error?:string};
export type ConnectionState='connecting'|'connected'|'reconnecting'|'offline'|'paused'|'error';
export type MarketState={interval:number;connection:ConnectionState;entries:Partial<Record<LiveAssetId,MarketEntry>>;error:string|null;revision:number;epoch:number};
export const emptyEntry=():MarketEntry=>({bars:[],receivedAt:0,hasUpdate:false});
const number=(v:unknown)=>typeof v==='number'&&Number.isFinite(v);
export function validCandle(c:MarketCandle):boolean{return [c.time,c.open,c.high,c.low,c.close,c.volume,c.trades].every(Number.isFinite)&&c.time>0&&c.open>0&&c.close>0&&c.low>0&&c.high>=Math.max(c.open,c.close)&&c.low<=Math.min(c.open,c.close)&&c.volume>=0&&Number.isInteger(c.trades)&&c.trades>=0&&(c.vwap===undefined||(Number.isFinite(c.vwap)&&c.vwap>=c.low&&c.vwap<=c.high));}
/** Kraken reports cumulative OHLC. Replace, never add volume. Reject older snapshots. */
export function mergeCandles(existing:MarketCandle[],incoming:MarketCandle[],limit=720):MarketCandle[]{
 const map=new Map(existing.map(c=>[c.time,c]));
 for(const c of incoming){if(!validCandle(c))continue;const prior=map.get(c.time);if(prior&&(c.trades<prior.trades||c.volume<prior.volume))continue;map.set(c.time,c);}
 return Array.from(map.values()).sort((a,b)=>a.time-b.time).slice(-limit);
}
export function parseKrakenHistory(payload:unknown):MarketCandle[]{
 if(!payload||typeof payload!=='object')throw new Error('Resposta de histórico inválida.');
 const p=payload as {error?:unknown;result?:Record<string,unknown>};
 if(!Array.isArray(p.error)||p.error.length||!p.result)throw new Error('A fonte não retornou o histórico.');
 const series=Object.entries(p.result).filter(([k,v])=>k!=='last'&&Array.isArray(v));
 if(series.length!==1)throw new Error('Instrumento do histórico não identificado.');
 const rows=series[0][1] as unknown[];
 const candles=rows.map(row=>{if(!Array.isArray(row)||row.length<8)throw new Error('Candle incompleto.');
 const c={time:Number(row[0])*1000,open:Number(row[1]),high:Number(row[2]),low:Number(row[3]),close:Number(row[4]),volume:Number(row[6]),trades:Number(row[7]),...(Number(row[5])>0?{vwap:Number(row[5])}:{})};
 if(!validCandle(c))throw new Error('Candle inválido na fonte.');return c;});
 if(!candles.length)throw new Error('Histórico vazio.');return mergeCandles([],candles);
}
export function parseOhlcEvent(value:unknown,interval:number):{assetId:LiveAssetId;candle:MarketCandle}|null{
 if(!value||typeof value!=='object')return null;const v=value as Record<string,unknown>;
 if(v.interval!==interval||typeof v.symbol!=='string'||typeof v.interval_begin!=='string')return null;
 const id=assetFromSymbol(v.symbol);if(!id)return null;
 const c={time:Date.parse(v.interval_begin),open:v.open,high:v.high,low:v.low,close:v.close,volume:v.volume,trades:v.trades,...(typeof v.vwap==='number'?{vwap:v.vwap}:{})} as MarketCandle;
 if(![v.open,v.high,v.low,v.close,v.volume,v.trades].every(number)||!validCandle(c)||c.time> Date.now()+5000)return null;
 if(c.time%(interval*60000)!==0)return null;
 return {assetId:id,candle:c};
}
export function parseTicker(value:unknown):{assetId:LiveAssetId;ticker:Ticker}|null{
 if(!value||typeof value!=='object')return null;const v=value as Record<string,unknown>;
 if(typeof v.symbol!=='string'||!number(v.bid)||!number(v.ask)||!number(v.change_pct)||typeof v.timestamp!=='string')return null;
 const id=assetFromSymbol(v.symbol),timestamp=Date.parse(v.timestamp);
 if(!id||!Number.isFinite(timestamp)||timestamp>Date.now()+5000||(v.bid as number)<=0||(v.ask as number)<(v.bid as number))return null;
 return {assetId:id,ticker:{bid:v.bid as number,ask:v.ask as number,changePct:v.change_pct as number,timestamp}};
}
/** Price and latest candle always come from the same OHLC event, never ticker.last. */
export function displayedPrice(entry?:MarketEntry):number|null{return entry?.bars.at(-1)?.close??null;}
export function feedLabel(connection:ConnectionState,entry:MarketEntry|undefined,now:number,interval:number):string{
 if(connection==='offline')return 'Sem internet';if(connection==='paused')return 'Pausado';
 const last=entry?.bars.at(-1),active=!!last&&last.time<=now+5000&&last.time+interval*60000>now;
 const wsAge=now-(entry?.wsReceivedAt??entry?.receivedAt??0);
 if(connection==='connected'&&!entry?.error&&entry?.hasUpdate&&wsAge>=-5000&&wsAge<=30000&&active)return 'Ao vivo';
 const restAge=now-(entry?.historyReceivedAt??0);
 if(entry?.historyReceivedAt&&restAge>=-5000&&restAge<=45000&&active)return 'Atualização periódica';
 if(last)return 'Sem atualização recente';
 if(entry?.error||connection==='error')return 'Fonte indisponível';
 if(connection==='reconnecting')return 'Reconectando';if(connection==='connecting')return 'Conectando';
 return 'Aguardando negócio';
}
/** Validate source and timeframe before merging a network response into a chart. */
export function readHistoryResponse(value:unknown,asset:string,interval:number,now=Date.now()):{bars:MarketCandle[];receivedAt:number}{
 if(!value||typeof value!=='object')throw new Error('Histórico inválido.');
 const v=value as Record<string,unknown>,receivedAt=typeof v.receivedAt==='string'?Date.parse(v.receivedAt):NaN;
 if(v.asset!==asset||v.interval!==interval||v.source!=='kraken-spot'||!Number.isFinite(receivedAt)||receivedAt>now+30000||!Array.isArray(v.bars)||!v.bars.length)throw new Error('Fonte ou período do histórico não confere.');
 const bars=v.bars as MarketCandle[];
 if(bars.some((c,i)=>!validCandle(c)||c.time>now+5000||c.time%(interval*60000)!==0||(i>0&&c.time<=bars[i-1].time)))throw new Error('A fonte retornou candles inconsistentes.');
 return {bars,receivedAt};
}
export function applyHistory(entry:MarketEntry,bars:MarketCandle[],receivedAt:number):MarketEntry{
 const merged=mergeCandles(entry.bars,bars),wsRecent=!!entry.wsReceivedAt&&receivedAt-entry.wsReceivedAt<15000;
 return {...entry,bars:merged,historyReceivedAt:receivedAt,receivedAt:Math.max(entry.receivedAt,receivedAt),transport:wsRecent?'ws':'rest'};
}
export function retryDelay(attempt:number,random=Math.random):number{return Math.min(30000,5000*2**Math.min(attempt,3))+Math.floor(random()*750);}
