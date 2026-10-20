import {authConfigFromEnv} from '@/lib/tradernova/account';
export const dynamic='force-dynamic';
// Configuração PÚBLICA do login: URL do Supabase e chave publicável. Uma chave secreta configurada por engano nunca sai daqui.
export async function GET(){
 const cfg=authConfigFromEnv(process.env);
 return Response.json(cfg?{configured:true,url:cfg.url,publishableKey:cfg.publishableKey}:{configured:false},{headers:{'Cache-Control':'no-store'}});
}
