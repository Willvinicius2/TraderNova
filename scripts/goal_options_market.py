"""Verified BTC/ETH development prices for N13; no signal computation."""
import importlib.util
import math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/goal-seven'
spec = importlib.util.spec_from_file_location('n13_io', ROOT / 'scripts/run-goal-directional.py')
io = importlib.util.module_from_spec(spec)
spec.loader.exec_module(io)
SYMBOLS = ('BTCUSDT', 'ETHUSDT')
START, END = io.epoch('2022-01-01'), io.epoch('2025-01-01')

def load_data():
    manifest = io.read(OUT / 'funding-data-manifest.json')
    perp, marks, funding = ({s: [] for s in SYMBOLS} for _ in range(3))
    for item in manifest['files']:
        if (item['symbol'] not in SYMBOLS or item['kind'] not in ('perp_h1', 'mark_h1')
                or not '2022-01' <= item['month'] < '2025-01'):
            continue
        if item['status'] != 'verified':
            raise ValueError('Unverified monthly derivative archive')
        target = perp if item['kind'] == 'perp_h1' else marks
        target[item['symbol']].extend(io.candle(row) for row in io.rows(
            io.checked_file(item['cachePath'], item['sha256'])))
    patch = io.read(OUT / 'mark-gap-data-manifest.json')
    additions = {s: [] for s in SYMBOLS}
    for symbol in SYMBOLS:
        marks[symbol].sort(key=lambda row: row['time'])
        io.quality(marks[symbol])  # Reject duplicates before building the merge index.
        marked = {row['time']: row for row in marks[symbol]}
        for item in patch['files']:
            if item['symbol'] != symbol or item['status'] != 'verified':
                continue
            for raw in io.rows(io.checked_file(item['cachePath'], item['sha256'])):
                row = io.candle(raw)
                if not START <= row['time'] < END:
                    raise ValueError('Patch outside development')
                if row['time'] in marked:
                    if any(row[k] != marked[row['time']][k] for k in ('open', 'high', 'low', 'close')):
                        raise ValueError('Daily/monthly mark conflict')
                else:
                    marked[row['time']] = row
                    additions[symbol].append(row['time'])
        marks[symbol] = sorted(marked.values(), key=lambda row: row['time'])
        perp[symbol].sort(key=lambda row: row['time'])
        if not manifest['apiFunding'][symbol]['matchedMonthlyArchive']:
            raise ValueError('Funding archive/API reconciliation missing')
        for page in manifest['apiFunding'][symbol]['pages']:
            events = io.read(io.checked_file(page['cachePath'], page['sha256']))
            for event in events:
                stamp = int(event['fundingTime'])
                if not START * 1000 <= stamp < END * 1000:
                    continue
                raw_mark = event.get('markPrice')
                mark = None if raw_mark in (None, '') else float(raw_mark)
                if mark is not None and (not math.isfinite(mark) or mark <= 0):
                    raise ValueError('Invalid funding mark')
                funding[symbol].append({'time_ms': stamp, 'rate': float(event['fundingRate']), 'mark_price': mark})
            if events and int(events[-1]['fundingTime']) >= END * 1000:
                break  # A frozen REST page may cross the boundary; later rates are never evaluated.
    market_audit = {kind: {s: io.quality(data[s]) for s in SYMBOLS}
                    for kind, data in (('perp', perp), ('mark', marks))}
    for kind in market_audit.values():
        for audit in kind.values():
            if (audit['gaps'] or audit['first'] != START or audit['last'] != END-3600
                    or audit['bars'] != (END-START)//3600):
                raise ValueError('Complete registered development prices required')
    return perp, marks, funding, {'market': market_audit, 'officialDailyMarkAdditions': additions}
