'use client';
import {useCallback,useEffect,useRef,useState} from 'react';
import {AccountError,accountClient,createPkce,emailRedirectTarget,needsRefresh,parseAuthConfig,readAuthReturn,storedSessionSchema,type AccountClient,type Session} from '@/lib/tradernova/account';
// Estado da conta no navegador/WebView. Sessão e verificador PKCE ficam no armazenamento deste aparelho.
const storageKey='tradernova-account-v1';
type Stored={session:Session|null;pending:{email:string;verifier:string;createdAt:number}|null};
const empty:Stored={session:null,pending:null};
function load():Stored{
 try{
  const raw=JSON.parse(localStorage.getItem(storageKey)||'null');
  if(!raw||typeof raw!=='object')return empty;
  const session=storedSessionSchema.safeParse(raw.session);
  const p=raw.pending,pending=p&&typeof p.email==='string'&&typeof p.verifier==='string'&&typeof p.createdAt==='number'&&Date.now()-p.createdAt<3_600_000?{email:p.email,verifier:p.verifier,createdAt:p.createdAt}:null;
  return {session:session.success?session.data:null,pending};
 }catch{return empty;}
}
function save(s:Stored){try{localStorage.setItem(storageKey,JSON.stringify(s));}catch{/* Sem armazenamento a sessão vale só nesta aba. */}}
export type AccountStatus='loading'|'unconfigured'|'signed-out'|'signed-in';
export function useAccount(){
 const [status,setStatus]=useState<AccountStatus>('loading'),[session,setSession]=useState<Session|null>(null),[pendingEmail,setPendingEmail]=useState<string|null>(null),[error,setError]=useState<string|null>(null);
 const client=useRef<AccountClient|null>(null),stored=useRef<Stored>(empty);
 const persist=useCallback((next:Stored)=>{stored.current=next;save(next);setSession(next.session);setPendingEmail(next.pending?.email??null);setStatus(next.session?'signed-in':'signed-out');},[]);
 useEffect(()=>{
  let alive=true;
  (async()=>{
   let cfg=null;
   try{const r=await fetch('/api/auth/config',{cache:'no-store'});if(r.ok)cfg=parseAuthConfig(await r.json());}catch{/* Sem servidor de configuração = login pendente. */}
   if(!alive)return;
   if(!cfg){setStatus('unconfigured');return;}
   const c=accountClient(cfg,(url,init)=>fetch(url,init));client.current=c;
   let s=load();
   const ret=readAuthReturn(location.href);
   if(ret.clean)history.replaceState({},'',ret.clean);
   if(ret.error)setError(`O link de acesso não funcionou: ${ret.error}`);
   if(ret.code){
    if(s.pending){
     try{s={session:await c.exchangeCode(ret.code,s.pending.verifier),pending:null};}
     catch(e){setError(e instanceof AccountError?'O link expirou ou já foi usado. Peça outro ou use o código do e-mail.':'Não foi possível entrar.');}
    }else setError('Abra o link no mesmo aparelho e navegador em que pediu o acesso, ou use o código do e-mail.');
   }
   if(s.session&&needsRefresh(s.session,Date.now())){
    try{s={...s,session:await c.refresh(s.session.refreshToken)};}
    catch(e){if(e instanceof AccountError&&e.reason==='session-expired')s={...s,session:null};}
   }
   if(alive)persist(s);
  })();
  return ()=>{alive=false;};
 },[persist]);
 // Executa uma chamada com sessão válida, renovando antes se preciso; sessão recusada = saída local.
 const withSession=useCallback(async<T,>(fn:(c:AccountClient,s:Session)=>Promise<T>):Promise<T>=>{
  const c=client.current;let s=stored.current.session;
  if(!c||!s)throw new AccountError('session-expired');
  try{
   if(needsRefresh(s,Date.now())){s=await c.refresh(s.refreshToken);persist({...stored.current,session:s});}
   return await fn(c,s);
  }catch(e){
   if(e instanceof AccountError&&e.reason==='session-expired')persist({...stored.current,session:null});
   throw e;
  }
 },[persist]);
 const requestLink=useCallback(async(email:string)=>{
  const c=client.current;if(!c)throw new AccountError('unreachable');
  const {verifier,challenge}=await createPkce();
  const inApp=typeof window!=='undefined'&&'ReactNativeWebView' in window;
  await c.requestEmailLink(email.trim(),emailRedirectTarget(location.href,inApp),challenge);
  setError(null);persist({...stored.current,pending:{email:email.trim(),verifier,createdAt:Date.now()}});
 },[persist]);
 const verifyCode=useCallback(async(code:string)=>{
  const c=client.current,p=stored.current.pending;if(!c||!p)throw new AccountError('rejected');
  const s=await c.verifyEmailCode(p.email,code.trim());
  setError(null);persist({session:s,pending:null});
 },[persist]);
 const cancelPending=useCallback(()=>persist({...stored.current,pending:null}),[persist]);
 // Sair encerra a sessão no servidor quando possível e sempre apaga a sessão deste aparelho. Dados locais ficam.
 const signOut=useCallback(async()=>{
  const c=client.current,s=stored.current.session;
  if(c&&s){try{await c.signOut(s);}catch{/* A sessão local é apagada de qualquer forma. */}}
  persist({session:null,pending:null});
 },[persist]);
 const deleteAccount=useCallback(async()=>{await withSession((c,s)=>c.deleteAccount(s));persist({session:null,pending:null});},[persist,withSession]);
 return {status,session,pendingEmail,error,setError,requestLink,verifyCode,cancelPending,signOut,deleteAccount,withSession};
}
export type Account=ReturnType<typeof useAccount>;
