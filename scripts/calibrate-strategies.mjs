import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {loadResearchModules} from './research-modules.mjs';
const root=new URL('../',import.meta.url),protocolBytes=await fs.readFile(new URL('research/calibration-protocol.json',root)),p=JSON.parse(protocolBytes),manifest=JSON.parse(await fs.readFile(new URL('public/research/manifest.json',root),'utf8'));
const hash=b=>createHash('sha256').update(b).digest('hex'),date=d=>Date.parse(d+'T00:00:00Z');
const median=a=>{const b=[...a].sort((a,b)=>a-b);return (b[Math.floor((b.length-1)/2)]+b[Math.ceil((b.length-1)/2)])/2;};
const m=await loadResearchModules();
try{
 const series=[];
 for(const symbol of p.symbols){const source=manifest.series.find(s=>s.symbol===symbol&&s.interval===60),bytes=await fs.readFile(new URL(`research/cache/${source.file}`,root));if(hash(bytes)!==source.sha256)throw new Error('Source checksum mismatch');series.push({...source,bars:JSON.parse(bytes)});}
 const options=(candidateId,window,parameters)=>({candidateId,interval:60,from:date(window[0]),to:date(window[1]),initialCapital:p.initialCapital,riskPct:p.riskPct,feeBps:p.feeBps,slippageBps:p.slippageBps,parameters});
 const summarize=r=>({...r,trades:r.trades.length,curve:r.curve.filter((_,i)=>i===0||i===r.curve.length-1||i%Math.ceil(r.curve.length/150)===0)});
 const trials=[],selection=[];
 // Only development bars are passed into ranking, not just date-filtered later results.
 for(const candidateId of p.candidates){
  for(const parameters of m.calibration.calibrationVariants(candidateId)){
   const cells=series.flatMap(s=>p.developmentWindows.map(window=>({symbol:s.symbol,window,...summarize(m.historical.runHistorical(s.bars.filter(b=>b.time<date(p.developmentWindows.at(-1)[1])),options(candidateId,window,parameters)))})));
   const score=median(cells.map(c=>c.returnPct))-.25*Math.max(...cells.map(c=>c.maxDrawdownPct));
   const adequate=cells.every(c=>c.trades>=5)&&cells.reduce((sum,c)=>sum+c.trades,0)>=60;
   trials.push({candidateId,parameters,score,adequate,cells});
  }
  const family=trials.filter(t=>t.candidateId===candidateId),baseline=family.find(t=>t.parameters.id===`${candidateId}-E0X0`),ranked=family.filter(t=>t.adequate).sort((a,b)=>b.score-a.score||a.parameters.id.localeCompare(b.parameters.id));
  const winner=ranked[0]&&ranked[0].score>baseline.score?ranked[0]:baseline;
  selection.push({candidateId,parameters:winner.parameters,developmentScore:winner.score,baselineScore:baseline.score,developmentAdequate:winner.adequate});
 }
 const frozen={protocolHash:hash(protocolBytes),selection,trials};
 await fs.writeFile(new URL('research/calibration-selection.json',root),JSON.stringify(frozen,null,2));
 console.log('Development selection frozen:',selection.map(s=>`${s.candidateId} ${s.parameters.id} score ${s.developmentScore.toFixed(2)}`).join('; '));
 // Validate frozen winners; never search again based on validation/final outcomes.
 const results=[];
 for(const chosen of selection){
  const rows=series.map(s=>{
   const baseline=m.historical.runHistorical(s.bars,options(chosen.candidateId,p.validationWindow,m.calibration.originalParameters(chosen.candidateId)));
   const validation=m.historical.runHistorical(s.bars,options(chosen.candidateId,p.validationWindow,chosen.parameters));
   return {source:s,baseline,validation};
  });
  const improvements=rows.filter(r=>r.validation.returnPct>r.baseline.returnPct).length;
  const validationImproved=improvements>=2&&rows.reduce((sum,r)=>sum+r.validation.returnPct-r.baseline.returnPct,0)>0;
  const adopted=chosen.developmentAdequate&&chosen.developmentScore>chosen.baselineScore&&validationImproved;
  for(const row of rows){
   const {source:s,baseline,validation}=row;
   const final=m.historical.runHistorical(s.bars,options(chosen.candidateId,p.retrospectiveFinalWindow,chosen.parameters));
   const originalFinal=m.historical.runHistorical(s.bars,options(chosen.candidateId,p.retrospectiveFinalWindow,m.calibration.originalParameters(chosen.candidateId)));
   const stress=m.historical.runHistorical(s.bars,{...options(chosen.candidateId,p.retrospectiveFinalWindow,chosen.parameters),feeBps:p.stressFeeBps,slippageBps:p.stressSlippageBps});
   const reasons=m.historical.screeningReasons(validation,final,stress);
   const result={candidateId:chosen.candidateId,symbol:s.symbol,interval:60,parameters:chosen.parameters,adopted,development:chosen,validation:summarize(validation),baselineValidation:summarize(baseline),final:summarize(final),baselineFinal:summarize(originalFinal),stress:summarize(stress),reasons,validated:false,sampleHash:s.sha256};
   results.push(result);
   await fs.writeFile(new URL(`public/research/calibrated-${chosen.candidateId}-${s.symbol}.json`,root),JSON.stringify({...result,validation,final,baselineValidation:baseline,baselineFinal:originalFinal,stress}));
   console.log(`${chosen.candidateId} ${s.symbol}: validation ${baseline.returnPct.toFixed(2)} -> ${validation.returnPct.toFixed(2)}%; final ${originalFinal.returnPct.toFixed(2)} -> ${final.returnPct.toFixed(2)}%; trades ${final.trades.length}; adopted ${adopted}`);
  }
 }
 const report={version:1,id:p.id,generatedAt:new Date().toISOString(),protocol:p,protocolHash:hash(protocolBytes),selectionHash:hash(JSON.stringify(frozen)),trials:trials.map(t=>({...t,cells:t.cells.map(({curve,...r})=>r)})),selection,results,validated:false};
 await fs.writeFile(new URL('public/research/calibration.json',root),JSON.stringify(report));
 const active=Object.fromEntries(p.candidates.map(id=>{const row=results.find(r=>r.candidateId===id);return [id,row.adopted?row.parameters:m.calibration.originalParameters(id)];}));
 await fs.writeFile(new URL('lib/tradernova/active-presets.ts',root),`// Generated from the frozen development selection and validation adoption rule.\nimport type {StrategyParameters} from './calibration';\nimport type {CandidateId} from './research';\nexport const activePresets:Record<CandidateId,StrategyParameters>=${JSON.stringify(active,null,2)};\n`);
 await fs.writeFile(new URL('research/CALIBRACAO.md',root),`# Calibração H1 v2\n\n${p.claim}\n\n27 variantes, três ativos; ranking apenas em 2024-09 a 2025-08, score mediana de retorno menos 0,25 do pior DD nas seis células. Validação e final excluídos do ranking. Custos/risco/critérios de aprovação mantidos.\n\n| Regra | Ativo | Preset | Validação original → calibrada | Final original → calibrada | Trades finais | PF final | DD final | Stress final | Adotada para pesquisa |\n|---|---|---|---|---|---|---|---|---|---|\n${results.map(r=>`| ${r.candidateId} | ${r.symbol} | ${r.parameters.id} | ${r.baselineValidation.returnPct.toFixed(2)}% → ${r.validation.returnPct.toFixed(2)}% | ${r.baselineFinal.returnPct.toFixed(2)}% → ${r.final.returnPct.toFixed(2)}% | ${r.final.trades} | ${r.final.profitFactor?.toFixed(2)??'—'} | ${r.final.maxDrawdownPct.toFixed(2)}% | ${r.stress.returnPct.toFixed(2)}% | ${r.adopted?'Sim':'Não'} |`).join('\n')}\n\nNenhuma aprovação automática. Arquivos completos exportáveis em public/research/calibrated-*.json; grade e protocolo públicos em calibration.json.\n`);
}finally{await m.cleanup();}
