'use client';
import {memo,useEffect,useMemo,useRef,useState,useSyncExternalStore} from 'react';
import {ExternalLink,RefreshCw} from 'lucide-react';
import type {AssetId} from '@/lib/tradernova/domain';
import {chartWidgetOptions,technicalWidgetOptions,marketChartUrl,marketSources,widgetStatus,type WidgetState} from '@/lib/tradernova/market-sources';
import {loadQuoteWidget} from '@/lib/tradernova/widget-loader';
import './external-market.css';
function subscribeEnvironment(update:()=>void){
 const root=document.documentElement,observer=new MutationObserver(update);observer.observe(root,{attributes:true,attributeFilter:['class','data-theme']});
 window.addEventListener('online',update);window.addEventListener('offline',update);document.addEventListener('visibilitychange',update);
 return()=>{observer.disconnect();window.removeEventListener('online',update);window.removeEventListener('offline',update);document.removeEventListener('visibilitychange',update);};
}
function environmentSnapshot(){const root=document.documentElement,theme=root.getAttribute('data-theme'),light=theme==='light'||root.classList.contains('light');return `${navigator.onLine}|${!document.hidden}|${light?'light':'dark'}`;}
function useWidgetEnvironment(){
 const snapshot=useSyncExternalStore(subscribeEnvironment,environmentSnapshot,()=>'true|true|dark');
 return useMemo(()=>{const [online,visible,theme]=snapshot.split('|');return {online:online==='true',visible:visible==='true',theme:theme as 'light'|'dark'};},[snapshot]);
}
// Status is keyed by the widget inputs: a new key reads as 'loading' until the async callbacks report back (no setState inside effects).
type WidgetStatus={key:string;value:WidgetState};
function useWidgetState(key:string,online:boolean,visible:boolean):[WidgetState,(next:WidgetStatus)=>void]{
 const [stored,setStored]=useState<WidgetStatus>({key,value:'loading'});
 return [!online?'offline':!visible?'paused':stored.key===key?stored.value:'loading',setStored];
}

export const ExternalQuote=memo(function ExternalQuote({asset}:{asset:AssetId}){
 const host=useRef<HTMLDivElement>(null),{online,visible,theme}=useWidgetEnvironment();
 const [retry,setRetry]=useState(0),key=`${asset}|${online}|${visible}|${theme}|${retry}`,[state,setState]=useWidgetState(key,online,visible);
 useEffect(()=>{
  const node=host.current;if(!node)return;node.replaceChildren();let cancelled=false;
  if(!online||!visible)return;
  void loadQuoteWidget().then(()=>{
   if(cancelled)return;
   const quote=document.createElement('tv-single-ticker');quote.setAttribute('symbol',marketSources[asset].symbol);quote.setAttribute('theme',theme);quote.setAttribute('transparent','');
   node.appendChild(quote);setState({key,value:'embedded'});
  }).catch(()=>{if(!cancelled)setState({key,value:'unavailable'});});
  return()=>{cancelled=true;node.replaceChildren();};
 },[asset,online,visible,theme,retry,key,setState]);
 return <div className="external-quote" aria-label={`Cotação de ${asset} por ${marketSources[asset].provider}`}>
  <div ref={host}/>
  {state!=='embedded'&&<div className="external-quote-message" role="status">{widgetStatus(state)}{state==='unavailable'&&<button className="text-button" onClick={()=>setRetry(n=>n+1)}><RefreshCw size={13}/> Recarregar</button>}</div>}
  {state!=='embedded'&&<a className="external-attribution" href={marketChartUrl(asset)} target="_blank" rel="noopener noreferrer">Abrir cotação <ExternalLink size={12}/></a>}
 </div>;
});

export function ExternalMarketPanel({asset,interval,onReturn}:{asset:AssetId;interval:string;onReturn?:()=>void}){
 const host=useRef<HTMLDivElement>(null),{online,visible,theme}=useWidgetEnvironment();
 const [retry,setRetry]=useState(0),key=`${asset}|${interval}|${online}|${visible}|${theme}|${retry}`,[state,setState]=useWidgetState(key,online,visible);
 const source=marketSources[asset];
 useEffect(()=>{
  const node=host.current;if(!node)return;node.replaceChildren();let cancelled=false,frame:HTMLIFrameElement|null=null;
  if(!online||!visible)return;
  const wrapper=document.createElement('div');wrapper.className='tradingview-widget-container';wrapper.style.cssText='height:100%;width:100%';
  const content=document.createElement('div');content.className='tradingview-widget-container__widget';content.style.cssText='height:calc(100% - 32px);width:100%';wrapper.appendChild(content);
  const attribution=document.createElement('div');attribution.className='tradingview-widget-copyright';
  const link=document.createElement('a');link.href=marketChartUrl(asset);link.target='_blank';link.rel='noopener noreferrer';link.textContent=`Gráfico de ${asset} por TradingView`;attribution.appendChild(link);wrapper.appendChild(attribution);
  const script=document.createElement('script');script.src='https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';script.type='text/javascript';script.async=true;script.textContent=JSON.stringify(chartWidgetOptions(asset,interval,theme));
  const timer=setTimeout(()=>{if(!cancelled)setState({key,value:'unavailable'});},18000);
  // iframe load means the panel loaded, not that its market feed is fresh.
  const loaded=()=>{if(!cancelled){clearTimeout(timer);setState({key,value:'embedded'});}};
  const observer=new MutationObserver(()=>{const found=wrapper.querySelector('iframe');if(found&&found!==frame){frame=found;frame.title=`Gráfico de ${asset} · ${source.provider} via TradingView`;frame.addEventListener('load',loaded,{once:true});}});
  observer.observe(wrapper,{childList:true,subtree:true});
  script.onerror=()=>{if(!cancelled){clearTimeout(timer);setState({key,value:'unavailable'});}};
  node.appendChild(wrapper);wrapper.appendChild(script);
  return()=>{cancelled=true;clearTimeout(timer);observer.disconnect();frame?.removeEventListener('load',loaded);script.onerror=null;node.replaceChildren();};
 },[asset,interval,theme,online,visible,retry,source.provider,key,setState]);
 return <section className="external-market-panel">
  <div className="external-market-controls"><span className="tag">{widgetStatus(state)}</span><button className="text-button" onClick={()=>setRetry(n=>n+1)}><RefreshCw size={15}/> Recarregar painel</button><a className="text-button" href={marketChartUrl(asset)} target="_blank" rel="noopener noreferrer">Abrir fonte <ExternalLink size={14}/></a>{onReturn&&<button className="text-button" onClick={onReturn}>Voltar à conexão direta</button>}</div>
  <p className="external-market-description">{source.contract}. Confira o horário da cotação e o estado do mercado no próprio gráfico.</p>
  {state!=='embedded'&&<p className="external-market-message" role="status">{state==='unavailable'?'O painel demorou para responder ou foi bloqueado. Recarregue ou abra a fonte. Se houver uma mensagem dentro do gráfico, siga o aviso da fonte.':state==='offline'?'Você está sem internet. A conexão será retomada quando a rede voltar.':state==='paused'?'Atualizações pausadas enquanto o aplicativo está em segundo plano.':'Carregando gráfico e cotação da fonte…'}</p>}
  <div className="external-chart-host" ref={host}/>
  <p className="external-market-description">Média simples e RSI estocástico já estão no gráfico; os parâmetros aparecem na legenda. Altere o período pelos botões do TraderNova. Esta conexão é para consulta visual; os dados não alimentam o robô nem os testes do laboratório.</p>
 </section>;
}


export function ExternalTechnicalIndicators({asset,interval}:{asset:AssetId;interval:string}){
 const host=useRef<HTMLDivElement>(null),{online,visible,theme}=useWidgetEnvironment();
 const [retry,setRetry]=useState(0),key=`${asset}|${interval}|${online}|${visible}|${theme}|${retry}`,[state,setState]=useWidgetState(key,online,visible);
 useEffect(()=>{
  const node=host.current;if(!node)return;node.replaceChildren();let cancelled=false,frame:HTMLIFrameElement|null=null;
  if(!online||!visible)return;
  const wrapper=document.createElement('div');wrapper.className='tradingview-widget-container';
  const body=document.createElement('div');body.className='tradingview-widget-container__widget';wrapper.appendChild(body);
  const attribution=document.createElement('a');attribution.className='tradingview-widget-copyright';attribution.href=marketChartUrl(asset);attribution.textContent='Análise técnica por TradingView';attribution.target='_blank';attribution.rel='noopener noreferrer';wrapper.appendChild(attribution);
  const script=document.createElement('script');script.src='https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js';script.async=true;script.textContent=JSON.stringify(technicalWidgetOptions(asset,interval,theme));
  const timeout=setTimeout(()=>{if(!cancelled)setState({key,value:'unavailable'});},18000);
  const loaded=()=>{if(!cancelled){clearTimeout(timeout);setState({key,value:'embedded'});}};
  const observer=new MutationObserver(()=>{const found=wrapper.querySelector('iframe');if(found&&found!==frame){frame=found;frame.title=`Indicadores de ${asset} · ${interval} minutos`;frame.addEventListener('load',loaded,{once:true});}});
  observer.observe(wrapper,{childList:true,subtree:true});script.onerror=()=>{if(!cancelled){clearTimeout(timeout);setState({key,value:'unavailable'});}};node.appendChild(wrapper);wrapper.appendChild(script);
  return()=>{cancelled=true;clearTimeout(timeout);observer.disconnect();frame?.removeEventListener('load',loaded);script.onerror=null;node.replaceChildren();};
 },[asset,interval,theme,online,visible,retry,key,setState]);
 return <section className="panel external-analysis-panel"><div className="section-heading"><div><h2>Indicadores da fonte</h2><p className="micro">{marketSources[asset].symbol} · {interval==='60'?'H1':`M${interval}`} · TradingView</p></div><button className="text-button" onClick={()=>setRetry(n=>n+1)}><RefreshCw size={15}/>Recarregar</button></div><p className="external-market-description">O resumo e os valores abaixo pertencem ao mesmo instrumento e período solicitados no gráfico. “Compra” e “Venda” aqui são classificações da fonte, não sinais validados do TraderNova.</p>{state!=='embedded'&&<p className="external-market-message" role="status">{widgetStatus(state)}. {state==='unavailable'?'Abra a fonte caso o navegador ou o provedor bloqueie o painel.':''}</p>}<div ref={host} className="external-analysis-host"/><p className="micro">Horário e disponibilidade informados pela fonte. Estes valores são exibidos pelo painel externo; a leitura automática para testes de ouro, Nasdaq e forex depende de uma API de mercado.</p></section>;
}
