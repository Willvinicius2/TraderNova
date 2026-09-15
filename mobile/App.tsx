import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Alert, BackHandler, Linking, Pressable, StyleSheet, Text, View } from 'react-native';
import { File, Paths } from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { WebView } from 'react-native-webview';
import { SITE_URL, bridgeScript, externalLink, sameSite, signalLink, parentPage } from './src/site';

function MobileSite() {
  const web = useRef<WebView>(null);
  const currentPage = useRef(SITE_URL);
  const [url, setUrl] = useState(SITE_URL), [canGoBack, setCanGoBack] = useState(false);
  const [navigationId, setNavigationId] = useState(0);
  const [error, setError] = useState(false), [background, setBackground] = useState('#111117'), [light, setLight] = useState(false);
  useEffect(() => {
    const open = (value: string) => { const target = signalLink(value); if (target) { setError(false); setUrl(target); setNavigationId(id => id + 1); } };
    void Linking.getInitialURL().then(value => { if (value) open(value); }).catch(() => {});
    const listener = Linking.addEventListener('url', event => open(event.url));
    return () => listener.remove();
  }, []);
  useEffect(() => {
    const handler = BackHandler.addEventListener('hardwareBackPress', () => {
      const parent = parentPage(currentPage.current);
      if (parent) { web.current?.injectJavaScript(`location.replace(${JSON.stringify(parent)}); true;`); return true; }
      if (!canGoBack) return false; web.current?.goBack(); return true;
    });
    return () => handler.remove();
  }, [canGoBack]);
  function openExternal(value: string) { if (externalLink(value) || sameSite(value)) void Linking.openURL(value).catch(() => Alert.alert('TraderNova', 'Não foi possível abrir o link.')); }
  async function exportFile(text: string, name: unknown) {
    try {
      JSON.parse(text);
      const filename = typeof name === 'string' && /^[a-zA-Z0-9_-]{1,100}\.json$/.test(name) ? name : 'tradernova-exportacao.json';
      if (!await Sharing.isAvailableAsync()) throw new Error('Compartilhamento indisponível');
      const file = new File(Paths.cache, filename);
      file.write(text);
      await Sharing.shareAsync(file.uri, { mimeType: 'application/json', UTI: 'public.json', dialogTitle: 'Exportar TraderNova' });
    } catch { Alert.alert('TraderNova', 'Não foi possível exportar o arquivo. Tente novamente na versão web.'); }
  }
  return <SafeAreaView style={{ flex: 1, backgroundColor: background }}>
    <StatusBar style={light ? 'dark' : 'light'} />
    <WebView key={navigationId} ref={web} source={{ uri: url }} style={{ flex: 1, backgroundColor: background }}
      javaScriptEnabled domStorageEnabled cacheEnabled sharedCookiesEnabled
      startInLoadingState allowsBackForwardNavigationGestures
      originWhitelist={['https://*']} mixedContentMode="never" allowFileAccess={false}
      onNavigationStateChange={state => setCanGoBack(state.canGoBack)}
      onShouldStartLoadWithRequest={request => {
        if (request.isTopFrame === false) return true;
        if (sameSite(request.url)) return true;
        openExternal(request.url); return false;
      }}
      onOpenWindow={event => openExternal(event.nativeEvent.targetUrl)}
      onLoadStart={() => setError(false)}
      onError={() => setError(true)}
      onHttpError={event => { if (sameSite(event.nativeEvent.url) && event.nativeEvent.statusCode >= 400) setError(true); }}
      renderLoading={() => <View style={[styles.overlay, { backgroundColor: background }]}><ActivityIndicator color="#b99bff" /><Text style={styles.body}>Abrindo TraderNova…</Text></View>}
      injectedJavaScript={bridgeScript}
      onMessage={event => {
        if (!sameSite(event.nativeEvent.url) || event.nativeEvent.data.length > 2100000) return;
        try {
          const value = JSON.parse(event.nativeEvent.data);
          if (value.type === 'route' && typeof value.url === 'string' && sameSite(value.url)) currentPage.current = value.url;
          if (value.type === 'theme' && /^#[0-9a-f]{6}$/i.test(value.color) && typeof value.light === 'boolean') { setBackground(value.color); setLight(value.light); }
          if (value.type === 'export' && typeof value.text === 'string' && value.text.length <= 2000000) void exportFile(value.text, value.name);
          if (value.type === 'export-error') Alert.alert('TraderNova', 'Não foi possível exportar. Tente novamente na versão web.');
        } catch { /* Ignore unrelated or malformed messages from embedded resources. */ }
      }}
    />
    {error && <View style={[styles.overlay, { backgroundColor: background }]}><Text style={[styles.title, { color: light ? '#1b2540' : '#f0eff8' }]}>Não foi possível abrir o TraderNova</Text><Text style={[styles.body, { color: light ? '#596980' : '#aaaabb' }]}>Confira sua conexão e tente novamente.</Text><Pressable accessibilityRole="button" onPress={() => { setError(false); web.current?.reload(); }} style={styles.button}><Text style={styles.buttonText}>Tentar novamente</Text></Pressable></View>}
  </SafeAreaView>;
}
const styles = StyleSheet.create({ overlay: { position: 'absolute', left: 0, right: 0, top: 0, bottom: 0, justifyContent: 'center', alignItems: 'center', padding: 28, gap: 18 }, title: { fontSize: 22, fontWeight: '600', textAlign: 'center' }, body: { fontSize: 16, lineHeight: 24, color: '#aaaabb', textAlign: 'center' }, button: { minHeight: 48, paddingHorizontal: 24, paddingVertical: 14, borderRadius: 10, backgroundColor: '#b99bff' }, buttonText: { fontSize: 16, fontWeight: '600', color: '#1a1132' } });
export default function App() { return <SafeAreaProvider><MobileSite /></SafeAreaProvider>; }
