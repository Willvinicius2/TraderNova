'use client';
import {useMemo} from 'react';
import {Activity,Clock3} from 'lucide-react';
import {formatPrice,type Asset,type Candle} from '@/lib/tradernova/domain';
import {indicatorReadings,countGaps} from '@/lib/tradernova/indicators';
import './market-calibration.css';
export function MarketIndicators({bars,asset,interval,status,live,receivedAt}:{bars:Candle[];asset:Asset;interval:number;status:string;live:boolean;receivedAt?:number}){
 const readings=useMemo(()=>indicatorReadings(bars),[bars]),gaps=countGaps(bars,interval),last=bars.at(-1);
 const format=(n:number,unit:string)=>unit==='price'?formatPrice(n,asset):n.toLocaleString('pt-BR',{maximumFractionDigits:unit==='number'?4:3})+(unit==='percent'?'%':'');
 return <section className="market-readings" aria-labelledby="readings-title"><div className="section-heading"><div><h2 id="readings-title">Leitura dos indicadores</h2><p className="micro">{asset.id} · {interval===60?'H1':`M${interval}`} · {live?'Kraken Spot':'dados sintéticos'} · {bars.length} candles</p></div><span className="tag">{status}</span></div>
 <div className="reading-context"><Clock3 size={15}/><span>{last?`Mesma série do gráfico · último candle ${new Date(last.time).toLocaleString('pt-BR',{timeZone:'UTC',day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'})} UTC`:'Aguardando dados para calcular.'}{live&&receivedAt?` · consulta/recebimento ${new Date(receivedAt).toLocaleTimeString('pt-BR')}`:''}</span></div>
 {gaps>0&&<p className="notice">A série contém {gaps} intervalo(s) sem candle. Os cálculos usam apenas os dados recebidos; não preenchemos lacunas com preços inventados.</p>}
 <div className="indicator-grid calibrated-indicators">{readings.map(ind=><article className="panel indicator-card" key={ind.id}><div className="row between"><span>{ind.name}</span><Activity size={17}/></div>{ind.values?ind.values.length===1?<strong>{format(ind.values[0],ind.unit)}</strong>:<dl className="reading-values">{ind.values.map((value,i)=><div key={i}><dt>{ind.labels?.[i]}</dt><dd>{format(value,ind.unit)}</dd></div>)}</dl>:<strong className="muted">—</strong>}<p>{ind.values?ind.description:`Aguardando ${ind.minimum} candles · ${bars.length} recebidos`}</p></article>)}</div><p className="micro reading-footnote">Inclui o candle em formação. A EMA 20 usa a mesma fórmula e os mesmos candles da linha no gráfico. No laboratório, os sinais usam somente candles fechados.</p></section>;
}
