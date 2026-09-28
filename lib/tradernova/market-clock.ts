/** Exchange time anchored to a monotonic clock. Never infer time from a trade. */
export type ClockSample={serverAt:number;monotonicAt:number;uncertaintyMs:number};
export function clockSample(timeIn:unknown,timeOut:unknown,sent:number,received:number):ClockSample|null{
 const incoming=typeof timeIn==='string'?Date.parse(timeIn):NaN,outgoing=typeof timeOut==='string'?Date.parse(timeOut):NaN;
 const roundTrip=received-sent,processing=outgoing-incoming;
 if(![incoming,outgoing,sent,received].every(Number.isFinite)||incoming<=0||roundTrip<0||roundTrip>2000||processing<0||processing>roundTrip+2)return null;
 const network=Math.max(0,roundTrip-processing);
 return {serverAt:outgoing+network/2,monotonicAt:received,uncertaintyMs:network/2+1};
}
let sample:ClockSample|null=null;
export function syncMarketClock(timeIn:unknown,timeOut:unknown,sent:number,received=performance.now()){
 const next=clockSample(timeIn,timeOut,sent,received);if(!next)return false;sample=next;return true;
}
export function marketClockReady(monotonic=performance.now()){return !!sample&&monotonic>=sample.monotonicAt&&monotonic-sample.monotonicAt<=90000;}
export function marketNow(){return sample?sample.serverAt+performance.now()-sample.monotonicAt:Date.now();}
