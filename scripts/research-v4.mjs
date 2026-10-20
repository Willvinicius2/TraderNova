import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {loadResearchModules} from './research-modules.mjs';
// Protocol v4 runner. Selection is frozen to disk before any validation candle is simulated.
const root=new URL('../',import.meta.url),read=file=>fs.readFile(new URL(file,root)),exists=file=>fs.access(new URL(file,root)).then(()=>true,()=>false);
const hash=b=>createHash('sha256').update(b).digest('hex'),date=d=>Date.parse(d+'T00:00:00Z'),hour=3600000;
const protocolBytes=await read('research/v4-protocol.json'),p=JSON.parse(protocolBytes);
const median=a=>{const b=[...a].sort((x,y)=>x-y);return (b[Math.floor((b.length-1)/2)]+b[Math.ceil((b.length-1)/2)])/2;};
const summary=({trades,...r})=>({...r,trades:trades.length});
const only=process.argv.includes('--market')?process.argv[process.argv.indexOf('--market')+1]:null;

async function loadSeries(market){
 const spec=p.markets[market],series=[];
 for(const symbol of spec.symbols){
  if(market==='crypto'){
   const manifestFile='research/cache/v4/crypto/manifest.json';if(!await exists(manifestFile))return null;
   const source=JSON.parse(await read(manifestFile)).series.find(s=>s.symbol===symbol),bytes=await read(`research/cache/v4/crypto/${source.file}`);
   if(hash(bytes)!==source.sha256)throw Error(`Source hash mismatch: ${symbol}`);
   series.push({symbol,sha256:source.sha256,bars:JSON.parse(bytes)});
  }else{
   const manifestFile=`research/cache/v4/fx/${symbol}/manifest.json`;if(!await exists(manifestFile))return null;
   const source=JSON.parse(await read(manifestFile)).series.H1,bytes=await read(`research/cache/v4/fx/${symbol}/${source.file}`);
   if(hash(bytes)!==source.sha256)throw Error(`Source hash mismatch: ${symbol}`);
   const bars=bytes.toString('utf8').trim().split('\n').slice(1).map(line=>{const [t,o,h,l,c]=line.split(',').map(Number);return {time:t*1000,open:o,high:h,low:l,close:c,volume:0};});
   series.push({symbol,sha256:source.sha256,bars});
  }
 }
 return series;
}

const m=await loadResearchModules();
try{
 const engineHash=hash(await read('lib/tradernova/research-v4.ts'));
 for(const market of Object.keys(p.markets).filter(k=>!only||k===only)){
  const spec=p.markets[market],series=await loadSeries(market);
  if(!series){console.log(`${market}: no verified cache under research/cache/v4; skipped (see research/V4.md for download steps).`);continue;}
  const cost=(symbol,kind)=>{const c=spec.costs[kind];return {feeBps:c.feeBps,slippageBps:c.slippageBps,spread:typeof c.spread==='number'?c.spread:c.spread[symbol]};};
  const run=(s,variant,window,kind='base')=>{
   const [from,to]=window.map(date),r=m.v4.runV4(s.bars.filter(b=>b.time<to),{variant,from,to,initialCapital:10000,riskPct:.5,...cost(s.symbol,kind),sides:spec.sides,maxLeverage:spec.maxLeverage,minStopCostMultiple:3},spec.calendar);
   return {...r,missingShare:r.missingHours/((to-from)/hour)};
  };
  // Development and frozen selection.
  const trials=[],selection=[];
  for(const familyId of p.families){
   for(const id of p.variants.filter(v=>v.startsWith(familyId))){
    const variant=m.v4.v4Variants.find(v=>v.id===id);
    const cells=series.flatMap(s=>spec.developmentWindows.map(window=>({symbol:s.symbol,window,base:summary(run(s,variant,window)),stress:summary(run(s,variant,window,'stress'))})));
    const score=median(cells.map(c=>c.base.returnPct))-.25*Math.max(...cells.map(c=>c.base.maxDrawdownPct));
    const total=cells.reduce((n,c)=>n+c.base.trades,0),perAsset=spec.symbols.map(sym=>cells.filter(c=>c.symbol===sym).reduce((n,c)=>n+c.base.trades,0));
    const net=k=>cells.reduce((n,c)=>n+c[k].net,0),a=spec.adequacy;
    const eligible=total>=a.totalTrades&&perAsset.every(n=>n>=a.perAssetTrades)&&cells.filter(c=>c.base.trades>=5).length>=a.cellsWithFiveTrades&&net('base')>0&&net('stress')>0;
    trials.push({familyId,variant,score,eligible,totalTrades:total,developmentNet:net('base'),developmentStressNet:net('stress'),cells});
    console.log(`${market} ${id}: dev score ${score.toFixed(3)}, ${total} trades, net ${net('base').toFixed(0)}, stress ${net('stress').toFixed(0)}, eligible=${eligible}`);
   }
   const winner=trials.filter(t=>t.familyId===familyId&&t.eligible).sort((x,y)=>y.score-x.score||x.variant.id.localeCompare(y.variant.id))[0];
   selection.push({familyId,variant:winner?.variant??null,rejectedInDevelopment:!winner});
  }
  const frozen={protocolHash:hash(protocolBytes),engineHash,sourceHashes:series.map(({symbol,sha256})=>({symbol,sha256})),selection,trials};
  const frozenBytes=JSON.stringify(frozen,null,2);
  await fs.writeFile(new URL(`research/v4-selection-${market}.json`,root),frozenBytes);
  console.log(`${market}: selection frozen (${selection.map(s=>`${s.familyId}=${s.variant?.id??'rejected'}`).join(', ')}). Opening validation.`);
  // Validation, then (FX only) the reserve for cells that passed.
  const screen=(r,stress,min)=>[r.trades.length<min&&`menos de ${min} operações`,!(r.net>0)&&'resultado líquido não positivo',!(r.profitFactor>=1.2)&&'fator de lucro abaixo de 1,20',r.maxDrawdownPct>15&&'drawdown acima de 15%',!(stress.net>0)&&'custos elevados: não positivo',r.missingShare>spec.maxMissingHourShare&&'lacunas de dados acima do limite'].filter(Boolean);
  const results=[];
  for(const chosen of selection.filter(s=>s.variant)){
   for(const s of series){
    const windows=Object.entries(spec.validationWindows).map(([name,w])=>{const base=run(s,chosen.variant,w[s.symbol]),stress=run(s,chosen.variant,w[s.symbol],'stress');return {name,window:w[s.symbol],base,stress,reasons:screen(base,stress,spec.validationMinTrades)};});
    const t=m.v4.tStatistic(windows.flatMap(w=>w.base.trades.map(x=>x.returnOnEquityPct)));
    const reasons=[...windows.flatMap(w=>w.reasons.map(r=>`${w.name}: ${r}`)),...(t!==null&&t>=p.multipleTesting.tThreshold?[]:[`estatística t ${t?.toFixed(2)??'—'} abaixo de ${p.multipleTesting.tThreshold} (correção para ${p.multipleTesting.variantAssetCells} testes)`])];
    results.push({familyId:chosen.familyId,symbol:s.symbol,variant:chosen.variant,tStatistic:t,windows,reasons});
   }
  }
  const validationBytes=JSON.stringify(results.map(r=>({...r,windows:r.windows.map(w=>({...w,base:summary(w.base),stress:summary(w.stress)}))})));
  await fs.writeFile(new URL(`research/cache/v4/${market}-validation.json`,root),validationBytes);
  if(spec.reserveWindow)for(const r of results.filter(r=>!r.reasons.length)){
   const s=series.find(s=>s.symbol===r.symbol),base=run(s,r.variant,spec.reserveWindow),stress=run(s,r.variant,spec.reserveWindow,'stress');
   r.reserve={window:spec.reserveWindow,base,stress,reasons:screen(base,stress,spec.validationMinTrades)};r.reasons.push(...r.reserve.reasons.map(x=>`reserva: ${x}`));
  }
  for(const r of results){r.historicalScreenPassed=!r.reasons.length;console.log(`${market} ${r.variant.id} ${r.symbol}: t=${r.tStatistic?.toFixed(2)} ${r.windows.map(w=>`${w.name} ${w.base.returnPct.toFixed(2)}% PF ${w.base.profitFactor?.toFixed(2)??'—'} n=${w.base.trades.length}`).join(' · ')} → ${r.historicalScreenPassed?'passou na triagem histórica':r.reasons.join('; ')}`);}
  const publish=r=>({...r,windows:r.windows.map(w=>({...w,base:summary(w.base),stress:summary(w.stress),trades:w.base.trades})),reserve:r.reserve&&{...r.reserve,base:summary(r.reserve.base),stress:summary(r.reserve.stress),trades:r.reserve.base.trades}});
  await fs.writeFile(new URL(`public/research/v4-${market}.json`,root),JSON.stringify({version:4,id:p.id,market,generatedAt:new Date().toISOString(),protocolHash:hash(protocolBytes),selectionHash:hash(frozenBytes),validationHash:hash(validationBytes),engineHash,selection,trials,results:results.map(publish),validated:false}));
 }
}finally{await m.cleanup();}
