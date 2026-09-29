"""N14 one registered rule; source acquisition, freeze, sample and gated DEV only."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

from goal_options_market import ROOT, OUT, START, END, io, load_data
from goal_execution_v4 import simulate

DAY, HOUR = 86400, 3600
SOURCE_START = io.epoch('2021-09-01')
CACHE = ROOT / 'research/cache/goal-seven/miner-pressure'
MANIFEST = OUT / 'miner-pressure-data-manifest.json'
FREEZE = OUT / 'miner-pressure-freeze.json'
SAMPLE = OUT / 'miner-pressure-sample.json'
RESULT = OUT / 'miner-pressure-results.json'


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def normalize(data):
    if not isinstance(data, dict) or data.get('next_page_url') or data.get('next_page_token'):
        raise ValueError('Incomplete or invalid single-page response')
    rows, seen = [], set()
    for row in data['data']:
        stamp = datetime.fromisoformat(row['time'].replace('Z', '+00:00'))
        time = int(stamp.timestamp())
        raw = row.get('HashRate')
        if row.get('asset') != 'btc' or not isinstance(raw, str):
            raise ValueError('Unexpected asset or missing source metric')
        value = Decimal(raw)
        if (not value.is_finite() or value <= 0 or stamp.microsecond or time % DAY
                or time in seen or not SOURCE_START <= time < END):
            raise ValueError('Invalid/duplicate/out-of-scope daily hashrate')
        seen.add(time)
        rows.append({'time': time, 'hashrate': raw})
    rows.sort(key=lambda r: r['time'])
    if [r['time'] for r in rows] != list(range(SOURCE_START, END, DAY)):
        raise ValueError('Daily hashrate coverage incomplete')
    return rows


def acquire():
    if MANIFEST.exists() or CACHE.exists():
        raise ValueError('Existing acquisition preserved; do not refetch/overwrite')
    query = urllib.parse.urlencode({'assets': 'btc', 'metrics': 'HashRate', 'frequency': '1d',
        'start_time': '2021-09-01T00:00:00Z', 'end_time': '2024-12-31T23:59:59Z',
        'paging_from': 'start', 'page_size': 10000})
    url = 'https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?' + query
    sent = datetime.now(timezone.utc).isoformat()
    request = urllib.request.Request(url, headers={'User-Agent': 'TraderNova-N14-research/1.0'})
    try:
        response = urllib.request.urlopen(request, timeout=30)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        body = response.read(2_000_000)
        status, headers = response.status, dict(response.headers.items())
    CACHE.mkdir(parents=True)
    raw_path = CACHE / 'response.json'
    with raw_path.open('xb') as f:
        f.write(body)
    record = {'id': 'N14-hashrate-data-v1', 'url': url, 'requestSentAtUtc': sent,
              'receivedAtUtc': datetime.now(timezone.utc).isoformat(), 'status': status,
              'headers': headers, 'rawPath': raw_path.relative_to(ROOT).as_posix(),
              'rawSha256': hashlib.sha256(body).hexdigest(), 'rawBytes': len(body),
              'acquisitionComplete': False, 'validated': False}
    try:
        if status != 200 or len(body) >= 2_000_000:
            raise ValueError('Non-200 or response cap reached')
        rows = normalize(json.loads(body))
        normalized = CACHE / 'BTCUSDT.json'
        write_new(normalized, rows)
        record.update(acquisitionComplete=True, normalizedPath=normalized.relative_to(ROOT).as_posix(),
                      normalizedSha256=io.sha(normalized), rows=len(rows))
    except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
        record['error'] = type(exc).__name__ + ': ' + str(exc)
    write_new(MANIFEST, record)
    return {k: record[k] for k in ('status', 'rawBytes', 'acquisitionComplete')}


def generate(rows, historical_assumption=False):
    index = {}
    for row in rows:
        stamp, raw = row.get('time'), row.get('hashrate')
        if type(stamp) is not int or stamp % DAY or stamp in index or not isinstance(raw, str):
            raise ValueError('Invalid or duplicate daily source')
        value = Decimal(raw)
        if not value.is_finite() or value <= 0:
            raise ValueError('Positive finite hashrate required')
        index[stamp] = {**row, 'value': value}
    signals = {}
    for stamp in sorted(index):
        days = [stamp - i * DAY for i in range(29, -1, -1)]
        if any(t not in index for t in days):
            continue
        observations = [index[t] for t in days]
        if not historical_assumption:
            def timely(row):
                received = row.get('received_at')
                return (type(received) in (int, float) and math.isfinite(received)
                        and row['time']+DAY <= received <= row['time']+3*DAY)
            if not all(timely(row) for row in observations):
                continue
        if sum(r['value'] for r in observations[-7:]) * 30 >= sum(r['value'] for r in observations) * 7:
            continue
        decision = stamp + 3 * DAY
        signals[decision] = {'symbol': 'BTCUSDT', 'direction': -1, 'stop_pct': .02,
            'hold_hours': 12, 'signal_close_time': decision+HOUR, 'feature_end': stamp+DAY,
            'decision_time': decision, 'source_label': stamp, 'reason': 'mining_capacity_mean7_below_mean30'}
    return signals


def hashes():
    names = ['research/goal-seven/protocol.json', 'research/goal-seven/miner-pressure-protocol.json',
        'research/goal-seven/miner-pressure-data-manifest.json', 'research/goal-seven/funding-data-manifest.json',
        'research/goal-seven/mark-gap-data-manifest.json', 'scripts/run-goal-miner-pressure.py',
        'tests/goal-miner-pressure.py', 'scripts/goal_options_market.py', 'scripts/goal_execution_v4.py',
        'scripts/run-goal-directional.py', 'scripts/goal_execution.py', 'scripts/goal_signals.py']
    return {name: io.sha(ROOT / name) for name in names}


def inputs():
    source = io.read(MANIFEST)
    if not source.get('acquisitionComplete'):
        raise ValueError('Complete acquisition required')
    raw = io.checked_file(source['rawPath'], source['rawSha256'])
    rows = io.read(io.checked_file(source['normalizedPath'], source['normalizedSha256']))
    if rows != normalize(io.read(raw)) or len(rows) != source['rows']:
        raise ValueError('Source normalization mismatch')
    perp, marks, funding, audit = load_data()
    return rows, {s: perp[s] for s in ('BTCUSDT',)}, {s: marks[s] for s in ('BTCUSDT',)}, \
        {s: funding[s] for s in ('BTCUSDT',)}, audit


def run(phase):
    if phase == 'acquire':
        return acquire()
    rows, perp, marks, funding, audit = inputs()
    current = hashes()
    if phase == 'prepare':
        if any(p.exists() for p in (FREEZE, SAMPLE, RESULT)):
            raise ValueError('Existing trial; preserve it')
        write_new(FREEZE, {'hashes': current, 'frozenAtUtc': datetime.now(timezone.utc).isoformat(),
            'marketAudit': audit, 'featuresPreviouslyViewed': False, 'performancePreviouslyViewed': False,
            'historicalAssumption': True, 'validated': False})
        return {'frozen': True, 'PnLComputed': False}
    frozen = io.read(FREEZE)
    if frozen['hashes'] != current or frozen['marketAudit'] != audit:
        raise ValueError('Frozen inputs changed')
    signals = {t: r for t, r in generate(rows, historical_assumption=True).items()
               if START <= r['signal_close_time'] < END}
    sample = {'family': 'N14', 'freezeSha256': io.sha(FREEZE), 'window': [START, END],
              'qualifyingDecisionDays': len(signals), 'sampleUpperBoundReached': len(signals) >= 100,
              'PnLComputed': False, 'validated': False, 'laterWindowsEvaluated': False}
    if phase == 'sample':
        write_new(SAMPLE, sample)
        return sample
    if phase != 'development' or io.read(SAMPLE) != sample or not sample['sampleUpperBoundReached']:
        raise ValueError('Matching sample of >=100 triggers required')
    paths = {s: CACHE / ('development-' + s + '.json') for s in ('base', 'stress')}
    if RESULT.exists() or any(p.exists() for p in paths.values()):
        raise ValueError('Development already started; no rerun')
    results = {}
    for scenario, path in paths.items():
        result = simulate(perp, marks, funding, signals, START, END, scenario)
        result['failures'] = io.gate(result, 100, scenario, io.read(OUT / 'protocol.json'))
        write_new(path, result)
        results[scenario] = {k: v for k, v in result.items() if k not in ('trades', 'daily', 'data_quality_flags')}
        results[scenario].update(detailPath=path.relative_to(ROOT).as_posix(), detailSha256=io.sha(path),
                                dataQualityFlagCount=len(result['data_quality_flags']))
    passed = all(not r['failures'] for r in results.values())
    report = {'family': 'N14', 'freezeSha256': io.sha(FREEZE), 'sampleSha256': io.sha(SAMPLE),
              'development': results, 'developmentPassed': passed, 'validated': False,
              'laterWindowsEvaluated': False, 'historicalAssumption': True,
              'decision': 'candidate_for_further_screening' if passed else 'rejected_in_development'}
    write_new(RESULT, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['acquire', 'prepare', 'sample', 'development'])
    print(json.dumps(run(parser.parse_args().phase), indent=2))
