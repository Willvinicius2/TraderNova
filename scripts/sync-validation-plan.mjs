// Rebuild the public research snapshot. No network, models, backtests or approvals.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const root=fileURLToPath(new URL('../',import.meta.url));
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8').replace(/^\uFEFF/,''));
const sha=p=>createHash('sha256').update(fs.readFileSync(path.join(root,p))).digest('hex');
const protocol=read('research/validation/protocol.json');
const registry=read('research/validation/candidates.json');
if(protocol.target!==7||registry.candidates.length<7||new Set(registry.candidates.map(c=>c.family)).size!==registry.candidates.length||new Set(registry.candidates.map(c=>c.id)).size!==registry.candidates.length)throw Error('At least seven distinct registered hypotheses required.');
const previous=read(protocol.supersedes.path);
for(const key of ['screenGates','prospectiveGate','statisticalGate','execution','independence','selection','counting','windows','capital','directionalRiskPct','directionalGrossExposurePct'])if(JSON.stringify(protocol[key])!==JSON.stringify(previous[key]))throw Error(`Changed gate: ${key}`);
if(sha(protocol.supersedes.path)!==protocol.supersedes.sha256)throw Error('Previous protocol changed.');
const sources=[];
function load(name){const p=`research/goal-seven/${name}.json`;sources.push({path:p,sha256:sha(p)});return read(p);}
const stats=r=>({trades:r.trade_count??r.trades,netPct:r.net_pct??r.netPct??r.returnPct,profitFactor:r.profit_factor??r.profitFactor,drawdownPct:r.max_drawdown_pct??r.maxConservativeDrawdownPct??r.conservativeDrawdownPct,accountBreach:r.account_breach??r.accountBreach??r.accountBreached??false});
const results=[];
function add(id,name,dev){const entry={id,name,status:'rejected_in_development',base:stats(dev.base),stress:stats(dev.stress)};for(const s of [entry.base,entry.stress])for(const k of ['trades','netPct','profitFactor','drawdownPct'])if(!Number.isFinite(s[k]))throw Error(`Missing ${id} ${k}`);results.push(entry);}
const funding=load('funding-results');if(funding.developmentGatePassed!==false)throw Error('Review changed funding result.');add('N2','Funding com hedge',funding.outcomes);
const directional=load('directional-results');for(const [id,name] of [['N5','Fluxo agressor'],['N6','Transmissão BTC → ETH/SOL']]){const r=directional.families[id];if(r.developmentPassed!==false)throw Error('Review changed directional result.');add(id,name,r.development);}
const gold=load('real-yield-results');if(gold.historicalDevelopmentScreenPass!==false)throw Error('Review changed gold result.');add('N7','Juro real e ouro',gold);
for(const [id,name,file] of [['N11','Posições abertas','open-interest'],['N12','Transferências on-chain','onchain-count'],['N13','Skew de opções','options-skew'],['N14','Capacidade de mineração','miner-pressure'],['N15','Emissão de stablecoins','stablecoin-liquidity']]){const r=load(`${file}-results`);if(r.developmentPassed!==false)throw Error(`Review changed ${id} result.`);add(id,name,r.development);}
const data={version:1,asOf:registry.updatedOn??registry.registeredOn,target:protocol.target,validatedCount:0,validated:false,protocol,protocolSha256:sha('research/validation/protocol.json'),candidates:registry.candidates,results,sources,limitations:['Nenhuma aprovação financeira ou operacional.','Histórico cripto até agosto/2026 já examinado; não é holdout intocado.','Hipóteses aguardam dados auditáveis e executor completo; módulos de condições não enviam ordens.'],pending:[{id:'N8',reason:'Amostra COT insuficiente: 12 sinais.'},{id:'N9',reason:'Swaps históricos e Bid/Ask do contrato ausentes.'},{id:'N10',reason:'Amostra de futuros datados insuficiente: 2 episódios.'}]};
data.supervision=read('research/validation/supervision.json');
fs.writeFileSync(path.join(root,'public/research/validation-plan.json'),JSON.stringify(data,null,2)+'\n');
fs.copyFileSync(path.join(root,'research/validation/protocol.json'),path.join(root,'public/research/validation-protocol.json'));
const novel=read('public/research/novel-study.json');
const n2=novel.candidates.find(c=>c.id==='N2');
if(n2){n2.status='exploratory-rejected';n2.results={trades:funding.outcomes.base.trades,netPct:funding.outcomes.base.netPct,profitFactor:funding.outcomes.base.profitFactor,drawdownPct:funding.outcomes.base.maxConservativeDrawdownPct};n2.limitations=['Atualização 29/09/2026: funding reprovado. Base +2,21%, DD 8,79%; stress −4,26%, DD 9,65%; amostra insuficiente, violação diária e lacunas. Nenhuma aprovação.',...n2.limitations.filter(s=>!s.startsWith('Atualização 29/09/2026:'))];fs.writeFileSync(path.join(root,'public/research/novel-study.json'),JSON.stringify(novel,null,2)+'\n');}
console.log(`Research snapshot: ${data.validatedCount}/${data.target} validated, ${data.candidates.length} hypotheses awaiting data, ${results.length} preserved rejections. No backtests executed.`);
