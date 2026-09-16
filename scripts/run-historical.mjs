import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {loadResearchModules} from './research-modules.mjs';
const root=new URL('../',import.meta.url),p=JSON.parse(await fs.readFile(new URL('research/protocol.json',root),'utf8'));
const manifest=JSON.parse(await fs.readFile(new URL('research/cache/manifest.json',root),'utf8'));
const hash=b=>createHash('sha256').update(b).digest('hex');
if(manifest.protocolSha256!==hash(await fs.readFile(new URL('research/protocol.json',root))))throw new Error('Protocol changed after download.');
const modules=await loadResearchModules();
try{
 const {runHistorical,screeningReasons}=modules.historical;
 const windows=[{id:'development',label:'Desenvolvimento',from:p.from,to:p.validationFrom},{id:'validation',label:'Validação retrospectiva',from:p.validationFrom,to:p.finalFrom},{id:'final',label:'Avaliação final retrospectiva',from:p.finalFrom,to:p.toExclusive}];
 const output=new URL('public/research/',root);await fs.mkdir(output,{recursive:true});
 await fs.mkdir(new URL('samples/',output),{recursive:true});
 await fs.copyFile(new URL('research/cache/BTCUSDT-1h.json',root),new URL('samples/BTCUSDT-1h.json',output));
 const study={version:1,id:p.id,generatedAt:new Date().toISOString(),protocol:p,windows,source:'Binance Spot · USDT',manifestUrl:'/research/manifest.json',results:[],validated:false};
 for(const series of manifest.series){
  const bytes=await fs.readFile(new URL(`research/cache/${series.file}`,root));if(hash(bytes)!==series.sha256)throw new Error('Dataset checksum mismatch.');
  const bars=JSON.parse(bytes);
  for(const candidateId of p.candidates){
   const options={candidateId,interval:series.interval,initialCapital:p.initialCapital,riskPct:p.riskPct,feeBps:p.feeBps,slippageBps:p.slippageBps};
   const runs={};
   for(const w of windows)runs[w.id]=runHistorical(bars,{...options,from:Date.parse(w.from+'T00:00:00Z'),to:Date.parse(w.to+'T00:00:00Z')});
   const stress=runHistorical(bars,{...runs.final.options,feeBps:p.stressFeeBps,slippageBps:p.stressSlippageBps});
   const reasons=screeningReasons(runs.validation,runs.final,stress),id=`${candidateId}-${series.symbol}-${series.interval}`;
   const summarize=r=>({...r,trades:r.trades.length,curve:r.curve.filter((_,i)=>i===0||i===r.curve.length-1||i%Math.ceil(r.curve.length/200)===0)});
   const result={id,candidateId,symbol:series.symbol,interval:series.interval,sampleHash:series.sha256,status:reasons.length?'rejected':'forward-candidate',reasons,windows:Object.fromEntries(Object.entries(runs).map(([k,r])=>[k,summarize(r)])),stress:summarize(stress),downloadUrl:`/research/${id}.json`,validated:false};
   await fs.writeFile(new URL(`${id}.json`,output),JSON.stringify({protocol:p,series,runs:Object.fromEntries(Object.entries(runs).map(([k,r])=>[k,{...r,curve:summarize(r).curve}])),stress:{...stress,curve:summarize(stress).curve},reasons,validated:false}));
   study.results.push(result);
   console.log(`${id}: final ${runs.final.returnPct.toFixed(2)}% | PF ${runs.final.profitFactor?.toFixed(2)} | ${runs.final.trades.length} trades | ${result.status}`);
  }
 }
 await fs.writeFile(new URL('study.json',output),JSON.stringify(study));
 await fs.writeFile(new URL('manifest.json',output),JSON.stringify(manifest,null,2));
 const rows=study.results.map(r=>`| ${r.candidateId} | ${r.symbol} | ${r.interval===60?'H1':'M15'} | ${r.windows.validation.returnPct.toFixed(2)}% | ${r.windows.final.returnPct.toFixed(2)}% | ${r.windows.final.trades} | ${r.windows.final.profitFactor?.toFixed(2)??'—'} | ${r.windows.final.maxDrawdownPct.toFixed(2)}% | ${r.stress.returnPct.toFixed(2)}% | ${r.status} |`);
 await fs.writeFile(new URL('research/RESULTADOS.md',root),`# Estudo histórico ${p.id}\n\nGerado: ${study.generatedAt}. ${p.claim}\n\nCapital reiniciado por janela: 10.000 USDT; risco planejado até 0,5%; somente compras; sem alavancagem. Taxa 0,10% por lado e slippage 0,02% por lado. Stress: 0,15% e 0,05%. Parâmetros fixos; 18 combinações; sem otimização.\n\nDesenvolvimento: ${p.from} a ${p.validationFrom} exclusivo; validação: ${p.validationFrom} a ${p.finalFrom} exclusivo; final: ${p.finalFrom} a ${p.toExclusive} exclusivo.\n\nDD abaixo é marcado no fechamento dos candles, incluindo custo estimado de liquidação; não mede o pior movimento intrabar nem as regras de perda diária da mesa.\n\n| Regra | Contrato | Período | Validação | Final | Trades final | PF final | DD final | Stress final | Triagem |\n|---|---|---|---|---|---|---|---|---|---|\n${rows.join('\n')}\n\nArquivos completos em public/research; amostras brutas em research/cache (não versionadas); arquivos de origem e SHA-256 em public/research/manifest.json. USDT spot Binance não equivale ao contrato da The5ers ou ao monitor Kraken USD. Resultados não incluem financiamento, restrições de lote/mínimo ou conversão cambial.\n`);
}finally{await modules.cleanup();}
