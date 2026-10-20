// Testes offline do worker de ingestão. Todos os candles aqui são FIXTURES SINTÉTICAS de teste, não dados de mercado.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import '../worker/register.mjs';
const imp = (rel) => import(pathToFileURL(path.resolve(new URL(rel, import.meta.url).pathname)).href);
const {createWorker, buildSignalRecord} = await imp('../worker/worker.ts');
const {createLogger} = await imp('../worker/log.ts');
const {parseConfig, workerConfigs} = await imp('../worker/config.ts');
const {main} = await imp('../worker/cli.ts');
const {openFileSignalStore} = await imp('../worker/signal-file-store.ts');
const {signalRecordSchema} = await imp('../lib/tradernova/signal-record.ts');
const {evaluatePaperEngine, strategyApprovals} = await imp('../lib/tradernova/paper-engine.ts');
const {contiguousTail, computeFeedState} = await imp('../worker/feed.ts');

const STEP = 3600000;
const price = (h) => 100 + 8 * Math.sin(h / 7) + 3 * Math.sin(h / 3.1); // FIXTURE sintética
const row = (time) => {
  const h = time / STEP, o = price(h), c = price(h + 1), hi = Math.max(o, c) + 0.5, lo = Math.min(o, c) - 0.5;
  return [time / 1000, String(o), String(hi), String(lo), String(c), String((o + c) / 2), '12.5', 40 + (h % 7)];
};
const baseCurrent = Math.floor(Date.UTC(2026, 0, 15, 12, 0, 0) / STEP) * STEP;
// "Kraken" falso: devolve até 720 linhas até world.latest (a última é o candle aberto), respeitando `since`.
function makeWorld(latest = baseCurrent) {
  const world = {latest, missing: new Set(), requests: [], fail: false, corrupt: new Map()};
  world.fetch = async (url) => {
    world.requests.push(url);
    if (world.fail) throw new TypeError('fetch failed');
    const u = new URL(url), since = u.searchParams.get('since');
    const rows = [];
    for (let t = world.latest - 719 * STEP; t <= world.latest; t += STEP) {
      if (since !== null && t <= Number(since) * 1000) continue;
      if (world.missing.has(t)) continue;
      const r = row(t); if (world.corrupt.has(t)) r[4] = String(world.corrupt.get(t));
      rows.push(r);
    }
    return {ok: true, status: 200, json: async () => ({error: [], result: {XXBTZUSD: rows, last: world.latest / 1000}})};
  };
  return world;
}
const baseTmp = await fs.mkdtemp(path.join(os.tmpdir(), 'tradernova-worker-test-'));
let n = 0;
const newDir = () => path.join(baseTmp, `t${n++}`);
async function setup(dir, world, {evaluate, clock = {t: baseCurrent + 10000}, config = {}} = {}) {
  const lines = [];
  const log = createLogger([(l) => lines.push(JSON.parse(l))], {provider: 'kraken-spot', symbol: 'BTCUSD', interval: 60}, () => clock.t);
  const cfg = {...parseConfig([], {}), dataDir: dir, ...config};
  const worker = await createWorker({config: cfg, log, fetch: world.fetch, now: () => clock.t, evaluate});
  return {worker, lines, clock, events: (e) => lines.filter((l) => l.event === e)};
}
const readLines = async (file) => (await fs.readFile(file, 'utf8')).split('\n').filter(Boolean);
const candleFile = (dir) => path.join(dir, 'candles', 'kraken-spot_BTCUSD_60m.jsonl');
const dirFiles = async (dir, sub) => (await fs.readdir(path.join(dir, sub)).catch(() => []));
// Avaliador falso: devolve uma leitura 'buy' coerente para o último candle fechado.
const stubEvaluate = (bars, interval, receivedAt, now) => {
  const step = interval * 60000, current = Math.floor(now / step) * step, forming = bars.find((b) => b.time === current);
  return {status: 'ready', reason: 'stub', source: 'kraken-spot', evaluatedAt: now, closedAt: current, readings: [
    {candidateId: 'T1', state: 'buy', signalTime: current - step, entryReference: forming.open, stop: forming.open - 2, target: forming.open + 4, evidence: ['Evidência de teste.']},
    {candidateId: 'T2', state: 'waiting', signalTime: current - step, entryReference: null, stop: null, target: null, evidence: []},
    {candidateId: 'T3', state: 'sell-excluded', signalTime: current - step, entryReference: null, stop: null, target: null, evidence: []}]};
};
try {
  // 1. Só candles fechados são gravados; o candle aberto e a última linha da fonte ficam de fora.
  {
    const dir = newDir(), world = makeWorld(), t = await setup(dir, world);
    const r = await t.worker.cycle();
    assert.equal(r.ok, true);
    const stored = (await readLines(candleFile(dir))).map((l) => JSON.parse(l));
    assert.equal(stored.length, 719, '720 linhas da fonte menos o candle aberto');
    assert.equal(stored.at(-1).time, baseCurrent - STEP);
    assert.ok(stored.every((c) => c.time + STEP <= t.clock.t), 'nenhum candle aberto gravado');
    assert.ok(stored.every((c, i) => i === 0 || c.time > stored[i - 1].time), 'ordem estritamente crescente');
    assert.equal(r.feed, 'ao_vivo');
    // 2. Reingestão do mesmo trecho não duplica.
    const again = await t.worker.cycle();
    assert.equal(again.newCandles, 0);
    assert.equal((await readLines(candleFile(dir))).length, 719);
    assert.ok(t.events('ciclo_concluido').at(-1).duplicates >= 0);
    // checkpoint atômico: nenhum .tmp sobrando
    const cps = await dirFiles(dir, 'checkpoints');
    assert.deepEqual(cps, ['kraken-spot_BTCUSD_60m.json']);
    const cp = JSON.parse(await fs.readFile(path.join(dir, 'checkpoints', cps[0]), 'utf8'));
    assert.equal(cp.lastClosedOpenTime, baseCurrent - STEP);
  }
  // 3. Reinício: usa `since` do checkpoint, não duplica, e anexa só o candle novo.
  {
    const dir = newDir(), world = makeWorld(), a = await setup(dir, world);
    await a.worker.cycle();
    world.latest = baseCurrent + STEP;
    const clock = {t: baseCurrent + STEP + 10000}, b = await setup(dir, world, {clock});
    assert.equal(b.events('armazem_carregado')[0].candles, 719);
    const r = await b.worker.cycle();
    const since = new URL(world.requests.at(-1)).searchParams.get('since');
    assert.equal(Number(since), (baseCurrent - STEP) / 1000, 'since vem do checkpoint');
    assert.equal(r.newCandles, 1);
    const times = (await readLines(candleFile(dir))).map((l) => JSON.parse(l).time);
    assert.equal(times.length, 720);
    assert.equal(new Set(times).size, 720);
    assert.equal(times.at(-1), baseCurrent);
  }
  // 4. Lacuna: detectada, registrada, e o feed passa a 'historico_insuficiente' (sem avaliação).
  {
    const dir = newDir(), world = makeWorld(), evaluated = [];
    world.missing.add(baseCurrent - 5 * STEP);
    const t = await setup(dir, world, {evaluate: (...args) => { evaluated.push(args); return stubEvaluate(...args); }});
    const r = await t.worker.cycle();
    assert.equal(t.events('lacuna_detectada').length, 1);
    assert.equal(t.events('lacuna_detectada')[0].missing, 1);
    assert.equal(r.feed, 'historico_insuficiente');
    assert.equal(evaluated.length, 0);
    assert.ok(t.events('avaliacao_ignorada').length >= 1);
    assert.equal(contiguousTail([{time: 0}, {time: STEP}, {time: 3 * STEP}, {time: 4 * STEP}], 60).length, 2);
  }
  // 5. Fonte parada: candle fechado velho demais -> 'atrasado', nada avaliado.
  {
    const dir = newDir(), world = makeWorld(), evaluated = [];
    const t = await setup(dir, world, {evaluate: (...args) => { evaluated.push(args); return stubEvaluate(...args); }});
    await t.worker.cycle();
    evaluated.length = 0;
    t.clock.t = baseCurrent + 4 * STEP; // a fonte continua devolvendo dados de 4 h atrás
    const r = await t.worker.cycle();
    assert.equal(r.ok, true);
    assert.equal(r.feed, 'atrasado');
    assert.equal(evaluated.length, 0);
    assert.equal(t.events('avaliacao_ignorada').at(-1).feed_state, 'atrasado');
    // limites do estado
    const base = {now: 1e9, interval: 60, pollMs: 30000, lastFetchOk: true, lastSuccessAt: 1e9 - 1000, lastClosedOpenTime: 1e9 - STEP, contiguousClosed: 300};
    assert.equal(computeFeedState(base).state, 'ao_vivo');
    assert.equal(computeFeedState({...base, lastSuccessAt: 1e9 - 91000}).state, 'atrasado');
    assert.equal(computeFeedState({...base, lastClosedOpenTime: 1e9 - 2 * STEP - 1}).state, 'atrasado');
    assert.equal(computeFeedState({...base, contiguousClosed: 200}).state, 'historico_insuficiente');
    assert.equal(computeFeedState({...base, lastFetchOk: false}).state, 'desconectado');
  }
  // 6. Falha de consulta: 'desconectado', sem sinais, sem exceção; recupera depois.
  {
    const dir = newDir(), world = makeWorld(), evaluated = [];
    world.fail = true;
    const t = await setup(dir, world, {evaluate: (...args) => { evaluated.push(args); return stubEvaluate(...args); }});
    const r = await t.worker.cycle();
    assert.deepEqual([r.ok, r.feed, r.signalsCreated], [false, 'desconectado', 0]);
    assert.equal(evaluated.length, 0);
    assert.equal(t.events('estado_do_feed')[0].feed_state, 'desconectado');
    assert.equal(t.worker.signals.list().length, 0);
    world.fail = false;
    assert.equal((await t.worker.cycle()).feed, 'ao_vivo');
  }
  // 7. Candle corrigido para open_time existente: mantém o primeiro e avisa.
  {
    const dir = newDir(), world = makeWorld(), t = await setup(dir, world);
    await t.worker.cycle();
    const t2 = await setup(dir, world); // reinício: carrega o armazém existente
    await t2.worker.store.append([{...JSON.parse((await readLines(candleFile(dir))).at(-3)), close: 123.456}]);
    assert.equal(t2.events('candle_corrigido_ignorado').length, 1);
    assert.equal((await readLines(candleFile(dir))).length, 719);
  }
  // 8. Sinais com avaliador injetado: validam no schema, são 'research' e deduplicam entre reinícios.
  {
    const dir = newDir(), world = makeWorld(), a = await setup(dir, world, {evaluate: stubEvaluate});
    const r = await a.worker.cycle();
    assert.equal(r.evaluated, true);
    assert.equal(r.signalsCreated, 1, 'só a leitura buy vira sinal');
    // reinício SEM checkpoint: reavalia o mesmo candle, e a chave de deduplicação impede o segundo registro
    await fs.rm(path.join(dir, 'checkpoints'), {recursive: true});
    const b = await setup(dir, world, {evaluate: stubEvaluate});
    const r2 = await b.worker.cycle();
    assert.equal(r2.evaluated, true);
    assert.equal(r2.signalsCreated, 0);
    assert.equal(b.events('sinal_duplicado_ignorado').length, 1);
    const stored = (await readLines(path.join(dir, 'signals', 'kraken-spot_BTCUSD_60m.jsonl'))).map((l) => JSON.parse(l));
    assert.equal(stored.length, 1);
    for (const s of stored) {
      assert.equal(signalRecordSchema.safeParse(s).success, true);
      assert.equal(s.mode, 'research');
      assert.equal(s.provider, 'kraken-spot');
      assert.equal(s.strategyId, 'T1');
      assert.equal(s.strategyVersion, 'T1-E0X0');
      assert.equal(s.expiresAt, baseCurrent + 30000);
    }
    // reinício COM checkpoint não reavalia
    const c = await setup(dir, world, {evaluate: stubEvaluate});
    assert.equal((await c.worker.cycle()).evaluated, false);
    // o armazém de sinais reabre idempotente
    const reopened = await openFileSignalStore(path.join(dir, 'signals', 'kraken-spot_BTCUSD_60m.jsonl'));
    assert.equal((await reopened.findByDedupKey(stored[0].dedupKey)).publicId, stored[0].publicId);
    assert.equal((await reopened.insertIfAbsent({...stored[0], publicId: '11111111-1111-4111-8111-111111111111'})).created, false);
  }
  // 9. Sinal fora da janela de entrada de 30 s é descartado, não gravado.
  {
    const dir = newDir(), world = makeWorld(), t = await setup(dir, world, {evaluate: stubEvaluate, clock: {t: baseCurrent + 45000}});
    const r = await t.worker.cycle();
    assert.equal(r.signalsCreated, 0);
    assert.equal(t.events('sinal_descartado').length, 1);
  }
  // 10. Integração com o motor real: roda sem erro; se alguma estratégia disparar, o registro é válido e 'research'.
  {
    // procura (de forma determinística) um fim de série em que o motor real emita 'buy'
    let found = null;
    for (let k = 0; k < 120 && !found; k++) {
      const cur = baseCurrent + k * STEP, bars = [];
      for (let t0 = cur - 400 * STEP; t0 <= cur; t0 += STEP) { const r = row(t0); bars.push({time: t0, open: +r[1], high: +r[2], low: +r[3], close: +r[4], volume: +r[6]}); }
      const snap = evaluatePaperEngine(bars, 60, cur + 10000, cur + 10000);
      if (snap.status === 'ready' && snap.readings.some((x) => x.state === 'buy')) found = cur;
    }
    console.log('real-engine fixture buy found:', found !== null);
    const cur = found ?? baseCurrent, dir = newDir(), world = makeWorld(cur);
    const t = await setup(dir, world, {clock: {t: cur + 10000}});
    const r = await t.worker.cycle();
    assert.equal(r.ok, true);
    assert.equal(r.evaluated, true, 'o motor real avaliou');
    assert.equal(t.events('sinal_invalido').length, 0);
    const sigs = t.worker.signals.list();
    for (const s of sigs) { assert.equal(signalRecordSchema.safeParse(s).success, true); assert.equal(s.mode, 'research'); }
    if (found) assert.ok(sigs.length >= 1, 'estratégia real disparou na fixture');
    assert.equal(strategyApprovals.length, 0, 'registro de aprovações continua vazio');
  }
  // 11. Linha final truncada no armazém (queda de energia) é tolerada.
  {
    const dir = newDir(), world = makeWorld(), a = await setup(dir, world);
    await a.worker.cycle();
    await fs.appendFile(candleFile(dir), '{"time":17');
    const b = await setup(dir, world);
    assert.equal(b.events('linhas_invalidas_ignoradas')[0].count, 1);
    await b.worker.cycle();
    const lines = await readLines(candleFile(dir));
    assert.equal(lines.filter((l) => { try { JSON.parse(l); return false; } catch { return true; } }).length, 1, 'apenas a linha truncada continua inválida');
  }
  // 12. Configuração: padrões, env, flags e rejeições.
  {
    const d = parseConfig([], {});
    assert.deepEqual([d.pair, d.interval, d.pollSeconds, d.dataDir], ['BTCUSD', 60, 30, 'worker-data']);
    assert.equal(parseConfig([], {TRADERNOVA_WORKER_PAIR: 'ethusd'}).pair, 'ETHUSD');
    assert.equal(parseConfig(['--pair', 'SOLUSD', '--interval=15', '--once'], {TRADERNOVA_WORKER_PAIR: 'ETHUSD'}).interval, 15);
    for (const bad of [['--pair', 'XAUUSD'], ['--interval', '5'], ['--poll-seconds', '1'], ['--nada']]) assert.throws(() => parseConfig(bad, {}));
    // Vários pares/intervalos: produto cartesiano, sem repetição, listas têm prioridade sobre --pair/--interval.
    const multi = parseConfig(['--pairs', 'btcusd, ETHUSD,BTCUSD', '--intervals=15,60', '--pair', 'SOLUSD'], {});
    assert.deepEqual(multi.targets, [{pair: 'BTCUSD', interval: 15}, {pair: 'BTCUSD', interval: 60}, {pair: 'ETHUSD', interval: 15}, {pair: 'ETHUSD', interval: 60}]);
    assert.deepEqual([multi.pair, multi.interval], ['BTCUSD', 15]);
    assert.deepEqual(parseConfig([], {TRADERNOVA_WORKER_PAIRS: 'SOLUSD,ETHUSD', TRADERNOVA_WORKER_INTERVALS: '60'}).targets, [{pair: 'SOLUSD', interval: 60}, {pair: 'ETHUSD', interval: 60}]);
    assert.deepEqual(d.targets, [{pair: 'BTCUSD', interval: 60}], 'padrão continua um par só');
    const split = workerConfigs(multi);
    assert.equal(split.length, 4);
    assert.deepEqual(split.map((c) => [c.pair, c.interval, c.targets.length, c.dataDir]), [['BTCUSD', 15, 1, 'worker-data'], ['BTCUSD', 60, 1, 'worker-data'], ['ETHUSD', 15, 1, 'worker-data'], ['ETHUSD', 60, 1, 'worker-data']]);
    for (const bad of [['--pairs', 'BTCUSD,XAUUSD'], ['--intervals', '15,5'], ['--pairs', ','], ['--intervals', '']]) assert.throws(() => parseConfig(bad, {}), undefined, bad.join(' '));
  }
  // 12b. Vários pares num processo: armazéns separados e a falha de um par não derruba os outros.
  {
    const dir = newDir(), world = makeWorld(Math.floor(Date.now() / STEP) * STEP);
    const realFetch = globalThis.fetch, realWrite = process.stdout.write, out = [];
    globalThis.fetch = async (url, init) => (new URL(url).searchParams.get('pair') === 'ETHUSD' ? Promise.reject(new TypeError('fetch failed')) : world.fetch(url, init));
    process.stdout.write = (line) => { out.push(JSON.parse(line)); return true; };
    let code;
    try { code = await main(['--pairs', 'BTCUSD,ETHUSD', '--once', '--data-dir', dir], {}); } finally { globalThis.fetch = realFetch; process.stdout.write = realWrite; }
    assert.equal(code, 1, '--once sai com 1 se alguma combinação falhou');
    assert.ok((await readLines(candleFile(dir))).length > 0, 'BTC gravou candles mesmo com ETH fora');
    assert.deepEqual(await dirFiles(dir, 'candles'), ['kraken-spot_BTCUSD_60m.jsonl']);
    assert.ok(out.some((l) => l.event === 'consulta_falhou' && l.symbol === 'ETHUSD'), 'falha registrada com o par certo');
    assert.ok(out.some((l) => l.event === 'ciclo_concluido' && l.symbol === 'BTCUSD'));
    assert.deepEqual(out.find((l) => l.event === 'worker_iniciado').targets, ['BTCUSD/60m', 'ETHUSD/60m']);
    // Heartbeat por combinação, inclusive da que falhou (estado desconectado, sem afirmar ao vivo).
    const status = async (pair) => JSON.parse(await fs.readFile(path.join(dir, 'status', `kraken-spot_${pair}_60m.json`), 'utf8'));
    assert.equal((await status('ETHUSD')).feedState, 'desconectado');
    assert.equal((await status('ETHUSD')).lastSuccessAt, null);
    assert.ok((await status('BTCUSD')).lastSuccessAt > 0);
  }
  // 13. buildSignalRecord só aceita 'buy'.
  {
    const cfg = parseConfig([], {}), snap = {closedAt: 5, readings: []};
    assert.equal(buildSignalRecord({candidateId: 'T1', state: 'sell-excluded', signalTime: 1, entryReference: null, stop: null, target: null, evidence: []}, snap, cfg, 1), null);
  }
  console.log('Worker checks passed: closed-only store, dedup, restart/since, gaps, feed states, signal dedup, research mode, atomic checkpoint.');
} finally { await fs.rm(baseTmp, {recursive: true, force: true}); }
