// Aplica supabase/migrations/*.sql em ordem num Postgres (projeto Supabase real ou banco de teste), uma única vez cada.
// Registra o que foi aplicado em supabase_migrations.schema_migrations (mesma tabela do Supabase CLI), então CLI, MCP e este script enxergam o mesmo histórico.
// Uso:
//   TRADERNOVA_MIGRATIONS_DATABASE_URL=postgresql://... node scripts/apply-migrations.mjs          (só lista o que falta)
//   TRADERNOVA_MIGRATIONS_DATABASE_URL=postgresql://... node scripts/apply-migrations.mjs --apply  (aplica)
// A URL vem só do ambiente (contém senha). Nunca é registrada no log. Precisa de psql.
import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
const url = process.env.TRADERNOVA_MIGRATIONS_DATABASE_URL;
const apply = process.argv.includes('--apply');
const unknown = process.argv.slice(2).filter((a) => a !== '--apply');
if (unknown.length) { console.error(`Opção desconhecida: ${unknown.join(' ')}`); process.exit(2); }
if (!url) { console.error('Defina TRADERNOVA_MIGRATIONS_DATABASE_URL (string de conexão do banco).'); process.exit(2); }
const dir = path.join('supabase', 'migrations');
const files = fs.readdirSync(dir).filter((f) => /^\d{12}_[a-z0-9_]+\.sql$/.test(f)).sort();
const psql = (args, input) => spawnSync('psql', [url, '-v', 'ON_ERROR_STOP=1', '-q', '-X', '-t', '-A', ...args], {encoding: 'utf8', input});
const fail = (label, result) => { process.stderr.write(result.stderr.replaceAll(url, '<url>')); console.error(`Falhou: ${label}`); process.exit(1); };
let r = psql(['-c', "create schema if not exists supabase_migrations; create table if not exists supabase_migrations.schema_migrations(version text primary key, statements text[], name text);"]);
if (r.error) throw r.error;
if (r.status !== 0) fail('preparar o registro de migrações', r);
r = psql(['-c', 'select version from supabase_migrations.schema_migrations']);
if (r.status !== 0) fail('ler o registro de migrações', r);
const applied = new Set(r.stdout.split('\n').map((l) => l.trim()).filter(Boolean));
const pending = files.filter((f) => !applied.has(f.slice(0, 12)));
if (!pending.length) { console.log('Nenhuma migração pendente.'); process.exit(0); }
console.log(`Pendentes: ${pending.join(', ')}`);
if (!apply) { console.log('Nada foi aplicado. Rode com --apply para aplicar.'); process.exit(0); }
for (const file of pending) {
  const version = file.slice(0, 12), name = file.slice(13, -4);
  r = psql(['-f', path.join(dir, file)]);
  if (r.status !== 0) fail(file, r);
  r = psql(['-v', `version=${version}`, '-v', `name=${name}`], "insert into supabase_migrations.schema_migrations(version,name) values (:'version',:'name');\n");
  if (r.status !== 0) fail(`registrar ${file}`, r);
  console.log(`Aplicada: ${file}`);
}
