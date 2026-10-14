// Testes offline da consulta de sinais: rota /api/signals/[id] (fetch simulado), mapeamento da ficha, servidor de leitura do worker e regressão do ID do motor.
// Os registros aqui são FIXTURES de teste (mode 'test'), não sinais reais.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import ts from 'typescript';
import '../worker/register.mjs';
import {loadResearchModules} from '../scripts/research-modules.mjs';
const imp = (rel) => import(pathToFileURL(path.resolve(new URL(rel, import.meta.url).pathname)).href);
const {GET, ...otherExports} = await imp('../app/api/signals/[id]/route.ts');
const {lookupSignal, workerHttpSource, signalSourceFromEnv} = await imp('../lib/tradernova/signal-source.ts');
const {toSheetModel, parseSignalResponse, fetchSignal} = await imp('../lib/tradernova/signal-client.ts');
const {newPublicSignalId, isPublicSignalId, signalDedupKey} = await imp('../lib/tradernova/signal-record.ts');
const {openFileSignalStore} = await imp('../worker/signal-file-store.ts');
const {startSignalReadServer} = await imp('../worker/http.ts');
const {parseConfig} = await imp('../worker/config.ts');

const BASE = 'http://127.0.0.1:8790';
const now = Date.now();
const makeRecord = (over = {}) => {
  const parts = {strategyId: 'T1', strategyVersion: 'E0X0', provider: 'kraken-spot', instrument: 'BTCUSD', timeframeMinutes: 60, side: 'buy', signalTime: now - 3600000};
  return {publicId: newPublicSignalId(), dedupKey: signalDedupKey({...parts, signalTime: parts.signalTime + Math.floor(Math.random() * 1e6)}), ...parts, generatedAt: now - 1000, expiresAt: now + 60000, entryReference: 100, stop: 95, target: 110, evidence: ['Evidência de teste.'], mode: 'test', invalidatedAt: null, invalidationReason: null, ...over};
};
const reply = (status, body) => ({ok: status >= 200 && status < 300, status, text: async () => (typeof body === 'string' ? body : JSON.stringify(body))});

// ---- 1. Rota /api/signals/[id] ----
assert.deepEqual(Object.keys(otherExports).filter((k) => /^(POST|PUT|PATCH|DELETE)$/.test(k)), [], 'somente GET');
const realFetch = globalThis.fetch, calls = [];
let handler = async () => reply(404, {});
globalThis.fetch = async (url, init) => { calls.push({url: String(url), init}); return handler(String(url), init); };
const call = async (id) => {
  const response = await GET(new Request(`http://app.local/api/signals/${encodeURIComponent(id)}`), {params: Promise.resolve({id})});
  const text = await response.text();
  return {status: response.status, cache: response.headers.get('cache-control'), text, body: JSON.parse(text)};
};
const reset = () => { calls.length = 0; };
try {
  const id = newPublicSignalId();
  // id inválido: 400, nunca consulta a fonte, nunca devolve o texto recebido
  process.env.TRADERNOVA_SIGNAL_SOURCE_URL = BASE;
  for (const bad of ['T1:abc', 'T1:T1-E0X0:1789948800000', 'test-123', '<script>alert(1)</script>', '../etc/passwd', '', `${id}x`, 'a'.repeat(5000)]) {
    reset();
    const r = await call(bad);
    assert.equal(r.status, 400, bad); assert.deepEqual(r.body, {state: 'invalid-id'}); assert.equal(r.cache, 'no-store');
    assert.ok(!r.text.includes('script') && !r.text.includes('passwd') && !r.text.includes('T1:'), 'não ecoa a entrada');
    assert.equal(calls.length, 0, 'ID inválido não chega à fonte');
  }
  // sem variável de ambiente: estado honesto, sem registro e sem consulta
  delete process.env.TRADERNOVA_SIGNAL_SOURCE_URL; reset();
  let r = await call(id);
  assert.equal(r.status, 503); assert.deepEqual(r.body, {state: 'source-unavailable', reason: 'not-configured'}); assert.equal(r.cache, 'no-store'); assert.equal(calls.length, 0);
  for (const junk of ['   ', 'ftp://127.0.0.1', 'não é url', 'javascript:alert(1)']) { process.env.TRADERNOVA_SIGNAL_SOURCE_URL = junk; r = await call(id); assert.equal(r.status, 503, junk); assert.equal(r.body.reason, 'not-configured'); }
  assert.equal(calls.length, 0);
  // fonte configurada
  process.env.TRADERNOVA_SIGNAL_SOURCE_URL = `${BASE}/`;
  handler = async () => reply(404, {error: 'not-found'}); reset();
  r = await call(id);
  assert.equal(r.status, 404); assert.deepEqual(r.body, {state: 'not-found'}); assert.equal('record' in r.body, false);
  assert.equal(calls.length, 1); assert.equal(calls[0].url, `${BASE}/signals/${id}`); assert.equal(calls[0].init.redirect, 'manual'); assert.ok(calls[0].init.signal instanceof AbortSignal);
  const active = makeRecord();
  handler = async () => reply(200, active);
  r = await call(active.publicId);
  assert.equal(r.status, 200); assert.equal(r.body.state, 'active'); assert.deepEqual(r.body.record, active); assert.equal(r.cache, 'no-store');
  r = await call(active.publicId.toUpperCase()); assert.equal(r.body.state, 'active', 'UUID em maiúsculas');
  const expired = makeRecord({generatedAt: now - 120000, expiresAt: now - 60000});
  handler = async () => reply(200, expired); r = await call(expired.publicId);
  assert.equal(r.status, 200); assert.equal(r.body.state, 'expired'); assert.equal(r.body.record.publicId, expired.publicId);
  const invalidated = makeRecord({invalidatedAt: now - 500, invalidationReason: 'Fonte atrasada.'});
  handler = async () => reply(200, invalidated); r = await call(invalidated.publicId);
  assert.equal(r.body.state, 'invalidated'); assert.equal(r.body.record.invalidationReason, 'Fonte atrasada.');
  // a fonte devolveu OUTRO sinal para este ID: não passa adiante
  handler = async () => reply(200, makeRecord()); r = await call(id);
  assert.equal(r.status, 404); assert.deepEqual(r.body, {state: 'not-found'});
  // registros malformados: tratados como erro da fonte, nunca repassados
  const malformed = [{...active, stop: 105}, {...active, mode: 'demo'}, {...active, publicId: 'T1:T1-E0X0:1'}, {...active, expiresAt: active.generatedAt}, Object.fromEntries(Object.entries(active).filter(([k]) => k !== 'evidence')), {}, [], null, 'texto'];
  for (const bad of malformed) {
    handler = async () => reply(200, bad); r = await call(active.publicId);
    assert.equal(r.status, 503); assert.deepEqual(r.body, {state: 'source-unavailable', reason: 'invalid-response'}); assert.equal('record' in r.body, false);
  }
  handler = async () => reply(200, '{truncado'); r = await call(active.publicId); assert.equal(r.body.reason, 'invalid-response');
  handler = async () => reply(200, 'x'.repeat(70000)); r = await call(active.publicId); assert.equal(r.body.reason, 'invalid-response', 'corpo grande demais');
  // fonte fora do ar
  handler = async () => reply(500, {error: 'read-failed'}); r = await call(active.publicId); assert.deepEqual(r.body, {state: 'source-unavailable', reason: 'unreachable'}); assert.equal(r.status, 503);
  handler = async () => reply(400, {error: 'invalid-id'}); r = await call(active.publicId); assert.equal(r.body.state, 'source-unavailable');
  handler = async () => reply(302, ''); r = await call(active.publicId); assert.equal(r.body.state, 'source-unavailable', 'redirecionamento não é seguido');
  handler = async () => { throw new TypeError('fetch failed'); }; r = await call(active.publicId); assert.deepEqual(r.body, {state: 'source-unavailable', reason: 'unreachable'});
  // tempo esgotado (limite curto no adaptador; a rota usa 3 s)
  const hanging = (url, init) => new Promise((_, reject) => { const keep = setTimeout(() => {}, 5000); init.signal.addEventListener('abort', () => { clearTimeout(keep); reject(new DOMException('timeout', 'TimeoutError')); }); }); // o timer de AbortSignal.timeout não segura o processo
  const slow = await lookupSignal(active.publicId, workerHttpSource(BASE, hanging, 30), now);
  assert.deepEqual(slow, {status: 503, body: {state: 'source-unavailable', reason: 'unreachable'}});
  // autorização: ponto de encaixe; hoje 'unauthorized' nunca sai da rota, mas o gancho funciona e não consulta a fonte
  reset(); handler = async () => reply(200, active);
  const denied = await lookupSignal(active.publicId, signalSourceFromEnv({TRADERNOVA_SIGNAL_SOURCE_URL: BASE}, globalThis.fetch), now, () => false);
  assert.deepEqual(denied, {status: 401, body: {state: 'unauthorized'}}); assert.equal(calls.length, 0);
  assert.equal(signalSourceFromEnv({}, globalThis.fetch), null);
  // nenhuma resposta de erro/ausência jamais traz um registro
  for (const impl of [async () => reply(404, {}), async () => reply(500, {}), async () => { throw new Error('x'); }, async () => reply(200, {lixo: true})]) {
    handler = impl; r = await call(newPublicSignalId()); assert.equal('record' in r.body, false); assert.notEqual(r.body.state, 'active');
  }
} finally { globalThis.fetch = realFetch; delete process.env.TRADERNOVA_SIGNAL_SOURCE_URL; }

// ---- 2. Modelo da ficha (sem React) ----
{
  const active = makeRecord(), test = toSheetModel({state: 'active', record: active}, now);
  assert.equal(test.kind, 'signal'); assert.equal(test.status, 'active'); assert.equal(test.modeLabel, 'Teste'); assert.equal(test.directionLabel, 'Compra'); assert.equal(test.timeframeLabel, 'H1'); assert.equal(test.sourceLabel, 'Kraken Spot');
  assert.equal(test.remainingSeconds, 60);
  assert.equal(toSheetModel({state: 'active', record: makeRecord({mode: 'research'})}, now).modeLabel, 'Pesquisa');
  assert.equal(toSheetModel({state: 'active', record: active}, active.expiresAt).status, 'expired', 'vira expirado pelo relógio local');
  assert.equal(toSheetModel({state: 'expired', record: active}, now).status, 'expired');
  const inv = toSheetModel({state: 'invalidated', record: makeRecord({invalidatedAt: now, invalidationReason: 'Motivo X.'})}, now);
  assert.equal(inv.status, 'invalidated'); assert.equal(inv.invalidationReason, 'Motivo X.');
  assert.deepEqual(toSheetModel(null, now), {kind: 'loading'});
  assert.equal(toSheetModel({state: 'not-found'}, now).text, 'Sinal não encontrado. Nenhum sinal foi criado no lugar.');
  assert.equal(toSheetModel({state: 'source-unavailable', reason: 'not-configured'}, now).text, 'A fonte de sinais não está conectada neste ambiente.');
  assert.equal(toSheetModel({state: 'source-unavailable', reason: 'unreachable'}, now).retry, true);
  assert.equal(toSheetModel({state: 'invalid-id'}, now).kind, 'message');
  for (const state of ['not-found', 'invalid-id', 'unauthorized']) assert.equal(toSheetModel({state}, now).kind, 'message', 'sem registro nunca vira ficha');
  // respostas inesperadas do servidor: nunca viram sinal
  assert.deepEqual(parseSignalResponse({state: 'active'}), {state: 'source-unavailable', reason: 'invalid-response'});
  assert.deepEqual(parseSignalResponse({state: 'active', record: {...active, stop: 105}}), {state: 'source-unavailable', reason: 'invalid-response'});
  assert.deepEqual(parseSignalResponse({state: 'demo', record: active}), {state: 'source-unavailable', reason: 'invalid-response'});
  assert.deepEqual(parseSignalResponse('x'), {state: 'source-unavailable', reason: 'invalid-response'});
  assert.equal(parseSignalResponse({state: 'active', record: active}).state, 'active');
  // cliente: ID inválido nem sai do navegador; falha de rede vira "fonte indisponível"
  let fetched = 0;
  assert.deepEqual(await fetchSignal('T1:abc', undefined, async () => { fetched++; }), {state: 'invalid-id'}); assert.equal(fetched, 0);
  const okId = newPublicSignalId();
  assert.deepEqual(await fetchSignal(okId, undefined, async () => { throw new TypeError('offline'); }), {state: 'source-unavailable', reason: 'unreachable'});
  assert.deepEqual(await fetchSignal(okId, undefined, async (url) => { assert.equal(url, `/api/signals/${okId}`); return {json: async () => ({state: 'not-found'})}; }), {state: 'not-found'});
  assert.deepEqual(await fetchSignal(okId, undefined, async () => ({json: async () => { throw new SyntaxError('html'); }})), {state: 'source-unavailable', reason: 'unreachable'});
}

// ---- 3. Servidor de leitura do worker ----
const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'tradernova-signal-http-'));
try {
  const dir = path.join(tmp, 'signals'), file = path.join(dir, 'kraken-spot_BTCUSD_60m.jsonl');
  const store = await openFileSignalStore(file);
  const first = makeRecord(); await store.insertIfAbsent(first);
  const reader = await startSignalReadServer({signalsDir: dir, port: 0});
  try {
    assert.equal(reader.server.address().address, '127.0.0.1', 'preso ao loopback');
    const url = (p) => `http://127.0.0.1:${reader.port}${p}`;
    let res = await fetch(url(`/signals/${first.publicId}`));
    assert.equal(res.status, 200); assert.deepEqual(await res.json(), first);
    assert.match(res.headers.get('content-type'), /application\/json/); assert.equal(res.headers.get('cache-control'), 'no-store');
    assert.equal(res.headers.get('access-control-allow-origin'), null, 'sem CORS');
    // leitura fresca: registro gravado DEPOIS de o servidor subir aparece na hora, inclusive por outro processo (anexo direto ao arquivo)
    const second = makeRecord(); await store.insertIfAbsent(second);
    res = await fetch(url(`/signals/${second.publicId}`)); assert.equal(res.status, 200); assert.equal((await res.json()).publicId, second.publicId);
    const third = makeRecord(); await fs.appendFile(file, `${JSON.stringify(third)}\n{linha truncada`);
    res = await fetch(url(`/signals/${third.publicId}`)); assert.equal(res.status, 200, 'linha final truncada é ignorada');
    res = await fetch(url(`/signals/${first.publicId.toUpperCase()}`)); assert.equal(res.status, 200);
    // arquivos de outros pares no mesmo diretório também são lidos
    const other = makeRecord({instrument: 'ETHUSD'}); await fs.writeFile(path.join(dir, 'kraken-spot_ETHUSD_60m.jsonl'), `${JSON.stringify(other)}\n`);
    res = await fetch(url(`/signals/${other.publicId}`)); assert.equal(res.status, 200);
    // desconhecido e inválido
    res = await fetch(url(`/signals/${newPublicSignalId()}`)); assert.equal(res.status, 404); assert.deepEqual(await res.json(), {error: 'not-found'});
    for (const bad of ['T1:abc', 'test-123', encodeURIComponent('T1:T1-E0X0:1789948800000'), '%E0%A4%A', 'a'.repeat(3000), '..%2F..%2Fetc']) {
      res = await fetch(url(`/signals/${bad}`)); assert.equal(res.status, 400, bad); assert.deepEqual(await res.json(), {error: 'invalid-id'});
    }
    for (const p of ['/', '/signals', '/signals/', `/signals/${first.publicId}/x`, '/candles']) assert.equal((await fetch(url(p))).status, 404, p);
    for (const method of ['POST', 'PUT', 'DELETE', 'PATCH']) { res = await fetch(url(`/signals/${first.publicId}`), {method, body: method === 'DELETE' ? undefined : '{}'}); assert.equal(res.status, 405, method); }
    // Host estranho (DNS rebinding) é recusado
    const status = await new Promise((resolve, reject) => http.get({host: '127.0.0.1', port: reader.port, path: `/signals/${first.publicId}`, headers: {Host: 'evil.example'}}, (r) => { r.resume(); resolve(r.statusCode); }).on('error', reject));
    assert.equal(status, 403);
    // adaptador ponta a ponta: rota -> worker HTTP real
    const e2e = await lookupSignal(second.publicId, workerHttpSource(`http://127.0.0.1:${reader.port}`, (u, init) => fetch(u, init)), now);
    assert.equal(e2e.status, 200); assert.equal(e2e.body.state, 'active'); assert.equal(e2e.body.record.publicId, second.publicId);
    const unknown = await lookupSignal(newPublicSignalId(), workerHttpSource(`http://127.0.0.1:${reader.port}`, (u, init) => fetch(u, init)), now);
    assert.deepEqual(unknown, {status: 404, body: {state: 'not-found'}});
  } finally { await reader.close(); }
  // diretório de sinais inexistente: 404, não erro
  const empty = await startSignalReadServer({signalsDir: path.join(tmp, 'nada'), port: 0});
  try { assert.equal((await fetch(`http://127.0.0.1:${empty.port}/signals/${newPublicSignalId()}`)).status, 404); } finally { await empty.close(); }
  // porta ocupada rejeita com clareza
  const a = await startSignalReadServer({signalsDir: dir, port: 0});
  try { await assert.rejects(startSignalReadServer({signalsDir: dir, port: a.port}), /EADDRINUSE/); } finally { await a.close(); }
  // configuração: porta padrão 8790, ajustável, desligável, validada
  assert.equal(parseConfig([], {}).httpPort, 8790);
  assert.equal(parseConfig(['--http-port', '9001'], {TRADERNOVA_WORKER_HTTP_PORT: '9000'}).httpPort, 9001);
  assert.equal(parseConfig([], {TRADERNOVA_WORKER_HTTP_PORT: '9000'}).httpPort, 9000);
  assert.equal(parseConfig(['--no-http'], {}).httpPort, null);
  for (const bad of ['0', '70000', 'abc', '80.5']) assert.throws(() => parseConfig(['--http-port', bad], {}), /porta HTTP/);
} finally { await fs.rm(tmp, {recursive: true, force: true}); }

// ---- 4. Regressão: o ID do motor passa nos links do mobile e na API; a chave de deduplicação fica separada ----
const m = await loadResearchModules();
try {
  const p = m.paper, start = Date.UTC(2025, 0, 1), step = 3600000, closedAt = start + 221 * step, at = closedAt + 5000;
  const snapshot = {status: 'ready', reason: 'fixture', source: 'kraken-spot', evaluatedAt: at, closedAt, readings: [{candidateId: 'T3', state: 'buy', signalTime: closedAt - step, entryReference: 108, stop: 100, target: 124, evidence: ['controlled test']}]};
  const quote = {bid: 109, ask: 109.1, timestamp: at}, presetId = p.newPaperSession('T3', closedAt - 10000).presetId;
  const approval = {candidateId: 'T3', presetId, assetId: 'BTCUSD', source: 'kraken-spot', interval: 60, status: 'validated', forwardPassed: true, approvedAt: at - 1, expiresAt: at + 1000};
  const opp = p.manualOpportunity(snapshot, 'T3', quote, at, [approval]), again = p.manualOpportunity(snapshot, 'T3', quote, at, [approval]);
  assert.ok(opp && again);
  assert.ok(isPublicSignalId(opp.publicId), 'a API aceita o ID do motor');
  assert.equal('id' in opp, false, 'o campo id antigo (com ":") não existe mais');
  const site = await import(`data:text/javascript;base64,${Buffer.from(ts.transpileModule(await fs.readFile(new URL('../mobile/src/site.ts', import.meta.url), 'utf8'), {compilerOptions: {target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022}}).outputText).toString('base64')}`);
  assert.equal(site.signalLink(`tradernova://signal/${opp.publicId}`), `${site.SITE_URL}?aba=robo&sinal=${opp.publicId}`, 'o deep link do mobile aceita o ID do motor');
  assert.equal(site.signalLink(`tradernova://signal/${opp.dedupKey}`), null, 'a chave de deduplicação nunca serve de link');
  assert.equal(site.signalLink('tradernova://signal/T3:T3-E0X0:1789948800000'), null);
  assert.equal(opp.dedupKey, `T3@${presetId}|kraken-spot|BTCUSD|60|buy|${closedAt}`);
  assert.equal(opp.dedupKey, again.dedupKey, 'mesma oportunidade, mesma chave');
  assert.notEqual(opp.publicId, again.publicId, 'cada chamada gera um ID público novo e opaco');
  assert.ok(!opp.publicId.includes(String(closedAt)) && !opp.publicId.includes('T3') && !opp.publicId.includes(opp.dedupKey), 'o ID público não carrega a chave');
  assert.equal(isPublicSignalId(opp.dedupKey), false);
} finally { await m.cleanup(); }
console.log('Signal route checks passed: id validation, explicit source adapter, honest unavailable state, malformed records rejected, sheet model, loopback read server, engine id regression.');
