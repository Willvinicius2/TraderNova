import type {AssetId} from './domain';

/** Display integrations only. Widget prices must never be consumed as robot signals. */
export const marketSources:Record<AssetId,{symbol:string;provider:string;contract:string;currency:string;direct:boolean}>={
 XAUUSD:{symbol:'OANDA:XAUUSD',provider:'OANDA',contract:'Ouro / dólar · referência OANDA',currency:'USD',direct:false},
 NAS100:{symbol:'OANDA:NAS100USD',provider:'OANDA',contract:'CFD US Nas 100 · não é o índice à vista',currency:'USD',direct:false},
 EURUSD:{symbol:'OANDA:EURUSD',provider:'OANDA',contract:'Euro / dólar · referência OANDA',currency:'USD',direct:false},
 USDJPY:{symbol:'OANDA:USDJPY',provider:'OANDA',contract:'Dólar / iene · referência OANDA',currency:'JPY',direct:false},
 BTCUSD:{symbol:'KRAKEN:BTCUSD',provider:'Kraken',contract:'Bitcoin · mercado à vista',currency:'USD',direct:true},
 ETHUSD:{symbol:'KRAKEN:ETHUSD',provider:'Kraken',contract:'Ethereum · mercado à vista',currency:'USD',direct:true},
 SOLUSD:{symbol:'KRAKEN:SOLUSD',provider:'Kraken',contract:'Solana · mercado à vista',currency:'USD',direct:true},
};
export function marketChartUrl(asset:AssetId){return `https://www.tradingview.com/chart/?symbol=${encodeURIComponent(marketSources[asset].symbol)}`;}
export function chartWidgetOptions(asset:AssetId,interval:string,theme:'light'|'dark'){
 if(!Object.hasOwn(marketSources,asset)||!['1','5','15','60'].includes(interval))throw new Error('Mercado ou período não suportado.');
 return {autosize:true,symbol:marketSources[asset].symbol,interval,timezone:'Etc/UTC',theme,style:'1',locale:'br',allow_symbol_change:false,calendar:false,hide_side_toolbar:false,hide_top_toolbar:true,studies:['MASimple@tv-basicstudies','StochasticRSI@tv-basicstudies'],save_image:false,support_host:'https://www.tradingview.com'};
}
export type WidgetState='loading'|'embedded'|'unavailable'|'offline'|'paused';
/** Loading an iframe proves neither fresh data nor an open market. */
export function widgetStatus(state:WidgetState){
 return {loading:'Carregando painel',embedded:'Painel externo',unavailable:'Painel indisponível',offline:'Sem internet',paused:'Pausado'}[state];
}

export function technicalWidgetOptions(asset:AssetId,interval:string,theme:'light'|'dark'){
 const chart=chartWidgetOptions(asset,interval,theme);
 const periods:Record<string,string>={'1':'1m','5':'5m','15':'15m','60':'1h'};
 return {symbol:chart.symbol,interval:periods[interval],width:'100%',height:650,locale:'br',colorTheme:theme,isTransparent:true,showIntervalTabs:false,displayMode:'multiple'};
}
