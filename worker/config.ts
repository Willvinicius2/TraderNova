import {isLiveAsset, livePairs, type LiveAssetId} from '../lib/tradernova/live-market';
export const allowedIntervals = [15, 60] as const;
export type WorkerConfig = {pair: LiveAssetId; interval: 15 | 60; dataDir: string; pollSeconds: number; logFile: string | null; once: boolean; httpPort: number | null};
export const provider = 'kraken-spot' as const;
export const krakenSymbol = (pair: LiveAssetId) => livePairs[pair].rest;
const flagNames: Record<string, keyof WorkerConfig> = {'--pair': 'pair', '--interval': 'interval', '--data-dir': 'dataDir', '--poll-seconds': 'pollSeconds', '--log-file': 'logFile', '--http-port': 'httpPort'};
const envNames: Record<string, keyof WorkerConfig> = {TRADERNOVA_WORKER_PAIR: 'pair', TRADERNOVA_WORKER_INTERVAL: 'interval', TRADERNOVA_WORKER_DATA_DIR: 'dataDir', TRADERNOVA_WORKER_POLL_SECONDS: 'pollSeconds', TRADERNOVA_WORKER_LOG_FILE: 'logFile', TRADERNOVA_WORKER_HTTP_PORT: 'httpPort'};
/** Prioridade: flags da linha de comando > variáveis de ambiente > padrões. Lança Error com mensagem em português. */
export function parseConfig(argv: string[], env: Record<string, string | undefined> = {}): WorkerConfig {
  const raw: Partial<Record<keyof WorkerConfig, string>> = {};
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
  const pair = (raw.pair ?? 'BTCUSD').toUpperCase();
  if (!isLiveAsset(pair)) throw new Error(`Par não suportado: ${pair}. Use BTCUSD, ETHUSD ou SOLUSD.`);
  const interval = Number(raw.interval ?? 60);
  if (!(allowedIntervals as readonly number[]).includes(interval)) throw new Error(`Intervalo não suportado: ${raw.interval}. Use 15 ou 60.`);
  const pollSeconds = Number(raw.pollSeconds ?? 30);
  if (!Number.isFinite(pollSeconds) || pollSeconds < 5 || pollSeconds > 600) throw new Error('O intervalo de consulta deve ficar entre 5 e 600 segundos.');
  const httpPort = Number(raw.httpPort ?? 8790);
  if (!Number.isInteger(httpPort) || httpPort < 1 || httpPort > 65535) throw new Error('A porta HTTP de leitura deve ficar entre 1 e 65535.');
  return {pair, interval: interval as 15 | 60, dataDir: raw.dataDir ?? 'worker-data', pollSeconds, logFile: raw.logFile ?? null, once, httpPort: noHttp ? null : httpPort};
}
