'use client';
import {useEffect,useMemo,useRef,useState} from 'react';
import {Bot,Download,Radio,ShieldCheck} from 'lucide-react';
import {toast} from 'sonner';
import {useLiveMarket} from '@/hooks/use-live-market';
import {marketNow} from '@/lib/tradernova/market-clock';
import {researchCandidates} from '@/lib/tradernova/research';
import {evaluatePaperEngine,observationOpportunity,observationStorageKey,readObservationSignals,type ObservationSignal} from '@/lib/tradernova/paper-engine';
import './research-workspace.css';
const format=(v:number)=>v.toLocaleString('pt-BR',{maximumFractionDigits:2});
function download(data:unknown,name:string){const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function load(){try{return readObservationSignals(JSON.parse(localStorage.getItem(observationStorageKey)||'[]'),Date.now());}catch{return [];}}
export function RobotWorkspace({alertsOn=true}:{alertsOn?:boolean}){
 const [now,setNow]=useState(0),[signals,setSignals]=useState<ObservationSignal[]>([]),[ready,setReady]=useState(false),[storageError,setStorageError]=useState(false),seen=useRef(new Set<string>()),current=useRef<ObservationSignal[]>([]);
 useEffect(()=>{const data=load();current.current=data;setSignals(data);seen.current=new Set(data.map(s=>s.id));setNow(marketNow());setReady(true);const timer=setInterval(()=>setNow(marketNow()),1000);return()=>clearInterval(timer);},[]);
 const feed=useLiveMarket(true,'BTCUSD',60),entry=feed.entries.BTCUSD;
 const snapshot=useMemo(()=>evaluatePaperEngine(entry?.bars??[],60,(feed.clockReady?entry?.receivedAt:0)??0,now),[entry,feed.clockReady,now]);
 const fresh=snapshot.status==='ready'&&!!entry?.ticker&&now-entry.ticker.timestamp<=30000;
 useEffect(()=>{
  if(!ready||!feed.clockReady||!entry?.ticker||document.hidden||!navigator.onLine)return;
  for(const c of researchCandidates){const signal=observationOpportunity(snapshot,c.id,'BTCUSD',entry.ticker,now);if(signal&&!seen.current.has(signal.id)){seen.current.add(signal.id);const next=[signal,...current.current].slice(0,200);current.current=next;setSignals(next);try{localStorage.setItem(observationStorageKey,JSON.stringify(next));}catch{setStorageError(true);}if(alertsOn)toast.info('Sinal de observação · não validado',{description:`${signal.assetId} · Compra · Entrada ${format(signal.entry)} · Stop ${format(signal.stop)} · Take ${format(signal.target)}`,duration:15000});}}
 },[entry,snapshot,now,feed.clockReady,alertsOn,ready]);
 const status=fresh?'Observação em BTCUSD H1 · nenhuma estratégia validada':'Aguardando dados recentes';
 return <><div className="robot-overview panel"><div className="row"><span className="robot-icon large"><Bot size={30}/></span><div><h2>Motor de sinais</h2><p role="status" aria-live="polite">{status}</p></div></div><div className="row"><span className="tag amber">0 estratégias validadas</span><span className="tag">{researchCandidates.length} candidatas em observação</span></div></div>
 <div className="section-heading"><h2>Sinais de observação</h2><span className="tag">{signals.filter(s=>s.expiresAt>now).length} ativos</span><button className="text-button" disabled={!signals.length} onClick={()=>download({validated:false,signals},'TraderNova_Observacao_BTCUSD.json')}><Download size={16}/>Exportar</button></div>
 {storageError&&<p role="alert" className="research-error">Falha ao salvar neste dispositivo. Exporte os sinais antes de sair.</p>}
 {signals.length?<div className="signal-grid">{signals.map(s=><article className="panel padded" key={s.id}><div className="row between"><h2>{s.assetId} · {s.direction}</h2><div className="row"><span className="tag amber">NÃO VALIDADA</span><span className="tag">{s.expiresAt>now?'Em observação':'Expirado'}</span></div></div><p className="micro research-form-note">{researchCandidates.find(c=>c.id===s.candidateId)?.name} · H1 · Kraken Spot</p><div className="levels-grid"><div>Entrada de referência<strong>{format(s.entry)}</strong></div><div>Stop loss<strong>{format(s.stop)}</strong></div><div>Take profit<strong>{format(s.target)}</strong></div></div><h3>Por que este sinal apareceu</h3><ul className="signal-evidence">{s.evidence.map(e=><li key={e}>{e}</li>)}</ul><p className="micro">Candle confirmado: {new Date(s.closedAt).toLocaleString('pt-BR')}. Cotação observada: {new Date(s.quoteAt).toLocaleString('pt-BR')}.</p><div className="notice">Esta estratégia não passou na validação; o sinal serve apenas para observação e pesquisa. Nenhuma ordem é enviada pelo TraderNova.</div></article>)}</div>:<div className="panel empty-state tall"><Radio size={36}/><h3>Nenhum sinal de observação ainda</h3><p>O robô avalia T1, T2 e T3 em cada fechamento H1 de BTCUSD e mostrará aqui o motivo, a entrada, o stop loss e o take profit quando houver condição. Nada aqui está validado.</p><span className="tag"><ShieldCheck size={14}/>Sem ordens · apenas observação</span></div>}
 <p className="micro research-form-note">A busca funciona enquanto esta tela estiver aberta e visível. Dados atrasados suspendem novos sinais.</p></>;
}
