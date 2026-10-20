// Testes offline das notificações push (Fase 4): elegibilidade, payload, dedup, expiração, preferências, envio simulado e central de alertas.
// Os registros aqui são FIXTURES de teste, não sinais reais. Nenhuma requisição sai da máquina.
import assert from 'node:assert/strict';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import '../worker/register.mjs';
const imp = (rel) => import(pathToFileURL(path.resolve(new URL(rel, import.meta.url).pathname)).href);
const p = await imp('../lib/tradernova/push-notifications.ts');
const {newPublicSignalId, signalDedupKey} = await imp('../lib/tradernova/signal-record.ts');

const now = Date.UTC(2026, 9, 20, 12, 0, 0);
const makeRecord = (over = {}) => {
  const parts = {strategyId: 'T1', strategyVersion: 'E0X0', provider: 'kraken-spot', instrument: 'BTCUSD', timeframeMinutes: 60, side: 'buy', signalTime: now - 3600000};
  return {publicId: newPublicSignalId(), dedupKey: signalDedupKey(parts), ...parts, generatedAt: now - 1000, expiresAt: now + 30 * 60000, entryReference: 67420.5, stop: 66900, target: 68500, evidence: ['Evidência de teste.'], mode: 'research', invalidatedAt: null, invalidationReason: null, ...over};
};
const token = (n) => `ExponentPushToken[abcdefghij${n}]`;
const on = {enabled: true, includeResearch: true, mutedInstruments: [], mutedStrategies: []};
// Os testes de envio de pesquisa ligam a política explicitamente; o padrão do servidor é não enviar pesquisa (seção 0).
const R = {allowResearch: true};

// ---- 0. Padrão do servidor: sinal de pesquisa nunca vira entrega (sem estratégia aprovada, nada sai) ----
{
  const research = makeRecord();
  assert.deepEqual(p.defaultPushPolicy, {allowResearch: false});
  assert.deepEqual(p.notificationEligibility(research, on, now), {send: false, reason: 'research-off'});
  const store0 = p.createMemoryPushDeliveryStore();
  let calls0 = 0;
  const r0 = await p.dispatchPush({signals: [research, makeRecord({instrument: 'ETHUSD', entryReference: 2600, stop: 2550, target: 2700})], devices: [{id: 'd1', userId: 'u1', platform: 'android', token: token(1), enabled: true}], preferences: new Map([['u1', on]]), now, store: store0, send: async (m) => { calls0++; return m.map(() => ({status: 'ok', id: 't'})); }});
  assert.equal(r0.sent, 0);
  assert.equal(calls0, 0, 'nada chega ao serviço de push');
  assert.equal(store0.rows.size, 0, 'nenhuma entrega registrada');
  assert.deepEqual(r0.skipped.map((x) => x.reason), ['research-off', 'research-off']);
  assert.deepEqual(p.notificationEligibility(makeRecord({mode: 'alert'}), on, now), {send: false, reason: 'unapproved-alert'}, 'alert sem aprovação também não sai');
}

// ---- 1. Tokens e deep link ----
assert.equal(p.isExpoPushToken(token(1)), true);
assert.equal(p.isExpoPushToken('ExpoPushToken[xxxxxxxxxxxx]'), true);
for (const bad of ['', 'ExponentPushToken[]', 'ExponentPushToken[abc]', 'fcm:abcdefghijkl', `ExponentPushToken[${'a'.repeat(300)}]`, 'ExponentPushToken[abcdefghijk] ', 42, null]) assert.equal(p.isExpoPushToken(bad), false, String(bad));
const id = newPublicSignalId();
assert.equal(p.signalDeepLink(id.toUpperCase()), `tradernova://signal/${id}`);

// ---- 2. Preferências: opt-in por padrão desligado, leitura defensiva ----
assert.deepEqual(p.readNotificationPreferences(undefined), {enabled: false, includeResearch: false, mutedInstruments: [], mutedStrategies: []});
assert.deepEqual(p.readNotificationPreferences({...on, mutedInstruments: ['DOGEUSD']}), p.readNotificationPreferences(null), 'ativo fora do catálogo invalida');
assert.deepEqual(p.readNotificationPreferences({...on, mutedInstruments: ['BTCUSD', 'BTCUSD']}).mutedInstruments, ['BTCUSD']);
let prefs = p.setInstrumentMuted(on, 'XAUUSD', true);
assert.deepEqual(prefs.mutedInstruments, ['XAUUSD']);
assert.deepEqual(p.setInstrumentMuted(prefs, 'XAUUSD', false).mutedInstruments, []);
prefs = p.setStrategyMuted(on, 'T2', true);
assert.deepEqual(prefs.mutedStrategies, ['T2']);
assert.deepEqual(p.setStrategyMuted(p.setStrategyMuted(prefs, 'T2', true), 'T2', false).mutedStrategies, []);
assert.deepEqual(on.mutedInstruments, [], 'não altera o objeto original');

// ---- 3. Elegibilidade ----
const el = (over, pr = on, t = now, approvals, policy = R) => p.notificationEligibility(makeRecord(over), pr, t, approvals, policy);
assert.deepEqual(el({}), {send: true, label: 'research'});
assert.deepEqual(el({invalidatedAt: now - 10, invalidationReason: 'Fonte atrasada.'}), {send: false, reason: 'invalidated'});
assert.deepEqual(el({expiresAt: now}), {send: false, reason: 'expired'});
assert.deepEqual(el({expiresAt: now + p.minLeadMs - 1}), {send: false, reason: 'expired'}, 'perto de vencer não sai');
assert.deepEqual(el({mode: 'test'}), {send: false, reason: 'test'});
assert.deepEqual(el({publicId: 'T1:T1-E0X0:1'}), {send: false, reason: 'invalid-id'});
assert.deepEqual(el({}, p.defaultNotificationPreferences), {send: false, reason: 'disabled'});
assert.deepEqual(el({}, {...on, includeResearch: false}), {send: false, reason: 'research-opt-out'});
assert.deepEqual(el({}, {...on, mutedInstruments: ['BTCUSD']}), {send: false, reason: 'muted-instrument'});
assert.deepEqual(el({}, {...on, mutedStrategies: ['T1']}), {send: false, reason: 'muted-strategy'});
// Modo alert: o registro de aprovação começa vazio; sem aprovação vigente não sai nem vira pesquisa.
assert.deepEqual(p.alertApprovals, []);
assert.deepEqual(el({mode: 'alert'}), {send: false, reason: 'unapproved-alert'});
const approval = {strategyId: 'T1', strategyVersion: 'E0X0', approvedAt: now - 1, expiresAt: now + 86400000};
assert.deepEqual(el({mode: 'alert'}, on, now, [approval]), {send: true, label: 'alert'});
assert.deepEqual(el({mode: 'alert'}, {...on, includeResearch: false}, now, [approval]), {send: true, label: 'alert'}, 'alerta aprovado não depende do opt-in de pesquisa');
assert.deepEqual(el({mode: 'alert', strategyVersion: 'E0X1'}, on, now, [approval]), {send: false, reason: 'unapproved-alert'}, 'outra versão');
assert.deepEqual(el({mode: 'alert'}, on, now, [{...approval, expiresAt: now}]), {send: false, reason: 'unapproved-alert'}, 'aprovação vencida');
assert.deepEqual(el({mode: 'alert'}, on, now, [{...approval, approvedAt: now + 1}]), {send: false, reason: 'unapproved-alert'}, 'aprovação futura');

// ---- 4. Payload ----
const rec = makeRecord();
const msg = p.buildPushMessage(rec, token(1), 'research', now);
assert.equal(msg.to, token(1));
assert.equal(msg.title, 'Pesquisa · BTCUSD compra');
assert.match(msg.body, /^Sinal de pesquisa, não é recomendação\. /);
assert.match(msg.body, /Ref\. 67\.420,50 · stop 66\.900,00 · alvo 68\.500,00/);
assert.match(msg.body, /Válido até 09:30\./, 'horário de Brasília');
assert.deepEqual(msg.data, {url: `tradernova://signal/${rec.publicId}`, signalId: rec.publicId, label: 'research'});
assert.equal(msg.ttl, 1800);
assert.equal(msg.expiration, Math.floor(rec.expiresAt / 1000));
assert.equal(msg.channelId, 'sinais');
assert.ok(!JSON.stringify(msg).includes(rec.dedupKey), 'dedupKey nunca vai para o aparelho');
const sell = p.buildPushMessage(makeRecord({instrument: 'EURUSD', side: 'sell', entryReference: 1.08215, stop: 1.0835, target: null}), token(1), 'alert', now);
assert.equal(sell.title, 'Alerta · EURUSD venda');
assert.match(sell.body, /^Estratégia aprovada, confira antes de agir\. Ref\. 1,08215 · stop 1,08350\. /);
assert.equal(p.formatSignalPrice(12.5, 'XYZ'), '12,5');
assert.ok(msg.body.length < 180, 'cabe na notificação');

// ---- 5. Planejamento: dedup, plataforma, token inválido, preferências por usuário ----
const devices = [
  {id: 'd1', userId: 'u1', platform: 'android', token: token(1), enabled: true},
  {id: 'd2', userId: 'u1', platform: 'ios', token: token(2), enabled: true},
  {id: 'd3', userId: 'u2', platform: 'android', token: token(3), enabled: true},
  {id: 'd4', userId: 'u3', platform: 'android', token: 'quebrado', enabled: true},
  {id: 'd5', userId: 'u1', platform: 'android', token: token(5), enabled: false},
  {id: 'd6', userId: 'u1', platform: 'web', token: token(6), enabled: true},
];
const preferences = new Map([['u1', on], ['u2', {...on, mutedInstruments: ['BTCUSD']}], ['u3', on]]);
const a = makeRecord(), b = makeRecord({instrument: 'XAUUSD', entryReference: 4000, stop: 3990, target: 4020});
const plan = p.planPushDispatch({signals: [a, a, b], devices, preferences, delivered: new Set([p.deliveryKey(b.publicId, 'd2')]), now, policy: R});
assert.deepEqual(plan.planned.map((x) => `${x.signalId === a.publicId ? 'a' : 'b'}:${x.deviceId}`), ['a:d1', 'a:d2', 'b:d1', 'b:d3']);
const reasons = plan.skipped.map((x) => `${x.signalId === a.publicId ? 'a' : 'b'}:${x.deviceId}:${x.reason}`);
assert.deepEqual(reasons, ['a:d3:muted-instrument', 'a:d4:invalid-token', 'a:d6:platform', 'b:d2:already-delivered', 'b:d4:invalid-token', 'b:d6:platform']);
const nobody = p.planPushDispatch({signals: [a], devices: [{id: 'd9', userId: 'sem-prefs', platform: 'android', token: token(9), enabled: true}], preferences: new Map(), delivered: new Set(), now, policy: R});
assert.deepEqual(nobody.skipped.map((x) => x.reason), ['disabled'], 'sem preferência salva = desligado');

// ---- 6. Envio: claim único, falhas, DeviceNotRegistered, lotes de 100 ----
const store = p.createMemoryPushDeliveryStore();
const sentBatches = [];
const send = async (messages) => { sentBatches.push(messages); return messages.map((m) => (m.to === token(2) ? {status: 'error', message: 'gone', details: {error: 'DeviceNotRegistered'}} : {status: 'ok', id: `ticket-${m.to}`})); };
const r1 = await p.dispatchPush({signals: [a], devices, preferences, now, policy: R, store, send});
assert.equal(r1.sent, 1);
assert.equal(r1.failed, 1);
assert.deepEqual(r1.disabledDevices, ['d2']);
assert.equal(store.disabled.get('d2'), 'DeviceNotRegistered');
assert.deepEqual(store.rows.get(p.deliveryKey(a.publicId, 'd1')), {status: 'sent', ticketId: `ticket-${token(1)}`});
assert.deepEqual(store.rows.get(p.deliveryKey(a.publicId, 'd2')), {status: 'failed', error: 'DeviceNotRegistered'});
// Rodar de novo (worker reiniciado, sinal relido) não envia nada.
const r2 = await p.dispatchPush({signals: [a], devices, preferences, now, policy: R, store, send});
assert.equal(r2.sent + r2.failed, 0);
assert.equal(sentBatches.length, 1);
assert.ok(r2.skipped.filter((x) => x.reason === 'already-delivered').length === 2);
// Dois workers ao mesmo tempo: o claim atômico garante uma só entrega.
const shared = p.createMemoryPushDeliveryStore(), raced = [];
const raceSend = async (messages) => { raced.push(...messages); return messages.map(() => ({status: 'ok', id: 't'})); };
const c = makeRecord();
await Promise.all([1, 2].map(() => p.dispatchPush({signals: [c], devices: [devices[0]], preferences, now, policy: R, store: shared, send: raceSend})));
assert.equal(raced.length, 1, 'sem duplicata em corrida');
// Serviço fora do ar: marca falha, não reenvia sozinho (no máximo uma vez).
const down = p.createMemoryPushDeliveryStore();
const r3 = await p.dispatchPush({signals: [makeRecord()], devices: [devices[0]], preferences, now, policy: R, store: down, send: async () => { throw new Error('offline'); }});
assert.equal(r3.failed, 1);
assert.equal([...down.rows.values()][0].error, 'unreachable');
// Resposta com número errado de tickets também é falha.
const r4 = await p.dispatchPush({signals: [makeRecord()], devices: [devices[0]], preferences, now, policy: R, store: p.createMemoryPushDeliveryStore(), send: async () => []});
assert.equal(r4.failed, 1);
// Sinal expirado nunca é enviado.
const r5 = await p.dispatchPush({signals: [makeRecord({expiresAt: now - 1, generatedAt: now - 2000})], devices: [devices[0]], preferences, now, policy: R, store: p.createMemoryPushDeliveryStore(), send});
assert.equal(r5.sent, 0);
assert.equal(r5.skipped[0].reason, 'expired');
// Lotes de no máximo 100 mensagens (limite do serviço Expo).
const many = Array.from({length: 230}, (_, i) => ({id: `m${i}`, userId: 'u1', platform: 'android', token: token(`m${i}`), enabled: true}));
const sizes = [];
const r6 = await p.dispatchPush({signals: [makeRecord()], devices: many, preferences, now, policy: R, store: p.createMemoryPushDeliveryStore(), send: async (m) => { sizes.push(m.length); return m.map(() => ({status: 'ok', id: 't'})); }});
assert.deepEqual(sizes, [100, 100, 30]);
assert.equal(r6.sent, 230);

// ---- 7. Cliente Expo com fetch simulado ----
const calls = [];
const reply = (status, body) => ({ok: status >= 200 && status < 300, status, text: async () => (typeof body === 'string' ? body : JSON.stringify(body))});
const sender = p.createExpoPushSender({fetch: async (url, init) => { calls.push({url, init}); return reply(200, {data: [{status: 'ok', id: 'abc'}]}); }});
assert.deepEqual(await sender([msg]), [{status: 'ok', id: 'abc'}]);
assert.equal(calls[0].url, 'https://exp.host/--/api/v2/push/send');
assert.equal(calls[0].init.method, 'POST');
assert.equal(calls[0].init.headers.Authorization, undefined, 'sem token de acesso por padrão');
assert.deepEqual(JSON.parse(calls[0].init.body), [msg]);
const authed = p.createExpoPushSender({accessToken: 'segredo', fetch: async (url, init) => { calls.push({url, init}); return reply(200, {data: [{status: 'ok', id: 'x'}]}); }});
await authed([msg]);
assert.equal(calls[1].init.headers.Authorization, 'Bearer segredo');
await assert.rejects(p.createExpoPushSender({fetch: async () => reply(500, 'erro')})([msg]), /HTTP 500/);
await assert.rejects(p.createExpoPushSender({fetch: async () => reply(200, {data: []})})([msg]), /inválida/);
await assert.rejects(p.createExpoPushSender({fetch: async () => reply(200, {data: [{status: 'talvez'}]})})([msg]), /inválida/);
await assert.rejects(sender(Array(101).fill(msg)), /100/);

// ---- 8. Central de alertas ----
const active = makeRecord({generatedAt: now - 1000});
const expired = makeRecord({generatedAt: now - 7200000, expiresAt: now - 3600000});
const invalidated = makeRecord({generatedAt: now - 5000, invalidatedAt: now - 100, invalidationReason: 'Fonte atrasada.'});
const items = p.alertCenterItems([expired, invalidated, active, active], now);
assert.deepEqual(items.map((i) => i.state), ['active', 'invalidated', 'expired']);
assert.equal(items[0].url, `?aba=robo&sinal=${active.publicId}`);
assert.equal(items[0].strategy, 'T1 E0X0');
assert.equal(p.alertCenterItems([active, expired, invalidated], now, 2).length, 2);
assert.deepEqual(p.alertCenterItems([makeRecord({publicId: 'nao-uuid'})], now), []);

// ---- 9. Adaptador Supabase (fetch simulado) ----
const sp = await imp('../lib/tradernova/supabase-push.ts');
const U = 'https://exemplo.supabase.co';
const uA = '00000000-0000-4000-8000-00000000000a', dA = '60000000-0000-4000-8000-00000000000a';
const sCalls = [];
const sFetch = async (url, init) => {
  sCalls.push({url, init});
  const u = new URL(url), table = u.pathname.split('/').pop();
  if (table === 'push_devices' && init.method === 'GET') return reply(200, [{id: dA.toUpperCase(), user_id: uA, platform: 'android', device_reference: token(1)}, {id: 'x', user_id: uA, platform: 'android', device_reference: token(2)}, {id: dA, user_id: uA, platform: 'web', device_reference: 'w'}]);
  if (table === 'notification_preferences') return reply(200, [{user_id: uA, enabled: true, include_research: true, muted_instruments: ['XAUUSD'], muted_strategies: []}]);
  if (table === 'push_deliveries' && init.method === 'GET') return reply(200, [{signal_public_id: a.publicId, device_id: dA}]);
  if (table === 'push_deliveries' && init.method === 'POST') return reply(201, JSON.parse(init.body)[0].signal_public_id === a.publicId ? [] : [{signal_public_id: 'ok'}]);
  if (init.method === 'PATCH') return reply(204, '');
  return reply(404, '');
};
const cfg = {url: U, key: 'service-key', fetch: sFetch};
const targets = await sp.loadPushTargets(cfg);
assert.deepEqual(targets.devices, [{id: dA, userId: uA, platform: 'android', token: token(1), enabled: true}], 'descarta linhas fora do formato');
assert.deepEqual(targets.preferences.get(uA), {enabled: true, includeResearch: true, mutedInstruments: ['XAUUSD'], mutedStrategies: []});
assert.match(sCalls[0].url, /push_devices\?enabled=is\.true&platform=in\.\(android,ios\)/);
assert.equal(sCalls[0].init.headers.Authorization, 'Bearer service-key');
const sStore = sp.supabasePushDeliveryStore(cfg);
assert.deepEqual([...await sStore.delivered([a.publicId, 'nao-uuid'])], [p.deliveryKey(a.publicId, dA)]);
assert.equal(await sStore.claim(a.publicId, dA), false, 'conflito = já reivindicado');
assert.equal(await sStore.claim(b.publicId, dA), true);
const claimCall = sCalls.findLast((c) => c.init.method === 'POST');
assert.match(claimCall.url, /on_conflict=signal_public_id,device_id/);
assert.match(claimCall.init.headers.Prefer, /ignore-duplicates/);
await sStore.finish(b.publicId, dA, {status: 'sent', ticketId: 't1'});
const fin = sCalls.at(-1);
assert.equal(fin.init.method, 'PATCH');
assert.deepEqual({...JSON.parse(fin.init.body), updated_at: 0}, {status: 'sent', ticket_id: 't1', error: null, updated_at: 0});
await sStore.disableDevice(dA, 'DeviceNotRegistered');
assert.match(sCalls.at(-1).url, new RegExp(`push_devices\\?id=eq\\.${dA}$`));
assert.equal(JSON.parse(sCalls.at(-1).init.body).enabled, false);
// Fluxo completo com o adaptador: o sinal já entregue não sai; o novo sai uma vez.
const full = await p.dispatchPush({signals: [a, b], ...targets, now, policy: R, store: sStore, send: async (m) => m.map(() => ({status: 'ok', id: 'tk'}))});
assert.equal(full.sent, 0, 'b é XAUUSD (silenciado) e a já foi entregue');
assert.throws(() => sp.supabasePushClient({url: 'http://exemplo.com', key: 'k', fetch: sFetch}), /HTTPS/);
await assert.rejects(sp.supabasePushDeliveryStore({...cfg, fetch: async () => reply(500, 'x')}).claim(a.publicId, dA), /HTTP 500/);

console.log('Push checks passed: opt-in default off, research label, no alert without approval, dedup per signal and device, expiry, Expo payload and client, alert center.');
