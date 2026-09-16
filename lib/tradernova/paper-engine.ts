import {atr,ema,rsi,type Candle} from './domain';
import {closedCandles,countGaps} from './indicators';
import {candidateSignals,researchCandidates,type CandidateId} from './research';
import {z} from 'zod';
import {activePresets} from './active-presets';
import {calibratedSignals,type StrategyParameters} from './calibration';
export type EngineReading={candidateId:CandidateId;state:'waiting'|'buy'|'sell-excluded';signalTime:number;entryReference:number|null;stop:number|null;target:number|null;evidence:string[]};
export type EngineSnapshot={status:'ready'|'blocked';reason:string;source:'kraken-spot';evaluatedAt:number;closedAt:number|null;readings:EngineReading[]};
export function evaluatePaperEngine(bars:Candle[],interval:number,receivedAt:number,now:number,presets:Partial<Record<CandidateId,StrategyParameters>>=activePresets):EngineSnapshot{
 const base={source:'kraken-spot' as const,evaluatedAt:now,closedAt:null,readings:[]};
 const blocked=(reason:string):EngineSnapshot=>({...base,status:'blocked',reason});
 if(![15,60].includes(interval)||!Number.isFinite(now)||!Number.isFinite(receivedAt)||receivedAt>now+5000||now-receivedAt>90000)return blocked('Aguardando dados recentes da fonte.');
 const step=interval*60000,current=Math.floor(now/step)*step;
 const closed=closedCandles(bars,interval,now);
 if(closed.length<201)return blocked('Aguardando 201 candles fechados para aquecimento.');
 if(closed.some((b,i)=>![b.time,b.open,b.high,b.low,b.close,b.volume].every(Number.isFinite)||b.low<=0||b.volume<0||b.high<Math.max(b.open,b.close)||b.low>Math.min(b.open,b.close)||b.time%step!==0||(i>0&&b.time<=closed[i-1].time))||countGaps(closed,interval))return blocked('Histórico inconsistente ou com lacunas.');
 if(closed.at(-1)!.time!==current-step)return blocked('O último fechamento ainda não chegou.');
 const forming=bars.find(b=>b.time===current);
 if(!forming||!Number.isFinite(forming.open)||forming.open<=0)return blocked('Aguardando abertura do candle seguinte.');
 const range=atr(closed).at(-1)!,signalTime=closed.at(-1)!.time;
 const values=closed.map(b=>b.close),last=closed.at(-1)!,pretty=(v:number)=>v.toLocaleString('pt-BR',{maximumFractionDigits:4});
 const e9=ema(values,9),e21=ema(values,21),e20=ema(values,20),e50=ema(values,50),e200=ema(values,200);
 const readings=researchCandidates.map(c=>{
  const parameters=presets[c.id],side=parameters?(parameters.trendFilter&&closed.length<600?0:calibratedSignals(closed,parameters).at(-1)!):candidateSignals(closed,c.id).at(-1)!;
  const stopAtr=parameters?.stopAtr??c.stopAtr,reward=parameters?.reward??2;
  const evidence=c.id==='T1'?[`EMA 9: ${pretty(e9.at(-2)!)} → ${pretty(e9.at(-1)!)}. EMA 21: ${pretty(e21.at(-2)!)} → ${pretty(e21.at(-1)!)}. Cruzamento confirmado no fechamento.`]:c.id==='T2'?[`EMA 20 ${pretty(e20.at(-1)!)} e EMA 50 ${pretty(e50.at(-1)!)}; EMA 50 há 3 candles ${pretty(e50.at(-4)!)}.`,`Mínima ${pretty(last.low)}, abertura ${pretty(last.open)}, fechamento ${pretty(last.close)}; RSI 14 ${pretty(rsi(closed)!)}.`]:[`Fechamento ${pretty(last.close)} acima da máxima dos 20 candles anteriores ${pretty(Math.max(...closed.slice(-21,-1).map(b=>b.high)))} e da EMA 50 ${pretty(e50.at(-1)!)}.`];
  if(parameters?.trendFilter)evidence.push(`EMA 200 ${pretty(e200.at(-1)!)} versus ${pretty(e200.at(-25)!)} há 24 candles; fechamento e EMA 50 acima dela. Distância do stop deve cobrir pelo menos 3 vezes o custo estimado.`);
  evidence.push(`ATR 14 ${pretty(range)}; stop a ${stopAtr} × ATR e take profit a ${reward} vezes essa distância.`);
  return {candidateId:c.id,state:side===1?'buy' as const:side===-1?'sell-excluded' as const:'waiting' as const,signalTime,entryReference:side===1?forming.open:null,stop:side===1?forming.open-range*stopAtr:null,target:side===1?forming.open+reward*range*stopAtr:null,evidence};
 });
 return {...base,status:'ready',reason:'Regras calculadas no último candle fechado.',closedAt:current,readings};
}

export const simulationPreset={assetId:'BTCUSD' as const,symbol:'BTCUSDT',interval:60,initialCapital:100000,riskPct:.5,feeBps:10,slippageBps:2,dailyLimit:3000,totalLimit:10000};
export type PaperPosition={entry:number;quantity:number;stop:number;target:number;entryAt:number;expiresAt:number;entryFee:number;cashBefore:number;signalTime:number};
export type PaperTrade=PaperPosition&{exit:number;exitAt:number;net:number;reason:string};
export type PaperSession={version:1;candidateId:CandidateId;presetId?:string;startedAt:number;cash:number;equity:number;day:string;dayStartEquity:number;lastSignalTime:number;lastQuoteAt:number;lastPrice:number|null;position:PaperPosition|null;trades:PaperTrade[];halted:string|null;dailyPaused:boolean};
export function newPaperSession(candidateId:CandidateId,now:number):PaperSession{
 return {version:1,candidateId,presetId:activePresets[candidateId].id,startedAt:now,cash:simulationPreset.initialCapital,equity:simulationPreset.initialCapital,day:new Date(now).toISOString().slice(0,10),dayStartEquity:simulationPreset.initialCapital,lastSignalTime:0,lastQuoteAt:0,lastPrice:null,position:null,trades:[],halted:null,dailyPaused:false};
}
/** Forward simulation fills at the quote actually observed, never retroactively
 * at a candle's opening price or using a wick that occurred before entry.
 * UTC daily boundary is a local safety assumption until the broker is specified.
 */
export function advancePaperSession(previous:PaperSession,snapshot:EngineSnapshot,quote:{bid:number;ask:number;timestamp:number},now:number):PaperSession{
 if(!Number.isFinite(now)||![quote.bid,quote.ask,quote.timestamp].every(Number.isFinite)||quote.bid<=0||quote.ask<quote.bid||quote.timestamp>now+5000||now-quote.timestamp>30000||quote.timestamp<=previous.lastQuoteAt)return previous;
 const p=simulationPreset,fee=p.feeBps/10000,slip=p.slippageBps/10000;
 const s={...previous,trades:[...previous.trades],lastQuoteAt:quote.timestamp,lastPrice:quote.bid};
 const day=new Date(now).toISOString().slice(0,10);
 if(day!==s.day){s.day=day;s.dayStartEquity=s.equity;if(s.dailyPaused){s.halted=null;s.dailyPaused=false;}}
 s.equity=s.cash+(s.position?s.position.quantity*quote.bid*(1-slip)*(1-fee):0);
 const totalHit=s.equity<=p.initialCapital-p.totalLimit,dailyHit=s.equity<=s.dayStartEquity-p.dailyLimit;
 if(totalHit||dailyHit){s.halted=totalHit?'Limite total da simulação atingido':'Limite diário da simulação atingido';s.dailyPaused=!totalHit;}
 const pos=s.position;
 if(pos&&(quote.bid<=pos.stop||quote.bid>=pos.target||now>=pos.expiresAt||totalHit||dailyHit)){
  const exit=quote.bid*(1-slip);s.cash+=pos.quantity*exit*(1-fee);s.equity=s.cash;
  s.trades.push({...pos,exit,exitAt:now,net:s.cash-pos.cashBefore,reason:s.halted??(quote.bid<=pos.stop?'Stop observado':quote.bid>=pos.target?'Alvo observado':'Limite de tempo')});s.position=null;
  // Never close and reopen on the same quote.
  return s;
 }
 if(snapshot.status!=='ready'||snapshot.evaluatedAt!==now)return s;
 if((s.presetId??`${s.candidateId}-E0X0`)!==activePresets[s.candidateId].id)return s;
 const reading=snapshot.readings.find(r=>r.candidateId===s.candidateId);
 if(!reading||reading.signalTime<=s.lastSignalTime)return s;
 if(snapshot.closedAt===null||quote.timestamp<snapshot.closedAt)return s;
 s.lastSignalTime=reading.signalTime;
 if(s.halted||s.position||reading.state!=='buy'||snapshot.closedAt!>now||snapshot.closedAt!<s.startedAt||now-snapshot.closedAt!>30000)return s;
 const candidate=activePresets[s.candidateId],distance=reading.entryReference!-reading.stop!;
 const rawEntry=quote.ask,entry=rawEntry*(1+slip),stop=rawEntry-distance,target=rawEntry+candidate.reward*distance,stopFill=stop*(1-slip);
 if(!Number.isFinite(distance)||distance<=0||stop<=0)return s;
 const riskPerUnit=entry-stopFill+fee*(entry+stopFill),riskBudget=Math.min(s.equity*p.riskPct/100,s.equity-(p.initialCapital-p.totalLimit),s.equity-(s.dayStartEquity-p.dailyLimit));
 if(riskBudget<=0)return s;
 const quantity=Math.min(riskBudget/riskPerUnit,s.cash/(entry*(1+fee))),entryFee=quantity*entry*fee;
 s.position={entry,quantity,stop,target,entryAt:now,expiresAt:now+candidate.hold*p.interval*60000,entryFee,cashBefore:s.cash,signalTime:reading.signalTime};
 s.cash-=quantity*entry+entryFee;s.equity=s.cash+quantity*quote.bid*(1-slip)*(1-fee);
 return s;
}

export type StrategyApproval={candidateId:CandidateId;presetId:string;assetId:string;source:string;interval:number;status:'validated';forwardPassed:true;approvedAt:number;expiresAt:number};
// Intentionally empty: the retrospective study rejected all tested combinations.
export const strategyApprovals:StrategyApproval[]=[];
export function canAlertForManualTrade(candidateId:CandidateId,now:number,approvals:StrategyApproval[]=strategyApprovals){
 return approvals.some(a=>a.candidateId===candidateId&&a.presetId===activePresets[candidateId].id&&a.assetId===simulationPreset.assetId&&a.source==='kraken-spot'&&a.interval===simulationPreset.interval&&a.status==='validated'&&a.forwardPassed===true&&a.approvedAt<=now&&a.expiresAt>now);
}

const finite=z.number().finite(),positive=finite.positive();
const positionSchema=z.object({entry:positive,quantity:positive,stop:positive,target:positive,entryAt:positive,expiresAt:positive,entryFee:finite.nonnegative(),cashBefore:positive,signalTime:positive});
const sessionSchema=z.object({version:z.literal(1),candidateId:z.enum(['T1','T2','T3']),presetId:z.string().max(40).optional(),startedAt:positive,cash:finite,equity:finite,day:z.string().regex(/^\d{4}-\d{2}-\d{2}$/),dayStartEquity:positive,lastSignalTime:finite.nonnegative(),lastQuoteAt:finite.nonnegative(),lastPrice:positive.nullable(),position:positionSchema.nullable(),trades:z.array(positionSchema.extend({exit:positive,exitAt:positive,net:finite,reason:z.string().max(150)})).max(10000),halted:z.string().max(150).nullable(),dailyPaused:z.boolean()});
export function readPaperSession(raw:unknown,candidate:CandidateId):PaperSession|null{
 const parsed=sessionSchema.safeParse(raw);if(!parsed.success||parsed.data.candidateId!==candidate)return null;
 const s=parsed.data,expected=simulationPreset.initialCapital+s.trades.reduce((sum,t)=>sum+t.net,0)-(s.position?s.position.quantity*s.position.entry+s.position.entryFee:0);
 if(Math.abs(expected-s.cash)>.01||s.startedAt>Date.now()+5000)return null;
 return s;
}

export function manualOpportunity(snapshot:EngineSnapshot,candidate:CandidateId,quote:{bid:number;ask:number;timestamp:number},now:number,approvals:StrategyApproval[]=strategyApprovals){
 if(!canAlertForManualTrade(candidate,now,approvals)||snapshot.status!=='ready'||snapshot.closedAt===null||now-snapshot.closedAt<0||now-snapshot.closedAt>30000||![quote.bid,quote.ask,quote.timestamp].every(Number.isFinite)||quote.bid<=0||quote.ask<quote.bid||quote.timestamp<snapshot.closedAt||now-quote.timestamp>30000||quote.timestamp>now+5000)return null;
 const r=snapshot.readings.find(r=>r.candidateId===candidate&&r.state==='buy');if(!r||r.entryReference===null||r.stop===null)return null;
 const distance=r.entryReference-r.stop;if(distance<=0||quote.ask-distance<=0)return null;
 return {id:`${candidate}:${activePresets[candidate].id}:${snapshot.closedAt}`,candidateId:candidate,source:snapshot.source,assetId:simulationPreset.assetId,direction:'Compra' as const,entry:quote.ask,stop:quote.ask-distance,target:quote.ask+distance*activePresets[candidate].reward,createdAt:now,expiresAt:snapshot.closedAt+30000,evidence:r.evidence,signalTime:r.signalTime};
}
