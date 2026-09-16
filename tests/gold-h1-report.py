"""Verify frozen inputs, account accounting and unopened failed-candidate holdouts."""
import hashlib,json,math
from pathlib import Path

root=Path(__file__).resolve().parents[1]
read=lambda path:json.loads(path.read_text(encoding='utf-8'))
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
report=read(root/'public/research/gold-h1-v2.json')
selection=read(root/'research/gold-h1-v2-selection.json')
assert report['selectionHash']==sha(root/'research/gold-h1-v2-selection.json')
assert report['protocolHash']==sha(root/'research/gold-h1-v2-protocol.json')
assert report['protocol']==read(root/'research/gold-h1-v2-protocol.json')
assert report['trials']==selection['trials'] and report['selection']==selection['selection']
assert len(report['trials'])==7 and len(report['results'])==5
assert {r['family'] for r in report['results']}=={'G1','G2','G3','G4','G5'}
assert not report['validated']
audit=read(root/'research/gold-source-audit.json')
for name,digest in report['sourceHashes'].items():assert digest==audit['series'][name]['sha256']
for name,digest in report['engineHashes'].items():assert sha(root/'scripts'/name)==digest
count=0
for row in report['results']:
    candidates=[r for r in selection['trials'] if r['family']==row['family']]
    picked=sorted([r for r in candidates if r['eligible']] or candidates,key=lambda r:(-r['score'],r['variant']))[0]
    assert picked['variant']==row['variant'] and picked['eligible']==row['developmentEligible']
    assert row['holdoutEvaluated']==row['developmentEligible']
    assert row['historicalScreenPassed']==(not row['reasons']) and not row['validated']
    public=read(root/f"public/research/gold-h1-v2-{row['family']}.json")
    local=read(root/f"research/cache/gold-h1-v2/{row['family']}.json")
    assert public['summary']==local['summary']==row
    if not row['developmentEligible']:
        assert not row['historicalScreenPassed']
        assert not any(k.startswith(('validation_','reserve_')) for k in row['results'])
    for label,stats in row['results'].items():
        run=public[label];full=local[label]
        assert run['trades']==full['trades'] and len(run['trades'])==stats['trades']
        assert run['conservativeDrawdown']+1e-7>=run['observedClosedDrawdown']
        assert math.isclose(sum(t['net'] for t in run['trades']),stats['net'],abs_tol=1e-6)
        assert math.isclose(run['endingBalance'],100000+stats['net'],abs_tol=1e-6)
        last_exit=-1
        for t in run['trades']:
            assert t['signalCloseTime']==t['signalTime']+3600==t['entryTime']
            assert run['start']<=t['signalTime']<t['entryTime']<=t['exitTime']<=run['end']
            assert 8*3600<=t['entryTime']%86400<20*3600
            assert t['entryTime']>=last_exit and t['plannedRisk']<=250+1e-7
            assert .01<=t['lots']<=100 and abs(t['lots']*100-round(t['lots']*100))<1e-7
            cash=t['direction']*(t['exit']-t['entry'])*t['quantityOz']-t['commission']
            assert math.isclose(cash,t['net'],abs_tol=1e-6)
            last_exit=t['exitTime'];count+=1
        for record in full['daily']:
            assert record['referenceEquity']==max(record['referenceBalance'],record['referenceMarkedEquity'])
            assert math.isclose(record['lossLimit'],min(3000,.03*record['referenceEquity']),abs_tol=1e-8)
print(f'H1 report verified: seven trials, five families, frozen hashes and {count} exported trades reconciled.')
