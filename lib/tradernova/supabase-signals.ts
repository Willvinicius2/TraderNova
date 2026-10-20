import {isPublicSignalId,signalRecordSchema,type SignalRecord,type SignalStore} from './signal-record';
// Sinais de pesquisa no Supabase (tabela public.research_signals, migração 202610190001). Ver docs/SINAIS.md.
// A chave usada aqui é SEMPRE de servidor (rota da web ou worker); nunca vai para o navegador nem para o app.
export type SupabaseFetch=(url:string,init:{method?:'GET'|'POST';signal:AbortSignal;headers:Record<string,string>;body?:string;redirect:'manual'})=>Promise<{ok:boolean;status:number;text():Promise<string>}>;
export class SupabaseSignalError extends Error{constructor(readonly reason:'unreachable'|'invalid-response',message:string=reason){super(message);}}
export type ResearchSignalRow={public_id:string;dedup_key:string;strategy_id:string;strategy_version:string;instrument:string;provider:string;timeframe_minutes:number;side:'buy'|'sell';signal_time:number;generated_at:number;expires_at:number;entry_reference:number;stop:number;target:number|null;evidence:string[];mode:SignalRecord['mode'];invalidated_at:number|null;invalidation_reason:string|null};
const maxBody=262144;
// PostgREST pode devolver numeric/bigint como texto; converte só strings numéricas.
const num=(v:unknown)=>typeof v==='string'&&v.trim()!==''&&Number.isFinite(Number(v))?Number(v):v;
const numOrNull=(v:unknown)=>v===null?null:num(v);
export function recordToRow(r:SignalRecord):ResearchSignalRow{
 return {public_id:r.publicId.toLowerCase(),dedup_key:r.dedupKey,strategy_id:r.strategyId,strategy_version:r.strategyVersion,instrument:r.instrument,provider:r.provider,timeframe_minutes:r.timeframeMinutes,side:r.side,signal_time:r.signalTime,generated_at:r.generatedAt,expires_at:r.expiresAt,entry_reference:r.entryReference,stop:r.stop,target:r.target,evidence:r.evidence,mode:r.mode,invalidated_at:r.invalidatedAt,invalidation_reason:r.invalidationReason};
}
// Linha do banco -> SignalRecord validado. Qualquer divergência do contrato lança (vira source-unavailable, nunca um sinal).
export function rowToRecord(row:unknown):SignalRecord{
 if(!row||typeof row!=='object')throw new SupabaseSignalError('invalid-response','linha ausente');
 const r=row as Record<string,unknown>;
 const parsed=signalRecordSchema.safeParse({publicId:r.public_id,dedupKey:r.dedup_key,strategyId:r.strategy_id,strategyVersion:r.strategy_version,instrument:r.instrument,provider:r.provider,timeframeMinutes:num(r.timeframe_minutes),side:r.side,signalTime:num(r.signal_time),generatedAt:num(r.generated_at),expiresAt:num(r.expires_at),entryReference:num(r.entry_reference),stop:num(r.stop),target:numOrNull(r.target),evidence:r.evidence,mode:r.mode,invalidatedAt:numOrNull(r.invalidated_at),invalidationReason:r.invalidation_reason});
 if(!parsed.success)throw new SupabaseSignalError('invalid-response','registro inválido');
 return parsed.data;
}
export type SupabaseSignalsConfig={url:string;key:string;fetch:SupabaseFetch;timeoutMs?:number};
// Cliente PostgREST mínimo de uma tabela. Exportado para outras tabelas do servidor (ex.: worker_status).
export function supabaseTable({url,key,fetch:fetchFn,timeoutMs=5000}:SupabaseSignalsConfig,table:string){
 const origin=new URL(url);
 if(origin.protocol!=='https:'&&!(origin.protocol==='http:'&&['127.0.0.1','localhost'].includes(origin.hostname)))throw new Error('O Supabase exige HTTPS (http só em 127.0.0.1/localhost para testes).');
 if(!key.trim())throw new Error('Chave do Supabase ausente.');
 const base=`${origin.origin}/rest/v1/${table}`,auth={apikey:key,Authorization:`Bearer ${key}`,Accept:'application/json'};
 async function call(query:string,init:{method?:'GET'|'POST';headers?:Record<string,string>;body?:string}={}){
  let response;
  try{response=await fetchFn(`${base}?${query}`,{method:init.method??'GET',signal:AbortSignal.timeout(timeoutMs),headers:{...auth,...init.headers},body:init.body,redirect:'manual'});}catch{throw new SupabaseSignalError('unreachable');}
  if(!response.ok)throw new SupabaseSignalError('unreachable',`HTTP ${response.status}`);
  let rows:unknown;
  try{const text=await response.text();if(text.length>maxBody)throw new Error('grande demais');rows=JSON.parse(text);}catch{throw new SupabaseSignalError('invalid-response');}
  if(!Array.isArray(rows))throw new SupabaseSignalError('invalid-response');
  return rows;
 }
 // Uma linha no máximo: chaves únicas. Mais de uma é resposta inválida.
 async function one(query:string){const rows=await call(`${query}&select=*&limit=2`);if(rows.length>1)throw new SupabaseSignalError('invalid-response');return rows.length?rowToRecord(rows[0]):null;}
 return {call,one};
}
// Leitura por ID público (rota /api/signals/[id]). ID fora do formato nunca vira consulta.
export function supabaseSignalSource(cfg:SupabaseSignalsConfig){
 const c=supabaseTable(cfg,'research_signals');
 return {async read(id:string){
  if(!isPublicSignalId(id))return null;
  const record=await c.one(`public_id=eq.${encodeURIComponent(id.toLowerCase())}`);
  if(record&&record.publicId.toLowerCase()!==id.toLowerCase())throw new SupabaseSignalError('invalid-response');
  return record;
 }};
}
// Armazém do worker: idempotente pela chave de deduplicação (unique no banco + on_conflict).
export function supabaseSignalStore(cfg:SupabaseSignalsConfig):SignalStore{
 const c=supabaseTable(cfg,'research_signals'),source=supabaseSignalSource(cfg);
 const findByDedupKey=(key:string)=>c.one(`dedup_key=eq.${encodeURIComponent(key)}`);
 return {
  get:(id)=>source.read(id),
  findByDedupKey,
  async insertIfAbsent(record){
   const parsed=signalRecordSchema.parse(record);
   const rows=await c.call('on_conflict=dedup_key&select=*',{method:'POST',headers:{'Content-Type':'application/json',Prefer:'resolution=ignore-duplicates,return=representation'},body:JSON.stringify([recordToRow(parsed)])});
   if(rows.length===1)return {record:rowToRecord(rows[0]),created:true};
   if(rows.length>1)throw new SupabaseSignalError('invalid-response');
   // Conflito ignorado: devolve o registro que já estava guardado.
   const existing=await findByDedupKey(parsed.dedupKey);
   if(!existing)throw new SupabaseSignalError('invalid-response','conflito sem registro existente');
   return {record:existing,created:false};
  }
 };
}
// Configuração por ambiente (servidor). Ausente ou inválida = null.
export function supabaseSignalsFromEnv(env:Record<string,string|undefined>,keyVar:'TRADERNOVA_SUPABASE_READ_KEY'|'TRADERNOVA_SUPABASE_SERVICE_KEY',fetchFn:SupabaseFetch):SupabaseSignalsConfig|null{
 const url=env.TRADERNOVA_SUPABASE_URL?.trim(),key=env[keyVar]?.trim();
 if(!url||!key)return null;
 try{supabaseTable({url,key,fetch:fetchFn},'research_signals');return {url,key,fetch:fetchFn};}catch{return null;}
}
