import {livePairs,isLiveAsset,liveIntervals,parseKrakenHistory,type MarketCandle} from '@/lib/tradernova/live-market';
export const dynamic='force-dynamic';
type Result={asset:string;interval:number;source:'kraken-spot';receivedAt:string;bars:MarketCandle[]};
const cache=new Map<string,{expires:number;data:Result}>();
const pending=new Map<string,Promise<Result>>();
export async function GET(request:Request){
 const url=new URL(request.url),asset=url.searchParams.get('asset')??'',interval=Number(url.searchParams.get('interval'));
 if(!isLiveAsset(asset)||!(liveIntervals as readonly number[]).includes(interval))return Response.json({error:'Ativo ou intervalo não suportado.'},{status:400});
 const key=`${asset}:${interval}`,cached=cache.get(key);
 const headers={'Cache-Control':'no-store','X-Market-Source':'kraken-spot'};
 if(cached&&cached.expires>Date.now())return Response.json(cached.data,{headers});
 let work=pending.get(key);
 if(!work){work=(async()=>{
  const upstream=new URL('https://api.kraken.com/0/public/OHLC');upstream.searchParams.set('pair',livePairs[asset].rest);upstream.searchParams.set('interval',String(interval));
  const response=await fetch(upstream,{signal:AbortSignal.timeout(10000),headers:{Accept:'application/json'}});
  if(!response.ok)throw new Error('Fonte indisponível.');
  const bars=parseKrakenHistory(await response.json());
  const data:Result={asset,interval,source:'kraken-spot',receivedAt:new Date().toISOString(),bars};
  cache.set(key,{expires:Date.now()+15000,data});return data;
 })();pending.set(key,work);}
 try{return Response.json(await work,{headers});}catch{return Response.json({error:'Histórico da Kraken indisponível. As atualizações por negociação podem continuar pelo canal ao vivo.'},{status:502,headers});}finally{if(pending.get(key)===work)pending.delete(key);}
}
