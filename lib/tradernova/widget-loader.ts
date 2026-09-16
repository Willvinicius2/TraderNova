const quoteScript='https://widgets.tradingview-widget.com/w/en/tv-single-ticker.js';
let pending:Promise<void>|null=null;

/** Share one module across quotes; allow a clean retry after a blocked script. */
export function loadQuoteWidget():Promise<void>{
 if(customElements.get('tv-single-ticker'))return Promise.resolve();
 if(pending)return pending;
 pending=new Promise<void>((resolve,reject)=>{
  let settled=false;
  const script=document.createElement('script');script.type='module';script.src=quoteScript;
  const timer=setTimeout(()=>finish(false),15000);
  function finish(ok:boolean){
   if(settled)return;settled=true;clearTimeout(timer);script.onerror=null;script.onload=null;
   if(ok)resolve();else{script.remove();pending=null;reject(new Error('Não foi possível carregar as cotações.'));}
  }
  script.onerror=()=>finish(false);script.onload=()=>finish(!!customElements.get('tv-single-ticker'));
  document.head.appendChild(script);
 });
 return pending;
}
