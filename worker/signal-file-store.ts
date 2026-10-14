import {appendFile, mkdir, readdir, readFile} from 'node:fs/promises';
import path from 'node:path';
import {isPublicSignalId, signalRecordSchema, type SignalRecord, type SignalStore} from '../lib/tradernova/signal-record';
import type {Logger} from './log';
/** SignalStore em arquivo: JSONL apenas-anexar + índices em memória; idempotente entre reinícios pela chave de deduplicação. */
export async function openFileSignalStore(file: string, log?: Logger): Promise<SignalStore & {list(): SignalRecord[]}> {
  await mkdir(path.dirname(file), {recursive: true});
  const byId = new Map<string, SignalRecord>(), byKey = new Map<string, SignalRecord>();
  let text = '';
  try { text = await readFile(file, 'utf8'); } catch { /* ainda não existe */ }
  let skipped = 0;
  for (const line of text.split('\n')) {
    if (!line.trim()) continue;
    try {
      const parsed = signalRecordSchema.parse(JSON.parse(line));
      if (!byKey.has(parsed.dedupKey)) { byId.set(parsed.publicId.toLowerCase(), parsed); byKey.set(parsed.dedupKey, parsed); }
    } catch { skipped++; }
  }
  if (skipped) log?.warn('sinais_invalidos_ignorados', {count: skipped, file});
  let needsNewline = text.length > 0 && !text.endsWith('\n');
  let queue: Promise<unknown> = Promise.resolve(); // serializa gravações concorrentes
  return {
    list: () => [...byKey.values()],
    async get(id) { return isPublicSignalId(id) ? byId.get(id.toLowerCase()) ?? null : null; },
    async findByDedupKey(key) { return byKey.get(key) ?? null; },
    insertIfAbsent(record) {
      const run = queue.then(async () => {
        const parsed = signalRecordSchema.parse(record), existing = byKey.get(parsed.dedupKey);
        if (existing) return {record: existing, created: false};
        await appendFile(file, (needsNewline ? '\n' : '') + JSON.stringify(parsed) + '\n');
        needsNewline = false;
        byId.set(parsed.publicId.toLowerCase(), parsed); byKey.set(parsed.dedupKey, parsed);
        return {record: parsed, created: true};
      });
      queue = run.catch(() => undefined);
      return run;
    },
  };
}
/** Leitura fresca do disco (sem cache) de um registro por ID público, em todos os `*.jsonl` do diretório de sinais. Usada pelo servidor de leitura. */
export async function findSignalOnDisk(dir: string, id: string): Promise<SignalRecord | null> {
  if (!isPublicSignalId(id)) return null;
  const wanted = id.toLowerCase();
  let names: string[];
  try { names = (await readdir(dir)).filter((n) => n.endsWith('.jsonl')).sort(); } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return null;
    throw error;
  }
  for (const name of names) {
    const text = await readFile(path.join(dir, name), 'utf8');
    for (const line of text.split('\n')) {
      if (!line.toLowerCase().includes(wanted)) continue;
      try {
        const parsed = signalRecordSchema.parse(JSON.parse(line));
        if (parsed.publicId.toLowerCase() === wanted) return parsed;
      } catch { /* linha truncada ou inválida */ }
    }
  }
  return null;
}
