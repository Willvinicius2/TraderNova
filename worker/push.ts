import {createExpoPushSender, defaultPushPolicy, dispatchPush} from '../lib/tradernova/push-notifications';
import {loadPushTargets, supabasePushDeliveryStore, type SupabasePushConfig} from '../lib/tradernova/supabase-push';
import type {SignalRecord} from '../lib/tradernova/signal-record';
import type {PushFetch} from '../lib/tradernova/push-notifications';
export type PushSummary = {skipped: 'research-only'} | {sent: number; failed: number; skipped: number; disabledDevices: number};
/**
 * Envio de push depois que o worker grava sinais novos (Fase 4, docs/NOTIFICACOES.md).
 * Com a política padrão, sinal de pesquisa nunca vira notificação: nesse caso nem consulta aparelhos.
 */
export function createPushDispatcher(cfg: SupabasePushConfig, opts: {fetch: PushFetch; accessToken?: string; now?: () => number}) {
  const store = supabasePushDeliveryStore(cfg), send = createExpoPushSender({fetch: opts.fetch, accessToken: opts.accessToken}), now = opts.now ?? Date.now;
  return async (records: SignalRecord[]): Promise<PushSummary> => {
    if (!defaultPushPolicy.allowResearch && records.every((r) => r.mode === 'research')) return {skipped: 'research-only'};
    const targets = await loadPushTargets(cfg);
    const result = await dispatchPush({signals: records, ...targets, now: now(), store, send});
    return {sent: result.sent, failed: result.failed, skipped: result.skipped.length, disabledDevices: result.disabledDevices.length};
  };
}
