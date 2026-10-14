import {lookupSignal,signalSourceFromEnv} from '@/lib/tradernova/signal-source';
export const dynamic='force-dynamic';
const headers={'Cache-Control':'no-store'};
// Somente leitura. O ID é validado como UUID antes de qualquer consulta e nunca é devolvido na resposta.
export async function GET(_request:Request,context:{params:Promise<{id:string}>|{id:string}}){
 const {id}=await context.params;
 // Autorização: quando houver login, passar aqui a verificação por usuário (4º argumento de lookupSignal).
 const {status,body}=await lookupSignal(id,signalSourceFromEnv(process.env,(url,init)=>fetch(url,init)),Date.now());
 return Response.json(body,{status,headers});
}
