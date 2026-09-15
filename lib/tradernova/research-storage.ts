import {z} from 'zod';
import type {ResearchReport} from './research';
const n=z.number().finite(),positive=n.positive();
const bar=z.object({time:positive,open:positive,high:positive,low:positive,close:positive,volume:n.nonnegative()});
const trade=z.object({signalTime:positive,entryTime:positive,exitTime:positive,side:z.enum(['Compra','Venda']),entry:positive,exit:positive,stop:positive,target:positive,r:n,reason:z.string()});
const report=z.object({version:z.literal(1),id:z.string(),createdAt:positive,candidateId:z.enum(['T1','T2','T3']),assetId:z.enum(['XAUUSD','NAS100','BTCUSD','ETHUSD','SOLUSD','EURUSD','USDJPY']),source:z.enum(['kraken-spot','synthetic']),interval:z.number().int().positive(),start:positive,end:positive,warmup:n,costR:n,reward:n,stopAtr:n,maxHold:n,bars:z.array(bar).min(260).max(720),trades:z.array(trade).max(720),curve:z.array(n).min(1).max(721),netR:n,maxDrawdownR:n.nonnegative(),winRate:n.nullable(),profitFactor:n.nullable(),expectancyR:n.nullable(),sampleHash:z.string(),validated:z.literal(false)});
export const researchStorageKey='tradernova-research-v1';
export function parseResearchReports(value:unknown):ResearchReport[]{return Array.isArray(value)?value.slice(0,12).flatMap(v=>{const p=report.safeParse(v);return p.success?[p.data]:[];}):[];}
