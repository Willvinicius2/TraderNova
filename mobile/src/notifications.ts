import { Platform } from 'react-native';
import Constants from 'expo-constants';
import * as Notifications from 'expo-notifications';
import { PUSH_CHANNEL_ID, isExpoPushToken, type PushRegistration } from './push';
// Mostra a notificação também com o app aberto.
Notifications.setNotificationHandler({ handleNotification: async () => ({ shouldShowBanner: true, shouldShowList: true, shouldPlaySound: true, shouldSetBadge: false }) });
// Só roda quando o site pede (após login e opt-in). Nunca pede permissão na abertura do app.
export async function registerForPush(): Promise<PushRegistration> {
  if (Platform.OS !== 'android' && Platform.OS !== 'ios') return { status: 'unavailable', reason: 'web' };
  try {
    if (Platform.OS === 'android') await Notifications.setNotificationChannelAsync(PUSH_CHANNEL_ID, { name: 'Sinais', importance: Notifications.AndroidImportance.HIGH, lightColor: '#b99bff' });
    let permission = await Notifications.getPermissionsAsync();
    if (!permission.granted && permission.canAskAgain) permission = await Notifications.requestPermissionsAsync();
    if (!permission.granted) return { status: 'denied' };
    // O token Expo exige o projectId do EAS (vínculo com a conta Expo, ainda pendente).
    const projectId = Constants.expoConfig?.extra?.eas?.projectId ?? Constants.easConfig?.projectId;
    if (typeof projectId !== 'string' || !projectId) return { status: 'unavailable', reason: 'not-configured' };
    const { data } = await Notifications.getExpoPushTokenAsync({ projectId });
    return isExpoPushToken(data) ? { status: 'granted', token: data, platform: Platform.OS } : { status: 'unavailable', reason: 'error' };
  } catch { return { status: 'unavailable', reason: 'error' }; }
}
// Toques em notificações: a que abriu o app (app fechado) e as seguintes.
export function onNotificationTap(handler: (data: unknown) => void) {
  const last = Notifications.getLastNotificationResponse();
  if (last) { handler(last.notification.request.content.data); Notifications.clearLastNotificationResponse(); }
  const subscription = Notifications.addNotificationResponseReceivedListener(response => handler(response.notification.request.content.data));
  return () => subscription.remove();
}
