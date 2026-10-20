import {appendFileSync, mkdirSync} from 'node:fs';
import path from 'node:path';
import {parseConfig, workerConfigs} from './config';
import {supabaseSignalStore, supabaseSignalsFromEnv} from '../lib/tradernova/supabase-signals';
import {supabaseWorkerStatusWriter} from '../lib/tradernova/worker-status';
import {createLogger, type Logger} from './log';
import {startSignalReadServer} from './http';
import {createWorker} from './worker';
import {createPushDispatcher} from './push';
const sleep = (ms: number, signal: AbortSignal) => new Promise<void>((resolve) => {
  const timer = setTimeout(resolve, ms);
  signal.addEventListener('abort', () => { clearTimeout(timer); resolve(); }, {once: true});
});
/** Executa o worker. Devolve o código de saída (0 ok; 1 falha de consulta no modo --once; 2 configuração inválida). */
export async function main(argv: string[], env: Record<string, string | undefined>): Promise<number> {
  let config;
  try { config = parseConfig(argv, env); } catch (error) {
    process.stderr.write(`${JSON.stringify({ts: new Date().toISOString(), level: 'error', event: 'configuracao_invalida', error: error instanceof Error ? error.message : String(error)})}\n`);
    return 2;
  }
  const sinks: Array<(line: string) => void> = [(line) => process.stdout.write(`${line}\n`)];
  if (config.logFile) {
    mkdirSync(path.dirname(path.resolve(config.logFile)), {recursive: true});
    const file = config.logFile;
    sinks.push((line) => appendFileSync(file, `${line}\n`));
  }
  const log: Logger = createLogger(sinks, {provider: 'kraken-spot'});
  // Supabase: chave de serviço SÓ por variável de ambiente (nunca flag, para não ficar no histórico do shell).
  let signalStore, statusSink, onSignalsCreated;
  if (config.signalStore === 'supabase') {
    const supabase = supabaseSignalsFromEnv(env, 'TRADERNOVA_SUPABASE_SERVICE_KEY', (url, init) => fetch(url, init));
    if (!supabase) {
      log.error('configuracao_invalida', {error: 'Defina TRADERNOVA_SUPABASE_URL (https) e TRADERNOVA_SUPABASE_SERVICE_KEY para usar --signal-store supabase.'});
      return 2;
    }
    signalStore = supabaseSignalStore(supabase);
    statusSink = supabaseWorkerStatusWriter(supabase);
    // Push (Fase 4): só com Supabase. EXPO_ACCESS_TOKEN é opcional; sinal de pesquisa nunca é enviado pela política padrão.
    onSignalsCreated = createPushDispatcher({url: supabase.url, key: supabase.key, fetch: (url, init) => fetch(url, init)}, {fetch: (url, init) => fetch(url, init), accessToken: env.EXPO_ACCESS_TOKEN?.trim() || undefined});
  }
  // Um worker por combinação par/intervalo, cada um com armazém e checkpoint próprios (mesmo formato de antes).
  const workers = [];
  for (const target of workerConfigs(config)) {
    const targetLog = createLogger(sinks, {provider: 'kraken-spot', symbol: target.pair, interval: target.interval});
    workers.push({target, log: targetLog, worker: await createWorker({config: target, log: targetLog, fetch: (url, init) => fetch(url, init), signalStore, statusSink, onSignalsCreated})});
  }
  // Leitura de sinais por HTTP (só 127.0.0.1) apenas no laço contínuo e com armazém em arquivo; --once nunca abre porta.
  // Com Supabase a ficha lê direto do banco (/api/signals com TRADERNOVA_SUPABASE_READ_KEY).
  let reader: Awaited<ReturnType<typeof startSignalReadServer>> | null = null;
  if (!config.once && config.httpPort !== null && config.signalStore === 'file') {
    try { reader = await startSignalReadServer({signalsDir: path.join(config.dataDir, 'signals'), statusDir: path.join(config.dataDir, 'status'), port: config.httpPort, log}); } catch (error) {
      log.error('http_nao_iniciou', {port: config.httpPort, error: error instanceof Error ? error.message : String(error), reason: 'Use --http-port com outra porta ou --no-http.'});
      return 2;
    }
    log.info('http_leitura_iniciado', {host: '127.0.0.1', port: reader.port, routes: ['GET /signals/:id', 'GET /status']});
  }
  const stop = new AbortController();
  for (const sig of ['SIGINT', 'SIGTERM'] as const) process.on(sig, () => { if (!stop.signal.aborted) log.info('encerrando', {signal: sig, reason: 'O ciclo atual será concluído antes de sair.'}); stop.abort(); });
  log.info('worker_iniciado', {mode: config.once ? 'once' : 'loop', poll_seconds: config.pollSeconds, data_dir: path.resolve(config.dataDir), signal_mode: 'research', signal_store: config.signalStore, targets: config.targets.map((t) => `${t.pair}/${t.interval}m`)});
  let exit = 0;
  do {
    // Em sequência (gentil com a Kraken). A falha de uma combinação não interrompe as outras.
    let failed = false;
    for (const {worker, log: targetLog} of workers) {
      if (stop.signal.aborted) break;
      try {
        if (!(await worker.cycle()).ok) failed = true;
      } catch (error) {
        failed = true;
        targetLog.error('ciclo_com_erro', {error: error instanceof Error ? error.message : String(error)});
      }
    }
    exit = failed ? 1 : 0;
    if (config.once || stop.signal.aborted) break;
    await sleep(Math.min(...workers.map(({worker}) => worker.nextDelayMs())), stop.signal);
  } while (!stop.signal.aborted);
  await reader?.close();
  log.info('worker_encerrado', {exit_code: exit});
  return config.once ? exit : 0;
}
