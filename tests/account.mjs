// Testes offline da conta (Fase 2): chave publicável, rota de configuração, cliente Auth/PostgREST (fetch simulado), PKCE,
// mapeamento do diário e retorno do link mágico. Nenhuma chamada sai da máquina.
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import '../worker/register.mjs';
const imp = (rel) => import(pathToFileURL(path.resolve(new URL(rel, import.meta.url).pathname)).href);
const acc = await imp('../lib/tradernova/account.ts');
const {GET} = await imp('../app/api/auth/config/route.ts');

const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
const jwt = (payload) => `${b64({alg: 'HS256', typ: 'JWT'})}.${b64(payload)}.assinatura`;
const ANON = jwt({role: 'anon', iss: 'supabase'}), SERVICE = jwt({role: 'service_role', iss: 'supabase'});
const PUB = 'sb_publishable_abcdefghijklmnop', SECRET = 'sb_secret_abcdefghijklmnop';
const URL_ = 'https://exemplo.supabase.co';

// ---- 1. Só chave publicável ----
assert.equal(acc.isPublishableKey(PUB), true);
assert.equal(acc.isPublishableKey(ANON), true);
assert.equal(acc.isPublishableKey(SECRET), false, 'chave secreta recusada');
assert.equal(acc.isPublishableKey(SERVICE), false, 'service_role recusada');
assert.equal(acc.isPublishableKey('qualquer'), false);
assert.deepEqual(acc.authConfigFromEnv({TRADERNOVA_SUPABASE_URL: URL_, TRADERNOVA_SUPABASE_PUBLISHABLE_KEY: PUB}), {url: URL_, publishableKey: PUB});
assert.equal(acc.authConfigFromEnv({TRADERNOVA_SUPABASE_URL: URL_, TRADERNOVA_SUPABASE_PUBLISHABLE_KEY: SERVICE}), null);
assert.equal(acc.authConfigFromEnv({TRADERNOVA_SUPABASE_URL: 'http://exemplo.com', TRADERNOVA_SUPABASE_PUBLISHABLE_KEY: PUB}), null, 'http fora de localhost');
assert.equal(acc.authConfigFromEnv({TRADERNOVA_SUPABASE_URL: URL_}), null);
assert.equal(acc.parseAuthConfig({configured: true, url: URL_, publishableKey: SECRET}), null);
assert.equal(acc.parseAuthConfig({configured: false}), null);
assert.throws(() => acc.accountClient({url: URL_, publishableKey: SERVICE}, async () => {}), /publicável/);

// ---- 2. Rota /api/auth/config: nunca devolve chave de servidor ----
const saved = {...process.env};
const routeBody = async (env) => { for (const k of ['TRADERNOVA_SUPABASE_URL', 'TRADERNOVA_SUPABASE_PUBLISHABLE_KEY', 'TRADERNOVA_SUPABASE_SERVICE_KEY', 'TRADERNOVA_SUPABASE_READ_KEY']) delete process.env[k]; Object.assign(process.env, env); const r = await GET(); assert.equal(r.headers.get('cache-control'), 'no-store'); return r.json(); };
assert.deepEqual(await routeBody({}), {configured: false});
assert.deepEqual(await routeBody({TRADERNOVA_SUPABASE_URL: URL_, TRADERNOVA_SUPABASE_PUBLISHABLE_KEY: PUB}), {configured: true, url: URL_, publishableKey: PUB});
const leaked = JSON.stringify(await routeBody({TRADERNOVA_SUPABASE_URL: URL_, TRADERNOVA_SUPABASE_PUBLISHABLE_KEY: SECRET, TRADERNOVA_SUPABASE_SERVICE_KEY: SECRET, TRADERNOVA_SUPABASE_READ_KEY: SERVICE}));
assert.equal(leaked, '{"configured":false}', 'chave secreta por engano não sai na rota');
process.env = saved;

// ---- 3. PKCE ----
const {verifier, challenge} = await acc.createPkce();
assert.match(verifier, /^[A-Za-z0-9_-]{43,128}$/);
assert.equal(challenge, crypto.createHash('sha256').update(verifier).digest('base64url'));

// ---- 4. Cliente Auth/PostgREST ----
const reply = (status, body) => ({ok: status >= 200 && status < 300, status, text: async () => (body === undefined ? '' : typeof body === 'string' ? body : JSON.stringify(body))});
const fake = (handler) => { const calls = []; return {calls, fetch: async (url, init) => { calls.push({url, init, body: init.body ? JSON.parse(init.body) : undefined}); return handler(url, init); }}; };
const USER = '00000000-0000-4000-8000-0000000000aa';
const tokenReply = {access_token: 'token-de-acesso-1234', refresh_token: 'r1', expires_in: 3600, user: {id: USER, email: 'a@exemplo.com'}};
{
  const f = fake((url) => url.includes('/auth/v1/') ? reply(200, url.includes('/otp') ? {} : tokenReply) : reply(200, []));
  const c = acc.accountClient({url: URL_, publishableKey: PUB}, f.fetch);
  await c.requestEmailLink('a@exemplo.com', 'tradernova://auth', challenge);
  const otp = f.calls[0];
  assert.equal(otp.url, `${URL_}/auth/v1/otp?redirect_to=${encodeURIComponent('tradernova://auth')}`);
  assert.deepEqual(otp.body, {email: 'a@exemplo.com', create_user: true, code_challenge: challenge, code_challenge_method: 's256'});
  assert.equal(otp.init.headers.apikey, PUB);
  assert.equal(otp.init.redirect, 'manual');
  await assert.rejects(c.requestEmailLink('sem-arroba', 'x', challenge), (e) => e.reason === 'rejected');
  const s = await c.exchangeCode('codigo-1', verifier);
  assert.equal(f.calls.at(-1).url, `${URL_}/auth/v1/token?grant_type=pkce`);
  assert.deepEqual(f.calls.at(-1).body, {auth_code: 'codigo-1', code_verifier: verifier});
  assert.equal(s.user.id, USER); assert.equal(s.user.email, 'a@exemplo.com'); assert.ok(s.expiresAt > Date.now() + 3500000);
  const v = await c.verifyEmailCode('a@exemplo.com', '123456');
  assert.deepEqual(f.calls.at(-1).body, {type: 'email', email: 'a@exemplo.com', token: '123456'});
  assert.equal(v.accessToken, 'token-de-acesso-1234');
  await assert.rejects(c.verifyEmailCode('a@exemplo.com', '12'), (e) => e.reason === 'rejected');
  await c.refresh('r1');
  assert.deepEqual(f.calls.at(-1).body, {refresh_token: 'r1'});
  // Dados do usuário usam o token dele, nunca a chave como Bearer.
  await c.listJournal(s);
  const list = f.calls.at(-1);
  assert.equal(list.init.method, 'GET');
  assert.equal(list.init.headers.Authorization, 'Bearer token-de-acesso-1234');
  assert.match(list.url, /\/rest\/v1\/journal_entries\?select=.*order=decided_at\.desc/);
  await c.deleteAccount(s);
  assert.equal(f.calls.at(-1).url, `${URL_}/rest/v1/rpc/delete_my_account`);
  assert.equal(f.calls.at(-1).init.headers.Authorization, 'Bearer token-de-acesso-1234');
  await c.signOut(s);
  assert.equal(f.calls.at(-1).url, `${URL_}/auth/v1/logout`);
  assert.ok(f.calls.every((x) => !JSON.stringify(x).includes('sb_secret')), 'nenhuma chave secreta em chamada alguma');
}
{
  const statuses = [[401, 'session-expired'], [403, 'session-expired'], [429, 'rate-limited'], [500, 'unreachable'], [422, 'rejected']];
  for (const [status, reason] of statuses) {
    const c = acc.accountClient({url: URL_, publishableKey: PUB}, async () => reply(status, {msg: 'x'}));
    await assert.rejects(c.listJournal({accessToken: 'token-de-acesso-1234', refreshToken: 'r', expiresAt: 1, user: {id: USER, email: ''}}), (e) => e.reason === reason, `HTTP ${status}`);
  }
  const bad = acc.accountClient({url: URL_, publishableKey: PUB}, async () => reply(400, {error: 'invalid_grant'}));
  await assert.rejects(bad.refresh('r'), (e) => e.reason === 'session-expired', 'refresh recusado = sessão expirada');
  const down = acc.accountClient({url: URL_, publishableKey: PUB}, async () => { throw new Error('rede'); });
  await assert.rejects(down.requestEmailLink('a@exemplo.com', 'x', 'y'), (e) => e.reason === 'unreachable');
  const garbage = acc.accountClient({url: URL_, publishableKey: PUB}, async () => reply(200, '<html>'));
  await assert.rejects(garbage.exchangeCode('c', 'v'), (e) => e.reason === 'invalid-response');
  const noUser = acc.accountClient({url: URL_, publishableKey: PUB}, async () => reply(200, {access_token: 'token-de-acesso-1234', refresh_token: 'r', user: {id: 'nao-uuid'}}));
  await assert.rejects(noUser.exchangeCode('c', 'v'), (e) => e.reason === 'invalid-response');
}

// ---- 5. Diário: local -> linha -> local ----
const signal = {id: 'demo-1', assetId: 'BTCUSD', direction: 'Compra', createdAt: 1, expiresAt: 2, entry: 100, stop: 95, target: 110, demo: true, strategyId: 'S1'};
const entry = {id: crypto.randomUUID(), signal, decision: 'Revisado', createdAt: Date.parse('2026-10-20T00:00:00Z'), note: 'Observei o rompimento.'};
const row = await acc.journalToRow(entry, true);
assert.deepEqual(row, {client_id: entry.id, decision: 'reviewed', note: 'Observei o rompimento.', mode: 'demo', signal_snapshot: signal, decided_at: '2026-10-20T00:00:00.000Z', imported: true});
assert.deepEqual(acc.rowToJournal({id: crypto.randomUUID(), ...row}), entry, 'ida e volta preserva a entrada');
assert.equal((await acc.journalToRow({...entry, note: '  '}, false)).note, null);
const legacy = await acc.stableClientId('id-antigo');
assert.ok(acc.isUuid(legacy)); assert.equal(legacy, await acc.stableClientId('id-antigo'), 'ID antigo vira UUID estável');
assert.notEqual(legacy, await acc.stableClientId('outro'));
assert.equal(acc.rowToJournal({...row, signal_snapshot: {...signal, assetId: 'DOGEUSD'}}), null, 'ativo fora do catálogo ignorado');
assert.equal(acc.rowToJournal({...row, decision: 'manually_executed'}), null);
assert.equal(acc.rowToJournal({...row, signal_snapshot: null}), null);
await assert.rejects(acc.journalToRow({...entry, signal: {...signal, demo: false}}, false), 'só exemplos demo sobem');
{
  const f = fake(() => reply(201, [row]));
  const c = acc.accountClient({url: URL_, publishableKey: PUB}, f.fetch);
  const s = {accessToken: 'token-de-acesso-1234', refreshToken: 'r', expiresAt: Date.now() + 1e6, user: {id: USER, email: ''}};
  assert.equal(await c.saveJournal(s, [row]), 1);
  assert.equal(f.calls[0].url, `${URL_}/rest/v1/journal_entries?on_conflict=user_id,client_id`);
  assert.equal(f.calls[0].init.headers.Prefer, 'resolution=ignore-duplicates,return=representation');
  assert.equal(f.calls[0].body[0].user_id, undefined, 'o dono vem do token, não do cliente');
  assert.equal(await c.saveJournal(s, []), 0); assert.equal(f.calls.length, 1, 'lista vazia não chama o servidor');
  await c.savePreferences(s, {theme: 'essential', density: null, alertsInApp: false});
  assert.match(f.calls.at(-1).url, /user_preferences\?on_conflict=user_id$/);
  assert.equal(f.calls.at(-1).body.alerts_in_app, false);
}

// ---- 6. Retorno do link e destino do e-mail ----
assert.equal(acc.emailRedirectTarget('https://site.exemplo/?aba=diario#x', false), 'https://site.exemplo/?aba=conta');
assert.equal(acc.emailRedirectTarget('https://site.exemplo/', true), 'tradernova://auth');
assert.deepEqual(acc.readAuthReturn('https://site.exemplo/?aba=conta'), {code: null, error: null, clean: null});
assert.deepEqual(acc.readAuthReturn('https://site.exemplo/?aba=conta&code=abc-123'), {code: 'abc-123', error: null, clean: 'https://site.exemplo/?aba=conta'});
assert.deepEqual(acc.readAuthReturn('https://site.exemplo/?aba=conta#error=access_denied&error_description=Link+expirado'), {code: null, error: 'Link expirado', clean: 'https://site.exemplo/?aba=conta'});
assert.equal(acc.readAuthReturn('https://site.exemplo/?code=%3Cscript%3E').code, null, 'código fora do formato descartado');
assert.equal(acc.needsRefresh({expiresAt: Date.now() + 30000}, Date.now()), true);
assert.equal(acc.needsRefresh({expiresAt: Date.now() + 600000}, Date.now()), false);
console.log('Account checks passed: publishable key only, config route, PKCE, auth/PostgREST client, journal mapping, link return.');
