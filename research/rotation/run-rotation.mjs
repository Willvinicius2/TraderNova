import fs from 'node:fs/promises';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';

const here = new URL('./', import.meta.url);
const root = new URL('../../', here);
const HOUR = 3_600_000, WEEK = 168 * HOUR;
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const at = day => Date.parse(`${day}T00:00:00Z`);
const round = n => Number(n.toFixed(6));

function verify(bars, meta) {
  if (bars.length !== meta.bars || bars[0].time !== meta.first || bars.at(-1).time + HOUR !== meta.toExclusive) throw Error('Coverage mismatch');
  let gaps = 0;
  for (let i=0;i<bars.length;i++) {
    const b=bars[i];
    if (![b.time,b.open,b.high,b.low,b.close,b.volume].every(Number.isFinite) || b.time % HOUR || b.low <= 0 || b.volume < 0 || b.high < Math.max(b.open,b.close) || b.low > Math.min(b.open,b.close)) throw Error(`Invalid bar ${i}`);
    if (i && b.time-bars[i-1].time!==HOUR) {
      if (bars[i-1].time!==Date.parse('2023-03-24T12:00:00Z') || b.time!==Date.parse('2023-03-24T14:00:00Z')) throw Error(`Unexpected gap ${i}`);
      gaps++;
    }
  }
  if (gaps!==1) throw Error(`Expected one documented spot halt, found ${gaps}`);
}

function rankAt(series, i, lookback) {
  const end=series[0][i-1]?.time, start=end-lookback*HOUR;
  if (!Number.isFinite(end) || end+HOUR!==series[0][i]?.time || i-1-lookback<0) return null;
  let best=null;
  for (let s=0;s<series.length;s++) {
    const bars=series[s], j=i-1-lookback;
    if (bars[j]?.time!==start || bars[i-1]?.time!==end || bars[i]?.time!==end+HOUR) return null;
    for (let k=j+1;k<=i-1;k++) if (bars[k].time-bars[k-1].time!==HOUR) return null;
    const ret=bars[i-1].close/bars[j].close-1;
    if (!best || ret>best.return) best={index:s,return:ret,signalTime:end};
  }
  return best?.return>0?best:null;
}

function runWindow(series, symbols, from, to, cost, protocol) {
  const fee=cost.feeBpsPerFill/10_000,slip=cost.slippageBpsPerFill/10_000;
  const stop=protocol.stopPct/100, lookback=protocol.rankingLookbackHours;
  let cash=protocol.initialCapital,position=null,peak=cash,drawdown=0,gapExits=0,stops=0,rankings=0,qualifyingRankings=0;
  const selections=Object.fromEntries(symbols.map(s=>[s,0])),trades=[];
  function exit(price,time,reason) {
    const filled=price*(1-slip),proceeds=position.qty*filled*(1-fee),pnl=proceeds-position.entryCash;
    cash+=proceeds;
    trades.push({symbol:symbols[position.symbolIndex],entryTime:position.entryTime,exitTime:time,entryCash:round(position.entryCash),pnl:round(pnl),returnPct:round(100*pnl/position.entryCash),reason});
    if (reason==='gap') gapExits++;
    if (reason==='stop') stops++;
    position=null;
  }
  for(let i=0;i<series[0].length;i++) {
    const bar=series[0][i],time=bar.time;
    if(time<from)continue;
    if(time>=to)break;
    for(let s=1;s<series.length;s++)if(series[s][i]?.time!==time)throw Error(`Series misalignment ${time}`);
    const gap=i>0&&time-series[0][i-1].time!==HOUR;
    const date=new Date(time),monday=date.getUTCDay()===1&&date.getUTCHours()===0;
    if(position && (gap || monday)) exit(series[position.symbolIndex][i].open,time,gap?'gap':'rebalance');
    if(monday && !gap && time+WEEK<to) {
      rankings++;
      const pick=rankAt(series,i,lookback);
      if(pick) {
        qualifyingRankings++;
        const b=series[pick.index][i],filled=b.open*(1+slip),entryCash=cash;
        position={symbolIndex:pick.index,qty:cash/(filled*(1+fee)),entryCash,entryTime:time,filledEntry:filled,signalTime:pick.signalTime};
        selections[symbols[pick.index]]++;
        cash=0;
      }
    }
    if(position) {
      const b=series[position.symbolIndex][i],stopPrice=position.filledEntry*(1-stop);
      if(b.low<=stopPrice) exit(Math.min(b.open,stopPrice),time,'stop');
    }
    const marked=cash+(position?position.qty*series[position.symbolIndex][i].close*(1-slip)*(1-fee):0);
    peak=Math.max(peak,marked);
    drawdown=Math.max(drawdown,100*(peak-marked)/peak);
  }
  if(position)throw Error('Position left open at window end');
  const wins=trades.reduce((v,t)=>v+Math.max(0,t.pnl),0),losses=-trades.reduce((v,t)=>v+Math.min(0,t.pnl),0);
  return {trades:trades.length,netPct:round(100*(cash/protocol.initialCapital-1)),profitFactor:losses>0?round(wins/losses):null,drawdownPct:round(drawdown),gapExits,stops,rankings,qualifyingRankings,selections,firstTrade:trades[0]?.entryTime,lastTrade:trades.at(-1)?.exitTime};
}

function selfTest() {
  const start=Date.parse('2026-09-20T23:00:00Z'),len=15*24+2;
  const series=[0,1,2].map(s=>Array.from({length:len},(_,i)=>{
    const p=100+(s===0?10:s===1?5:0)*Math.min(i,168)/168;
    return {time:start+i*HOUR,open:p,high:p,low:p,close:p,volume:1};
  }));
  const monday=Date.parse('2026-09-28T00:00:00Z');
  const ix=(monday-start)/HOUR;
  assert.equal(rankAt(series,ix,168).index,0);
  assert.equal(rankAt(series,ix,168).signalTime,monday-HOUR);
  const p={initialCapital:10000,stopPct:8,rankingLookbackHours:168};
  const cost={feeBpsPerFill:10,slippageBpsPerFill:2};
  const out=runWindow(series,['BTC','ETH','SOL'],monday,monday+WEEK+HOUR,cost,p);
  assert.equal(out.trades,1); assert.equal(out.selections.BTC,1);
  assert.equal(out.firstTrade,monday);assert.equal(out.lastTrade,monday+WEEK);
  assert(out.netPct<-.23&&out.netPct>-.25,'both fills must include costs');
  const shocked=series.map(a=>a.map(b=>({...b})));
  shocked[0][ix+1]={...shocked[0][ix+1],open:99,high:99,low:99,close:99};
  const stopped=runWindow(shocked,['BTC','ETH','SOL'],monday,monday+WEEK+HOUR,cost,p);
  assert.equal(stopped.stops,1);assert.equal(stopped.lastTrade,monday+HOUR);
  assert(stopped.netPct<-9,'adverse opening gap must fill below stop');
  const leak=series.map(a=>a.map(b=>({...b})));
  leak[0][ix-1].close=100; leak[0][ix-1].high=110;
  assert.equal(rankAt(leak,ix,168).index,1,'ranking must use last completed close');
  console.log('rotation self-test OK');
}

if(process.argv.includes('--self-test'))selfTest();
else {
  const phase=process.argv.find(a=>a.startsWith('--phase='))?.split('=')[1];
  if(!['screen','final'].includes(phase))throw Error('Use --phase=screen or --phase=final');
  const protocolBytes=await fs.readFile(new URL('protocol-N4.json',here));
  const protocol=JSON.parse(protocolBytes),protocolSha256=sha(protocolBytes);
  const manifest=JSON.parse(await fs.readFile(new URL('research/cache/v3/manifest.json',root)));
  const datasets={};
  for(const symbol of protocol.symbols) {
    const meta=manifest.series.find(s=>s.symbol===symbol&&s.interval===60);
    if(!meta)throw Error(`Missing manifest ${symbol}`);
    const bytes=await fs.readFile(new URL(`research/cache/v3/${meta.file}`,root));
    if(sha(bytes)!==meta.sha256)throw Error(`SHA mismatch ${symbol}`);
    const bars=JSON.parse(bytes);verify(bars,meta);datasets[symbol]={bars,sha256:meta.sha256};
  }
  const series=protocol.symbols.map(s=>datasets[s].bars);
  for(let i=0;i<series[0].length;i++)for(let s=1;s<series.length;s++)if(series[s][i].time!==series[0][i].time)throw Error(`Series misalignment ${i}`);
  const evaluate=(window,cost)=>runWindow(series,protocol.symbols,at(window[0]),at(window[1]),cost,protocol);
  if(phase==='screen') {
    const screen={generatedAt:new Date().toISOString(),protocolSha256,validated:false,forwardPassed:false,dataSha256:Object.fromEntries(protocol.symbols.map(s=>[s,datasets[s].sha256])),developmentYears:protocol.windows.developmentYears.map(window=>({window,base:evaluate(window,protocol.base),stress:evaluate(window,protocol.stress)})),development:{base:evaluate(protocol.windows.development,protocol.base),stress:evaluate(protocol.windows.development,protocol.stress)},validation:{base:evaluate(protocol.windows.validation,protocol.base),stress:evaluate(protocol.windows.validation,protocol.stress)}};
    await fs.writeFile(new URL('screen-N4.json',here),JSON.stringify(screen,null,2)+'\n');
    console.log(JSON.stringify({phase,protocolSha256,development:screen.development,validation:screen.validation},null,2));
  } else {
    const screen=JSON.parse(await fs.readFile(new URL('screen-N4.json',here)));
    if(screen.protocolSha256!==protocolSha256)throw Error('Protocol changed since screen');
    for(const symbol of protocol.symbols)if(screen.dataSha256[symbol]!==datasets[symbol].sha256)throw Error(`Dataset changed ${symbol}`);
    const final={window:protocol.windows.retrospectiveFinal,base:evaluate(protocol.windows.retrospectiveFinal,protocol.base),stress:evaluate(protocol.windows.retrospectiveFinal,protocol.stress)};
    const g=protocol.fixedGates,checks={positiveDevelopmentYears:screen.developmentYears.filter(y=>y.base.netPct>0).length>=g.developmentPositiveYears,minimumDevelopmentTrades:screen.development.base.trades>=g.minimumTradesDevelopment,minimumValidationTrades:screen.validation.base.trades>=g.minimumTradesValidation,minimumFinalTrades:final.base.trades>=g.minimumTradesFinal,validationPositive:screen.validation.base.netPct>0&&screen.validation.stress.netPct>0,finalPositive:final.base.netPct>0&&final.stress.netPct>0,profitFactor:screen.validation.base.profitFactor!==null&&screen.validation.base.profitFactor>=g.minProfitFactorValidationAndFinal&&final.base.profitFactor!==null&&final.base.profitFactor>=g.minProfitFactorValidationAndFinal,drawdown:screen.validation.base.drawdownPct<=g.maxDrawdownPctValidationAndFinal&&final.base.drawdownPct<=g.maxDrawdownPctValidationAndFinal};
    const historicalScreenPass=Object.values(checks).every(Boolean);
    const result={generatedAt:new Date().toISOString(),protocolSha256,validated:false,forwardPassed:false,holdoutUntouched:false,historicalScreenPass,checks,screen,final};
    await fs.writeFile(new URL('result-N4.json',here),JSON.stringify(result,null,2)+'\n');
    console.log(JSON.stringify({phase,historicalScreenPass,checks,final},null,2));
  }
}
