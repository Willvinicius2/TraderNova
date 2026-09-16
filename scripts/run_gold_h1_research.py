"""Two-phase, frozen H1 study. Reads offline CSVs only. Never initializes MT5."""
import argparse,datetime as dt,hashlib,json,pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
FILES=['gold_signals.py','gold_h1_signals.py','gold_h1_execution.py','run_gold_h1_research.py']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def stamp(value):return int(dt.datetime.fromisoformat(value).replace(tzinfo=dt.timezone.utc).timestamp())
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def summary(run):return {key:(len(value) if key=='trades' else value) for key,value in run.items() if key not in ['curve','daily']}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=pathlib.Path,required=True)
    parser.add_argument('--phase',choices=['develop','evaluate'],required=True)
    args=parser.parse_args()
    from gold_signals import read_bars
    from gold_h1_signals import make_signals
    import gold_h1_execution as engine
    protocol_path=ROOT/'research/gold-h1-v2-protocol.json'
    protocol=json.loads(protocol_path.read_text(encoding='utf-8'))
    hashes={'protocolHash':sha(protocol_path),'engineHashes':{name:sha(ROOT/'scripts'/name) for name in FILES},
            'sourceHashes':{name:sha(args.source/f'XAUUSD_{name}.csv') for name in ['H1','H4']}}
    source_reference=json.loads((args.source/'selection.json').read_text(encoding='utf-8'))
    assert all(digest==source_reference['data_sha256'][name] for name,digest in hashes['sourceHashes'].items()),'Source hash mismatch'
    assert engine.BAR_SECONDS==protocol['barSeconds'] and engine.INITIAL_CAPITAL==protocol['capital'] and engine.RISK_PER_TRADE==protocol['riskCash']
    assert engine.COSTS==protocol['costs'],'Cost scenarios differ from preregistration'
    bars,higher=(read_bars(args.source/f'XAUUSD_{name}.csv') for name in ['H1','H4'])
    cache=ROOT/'research/cache/gold-h1-v2'
    cache.mkdir(parents=True,exist_ok=True)
    selection_path=ROOT/'research/gold-h1-v2-selection.json'

    def verify():
        assert hashes['protocolHash']==sha(protocol_path),'Protocol changed during run'
        assert hashes['engineHashes']=={name:sha(ROOT/'scripts'/name) for name in FILES},'Code changed during run'
        assert hashes['sourceHashes']=={name:sha(args.source/f'XAUUSD_{name}.csv') for name in ['H1','H4']},'Source changed during run'

    def run_pair(family,variant,window):
        end=stamp(window[1]);sample=bars[bars['time']<end]
        signals=make_signals(sample,higher[higher['time']+14400<=end],family,variant)
        return {scenario:engine.simulate(sample,signals,stamp(window[0]),end,scenario) for scenario in ['base','stress']}

    if args.phase=='develop':
        if selection_path.exists():raise RuntimeError('Selection is already frozen; use evaluate. A new hypothesis needs a new study ID.')
        trials=[];chosen=[]
        for family in protocol['families']:
            rows=[]
            for variant in family['variants']:
                pair=run_pair(family['id'],variant,protocol['development'])
                base,stress=(summary(pair[key]) for key in ['base','stress'])
                eligible=all(r['trades']>=100 and r['net']>0 and r['profitFactor'] is not None and r['profitFactor']>=1.1 and r['overnightUnpriced']==0 and not r['accountBreached'] and r['conservativeDrawdown']>0 for r in [base,stress])
                score=stress['net']/stress['conservativeDrawdown'] if stress['conservativeDrawdown']>0 else -1e9
                row={'family':family['id'],'name':family['name'],'variant':variant,'base':base,'stress':stress,'eligible':eligible,'score':score}
                rows.append(row);trials.append(row)
                write(cache/f"development-{family['id']}-{variant}.json",pair)
                print(f"{family['id']} {variant}: dev base={base['net']:.2f}, stress={stress['net']:.2f}, n={base['trades']}, eligible={eligible}",flush=True)
            chosen.append(sorted([r for r in rows if r['eligible']] or rows,key=lambda r:(-r['score'],r['variant']))[0])
        verify()
        write(selection_path,{'id':protocol['id'],**hashes,'trials':trials,'selection':chosen})
        print('Selection frozen. Evaluation has NOT run.',flush=True)
        return

    frozen=json.loads(selection_path.read_text(encoding='utf-8'))
    assert all(frozen[key]==value for key,value in hashes.items()),'Frozen inputs changed: do not reuse a viewed evaluation after editing code'
    results=[];outputs=[]
    for selected in frozen['selection']:
        family,variant=selected['family'],selected['variant']
        development=json.loads((cache/f'development-{family}-{variant}.json').read_text(encoding='utf-8'))
        assert all(summary(development[k])==selected[k] for k in ['base','stress']),'Development cache changed'
        reports={f'development_{k}':v for k,v in development.items()}
        reasons=[]
        labels=[('validation','validation'),('reserve','retrospectiveReserve'),('recent','knownRecent'),('trailing','knownTrailing')]
        if not selected['eligible']:reasons.append('Desenvolvimento reprovado; validação e reserva não foram abertas para esta candidata')
        for label,window in labels:
            if label in ['validation','reserve'] and not selected['eligible']:
                continue
            pair=run_pair(family,variant,protocol[window])
            reports.update({f'{label}_{key}':value for key,value in pair.items()})
            base,stress=pair['base'],pair['stress']
            if len(base['trades'])<100:reasons.append(f'{label}: menos de100operações')
            if base['net']<=0:reasons.append(f'{label}: líquido não positivo')
            if base['profitFactor'] is None or base['profitFactor']<1.2:reasons.append(f'{label}: fator de lucro abaixo de1,20')
            if base['conservativeDrawdown']>8000 or base['maxDailyConservativeEquityLoss']>2000:reasons.append(f'{label}: queda conservadora acima do limite')
            if stress['net']<=0 or stress['conservativeDrawdown']>10000 or stress['maxDailyConservativeEquityLoss']>3000:reasons.append(f'{label}: reprovada com custos elevados')
            if any(r['overnightUnpriced'] or r['accountBreached'] for r in pair.values()):reasons.append(f'{label}: violação da conta ou custo noturno não reconstruído')
        result={'family':family,'name':selected['name'],'variant':variant,'developmentEligible':selected['eligible'],
                'holdoutEvaluated':selected['eligible'],'historicalScreenPassed':not reasons,'validated':False,
                'reasons':reasons,'results':{key:summary(value) for key,value in reports.items()},'pending':protocol['remainingBeforeOperation']}
        results.append(result)
        write(cache/f'{family}.json',{'summary':result,**reports})
        outputs.append((ROOT/f'public/research/gold-h1-v2-{family}.json',{'summary':result,**{key:{**summary(value),'trades':value['trades']} for key,value in reports.items()}}))
        print(f"{family}/{variant}: devEligible={selected['eligible']}, recent={reports['recent_base']['net']:.2f}, trailing={reports['trailing_base']['net']:.2f}, screen={not reasons}",flush=True)
    verify()
    for path,value in outputs:write(path,value)
    report={'id':protocol['id'],'version':2,'generatedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'validated':False,
            'protocol':protocol,**hashes,'selectionHash':sha(selection_path),'trials':frozen['trials'],'selection':frozen['selection'],'results':results}
    write(ROOT/'public/research/gold-h1-v2.json',report)

if __name__=='__main__':main()
