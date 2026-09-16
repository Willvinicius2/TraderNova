"""Frozen, offline CFD research. Source files are never modified."""
import argparse,datetime as dt,hashlib,json,pathlib

ROOT=pathlib.Path(__file__).resolve().parent.parent
def sha(blob):return hashlib.sha256(blob).hexdigest()
def stamp(day):return int(dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc).timestamp())
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def summary(result):return {k:(len(v) if k=='trades' else v) for k,v in result.items() if k not in ['curve','daily']}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=pathlib.Path,required=True);args=parser.parse_args()
    protocol_path=ROOT/'research/gold-v1-protocol.json';raw_protocol=protocol_path.read_bytes();p=json.loads(raw_protocol)
    engine_files=['gold_signals.py','gold_execution.py','run_gold_research.py']
    engine_hashes={name:sha((ROOT/'scripts'/name).read_bytes()) for name in engine_files}
    from gold_signals import read_bars,make_signals
    import gold_execution as engine
    simulate=engine.simulate
    assert (engine.INITIAL_CAPITAL,engine.RISK_PER_TRADE,engine.DAILY_LOSS_LIMIT,engine.TOTAL_EQUITY_FLOOR)==(p['capital'],p['riskCash'],p['dailyLossLimit'],p['capital']-p['totalLossLimit'])
    assert (engine.CONTRACT_OZ,engine.LOT_STEP,engine.MAX_LOTS,engine.TICK_SIZE,engine.MIN_STOP_DISTANCE,engine.MAX_LEVERAGE)==tuple(p['contract'][key] for key in ['size','lotStep','maxLot','tickSize','minimumStopDistance','maxGrossLeverage'])
    for scenario in ['base','stress']:
        assert tuple(engine.COSTS[scenario][key] for key in ['spread','slippage','commissionPerLotRT'])==tuple(p['costs'][scenario][key] for key in ['spreadUsdPerOz','slippageUsdPerOzPerSide','commissionUsdPerLotRoundTrip'])
    reference=json.loads((args.source/'selection.json').read_text(encoding='utf-8'))
    source_hashes={}
    for name in ['M15','H1']:
        digest=sha((args.source/f'XAUUSD_{name}.csv').read_bytes())
        if digest!=reference['data_sha256'][name]:raise ValueError(f'Source changed: {name}')
        source_hashes[name]=digest
    bars=read_bars(args.source/'XAUUSD_M15.csv');higher=read_bars(args.source/'XAUUSD_H1.csv')
    cache=ROOT/'research/cache/gold-v1';cache.mkdir(parents=True,exist_ok=True)
    trials=[];chosen=[]
    def run(family,preset,window,scenario,signals=None):
        end=stamp(window[1]);sample=bars[bars['time']<end];context=higher[higher['time']+3600<=end]
        readings=signals if signals is not None else make_signals(sample,context,family,preset)
        return simulate(sample,readings,stamp(window[0]),end,scenario)
    for family in p['families']:
        rows=[]
        for preset in family['presets']:
            end=stamp(p['development'][1]);sample=bars[bars['time']<end]
            readings=make_signals(sample,higher[higher['time']+3600<=end],family['id'],preset)
            base=summary(run(family['id'],preset,p['development'],'base',readings));stress=summary(run(family['id'],preset,p['development'],'stress',readings))
            eligible=all(r['trades']>=100 and r['net']>0 and r['profitFactor'] is not None and r['profitFactor']>=1.1 and r['overnightUnpriced']==0 and r['maxDrawdown']>0 for r in [base,stress])
            score=stress['net']/stress['maxDrawdown'] if stress['maxDrawdown']>0 else -1e9
            row={'family':family['id'],'name':family['name'],'preset':preset,'base':base,'stress':stress,'eligible':eligible,'score':score}
            rows.append(row);trials.append(row)
        ranked=sorted([r for r in rows if r['eligible']] or rows,key=lambda r:(-r['score'],r['preset']))
        chosen.append(ranked[0]);print(f"{family['id']}: frozen preset {ranked[0]['preset']}, devEligible={ranked[0]['eligible']}, stressScore={ranked[0]['score']:.3f}",flush=True)
    def verify_inputs():
        assert engine_hashes=={name:sha((ROOT/'scripts'/name).read_bytes()) for name in engine_files},'Engine changed during research'
        assert sha(raw_protocol)==sha(protocol_path.read_bytes()),'Protocol changed during research'
        assert all(source_hashes[name]==sha((args.source/f'XAUUSD_{name}.csv').read_bytes()) for name in source_hashes),'Source changed during research'
    verify_inputs()
    frozen={'protocolHash':sha(raw_protocol),'sourceHashes':source_hashes,'engineHashes':engine_hashes,'trials':trials,'selection':chosen}
    selection_path=ROOT/'research/gold-v1-selection.json';write(selection_path,frozen)
    print('Selection saved before validation and retrospective final.',flush=True)
    results=[];public_outputs=[]
    for selected in chosen:
        family=selected['family'];preset=selected['preset'];reports={}
        for label,window in [('validation',p['validation']),('final',p['retrospectiveFinal'])]:
            end=stamp(window[1]);sample=bars[bars['time']<end]
            readings=make_signals(sample,higher[higher['time']+3600<=end],family,preset)
            for scenario in ['base','stress']:reports[f'{label}_{scenario}']=run(family,preset,window,scenario,readings)
        reasons=[]
        if not selected['eligible']:reasons.append('Desenvolvimento não passou nos critérios fixos')
        for label in ['validation','final']:
            base=reports[f'{label}_base'];stress=reports[f'{label}_stress']
            if len(base['trades'])<100:reasons.append(f'{label}: menos de 100 operações')
            if base['net']<=0:reasons.append(f'{label}: resultado líquido não positivo')
            if base['profitFactor'] is None or base['profitFactor']<1.2:reasons.append(f'{label}: fator de lucro inferior a 1,20')
            if base['maxDrawdown']>8000 or base['maxDailyClosedEquityLoss']>2000:reasons.append(f'{label}: queda acima do limite de pesquisa')
            if stress['net']<=0 or stress['maxDrawdown']>10000 or stress['maxDailyClosedEquityLoss']>3000:reasons.append(f'{label}: reprovação com custos elevados')
            if base['overnightUnpriced'] or stress['overnightUnpriced']:reasons.append(f'{label}: custo noturno não reconstruído')
        result={'family':family,'name':selected['name'],'preset':preset,'developmentEligible':selected['eligible'],'results':{k:summary(v) for k,v in reports.items()},'historicalScreenPassed':not reasons,'validated':False,'reasons':reasons,'pending':['Spreads e comissão executáveis do contrato','Regra diária e horário do programa','Teste prospectivo','Risco conjunto das estratégias']}
        results.append(result);write(cache/f'{family}.json',{'summary':result,**reports})
        public_reports={k:{**summary(v),'trades':v['trades']} for k,v in reports.items()}
        public_outputs.append((ROOT/f'public/research/gold-v1-{family}.json',{'summary':result,**public_reports}))
        print(f"{family}: V {reports['validation_base']['net']:.2f}, F {reports['final_base']['net']:.2f}, stressF {reports['final_stress']['net']:.2f}, screen={not reasons}",flush=True)
    verify_inputs()
    for path,payload in public_outputs:write(path,payload)
    report={'version':1,'id':p['id'],'generatedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'protocol':p,'protocolHash':sha(raw_protocol),'selectionHash':sha(selection_path.read_bytes()),'sourceHashes':source_hashes,'engineHashes':engine_hashes,'trials':trials,'selection':chosen,'results':results,'validated':False}
    write(ROOT/'public/research/gold-v1.json',report)
    table='\n'.join(f"| {r['family']} · {r['name']} | {r['preset']} | {r['results']['validation_base']['net']:.2f} | {r['results']['final_base']['net']:.2f} | {r['results']['final_base']['trades']} | {r['results']['final_base']['profitFactor']} | {r['results']['final_stress']['net']:.2f} | {'Passou' if r['historicalScreenPassed'] else 'Reprovada'} |" for r in results)
    (ROOT/'research/OURO_V1.md').write_text(f"# Ouro CFD · primeira rodada\n\nCinco famílias distintas, dois presets fixos por família. Seleção gravada antes das avaliações. Capital fictício US$100 mil e risco planejado US$250/trade.\n\n| Família | Preset | Líquido validação USD | Líquido final USD | Trades finais | PF final | Stress final USD | Filtro histórico |\n|---|---|---|---|---|---|---|---|\n{table}\n\n{p['limitations']}\n\nCustos base: spread fixo US$0,60/oz, slippage US$0,10 por lado e comissão US$10/lote ida e volta. Stress: US$1,20, US$0,25 e US$20. São cenários, não tarifas históricas verificadas. Fonte original somente leitura, hashes preservados. Horários nativos do servidor; saída às 20h45 conforme protocolo.\n",encoding='utf-8')

if __name__=='__main__':main()
