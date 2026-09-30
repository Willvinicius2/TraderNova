import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const read=p=>JSON.parse(readFileSync(new URL(`../${p}`,import.meta.url),'utf8').replace(/^\uFEFF/,''));
const sha=p=>createHash('sha256').update(readFileSync(new URL(`../${p}`,import.meta.url))).digest('hex');
const plan=read('public/research/validation-plan.json'),protocol=read('research/validation/protocol.json');
assert.deepEqual(plan.protocol,protocol);
assert.equal(sha(protocol.supersedes.path),protocol.supersedes.sha256,'Previous frozen protocol must remain intact');
const old=read(protocol.supersedes.path);
for(const key of ['screenGates','prospectiveGate','statisticalGate','counting','execution','independence','selection','windows','directionalRiskPct','directionalGrossExposurePct'])assert.deepEqual(protocol[key],old[key],`${key} cannot be relaxed to obtain five passes`);
assert.equal(plan.target,7);assert.equal(plan.validatedCount,0);assert.equal(plan.validated,false);
assert.deepEqual(plan.candidates,read('research/validation/candidates.json').candidates);
assert(plan.candidates.length>=7);
for(const id of ['N16','N17','N18','N19','N20','N21','N22'])assert(plan.candidates.some(c=>c.id===id));
assert.equal(new Set(plan.candidates.map(c=>c.family)).size,plan.candidates.length);
assert.equal(plan.supervision.state,'active_research');
assert.equal(plan.supervision.limits.maxScheduledChecks,undefined);
assert.equal(plan.supervision.limits.maxUnchangedRounds,undefined);
assert.equal(plan.supervision.limits.maxAttemptsPerDay,undefined);
assert.equal(plan.supervision.limits.maxAttemptsPerRound,2);
for(const c of plan.candidates){assert.equal(c.status,'awaiting_data');assert(c.requiredData.length);assert(c.references.every(r=>r.url.startsWith('https://')));assert(c.assets.every(a=>protocol.assets.includes(a)));}
for(const s of plan.sources)assert.equal(s.sha256,sha(s.path),'Published source hash must match the preserved report');
const result=read('research/goal-seven/options-skew-results.json');
const n13=plan.results.find(r=>r.id==='N13');
assert.equal(result.laterWindowsEvaluated,false);assert.equal(n13.status,result.decision);
for(const scenario of ['base','stress']){assert.equal(n13[scenario].netPct,result.development[scenario].net_pct);assert.equal(n13[scenario].drawdownPct,result.development[scenario].max_drawdown_pct);assert.equal(n13[scenario].trades,result.development[scenario].trade_count);}
assert.equal(plan.results.length,9);assert(plan.results.every(r=>r.status==='rejected_in_development'));
console.log('Validation plan: unchanged gates, preserved protocol hash, distinct hypotheses and continued research passed.');
