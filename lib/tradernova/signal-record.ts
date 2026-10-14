import {z} from 'zod';
// Contrato único de um sinal persistido. O ID público é opaco (UUID v4) e não concede acesso;
// a chave de deduplicação é separada e nunca aparece em links. Ver docs/SINAIS.md.
export const signalModes=['research','alert','test'] as const;
export type SignalMode=typeof signalModes[number];
export const signalRecordSchema=z.object({
 publicId:z.string().uuid(),
 dedupKey:z.string().min(1).max(300),
 strategyId:z.string().min(1).max(40),
 strategyVersion:z.string().min(1).max(40),
 instrument:z.string().min(1).max(20),
 provider:z.string().min(1).max(40),
 timeframeMinutes:z.number().int().positive(),
 side:z.enum(['buy','sell']),
 signalTime:z.number().int().nonnegative(),
 generatedAt:z.number().int().nonnegative(),
 expiresAt:z.number().int().nonnegative(),
 entryReference:z.number().positive(),
 stop:z.number().positive(),
 target:z.number().positive().nullable(),
 evidence:z.array(z.string().max(500)).max(20),
 mode:z.enum(signalModes),
 invalidatedAt:z.number().int().nonnegative().nullable(),
 invalidationReason:z.string().max(300).nullable()
}).refine(s=>s.expiresAt>s.generatedAt,{message:'expiresAt deve ser posterior a generatedAt'})
 .refine(s=>s.side==='buy'?s.stop<s.entryReference&&(s.target===null||s.target>s.entryReference):s.stop>s.entryReference&&(s.target===null||s.target<s.entryReference),{message:'stop/alvo incoerentes com a direção'});
export type SignalRecord=z.infer<typeof signalRecordSchema>;
export type DedupParts={strategyId:string;strategyVersion:string;provider:string;instrument:string;timeframeMinutes:number;side:'buy'|'sell';signalTime:number};
export function signalDedupKey(p:DedupParts){return [`${p.strategyId}@${p.strategyVersion}`,p.provider,p.instrument,String(p.timeframeMinutes),p.side,String(p.signalTime)].join('|');}
const uuidPattern=/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export function isPublicSignalId(id:unknown):id is string{return typeof id==='string'&&uuidPattern.test(id);}
export function newPublicSignalId(){return globalThis.crypto.randomUUID();}
export type SignalView={state:'active'|'expired'|'invalidated';record:SignalRecord}|{state:'not-found'|'invalid-id'|'unauthorized'};
// Resolve o que a ficha deve mostrar. Nunca cria nem substitui um sinal ausente.
export function resolveSignalView(id:unknown,record:SignalRecord|null|undefined,now:number,authorized=true):SignalView{
 if(!isPublicSignalId(id))return {state:'invalid-id'};
 if(!authorized)return {state:'unauthorized'};
 if(!record||record.publicId.toLowerCase()!==id.toLowerCase())return {state:'not-found'};
 if(record.invalidatedAt!==null)return {state:'invalidated',record};
 return {state:now>=record.expiresAt?'expired':'active',record};
}
// Armazenamento de sinais: a implementação concreta (arquivo no worker, Supabase no futuro) fica fora daqui.
export interface SignalStore{
 get(publicId:string):Promise<SignalRecord|null>;
 findByDedupKey(key:string):Promise<SignalRecord|null>;
 // Insere se a chave de deduplicação ainda não existe; devolve o registro que ficou guardado.
 insertIfAbsent(record:SignalRecord):Promise<{record:SignalRecord;created:boolean}>;
}
export function createMemorySignalStore(initial:SignalRecord[]=[]):SignalStore{
 const byId=new Map<string,SignalRecord>(),byKey=new Map<string,SignalRecord>();
 for(const r of initial){byId.set(r.publicId.toLowerCase(),r);byKey.set(r.dedupKey,r);}
 return {
  async get(id){return isPublicSignalId(id)?byId.get(id.toLowerCase())??null:null;},
  async findByDedupKey(key){return byKey.get(key)??null;},
  async insertIfAbsent(record){const parsed=signalRecordSchema.parse(record),existing=byKey.get(parsed.dedupKey);if(existing)return {record:existing,created:false};byId.set(parsed.publicId.toLowerCase(),parsed);byKey.set(parsed.dedupKey,parsed);return {record:parsed,created:true};}
 };
}
