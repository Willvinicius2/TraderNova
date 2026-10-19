import {appendFileSync, mkdirSync} from 'node:fs';
import path from 'node:path';
import {parseConfig} from './config';
import {supabaseSignalStore, supabaseSignalsFromEnv} from '../lib/tradernova/supabase-signals';
import {createLogger, type Logger} from './log';
import {startSignalReadServer} from './http';
import {createWorker} from './worker';
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
  const log: Logger = createLogger(sinks, {provider: 'kraken-spot', symbol: config.pair, interval: config.interval});
  // Supabase: chave de serviço SÓ por variável de ambiente (nunca flag, para não ficar no histórico do shell).
  let signalStore;
  if (config.signalStore === 'supabase') {
    const supabase = supabaseSignalsFromEnv(env, 'TRADERNOVA_SUPABASE_SERVICE_KEY', (url, init) => fetch(url, init));
    if (!supabase) {
      log.error('configuracao_invalida', {error: 'Defina TRADERNOVA_SUPABASE_URL (https) e TRADERNOVA_SUPABASE_SERVICE_KEY para usar --signal-store supabase.'});
      return 2;
    }
    signalStore = supabaseSignalStore(supabase);
  }
  const worker = await createWorker({config, log, fetch: (url, init) => fetch(url, init), signalStore});
  // Leitura de sinais por HTTP (só 127.0.0.1) apenas no laço contínuo e com armazém em arquivo; --once nunca abre porta.
  // Com Supabase a ficha lê direto do banco (/api/signals com TRADERNOVA_SUPABASE_READ_KEY).
  let reader: Awaited<ReturnType<typeof startSignalReadServer>> | null = null;
  if (!config.once && config.httpPort !== null && config.signalStore === 'file') {
    try { reader = await startSignalReadServer({signalsDir: path.join(config.dataDir, 'signals'), port: config.httpPort, log}); } catch (error) {
      log.error('http_nao_iniciou', {port: config.httpPort, error: error instanceof Error ? error.message : String(error), reason: 'Use --http-port com outra porta ou --no-http.'});
      return 2;
    }
    log.info('http_leitura_iniciado', {host: '127.0.0.1', port: reader.port, route: 'GET /signals/:id'});
  }
  const stop = new AbortController();
  for (const sig of ['SIGINT', 'SIGTERM'] as const) process.on(sig, () => { if (!stop.signal.aborted) log.info('encerrando', {signal: sig, reason: 'O ciclo atual será concluído antes de sair.'}); stop.abort(); });
  log.info('worker_iniciado', {mode: config.once ? 'once' : 'loop', poll_seconds: config.pollSeconds, data_dir: path.resolve(config.dataDir), signal_mode: 'research', signal_store: config.signalStore});
  let exit = 0;
  do {
    try {
      const result = await worker.cycle();
      if (!result.ok) exit = 1; else if (!config.once) exit = 0;
    } catch (error) {
      exit = 1;
      log.error('ciclo_com_erro', {error: error instanceof Error ? error.message : String(error)});
    }
    if (config.once || stop.signal.aborted) break;
    await sleep(worker.nextDelayMs(), stop.signal);
  } while (!stop.signal.aborted);
  await reader?.close();
  log.info('worker_encerrado', {exit_code: exit});
  return config.once ? exit : 0;
}
