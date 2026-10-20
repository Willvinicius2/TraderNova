import {z} from 'zod';
import {supabaseTable,SupabaseSignalError,type SupabaseSignalsConfig} from './supabase-signals';
// Saúde do worker (heartbeat): uma linha por combinação provedor/par/intervalo, regravada a cada ciclo. Ver docs/WORKER.md.
// "Ativo" só diz que o worker rodou há pouco; se o mercado está ao vivo é o feedState que diz, nunca o contrário.
export const feedStates=['ao_vivo','atrasado','desconectado','historico_insuficiente'] as const;
export const workerStatusSchema=z.object({
 provider:z.string().min(1).max(40),
 instrument:z.string().min(1).max(20),
 timeframeMinutes:z.number().int().positive(),
 pollSeconds:z.number().int().min(5).max(600),
 lastCycleAt:z.number().int().nonnegative(),
 lastSuccessAt:z.number().int().nonnegative().nullable(),
 feedState:z.enum(feedStates),
 lastClosedOpenTime:z.number().int().nonnegative().nullable()
}).strict();
export type WorkerStatus=z.infer<typeof workerStatusSchema>;
export type WorkerHealth='ativo'|'atrasado'|'parado';
/** Ativo: último ciclo dentro de 2 consultas + 1 min. Atrasado: até 15 min (ou 6 consultas, o que for maior). Depois disso, parado. Relógio adiantado conta como parado. */
export function workerHealth(status:Pick<WorkerStatus,'lastCycleAt'|'pollSeconds'>,now:number):WorkerHealth{
 const age=now-status.lastCycleAt,poll=status.pollSeconds*1000;
 if(age<-60000)return 'parado';
 if(age<=2*poll+60000)return 'ativo';
 if(age<=Math.max(15*60000,6*poll))return 'atrasado';
 return 'parado';
}
export type WorkerStatusResponse={state:'ok';checkedAt:number;workers:Array<WorkerStatus&{health:WorkerHealth}>}|{state:'source-unavailable';reason:'not-configured'|'unreachable'|'invalid-response'};
export const workerStatusResponseSchema=z.discriminatedUnion('state',[
 z.object({state:z.literal('ok'),checkedAt:z.number(),workers:z.array(workerStatusSchema.extend({health:z.enum(['ativo','atrasado','parado'])}).strict()).max(50)}),
 z.object({state:z.literal('source-unavailable'),reason:z.enum(['not-configured','unreachable','invalid-response'])})
]);
const num=(v:unknown)=>typeof v==='string'&&v.trim()!==''&&Number.isFinite(Number(v))?Number(v):v;
const numOrNull=(v:unknown)=>v===null?null:num(v);
export const statusToRow=(s:WorkerStatus)=>({provider:s.provider,instrument:s.instrument,timeframe_minutes:s.timeframeMinutes,poll_seconds:s.pollSeconds,last_cycle_at:s.lastCycleAt,last_success_at:s.lastSuccessAt,feed_state:s.feedState,last_closed_open_time:s.lastClosedOpenTime});
export function rowToStatus(row:unknown):WorkerStatus{
 const r=(row&&typeof row==='object'?row:{}) as Record<string,unknown>;
 const parsed=workerStatusSchema.safeParse({provider:r.provider,instrument:r.instrument,timeframeMinutes:num(r.timeframe_minutes),pollSeconds:num(r.poll_seconds),lastCycleAt:num(r.last_cycle_at),lastSuccessAt:numOrNull(r.last_success_at),feedState:r.feed_state,lastClosedOpenTime:numOrNull(r.last_closed_open_time)});
 if(!parsed.success)throw new SupabaseSignalError('invalid-response','status inválido');
 return parsed.data;
}
const columns='provider,instrument,timeframe_minutes,poll_seconds,last_cycle_at,last_success_at,feed_state,last_closed_open_time';
/** Gravação (worker, chave de serviço): upsert pela chave provider/instrument/timeframe_minutes. */
export function supabaseWorkerStatusWriter(cfg:SupabaseSignalsConfig){
 const t=supabaseTable(cfg,'worker_status');
 return async(status:WorkerStatus)=>{
  const parsed=workerStatusSchema.parse(status);
  await t.call(`on_conflict=provider,instrument,timeframe_minutes&select=${columns}`,{method:'POST',headers:{'Content-Type':'application/json',Prefer:'resolution=merge-duplicates,return=representation'},body:JSON.stringify([statusToRow(parsed)])});
 };
}
/** Leitura (rota da web, chave de leitura do servidor). */
export function supabaseWorkerStatusReader(cfg:SupabaseSignalsConfig){
 const t=supabaseTable(cfg,'worker_status');
 return async()=>{const rows=await t.call(`select=${columns}&order=instrument.asc,timeframe_minutes.asc&limit=50`);return rows.map(rowToStatus);};
}
/** Monta a resposta da rota: saúde calculada no servidor com o relógio do servidor. */
export function toStatusResponse(statuses:WorkerStatus[],now:number):WorkerStatusResponse{
 return {state:'ok',checkedAt:now,workers:statuses.map((s)=>({...s,health:workerHealth(s,now)}))};
}
// Modelo de tela (sem React) para a aba Robô. Só diz "feed ao vivo" com worker ativo; com worker atrasado/parado mostra o último estado conhecido.
const healthLabel:Record<WorkerHealth,string>={ativo:'Ativo',atrasado:'Atrasado',parado:'Parado'};
const feedLabel:Record<WorkerStatus['feedState'],string>={ao_vivo:'feed ao vivo',atrasado:'feed atrasado',desconectado:'feed desconectado',historico_insuficiente:'histórico insuficiente'};
export type WorkerStatusView={kind:'loading'}|{kind:'message';text:string}|{kind:'list';items:Array<{key:string;label:string;health:WorkerHealth;healthLabel:string;tone:'positive'|'amber'|'neutral';detail:string}>};
export function describeWorkerStatus(response:WorkerStatusResponse|null,timeZone?:string):WorkerStatusView{
 if(!response)return {kind:'loading'};
 if(response.state!=='ok')return {kind:'message',text:response.reason==='not-configured'?'O worker de pesquisa não está conectado neste ambiente.':'Não foi possível consultar a saúde do worker agora.'};
 if(!response.workers.length)return {kind:'message',text:'O worker de pesquisa ainda não registrou nenhum ciclo.'};
 const time=(ms:number)=>new Date(ms).toLocaleString('pt-BR',{timeZone,day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});
 return {kind:'list',items:response.workers.map((w)=>({
  key:`${w.provider}_${w.instrument}_${w.timeframeMinutes}`,
  label:`${w.instrument} · ${w.timeframeMinutes%60===0?`H${w.timeframeMinutes/60}`:`M${w.timeframeMinutes}`}`,
  health:w.health,healthLabel:healthLabel[w.health],tone:w.health==='ativo'?'positive':w.health==='atrasado'?'amber':'neutral',
  detail:`Último ciclo ${time(w.lastCycleAt)} · ${w.health==='ativo'?feedLabel[w.feedState]:`último estado: ${feedLabel[w.feedState]}`}`
 }))};
}
