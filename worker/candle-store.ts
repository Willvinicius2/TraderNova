import {appendFile, mkdir, readFile, rename, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {validCandle, type MarketCandle} from '../lib/tradernova/live-market';
import type {Logger} from './log';
export type Checkpoint = {version: 1; provider: string; symbol: string; interval: number; lastClosedOpenTime: number | null; lastSuccessAt: number | null; lastEvaluatedOpenTime: number | null};
export type AppendResult = {added: number; duplicates: number; corrected: number; outOfOrder: number; gapCandles: number};
export type CandleStore = {
  candles(): MarketCandle[];
  checkpoint(): Checkpoint;
  append(batch: MarketCandle[]): Promise<AppendResult>;
  saveCheckpoint(patch: Partial<Pick<Checkpoint, 'lastClosedOpenTime' | 'lastSuccessAt' | 'lastEvaluatedOpenTime'>>): Promise<void>;
};
const sameCandle = (a: MarketCandle, b: MarketCandle) => a.open === b.open && a.high === b.high && a.low === b.low && a.close === b.close && a.volume === b.volume;
/** Escrita atômica: grava em arquivo temporário e renomeia por cima do destino. */
export async function writeJsonAtomic(file: string, value: unknown) {
  const tmp = `${file}.tmp`;
  await writeFile(tmp, JSON.stringify(value, null, 1) + '\n');
  await rename(tmp, file);
}
/**
 * Armazém de candles fechados, apenas-anexar (JSONL), um arquivo por provedor/símbolo/intervalo.
 * Duplicata exata é ignorada. Candle "corrigido" para um open_time já gravado: mantém o PRIMEIRO e registra aviso
 * (o histórico gravado é a base de qualquer sinal já emitido; reescrevê-lo mudaria a evidência depois do fato).
 */
export async function openCandleStore(opts: {dir: string; provider: string; symbol: string; interval: number; log: Logger}): Promise<CandleStore> {
  const {dir, provider, symbol, interval, log} = opts, step = interval * 60000;
  const name = `${provider}_${symbol}_${interval}m`;
  const candleFile = path.join(dir, 'candles', `${name}.jsonl`), checkpointFile = path.join(dir, 'checkpoints', `${name}.json`);
  await mkdir(path.dirname(candleFile), {recursive: true});
  await mkdir(path.dirname(checkpointFile), {recursive: true});
  const list: MarketCandle[] = [], byTime = new Map<number, MarketCandle>();
  let text = '';
  try { text = await readFile(candleFile, 'utf8'); } catch { /* arquivo ainda não existe */ }
  let skipped = 0;
  for (const line of text.split('\n')) {
    if (!line.trim()) continue;
    let c: MarketCandle | null = null;
    try { c = JSON.parse(line) as MarketCandle; } catch { /* linha truncada por queda de energia */ }
    if (!c || !validCandle(c) || c.time % step !== 0 || (list.length && c.time <= list[list.length - 1].time)) { skipped++; continue; }
    list.push(c); byTime.set(c.time, c);
  }
  if (skipped) log.warn('linhas_invalidas_ignoradas', {count: skipped, file: candleFile});
  const needsNewline = text.length > 0 && !text.endsWith('\n');
  const empty: Checkpoint = {version: 1, provider, symbol, interval, lastClosedOpenTime: null, lastSuccessAt: null, lastEvaluatedOpenTime: null};
  let checkpoint = empty;
  try {
    const parsed = JSON.parse(await readFile(checkpointFile, 'utf8')) as Checkpoint;
    if (parsed.version === 1 && parsed.provider === provider && parsed.symbol === symbol && parsed.interval === interval) checkpoint = {...empty, ...parsed};
    else log.warn('checkpoint_incompativel_ignorado', {file: checkpointFile});
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== 'ENOENT') log.warn('checkpoint_ilegivel_ignorado', {file: checkpointFile});
  }
  // O armazém é a verdade: se o checkpoint ficou para trás (queda entre gravações), avança.
  const storeLast = list.at(-1)?.time ?? null;
  if (storeLast !== null && (checkpoint.lastClosedOpenTime ?? 0) < storeLast) checkpoint = {...checkpoint, lastClosedOpenTime: storeLast};
  log.info('armazem_carregado', {candles: list.length, last_open_time: storeLast, checkpoint_last_closed: checkpoint.lastClosedOpenTime});
  let pendingNewline = needsNewline;
  return {
    candles: () => list.slice(),
    checkpoint: () => ({...checkpoint}),
    async append(batch) {
      const result: AppendResult = {added: 0, duplicates: 0, corrected: 0, outOfOrder: 0, gapCandles: 0};
      const accepted: MarketCandle[] = [];
      let tail = list.at(-1);
      for (const c of [...batch].sort((a, b) => a.time - b.time)) {
        const prior = byTime.get(c.time);
        if (prior) {
          if (sameCandle(prior, c)) result.duplicates++;
          else { result.corrected++; log.warn('candle_corrigido_ignorado', {open_time: c.time, mantido: 'primeiro'}); }
          continue;
        }
        if (tail && c.time < tail.time) { result.outOfOrder++; log.warn('candle_fora_de_ordem_ignorado', {open_time: c.time, last_open_time: tail.time}); continue; }
        if (tail) {
          const missing = Math.round((c.time - tail.time) / step) - 1;
          if (missing > 0) { result.gapCandles += missing; log.warn('lacuna_detectada', {from_open_time: tail.time, to_open_time: c.time, missing}); }
        }
        accepted.push(c); tail = c; result.added++;
      }
      if (accepted.length) {
        await appendFile(candleFile, (pendingNewline ? '\n' : '') + accepted.map((c) => JSON.stringify(c)).join('\n') + '\n');
        pendingNewline = false;
        for (const c of accepted) { list.push(c); byTime.set(c.time, c); }
        checkpoint = {...checkpoint, lastClosedOpenTime: list[list.length - 1].time};
      }
      return result;
    },
    async saveCheckpoint(patch) {
      checkpoint = {...checkpoint, ...patch};
      await writeJsonAtomic(checkpointFile, checkpoint);
    },
  };
}
