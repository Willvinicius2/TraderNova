'use client';
import {useEffect,useState} from 'react';
import {Download} from 'lucide-react';
import {Table,TableHeader,TableBody,TableRow,TableHead,TableCell} from '@/components/ui/table';

type Run={net:number;trades:number;profitFactor:number|null;conservativeDrawdown:number;maxDailyConservativeEquityLoss:number;accountBreached:boolean};
type Row={family:string;name:string;variant:'control'|'confirmation';developmentEligible:boolean;holdoutEvaluated:boolean;historicalScreenPassed:boolean;validated:false;results:Record<string,Run>};
type Report={id:'gold-h1-v2';version:2;validated:false;results:Row[]};
const number=(n:number|null)=>n===null?'—':n.toLocaleString('pt-BR',{maximumFractionDigits:2});

export function GoldH1ResearchResults(){
 const [report,setReport]=useState<Report|null>(null),[error,setError]=useState('');
 useEffect(()=>{
  const controller=new AbortController();
  fetch('/research/gold-h1-v2.json',{signal:controller.signal}).then(async response=>{
   if(!response.ok)throw Error('Pesquisa H1 indisponível.');
   const value=await response.json() as Report;
   if(value.id!=='gold-h1-v2'||value.version!==2||value.validated!==false||value.results?.length!==5||new Set(value.results.map(r=>r.family)).size!==5||value.results.some(r=>r.validated!==false||!['G1','G2','G3','G4','G5'].includes(r.family)||!['development_base','development_stress','recent_base','trailing_base'].every(key=>{
    const run=r.results?.[key];return run&&[run.net,run.trades,run.conservativeDrawdown,run.maxDailyConservativeEquityLoss].every(Number.isFinite);
   })))throw Error('Pesquisa H1 inconsistente.');
   setReport(value);
  }).catch(e=>{if(!controller.signal.aborted)setError(e.message);});
  return()=>controller.abort();
 },[]);
 if(error)return <p role="alert" className="research-error">{error}</p>;
 if(!report)return <p className="micro">Carregando a rodada H1…</p>;
 const advanced=report.results.filter(r=>r.developmentEligible).length;
 return <section className="panel padded historical-study">
  <div className="section-heading"><div><h2>Calibração de ouro · H1</h2><p className="micro">Sete configurações · cinco métodos · seleção encerrada</p></div><a className="text-button" href="/research/gold-h1-v2.json" download="TraderNova_Ouro_H1.json"><Download size={16}/>Exportar estudo</a></div>
  <p className="notice">{advanced} de 5 métodos passaram no desenvolvimento. {advanced===0?'Os períodos reservados de 2016–2021 não foram abertos para essas candidatas.':'As candidatas elegíveis avançaram para os períodos reservados.'} Nenhuma estratégia desta rodada está aprovada para operar.</p>
  <details className="research-rules"><summary>Resultados e critérios desta rodada</summary>
   <p>Histórico H1 conferido desde 2009. Desenvolvimento: 2010–2015. Os resultados recentes abaixo são diagnósticos de períodos já conhecidos; não recuperam uma candidata reprovada.</p>
   <Table><TableHeader><TableRow><TableHead>Método selecionado</TableHead><TableHead>Desenvolvimento / custos elevados</TableHead><TableHead>Jan/2022–ago/2026</TableHead><TableHead>Jan/2025–ago/2026</TableHead><TableHead>Trades / PF recente</TableHead><TableHead>Operações</TableHead></TableRow></TableHeader><TableBody>{report.results.map(row=>{
    const development=row.results.development_base,stress=row.results.development_stress,recent=row.results.recent_base,trailing=row.results.trailing_base;
    return <TableRow key={row.family}><TableCell>{row.name}<p className="micro">{row.variant==='confirmation'?'Confirmação posterior':'Controle H1'}</p></TableCell><TableCell>US$ {number(development.net)} / US$ {number(stress.net)}</TableCell><TableCell>US$ {number(recent.net)}</TableCell><TableCell>US$ {number(trailing.net)}</TableCell><TableCell>{trailing.trades} / {number(trailing.profitFactor)}</TableCell><TableCell><a className="text-button" href={`/research/gold-h1-v2-${row.family}.json`} download={`TraderNova_H1_${row.family}.json`} aria-label={`Exportar operações H1 ${row.name}`}><Download size={16}/></a></TableCell></TableRow>;
   })}</TableBody></Table>
   <p>Conta simulada de US$ 100 mil, risco de até US$ 250 por operação, saída às 20h no relógio exportado. O modelo usa a referência diária do Summer 2-Step, limitada também ao teto informado de US$ 3 mil. Atingir o limite bloqueia novas entradas nos dias seguintes.</p>
   <p>Custos mantidos: spread de US$ 0,60 por onça, slippage de US$ 0,10 por lado e comissão de US$ 10 por lote completo; cenário elevado de US$ 1,20, US$ 0,25 e US$ 20. São hipóteses explícitas de pesquisa, ainda sem certificação dos custos executáveis da conta.</p>
   <p>A aprovação histórica exige desenvolvimento positivo em ambos os cenários, pelo menos 100 operações em cada avaliação, lucro líquido, fator de lucro ≥ 1,20 e limites de perda atendidos. A estimativa de perda dentro da vela é separada da perda observada nos fechamentos. Também faltam acompanhamento prospectivo e avaliação do risco conjunto.</p>
  </details>
 </section>;
}
