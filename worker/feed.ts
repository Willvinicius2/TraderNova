import type {Candle} from '../lib/tradernova/domain';
export type FeedState = 'ao_vivo' | 'atrasado' | 'desconectado' | 'historico_insuficiente';
/** Mesmo mínimo do motor (paper-engine): 201 candles fechados e contíguos. */
export const minClosedCandles = 201;
/** Quantidade de consultas sem sucesso a partir da qual a fonte é considerada atrasada. */
export const staleAfterPolls = 3;
/** Fatia final do histórico sem lacunas (o motor bloqueia qualquer lacuna na janela que recebe). */
export function contiguousTail<T extends Candle>(closed: T[], interval: number): T[] {
  const step = interval * 60000;
  let start = closed.length - 1;
  while (start > 0 && closed[start].time - closed[start - 1].time === step) start--;
  return closed.slice(Math.max(start, 0));
}
export type FeedInput = {now: number; interval: number; pollMs: number; lastFetchOk: boolean; lastSuccessAt: number | null; lastClosedOpenTime: number | null; contiguousClosed: number};
/**
 * Ordem de decisão:
 *  desconectado: nunca houve consulta bem-sucedida ou a última consulta falhou;
 *  atrasado: último sucesso há mais de 3 consultas (3 × poll) OU o candle fechado mais novo (medido pelo open_time) é mais velho que 2 × intervalo;
 *  historico_insuficiente: menos de 201 candles fechados contíguos;
 *  ao_vivo: caso contrário. Somente 'ao_vivo' permite avaliar a estratégia.
 */
export function computeFeedState(i: FeedInput): {state: FeedState; reason: string} {
  if (!i.lastFetchOk || i.lastSuccessAt === null) return {state: 'desconectado', reason: 'A última consulta à Kraken falhou ou ainda não houve sucesso.'};
  if (i.now - i.lastSuccessAt > staleAfterPolls * i.pollMs) return {state: 'atrasado', reason: `Último sucesso há mais de ${staleAfterPolls} consultas.`};
  if (i.lastClosedOpenTime === null || i.now - i.lastClosedOpenTime > 2 * i.interval * 60000) return {state: 'atrasado', reason: 'O candle fechado mais recente é mais velho que 2 intervalos.'};
  if (i.contiguousClosed < minClosedCandles) return {state: 'historico_insuficiente', reason: `Apenas ${i.contiguousClosed} candles fechados contíguos (mínimo ${minClosedCandles}).`};
  return {state: 'ao_vivo', reason: 'Fonte recente e histórico suficiente.'};
}
