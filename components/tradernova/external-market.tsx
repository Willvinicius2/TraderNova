'use client';
import {memo,useEffect,useRef,useState} from 'react';
import {ExternalLink,RefreshCw} from 'lucide-react';
import type {AssetId} from '@/lib/tradernova/domain';
import {chartWidgetOptions,marketChartUrl,marketSources,widgetStatus,type WidgetState} from '@/lib/tradernova/market-sources';
import {loadQuoteWidget} from '@/lib/tradernova/widget-loader';
import './external-market.css';
function useWidgetEnvironment(){
 const [environment,setEnvironment]=useState({online:true,visible:true,theme:'dark' as 'light'|'dark'});
 useEffect(()=>{
  const root=document.documentElement;
  const update=()=>{const theme=root.getAttribute('data-theme');const light=theme==='light'||root.classList.contains('light');setEnvironment({online:navigator.onLine,visible:!document.hidden,theme:light?'light':'dark'});};
  update();const observer=new MutationObserver(update);observer.observe(root,{attributes:true,attributeFilter:['class','data-theme']});
  window.addEventListener('online',update);window.addEventListener('offline',update);document.addEventListener('visibilitychange',update);
  return()=>{observer.disconnect();window.removeEventListener('online',update);window.removeEventListener('offline',update);document.removeEventListener('visibilitychange',update);};
 },[]);
 return environment;
}

export const ExternalQuote=memo(function ExternalQuote({asset}:{asset:AssetId}){
 const host=useRef<HTMLDivElement>(null),{online,visible,theme}=useWidgetEnvironment();
 const [state,setState]=useState<WidgetState>('loading'),[retry,setRetry]=useState(0);
 useEffect(()=>{
  const node=host.current;if(!node)return;node.replaceChildren();let cancelled=false;
  if(!online||!visible){setState(!online?'offline':'paused');return;}
  setState('loading');
  void loadQuoteWidget().then(()=>{
   if(cancelled)return;
   const quote=document.createElement('tv-single-ticker');quote.setAttribute('symbol',marketSources[asset].symbol);quote.setAttribute('theme',theme);
   node.appendChild(quote);setState('embedded');
  }).catch(()=>{if(!cancelled)setState('unavailable');});
  return()=>{cancelled=true;node.replaceChildren();};
 },[asset,online,visible,theme,retry]);
 return <div className="external-quote" aria-label={`Cotação de ${asset} por ${marketSources[asset].provider}`}>
  <div ref={host}/>
  {state!=='embedded'&&<div className="external-quote-message" role="status">{widgetStatus(state)}{state==='unavailable'&&<button className="text-button" onClick={()=>setRetry(n=>n+1)}><RefreshCw size={13}/> Recarregar</button>}</div>}
  <a className="external-attribution" href={marketChartUrl(asset)} target="_blank" rel="noopener noreferrer">{asset} no TradingView</a>
 </div>;
});

export function ExternalMarketPanel({asset,interval,onReturn}:{asset:AssetId;interval:string;onReturn?:()=>void}){
 const host=useRef<HTMLDivElement>(null),{online,visible,theme}=useWidgetEnvironment();
 const [state,setState]=useState<WidgetState>('loading'),[retry,setRetry]=useState(0);
 const source=marketSources[asset];
 useEffect(()=>{
  const node=host.current;if(!node)return;node.replaceChildren();let cancelled=false,frame:HTMLIFrameElement|null=null;
  if(!online||!visible){setState(!online?'offline':'paused');return;}
  setState('loading');
  const wrapper=document.createElement('div');wrapper.className='tradingview-widget-container';wrapper.style.cssText='height:100%;width:100%';
  const content=document.createElement('div');content.className='tradingview-widget-container__widget';content.style.cssText='height:calc(100% - 32px);width:100%';wrapper.appendChild(content);
  const attribution=document.createElement('div');attribution.className='tradingview-widget-copyright';
  const link=document.createElement('a');link.href=marketChartUrl(asset);link.target='_blank';link.rel='noopener noreferrer';link.textContent=`Gráfico de ${asset} por TradingView`;attribution.appendChild(link);wrapper.appendChild(attribution);
  const script=document.createElement('script');script.src='https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';script.type='text/javascript';script.async=true;script.textContent=JSON.stringify(chartWidgetOptions(asset,interval,theme));
  const timer=setTimeout(()=>{if(!cancelled)setState('unavailable');},18000);
  // iframe load means the panel loaded, not that its market feed is fresh.
  const loaded=()=>{if(!cancelled){clearTimeout(timer);setState('embedded');}};
  const observer=new MutationObserver(()=>{const found=wrapper.querySelector('iframe');if(found&&found!==frame){frame=found;frame.title=`Gráfico de ${asset} · ${source.provider} via TradingView`;frame.addEventListener('load',loaded,{once:true});}});
  observer.observe(wrapper,{childList:true,subtree:true});
  script.onerror=()=>{if(!cancelled){clearTimeout(timer);setState('unavailable');}};
  node.appendChild(wrapper);wrapper.appendChild(script);
  return()=>{cancelled=true;clearTimeout(timer);observer.disconnect();frame?.removeEventListener('load',loaded);script.onerror=null;node.replaceChildren();};
 },[asset,interval,theme,online,visible,retry,source.provider]);
 return <section className="external-market-panel">
  <div className="external-market-controls"><span className="tag">{widgetStatus(state)}</span><button className="text-button" onClick={()=>setRetry(n=>n+1)}><RefreshCw size={15}/> Recarregar painel</button><a className="text-button" href={marketChartUrl(asset)} target="_blank" rel="noopener noreferrer">Abrir fonte <ExternalLink size={14}/></a>{onReturn&&<button className="text-button" onClick={onReturn}>Voltar à conexão direta</button>}</div>
  <p className="external-market-description">{source.contract}. Confira o horário da cotação e o estado do mercado no próprio gráfico.</p>
  {state!=='embedded'&&<p className="external-market-message" role="status">{state==='unavailable'?'O painel demorou para responder ou foi bloqueado. Recarregue ou abra a fonte. Se houver uma mensagem dentro do gráfico, siga o aviso da fonte.':state==='offline'?'Você está sem internet. A conexão será retomada quando a rede voltar.':state==='paused'?'Atualizações pausadas enquanto o aplicativo está em segundo plano.':'Carregando gráfico e cotação da fonte…'}</p>}
  <div className="external-chart-host" ref={host}/>
  <p className="external-market-description">Indicadores e desenhos estão disponíveis na barra do gráfico. Esta conexão é para consulta visual; os dados não alimentam o robô nem os testes do laboratório.</p>
 </section>;
}
