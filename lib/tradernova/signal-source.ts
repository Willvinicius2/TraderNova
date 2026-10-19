import {isPublicSignalId,resolveSignalView,signalRecordSchema,type SignalRecord,type SignalView} from './signal-record';
import {SupabaseSignalError,supabaseSignalSource,supabaseSignalsFromEnv} from './supabase-signals';
// Leitura server-side de um sinal persistido por um adaptador EXPLÍCITO escolhido por ambiente. Sem fonte configurada nada é inventado. Ver docs/SINAIS.md.
export type SourceUnavailableReason='not-configured'|'unreachable'|'invalid-response';
export type SignalApiResponse=SignalView|{state:'source-unavailable';reason:SourceUnavailableReason};
export type SignalSource={read(id:string):Promise<SignalRecord|null>};
export type SourceFetch=(url:string,init:{method?:'GET'|'POST';signal:AbortSignal;headers:Record<string,string>;body?:string;redirect:'manual'})=>Promise<{ok:boolean;status:number;text():Promise<string>}>;
export class SourceError extends Error{constructor(readonly reason:Exclude<SourceUnavailableReason,'not-configured'>){super(reason);}}
const maxBody=65536;
// Adaptador do worker local (GET /signals/:id). 404 = sem registro; qualquer outra falha, timeout ou corpo inválido vira SourceError.
export function workerHttpSource(baseUrl:string,fetchFn:SourceFetch,timeoutMs=3000):SignalSource{
 const base=baseUrl.replace(/\/+$/,'');
 return {async read(id){
  let response;
  try{response=await fetchFn(`${base}/signals/${encodeURIComponent(id)}`,{signal:AbortSignal.timeout(timeoutMs),headers:{Accept:'application/json'},redirect:'manual'});}catch{throw new SourceError('unreachable');}
  if(response.status===404)return null;
  if(!response.ok)throw new SourceError('unreachable');
  try{
   const text=await response.text();if(text.length>maxBody)throw new Error('grande demais');
   const parsed=signalRecordSchema.safeParse(JSON.parse(text));if(!parsed.success)throw new Error('registro inválido');
   return parsed.data;
  }catch{throw new SourceError('invalid-response');}
 }};
}
// Adaptador do Supabase (tabela research_signals). Erros do cliente viram SourceError com o mesmo motivo.
export function supabaseSource(cfg:Parameters<typeof supabaseSignalSource>[0]):SignalSource{
 const source=supabaseSignalSource(cfg);
 return {async read(id){try{return await source.read(id);}catch(error){throw new SourceError(error instanceof SupabaseSignalError?error.reason:'unreachable');}}};
}
// Escolha do adaptador: Supabase (TRADERNOVA_SUPABASE_URL + TRADERNOVA_SUPABASE_READ_KEY, só no servidor) tem prioridade;
// senão TRADERNOVA_SIGNAL_SOURCE_URL (worker local, http/https). Nada configurado ou inválido = null (fonte não conectada).
export function signalSourceFromEnv(env:Record<string,string|undefined>,fetchFn:SourceFetch):SignalSource|null{
 const supabase=supabaseSignalsFromEnv(env,'TRADERNOVA_SUPABASE_READ_KEY',fetchFn);
 if(supabase)return supabaseSource(supabase);
 const raw=env.TRADERNOVA_SIGNAL_SOURCE_URL?.trim();if(!raw)return null;
 try{const url=new URL(raw);if(url.protocol!=='http:'&&url.protocol!=='https:')return null;return workerHttpSource(url.href,fetchFn);}catch{return null;}
}
export const statusByState:Record<SignalApiResponse['state'],number>={active:200,expired:200,invalidated:200,'not-found':404,'invalid-id':400,unauthorized:401,'source-unavailable':503};
// authorize: ponto de encaixe da autorização por usuário (ainda não há login; hoje sempre true e 'unauthorized' nunca é produzido).
export async function lookupSignal(id:unknown,source:SignalSource|null,now:number,authorize:(id:string)=>boolean|Promise<boolean>=()=>true):Promise<{status:number;body:SignalApiResponse}>{
 const done=(body:SignalApiResponse)=>({status:statusByState[body.state],body});
 if(!isPublicSignalId(id))return done({state:'invalid-id'});
 if(!await authorize(id))return done({state:'unauthorized'});
 if(!source)return done({state:'source-unavailable',reason:'not-configured'});
 try{return done(resolveSignalView(id,await source.read(id),now));}
 catch(error){return done({state:'source-unavailable',reason:error instanceof SourceError?error.reason:'unreachable'});}
}
