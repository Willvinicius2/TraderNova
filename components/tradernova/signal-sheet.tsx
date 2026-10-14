'use client';
import {useEffect,useState} from 'react';
import {ArrowDownLeft,ArrowUpRight} from 'lucide-react';
import {Sheet,SheetContent,SheetHeader,SheetTitle,SheetDescription} from '@/components/ui/sheet';
import {useNow} from '@/hooks/use-now';
import {assets,type AssetId} from '@/lib/tradernova/domain';
import {fetchSignal,toSheetModel} from '@/lib/tradernova/signal-client';
import type {SignalApiResponse} from '@/lib/tradernova/signal-source';
import {AssetIcon} from '@/components/tradernova/asset-icon';
const price=(v:number)=>v.toLocaleString('pt-BR',{maximumFractionDigits:v<10?5:2});
const when=(t:number)=>new Date(t).toLocaleString('pt-BR');
// Ficha de um sinal persistido, aberta por ?aba=robo&sinal=<uuid>. Só mostra o que a fonte devolveu; nunca usa exemplo ou demonstração no lugar.
export function SignalSheet({id,onClose}:{id:string;onClose:()=>void}){
 const now=useNow(),[attempt,setAttempt]=useState(0),[result,setResult]=useState<{key:string;response:SignalApiResponse}|null>(null),key=`${attempt}`;
 useEffect(()=>{
  const control=new AbortController();
  fetchSignal(id,control.signal).then(response=>{if(!control.signal.aborted)setResult({key,response});}).catch(()=>{});
  return ()=>control.abort();
 },[id,key]);
 const model=toSheetModel(result?.key===key?result.response:null,now);
 return <Sheet open onOpenChange={v=>{if(!v)onClose();}}><SheetContent className="detail-sheet"><SheetHeader><div className="eyebrow">REVISÃO MANUAL</div><SheetTitle>Ficha do sinal</SheetTitle><SheetDescription>Registro da fonte de sinais. Nenhuma ordem será enviada.</SheetDescription></SheetHeader>
 {model.kind==='loading'&&<div className="sheet-body"><p className="muted" role="status" aria-live="polite">Carregando sinal…</p></div>}
 {model.kind==='message'&&<div className="sheet-body"><div className="notice" role="status"><strong>{model.title}</strong><br/>{model.text}</div>{model.retry&&<button className="secondary-button full" onClick={()=>setAttempt(a=>a+1)}>Tentar novamente</button>}</div>}
 {model.kind==='signal'&&(()=>{const r=model.record,buy=r.side==='buy',known=assets.some(a=>a.id===r.instrument);return <div className="sheet-body">
  <div className="row between"><div className="signal-instrument-heading">{known&&<AssetIcon id={r.instrument as AssetId} size={44}/>}<h2>{r.instrument} <span className="muted">· {model.timeframeLabel}</span></h2></div><span className={`tag ${model.status==='active'?'amber':'neutral'}`}>{model.status==='active'?`${model.remainingSeconds}s restantes`:model.status==='expired'?'Expirado':'Invalidado'}</span></div>
  <div className={`signal-hero ${buy?'positive':'negative'}`}>{buy?<ArrowUpRight size={28}/>:<ArrowDownLeft size={28}/>}{model.directionLabel}</div>
  <div className="row"><span className={`tag ${model.modeTone}`}>{model.modeLabel}</span><span className="micro">{model.sourceLabel} · {model.timeframeLabel} · {r.strategyId} · {r.strategyVersion}</span></div>
  {model.status==='invalidated'&&<div className="notice">Sinal invalidado{model.invalidationReason?`: ${model.invalidationReason}`:'.'}</div>}
  <div className="levels-grid"><div><span>Entrada de referência</span><strong>{price(r.entryReference)}</strong></div><div><span>Stop</span><strong>{price(r.stop)}</strong></div><div><span>Alvo</span><strong>{r.target===null?'—':price(r.target)}</strong></div></div>
  <h3>Por que este sinal apareceu</h3>
  {r.evidence.length?<ul className="signal-evidence">{r.evidence.map((e,i)=><li key={i}>{e}</li>)}</ul>:<p className="muted">Sem evidências registradas.</p>}
  <p className="micro">Gerado em {when(r.generatedAt)} · Validade até {when(r.expiresAt)}.</p>
  <div className="notice">{model.status==='active'?'Confira o símbolo e o preço atual na sua corretora. Se decidir operar, informe a entrada, o stop e o alvo manualmente.':model.status==='expired'?'Este sinal expirou. Aguarde uma nova oportunidade.':'Este sinal não vale mais.'} Nenhuma ordem é enviada pelo TraderNova.</div>
 </div>;})()}
 </SheetContent></Sheet>;
}
