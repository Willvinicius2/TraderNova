export const SITE_URL = 'https://tradernova.willvinicius.chatgpt.site/';
export function sameSite(url: string) {
  try { const parsed = new URL(url); return parsed.origin === new URL(SITE_URL).origin && !parsed.username && !parsed.password; }
  catch { return false; }
}
export function externalLink(url: string) {
  try { const parsed = new URL(url); return parsed.protocol === 'https:' && !parsed.username && !parsed.password && !sameSite(url); }
  catch { return false; }
}
export function signalLink(url: string): string | null {
  const id = /^tradernova:\/\/signal\/([a-zA-Z0-9-]{1,100})\/?$/.exec(url)?.[1];
  if (!id) return null;
  const target = new URL(SITE_URL); target.searchParams.set('aba', 'robo'); target.searchParams.set('sinal', id);
  return target.href;
}
export function parentPage(url: string): string | null {
  if (!sameSite(url)) return null;
  const target = new URL(url);
  if (target.searchParams.has('sinal')) target.searchParams.delete('sinal');
  else if (target.searchParams.get('aba') && target.searchParams.get('aba') !== 'mercado') target.searchParams.set('aba', 'mercado');
  else return null;
  return target.href;
}
// Observe the site's own theme; no replacement styles, layout or navigation.
export const bridgeScript = `(() => {
  const send = value => window.ReactNativeWebView.postMessage(JSON.stringify(value));
  const theme = () => send({type:'theme', color:getComputedStyle(document.documentElement).getPropertyValue('--background').trim(), light:document.documentElement.classList.contains('light')});
  theme(); new MutationObserver(theme).observe(document.documentElement,{attributes:true,attributeFilter:['class']});
  const route = () => send({type:'route',url:location.href});
  route(); const replace = history.replaceState;
  history.replaceState = function(...args){ replace.apply(this,args); route(); };
  addEventListener('popstate',route);
  const download = anchor => {
    if (!anchor || !anchor.hasAttribute('download') || !anchor.href.startsWith('blob:')) return false;
    fetch(anchor.href).then(response => response.text()).then(text => {
      if(text.length > 2000000) throw new Error('Exportação muito grande');
      send({type:'export', text, name:anchor.download});
    }).catch(() => send({type:'export-error'}));
    return true;
  };
  const anchorClick = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function(){ if(!download(this)) anchorClick.call(this); };
  document.addEventListener('click', event => {
    const anchor = event.target instanceof Element ? event.target.closest('a[download]') : null;
    if(download(anchor)) event.preventDefault();
  },true);
  true;
})(); true;`;
