import path from 'node:path';
import type {Candle} from '../lib/tradernova/domain';
import type {MarketCandle} from '../lib/tradernova/live-market';
import {evaluatePaperEngine, type EngineReading, type EngineSnapshot} from '../lib/tradernova/paper-engine';
import {activePresets} from '../lib/tradernova/active-presets';
import {newPublicSignalId, signalDedupKey, type SignalRecord, type SignalStore} from '../lib/tradernova/signal-record';
import {openCandleStore, type CandleStore} from './candle-store';
import {provider, type WorkerConfig} from './config';
import {computeFeedState, contiguousTail, type FeedState} from './feed';
import {fetchKrakenOhlc, type FetchLike} from './kraken';
import type {Logger} from './log';
import {openFileSignalStore} from './signal-file-store';
export type Evaluator = (bars: Candle[], interval: number, receivedAt: number, now: number) => EngineSnapshot;
export type WorkerDeps = {config: WorkerConfig; log: Logger; fetch: FetchLike; now?: () => number; evaluate?: Evaluator; signalStore?: SignalStore};
export type CycleResult = {ok: boolean; feed: FeedState; newCandles: number; evaluated: boolean; signalsCreated: number};
/** Janela de entrada do motor: uma leitura só vale até 30 s depois do fechamento (ver advancePaperSession / manualOpportunity). */
export const entryWindowMs = 30000;
const maxEngineBars = 720;
const trim = (text: string) => (text.length > 500 ? `${text.slice(0, 497)}...` : text);
/** Monta o registro de pesquisa. Sempre mode 'research': strategyApprovals está vazio, nenhum alerta é permitido. */
export function buildSignalRecord(r: EngineReading, snapshot: EngineSnapshot, cfg: WorkerConfig, generatedAt: number): SignalRecord | null {
  if (r.state !== 'buy' || r.entryReference === null || r.stop === null || snapshot.closedAt === null) return null;
  const strategyVersion = activePresets[r.candidateId].id;
  const parts = {strategyId: r.candidateId, strategyVersion, provider, instrument: cfg.pair, timeframeMinutes: cfg.interval, side: 'buy' as const, signalTime: r.signalTime};
  return {publicId: newPublicSignalId(), dedupKey: signalDedupKey(parts), ...parts, generatedAt, expiresAt: snapshot.closedAt + entryWindowMs, entryReference: r.entryReference, stop: r.stop, target: r.target, evidence: r.evidence.map(trim), mode: 'research', invalidatedAt: null, invalidationReason: null};
}
export async function createWorker(deps: WorkerDeps) {
  const {config, log, fetch: fetchFn} = deps, now = deps.now ?? Date.now, evaluate: Evaluator = deps.evaluate ?? ((b, i, r, n) => evaluatePaperEngine(b, i, r, n));
  const step = config.interval * 60000, pollMs = config.pollSeconds * 1000;
  const store: CandleStore = await openCandleStore({dir: config.dataDir, provider, symbol: config.pair, interval: config.interval, log});
  const signals = deps.signalStore ?? await openFileSignalStore(path.join(config.dataDir, 'signals', `${provider}_${config.pair}_${config.interval}m.jsonl`), log);
  let forming: MarketCandle | null = null; // só em memória, nunca gravado
  let lastFetchOk = false, lastState: FeedState | null = null;
  let lastSuccessAt = store.checkpoint().lastSuccessAt;
  const setState = (state: FeedState, reason: string) => {
    if (state !== lastState) log.info('estado_do_feed', {feed_state: state, reason, previous: lastState});
    lastState = state;
  };
  async function cycle(): Promise<CycleResult> {
    const result: CycleResult = {ok: false, feed: 'desconectado', newCandles: 0, evaluated: false, signalsCreated: 0};
    let rows: MarketCandle[];
    try {
      rows = await fetchKrakenOhlc(fetchFn, config.pair, config.interval, store.checkpoint().lastClosedOpenTime);
    } catch (error) {
      lastFetchOk = false;
      log.warn('consulta_falhou', {error: error instanceof Error ? error.message : String(error)});
      setState('desconectado', 'A consulta à Kraken falhou.');
      log.info('avaliacao_ignorada', {feed_state: 'desconectado', reason: 'Nenhum sinal novo com a fonte desconectada.'});
      return result;
    }
    const receivedAt = now(), serverNow = receivedAt;
    lastFetchOk = true; lastSuccessAt = receivedAt; result.ok = true;
    // A última linha da Kraken é o candle em formação: nunca vai para o armazém.
    const open = rows.at(-1), history = rows.slice(0, -1);
    const current = Math.floor(serverNow / step) * step;
    forming = open && open.time === current ? open : null;
    const closed = history.filter((c) => c.time + step <= serverNow);
    const appended = await store.append(closed);
    result.newCandles = appended.added;
    await store.saveCheckpoint({lastSuccessAt});
    const all = store.candles(), tail = contiguousTail(all, config.interval), cp = store.checkpoint();
    const feed = computeFeedState({now: serverNow, interval: config.interval, pollMs, lastFetchOk, lastSuccessAt, lastClosedOpenTime: all.at(-1)?.time ?? null, contiguousClosed: tail.length});
    result.feed = feed.state;
    setState(feed.state, feed.reason);
    log.info('ciclo_concluido', {feed_state: feed.state, candles_added: appended.added, duplicates: appended.duplicates, ignored_corrections: appended.corrected, gap_candles: appended.gapCandles, stored: all.length, last_open_time: all.at(-1)?.time ?? null, forming: forming !== null});
    if (feed.state !== 'ao_vivo') { log.warn('avaliacao_ignorada', {feed_state: feed.state, reason: feed.reason}); return result; }
    const lastClosed = all.at(-1)!.time;
    if (cp.lastEvaluatedOpenTime !== null && lastClosed <= cp.lastEvaluatedOpenTime) return result;
    if (!forming) { log.info('avaliacao_adiada', {candle_open_time: lastClosed, reason: 'Aguardando a abertura do candle seguinte.'}); return result; }
    const snapshot = evaluate([...tail.slice(-maxEngineBars), forming], config.interval, receivedAt, serverNow);
    if (snapshot.status !== 'ready') { log.info('motor_bloqueado', {candle_open_time: lastClosed, reason: snapshot.reason}); return result; }
    result.evaluated = true;
    for (const reading of snapshot.readings) {
      const version = activePresets[reading.candidateId].id;
      if (reading.state !== 'buy') { log.info('leitura', {strategy: reading.candidateId, strategy_version: version, candle_open_time: reading.signalTime, state: reading.state}); continue; }
      const record = buildSignalRecord(reading, snapshot, config, serverNow);
      if (!record || record.expiresAt <= serverNow) { log.warn('sinal_descartado', {strategy: reading.candidateId, strategy_version: version, candle_open_time: reading.signalTime, reason: 'Janela de entrada de 30 s já encerrada.'}); continue; }
      try {
        const saved = await signals.insertIfAbsent(record);
        if (saved.created) result.signalsCreated++;
        log.info(saved.created ? 'sinal_registrado' : 'sinal_duplicado_ignorado', {strategy: reading.candidateId, strategy_version: version, candle_open_time: reading.signalTime, mode: saved.record.mode, public_id: saved.record.publicId});
      } catch (error) {
        log.error('sinal_invalido', {strategy: reading.candidateId, strategy_version: version, candle_open_time: reading.signalTime, error: error instanceof Error ? error.message : String(error)});
      }
    }
    await store.saveCheckpoint({lastEvaluatedOpenTime: lastClosed});
    return result;
  }
  /** Espera até a próxima consulta; acelera (5 s) logo após a virada do candle, enquanto o novo fechamento ainda não foi avaliado. */
  function nextDelayMs(): number {
    const t = now(), cp = store.checkpoint(), sinceBoundary = t - Math.floor(t / step) * step;
    const pending = lastState === 'ao_vivo' && (cp.lastEvaluatedOpenTime ?? 0) < Math.floor(t / step) * step - step && sinceBoundary < entryWindowMs + 5000;
    const awaitingNew = (cp.lastClosedOpenTime ?? 0) < Math.floor(t / step) * step - step && sinceBoundary < entryWindowMs + 5000;
    return pending || awaitingNew ? Math.min(pollMs, 5000) : pollMs;
  }
  return {cycle, nextDelayMs, store, signals, feedState: () => lastState};
}
