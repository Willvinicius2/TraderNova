"""Check closed-candle H1 decisions without calculating strategy PnL."""
import argparse,sys
from pathlib import Path
import numpy as np
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from gold_signals import read_bars
from gold_h1_signals import make_signals

parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,required=True)
args=parser.parse_args()
bars=read_bars(args.source/'XAUUSD_H1.csv')[:18000]
h4=read_bars(args.source/'XAUUSD_H4.csv')
h4=h4[h4['time']+14400<=bars['time'][-1]+3600]

def mirror(sample):
    out=sample.copy()
    for name in ['open','close']:out[name]=10000-sample[name]
    out['high']=10000-sample['low'];out['low']=10000-sample['high']
    return out

checks=0
for family in ['G1','G2','G3','G4','G5']:
    for variant in (['control','confirmation'] if family in ['G2','G4'] else ['control']):
        full=make_signals(bars,h4,family,variant)
        assert any(full),f'{family}/{variant}: fixture needs real signals'
        for cut in [2049,4096,8193,12000,17001]:
            prefix=make_signals(bars[:cut],h4[h4['time']+14400<=bars['time'][cut-1]+3600],family,variant)
            assert prefix==full[:cut],f'{family}/{variant}: future data altered earlier decision'
            checks+=1
        reverse=make_signals(mirror(bars),mirror(h4),family,variant)
        assert [s is not None for s in full]==[s is not None for s in reverse],f'{family}/{variant}: direction bias'
        for i,(one,two) in enumerate(zip(full,reverse)):
            if one:
                assert one['direction']==-two['direction']
                assert abs(one['stop']+two['stop']-10000)<1e-7
                assert abs(one['target']+two['target']-10000)<1e-7
                assert 8*3600<=(one['signalTime']+3600)%86400<20*3600
                assert bars['time'][i]-bars['time'][i-1]==3600
                if family=='G2':assert (one['signalTime']+3600)%86400<14*3600
        checks+=1
# A candle crossing the entire previous-day range is not a return inside it.
origin=int(datetime(2020,1,1,tzinfo=timezone.utc).timestamp())
times=[origin+h*3600 for h in range(1,24)]+[origin+86400+h*3600 for h in range(1,9)]
fixture=np.array([(t,100.,101.,99.,100.,0) for t in times],dtype=bars.dtype)
fixture[-1]=(times[-1],99.5,100.7,98.6,100.5,0)
assert make_signals(fixture,fixture[::4],'G4')[-1] is not None
fixture[-1]=(times[-1],99.5,102.1,98.6,102.,0)
assert make_signals(fixture,fixture[::4],'G4')[-1] is None
assert make_signals(mirror(fixture),mirror(fixture[::4]),'G4')[-1] is None
checks+=3
print(f'{checks} H1 signal checks passed: nonempty configurations, causal prefixes, mirrored prices, entry hours and inside-range rejections.')
