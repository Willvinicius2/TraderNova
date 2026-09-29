"""Audited acquisition -> frozen inputs -> development -> gated evaluation.

This runner never approves a strategy. Reused history can only reject a rule or
nominate a candidate for genuinely independent, prospective observation.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from goal_execution import simulate
from goal_signals import generate_signals

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/goal-seven'
DETAIL = ROOT / 'research/cache/goal-seven'
SYMBOLS = ('BTCUSDT', 'ETHUSDT', 'SOLUSDT')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def checked_file(relative, expected):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT) or sha(path) != expected:
        raise ValueError(f'Path or source checksum mismatch: {relative}')
    return path


def rows(path):
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.endswith('.csv')]
        if len(members) != 1:
            raise ValueError(f'Unexpected ZIP contents: {path}')
        with archive.open(members[0]) as stream:
            for row in csv.reader(io.TextIOWrapper(stream, encoding='utf-8-sig')):
                if row and row[0].isdigit():
                    yield row


def candle(row):
    stamp = int(row[0])
    if stamp >= 100_000_000_000_000:
        stamp //= 1000  # Spot archives switched ms -> microseconds in 2025.
    if stamp % 1000:
        raise ValueError('Subsecond candle open')
    return {'time': stamp // 1000,
            **dict(zip(('open', 'high', 'low', 'close'), map(float, row[1:5]))),
            'quote_volume': float(row[7]), 'taker_buy_quote_volume': float(row[10])}


def quality(bars):
    if any(bars[i]['time'] >= bars[i + 1]['time'] for i in range(len(bars) - 1)):
        raise ValueError('Unordered/duplicate source bars')
    return {'bars': len(bars), 'first': bars[0]['time'], 'last': bars[-1]['time'],
            'gaps': [{'after': a['time'], 'before': b['time']} for a, b in zip(bars, bars[1:])
                     if b['time'] - a['time'] != 3600]}


def load_data():
    spot_manifest = read(ROOT / 'research/cache/v3/manifest.json')
    derivatives = read(OUT / 'funding-data-manifest.json')
    if len(derivatives['files']) != 504 or any(f['status'] != 'verified' for f in derivatives['files']):
        raise ValueError('Monthly derivative acquisition not complete/checksummed')
    if not all(derivatives.get('apiFunding', {}).get(s, {}).get('matchedMonthlyArchive') for s in SYMBOLS):
        raise ValueError('REST funding must be complete and reconciled with official monthly archives')
    spot = {s: [] for s in SYMBOLS}
    perp = {s: [] for s in SYMBOLS}
    marks = {s: [] for s in SYMBOLS}
    funding = {s: [] for s in SYMBOLS}
    for record in sorted(spot_manifest['archives'], key=lambda r: (r['symbol'], r['month'])):
        if record['interval'] != '1h' or record['symbol'] not in SYMBOLS:
            continue
        name = Path(urlsplit(record['url']).path).name
        path = checked_file('research/cache/' + name, record['sha256'])
        spot[record['symbol']].extend(candle(row) for row in rows(path))
    for record in derivatives['files']:
        path = checked_file(record['cachePath'], record['sha256'])
        if record['kind'] == 'perp_h1':
            perp[record['symbol']].extend(candle(row) for row in rows(path))
        elif record['kind'] == 'mark_h1':
            marks[record['symbol']].extend(candle(row) for row in rows(path))
    for symbol in SYMBOLS:
        for page in derivatives['apiFunding'][symbol]['pages']:
            path = checked_file(page['cachePath'], page['sha256'])
            for event in read(path):
                raw_mark = event.get('markPrice')
                mark = float(raw_mark) if raw_mark not in (None, '') else None
                if mark is not None and (not math.isfinite(mark) or mark <= 0):
                    raise ValueError('Invalid event mark')
                funding[symbol].append({'time_ms': int(event['fundingTime']),
                                        'rate': float(event['fundingRate']), 'mark_price': mark})
    audit = {kind: {s: quality(bars[s]) for s in SYMBOLS}
             for kind, bars in (('spot', spot), ('perp', perp), ('mark', marks))}
    return spot, perp, marks, funding, audit


def snapshot():
    files = ['research/goal-seven/protocol.json', 'research/goal-seven/directional-protocol.json',
             'research/goal-seven/funding-data-manifest.json', 'research/cache/v3/manifest.json',
             'scripts/goal_execution.py', 'scripts/goal_signals.py', 'scripts/run-goal-directional.py']
    return {name: sha(ROOT / name) for name in files}


def epoch(value):
    return int(datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp())


def gate(result, minimum, scenario, protocol):
    g = protocol['screenGates']
    reasons = []
    if result['trade_count'] < minimum: reasons.append('insufficient_trades')
    if result['net_cash'] <= 0: reasons.append('nonpositive_net')
    if scenario == 'base' and (result['profit_factor'] is None or result['profit_factor'] < g['profitFactorBaseMinimum']):
        reasons.append('profit_factor')
    limit = g['maxConservativeDrawdownBasePct' if scenario == 'base' else 'maxConservativeDrawdownStressPct']
    if result['max_drawdown_pct'] > limit: reasons.append('drawdown')
    limit = g['maxConservativeDailyLossBasePct' if scenario == 'base' else 'maxConservativeDailyLossStressPct']
    if result['max_daily_loss_pct'] > limit: reasons.append('daily_loss')
    if result['account_breach']: reasons.append('account_breach')
    if result['data_quality_flags']: reasons.append('incomplete_active_source')
    return reasons


def run_window(perp, marks, funding, signals, name, dates, minimum, protocol):
    results = {}
    for scenario in ('base', 'stress'):
        r = simulate(perp, marks, funding, signals, epoch(dates[0]), epoch(dates[1]), scenario)
        r['failures'] = gate(r, minimum, scenario, protocol)
        path = DETAIL / f'{name}-{scenario}.json'
        save(path, r)
        results[scenario] = {k: v for k, v in r.items() if k not in ('trades', 'daily', 'data_quality_flags')}
        results[scenario]['data_quality_flag_count'] = len(r['data_quality_flags'])
        results[scenario]['detail_path'] = path.relative_to(ROOT).as_posix()
        results[scenario]['detail_sha256'] = sha(path)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['prepare', 'development', 'evaluation'])
    args = parser.parse_args()
    spot, perp, marks, funding, audit = load_data()
    frozen_path = OUT / 'directional-freeze.json'
    hashes = snapshot()
    if args.phase == 'prepare':
        if frozen_path.exists() and read(frozen_path)['hashes'] != hashes:
            raise ValueError('Frozen run exists with different inputs; register a new trial, never overwrite it')
        if not frozen_path.exists():
            save(frozen_path, {'frozenAtUtc': datetime.now(timezone.utc).isoformat(), 'hashes': hashes,
                               'families': ['N5', 'N6'], 'performanceViewedAtFreeze': False,
                               'dataAudit': audit, 'validated': False})
        print('N5/N6 source, rules, costs and executor frozen before performance; no backtest run.')
        return
    if not frozen_path.exists() or read(frozen_path)['hashes'] != hashes:
        raise ValueError('Prepare immutable inputs before running performance')
    protocol = read(OUT / 'protocol.json')
    signals = generate_signals(spot)
    result_path = OUT / 'directional-results.json'
    if args.phase == 'development':
        if result_path.exists():
            raise ValueError('Development results already recorded; do not overwrite a trial')
        result = {'id': 'N5-N6-v1', 'generatedAtUtc': datetime.now(timezone.utc).isoformat(),
                  'freeze_sha256': sha(frozen_path), 'validatedCount': 0, 'families': {}}
        for family in ('N5', 'N6'):
            dev = run_window(perp, marks, funding, signals[family], family + '-development',
                             protocol['windows']['cryptoDevelopment'],
                             protocol['screenGates']['minimumTradesDevelopment'], protocol)
            passed = not any(r['failures'] for r in dev.values())
            result['families'][family] = {'development': dev, 'developmentPassed': passed,
                                         'evaluation': None, 'validated': False,
                                         'decision': 'eligible_for_historical_evaluation' if passed else 'rejected_in_development'}
        save(result_path, result)
    else:
        result = read(result_path)
        for family, record in result['families'].items():
            if not record['developmentPassed'] or record['evaluation'] is not None:
                continue
            evaluation = {}
            for name, key, minimum in [('validation', 'cryptoValidation', 'minimumTradesValidation'),
                                       ('recent', 'cryptoRecent', 'minimumTradesRecent')]:
                evaluation[name] = run_window(perp, marks, funding, signals[family], family + '-' + name,
                                             protocol['windows'][key], protocol['screenGates'][minimum], protocol)
            record['evaluation'] = evaluation
            passed = not any(r['failures'] for window in evaluation.values() for r in window.values())
            # Return/DD gate applies on the continuous evaluation path as well.
            combined = run_window(perp, marks, funding, signals[family], family + '-evaluation-continuous',
                                  [protocol['windows']['cryptoValidation'][0], protocol['windows']['cryptoRecent'][1]],
                                  protocol['screenGates']['minimumTradesValidation'] + protocol['screenGates']['minimumTradesRecent'], protocol)
            base = combined['base']
            years = (base['end'] - base['start']) / (365.25 * 86400)
            cagr = 100 * ((1 + base['net_pct'] / 100) ** (1 / years) - 1)
            ratio = cagr / base['max_drawdown_pct'] if base['max_drawdown_pct'] > 0 else None
            record['continuousEvaluation'] = combined
            record['annualizedReturnOverDrawdown'] = ratio
            passed = (passed and not any(r['failures'] for r in combined.values()) and ratio is not None
                      and ratio >= protocol['screenGates']['minimumAnnualizedReturnOverDrawdownCombinedEvaluation'])
            record['decision'] = 'candidate_needs_independent_prospective_evidence' if passed else 'rejected_in_evaluation'
        save(result_path, result)
    print(json.dumps({f: {'decision': r['decision'], 'development': r['development']}
                      for f, r in result['families'].items()}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
