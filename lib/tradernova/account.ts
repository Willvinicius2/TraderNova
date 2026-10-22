import {z} from 'zod';
import type {JournalEntry} from './domain';
// Conta do usuário (Fase 2): Supabase Auth por link mágico/código e dados do próprio usuário via PostgREST com o token dele.
// Só a chave PUBLICÁVEL chega ao navegador ou à WebView; a RLS no banco decide o acesso. Ver docs/CONTA.md.
export type AccountFetch=(url:string,init:{method:'GET'|'POST';signal:AbortSignal;headers:Record<string,string>;body?:string;redirect:'manual'})=>Promise<{ok:boolean;status:number;text():Promise<string>}>;
export type AuthConfig={url:string;publishableKey:string};
export type AccountUser={id:string;email:string};
export type Session={accessToken:string;refreshToken:string;expiresAt:number;user:AccountUser};
export type AccountErrorReason='unreachable'|'rejected'|'invalid-response'|'session-expired'|'rate-limited';
export class AccountError extends Error{constructor(readonly reason:AccountErrorReason,message:string=reason){super(message);}}
export const accountErrorText:Record<AccountErrorReason,string>={
 unreachable:'Não foi possível falar com o servidor da conta. Verifique a conexão.',
 rejected:'O servidor recusou o pedido. Confira o e-mail ou o código.',
 'invalid-response':'Resposta inesperada do servidor da conta.',
 'session-expired':'Sua sessão expirou. Entre novamente.',
 'rate-limited':'Muitas tentativas. Aguarde um pouco antes de pedir outro link.'
};
const maxBody=2_000_000;
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export const isUuid=(v:unknown):v is string=>typeof v==='string'&&uuid.test(v);
export const isEmail=(v:string)=>v.length<=254&&/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);

// Chave publicável: sb_publishable_… ou JWT legado com role anon. Chave secreta/service_role nunca é aceita no cliente.
export function isPublishableKey(key:string){
 const k=key.trim();
 if(k.startsWith('sb_publishable_'))return k.length>20;
 if(k.startsWith('sb_secret_'))return false;
 const parts=k.split('.');
 if(parts.length!==3)return false;
 try{
  const payload=JSON.parse(atob(parts[1].replace(/-/g,'+').replace(/_/g,'/').padEnd(Math.ceil(parts[1].length/4)*4,'=')));
  return payload?.role==='anon';
 }catch{return false;}
}
function checkUrl(raw:string){
 const url=new URL(raw);
 if(url.protocol!=='https:'&&!(url.protocol==='http:'&&['127.0.0.1','localhost'].includes(url.hostname)))throw new Error('O Supabase exige HTTPS (http só em 127.0.0.1/localhost para testes).');
 return url.origin;
}
// Configuração pública do login (rota /api/auth/config). Ausente ou com chave que não é publicável = null (login fica "pendente").
export function authConfigFromEnv(env:Record<string,string|undefined>):AuthConfig|null{
 const url=env.TRADERNOVA_SUPABASE_URL?.trim(),key=env.TRADERNOVA_SUPABASE_PUBLISHABLE_KEY?.trim();
 if(!url||!key||!isPublishableKey(key))return null;
 try{return {url:checkUrl(url),publishableKey:key};}catch{return null;}
}
export function parseAuthConfig(raw:unknown):AuthConfig|null{
 if(!raw||typeof raw!=='object')return null;
 const r=raw as Record<string,unknown>;
 if(r.configured!==true||typeof r.url!=='string'||typeof r.publishableKey!=='string'||!isPublishableKey(r.publishableKey))return null;
 try{return {url:checkUrl(r.url),publishableKey:r.publishableKey};}catch{return null;}
}

// PKCE (S256): o código que volta no link só vale com o verificador guardado neste navegador/WebView.
const b64url=(bytes:Uint8Array)=>btoa(String.fromCharCode(...bytes)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
export async function createPkce(){
 const verifier=b64url(crypto.getRandomValues(new Uint8Array(48)));
 const challenge=b64url(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(verifier))));
 return {verifier,challenge};
}

const sessionSchema=z.object({access_token:z.string().min(10),refresh_token:z.string().min(1),expires_in:z.number().positive().optional(),expires_at:z.number().positive().optional(),user:z.object({id:z.string().refine(isUuid),email:z.string().optional().nullable()})});
export function parseSession(raw:unknown,now:number):Session{
 const parsed=sessionSchema.safeParse(raw);
 if(!parsed.success)throw new AccountError('invalid-response','sessão inválida');
 const s=parsed.data,expiresAt=s.expires_at?s.expires_at*1000:now+(s.expires_in??3600)*1000;
 return {accessToken:s.access_token,refreshToken:s.refresh_token,expiresAt,user:{id:s.user.id,email:s.user.email??''}};
}
export const storedSessionSchema=z.object({accessToken:z.string().min(10),refreshToken:z.string().min(1),expiresAt:z.number().positive(),user:z.object({id:z.string().refine(isUuid),email:z.string()})});
// Renova quando falta menos de um minuto.
export const needsRefresh=(s:Session,now:number)=>s.expiresAt-now<60_000;

// Diário: entrada local <-> linha de public.journal_entries (migração 202610210101).
const localSignal=z.object({id:z.string().max(100),assetId:z.enum(['XAUUSD','NAS100','BTCUSD','ETHUSD','SOLUSD','EURUSD','USDJPY']),direction:z.enum(['Compra','Venda']),createdAt:z.number().finite(),expiresAt:z.number().finite(),entry:z.number().finite().positive(),stop:z.number().finite().positive(),target:z.number().finite().positive(),demo:z.literal(true),strategyId:z.string().max(40)});
export type JournalRow={client_id:string;decision:'reviewed'|'ignored';note:string|null;mode:'demo';signal_snapshot:z.infer<typeof localSignal>;decided_at:string;imported:boolean};
const decisionToRow={Revisado:'reviewed',Ignorado:'ignored'} as const;
const decisionFromRow={reviewed:'Revisado',ignored:'Ignorado'} as const;
// IDs antigos que não são UUID viram um UUID estável (SHA-256), para a importação continuar idempotente.
export async function stableClientId(id:string){
 if(isUuid(id))return id.toLowerCase();
 const h=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(`tradernova-journal:${id}`))),b=>b.toString(16).padStart(2,'0')).join('');
 return `${h.slice(0,8)}-${h.slice(8,12)}-5${h.slice(13,16)}-${((parseInt(h[16],16)&3)|8).toString(16)}${h.slice(17,20)}-${h.slice(20,32)}`;
}
export async function journalToRow(entry:JournalEntry,imported:boolean):Promise<JournalRow>{
 // Todo registro do diário de hoje é exemplo: sempre mode 'demo', com o retrato do sinal como foi visto.
 return {client_id:await stableClientId(entry.id),decision:decisionToRow[entry.decision],note:entry.note.trim()?entry.note.slice(0,2000):null,mode:'demo',signal_snapshot:localSignal.parse(entry.signal),decided_at:new Date(entry.createdAt).toISOString(),imported};
}
// Linha remota -> entrada exibida. Linhas fora do formato do app (ex.: sinais por usuário futuros) são ignoradas, nunca inventadas.
export function rowToJournal(row:unknown):JournalEntry|null{
 if(!row||typeof row!=='object')return null;
 const r=row as Record<string,unknown>,signal=localSignal.safeParse(r.signal_snapshot),created=Date.parse(String(r.decided_at));
 if(!signal.success||!Number.isFinite(created)||(r.decision!=='reviewed'&&r.decision!=='ignored'))return null;
 const id=isUuid(r.client_id)?r.client_id:isUuid(r.id)?r.id:null;
 if(!id)return null;
 return {id,signal:signal.data,decision:decisionFromRow[r.decision],createdAt:created,note:typeof r.note==='string'?r.note:''};
}

export type Preferences={theme:'essential'|'dark'|'light'|'system'|null;density:'comfortable'|'compact'|null;alertsInApp:boolean};
const prefSchema=z.object({theme:z.enum(['essential','dark','light','system']).nullable(),density:z.enum(['comfortable','compact']).nullable(),alerts_in_app:z.boolean()});

export function accountClient({url,publishableKey}:AuthConfig,fetchFn:AccountFetch,timeoutMs=8000){
 const origin=checkUrl(url);
 if(!isPublishableKey(publishableKey))throw new Error('Use a chave publicável do Supabase no cliente.');
 async function call(path:string,{method='POST',body,token,prefer}:{method?:'GET'|'POST';body?:unknown;token?:string;prefer?:string}={}):Promise<unknown>{
  const headers:Record<string,string>={apikey:publishableKey,Accept:'application/json',Authorization:`Bearer ${token??publishableKey}`};
  if(body!==undefined)headers['Content-Type']='application/json';
  if(prefer)headers.Prefer=prefer;
  let response;
  try{response=await fetchFn(`${origin}${path}`,{method,signal:AbortSignal.timeout(timeoutMs),headers,body:body===undefined?undefined:JSON.stringify(body),redirect:'manual'});}catch{throw new AccountError('unreachable');}
  if(response.status===429)throw new AccountError('rate-limited');
  if(response.status===401||(token&&response.status===403))throw new AccountError(token?'session-expired':'rejected');
  if(response.status>=400&&response.status<500)throw new AccountError('rejected',`HTTP ${response.status}`);
  if(!response.ok)throw new AccountError('unreachable',`HTTP ${response.status}`);
  let text;
  try{text=await response.text();}catch{throw new AccountError('invalid-response');}
  if(text.length>maxBody)throw new AccountError('invalid-response','grande demais');
  if(!text.trim())return null;
  try{return JSON.parse(text);}catch{throw new AccountError('invalid-response');}
 }
 const now=()=>Date.now();
 const rows=(v:unknown)=>{if(!Array.isArray(v))throw new AccountError('invalid-response');return v;};
 return {
  // Envia o e-mail com link (PKCE) e código. create_user: o primeiro acesso cria a conta.
  async requestEmailLink(email:string,redirectTo:string,codeChallenge:string){
   if(!isEmail(email))throw new AccountError('rejected','e-mail inválido');
   await call(`/auth/v1/otp?redirect_to=${encodeURIComponent(redirectTo)}`,{body:{email,create_user:true,code_challenge:codeChallenge,code_challenge_method:'s256'}});
  },
  // Código de 6 dígitos do mesmo e-mail: funciona mesmo quando o link abre em outro aparelho ou navegador.
  async verifyEmailCode(email:string,code:string){
   if(!isEmail(email)||!/^\d{6,10}$/.test(code))throw new AccountError('rejected','código inválido');
   return parseSession(await call('/auth/v1/verify',{body:{type:'email',email,token:code}}),now());
  },
  async exchangeCode(authCode:string,verifier:string){
   return parseSession(await call('/auth/v1/token?grant_type=pkce',{body:{auth_code:authCode,code_verifier:verifier}}),now());
  },
  async refresh(refreshToken:string){
   try{return parseSession(await call('/auth/v1/token?grant_type=refresh_token',{body:{refresh_token:refreshToken}}),now());}
   catch(e){if(e instanceof AccountError&&e.reason==='rejected')throw new AccountError('session-expired');throw e;}
  },
  async signOut(s:Session){await call('/auth/v1/logout',{token:s.accessToken});},
  async listJournal(s:Session){
   const data=rows(await call('/rest/v1/journal_entries?select=id,client_id,decision,note,mode,signal_snapshot,decided_at&order=decided_at.desc&limit=500',{method:'GET',token:s.accessToken}));
   return data.map(rowToJournal).filter((e):e is JournalEntry=>e!==null);
  },
  // Gravação idempotente pelo client_id (unique user_id,client_id). user_id vem do token no banco (default auth.uid()).
  async saveJournal(s:Session,entries:JournalRow[]){
   if(!entries.length)return 0;
   const data=rows(await call('/rest/v1/journal_entries?on_conflict=user_id,client_id',{body:entries,token:s.accessToken,prefer:'resolution=ignore-duplicates,return=representation'}));
   return data.length;
  },
  async getPreferences(s:Session):Promise<Preferences|null>{
   const data=rows(await call('/rest/v1/user_preferences?select=theme,density,alerts_in_app&limit=1',{method:'GET',token:s.accessToken}));
   if(!data.length)return null;
   const p=prefSchema.safeParse(data[0]);if(!p.success)throw new AccountError('invalid-response');
   return {theme:p.data.theme,density:p.data.density,alertsInApp:p.data.alerts_in_app};
  },
  async savePreferences(s:Session,p:Preferences){
   await call('/rest/v1/user_preferences?on_conflict=user_id',{body:{theme:p.theme,density:p.density,alerts_in_app:p.alertsInApp,updated_at:new Date().toISOString()},token:s.accessToken,prefer:'resolution=merge-duplicates,return=minimal'});
  },
  async exportData(s:Session){
   const data=await call('/rest/v1/rpc/export_my_data',{body:{},token:s.accessToken});
   if(!data||typeof data!=='object'||Array.isArray(data))throw new AccountError('invalid-response');
   return data as Record<string,unknown>;
  },
  async deleteAccount(s:Session){await call('/rest/v1/rpc/delete_my_account',{body:{},token:s.accessToken});}
 };
}
export type AccountClient=ReturnType<typeof accountClient>;
// Para onde o link do e-mail volta: no app, o deep link tradernova://auth (aberto na mesma WebView); no navegador, a aba Conta do site.
export function emailRedirectTarget(href:string,inApp:boolean){
 if(inApp)return 'tradernova://auth';
 const u=new URL(href);return `${u.origin}/?aba=conta`;
}
// Lê ?code= ou erro do retorno do link e devolve a URL limpa (sem o código).
export function readAuthReturn(href:string):{code:string|null;error:string|null;clean:string|null}{
 const u=new URL(href),hash=new URLSearchParams(u.hash.replace(/^#/,''));
 const rawCode=u.searchParams.get('code'),code=rawCode&&/^[A-Za-z0-9._-]{1,200}$/.test(rawCode)?rawCode:null;
 const error=u.searchParams.get('error_description')??hash.get('error_description')??u.searchParams.get('error')??hash.get('error');
 if(rawCode===null&&error===null)return {code:null,error:null,clean:null};
 for(const k of ['code','error','error_code','error_description'])u.searchParams.delete(k);
 if(hash.has('error')||hash.has('error_description'))u.hash='';
 return {code,error:error?error.slice(0,200):null,clean:u.href};
}
