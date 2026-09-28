import fs from 'node:fs/promises';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';

const here = new URL('./', import.meta.url);
const root = new URL('../../', here);
const STEP = 3_600_000, DAY = 24 * STEP;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const at = day => Date.parse(`${day}T00:00:00Z`);
const round = n => Number(n.toFixed(6));

function verify(bars, meta) {
  if (bars.length !== meta.bars || bars[0].time !== meta.first || bars.at(-1).time + STEP !== meta.toExclusive) throw Error('Coverage mismatch');
  let gaps = 0;
  for (let i = 0; i < bars.length; i++) {
    const b = bars[i];
    if (![b.time,b.open,b.high,b.low,b.close,b.volume].every(Number.isFinite) || b.time % STEP || b.low <= 0 || b.volume < 0 || b.high < Math.max(b.open,b.close) || b.low > Math.min(b.open,b.close)) throw Error(`Invalid bar ${i}`);
    if (i && b.time - bars[i-1].time !== STEP) {
      if (bars[i-1].time !== Date.parse('2023-03-24T12:00:00Z') || b.time !== Date.parse('2023-03-24T14:00:00Z')) throw Error(`Unexpected gap ${i}`);
      gaps++;
    }
  }
  if (gaps !== 1) throw Error(`Expected one documented spot halt, found ${gaps}`);
}

function runWindow(bars, from, to, cost, capital=10_000) {
  const fee=cost.feeBpsPerFill/10_000,slip=cost.slippageBpsPerFill/10_000;
  let cash=capital,position=null,peak=capital,drawdown=0,gapExits=0;
  const trades=[];
  for(let i=0;i<bars.length;i++) {
    const b=bars[i]; if(b.time<from)continue; if(b.time>=to)break;
    const gap=!!position&&i>0&&b.time-bars[i-1].time!==STEP;
    if(position&&(b.time>=position.plannedExit||gap)) {
      const filled=b.open*(1-slip),proceeds=position.quantity*filled*(1-fee),pnl=proceeds-position.entryCash;
      cash+=proceeds;
      trades.push({entryTime:position.entryTime,exitTime:b.time,pnl,returnPct:100*pnl/position.entryCash,reason:gap?'documented-gap':'calendar'});
      if(gap)gapExits++;
      position=null;
    }
    const date=new Date(b.time);
    if(!position&&date.getUTCDay()===1&&date.getUTCHours()===0&&b.time+5*DAY<to&&i>0&&b.time-bars[i-1].time===STEP) {
      const filled=b.open*(1+slip),quantity=cash/(filled*(1+fee));
      position={quantity,entryCash:cash,entryTime:b.time,plannedExit:b.time+5*DAY};
      cash=0;
    }
    const marked=cash+(position?position.quantity*b.close*(1-slip)*(1-fee):0);
    peak=Math.max(peak,marked);
    drawdown=Math.max(drawdown,100*(peak-marked)/peak);
  }
  if(position)throw Error('Position left open at window end');
  const gains=trades.reduce((v,t)=>v+Math.max(0,t.pnl),0),losses=-trades.reduce((v,t)=>v+Math.min(0,t.pnl),0);
  const first=bars.find(b=>b.time===from),last=bars.find(b=>b.time===to-STEP);
  if(!first||!last)throw Error('Missing window edge');
  const passiveQty=capital/(first.open*(1+slip)*(1+fee));
  const buyHoldPct=100*(passiveQty*last.close*(1-slip)*(1-fee)/capital-1);
  return {trades:trades.length,netPct:100*(cash/capital-1),profitFactor:losses>0?gains/losses:null,drawdownPct:drawdown,buyHoldPct,gapExits,firstTrade:trades[0]?.entryTime,lastTrade:trades.at(-1)?.exitTime};
}

function selfTest() {
  const mon=Date.parse('2026-09-28T00:00:00Z');
  const bars=Array.from({length:7*24+1},(_,i)=>({time:mon-STEP+i*STEP,open:100,high:100,low:100,close:100,volume:1}));
  const out=runWindow(bars,mon,mon+7*DAY,{feeBpsPerFill:10,slippageBpsPerFill:2});
  assert.equal(out.trades,1);
  assert.equal(out.firstTrade,mon);
  assert.equal(out.lastTrade,mon+5*DAY);
  assert(out.netPct < -.23 && out.netPct > -.25, 'both fills and fees must be charged');
  console.log('calendar self-test OK');
}

if(process.argv.includes('--self-test'))selfTest();
else {
  const phase=process.argv.find(a=>a.startsWith('--phase='))?.split('=')[1];
  if(!['screen','final'].includes(phase))throw Error('Use --phase=screen or --phase=final');
  const protocolBytes=await fs.readFile(new URL('protocol.json',here));
  const protocol=JSON.parse(protocolBytes),protocolSha256=sha(protocolBytes);
  const manifest=JSON.parse(await fs.readFile(new URL('research/cache/v3/manifest.json',root)));
  const datasets={};
  for(const symbol of protocol.symbols){
    const meta=manifest.series.find(s=>s.symbol===symbol&&s.interval===60);
    if(!meta)throw Error(`Missing manifest ${symbol}`);
    const bytes=await fs.readFile(new URL(`research/cache/v3/${meta.file}`,root));
    if(sha(bytes)!==meta.sha256)throw Error(`SHA mismatch ${symbol}`);
    const bars=JSON.parse(bytes);verify(bars,meta);datasets[symbol]={bars,sha256:meta.sha256};
  }
  const evaluate=(window, cost)=>Object.fromEntries(protocol.symbols.map(symbol=>[symbol,runWindow(datasets[symbol].bars,at(window[0]),at(window[1]),cost,protocol.initialCapital)]));
  if(phase==='screen'){
    const screen={generatedAt:new Date().toISOString(),protocolSha256,validated:false,dataSha256:Object.fromEntries(protocol.symbols.map(s=>[s,datasets[s].sha256])),developmentYears:protocol.windows.developmentYears.map(w=>({window:w,base:evaluate(w,protocol.base),stress:evaluate(w,protocol.stress)})),development:{base:evaluate(protocol.windows.development,protocol.base),stress:evaluate(protocol.windows.development,protocol.stress)},validation:{base:evaluate(protocol.windows.validation,protocol.base),stress:evaluate(protocol.windows.validation,protocol.stress)}};
    await fs.writeFile(new URL('screen.json',here),JSON.stringify(screen,null,2)+'\n');
    console.log(JSON.stringify({phase,protocolSha256,validation:screen.validation},null,2));
  }else{
    const screen=JSON.parse(await fs.readFile(new URL('screen.json',here)));
    if(screen.protocolSha256!==protocolSha256)throw Error('Protocol changed since screen');
    for(const symbol of protocol.symbols)if(screen.dataSha256[symbol]!==datasets[symbol].sha256)throw Error('Dataset changed since screen');
    const final={window:protocol.windows.retrospectiveFinal,base:evaluate(protocol.windows.retrospectiveFinal,protocol.base),stress:evaluate(protocol.windows.retrospectiveFinal,protocol.stress)};
    const g=protocol.fixedGates,judgments={};
    for(const symbol of protocol.symbols){
      const years=screen.developmentYears.filter(y=>y.base[symbol].netPct>0).length;
      const d=screen.development.base[symbol],v=screen.validation.base[symbol],vs=screen.validation.stress[symbol],f=final.base[symbol],fs=final.stress[symbol];
      const checks={positiveDevelopmentYears:years>=g.developmentPositiveYearsPerAsset,minimumDevelopmentTrades:d.trades>=g.minimumTradesDevelopment,minimumValidationTrades:v.trades>=g.minimumTradesValidation,minimumFinalTrades:f.trades>=g.minimumTradesFinal,validationPositive:v.netPct>0&&vs.netPct>0,finalPositive:f.netPct>0&&fs.netPct>0,profitFactor:v.profitFactor!==null&&v.profitFactor>=g.minProfitFactorValidationAndFinal&&f.profitFactor!==null&&f.profitFactor>=g.minProfitFactorValidationAndFinal,drawdown:v.drawdownPct<=g.maxDrawdownPctValidationAndFinal&&f.drawdownPct<=g.maxDrawdownPctValidationAndFinal};
      judgments[symbol]={pass:Object.values(checks).every(Boolean),checks};
    }
    const historicalScreenPass=Object.values(judgments).filter(j=>j.pass).length>=g.minPassingAssets;
    const result={generatedAt:new Date().toISOString(),protocolSha256,validated:false,holdoutUntouched:false,historicalScreenPass,judgments,screen,final};
    await fs.writeFile(new URL('result.json',here),JSON.stringify(result,null,2)+'\n');
    console.log(JSON.stringify({phase,historicalScreenPass,judgments,final},null,2));
  }
}
