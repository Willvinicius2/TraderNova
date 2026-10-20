// Testes offline da saúde do worker (heartbeat): limites de saúde, gravação/leitura (arquivo, HTTP local, Supabase simulado), rota e modelo de tela.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import '../worker/register.mjs';
const imp = (rel) => import(pathToFileURL(path.resolve(new URL(rel, import.meta.url).pathname)).href);
const {workerHealth, describeWorkerStatus, toStatusResponse, supabaseWorkerStatusWriter, supabaseWorkerStatusReader, workerStatusResponseSchema} = await imp('../lib/tradernova/worker-status.ts');
const {lookupWorkerStatus, statusReaderFromEnv} = await imp('../lib/tradernova/worker-status-source.ts');
const {writeFileStatus, readFileStatuses, statusFile} = await imp('../worker/status-file.ts');
const {startSignalReadServer} = await imp('../worker/http.ts');
const {GET} = await imp('../app/api/worker-status/route.ts');

const now = Date.UTC(2026, 9, 20, 12, 0, 0);
const status = (over = {}) => ({provider: 'kraken-spot', instrument: 'BTCUSD', timeframeMinutes: 60, pollSeconds: 30, lastCycleAt: now - 10000, lastSuccessAt: now - 10000, feedState: 'ao_vivo', lastClosedOpenTime: now - 7200000, ...over});
const reply = (code, body) => ({ok: code >= 200 && code < 300, status: code, text: async () => (typeof body === 'string' ? body : JSON.stringify(body))});

// ---- 1. Limites de saúde ----
const h = (ageMs, poll = 30) => workerHealth({lastCycleAt: now - ageMs, pollSeconds: poll}, now);
assert.equal(h(0), 'ativo');
assert.equal(h(120000), 'ativo', '2 consultas + 1 min');
assert.equal(h(120001), 'atrasado');
assert.equal(h(15 * 60000), 'atrasado');
assert.equal(h(15 * 60000 + 1), 'parado');
assert.equal(h(-120000), 'parado', 'relógio do worker no futuro não conta como ativo');
assert.equal(h(11 * 60000, 300), 'ativo', 'consulta lenta (5 min) tolera mais');
assert.equal(h(20 * 60000, 300), 'atrasado');
assert.equal(h(31 * 60000, 300), 'parado');

// ---- 2. Modelo de tela ----
assert.deepEqual(describeWorkerStatus(null), {kind: 'loading'});
assert.match(describeWorkerStatus({state: 'source-unavailable', reason: 'not-configured'}).text, /não está conectado/);
assert.match(describeWorkerStatus({state: 'source-unavailable', reason: 'unreachable'}).text, /Não foi possível/);
assert.match(describeWorkerStatus(toStatusResponse([], now)).text, /nenhum ciclo/);
{
  const view = describeWorkerStatus(toStatusResponse([status(), status({instrument: 'ETHUSD', timeframeMinutes: 15, lastCycleAt: now - 3600000})], now), 'UTC');
  assert.equal(view.kind, 'list');
  assert.deepEqual(view.items.map((i) => [i.label, i.healthLabel, i.tone]), [['BTCUSD · H1', 'Ativo', 'positive'], ['ETHUSD · M15', 'Parado', 'neutral']]);
  assert.match(view.items[0].detail, /20\/10.*11:59.*feed ao vivo/);
  assert.match(view.items[1].detail, /último estado: feed ao vivo/, 'worker parado nunca afirma feed ao vivo');
}

// ---- 3. Supabase simulado ----
{
  const rows = new Map(), calls = [];
  const fetch = async (url, init) => {
    calls.push({url, init});
    const u = new URL(url);
    assert.equal(u.pathname, '/rest/v1/worker_status');
    if (init.method === 'POST') {
      assert.equal(u.searchParams.get('on_conflict'), 'provider,instrument,timeframe_minutes');
      assert.match(init.headers.Prefer, /resolution=merge-duplicates/);
      const [row] = JSON.parse(init.body);
      rows.set(`${row.provider}|${row.instrument}|${row.timeframe_minutes}`, row);
      return reply(201, [row]);
    }
    return reply(200, [...rows.values()].map((r) => ({...r, last_cycle_at: String(r.last_cycle_at)})));
  };
  const cfg = {url: 'https://exemplo.supabase.co', key: 'k', fetch};
  const write = supabaseWorkerStatusWriter(cfg), read = supabaseWorkerStatusReader(cfg);
  await write(status({lastCycleAt: now - 50000}));
  await write(status());
  assert.deepEqual(await read(), [status()], 'upsert mantém uma linha por combinação');
  await assert.rejects(write({...status(), feedState: 'otimo'}));
  const reader = statusReaderFromEnv({TRADERNOVA_SUPABASE_URL: cfg.url, TRADERNOVA_SUPABASE_READ_KEY: 'k', TRADERNOVA_SIGNAL_SOURCE_URL: 'http://127.0.0.1:1'}, fetch);
  const res = await lookupWorkerStatus(reader, now);
  assert.equal(res.state, 'ok');
  assert.equal(res.workers[0].health, 'ativo');
  assert.ok(workerStatusResponseSchema.safeParse(res).success);
  const bad = await lookupWorkerStatus(supabaseWorkerStatusReader({...cfg, fetch: async () => reply(200, [{provider: 'x'}])}), now);
  assert.deepEqual(bad, {state: 'source-unavailable', reason: 'invalid-response'});
  const down = await lookupWorkerStatus(supabaseWorkerStatusReader({...cfg, fetch: async () => reply(500, '')}), now);
  assert.deepEqual(down, {state: 'source-unavailable', reason: 'unreachable'});
}
assert.deepEqual(await lookupWorkerStatus(statusReaderFromEnv({}, async () => reply(200, [])), now), {state: 'source-unavailable', reason: 'not-configured'});

// ---- 4. Arquivo + servidor local do worker + rota ----
const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'tradernova-status-'));
let server;
try {
  await writeFileStatus(dir, status());
  await writeFileStatus(dir, status({instrument: 'ETHUSD'}));
  await fs.writeFile(path.join(dir, 'status', 'quebrado.json'), '{"provider":');
  assert.equal(statusFile(dir, status()), path.join(dir, 'status', 'kraken-spot_BTCUSD_60m.json'));
  assert.deepEqual((await readFileStatuses(path.join(dir, 'status'))).map((s) => s.instrument), ['BTCUSD', 'ETHUSD'], 'arquivo corrompido é ignorado');
  assert.deepEqual(await readFileStatuses(path.join(dir, 'nada')), []);
  server = await startSignalReadServer({signalsDir: path.join(dir, 'signals'), statusDir: path.join(dir, 'status'), port: 0});
  const base = `http://127.0.0.1:${server.port}`;
  const viaHttp = await fetch(`${base}/status`);
  assert.equal(viaHttp.status, 200);
  assert.equal((await viaHttp.json()).length, 2);
  assert.equal((await fetch(`${base}/status`, {method: 'POST'})).status, 405);
  const env = {...process.env};
  try {
    for (const k of Object.keys(process.env)) if (k.startsWith('TRADERNOVA_')) delete process.env[k];
    let response = await GET();
    assert.equal(response.status, 503);
    assert.deepEqual(await response.json(), {state: 'source-unavailable', reason: 'not-configured'});
    process.env.TRADERNOVA_SIGNAL_SOURCE_URL = base;
    response = await GET();
    assert.equal(response.status, 200);
    assert.equal(response.headers.get('cache-control'), 'no-store');
    const body = await response.json();
    assert.deepEqual(body.workers.map((w) => w.instrument), ['BTCUSD', 'ETHUSD']);
    const expected = workerHealth(status(), Date.now());
    assert.ok(body.workers.every((w) => w.health === expected), 'saúde calculada com o relógio do servidor');
  } finally { process.env = env; }
} finally { await server?.close(); await fs.rm(dir, {recursive: true, force: true}); }

console.log('Worker status checks passed: health limits, screen model, Supabase upsert/read, file and local HTTP, route.');
