// Testes offline do adaptador Supabase de sinais (fetch simulado): leitura pela rota, armazém idempotente do worker e escolha por ambiente.
// Os registros aqui são FIXTURES de teste (mode 'test'), não sinais reais.
import assert from 'node:assert/strict';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import '../worker/register.mjs';
const imp = (rel) => import(pathToFileURL(path.resolve(new URL(rel, import.meta.url).pathname)).href);
const {recordToRow, rowToRecord, supabaseSignalSource, supabaseSignalStore, supabaseSignalsFromEnv, SupabaseSignalError} = await imp('../lib/tradernova/supabase-signals.ts');
const {lookupSignal, signalSourceFromEnv} = await imp('../lib/tradernova/signal-source.ts');
const {newPublicSignalId, signalDedupKey} = await imp('../lib/tradernova/signal-record.ts');
const {parseConfig} = await imp('../worker/config.ts');

const now = Date.now();
const makeRecord = (over = {}) => {
  const parts = {strategyId: 'T1', strategyVersion: 'E0X0', provider: 'kraken-spot', instrument: 'BTCUSD', timeframeMinutes: 60, side: 'buy', signalTime: now - 3600000};
  return {publicId: newPublicSignalId(), dedupKey: signalDedupKey(parts), ...parts, generatedAt: now - 1000, expiresAt: now + 60000, entryReference: 100, stop: 95, target: 110, evidence: ['Evidência de teste.'], mode: 'test', invalidatedAt: null, invalidationReason: null, ...over};
};
const reply = (status, body) => ({ok: status >= 200 && status < 300, status, text: async () => (typeof body === 'string' ? body : JSON.stringify(body))});
const URL_ = 'https://exemplo.supabase.co';
const fake = (handler) => { const calls = []; return {calls, fetch: async (url, init) => { calls.push({url, init}); return handler(url, init); }}; };

// ---- 1. Mapeamento linha <-> registro ----
const record = makeRecord();
const row = recordToRow(record);
assert.equal(row.public_id, record.publicId.toLowerCase());
assert.deepEqual(rowToRecord(row), record, 'ida e volta preserva o registro');
// PostgREST pode devolver numeric/bigint como texto.
assert.deepEqual(rowToRecord({...row, entry_reference: '100', stop: '95', target: '110', signal_time: String(row.signal_time)}), record);
assert.throws(() => rowToRecord({...row, side: 'hold'}), SupabaseSignalError);
assert.throws(() => rowToRecord({...row, stop: 'abc'}), SupabaseSignalError);
assert.throws(() => rowToRecord(null), SupabaseSignalError);

// ---- 2. Leitura por ID ----
{
  const f = fake(() => reply(200, [row]));
  const source = supabaseSignalSource({url: URL_, key: 'k-leitura', fetch: f.fetch});
  assert.deepEqual(await source.read(record.publicId.toUpperCase()), record);
  const {url, init} = f.calls[0];
  assert.equal(url, `${URL_}/rest/v1/research_signals?public_id=eq.${record.publicId.toLowerCase()}&select=*&limit=2`);
  assert.equal(init.method, 'GET');
  assert.equal(init.headers.apikey, 'k-leitura');
  assert.equal(init.headers.Authorization, 'Bearer k-leitura');
  assert.equal(init.redirect, 'manual');
  // ID fora do formato nunca vira consulta.
  assert.equal(await source.read('nao-e-uuid'), null);
  assert.equal(await source.read(`${record.publicId}&select=*`), null);
  assert.equal(f.calls.length, 1);
}
{
  const source = (handler) => supabaseSignalSource({url: URL_, key: 'k', fetch: fake(handler).fetch});
  assert.equal(await source(() => reply(200, [])).read(record.publicId), null, 'sem linha = não encontrado');
  const reason = async (handler) => { try { await source(handler).read(record.publicId); return 'ok'; } catch (e) { return e.reason; } };
  assert.equal(await reason(() => { throw new Error('rede'); }), 'unreachable');
  assert.equal(await reason(() => reply(401, {message: 'JWT'})), 'unreachable');
  assert.equal(await reason(() => reply(500, 'x')), 'unreachable');
  assert.equal(await reason(() => reply(200, 'não é json')), 'invalid-response');
  assert.equal(await reason(() => reply(200, {})), 'invalid-response');
  assert.equal(await reason(() => reply(200, [row, row])), 'invalid-response');
  assert.equal(await reason(() => reply(200, [{...row, mode: 'live'}])), 'invalid-response');
  assert.equal(await reason(() => reply(200, [{...row, public_id: newPublicSignalId()}])), 'invalid-response', 'linha de outro ID é rejeitada');
  assert.equal(await reason(() => reply(200, 'x'.repeat(262145))), 'invalid-response');
}
// HTTPS obrigatório (http só em localhost) e chave obrigatória.
assert.throws(() => supabaseSignalSource({url: 'http://exemplo.supabase.co', key: 'k', fetch: async () => reply(200, [])}));
assert.throws(() => supabaseSignalSource({url: URL_, key: ' ', fetch: async () => reply(200, [])}));
supabaseSignalSource({url: 'http://127.0.0.1:54321', key: 'k', fetch: async () => reply(200, [])});

// ---- 3. Rota: lookupSignal com a fonte do Supabase ----
{
  const env = {TRADERNOVA_SUPABASE_URL: URL_, TRADERNOVA_SUPABASE_READ_KEY: 'k-leitura', TRADERNOVA_SIGNAL_SOURCE_URL: 'http://127.0.0.1:8790'};
  const f = fake(() => reply(200, [row]));
  const source = signalSourceFromEnv(env, f.fetch);
  const found = await lookupSignal(record.publicId, source, now);
  assert.equal(found.status, 200);
  assert.equal(found.body.state, 'active');
  assert.ok(f.calls[0].url.startsWith(`${URL_}/rest/v1/`), 'Supabase tem prioridade sobre o worker local');
  const down = await lookupSignal(record.publicId, signalSourceFromEnv(env, async () => reply(503, '')), now);
  assert.deepEqual(down, {status: 503, body: {state: 'source-unavailable', reason: 'unreachable'}});
  const bad = await lookupSignal(record.publicId, signalSourceFromEnv(env, async () => reply(200, [{...row, stop: 200}])), now);
  assert.deepEqual(bad.body, {state: 'source-unavailable', reason: 'invalid-response'});
  // A chave de serviço nunca é usada pela rota.
  const onlyService = signalSourceFromEnv({TRADERNOVA_SUPABASE_URL: URL_, TRADERNOVA_SUPABASE_SERVICE_KEY: 's'}, f.fetch);
  assert.equal(onlyService, null);
  assert.equal(signalSourceFromEnv({TRADERNOVA_SUPABASE_URL: 'http://exemplo.supabase.co', TRADERNOVA_SUPABASE_READ_KEY: 'k'}, f.fetch), null);
}
assert.equal(supabaseSignalsFromEnv({TRADERNOVA_SUPABASE_URL: URL_}, 'TRADERNOVA_SUPABASE_SERVICE_KEY', async () => reply(200, [])), null);
assert.equal(supabaseSignalsFromEnv({TRADERNOVA_SUPABASE_URL: 'nada', TRADERNOVA_SUPABASE_SERVICE_KEY: 's'}, 'TRADERNOVA_SUPABASE_SERVICE_KEY', async () => reply(200, [])), null);

// ---- 4. Armazém do worker: insertIfAbsent idempotente ----
{
  // Banco simulado com unique em dedup_key, como a migração.
  const table = new Map();
  const f = fake((url, init) => {
    const u = new URL(url);
    if (init.method === 'POST') {
      assert.equal(u.searchParams.get('on_conflict'), 'dedup_key');
      assert.match(init.headers.Prefer, /resolution=ignore-duplicates/);
      assert.match(init.headers.Prefer, /return=representation/);
      const [incoming] = JSON.parse(init.body);
      if (table.has(incoming.dedup_key)) return reply(201, []);
      table.set(incoming.dedup_key, incoming);
      return reply(201, [incoming]);
    }
    const dedup = u.searchParams.get('dedup_key'), pub = u.searchParams.get('public_id');
    const rows = [...table.values()].filter((r) => (dedup ? `eq.${r.dedup_key}` === dedup : `eq.${r.public_id}` === pub));
    return reply(200, rows);
  });
  const store = supabaseSignalStore({url: URL_, key: 'k-servico', fetch: f.fetch});
  const first = await store.insertIfAbsent(record);
  assert.deepEqual(first, {record, created: true});
  const again = await store.insertIfAbsent({...record, publicId: newPublicSignalId()});
  assert.equal(again.created, false);
  assert.equal(again.record.publicId, record.publicId, 'duplicata devolve o registro guardado');
  assert.equal(table.size, 1);
  assert.deepEqual(await store.get(record.publicId), record);
  assert.deepEqual(await store.findByDedupKey(record.dedupKey), record);
  assert.equal(await store.findByDedupKey('inexistente'), null);
  assert.equal(f.calls.find((c) => c.init.method === 'POST').init.headers.apikey, 'k-servico');
  // Registro fora do contrato nunca é enviado.
  const before = f.calls.length;
  await assert.rejects(store.insertIfAbsent({...record, mode: 'live'}));
  assert.equal(f.calls.length, before);
}
{
  const store = supabaseSignalStore({url: URL_, key: 'k', fetch: async (url, init) => (init.method === 'POST' ? reply(201, []) : reply(200, []))});
  await assert.rejects(store.insertIfAbsent(record), (e) => e.reason === 'invalid-response', 'conflito sem registro existente');
  const failing = supabaseSignalStore({url: URL_, key: 'k', fetch: async () => reply(409, {message: 'conflict'})});
  await assert.rejects(failing.insertIfAbsent(record), (e) => e.reason === 'unreachable');
}

// ---- 5. Configuração do worker ----
assert.equal(parseConfig([], {}).signalStore, 'file');
assert.equal(parseConfig(['--signal-store', 'supabase'], {}).signalStore, 'supabase');
assert.equal(parseConfig([], {TRADERNOVA_WORKER_SIGNAL_STORE: 'SUPABASE'}).signalStore, 'supabase');
assert.throws(() => parseConfig(['--signal-store', 'redis'], {}), /não suportado/);

console.log('supabase-signals: ok');
