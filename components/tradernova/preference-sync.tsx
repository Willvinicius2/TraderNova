'use client';
import {useEffect,useRef} from 'react';
import {useTheme} from 'next-themes';
import {useDensity} from './appearance';
import type {Account} from './use-account';
import type {Preferences} from '@/lib/tradernova/account';
// Preferências na conta (#22): ao entrar, aplica as da conta; se a conta ainda não tem, envia as deste aparelho.
// Depois disso, cada mudança de tema, densidade ou alertas no app é gravada (com pequena espera). Sem conta, nada muda.
const themes=['essential','dark','light','system'] as const;
export function PreferenceSync({account,alertsOn,setAlertsOn}:{account:Account;alertsOn:boolean;setAlertsOn:(v:boolean)=>void}){
 const {theme,setTheme}=useTheme(),{density,setDensity}=useDensity();
 const userId=account.status==='signed-in'?account.session?.user.id??null:null,{withSession}=account;
 const t=themes.find(x=>x===theme)??null,prefs:Preferences={theme:t,density,alertsInApp:alertsOn},key=JSON.stringify(prefs);
 // Refs: os setters do provedor mudam de identidade a cada render e não devem reiniciar a carga.
 const live=useRef({prefs,setTheme,setDensity,setAlertsOn}),loadedFor=useRef<string|null>(null),synced=useRef<string|null>(null);
 useEffect(()=>{live.current={prefs,setTheme,setDensity,setAlertsOn};});
 useEffect(()=>{
  loadedFor.current=null;
  if(!userId)return;
  let alive=true;
  withSession(async(c,s)=>{
   const remote=await c.getPreferences(s),l=live.current;
   if(!alive)return;
   if(remote){
    const applied={theme:remote.theme??l.prefs.theme,density:remote.density??l.prefs.density,alertsInApp:remote.alertsInApp};
    if(remote.theme)l.setTheme(remote.theme);if(remote.density)l.setDensity(remote.density);l.setAlertsOn(remote.alertsInApp);
    synced.current=JSON.stringify(applied);
   }else{await c.savePreferences(s,l.prefs);synced.current=JSON.stringify(l.prefs);}
   if(alive)loadedFor.current=userId;
  }).catch(()=>{/* Preferências continuam locais; nova tentativa no próximo login. */});
  return ()=>{alive=false;};
 },[userId,withSession]);
 useEffect(()=>{
  if(!userId||loadedFor.current!==userId||synced.current===key)return;
  const timer=setTimeout(()=>{withSession(async(c,s)=>{await c.savePreferences(s,JSON.parse(key));synced.current=key;}).catch(()=>{/* Fica local; a próxima mudança tenta de novo. */});},800);
  return ()=>clearTimeout(timer);
 },[userId,key,withSession]);
 return null;
}
