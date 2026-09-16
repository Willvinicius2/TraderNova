"""Audit selection, published metrics, source code hashes and approval gates."""
import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
report=json.loads((root/'public/research/gold-v1.json').read_text(encoding='utf-8'))
frozen_bytes=(root/'research/gold-v1-selection.json').read_bytes();frozen=json.loads(frozen_bytes)
assert sha(frozen_bytes)==report['selectionHash']
assert sha((root/'research/gold-v1-protocol.json').read_bytes())==report['protocolHash']
for file,digest in report['engineHashes'].items():assert sha((root/'scripts'/file).read_bytes())==digest,file
assert len(report['trials'])==10 and len(report['results'])==5
for selected,row in zip(report['selection'],report['results']):
    trials=[r for r in frozen['trials'] if r['family']==selected['family']]
    expected=sorted([r for r in trials if r['eligible']] or trials,key=lambda r:(-r['score'],r['preset']))[0]
    assert selected==expected and row['preset']==expected['preset']
    assert all(r['base']['end']<=1735689600 and r['stress']['end']<=1735689600 for r in trials)
    assert row['validated'] is False and row['historicalScreenPassed']==(len(row['reasons'])==0)
    if not selected['eligible']:assert not row['historicalScreenPassed']
    raw=json.loads((root/f"public/research/gold-v1-{row['family']}.json").read_text(encoding='utf-8'))
    for key,metrics in row['results'].items():
        trades=raw[key]['trades']
        assert len(trades)==metrics['trades']
        assert abs(sum(t['net'] for t in trades)-metrics['net'])<1e-6
        assert all(t['plannedRisk']<=250.000001 and t['signalTime']<t['entryTime']<=t['exitTime'] for t in trades)
print('Gold report checks passed: frozen selection, code/protocol hashes, window isolation, cash reconciliation and no false approvals.')
