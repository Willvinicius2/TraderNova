'use client';
import {useEffect,useRef,useState,useCallback} from 'react';
import {marketNow,marketClockReady,syncMarketClock} from '@/lib/tradernova/market-clock';
import {livePairs,liveAssetIds,isLiveAsset,emptyEntry,mergeCandles,parseOhlcEvent,parseTicker,retryDelay,readHistoryResponse,applyHistory,type MarketState,type MarketEntry,type MarketCandle} from '@/lib/tradernova/live-market';
const initial=(interval:number):MarketState=>({interval,connection:'connecting',entries:{},error:null,revision:0,epoch:0});
export function useLiveMarket(enabled:boolean,selected:string,interval:number){
 const [foreground,setForeground]=useState(true),[online,setOnline]=useState(true),[retry,setRetry]=useState(0),[state,setState]=useState<MarketState>(()=>initial(interval)),[historyStatus,setHistoryStatus]=useState({key:'',status:'loading',error:''});
 const current=useRef(state),generation=useRef(0);
 const manualReconnect=useCallback(()=>setRetry(n=>n+1),[]);
 useEffect(()=>{const visible=()=>setForeground(!document.hidden),network=()=>setOnline(navigator.onLine);visible();network();document.addEventListener('visibilitychange',visible);window.addEventListener('online',network);window.addEventListener('offline',network);return()=>{document.removeEventListener('visibilitychange',visible);window.removeEventListener('online',network);window.removeEventListener('offline',network);};},[]);
 const publish=useCallback(()=>{const s=current.current;setState({...s,entries:{...s.entries},revision:s.revision+1});s.revision++;},[]);
 useEffect(()=>{
  const gen=++generation.current;let disposed=false,ws:WebSocket|null=null,reconnectTimer:ReturnType<typeof setTimeout>|null=null,flushTimer:ReturnType<typeof setTimeout>|null=null,openTimer:ReturnType<typeof setTimeout>|null=null;let attempt=0,lastMessage=0,lastPing=0,pingId=100,pingSent:number|null=null;
  current.current={...initial(interval),entries:current.current.interval===interval?current.current.entries:{},epoch:current.current.epoch};
  if(!enabled||!foreground||!online){current.current.connection=!online?'offline':'paused';publish();return;}
  const fresh=()=>!disposed&&generation.current===gen;
  const flush=()=>{if(!flushTimer)flushTimer=setTimeout(()=>{flushTimer=null;if(fresh())publish();},200);};
  const send=(data:unknown)=>{if(ws?.readyState===WebSocket.OPEN)ws.send(JSON.stringify(data));};
  const ping=()=>{pingSent=performance.now();lastPing=performance.now();send({method:'ping',req_id:++pingId});};
  function schedule(){if(!fresh()||reconnectTimer)return;current.current.connection='reconnecting';publish();reconnectTimer=setTimeout(()=>{reconnectTimer=null;connect();},retryDelay(attempt++));}
  function connect(){
   if(!fresh())return;
   current.current.connection=attempt?'reconnecting':'connecting';current.current.error=null;
   for(const id of liveAssetIds){const e=current.current.entries[id];if(e)current.current.entries[id]={...e,hasUpdate:false,error:undefined};}publish();
   try{ws=new WebSocket('wss://ws.kraken.com/v2');}catch{current.current.error='Não foi possível abrir a conexão com a Kraken.';schedule();return;}
   const socket=ws;
   openTimer=setTimeout(()=>{if(fresh()&&socket.readyState!==WebSocket.OPEN){socket.close();schedule();}},12000);
   socket.onopen=()=>{if(!fresh())return socket.close();if(openTimer)clearTimeout(openTimer);lastMessage=performance.now();current.current.connection='connected';current.current.epoch++;current.current.error=null;publish();ping();
    send({method:'subscribe',params:{channel:'ohlc',symbol:liveAssetIds.map(id=>livePairs[id].ws),interval,snapshot:true},req_id:1});
    send({method:'subscribe',params:{channel:'ticker',symbol:liveAssetIds.map(id=>livePairs[id].ws),event_trigger:'trades',snapshot:true},req_id:2});
   };
   socket.onmessage=(event)=>{
    if(!fresh()||socket!==ws)return;lastMessage=performance.now();let message:Record<string,unknown>;
    try{message=JSON.parse(event.data);}catch{return;}if(!message||typeof message!=='object')return;
    if(message.method==='pong'&&message.req_id===pingId&&pingSent!==null){const wasReady=marketClockReady();if(syncMarketClock(message.time_in,message.time_out,pingSent)){if(!wasReady)for(const id of liveAssetIds){const entry=current.current.entries[id];if(entry)current.current.entries[id]={...entry,receivedAt:0,historyReceivedAt:0,wsReceivedAt:0,hasUpdate:false};}flush();}pingSent=null;return;}
    if(message.success===false){current.current.error='A fonte recusou uma assinatura de dados.';const result=message.result as {symbol?:string;channel?:string}|undefined;const id=liveAssetIds.find(id=>livePairs[id].ws===result?.symbol);if(id){const e=current.current.entries[id]??emptyEntry();current.current.entries[id]={...e,error:'Assinatura recusada pela fonte.'};}else current.current.connection='error';flush();return;}
    if(message.channel==='status'){const data=message.data as {system?:string}[]|undefined;if(data?.[0]?.system&&data[0].system!=='online'){current.current.error='A Kraken informou uma restrição operacional.';current.current.connection='error';flush();}return;}
    if(!Array.isArray(message.data)||!['snapshot','update'].includes(String(message.type)))return;
    if(message.channel==='ohlc')for(const raw of message.data){const parsed=parseOhlcEvent(raw,interval,marketNow());if(!parsed)continue;const old=current.current.entries[parsed.assetId]??emptyEntry();const bars=mergeCandles(old.bars,[parsed.candle]);const latest=bars.at(-1);const accepted=latest?.time===parsed.candle.time&&latest?.close===parsed.candle.close&&latest?.volume===parsed.candle.volume;
     current.current.entries[parsed.assetId]={...old,bars,receivedAt:accepted?marketNow():old.receivedAt,wsReceivedAt:accepted&&message.type==='update'?marketNow():old.wsReceivedAt,transport:accepted&&message.type==='update'?'ws':old.transport,hasUpdate:old.hasUpdate||(accepted&&message.type==='update')};if(accepted&&message.type==='update')attempt=0;flush();
    }
    if(message.channel==='ticker')for(const raw of message.data){const parsed=parseTicker(raw,marketNow());if(!parsed)continue;const old=current.current.entries[parsed.assetId]??emptyEntry();if(old.ticker&&old.ticker.timestamp>parsed.ticker.timestamp)continue;current.current.entries[parsed.assetId]={...old,ticker:parsed.ticker};flush();}
   };
   socket.onerror=()=>{if(fresh()&&socket===ws){current.current.error='Conexão com a fonte interrompida.';socket.close();}};
   socket.onclose=()=>{if(!fresh()||socket!==ws)return;if(openTimer)clearTimeout(openTimer);schedule();};
  }
  connect();
  const watchdog=setInterval(()=>{if(!fresh()||ws?.readyState!==WebSocket.OPEN)return;const time=performance.now();if(time-lastMessage>30000){ws.close();return;}if(time-lastPing>20000)ping();},5000);
  return()=>{disposed=true;if(reconnectTimer)clearTimeout(reconnectTimer);if(flushTimer)clearTimeout(flushTimer);if(openTimer)clearTimeout(openTimer);clearInterval(watchdog);if(ws){ws.onclose=null;ws.close();}};
 },[enabled,interval,foreground,online,retry,publish]);
 useEffect(()=>{
  if(!enabled||!foreground||!online)return;
  const key=`${selected}:${interval}`,gen=generation.current,controllers=new Set<AbortController>(),busy=new Set<string>();let cancelled=false;
  setHistoryStatus({key,status:current.current.entries[selected as keyof typeof livePairs]?.historyReceivedAt?'ready':'loading',error:''});
  async function load(id:keyof typeof livePairs){
   if(busy.has(id))return;busy.add(id);
   const controller=new AbortController();controllers.add(controller);const timeout=setTimeout(()=>controller.abort(),12000);
   try{
    const started=performance.now(),response=await fetch(`/api/market/candles?asset=${id}&interval=${interval}`,{signal:controller.signal,cache:'no-store'});
    if(!response.ok)throw new Error('Histórico temporariamente indisponível. Nova tentativa automática.');
    const payload=await response.json(),requestMs=performance.now()-started;
    const {bars,receivedAt}=readHistoryResponse(payload,id,interval,marketNow()-requestMs);
    if(cancelled||generation.current!==gen||current.current.interval!==interval)return;
    const old=current.current.entries[id]??emptyEntry();current.current.entries[id]=applyHistory(old,bars,receivedAt);publish();
    if(id===selected)setHistoryStatus({key,status:'ready',error:''});
   }catch(error){
    if(!cancelled&&id===selected)setHistoryStatus({key,status:'error',error:error instanceof Error&&error.name==='AbortError'?'A fonte demorou para responder. Tentando novamente.':error instanceof Error?error.message:'Histórico indisponível.'});
   }finally{clearTimeout(timeout);controllers.delete(controller);busy.delete(id);}
  }
  const attempted=new Map<string,number>();
  function refresh(){
   if(cancelled||generation.current!==gen)return;const now=marketNow();
   for(const id of liveAssetIds){
    const e=current.current.entries[id],wsFresh=current.current.connection==='connected'&&!!e?.wsReceivedAt&&now-e.wsReceivedAt<15000;
    const every=wsFresh?60000:id===selected?15000:30000;
    if(now-(e?.historyReceivedAt??0)>=every&&performance.now()-(attempted.get(id)??-Infinity)>=every){attempted.set(id,performance.now());void load(id);}
   }
  }
  refresh();const timer=setInterval(refresh,5000);
  return()=>{cancelled=true;clearInterval(timer);for(const c of controllers)c.abort();};
 },[enabled,selected,interval,foreground,online,retry,publish]);
 const effective=state.interval===interval?state:initial(interval);
 return {...effective,clockReady:marketClockReady(),history:historyStatus.key===`${selected}:${interval}`?historyStatus:{key:'',status:'loading',error:''},reconnect:manualReconnect};
}
