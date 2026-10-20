import {lookupWorkerStatus,statusReaderFromEnv} from '@/lib/tradernova/worker-status-source';
export const dynamic='force-dynamic';
// Somente leitura: saúde do worker por par/intervalo, com a saúde calculada pelo relógio do servidor.
export async function GET(){
 const body=await lookupWorkerStatus(statusReaderFromEnv(process.env,(url,init)=>fetch(url,init)),Date.now());
 return Response.json(body,{status:body.state==='ok'?200:503,headers:{'Cache-Control':'no-store'}});
}
