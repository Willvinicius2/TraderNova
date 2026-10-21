import { signalLink } from './site';
// Fase 4: partes puras do push (testadas em tests/site.mjs). O código nativo fica em src/notifications.ts.
// Canal Android; o servidor usa o mesmo nome (lib/tradernova/push-notifications.ts).
export const PUSH_CHANNEL_ID = 'sinais';
export function isExpoPushToken(value: unknown): value is string {
  return typeof value === 'string' && /^Expo(nent)?PushToken\[[A-Za-z0-9_-]{10,200}\]$/.test(value);
}
// Toque na notificação: só abre a ficha quando data.url é um link de sinal válido (UUID v4). Qualquer outra coisa é ignorada.
export function notificationTarget(data: unknown): string | null {
  if (!data || typeof data !== 'object') return null;
  const url = (data as { url?: unknown }).url;
  return typeof url === 'string' && url.length <= 200 ? signalLink(url) : null;
}
export type PushRegistration =
  | { status: 'granted'; token: string; platform: 'android' | 'ios' }
  | { status: 'denied' }
  | { status: 'unavailable'; reason: 'web' | 'not-configured' | 'error' };
// Resposta ao site (que pediu {type:'push-register'} pela ponte). O site grava o token em push_devices com a sessão do usuário.
export function pushResultScript(result: PushRegistration) {
  return `window.dispatchEvent(new CustomEvent('tradernova-push',{detail:${JSON.stringify(result)}})); true;`;
}
