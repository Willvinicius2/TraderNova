import {z} from 'zod';
import {supabaseSignalsFromEnv} from './supabase-signals';
import type {SourceFetch} from './signal-source';
import {supabaseWorkerStatusReader,toStatusResponse,workerStatusSchema,type WorkerStatus,type WorkerStatusResponse} from './worker-status';
// Leitura server-side da saúde do worker, com a mesma escolha de fonte da rota de sinais:
// Supabase (URL + READ_KEY) tem prioridade; senão o servidor local do worker (GET /status). Sem fonte = not-configured.
export type StatusReader=()=>Promise<WorkerStatus[]>;
export class StatusSourceError extends Error{constructor(readonly reason:'unreachable'|'invalid-response'){super(reason);}}
export function workerHttpStatusReader(baseUrl:string,fetchFn:SourceFetch,timeoutMs=3000):StatusReader{
 const base=baseUrl.replace(/\/+$/,'');
 return async()=>{
  let response;
  try{response=await fetchFn(`${base}/status`,{signal:AbortSignal.timeout(timeoutMs),headers:{Accept:'application/json'},redirect:'manual'});}catch{throw new StatusSourceError('unreachable');}
  if(!response.ok)throw new StatusSourceError('unreachable');
  try{
   const text=await response.text();if(text.length>65536)throw new Error('grande demais');
   const parsed=z.array(workerStatusSchema).max(50).safeParse(JSON.parse(text));if(!parsed.success)throw new Error('inválido');
   return parsed.data;
  }catch{throw new StatusSourceError('invalid-response');}
 };
}
export function statusReaderFromEnv(env:Record<string,string|undefined>,fetchFn:SourceFetch):StatusReader|null{
 const supabase=supabaseSignalsFromEnv(env,'TRADERNOVA_SUPABASE_READ_KEY',fetchFn);
 if(supabase)return supabaseWorkerStatusReader(supabase);
 const raw=env.TRADERNOVA_SIGNAL_SOURCE_URL?.trim();if(!raw)return null;
 try{const url=new URL(raw);if(url.protocol!=='http:'&&url.protocol!=='https:')return null;return workerHttpStatusReader(url.href,fetchFn);}catch{return null;}
}
export async function lookupWorkerStatus(reader:StatusReader|null,now:number):Promise<WorkerStatusResponse>{
 if(!reader)return {state:'source-unavailable',reason:'not-configured'};
 try{return toStatusResponse(await reader(),now);}
 catch(error){const reason=(error as {reason?:unknown})?.reason;return {state:'source-unavailable',reason:reason==='invalid-response'?'invalid-response':'unreachable'};}
}
