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
  const migrations = fs.readdirSync('supabase/migrations').filter((f) => f.endsWith('.sql')).sort().map((f) => `supabase/migrations/${f}`);
  for (const file of ['supabase/tests/auth-stub.sql', ...migrations]) if (psql(target.href, ['-f', file], file) === false) { ok = false; break; }
  if (ok) {
    const out = psql(target.href, ['-t', '-A', '-f', 'supabase/tests/rls.sql'], 'supabase/tests/rls.sql');
    if (out === false) ok = false; else console.log(out.trim().split('\n').filter((l) => l.startsWith('RLS')).join('\n'));
  }
} finally { psql(url, ['-c', `drop database if exists ${db}`], 'apagar banco'); }
process.exit(ok ? 0 : 1);
