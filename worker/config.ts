import {isLiveAsset, livePairs, type LiveAssetId} from '../lib/tradernova/live-market';
export const allowedIntervals = [15, 60] as const;
export type WorkerTarget = {pair: LiveAssetId; interval: 15 | 60};
/** pair/interval = primeira combinação de targets (compatível com o modo de um par só). */
export type WorkerConfig = {pair: LiveAssetId; interval: 15 | 60; targets: WorkerTarget[]; dataDir: string; pollSeconds: number; logFile: string | null; once: boolean; httpPort: number | null; signalStore: 'file' | 'supabase'};
export const provider = 'kraken-spot' as const;
export const krakenSymbol = (pair: LiveAssetId) => livePairs[pair].rest;
const flagNames: Record<string, RawKey> = {'--pair': 'pair', '--interval': 'interval', '--data-dir': 'dataDir', '--poll-seconds': 'pollSeconds', '--log-file': 'logFile', '--http-port': 'httpPort', '--signal-store': 'signalStore', '--pairs': 'pairs', '--intervals': 'intervals'};
const envNames: Record<string, RawKey> = {TRADERNOVA_WORKER_PAIR: 'pair', TRADERNOVA_WORKER_INTERVAL: 'interval', TRADERNOVA_WORKER_DATA_DIR: 'dataDir', TRADERNOVA_WORKER_POLL_SECONDS: 'pollSeconds', TRADERNOVA_WORKER_LOG_FILE: 'logFile', TRADERNOVA_WORKER_HTTP_PORT: 'httpPort', TRADERNOVA_WORKER_SIGNAL_STORE: 'signalStore', TRADERNOVA_WORKER_PAIRS: 'pairs', TRADERNOVA_WORKER_INTERVALS: 'intervals'};
type RawKey = keyof WorkerConfig | 'pairs' | 'intervals';
const parsePair = (value: string) => {
  const pair = value.trim().toUpperCase();
  if (!isLiveAsset(pair)) throw new Error(`Par não suportado: ${pair}. Use BTCUSD, ETHUSD ou SOLUSD.`);
  return pair;
};
const parseInterval = (value: string) => {
  const interval = Number(value);
  if (!value.trim() || !(allowedIntervals as readonly number[]).includes(interval)) throw new Error(`Intervalo não suportado: ${value}. Use 15 ou 60.`);
  return interval as 15 | 60;
};
const parseList = <T>(value: string, parse: (v: string) => T) => {
  const items = [...new Set(value.split(',').map((v) => v.trim()).filter(Boolean))].map(parse);
  if (!items.length) throw new Error('Lista vazia em --pairs/--intervals.');
  return [...new Set(items)];
};
/** Combinação de cada par com cada intervalo, na ordem dada. Usada para criar um worker por combinação no mesmo processo. */
export const workerConfigs = (config: WorkerConfig): WorkerConfig[] => config.targets.map(({pair, interval}) => ({...config, pair, interval, targets: [{pair, interval}]}));
/** Prioridade: flags da linha de comando > variáveis de ambiente > padrões. Lança Error com mensagem em português. */
export function parseConfig(argv: string[], env: Record<string, string | undefined> = {}): WorkerConfig {
  const raw: Partial<Record<RawKey, string>> = {};
  for (const [name, key] of Object.entries(envNames)) if (env[name]) raw[key] = env[name];
  let once = false, noHttp = false;
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--once') { once = true; continue; }
    if (arg === '--no-http') { noHttp = true; continue; }
    const [flag, inline] = arg.split('=', 2);
    const key = flagNames[flag];
    if (!key) throw new Error(`Opção desconhecida: ${flag}`);
    const value = inline ?? argv[++i];
    if (value === undefined) throw new Error(`A opção ${flag} precisa de um valor.`);
    raw[key] = value;
  }
  // --pairs/--intervals (listas) têm prioridade sobre --pair/--interval.
  const pairs = parseList(raw.pairs ?? raw.pair ?? 'BTCUSD', parsePair);
  const intervals = parseList(raw.intervals ?? raw.interval ?? '60', parseInterval);
  const targets = pairs.flatMap((pair) => intervals.map((interval) => ({pair, interval})));
  const [{pair, interval}] = targets;
  const pollSeconds = Number(raw.pollSeconds ?? 30);
  if (!Number.isFinite(pollSeconds) || pollSeconds < 5 || pollSeconds > 600) throw new Error('O intervalo de consulta deve ficar entre 5 e 600 segundos.');
  const httpPort = Number(raw.httpPort ?? 8790);
  if (!Number.isInteger(httpPort) || httpPort < 1 || httpPort > 65535) throw new Error('A porta HTTP de leitura deve ficar entre 1 e 65535.');
  const signalStore = (raw.signalStore ?? 'file').toLowerCase();
  if (signalStore !== 'file' && signalStore !== 'supabase') throw new Error(`Armazém de sinais não suportado: ${raw.signalStore}. Use file ou supabase.`);
  return {pair, interval, targets, dataDir: raw.dataDir ?? 'worker-data', pollSeconds, logFile: raw.logFile ?? null, once, httpPort: noHttp ? null : httpPort, signalStore};
}
