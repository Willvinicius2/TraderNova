import {livePairs, parseKrakenHistory, type LiveAssetId, type MarketCandle} from '../lib/tradernova/live-market';
export type FetchLike = (url: string, init?: {signal?: AbortSignal; headers?: Record<string, string>}) => Promise<{ok: boolean; status: number; json(): Promise<unknown>}>;
/** Consulta o OHLC público da Kraken e reaproveita o parser do app (parseKrakenHistory). Devolve linhas em ordem, a última é o candle aberto. */
export async function fetchKrakenOhlc(fetchFn: FetchLike, pair: LiveAssetId, interval: number, sinceMs: number | null, timeoutMs = 10000): Promise<MarketCandle[]> {
  const url = new URL('https://api.kraken.com/0/public/OHLC');
  url.searchParams.set('pair', livePairs[pair].rest);
  url.searchParams.set('interval', String(interval));
  if (sinceMs !== null) url.searchParams.set('since', String(Math.floor(sinceMs / 1000)));
  const response = await fetchFn(url.toString(), {signal: AbortSignal.timeout(timeoutMs), headers: {Accept: 'application/json'}});
  if (!response.ok) throw new Error(`Kraken respondeu HTTP ${response.status}.`);
  return parseKrakenHistory(await response.json());
}
