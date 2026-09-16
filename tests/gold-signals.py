"""Causality and symmetry checks against an explicitly supplied offline export."""
import argparse,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from gold_signals import read_bars,make_signals

parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);args=parser.parse_args()
bars=read_bars(args.source/'XAUUSD_M15.csv')[:4096]
h1=read_bars(args.source/'XAUUSD_H1.csv');h1=h1[(h1['time']>=bars['time'][0]-600*3600)&(h1['time']<=bars['time'][-1])]
def mirror(sample):
    out=sample.copy()
    for name in ['open','close']:out[name]=10000-sample[name]
    out['high']=10000-sample['low'];out['low']=10000-sample['high'];return out
checks=0
for family,presets in [('G1',[20,50]),('G2',[60,120]),('G3',[2,2.5]),('G4',[.1,.25]),('G5',[2,3])]:
    for preset in presets:
        full=make_signals(bars,h1,family,preset)
        assert any(full),f'{family}/{preset}: fixture must exercise an actual signal'
        for cut in [600,1201,2037,3000,4001]:
            prefix=make_signals(bars[:cut],h1[h1['time']+3600<=bars['time'][cut-1]+900],family,preset)
            assert prefix==full[:cut],f'{family}/{preset}: future-data dependence at {cut}'
            checks+=1
        reverse=make_signals(mirror(bars),mirror(h1),family,preset)
        assert [s is not None for s in full]==[s is not None for s in reverse],f'{family}/{preset}: asymmetric signal timing'
        for long,short in zip(full,reverse):
            if long:
                assert long['direction']==-short['direction']
                assert abs(long['stop']+short['stop']-10000)<1e-7
                assert 8*3600<=(long['signalTime']+900)%86400<20*3600
                if family=='G2':assert (long['signalTime']+900)%86400<12*3600
        checks+=1
print(f'{checks} gold signal checks passed: nonempty presets, causal prefixes, long/short symmetry and entry hours.')
