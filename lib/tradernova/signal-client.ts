import {z} from 'zod';
import {isPublicSignalId,signalRecordSchema,type SignalMode,type SignalRecord} from './signal-record';
import type {SignalApiResponse} from './signal-source';
// Cliente da ficha do sinal: busca em /api/signals/:id e traduz a resposta em um modelo de tela puro (sem React). Nunca cria nem substitui um sinal.
const reasons=z.enum(['not-configured','unreachable','invalid-response']);
const responseSchema=z.discriminatedUnion('state',[
 z.object({state:z.enum(['active','expired','invalidated']),record:signalRecordSchema}),
 z.object({state:z.enum(['not-found','invalid-id','unauthorized'])}),
 z.object({state:z.literal('source-unavailable'),reason:reasons})
]);
const unavailable=(reason:z.infer<typeof reasons>):SignalApiResponse=>({state:'source-unavailable',reason});
// Valida o corpo recebido; qualquer formato inesperado vira "fonte indisponível", nunca um sinal.
export function parseSignalResponse(body:unknown):SignalApiResponse{
 const parsed=responseSchema.safeParse(body);
 return parsed.success?parsed.data:unavailable('invalid-response');
}
export async function fetchSignal(id:string,signal?:AbortSignal,fetchFn:typeof fetch=fetch):Promise<SignalApiResponse>{
 if(!isPublicSignalId(id))return {state:'invalid-id'};
 try{
  const response=await fetchFn(`/api/signals/${encodeURIComponent(id)}`,{signal,cache:'no-store',headers:{Accept:'application/json'}});
  return parseSignalResponse(await response.json());
 }catch(error){
  if(error instanceof DOMException&&error.name==='AbortError')throw error;
  return unavailable('unreachable');
 }
}
export type SheetModel=
 |{kind:'loading'}
 |{kind:'message';tone:'neutral'|'amber';title:string;text:string;retry:boolean}
 |{kind:'signal';status:'active'|'expired'|'invalidated';record:SignalRecord;modeLabel:string;modeTone:'purple'|'amber'|'neutral';directionLabel:'Compra'|'Venda';sourceLabel:string;timeframeLabel:string;remainingSeconds:number;invalidationReason:string|null};
const modeLabels:Record<SignalMode,{label:string;tone:'purple'|'amber'|'neutral'}>={research:{label:'Pesquisa',tone:'purple'},test:{label:'Teste',tone:'amber'},alert:{label:'Alerta',tone:'neutral'}};
const sources:Record<string,string>={'kraken-spot':'Kraken Spot'};
export const timeframeLabel=(minutes:number)=>minutes===60?'H1':minutes<60?`M${minutes}`:minutes%60===0?`H${minutes/60}`:`${minutes} min`;
// null = ainda carregando. `now` permite virar "expirado" no relógio do aparelho sem nova consulta.
export function toSheetModel(response:SignalApiResponse|null,now:number):SheetModel{
 if(!response)return {kind:'loading'};
 switch(response.state){
  case 'active':case 'expired':case 'invalidated':{
   const r=response.record,mode=modeLabels[r.mode];
   const status=response.state==='active'&&now>=r.expiresAt?'expired':response.state;
   return {kind:'signal',status,record:r,modeLabel:mode.label,modeTone:mode.tone,directionLabel:r.side==='buy'?'Compra':'Venda',sourceLabel:sources[r.provider]??r.provider,timeframeLabel:timeframeLabel(r.timeframeMinutes),remainingSeconds:status==='active'?Math.max(0,Math.ceil((r.expiresAt-now)/1000)):0,invalidationReason:status==='invalidated'?r.invalidationReason:null};
  }
  case 'not-found':return {kind:'message',tone:'neutral',title:'Sinal não encontrado',text:'Sinal não encontrado. Nenhum sinal foi criado no lugar.',retry:false};
  case 'invalid-id':return {kind:'message',tone:'neutral',title:'Link inválido',text:'Este link não é um identificador de sinal válido. Nenhum sinal foi criado no lugar.',retry:false};
  case 'unauthorized':return {kind:'message',tone:'neutral',title:'Acesso não autorizado',text:'Você não tem acesso a este sinal.',retry:false};
  case 'source-unavailable':return response.reason==='not-configured'
   ?{kind:'message',tone:'amber',title:'Fonte de sinais indisponível',text:'A fonte de sinais não está conectada neste ambiente.',retry:false}
   :{kind:'message',tone:'amber',title:'Fonte de sinais indisponível',text:'A fonte de sinais não respondeu corretamente. Nenhum sinal foi criado no lugar.',retry:true};
 }
}
