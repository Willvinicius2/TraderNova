/** Future integration boundary. No market data or trading endpoint is enabled. */
export type Instrument = { id:string; display_symbol:string; provider:string; server:string; broker_symbol:string; contract_type:'spot'|'cfd'|'future'|'forex'|'index'; volume_type:'traded'|'ticks'|'unavailable'; tick_size:number; currency:string };
export type FeedState = 'unconfigured'|'live'|'delayed'|'stale'|'disconnected';
export type MarketSnapshot = { instrument_id:string; observed_at:string; received_at:string; bid:number; ask:number; source:string; mode:'live'|'delayed'|'demo' };
export interface ReadOnlyMarketProvider {
 readonly supportsOrderExecution:false;
 getInstruments():Promise<Instrument[]>;
 getSnapshot(instrumentId:string):Promise<MarketSnapshot>;
}
export function isUsableSnapshot(s:MarketSnapshot,now=Date.now(),maxAgeMs=15000):boolean {
 const t=Date.parse(s.observed_at),received=Date.parse(s.received_at);
 return s.mode==='live'&&!!s.source&&Number.isFinite(t)&&Number.isFinite(received)&&t<=now&&received<=now&&now-t<=maxAgeMs&&now-received<=maxAgeMs&&Number.isFinite(s.bid)&&Number.isFinite(s.ask)&&s.bid>0&&s.ask>=s.bid;
}
export type Entitlement = {plan:'free'|'pro';status:'inactive'|'active'|'expired';expires_at:string|null;provider:'apple'|'google'|'web'|null};
export function hasProAccess(e:Entitlement,now=Date.now()) {return e.plan==='pro'&&e.status==='active'&&e.expires_at!==null&&Date.parse(e.expires_at)>now;}
/** Adapter scaffold. Instantiate only after real Auth; no service-role key in browser. */
export function createSupabaseReader(url:string,publishableKey:string,getUserAccessToken:()=>Promise<string>) {
 const origin=new URL(url);if(origin.protocol!=='https:')throw new Error('Supabase exige HTTPS.');
 const tables=['signals','strategy_versions','test_runs','entitlements'] as const;
 return {async list(table:typeof tables[number]) {
  if(!tables.includes(table))throw new Error('Tabela não permitida.');
  const token=await getUserAccessToken();if(!token)throw new Error('Sessão autenticada necessária.');
  const res=await fetch(new URL(`/rest/v1/${table}?select=*&limit=100`,origin),{headers:{apikey:publishableKey,Authorization:`Bearer ${token}`},signal:AbortSignal.timeout(10000)});
  if(!res.ok)throw new Error(`Não foi possível carregar ${table} (${res.status}).`);
  return res.json() as Promise<Record<string,unknown>[]>;
 }};
}
