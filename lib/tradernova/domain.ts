import type {ObservationSignal} from './paper-engine';
export type AssetId = 'XAUUSD' | 'NAS100' | 'BTCUSD' | 'ETHUSD' | 'SOLUSD' | 'EURUSD' | 'USDJPY';
export type Candle = { time: number; open: number; high: number; low: number; close: number; volume: number };
export type Asset = { id: AssetId; name: string; mark: string; price: number; decimals: number; color: string; kind: string };
export const assets: Asset[] = [
 {id:'XAUUSD',name:'Ouro',mark:'Au',price:4000,decimals:2,color:'#e3ba65',kind:'Metal'},
 {id:'NAS100',name:'Nasdaq 100',mark:'N',price:20000,decimals:2,color:'#6f9fee',kind:'Índice · contrato pendente'},
 {id:'BTCUSD',name:'Bitcoin',mark:'₿',price:67420,decimals:2,color:'#e8a25b',kind:'Cripto'},
 {id:'ETHUSD',name:'Ethereum',mark:'Ξ',price:2640,decimals:2,color:'#aaa5ed',kind:'Cripto'},
 {id:'SOLUSD',name:'Solana',mark:'S',price:145,decimals:2,color:'#9cd0c9',kind:'Cripto'},
 {id:'EURUSD',name:'Euro / Dólar',mark:'€',price:1.082,decimals:5,color:'#78afe8',kind:'Forex'},
 {id:'USDJPY',name:'Dólar / Iene',mark:'¥',price:145.32,decimals:3,color:'#e18e9f',kind:'Forex'},
];
export const strategies = [
 {id:'S1',name:'Pullback de tendência',group:'Tendência',summary:'Retração na EMA20, com contexto H1 e confirmação por fechamento.',tags:['EMA 20/50/200','ATR 14'],rule:'H1 encerrado acima da EMA200, EMA50 ascendente e retomada da EMA20 no M15. Venda simétrica.',status:'Especificada'},
 {id:'S2',name:'Rompimento e reteste',group:'Estrutura',summary:'Rompimento de consolidação seguido de um reteste confirmado.',tags:['Estrutura','ATR 14'],rule:'Identificar faixa concluída, confirmar fechamento fora da faixa e esperar o reteste. Parâmetros dependem do instrumento.',status:'Especificada'},
 {id:'S3',name:'Retorno ao POC',group:'Volume',summary:'Rejeição da área de valor em direção ao POC da sessão anterior.',tags:['POC','Área de valor'],rule:'Usar somente o perfil da sessão concluída; distinguir volume negociado de perfil de ticks.',status:'Depende de dados'},
 {id:'S4',name:'Varredura de liquidez',group:'SMC',summary:'Rompimento temporário e recuperação de um nível já conhecido.',tags:['Pivôs causais','SMC'],rule:'Pivôs com duas barras de confirmação posterior. O sinal só pode surgir depois dessa confirmação.',status:'Especificada'},
 {id:'S5',name:'Oferta e demanda',group:'Zonas',summary:'Reteste de zona após deslocamento e confirmação de estrutura.',tags:['Zonas','ATR 14'],rule:'Definir zona por regra causal e congelar a origem antes do reteste. Nenhuma inferência de ordens institucionais.',status:'Especificada'},
 {id:'S6',name:'Faixa de abertura',group:'Sessão',summary:'Expansão e reteste da faixa inicial, com foco no Nasdaq.',tags:['Opening range','Sessão'],rule:'Congelar a faixa após seu encerramento; calendário, sessão e horário de verão precisam ser configurados.',status:'Depende de dados'},
];
export type Signal = {id:string;assetId:AssetId;direction:'Compra'|'Venda';createdAt:number;expiresAt:number;entry:number;stop:number;target:number;demo:true;strategyId:string};
export type JournalSignal = Signal|ObservationSignal;
export type JournalEntry = {id:string;signal:JournalSignal;decision:'Revisado'|'Ignorado';createdAt:number;note:string};
export function isObservationSignal(s:JournalSignal):s is ObservationSignal {return 'kind' in s&&s.kind==='observation';}
export function makeSignal(asset:Asset,direction:'Compra'|'Venda'):Signal {
 const now=Date.now(), distance=asset.price*0.0025, side=direction==='Compra'?1:-1;
 return {id:crypto.randomUUID(),assetId:asset.id,direction,createdAt:now,expiresAt:now+60000,entry:asset.price,stop:asset.price-distance*side,target:asset.price+2*distance*side,demo:true,strategyId:'S1'};
}
export function signalState(s:Signal, now:number) {return now>=s.expiresAt?'Expirado':'Exemplo ativo';}
export function formatPrice(price:number,asset:Asset) {return price.toLocaleString('pt-BR',{minimumFractionDigits:asset.decimals,maximumFractionDigits:asset.decimals});}
export function createCandles(asset:Asset,count=240,minutes=15):Candle[] {
 let seed=asset.id.split('').reduce((v,c)=>v+c.charCodeAt(0),19)+minutes;
 const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
 let close=asset.price*0.987;
 return Array.from({length:count},(_,i)=>{
 const open=close; close=open+asset.price*(0.00012+Math.sin(i/13)*0.0005+(random()-.5)*.002);
 const range=asset.price*(.0002+random()*.0007);
 return {time:Date.UTC(2026,8,1)+i*minutes*60000,open,close,high:Math.max(open,close)+range,low:Math.min(open,close)-range,volume:Math.floor(150+random()*1100)};
 });
}
export function ema(values:number[],period:number):(number|null)[] {
 if(!Number.isInteger(period)||period<1)throw new Error('Período inválido');
 let prior:number|null=null;
 return values.map((v,i)=>{if(i<period-1)return null; prior=prior===null?values.slice(0,period).reduce((a,b)=>a+b,0)/period:v*2/(period+1)+prior*(1-2/(period+1));return prior;});
}
export function atr(bars:Candle[],period=14):(number|null)[] {
 const tr=bars.map((b,i)=>i?Math.max(b.high-b.low,Math.abs(b.high-bars[i-1].close),Math.abs(b.low-bars[i-1].close)):b.high-b.low);
 let prior:number|null=null;
 return tr.map((v,i)=>{if(i<period-1)return null; prior=prior===null?tr.slice(0,period).reduce((a,b)=>a+b,0)/period:(prior*(period-1)+v)/period;return prior;});
}
export function rsi(bars:Candle[],period=14):number|null {
 if(bars.length<=period)return null;
 let gain=0,loss=0;
 for(let i=1;i<bars.length;i++) {const d=bars[i].close-bars[i-1].close;if(i<=period){gain+=Math.max(d,0)/period;loss+=Math.max(-d,0)/period;}else{gain=(gain*(period-1)+Math.max(d,0))/period;loss=(loss*(period-1)+Math.max(-d,0))/period;}}
 return loss===0?(gain===0?50:100):100-100/(1+gain/loss);
}
