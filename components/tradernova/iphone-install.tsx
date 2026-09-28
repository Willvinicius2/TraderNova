'use client';
import {useEffect,useState} from 'react';
import {Download,Check} from 'lucide-react';
export function IphoneInstall(){
 const [installed,setInstalled]=useState(false);
 useEffect(()=>{const display=matchMedia('(display-mode: standalone)'),update=()=>setInstalled(display.matches||(navigator as Navigator&{standalone?:boolean}).standalone===true);update();display.addEventListener('change',update);return()=>display.removeEventListener('change',update);},[]);
 return <section className="panel padded account-install" id="instalar"><div className="row">{installed?<Check size={20}/>:<Download size={20}/>}<h2>{installed?'TraderNova na tela de início':'Instalar no iPhone'}</h2></div>
 {installed?<p>Você abriu a versão web instalada. As atualizações chegam pelo mesmo endereço.</p>:<ol className="install-steps"><li>Abra <a href="https://tradernova.willvinicius.chatgpt.site/">TraderNova no Safari</a>.</li><li>Toque em <strong>Compartilhar → Adicionar à Tela de Início</strong>.</li><li>Mantenha <strong>Abrir como App da Web</strong> ativado, se essa opção aparecer, e toque em <strong>Adicionar</strong>.</li></ol>}
 <p className="micro">Instalação da versão web, sem TestFlight. Precisa de internet. O radar funciona com a tela aberta; não há alertas com o app fechado.</p><p className="micro">Para testar: abra Robô → Testar exemplo de sinal, confira a ficha e exporte o JSON. O diário e as preferências ficam neste dispositivo.</p><p className="micro">A versão nativa iOS ainda precisa de assinatura Apple e teste físico antes de ser distribuída.</p></section>;
}
