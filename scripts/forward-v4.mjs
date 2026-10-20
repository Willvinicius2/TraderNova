import fs from 'node:fs/promises';
import {loadResearchModules} from './research-modules.mjs';
// Forward test (#31) over the worker's closed-candle store. Usage:
// node scripts/forward-v4.mjs --candles worker-data/candles/kraken_BTCUSD_60m.jsonl --variant R1-E0X0 --started 2026-10-20T00:00:00Z --worst-dd 6.5 [--market crypto] [--symbol BTCUSDT] [--out file.json]
const arg=name=>{const i=process.argv.indexOf(`--${name}`);return i>0?process.argv[i+1]:undefined;};
const candles=arg('candles'),variantId=arg('variant'),started=Date.parse(arg('started')??''),worst=Number(arg('worst-dd')),market=arg('market')??'crypto';
if(!candles||!variantId||!Number.isFinite(started)||!(worst>0))throw new Error('Informe --candles, --variant, --started e --worst-dd (pior drawdown da validação, em %).');
const p=JSON.parse(await fs.readFile(new URL('../research/v4-protocol.json',import.meta.url))),spec=p.markets[market],base=spec.costs.base;
const spread=typeof base.spread==='number'?base.spread:base.spread[arg('symbol')??''];
if(spread===undefined)throw new Error('Informe --symbol para o custo do forex.');
const bars=(await fs.readFile(candles,'utf8')).split('\n').filter(Boolean).map(line=>JSON.parse(line));
const m=await loadResearchModules();
try{
 const r=m.forward.forwardV4(bars,{variantId,startedAt:started,now:Date.now(),initialCapital:10000,riskPct:.5,feeBps:base.feeBps,slippageBps:base.slippageBps,spread,sides:spec.sides,maxLeverage:spec.maxLeverage,minStopCostMultiple:3,worstValidationDrawdownPct:worst,calendar:spec.calendar});
 const out={...r,result:{...r.result,trades:r.result.trades}};
 if(arg('out'))await fs.writeFile(arg('out'),JSON.stringify(out,null,1));
 console.log(`${variantId}: ${r.days.toFixed(1)} dias, ${r.result.trades.length} operações, ${r.result.returnPct.toFixed(2)}%, DD ${r.result.maxDrawdownPct.toFixed(2)}% → ${r.passed?'critérios do forward test atendidos':r.reasons.join('; ')}`);
}finally{await m.cleanup();}
