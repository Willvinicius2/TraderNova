'use client';
import {useState} from 'react';
import {Download,LogIn,LogOut,Mail,Trash2} from 'lucide-react';
import {toast} from 'sonner';
import {AccountError,accountErrorText,isEmail} from '@/lib/tradernova/account';
import type {Account} from './use-account';
// Linhas da aba Conta para login, exportação e exclusão. Usa só as classes existentes do site (settings-row, botões, notice).
const message=(e:unknown)=>e instanceof AccountError?accountErrorText[e.reason]:'Algo deu errado. Tente de novo.';
function download(name:string,data:unknown){
 const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'})),a=document.createElement('a');
 a.href=url;a.download=name;a.click();URL.revokeObjectURL(url);
}
function Tag({children,tone='neutral'}:{children:React.ReactNode;tone?:string}){return <span className={`tag ${tone}`}>{children}</span>;}
export function AccountSettings({account}:{account:Account}){
 const [email,setEmail]=useState(''),[code,setCode]=useState(''),[busy,setBusy]=useState(false),[confirming,setConfirming]=useState(false),[confirmText,setConfirmText]=useState('');
 async function run(fn:()=>Promise<void>){setBusy(true);try{await fn();}catch(e){toast.error(message(e));}finally{setBusy(false);}}
 if(account.status==='loading')return <div className="settings-row"><div><h3>Dados e conta</h3><p>Verificando a conta…</p></div><Tag>…</Tag></div>;
 if(account.status==='unconfigured')return <div className="settings-row"><div><h3>Dados e conta</h3><p>Supabase preparado no projeto; não conectado.</p></div><Tag>Pendente</Tag></div>;
 if(account.status==='signed-out')return <div className="settings-row account-login"><div className="full">
  <h3>Entrar na sua conta</h3>
  <p>Receba um link e um código por e-mail. Sem senha. O diário passa a ser sincronizado entre celular e computador.</p>
  {account.error&&<div className="notice spaced">{account.error}</div>}
  {account.pendingEmail?<form onSubmit={e=>{e.preventDefault();void run(async()=>{await account.verifyCode(code);setCode('');toast.success('Conta conectada.');});}}>
   <label className="field-label" htmlFor="account-code">Código enviado para {account.pendingEmail}</label>
   <input id="account-code" inputMode="numeric" autoComplete="one-time-code" value={code} maxLength={10} onChange={e=>setCode(e.target.value.replace(/\D/g,''))} placeholder="000000"/>
   <p className="micro spaced">Ou toque no link do e-mail neste mesmo aparelho.</p>
   <button className="primary-button full spaced" type="submit" disabled={busy||code.length<6}><LogIn size={16}/> Entrar com código</button><button className="text-button" type="button" disabled={busy} onClick={account.cancelPending}>Usar outro e-mail</button>
  </form>:<form onSubmit={e=>{e.preventDefault();void run(async()=>{await account.requestLink(email);toast.success('Enviamos o link e o código para o seu e-mail.');});}}>
   <label className="field-label" htmlFor="account-email">E-mail</label>
   <input id="account-email" type="email" autoComplete="email" value={email} maxLength={254} onChange={e=>setEmail(e.target.value)} placeholder="voce@exemplo.com"/>
   <button className="primary-button spaced" type="submit" disabled={busy||!isEmail(email.trim())}><Mail size={16}/> Enviar link de acesso</button>
  </form>}
 </div></div>;
 const s=account.session!;
 return <>
  <div className="settings-row"><div><h3>Conta conectada</h3><p>{s.user.email||'E-mail não informado'} · diário sincronizado.</p></div><button className="secondary-button" disabled={busy} onClick={()=>void run(async()=>{await account.signOut();toast.success('Você saiu. Os dados deste aparelho continuam aqui.');})}><LogOut size={16}/> Sair</button></div>
  <div className="settings-row"><div><h3>Exportar meus dados</h3><p>Diário, preferências e aparelhos guardados na conta, em JSON.</p></div><button className="secondary-button" disabled={busy} onClick={()=>void run(async()=>{const data=await account.withSession((c,x)=>c.exportData(x));download('tradernova-meus-dados.json',{email:s.user.email,...data});})}><Download size={16}/> Exportar</button></div>
  <div className="settings-row account-delete"><div className="full"><h3>Excluir conta</h3><p>Apaga a conta e, no servidor, diário, preferências e aparelhos. Não pode ser desfeito. Os dados locais deste aparelho não são apagados.</p>
   {confirming&&<><label className="field-label" htmlFor="account-delete">Digite EXCLUIR para confirmar</label><input id="account-delete" value={confirmText} onChange={e=>setConfirmText(e.target.value)} autoComplete="off"/>
    <div className="row spaced account-actions"><button className="primary-button" disabled={busy||confirmText.trim().toUpperCase()!=='EXCLUIR'} onClick={()=>void run(async()=>{await account.deleteAccount();setConfirming(false);setConfirmText('');toast.success('Conta excluída.');})}><Trash2 size={16}/> Excluir definitivamente</button><button className="secondary-button" disabled={busy} onClick={()=>{setConfirming(false);setConfirmText('');}}>Cancelar</button></div></>}
  </div>{!confirming&&<button className="secondary-button" disabled={busy} onClick={()=>setConfirming(true)}><Trash2 size={16}/> Excluir</button>}</div>
 </>;
}
