"""N12: freeze inputs, count development triggers, then one gated net screen."""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from goal_execution_v3 import simulate
from goal_onchain_count_signals import DAY, HOUR, generate_signals, _index

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/goal-seven'
spec = importlib.util.spec_from_file_location('directional_io', ROOT / 'scripts/run-goal-directional.py')
io = importlib.util.module_from_spec(spec)
spec.loader.exec_module(io)
SYMBOLS = ('BTCUSDT', 'ETHUSDT')
START, END = io.epoch('2022-01-01'), io.epoch('2025-01-01')
SOURCE_START = io.epoch('2021-09-01')


def audit_daily(rows, expected_rows):
    if len(rows) != expected_rows:
        raise ValueError('Normalized count differs from manifest')
    indexed = _index(rows)
    if any(t < SOURCE_START or t >= END for t in indexed):
        raise ValueError('Daily observation outside registered acquisition window')
    missing = [t for t in range(SOURCE_START, END, DAY) if t not in indexed]
    return {'rows': len(rows), 'missingDays': missing, 'complete': not missing}


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
    source = io.read(OUT / 'onchain-count-data-manifest.json')
    if not source['acquisitionComplete'] or sorted(source['series']) != sorted(SYMBOLS):
        raise ValueError('Complete BTC/ETH acquisition required')
    for page in source['pages']:
        if page['status'] != 200:
            raise ValueError('Daily source request did not succeed')
        io.checked_file(page['rawPath'], page['sha256'])
    series, daily_audit = {}, {}
    for symbol in SYMBOLS:
        normalized = source['series'][symbol]['normalized']
        series[symbol] = io.read(io.checked_file(normalized['cachePath'], normalized['sha256']))
        daily_audit[symbol] = audit_daily(series[symbol], normalized['rows'])
    market_audit = {kind: {s: io.quality(data[s]) for s in SYMBOLS}
                    for kind, data in (('perp', perp), ('mark', marks))}
    return perp, marks, funding, series, {'daily': daily_audit, 'market': market_audit,
                                         'officialDailyMarkAdditions': additions}


def hashes():
    files = ['research/goal-seven/protocol.json', 'research/goal-seven/onchain-count-protocol.json',
             'research/goal-seven/onchain-count-data-manifest.json',
             'research/goal-seven/mark-gap-data-manifest.json',
             'research/goal-seven/funding-data-manifest.json',
             'scripts/download-goal-onchain-count.py', 'scripts/download-goal-mark-gaps.py',
             'scripts/goal_onchain_count_signals.py', 'tests/goal-onchain-count-signals.py',
             'scripts/goal_execution_v3.py', 'tests/goal-execution-v3.py',
             'scripts/run-goal-onchain-count.py', 'tests/goal-onchain-count-integration.py',
             'scripts/run-goal-directional.py', 'scripts/goal_execution.py', 'scripts/goal_signals.py']
    return {name: io.sha(ROOT / name) for name in files}


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def sample(signals, frozen_path, audit):
    return {'family': 'N12', 'freezeSha256': io.sha(frozen_path),
            'window': [START, END], 'qualifyingDecisionDays': len(signals),
            'byPrioritySelectedSymbol': {s: sum(r['symbol'] == s for r in signals.values()) for s in SYMBOLS},
            'sampleUpperBoundReached': len(signals) >= 100,
            'inputDailyComplete': all(a['complete'] for a in audit['daily'].values()),
            'interpretation': 'Daily triggers before execution, overlap and risk suspension; not closed trades.',
            'PnLComputed': False, 'laterWindowsEvaluated': False, 'validated': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['prepare', 'sample', 'development'])
    args = parser.parse_args()
    perp, marks, funding, series, audit = load_data()
    frozen_path = OUT / 'onchain-count-freeze.json'
    current = hashes()
    if args.phase == 'prepare':
        write_new(frozen_path, {'frozenAtUtc': datetime.now(timezone.utc).isoformat(), 'hashes': current,
                              'signalCountsPreviouslyViewed': False, 'performancePreviouslyViewed': False,
                              'dataAudit': audit, 'historicalAssumption': True, 'validated': False})
        print('N12 inputs frozen before signal counts or performance.')
        return
    frozen = io.read(frozen_path)
    if frozen['hashes'] != current or frozen['dataAudit'] != audit:
        raise ValueError('Frozen source or audit changed; preserve and register a revision')
    signals = {t: r for t, r in generate_signals(series, historical_assumption=True)['N12'].items()
               if START <= r['signal_close_time'] < END}
    counted = sample(signals, frozen_path, audit)
    sample_path = OUT / 'onchain-count-sample.json'
    if args.phase == 'sample':
        write_new(sample_path, counted)
        print(json.dumps(counted, indent=2))
        return
    if (io.read(sample_path) != counted or not counted['sampleUpperBoundReached']
            or not counted['inputDailyComplete']):
        raise ValueError('Frozen matching sample of at least 100 triggers and complete daily inputs required before PnL')
    result_path = OUT / 'onchain-count-results.json'
    if result_path.exists():
        raise ValueError('Results already exist; never overwrite frozen results')
    protocol = io.read(OUT / 'protocol.json')
    results = {}
    for scenario in ('base', 'stress'):
        result = simulate(perp, marks, funding, signals, START, END, scenario)
        result['failures'] = io.gate(result, 100, scenario, protocol)
        if not counted['inputDailyComplete']:
            result['failures'].append('incomplete_native_transfer_input_history')
        path = ROOT / f'research/cache/goal-seven/N12-development-{scenario}.json'
        write_new(path, result)
        results[scenario] = {k: v for k, v in result.items() if k not in ('trades', 'daily', 'data_quality_flags')}
        results[scenario].update(detail_path=path.relative_to(ROOT).as_posix(), detail_sha256=io.sha(path),
                                 data_quality_flag_count=len(result['data_quality_flags']))
    passed = all(not r['failures'] for r in results.values())
    report = {'family': 'N12', 'freezeSha256': io.sha(frozen_path), 'sampleSha256': io.sha(sample_path),
              'development': results, 'developmentPassed': passed, 'validated': False,
              'laterWindowsEvaluated': False, 'historicalPublicationAvailabilityAssumed': True,
              'decision': 'candidate_for_further_screening' if passed else 'rejected_in_development'}
    write_new(result_path, report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
