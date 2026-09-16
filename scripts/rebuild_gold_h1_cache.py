"""Reproduce frozen development selections without overwriting their manifest."""
import argparse,datetime as dt,hashlib,json
from pathlib import Path
from gold_signals import read_bars
from gold_h1_signals import make_signals
from gold_h1_execution import simulate

ROOT=Path(__file__).resolve().parents[1]
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
summary=lambda run:{k:(len(v) if k=='trades' else v) for k,v in run.items() if k not in ['curve','daily']}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'research/cache/gold-h1-v2')
    args=parser.parse_args()
    frozen=json.loads((ROOT/'research/gold-h1-v2-selection.json').read_text(encoding='utf-8'))
    protocol=json.loads((ROOT/'research/gold-h1-v2-protocol.json').read_text(encoding='utf-8'))
    assert sha(ROOT/'research/gold-h1-v2-protocol.json')==frozen['protocolHash']
    assert all(sha(ROOT/'scripts'/name)==digest for name,digest in frozen['engineHashes'].items())
    assert all(sha(args.source/f'XAUUSD_{name}.csv')==digest for name,digest in frozen['sourceHashes'].items())
    start,end=[int(dt.datetime.fromisoformat(value).replace(tzinfo=dt.timezone.utc).timestamp()) for value in protocol['development']]
    bars=read_bars(args.source/'XAUUSD_H1.csv');bars=bars[bars['time']<end]
    higher=read_bars(args.source/'XAUUSD_H4.csv');higher=higher[higher['time']+14400<=end]
    args.output.mkdir(parents=True,exist_ok=True)
    for row in frozen['selection']:
        signals=make_signals(bars,higher,row['family'],row['variant'])
        pair={scenario:simulate(bars,signals,start,end,scenario) for scenario in ['base','stress']}
        assert all(summary(pair[key])==row[key] for key in pair),f"Frozen result mismatch: {row['family']}"
        target=args.output/f"development-{row['family']}-{row['variant']}.json"
        if target.exists():
            assert json.loads(target.read_text(encoding='utf-8'))==pair,'Existing cache differs; not overwritten'
        else:
            with target.open('x',encoding='utf-8') as stream:
                json.dump(pair,stream,ensure_ascii=False,indent=2,allow_nan=False)
        print(f"{row['family']}: exact development reproduction confirmed",flush=True)
