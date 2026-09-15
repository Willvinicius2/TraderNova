'use client';
import {useId} from 'react';
import {useIsMobile} from '@/hooks/use-mobile';
import {ema,formatPrice,type Candle,type Asset} from '@/lib/tradernova/domain';
export function Sparkline({values,color='#b9f582',height=45}:{values:number[];color?:string;height?:number}){
 const id=useId().replace(/:/g,''),lo=Math.min(...values),hi=Math.max(...values),span=hi-lo||1;
 const points=values.map((v,i)=>`${i*160/Math.max(values.length-1,1)},${height-4-(v-lo)/span*(height-8)}`).join(' ');
 return <svg viewBox={`0 0 160 ${height}`} className="sparkline" aria-hidden="true"><defs><linearGradient id={id} x1="0" y1="0" x2="0" y2="1"><stop stopColor={color} stopOpacity=".2"/><stop offset="1" stopColor={color} stopOpacity="0"/></linearGradient></defs><polygon points={`0,${height} ${points} 160,${height}`} fill={`url(#${id})`}/><polyline points={points} stroke={color} fill="none" strokeWidth="1.6" vectorEffect="non-scaling-stroke"/></svg>;
}
export function CandleChart({bars,asset,showEma,showVolume,source='Demonstração · dados sintéticos',highlightLatest=false}:{bars:Candle[];asset:Asset;showEma:boolean;showVolume:boolean;source?:string;highlightLatest?:boolean}){
 const mobile=useIsMobile(),visible=mobile?30:60;
 if(!bars.length)return <div className="empty-market">Aguardando candles da fonte.</div>;
 const data=bars.slice(-visible),width=mobile?410:760,height=310,left=8,right=90,top=18,bottom=55,lo=Math.min(...data.map(b=>b.low)),hi=Math.max(...data.map(b=>b.high)),pad=Math.max((hi-lo)*.14,Math.abs(hi)*.00002),y=(v:number)=>top+(hi+pad-v)/(hi-lo+pad*2)*(height-top-bottom),step=(width-left-right)/Math.max(data.length,mobile?30:60),avg=ema(bars.map(b=>b.close),20).slice(-visible),last=data[data.length-1];
 return <svg className="candle-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Gráfico de ${asset.name}. Fonte: ${source}.`}>
 {[0,1,2,3,4].map(n=>{const value=lo+(hi-lo)*n/4;return <g key={n}><line x1="0" x2={width-right+4} y1={y(value)} y2={y(value)} stroke="#253139" strokeDasharray="3 5"/><text x={width-right+15} y={y(value)+4} fill="#8e9ba4" fontSize={mobile?14:12}>{formatPrice(value,asset)}</text></g>;})}
 {data.map((b,i)=>{const x=left+i*step+step/2,up=b.close>=b.open,color=up?'#aeea78':'#e78187';return <g key={b.time} className={highlightLatest&&i===data.length-1?'forming-bar':undefined}><line x1={x} x2={x} y1={y(b.high)} y2={y(b.low)} stroke={color}/><rect x={x-step*.29} width={step*.58} y={Math.min(y(b.open),y(b.close))} height={Math.max(1.5,Math.abs(y(b.open)-y(b.close)))} rx=".7" fill={color}/>{showVolume&&<rect x={x-step*.29} width={step*.58} y={height-22-b.volume/Math.max(...data.map(c=>c.volume),1)*28} height={b.volume/Math.max(...data.map(c=>c.volume),1)*28} fill={color} opacity=".2"/>}</g>;})}
 {showEma&&<polyline points={avg.map((v,i)=>v===null?'':`${left+i*step+step/2},${y(v)}`).join(' ')} fill="none" stroke="#aea1f3" strokeWidth="1.6"/>}
 <line x1="0" x2={width-right+8} y1={y(last.close)} y2={y(last.close)} stroke="#b9f582" strokeDasharray="4 4" opacity=".6"/><rect x={width-right+4} y={y(last.close)-11} width={right-4} height="23" rx="4" fill="#b9f582"/><text x={width-right+10} y={y(last.close)+4} fill="#142212" fontSize={mobile?14:12}>{formatPrice(last.close,asset)}</text>
 {Array.from(new Set([0,Math.floor(data.length/3),Math.floor(data.length*2/3)])).map(i=><text key={i} x={left+i*step} y={height-3} fill="#8e9ba4" fontSize={mobile?14:12}>{new Date(data[i].time).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit',timeZone:'UTC'})}</text>)}
 </svg>;
}
