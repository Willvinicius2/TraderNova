import {deliveryKey,readNotificationPreferences,type NotificationPreferences,type PushDeliveryStore,type PushDevice} from './push-notifications';
// Fase 4: leitura de aparelhos/preferências e registro de entregas no Supabase (migração 202610200101). Só servidor, com chave service_role.
// Cliente próprio porque precisa de PATCH (desligar aparelho); o de supabase-signals.ts só faz GET/POST.
export type SupabasePushFetch=(url:string,init:{method:'GET'|'POST'|'PATCH';signal:AbortSignal;headers:Record<string,string>;body?:string;redirect:'manual'})=>Promise<{ok:boolean;status:number;text():Promise<string>}>;
export type SupabasePushConfig={url:string;key:string;fetch:SupabasePushFetch;timeoutMs?:number};
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const maxBody=1048576;
export function supabasePushClient({url,key,fetch:fetchFn,timeoutMs=5000}:SupabasePushConfig){
 const origin=new URL(url);
 if(origin.protocol!=='https:'&&!(origin.protocol==='http:'&&['127.0.0.1','localhost'].includes(origin.hostname)))throw new Error('O Supabase exige HTTPS (http só em 127.0.0.1/localhost para testes).');
 if(!key.trim())throw new Error('Chave do Supabase ausente.');
 const auth={apikey:key,Authorization:`Bearer ${key}`,Accept:'application/json'};
 return async function call(table:string,query:string,init:{method?:'GET'|'POST'|'PATCH';prefer?:string;body?:unknown}={}):Promise<Record<string,unknown>[]>{
  const headers:Record<string,string>={...auth};
  if(init.body!==undefined)headers['Content-Type']='application/json';
  if(init.prefer)headers.Prefer=init.prefer;
  const response=await fetchFn(`${origin.origin}/rest/v1/${table}?${query}`,{method:init.method??'GET',signal:AbortSignal.timeout(timeoutMs),headers,body:init.body===undefined?undefined:JSON.stringify(init.body),redirect:'manual'});
  if(!response.ok)throw new Error(`Supabase HTTP ${response.status}`);
  const text=await response.text();
  if(text.length>maxBody)throw new Error('Resposta grande demais.');
  if(!text.trim())return [];
  const rows=JSON.parse(text);
  if(!Array.isArray(rows))throw new Error('Resposta inválida do Supabase.');
  return rows;
 };
}
const inList=(ids:string[])=>`in.(${ids.map(i=>encodeURIComponent(i.toLowerCase())).join(',')})`;
// Aparelhos ligados (android/ios) e preferências dos donos. Usuário sem linha de preferências fica com o padrão (desligado).
export async function loadPushTargets(cfg:SupabasePushConfig,limit=1000):Promise<{devices:PushDevice[];preferences:Map<string,NotificationPreferences>}>{
 const call=supabasePushClient(cfg);
 const rows=await call('push_devices',`enabled=is.true&platform=in.(android,ios)&select=id,user_id,platform,device_reference&order=id&limit=${limit}`);
 const devices:PushDevice[]=[];
 for(const r of rows){
  if(typeof r.id!=='string'||!uuid.test(r.id)||typeof r.user_id!=='string'||!uuid.test(r.user_id)||(r.platform!=='android'&&r.platform!=='ios')||typeof r.device_reference!=='string')continue;
  devices.push({id:r.id.toLowerCase(),userId:r.user_id.toLowerCase(),platform:r.platform,token:r.device_reference,enabled:true});
 }
 const preferences=new Map<string,NotificationPreferences>();
 const users=[...new Set(devices.map(d=>d.userId))];
 for(let i=0;i<users.length;i+=100){
  const prefRows=await call('notification_preferences',`user_id=${inList(users.slice(i,i+100))}&select=user_id,enabled,include_research,muted_instruments,muted_strategies`);
  for(const r of prefRows)if(typeof r.user_id==='string')preferences.set(r.user_id.toLowerCase(),readNotificationPreferences({enabled:r.enabled,includeResearch:r.include_research,mutedInstruments:r.muted_instruments,mutedStrategies:r.muted_strategies}));
 }
 return {devices,preferences};
}
export function supabasePushDeliveryStore(cfg:SupabasePushConfig):PushDeliveryStore{
 const call=supabasePushClient(cfg);
 return {
  async delivered(signalIds){
   const ids=signalIds.filter(i=>uuid.test(i)),out=new Set<string>();
   for(let i=0;i<ids.length;i+=50){
    const rows=await call('push_deliveries',`signal_public_id=${inList(ids.slice(i,i+50))}&select=signal_public_id,device_id`);
    for(const r of rows)if(typeof r.signal_public_id==='string'&&typeof r.device_id==='string')out.add(deliveryKey(r.signal_public_id,r.device_id.toLowerCase()));
   }
   return out;
  },
  // Insere ou ignora: só quem recebeu a linha de volta pode enviar.
  async claim(signalId,deviceId){
   const rows=await call('push_deliveries','on_conflict=signal_public_id,device_id&select=signal_public_id',{method:'POST',prefer:'resolution=ignore-duplicates,return=representation',body:[{signal_public_id:signalId.toLowerCase(),device_id:deviceId,status:'claimed'}]});
   return rows.length===1;
  },
  async finish(signalId,deviceId,result){
   const body=result.status==='sent'?{status:'sent',ticket_id:result.ticketId,error:null}:{status:'failed',ticket_id:null,error:result.error.slice(0,200)};
   await call('push_deliveries',`signal_public_id=eq.${encodeURIComponent(signalId.toLowerCase())}&device_id=eq.${encodeURIComponent(deviceId)}`,{method:'PATCH',prefer:'return=minimal',body:{...body,updated_at:new Date().toISOString()}});
  },
  async disableDevice(deviceId,reason){
   await call('push_devices',`id=eq.${encodeURIComponent(deviceId)}`,{method:'PATCH',prefer:'return=minimal',body:{enabled:false,disabled_reason:reason.slice(0,200),updated_at:new Date().toISOString()}});
  }
 };
}
