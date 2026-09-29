"""Frozen N11 historical screen; no orders and no independent-approval shortcut."""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from pathlib import Path

from goal_open_interest_signals import generate_signals
from goal_execution_v2 import simulate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/goal-seven'
spec = importlib.util.spec_from_file_location('directional_io', ROOT / 'scripts/run-goal-directional.py')
io = importlib.util.module_from_spec(spec)
spec.loader.exec_module(io)
SYMBOLS = ('BTCUSDT', 'ETHUSDT', 'SOLUSDT')
START, END = io.epoch('2022-01-01'), io.epoch('2025-01-01')


def align_and_audit_oi(rows, declared_rows):
    """Keep archive bytes unchanged; map slot start to the corroborated end label."""
    if len(rows) != declared_rows:
        raise ValueError('Normalized OI row count differs from manifest')
    previous = None
    indexed = {}
    for row in rows:
        raw_time = row['time']
        if (not isinstance(raw_time, int) or isinstance(raw_time, bool) or raw_time % 300
                or (previous is not None and raw_time <= previous)):
            raise ValueError('Invalid, duplicate or unordered normalized OI timestamp')
        previous = raw_time
        for field in ('sum_open_interest', 'sum_open_interest_value'):
            try:
                number = Decimal(row[field])
            except (InvalidOperation, TypeError, ValueError):
                raise ValueError('Invalid normalized OI value')
            if not number.is_finite() or number <= 0:
                raise ValueError('Nonpositive/nonfinite normalized OI value')
        end_time = raw_time + 300
        if START - 3600 <= end_time < END:
            indexed[end_time] = dict(row, observation_end=end_time)
    missing_hours = [t for t in range(START, END, 3600) if t not in indexed]
    audit = {'normalizedRows': len(rows), 'mappingSeconds': 300,
             'expectedRequiredHourlyPoints': (END - START) // 3600,
             'missingRequiredHourlyPoints': len(missing_hours),
             'firstMissingHourlyPoints': missing_hours[:16],
             'missingFiveMinutePoints': sum(t not in indexed for t in range(START, END, 300)),
             'requiredHourlyComplete': not missing_hours}
    return [row for time, row in indexed.items() if time % 3600 == 0], audit


def load_development():
    manifest = io.read(OUT / 'funding-data-manifest.json')
    perp, marks, funding, oi = ({s: [] for s in SYMBOLS} for _ in range(4))
    for item in manifest['files']:
        if item['kind'] not in ('perp_h1', 'mark_h1') or not '2022-01' <= item['month'] < '2025-01':
            continue
        if item['status'] != 'verified':
            raise ValueError('Unverified derivative archive')
        path = io.checked_file(item['cachePath'], item['sha256'])
        (perp if item['kind'] == 'perp_h1' else marks)[item['symbol']].extend(
            io.candle(row) for row in io.rows(path))
    for symbol in SYMBOLS:
        for target in (perp, marks):
            target[symbol].sort(key=lambda row: row['time'])
            io.quality(target[symbol])
        if not manifest['apiFunding'][symbol]['matchedMonthlyArchive']:
            raise ValueError('Funding REST/archive reconciliation missing')
        for page in manifest['apiFunding'][symbol]['pages']:
            events = io.read(io.checked_file(page['cachePath'], page['sha256']))
            for row in events:
                stamp = int(row['fundingTime'])
                if not START * 1000 <= stamp < END * 1000:
                    continue
                raw_mark = row.get('markPrice')
                mark = None if raw_mark in (None, '') else float(raw_mark)
                if mark is not None and (not math.isfinite(mark) or mark <= 0):
                    raise ValueError('Invalid funding settlement mark')
                funding[symbol].append({'time_ms': stamp, 'rate': float(row['fundingRate']), 'mark_price': mark})
            if events and int(events[-1]['fundingTime']) >= END * 1000:
                break  # A crossing REST page can include later rates; no later path is evaluated.
    source = io.read(OUT / 'open-interest-data-manifest.json')
    if (not source['acquisitionComplete'] or len(source['files']) != 3291
            or any(item['status'] != 'verified' for item in source['files'])):
        raise ValueError('Complete checksum-audited development acquisition required')
    normalized = [dict(item['normalized'], symbol=symbol) for symbol, item in source['series'].items()]
    if sorted(item['symbol'] for item in normalized) != sorted(SYMBOLS):
        raise ValueError('Expected exactly one OI source per authorized crypto symbol')
    oi_audit = {}
    clock_audit = io.read(OUT / 'open-interest-clock-offset-audit.json')
    prior_clock = OUT / 'open-interest-clock-audit.json'
    if (clock_audit['mappingSeconds'] != 300 or clock_audit['priorZeroOffsetAuditSha256'] != io.sha(prior_clock)
            or not all(v['allOverlappingQuantitiesEqual'] and v['allOverlappingNotionalsEqual']
                       for v in clock_audit['symbols'].values())):
        raise ValueError('Archive/statistical endpoint clock mapping not corroborated')
    for evidence in io.read(prior_clock)['symbols'].values():
        for key in ('archive', 'checksum', 'api'):
            io.checked_file(evidence[key]['path'], evidence[key]['sha256'])
    for item in normalized:
        rows = io.read(io.checked_file(item['path'], item['sha256']))
        oi[item['symbol']], oi_audit[item['symbol']] = align_and_audit_oi(rows, item['rows'])
    return perp, marks, funding, oi, oi_audit


def hashes():
    paths = [
        'research/goal-seven/protocol.json', 'research/goal-seven/open-interest-protocol.json',
        'research/goal-seven/open-interest-data-manifest.json', 'research/goal-seven/funding-data-manifest.json',
        'research/goal-seven/open-interest-clock-audit.json',
        'research/goal-seven/open-interest-clock-offset-audit.json', 'scripts/check-goal-oi-clock.py',
        'scripts/goal_open_interest_signals.py', 'tests/goal-open-interest-signals.py',
        'tests/goal-open-interest-integration.py',
        'scripts/goal_execution.py', 'scripts/run-goal-directional.py',
        'scripts/goal_execution_v2.py', 'tests/goal-execution-v2.py',
        'scripts/run-goal-open-interest.py', 'scripts/download-goal-open-interest.py',
    ]
    return {path: io.sha(ROOT / path) for path in paths}


def run_development(perp, marks, funding, signals, protocol, complete):
    outcomes = {}
    for scenario in ('base', 'stress'):
        path = ROOT / f'research/cache/goal-seven/N11-development-{scenario}.json'
        if path.exists():
            raise ValueError('Preserve existing development ledger before any audited revision')
        result = simulate(perp, marks, funding, signals, START, END, scenario)
        result['failures'] = io.gate(result, 100, scenario, protocol)
        if not complete:
            result['failures'].append('incomplete_open_interest_input_history')
        io.save(path, result)
        concise = {k: v for k, v in result.items() if k not in ('trades', 'daily', 'data_quality_flags')}
        concise['data_quality_flag_count'] = len(result['data_quality_flags'])
        concise['detail_path'] = path.relative_to(ROOT).as_posix()
        concise['detail_sha256'] = io.sha(path)
        outcomes[scenario] = concise
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'sample', 'development'))
    phase = parser.parse_args().phase
    perp, marks, funding, oi, oi_audit = load_development()
    snapshot = hashes()
    frozen = OUT / 'open-interest-freeze.json'
    if phase == 'prepare':
        if frozen.exists() and io.read(frozen)['hashes'] != snapshot:
            raise ValueError('An immutable N11 trial exists with different inputs')
        if not frozen.exists():
            io.save(frozen, {'frozenAtUtc': datetime.now(timezone.utc).isoformat(),
                            'hashes': snapshot, 'signalCountsPreviouslyViewed': False,
                            'performancePreviouslyViewed': False, 'historicalAssumption': True,
                            'validated': False,
                            'dataAudit': {kind: {s: io.quality(series[s]) for s in SYMBOLS}
                                          for kind, series in [('perp', perp), ('mark', marks)]},
                            'openInterestAudit': oi_audit})
        print('N11 inputs frozen before signal counts or performance.')
        return
    if not frozen.exists() or io.read(frozen)['hashes'] != snapshot:
        raise ValueError('Frozen N11 inputs required')
    signals = {time: row for time, row in generate_signals(perp, oi, historical_assumption=True)['N11'].items()
               if START <= time + 3600 < END}
    counts = {s: sum(row['symbol'] == s for row in signals.values()) for s in SYMBOLS}
    complete = all(v['requiredHourlyComplete'] for v in oi_audit.values())
    sample_path = OUT / 'open-interest-sample.json'
    if phase == 'sample':
        if sample_path.exists():
            raise ValueError('N11 sample already recorded; do not overwrite')
        result = {'family': 'N11', 'freezeSha256': io.sha(frozen), 'window': [START, END],
                  'qualifyingDecisionHours': len(signals), 'byPrioritySelectedSymbol': counts,
                  'sampleUpperBoundReached': len(signals) >= 100,
                  'inputHourlyComplete': complete, 'openInterestAudit': oi_audit,
                  'interpretation': 'Snapshot trigger count before overlapping positions, missing execution bars or stops; not trades.',
                  'PnLComputed': False, 'laterWindowsEvaluated': False, 'validated': False}
        io.save(sample_path, result)
        print(json.dumps(result, indent=2))
        return
    sample = io.read(sample_path)
    if (sample['freezeSha256'] != io.sha(frozen) or not sample['sampleUpperBoundReached']
            or len(signals) < 100 or sample['qualifyingDecisionHours'] != len(signals)
            or sample['byPrioritySelectedSymbol'] != counts or sample['openInterestAudit'] != oi_audit):
        raise ValueError('N11 sample failed or does not match frozen inputs')
    result_path = OUT / 'open-interest-results.json'
    if result_path.exists():
        raise ValueError('N11 development already recorded; do not overwrite')
    protocol = io.read(OUT / 'protocol.json')
    outcomes = run_development(perp, marks, funding, signals, protocol, complete)
    passed = not any(one['failures'] for one in outcomes.values())
    result = {'family': 'N11', 'freezeSha256': io.sha(frozen), 'sampleSha256': io.sha(sample_path),
              'development': outcomes, 'developmentPassed': passed, 'validated': False,
              'laterWindowsEvaluated': False, 'historicalPublicationAvailabilityAssumed': True,
              'inputHourlyComplete': complete, 'openInterestAudit': oi_audit,
              'decision': 'eligible_for_review_before_evaluation' if passed else 'rejected_in_development'}
    io.save(result_path, result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
