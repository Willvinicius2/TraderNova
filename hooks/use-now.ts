'use client';
import {useSyncExternalStore} from 'react';
// Relógio compartilhado (1 Hz). 0 no servidor e na hidratação; Date.now() atualizado a cada segundo no navegador.
const listeners=new Set<()=>void>();let tick=0,timer:ReturnType<typeof setInterval>|undefined;
function notify(){tick=Date.now();listeners.forEach(l=>l());}
function subscribe(listener:()=>void){notify();listeners.add(listener);if(!timer)timer=setInterval(notify,1000);return()=>{listeners.delete(listener);if(!listeners.size&&timer){clearInterval(timer);timer=undefined;}};}
export function useNow(){return useSyncExternalStore(subscribe,()=>tick,()=>0);}
