// Testa as migrações do Supabase (RLS, grants, checks) num Postgres descartável. Ver supabase/tests/rls.sql (issue #13).
// Precisa de psql e de TRADERNOVA_TEST_DATABASE_URL apontando para um Postgres onde o usuário pode criar bancos e papéis.
// Nunca aponte para o projeto Supabase real: o script cria e apaga um banco temporário.
import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
const url = process.env.TRADERNOVA_TEST_DATABASE_URL;
if (!url) { console.error('Defina TRADERNOVA_TEST_DATABASE_URL (Postgres local descartável) para rodar os testes de RLS.'); process.exit(2); }
if (/supabase\.(co|com)/.test(url)) { console.error('Recusado: TRADERNOVA_TEST_DATABASE_URL aponta para o Supabase. Use um Postgres local.'); process.exit(2); }
const psql = (target, args, label) => {
  const result = spawnSync('psql', [target, '-v', 'ON_ERROR_STOP=1', '-q', '-X', ...args], {encoding: 'utf8'});
  if (result.error) throw result.error;
  if (result.status !== 0) { process.stdout.write(result.stdout); process.stderr.write(result.stderr); console.error(`Falhou em: ${label}`); return false; }
  return result.stdout;
};
const db = `tradernova_rls_${process.pid}`;
const target = new URL(url); target.pathname = `/${db}`;
if (psql(url, ['-c', `create database ${db}`], 'criar banco') === false) process.exit(1);
let ok = true;
try {
  if (psql(target.href, ['-f', 'supabase/tests/auth-stub.sql'], 'auth-stub') === false) ok = false;
  // Migrações pelo mesmo script usado no projeto real; a segunda execução não pode ter nada pendente.
  const migrate = (args) => spawnSync(process.execPath, ['scripts/apply-migrations.mjs', ...args], {encoding: 'utf8', env: {...process.env, TRADERNOVA_MIGRATIONS_DATABASE_URL: target.href}});
  if (ok) {
    const first = migrate(['--apply']), second = migrate([]);
    if (first.status !== 0 || second.status !== 0 || !second.stdout.includes('Nenhuma migração pendente.')) {
      process.stdout.write(first.stdout + first.stderr + second.stdout + second.stderr); console.error('Falhou em: aplicar migrações'); ok = false;
    }
  }
  if (ok) {
    // helpers.sql primeiro; depois todo rls*.sql em ordem (cada fase acrescenta seu próprio arquivo).
    const tests = fs.readdirSync('supabase/tests').filter((f) => /^rls.*\.sql$/.test(f)).sort().map((f) => `supabase/tests/${f}`);
    for (const file of ['supabase/tests/helpers.sql', ...tests]) {
      const out = psql(target.href, ['-t', '-A', '-f', file], file);
      if (out === false) { ok = false; break; }
      const summary = out.trim().split('\n').filter((l) => l.startsWith('RLS')).join('\n');
      if (summary) console.log(summary);
    }
  }
} finally { psql(url, ['-c', `drop database if exists ${db}`], 'apagar banco'); }
process.exit(ok ? 0 : 1);
