import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import ts from 'typescript';

const temp=await fs.mkdtemp(path.join(os.tmpdir(),'tradernova-sources-'));
try{
 for(const file of ['market-sources','widget-loader']){
  const source=await fs.readFile(new URL(`../lib/tradernova/${file}.ts`,import.meta.url),'utf8');
  await fs.writeFile(path.join(temp,`${file}.mjs`),ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText);
 }
 const m=await import(pathToFileURL(path.join(temp,'market-sources.mjs')));
 for(const id of ['XAUUSD','NAS100','BTCUSD','ETHUSD','SOLUSD','EURUSD','USDJPY']){
  for(const interval of ['1','5','15','60']){
   const config=m.chartWidgetOptions(id,interval,'light');
   assert.equal(config.symbol,new URL(m.marketChartUrl(id)).searchParams.get('symbol'),'Link and chart must keep the same instrument');
   assert.equal(config.allow_symbol_change,false,'Widget cannot change instrument behind the app selection');
   assert.equal(config.interval,interval);
   assert.equal(config.hide_top_toolbar,true,'Only the app changes the selected timeframe');
   const analysis=m.technicalWidgetOptions(id,interval,'light');
   assert.equal(analysis.symbol,config.symbol);
   assert.equal(analysis.interval,{'1':'1m','5':'5m','15':'15m','60':'1h'}[interval]);
   assert.equal(analysis.showIntervalTabs,false,'Companion indicators retain the chart timeframe');
  }
 }
 assert.equal(m.marketSources.USDJPY.currency,'JPY');
 assert.equal(m.marketSources.NAS100.symbol,'OANDA:NAS100USD','Do not replace CFD with NDX or an ETF');
 assert.throws(()=>m.chartWidgetOptions('__proto__','1','dark'));
 assert.throws(()=>m.chartWidgetOptions('XAUUSD','999','dark'));
 assert.notEqual(m.widgetStatus('embedded'),'Ao vivo','DOM readiness must never certify fresh market data');
 assert.equal(m.widgetStatus('offline'),'Sem internet');

 const original={document:globalThis.document,customElements:globalThis.customElements,setTimeout:globalThis.setTimeout,clearTimeout:globalThis.clearTimeout};
 const scripts=[],timers=new Map();let nextTimer=0,defined=false;
 globalThis.document={head:{appendChild(script){scripts.push(script);}},createElement(tag){assert.equal(tag,'script');return {removed:false,remove(){this.removed=true;}};}};
 globalThis.customElements={get(){return defined?class Quote{}:undefined;}};
 globalThis.setTimeout=fn=>{timers.set(++nextTimer,fn);return nextTimer;};
 globalThis.clearTimeout=id=>timers.delete(id);
 try{
  const {loadQuoteWidget}=await import(pathToFileURL(path.join(temp,'widget-loader.mjs')));
  const first=loadQuoteWidget();const failFirst=assert.rejects(first);
  assert.equal(loadQuoteWidget(),first);assert.equal(scripts.length,1,'Multiple cards share one module');
  scripts[0].onerror();await failFirst;assert.equal(scripts[0].removed,true);assert.equal(timers.size,0);
  const second=loadQuoteWidget();const failSecond=assert.rejects(second);assert.equal(scripts.length,2);
  const late=scripts[1].onload;[...timers.values()][0]();await failSecond;
  const third=loadQuoteWidget();const failThird=assert.rejects(third);
  late();assert.equal(loadQuoteWidget(),third,'Late callbacks cannot invalidate the current retry');
  scripts[2].onload();await failThird;assert.equal(scripts[2].removed,true,'A loaded module without registration must fail');
  const fourth=loadQuoteWidget();defined=true;scripts[3].onload();await fourth;
  await loadQuoteWidget();assert.equal(scripts.length,4,'Registered module is reused');assert.equal(timers.size,0);
 }finally{Object.assign(globalThis,original);}
 console.log('Market source checks passed: contract consistency, all seven assets, timeframe allowlist, honest widget status, one shared loader, network failure, timeout, clean retry and ignored late callbacks.');
}finally{await fs.rm(temp,{recursive:true,force:true});}
