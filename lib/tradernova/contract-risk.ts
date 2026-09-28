export type RiskInput={direction:'Compra'|'Venda';entry:number;stop:number;target:number;tickSize:number;tickValue:number;volumeStep:number;minVolume:number;maxVolume:number;budget:number;roundTripCost:number;slippageTicks:number};
/** Linear contracts only. Tick value and budget must use the same account currency. */
export function planContractRisk(p:RiskInput){
 const positive=[p.entry,p.stop,p.target,p.tickSize,p.tickValue,p.volumeStep,p.minVolume,p.maxVolume,p.budget];
 if(positive.some(n=>!Number.isFinite(n)||n<=0)||![p.roundTripCost,p.slippageTicks].every(n=>Number.isFinite(n)&&n>=0)||!['Compra','Venda'].includes(p.direction))throw new Error('Preencha todos os valores com números válidos.');
 if(p.minVolume>p.maxVolume)throw new Error('O volume mínimo não pode superar o máximo.');
 const aligned=(v:number,step:number)=>Math.abs(v/step-Math.round(v/step))<1e-5;
 if(![p.entry,p.stop,p.target].every(v=>aligned(v,p.tickSize)))throw new Error('Entrada, stop e alvo precisam respeitar o tamanho do tick.');
 if(!aligned(p.minVolume,p.volumeStep)||!aligned(p.maxVolume,p.volumeStep))throw new Error('Volumes precisam respeitar o passo de quantidade.');
 const side=p.direction==='Compra'?1:-1,stopTicks=(p.entry-p.stop)*side/p.tickSize,targetTicks=(p.target-p.entry)*side/p.tickSize;
 if(stopTicks<=0||targetTicks<=0)throw new Error('Revise a posição do stop e do alvo para esta direção.');
 const cost=p.roundTripCost+2*p.slippageTicks*p.tickValue,riskPerUnit=stopTicks*p.tickValue+cost,rewardPerUnit=targetTicks*p.tickValue-cost;
 const maxAffordable=Math.min(p.maxVolume,p.budget/riskPerUnit);
 let quantity=Number((Math.floor((maxAffordable+1e-10)/p.volumeStep)*p.volumeStep).toPrecision(12));
 if(quantity*riskPerUnit>p.budget)quantity=Number(Math.max(0,quantity-p.volumeStep).toPrecision(12));
 if(quantity<p.minVolume)quantity=0;
 return {quantity,riskPerUnit,rewardPerUnit,risk:quantity*riskPerUnit,reward:quantity*rewardPerUnit,ratio:rewardPerUnit/riskPerUnit,stopTicks,targetTicks};
}
