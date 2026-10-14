'use client';
import {useEffect,useMemo,useRef,useState} from 'react';
import {useNow} from '@/hooks/use-now';
import {Bot,Radio,ShieldCheck} from 'lucide-react';
import {toast} from 'sonner';
import {useLiveMarket} from '@/hooks/use-live-market';
import {researchCandidates} from '@/lib/tradernova/research';
import {evaluatePaperEngine,manualOpportunity,strategyApprovals,canAlertForManualTrade} from '@/lib/tradernova/paper-engine';
import './research-workspace.css';
const format=(v:number)=>v.toLocaleString('pt-BR',{maximumFractionDigits:2});
type Opportunity=NonNullable<ReturnType<typeof manualOpportunity>>;
export function RobotWorkspace(){
 const now=useNow(),[signals,setSignals]=useState<Opportunity[]>([]),seen=useRef(new Set<string>());
 const approved=researchCandidates.filter(c=>canAlertForManualTrade(c.id,now,strategyApprovals));
 const feed=useLiveMarket(approved.length>0,'BTCUSD',60),entry=feed.entries.BTCUSD;
 const snapshot=useMemo(()=>evaluatePaperEngine(entry?.bars??[],60,entry?.receivedAt??0,now),[entry,now]);
 const fresh=snapshot.status==='ready'&&!!entry?.ticker&&now-entry.ticker.timestamp<=30000;
 useEffect(()=>{
  if(!entry?.ticker||document.hidden||!navigator.onLine)return;
  for(const c of researchCandidates){const signal=manualOpportunity(snapshot,c.id,entry.ticker,now);if(signal&&!seen.current.has(signal.dedupKey)){seen.current.add(signal.dedupKey);setSignals(old=>[signal,...old].slice(0,30));toast.info('Oportunidade para revisão manual',{description:`${signal.assetId} · Compra · Entrada ${format(signal.entry)} · Stop ${format(signal.stop)} · Take ${format(signal.target)}`,duration:15000});}}
 },[entry,snapshot,now]);
 const status=!approved.length?'Aguardando estratégias validadas':fresh?'Buscando oportunidades':'Aguardando dados recentes';
 return <><div className="robot-overview panel"><div className="row"><span className="robot-icon large"><Bot size={30}/></span><div><h2>Motor de sinais</h2><p role="status" aria-live="polite">{status}</p></div></div><span className={`tag ${approved.length?'purple':'amber'}`}>{approved.length} estratégias habilitadas</span></div>
 <div className="section-heading"><h2>Sinais para revisão manual</h2><span className="tag">{signals.filter(s=>s.expiresAt>now).length} ativos</span></div>
 {signals.length?<div className="signal-grid">{signals.map(s=><article className="panel padded" key={s.publicId} role={s.expiresAt>now?'alert':undefined}><div className="row between"><h2>{s.assetId} · {s.direction}</h2><span className="tag">{s.expiresAt>now?'Em revisão':'Expirado'}</span></div><p className="micro research-form-note">{researchCandidates.find(c=>c.id===s.candidateId)?.name} · H1 · Kraken Spot</p><div className="levels-grid"><div>Entrada de referência<strong>{format(s.entry)}</strong></div><div>Stop loss<strong>{format(s.stop)}</strong></div><div>Take profit<strong>{format(s.target)}</strong></div></div><h3>Por que este sinal apareceu</h3><ul className="signal-evidence">{s.evidence.map(e=><li key={e}>{e}</li>)}</ul><p className="micro">Candle confirmado: {new Date(s.signalTime+3600000).toLocaleString('pt-BR')}. Cotação observada: {new Date(s.createdAt).toLocaleString('pt-BR')}.</p><div className="notice">{s.expiresAt>now?'Confira o símbolo e o preço atual na sua corretora. Se decidir operar, informe a entrada, o stop loss e o take profit manualmente.':'Este sinal expirou. Aguarde uma nova oportunidade.'} Nenhuma ordem é enviada pelo TraderNova.</div></article>)}</div>:<div className="panel empty-state tall"><Radio size={36}/><h3>{approved.length?'Buscando uma oportunidade para você':'Nenhuma estratégia liberada ainda'}</h3><p>{approved.length?'O robô verifica os fechamentos e mostrará aqui o motivo, a entrada, o stop loss e o take profit quando houver sinal.':'A calibração trouxe melhorias, mas ainda não cumpriu os critérios de aprovação. Quando uma estratégia passar pela validação, o robô buscará oportunidades e emitirá alertas nesta tela.'}</p><span className="tag"><ShieldCheck size={14}/>Execução manual na corretora</span></div>}
 <p className="micro research-form-note">A busca funciona enquanto esta tela estiver aberta e visível. Dados atrasados suspendem novos sinais.</p></>;
}
