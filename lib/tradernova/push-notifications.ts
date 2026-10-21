import {z} from 'zod';
import {assets,formatPrice} from './domain';
import {isPublicSignalId,resolveSignalView,type SignalRecord} from './signal-record';
// Fase 4: regras de notificação push (issues #33-#35). Puro e sem rede: quem envia é o servidor (worker), com dedup por sinal e dispositivo.
// Nada aqui executa ordens. Sem estratégia aprovada, só sai notificação rotulada como pesquisa e para quem optou por recebê-la. Ver docs/NOTIFICACOES.md.
export const pushInstruments=['XAUUSD','NAS100','BTCUSD','ETHUSD','SOLUSD','EURUSD','USDJPY'] as const;
export const expoPushTokenPattern=/^Expo(nent)?PushToken\[[A-Za-z0-9_-]{10,200}\]$/;
export function isExpoPushToken(value:unknown):value is string{return typeof value==='string'&&expoPushTokenPattern.test(value);}
export const signalDeepLink=(publicId:string)=>`tradernova://signal/${publicId.toLowerCase()}`;
// Canal Android criado pelo app (mobile/src/push.ts). Mudar aqui exige mudar lá.
export const pushChannelId='sinais';
// Sinal que vence em menos que isso não é enviado: chegaria vencido.
export const minLeadMs=15000;

// Preferências por usuário. Padrão: tudo desligado (opt-in).
export const notificationPreferencesSchema=z.object({
 enabled:z.boolean(),
 includeResearch:z.boolean(),
 mutedInstruments:z.array(z.enum(pushInstruments)).max(pushInstruments.length),
 mutedStrategies:z.array(z.string().min(1).max(40)).max(50)
});
export type NotificationPreferences=z.infer<typeof notificationPreferencesSchema>;
export const defaultNotificationPreferences:NotificationPreferences=Object.freeze({enabled:false,includeResearch:false,mutedInstruments:[],mutedStrategies:[]}) as NotificationPreferences;
export function readNotificationPreferences(raw:unknown):NotificationPreferences{
 const parsed=notificationPreferencesSchema.safeParse(raw);
 if(!parsed.success)return {...defaultNotificationPreferences,mutedInstruments:[],mutedStrategies:[]};
 return {...parsed.data,mutedInstruments:[...new Set(parsed.data.mutedInstruments)],mutedStrategies:[...new Set(parsed.data.mutedStrategies)]};
}
export function setInstrumentMuted(p:NotificationPreferences,instrument:typeof pushInstruments[number],muted:boolean):NotificationPreferences{
 const rest=p.mutedInstruments.filter(i=>i!==instrument);return {...p,mutedInstruments:muted?[...rest,instrument]:rest};
}
export function setStrategyMuted(p:NotificationPreferences,strategyId:string,muted:boolean):NotificationPreferences{
 const rest=p.mutedStrategies.filter(s=>s!==strategyId);return readNotificationPreferences({...p,mutedStrategies:muted?[...rest,strategyId]:rest});
}

// Registro de aprovação para o modo `alert`. Vazio enquanto nenhuma estratégia passar no protocolo (Fase 3).
export type AlertApproval={strategyId:string;strategyVersion:string;approvedAt:number;expiresAt:number};
export const alertApprovals:AlertApproval[]=[];
export function isApprovedForAlert(s:Pick<SignalRecord,'strategyId'|'strategyVersion'>,now:number,approvals:AlertApproval[]=alertApprovals){
 return approvals.some(a=>a.strategyId===s.strategyId&&a.strategyVersion===s.strategyVersion&&a.approvedAt<=now&&a.expiresAt>now);
}

export type PushLabel='research'|'alert';
export type SkipReason='invalid-id'|'invalidated'|'expired'|'test'|'unapproved-alert'|'research-off'|'disabled'|'research-opt-out'|'muted-instrument'|'muted-strategy';
export type Eligibility={send:true;label:PushLabel}|{send:false;reason:SkipReason};
// Envio de sinais de pesquisa (rotulados, com opt-in do usuário, issue #34) fica desligado no servidor até decisão do Will.
// Com o padrão, só `alert` de estratégia aprovada sai, e o registro de aprovação está vazio: nada é enviado.
export type PushPolicy={allowResearch:boolean};
export const defaultPushPolicy:PushPolicy=Object.freeze({allowResearch:false});
// Decide se um sinal pode virar notificação para um usuário. Regras do sinal primeiro, preferências depois.
export function notificationEligibility(s:SignalRecord,prefs:NotificationPreferences,now:number,approvals:AlertApproval[]=alertApprovals,policy:PushPolicy=defaultPushPolicy):Eligibility{
 if(!isPublicSignalId(s.publicId))return {send:false,reason:'invalid-id'};
 if(s.invalidatedAt!==null)return {send:false,reason:'invalidated'};
 if(now>=s.expiresAt-minLeadMs)return {send:false,reason:'expired'};
 if(s.mode==='test')return {send:false,reason:'test'};
 // `alert` sem aprovação vigente indica erro no pipeline: não envia nem rebaixa para pesquisa.
 if(s.mode==='alert'&&!isApprovedForAlert(s,now,approvals))return {send:false,reason:'unapproved-alert'};
 const label:PushLabel=s.mode==='alert'?'alert':'research';
 if(label==='research'&&!policy.allowResearch)return {send:false,reason:'research-off'};
 if(!prefs.enabled)return {send:false,reason:'disabled'};
 if(label==='research'&&!prefs.includeResearch)return {send:false,reason:'research-opt-out'};
 if((prefs.mutedInstruments as string[]).includes(s.instrument))return {send:false,reason:'muted-instrument'};
 if(prefs.mutedStrategies.includes(s.strategyId))return {send:false,reason:'muted-strategy'};
 return {send:true,label};
}

// Mensagem no formato do serviço Expo Push. Nunca leva dedupKey, preço de execução ou instrução de ordem.
export type ExpoPushMessage={to:string;title:string;body:string;data:{url:string;signalId:string;label:PushLabel};ttl:number;expiration:number;priority:'high';channelId:string;sound:'default'};
const sideLabel={buy:'compra',sell:'venda'} as const;
export function formatSignalPrice(value:number,instrument:string){
 const asset=assets.find(a=>a.id===instrument);
 return asset?formatPrice(value,asset):value.toLocaleString('pt-BR',{maximumFractionDigits:5});
}
export function buildPushMessage(s:SignalRecord,token:string,label:PushLabel,now:number,timeZone='America/Sao_Paulo'):ExpoPushMessage{
 const price=(v:number)=>formatSignalPrice(v,s.instrument);
 const until=new Date(s.expiresAt).toLocaleTimeString('pt-BR',{timeZone,hour:'2-digit',minute:'2-digit'});
 const title=`${label==='alert'?'Alerta':'Pesquisa'} · ${s.instrument} ${sideLabel[s.side]}`;
 const levels=`Ref. ${price(s.entryReference)} · stop ${price(s.stop)}${s.target===null?'':` · alvo ${price(s.target)}`}`;
 const body=`${label==='alert'?'Estratégia aprovada, confira antes de agir.':'Sinal de pesquisa, não é recomendação.'} ${levels}. Válido até ${until}.`;
 const ttl=Math.max(0,Math.floor((s.expiresAt-now)/1000));
 return {to:token,title,body,data:{url:signalDeepLink(s.publicId),signalId:s.publicId.toLowerCase(),label},ttl,expiration:Math.floor(s.expiresAt/1000),priority:'high',channelId:pushChannelId,sound:'default'};
}

export type PushDevice={id:string;userId:string;platform:'android'|'ios'|'web';token:string;enabled:boolean};
export type PlannedPush={signalId:string;deviceId:string;message:ExpoPushMessage};
export type PushSkip={signalId:string;deviceId?:string;userId?:string;reason:SkipReason|'invalid-token'|'already-delivered'|'platform'};
export const deliveryKey=(signalId:string,deviceId:string)=>`${signalId.toLowerCase()}|${deviceId}`;
// Planeja o envio: uma mensagem por (sinal, dispositivo) ainda não entregue. A garantia final contra duplicata é o claim no armazém.
export function planPushDispatch(input:{signals:SignalRecord[];devices:PushDevice[];preferences:Map<string,NotificationPreferences>;delivered:Set<string>;now:number;approvals?:AlertApproval[];policy?:PushPolicy}){
 const planned:PlannedPush[]=[],skipped:PushSkip[]=[],seen=new Set<string>();
 for(const s of input.signals){
  const signalId=s.publicId.toLowerCase();
  for(const d of input.devices){
   if(!d.enabled)continue;
   const key=deliveryKey(signalId,d.id);if(seen.has(key))continue;seen.add(key);
   if(d.platform==='web'){skipped.push({signalId,deviceId:d.id,reason:'platform'});continue;}
   if(!isExpoPushToken(d.token)){skipped.push({signalId,deviceId:d.id,reason:'invalid-token'});continue;}
   if(input.delivered.has(key)){skipped.push({signalId,deviceId:d.id,reason:'already-delivered'});continue;}
   const e=notificationEligibility(s,input.preferences.get(d.userId)??defaultNotificationPreferences,input.now,input.approvals,input.policy);
   if(!e.send){skipped.push({signalId,deviceId:d.id,userId:d.userId,reason:e.reason});continue;}
   planned.push({signalId,deviceId:d.id,message:buildPushMessage(s,d.token,e.label,input.now)});
  }
 }
 return {planned,skipped};
}

// Resposta do serviço Expo por mensagem (ticket).
export type ExpoPushTicket={status:'ok';id:string}|{status:'error';message:string;details?:{error?:string}};
export type DeliveryResult={status:'sent';ticketId:string}|{status:'failed';error:string};
// Armazém de entregas. claim é atômico (chave única sinal+dispositivo): quem não consegue o claim não envia.
// Isso dá no máximo uma notificação por sinal e dispositivo, mesmo com dois workers.
export interface PushDeliveryStore{
 delivered(signalIds:string[]):Promise<Set<string>>;
 claim(signalId:string,deviceId:string):Promise<boolean>;
 finish(signalId:string,deviceId:string,result:DeliveryResult):Promise<void>;
 disableDevice(deviceId:string,reason:string):Promise<void>;
}
export function createMemoryPushDeliveryStore(){
 const rows=new Map<string,{status:'claimed'|DeliveryResult['status'];ticketId?:string;error?:string}>(),disabled=new Map<string,string>();
 const store:PushDeliveryStore&{rows:typeof rows;disabled:typeof disabled}={rows,disabled,
  async delivered(ids){const wanted=new Set(ids.map(i=>i.toLowerCase()));return new Set([...rows.keys()].filter(k=>wanted.has(k.split('|')[0])));},
  async claim(signalId,deviceId){const key=deliveryKey(signalId,deviceId);if(rows.has(key))return false;rows.set(key,{status:'claimed'});return true;},
  async finish(signalId,deviceId,result){rows.set(deliveryKey(signalId,deviceId),result.status==='sent'?{status:'sent',ticketId:result.ticketId}:{status:'failed',error:result.error});},
  async disableDevice(deviceId,reason){disabled.set(deviceId,reason);}
 };
 return store;
}
export type PushSender=(messages:ExpoPushMessage[])=>Promise<ExpoPushTicket[]>;
export const expoBatchSize=100;
export async function dispatchPush(input:{signals:SignalRecord[];devices:PushDevice[];preferences:Map<string,NotificationPreferences>;now:number;approvals?:AlertApproval[];policy?:PushPolicy;store:PushDeliveryStore;send:PushSender}){
 const delivered=await input.store.delivered(input.signals.map(s=>s.publicId));
 const {planned,skipped}=planPushDispatch({...input,delivered});
 const claimed:PlannedPush[]=[];
 for(const p of planned){if(await input.store.claim(p.signalId,p.deviceId))claimed.push(p);else skipped.push({signalId:p.signalId,deviceId:p.deviceId,reason:'already-delivered'});}
 let sent=0,failed=0;const disabledDevices:string[]=[];
 for(let i=0;i<claimed.length;i+=expoBatchSize){
  const batch=claimed.slice(i,i+expoBatchSize);
  let tickets:ExpoPushTicket[]|null=null;
  try{tickets=await input.send(batch.map(p=>p.message));if(tickets.length!==batch.length)tickets=null;}catch{tickets=null;}
  for(const [j,p] of batch.entries()){
   const t=tickets?.[j];
   if(t?.status==='ok'){sent++;await input.store.finish(p.signalId,p.deviceId,{status:'sent',ticketId:t.id});continue;}
   failed++;
   const error=t?.status==='error'?(t.details?.error??'error'):'unreachable';
   await input.store.finish(p.signalId,p.deviceId,{status:'failed',error:error.slice(0,200)});
   // Token desinstalado ou revogado: desliga o dispositivo para não tentar de novo.
   if(error==='DeviceNotRegistered'&&!disabledDevices.includes(p.deviceId)){disabledDevices.push(p.deviceId);await input.store.disableDevice(p.deviceId,error);}
  }
 }
 return {sent,failed,skipped,disabledDevices};
}

// Cliente do serviço Expo Push (https://exp.host). Só no servidor. Não é chamado por nenhum fluxo ativo hoje.
export type PushFetch=(url:string,init:{method:'POST';headers:Record<string,string>;body:string;signal:AbortSignal;redirect:'manual'})=>Promise<{ok:boolean;status:number;text():Promise<string>}>;
export const expoPushUrl='https://exp.host/--/api/v2/push/send';
const ticketSchema=z.union([z.object({status:z.literal('ok'),id:z.string().min(1).max(200)}),z.object({status:z.literal('error'),message:z.string().max(2000),details:z.object({error:z.string().max(100).optional()}).passthrough().optional()})]);
export function createExpoPushSender({fetch:fetchFn,accessToken,timeoutMs=10000}:{fetch:PushFetch;accessToken?:string;timeoutMs?:number}):PushSender{
 return async messages=>{
  if(messages.length>expoBatchSize)throw new Error(`No máximo ${expoBatchSize} mensagens por envio.`);
  const headers:Record<string,string>={'Content-Type':'application/json',Accept:'application/json'};
  if(accessToken)headers.Authorization=`Bearer ${accessToken}`;
  const response=await fetchFn(expoPushUrl,{method:'POST',headers,body:JSON.stringify(messages),signal:AbortSignal.timeout(timeoutMs),redirect:'manual'});
  if(!response.ok)throw new Error(`HTTP ${response.status}`);
  const text=await response.text();if(text.length>1048576)throw new Error('Resposta grande demais.');
  const parsed=z.object({data:z.array(ticketSchema)}).safeParse(JSON.parse(text));
  if(!parsed.success||parsed.data.data.length!==messages.length)throw new Error('Resposta inválida do serviço de push.');
  return parsed.data.data as ExpoPushTicket[];
 };
}

// Central de alertas (#35): últimos sinais com o mesmo estado da ficha.
export type AlertCenterItem={signalId:string;instrument:string;side:SignalRecord['side'];strategy:string;mode:SignalRecord['mode'];generatedAt:number;expiresAt:number;state:'active'|'expired'|'invalidated';url:string};
export function alertCenterItems(records:SignalRecord[],now:number,limit=30):AlertCenterItem[]{
 const items:AlertCenterItem[]=[],seen=new Set<string>();
 for(const r of [...records].sort((a,b)=>b.generatedAt-a.generatedAt)){
  const id=r.publicId.toLowerCase();if(seen.has(id))continue;seen.add(id);
  const view=resolveSignalView(r.publicId,r,now);if(view.state!=='active'&&view.state!=='expired'&&view.state!=='invalidated')continue;
  items.push({signalId:id,instrument:r.instrument,side:r.side,strategy:`${r.strategyId} ${r.strategyVersion}`,mode:r.mode,generatedAt:r.generatedAt,expiresAt:r.expiresAt,state:view.state,url:`?aba=robo&sinal=${id}`});
  if(items.length>=limit)break;
 }
 return items;
}
