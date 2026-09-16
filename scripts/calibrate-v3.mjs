import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {loadResearchModules} from './research-modules.mjs';
const root=new URL('../',import.meta.url),read=async file=>fs.readFile(new URL(file,root));
const hash=b=>createHash('sha256').update(b).digest('hex'),date=d=>Date.parse(d+'T00:00:00Z');
const protocolBytes=await read('research/calibration-v3-protocol.json'),p=JSON.parse(protocolBytes),manifest=JSON.parse(await read('research/cache/v3/manifest.json'));
const median=a=>{const b=[...a].sort((a,b)=>a-b);return (b[Math.floor((b.length-1)/2)]+b[Math.ceil((b.length-1)/2)])/2;};
const summary=({trades,curve,...r})=>({...r,trades:trades.length});
const m=await loadResearchModules();
try{
 const series=[];
 for(const symbol of p.symbols){
  const source=manifest.series.find(s=>s.symbol===symbol&&s.interval===60),bytes=await read(`research/cache/v3/${source.file}`);
  if(hash(bytes)!==source.sha256)throw Error(`Source hash mismatch: ${symbol}`);
  series.push({...source,bars:JSON.parse(bytes)});
 }
 const control=id=>m.calibration.calibrationVariants(id).find(v=>v.id===p.control[id]);
 const options=(candidateId,window,parameters)=>({candidateId,interval:60,from:date(window[0]),to:date(window[1]),initialCapital:p.initialCapital,riskPct:p.riskPct,feeBps:p.feeBps,slippageBps:p.slippageBps,parameters,sourcePolicy:p.dataQualityAmendmentBeforeResults.sourcePolicy});
 const execute=(source,id,window,parameters,costs={})=>m.historical.runHistorical(source.bars.filter(b=>b.time<date(window[1])),{...options(id,window,parameters),...costs});
 const trials=[],selection=[];
 for(const id of p.candidates){
  for(const parameters of [control(id),...m.v3.v3Variants(id)]){
   const cells=series.flatMap(s=>p.developmentWindows.map(window=>({symbol:s.symbol,window,...summary(execute(s,id,window,parameters))})));
   const score=median(cells.map(c=>c.returnPct))-.25*Math.max(...cells.map(c=>c.maxDrawdownPct));
   const total=cells.reduce((sum,c)=>sum+c.trades,0),perAsset=p.symbols.map(symbol=>cells.filter(c=>c.symbol===symbol).reduce((sum,c)=>sum+c.trades,0));
   const adequate=total>=120&&perAsset.every(n=>n>=20)&&cells.filter(c=>c.trades>=5).length>=12;
   trials.push({candidateId:id,parameters,score,adequate,totalTrades:total,cells});
  }
  const family=trials.filter(t=>t.candidateId===id),baseline=family.find(t=>t.parameters.id===p.control[id]);
  const ranked=family.filter(t=>t.adequate).sort((a,b)=>b.score-a.score||a.parameters.id.localeCompare(b.parameters.id));
  const winner=ranked[0]&&ranked[0].score>baseline.score?ranked[0]:baseline;
  selection.push({candidateId:id,parameters:winner.parameters,developmentScore:winner.score,baselineScore:baseline.score,developmentAdequate:winner.adequate});
  console.log(`${id}: development winner ${winner.parameters.id}, score ${winner.score.toFixed(3)}, ${winner.totalTrades} trades`);
 }
 const engineFiles=['historical','calibration','calibration-v3','research','domain'];
 const engineHashes=Object.fromEntries(await Promise.all(engineFiles.map(async name=>[name,hash(await read(`lib/tradernova/${name}.ts`))])));
 const frozen={protocolHash:hash(protocolBytes),engineHashes,sourceHashes:series.map(({symbol,sha256})=>({symbol,sha256})),selection,trials};
 const frozenBytes=JSON.stringify(frozen,null,2);
 await fs.writeFile(new URL('research/calibration-v3-selection.json',root),frozenBytes);
 console.log('Selection frozen. Starting validation; final data excluded from selection and adoption.');
 const results=[];
 for(const chosen of selection){
  const id=chosen.candidateId,rows=series.map(source=>({source,baseline:execute(source,id,p.validationWindow,control(id)),validation:execute(source,id,p.validationWindow,chosen.parameters)}));
  const improve=rows.filter(r=>r.validation.returnPct>r.baseline.returnPct).length>=2&&rows.reduce((s,r)=>s+r.validation.returnPct-r.baseline.returnPct,0)>0;
  const positive=rows.filter(r=>r.validation.net>0).length>=2;
  const adopted=chosen.developmentAdequate&&chosen.developmentScore>chosen.baselineScore&&improve&&positive;
  for(const {source,baseline,validation} of rows){
   const final=execute(source,id,p.retrospectiveFinalWindow,chosen.parameters),baselineFinal=execute(source,id,p.retrospectiveFinalWindow,control(id));
   const stress=execute(source,id,p.retrospectiveFinalWindow,chosen.parameters,{feeBps:p.stressFeeBps,slippageBps:p.stressSlippageBps});
   const reasons=m.historical.screeningReasons(validation,final,stress);
   const result={candidateId:id,symbol:source.symbol,interval:60,parameters:chosen.parameters,adopted,validation:summary(validation),baselineValidation:summary(baseline),final:summary(final),baselineFinal:summary(baselineFinal),stress:summary(stress),historicalScreenPassed:reasons.length===0,validated:false,reasons,operationalReasons:['Avaliação retrospectiva reutilizada; acompanhamento prospectivo pendente','Fonte spot Binance não corresponde ao contrato da mesa'],sampleHash:source.sha256};
   results.push(result);
   // Full trades remain inspectable; curves are kept in the local research artifact.
   await fs.writeFile(new URL(`research/cache/v3/result-${id}-${source.symbol}.json`,root),JSON.stringify({...result,validation,final,baselineValidation:baseline,baselineFinal,stress}));
   await fs.writeFile(new URL(`public/research/v3-${id}-${source.symbol}.json`,root),JSON.stringify({...result,trades:{validation:validation.trades,final:final.trades,stress:stress.trades}}));
   console.log(`${id} ${source.symbol}: V ${validation.returnPct.toFixed(2)}% F ${final.returnPct.toFixed(2)}% PF ${final.profitFactor?.toFixed(2)} DD ${final.maxDrawdownPct.toFixed(2)}% stress ${stress.returnPct.toFixed(2)}% trades ${final.trades.length}; adopt=${adopted}; screen=${!reasons.length}`);
  }
 }
 const report={version:3,id:p.id,generatedAt:new Date().toISOString(),protocol:p,protocolHash:hash(protocolBytes),selectionHash:hash(frozenBytes),engineHashes,sourceManifest:manifest,selection,trials,results,validated:false};
 await fs.writeFile(new URL('public/research/calibration-v3.json',root),JSON.stringify(report));
 const table=results.map(r=>`| ${r.candidateId} | ${r.symbol} | ${r.parameters.id} | ${r.validation.returnPct.toFixed(2)}% | ${r.final.returnPct.toFixed(2)}% | ${r.final.trades} | ${r.final.profitFactor?.toFixed(2)??'—'} | ${r.final.maxDrawdownPct.toFixed(2)}% | ${r.stress.returnPct.toFixed(2)}% | ${r.adopted?'Sim':'Não'} |`).join('\n');
 await fs.writeFile(new URL('research/CALIBRACAO_V3.md',root),`# Calibração H1 v3\n\n${p.claim}\n\n21 variantes incluindo os três controles v2; desenvolvimento 2022–2024, validação jan/2025–fev/2026 e avaliação retrospectiva mar–ago/2026. A última janela já era conhecida antes desta rodada.\n\n| Família | Ativo | Preset selecionado | Validação | Final | Trades finais | PF final | DD final | Stress | Elegível para adoção experimental |\n|---|---|---|---|---|---|---|---|---|---|\n${table}\n\nO arquivo de seleção foi gravado antes da avaliação. Critérios e todos os ensaios constam no JSON público; custos de 10+2 bps por lado e stress de 15+5 bps. DD em fechamentos, sem certificar limite intrabar da mesa.\n\nA interrupção de 24/03/2023 é preservada sem interpolação; apenas essa lacuna oficial é permitida, sem entrada baseada em sinal anterior à lacuna. [Comunicado da Binance](${p.dataQualityAmendmentBeforeResults.evidence}).\n`);
}finally{await m.cleanup();}
