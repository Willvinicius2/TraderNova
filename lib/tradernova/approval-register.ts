import {z} from 'zod';
// Versioned approval register (#32). An entry can only be 'approved' with every gate of the protocol met;
// the register file is research/approval-register.json and starts empty. Nothing here sends orders.
const sha=z.string().regex(/^[0-9a-f]{64}$/);
export const approvalEntrySchema=z.object({
 strategyId:z.string().min(1).max(20),
 version:z.string().min(1).max(20),
 variantId:z.string().min(1).max(40),
 instruments:z.array(z.string().min(1).max(20)).min(1),
 protocol:z.object({file:z.string().min(1),sha256:sha}),
 selectionSha256:sha,
 engineSha256:sha,
 historical:z.object({passed:z.boolean(),report:z.string().min(1)}),
 contract:z.object({confirmed:z.boolean(),reference:z.string().max(200),costsWithinStress:z.boolean()}),
 forward:z.object({startedAt:z.number().int(),endedAt:z.number().int(),days:z.number(),trades:z.number().int().nonnegative(),maxDrawdownPct:z.number().nonnegative(),worstValidationDrawdownPct:z.number().positive(),parity:z.boolean(),violations:z.number().int().nonnegative()}),
 riskPctPerTrade:z.number().positive().max(1),
 status:z.enum(['approved','suspended','revoked']),
 decidedAt:z.number().int().nonnegative(),
 decidedBy:z.string().min(1).max(80),
 reason:z.string().max(500)
}).refine(e=>e.status!=='approved'||(e.historical.passed&&e.contract.confirmed&&e.contract.costsWithinStress&&e.forward.days>=30&&e.forward.trades>=10&&e.forward.maxDrawdownPct<=e.forward.worstValidationDrawdownPct&&e.forward.parity&&e.forward.violations===0&&e.forward.endedAt>e.forward.startedAt),{message:'Aprovação exige triagem histórica, contrato confirmado e forward test completo'});
export type ApprovalEntry=z.infer<typeof approvalEntrySchema>;
export const riskLimitsSchema=z.object({maxOpenRiskPct:z.number().positive().max(5),maxClusterRiskPct:z.number().positive().max(5),dailyLossLimitPct:z.number().positive().max(10),dailyBufferPct:z.number().nonnegative(),clusters:z.record(z.string(),z.array(z.string()))});
export type RiskLimits=z.infer<typeof riskLimitsSchema>;
export const approvalRegisterSchema=z.object({version:z.literal(1),updatedAt:z.string(),limits:riskLimitsSchema,entries:z.array(approvalEntrySchema)})
 .refine(r=>new Set(r.entries.map(e=>`${e.strategyId}@${e.version}`)).size===r.entries.length,{message:'Estratégia e versão repetidas'});
export type ApprovalRegister=z.infer<typeof approvalRegisterSchema>;

/** Distinct approved methods; assets of the same family count once toward the five-strategy goal. */
export function approvedCount(register:ApprovalRegister){return new Set(register.entries.filter(e=>e.status==='approved').map(e=>e.strategyId)).size;}
export function approvalFor(register:ApprovalRegister,strategyId:string,instrument:string){return register.entries.find(e=>e.status==='approved'&&e.strategyId===strategyId&&e.instruments.includes(instrument))??null;}

export type OpenRisk={strategyId:string;instrument:string;riskPct:number};
/** Joint risk: total open risk, correlated clusters and the daily loss floor if every open stop were hit. */
export function jointRiskCheck(register:ApprovalRegister,open:OpenRisk[],candidate:{strategyId:string;instrument:string},dailyLossSoFarPct:number){
 const reasons:string[]=[],entry=approvalFor(register,candidate.strategyId,candidate.instrument),l=register.limits;
 if(!entry)return {allowed:false,riskPct:0,reasons:['Estratégia não aprovada para este ativo']};
 const risk=entry.riskPctPerTrade,all=[...open,{...candidate,riskPct:risk}],total=all.reduce((s,o)=>s+o.riskPct,0);
 const cluster=(i:string)=>Object.entries(l.clusters).find(([,members])=>members.includes(i))?.[0]??i;
 if(open.some(o=>o.strategyId===candidate.strategyId&&o.instrument===candidate.instrument))reasons.push('Já existe posição desta estratégia neste ativo');
 if(total>l.maxOpenRiskPct+1e-9)reasons.push(`Risco aberto ${total.toFixed(2)}% acima de ${l.maxOpenRiskPct}%`);
 const same=all.filter(o=>cluster(o.instrument)===cluster(candidate.instrument)).reduce((s,o)=>s+o.riskPct,0);
 if(same>l.maxClusterRiskPct+1e-9)reasons.push(`Risco no grupo ${cluster(candidate.instrument)} ${same.toFixed(2)}% acima de ${l.maxClusterRiskPct}%`);
 if(dailyLossSoFarPct+total>l.dailyLossLimitPct-l.dailyBufferPct+1e-9)reasons.push('Todos os stops somados à perda do dia ultrapassariam o limite diário com folga');
 return {allowed:!reasons.length,riskPct:risk,reasons};
}
