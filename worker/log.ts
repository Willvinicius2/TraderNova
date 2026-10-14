// Logs estruturados: um objeto JSON por linha. Nunca registra segredos (o worker não usa nenhum).
export type LogFields = Record<string, unknown>;
export type Logger = {
  info(event: string, fields?: LogFields): void;
  warn(event: string, fields?: LogFields): void;
  error(event: string, fields?: LogFields): void;
};
export function createLogger(sinks: Array<(line: string) => void>, base: LogFields, clock: () => number = Date.now): Logger {
  const emit = (level: string, event: string, fields: LogFields = {}) => {
    const line = JSON.stringify({ts: new Date(clock()).toISOString(), level, event, ...base, ...fields});
    for (const sink of sinks) {
      try { sink(line); } catch { /* um destino de log com falha não derruba o worker */ }
    }
  };
  return {info: (e, f) => emit('info', e, f), warn: (e, f) => emit('warn', e, f), error: (e, f) => emit('error', e, f)};
}
