import {mkdir, readdir, readFile, rename, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {workerStatusSchema, type WorkerStatus} from '../lib/tradernova/worker-status';
// Saúde do worker em arquivo (modo local): worker-data/status/<provedor>_<par>_<intervalo>m.json, gravado de forma atômica.
export const statusFile = (dataDir: string, s: Pick<WorkerStatus, 'provider' | 'instrument' | 'timeframeMinutes'>) => path.join(dataDir, 'status', `${s.provider}_${s.instrument}_${s.timeframeMinutes}m.json`);
export async function writeFileStatus(dataDir: string, status: WorkerStatus): Promise<void> {
  const file = statusFile(dataDir, status), tmp = `${file}.tmp`;
  await mkdir(path.dirname(file), {recursive: true});
  await writeFile(tmp, JSON.stringify(workerStatusSchema.parse(status)) + '\n');
  await rename(tmp, file);
}
/** Lê todos os status válidos de uma pasta; arquivos corrompidos são ignorados (nunca viram "ativo"). */
export async function readFileStatuses(statusDir: string): Promise<WorkerStatus[]> {
  const names = (await readdir(statusDir).catch(() => [] as string[])).filter((n) => n.endsWith('.json')).sort();
  const out: WorkerStatus[] = [];
  for (const name of names.slice(0, 50)) {
    try {
      const parsed = workerStatusSchema.safeParse(JSON.parse(await readFile(path.join(statusDir, name), 'utf8')));
      if (parsed.success) out.push(parsed.data);
    } catch { /* arquivo ilegível: ignorado */ }
  }
  return out;
}
