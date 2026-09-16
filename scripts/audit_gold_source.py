"""Read-only provenance/OHLC audit. Does not compute strategy performance."""
import argparse, datetime as dt, hashlib, json
from pathlib import Path
import numpy as np
from gold_signals import read_bars


def audit(source):
    series = {name: read_bars(source / f'XAUUSD_{name}.csv') for name in ['M15', 'H1', 'H4']}
    reference = json.loads((source / 'selection.json').read_text(encoding='utf-8'))
    records = {}
    for name, bars in series.items():
        digest = hashlib.sha256((source / f'XAUUSD_{name}.csv').read_bytes()).hexdigest()
        assert digest == reference['data_sha256'][name], f'Source changed: {name}'
        seconds = {'M15': 900, 'H1': 3600, 'H4': 14400}[name]
        assert np.all(np.diff(bars['time']) > 0), f'Unordered/duplicate {name}'
        assert np.all(bars['time'] % seconds == 0), f'Unaligned {name}'
        assert np.all(np.isfinite([bars[k] for k in ['open', 'high', 'low', 'close']]))
        assert np.all(bars['low'] > 0)
        assert np.all(bars['low'] <= np.minimum(bars['open'], bars['close']))
        assert np.all(bars['high'] >= np.maximum(bars['open'], bars['close']))
        years = np.array([dt.datetime.fromtimestamp(int(t), dt.timezone.utc).year for t in bars['time']])
        rows = []
        for year in np.unique(years):
            group = bars[years == year]
            differences = np.diff(group['time'])
            rows.append({'year': int(year), 'bars': len(group),
                         'gapsOverNominalBar': int(sum(differences > seconds)),
                         'zeroSpread': int(sum(group['spread'] == 0))})
        records[name] = {'sha256': digest, 'bars': len(bars), 'firstBar': int(bars['time'][0]),
                         'lastBar': int(bars['time'][-1]), 'validOHLC': True, 'years': rows}
    m15, hourly = series['M15'], series['H1']
    complete = matched = 0
    max_difference = 0.
    for bar in hourly[hourly['time'] >= m15[0]['time']]:
        index = np.searchsorted(m15['time'], bar['time'])
        group = m15[index:index+4]
        if len(group) != 4 or not np.array_equal(group['time'], int(bar['time']) + np.arange(4)*900):
            continue
        complete += 1
        values = [group['open'][0], max(group['high']), min(group['low']), group['close'][-1]]
        difference = max(abs(float(bar[k])-value) for k, value in zip(['open','high','low','close'], values))
        max_difference = max(max_difference, difference)
        matched += int(difference <= .011)
    return {'series': records, 'overlap': {'completeHours': complete, 'matchedWithinTick': matched,
            'maxPriceDifference': max_difference}, 'limitations': [
                'Gaps include session breaks, weekends and holidays; no synthetic candles were inserted.',
                'Price consistency does not certify historical executable spreads or commission.',
                'Exported timestamp labels are not a verified UTC/session conversion.',
                'A provenance audit does not establish that research periods were previously untouched.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'bars': {key: item['bars'] for key, item in result['series'].items()}, 'overlap': result['overlap']}))
