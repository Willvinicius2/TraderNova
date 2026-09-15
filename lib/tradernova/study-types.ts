import type {HistoricalResult} from './historical';
import type {CandidateId} from './research';
export type StudyRun=Omit<HistoricalResult,'trades'>&{trades:number};
export type StudyRow={id:string;candidateId:CandidateId;symbol:string;interval:number;sampleHash:string;status:'rejected'|'forward-candidate';reasons:string[];windows:Record<'development'|'validation'|'final',StudyRun>;stress:StudyRun;downloadUrl:string;validated:false};
export type HistoricalStudy={version:1;id:string;generatedAt:string;source:string;manifestUrl:string;results:StudyRow[];validated:false};
export function isHistoricalStudy(value:unknown):value is HistoricalStudy{
 if(!value||typeof value!=='object')return false;
 const s=value as HistoricalStudy;
 return s.version===1&&s.validated===false&&typeof s.generatedAt==='string'&&s.manifestUrl==='/research/manifest.json'&&Array.isArray(s.results)&&s.results.length===18&&s.results.every(r=>r&&['T1','T2','T3'].includes(r.candidateId)&&['BTCUSDT','ETHUSDT','SOLUSDT'].includes(r.symbol)&&[15,60].includes(r.interval)&&r.validated===false&&typeof r.sampleHash==='string'&&/^[a-f0-9]{64}$/.test(r.sampleHash)&&Array.isArray(r.reasons)&&r.reasons.every(v=>typeof v==='string')&&['development','validation','final'].every(k=>{const w=r.windows?.[k as keyof typeof r.windows];return w&&[w.net,w.returnPct,w.trades,w.maxDrawdownPct].every(Number.isFinite)&&w.options?.candidateId===r.candidateId&&w.options.interval===r.interval;}));
}
