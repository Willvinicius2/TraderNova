"""N13 immutable freeze -> daily features -> sample -> development, never approval."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from goal_options_market import ROOT, OUT, START, END, SYMBOLS, io, load_data
from goal_execution_v4 import simulate
from goal_options_skew_signals import DAY, generate_signals

FREEZE = OUT / 'options-skew-freeze.json'
DAILY = OUT / 'options-skew-daily-manifest.json'
SAMPLE = OUT / 'options-skew-sample.json'
RESULT = OUT / 'options-skew-results.json'
TRADE = OUT / 'options-trades-v2-data-manifest.json'
INSTRUMENT = OUT / 'options-instruments-data-manifest.json'
PROTOCOL = OUT / 'options-skew-protocol.json'


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def source_roles(identity, metadata):
    return {'prepareScript': ROOT / 'scripts/prepare-goal-options-skew.py',
            'prepareTests': ROOT / 'tests/goal-options-skew-prepare.py',
            'signalGenerator': ROOT / 'scripts/goal_options_skew_signals.py',
            'protocol': PROTOCOL, 'tradeManifest': TRADE, 'identityAudit': identity,
            'instrumentManifest': INSTRUMENT, 'metadataAudit': metadata}


def snapshot(identity, metadata):
    files = list(source_roles(identity, metadata).values()) + [ROOT / p for p in (
        'research/goal-seven/protocol.json', 'research/goal-seven/funding-data-manifest.json',
        'research/goal-seven/mark-gap-data-manifest.json', 'scripts/goal_options_market.py',
        'scripts/run-goal-options-skew.py', 'scripts/goal_execution_v4.py',
        'scripts/audit-goal-options-trades.py', 'scripts/download-goal-option-instruments.py',
        'scripts/run-goal-directional.py', 'scripts/goal_execution.py', 'scripts/goal_signals.py',
        'tests/goal-options-skew-runner.py', 'tests/goal-options-skew-signals.py',
        'tests/goal-execution-v4.py', 'tests/goal-options-identity-audit.py')]
    return {relative(p): io.sha(p) for p in files}


def source_gate(identity, metadata):
    trade, ident, meta = map(io.read, (TRADE, identity, metadata))
    if (not trade.get('coverageComplete') or trade.get('runningPid')
            or trade.get('inFlight') or trade.get('pending') or trade.get('fatalGaps')):
        raise ValueError('Complete idle trade corpus required')
    if (ident.get('fullIdentityAuditComplete') is not True
            or ident.get('inputManifestSha256') != io.sha(TRADE)):
        raise ValueError('Matching complete identity audit required')
    if (meta.get('fullMetadataAuditComplete') is not True
            or meta.get('tradeManifestSha256') != io.sha(TRADE)
            or meta.get('identityAuditSha256') != io.sha(identity)
            or meta.get('instrumentManifestSha256') != io.sha(INSTRUMENT)):
        raise ValueError('Matching complete metadata audit required')


def freeze(identity, metadata):
    if FREEZE.exists() or DAILY.exists() or SAMPLE.exists() or RESULT.exists():
        raise ValueError('Existing trial artifacts: do not replace or refreeze')
    source_gate(identity, metadata)
    before = snapshot(identity, metadata)
    _, _, _, audit = load_data()
    if snapshot(identity, metadata) != before:
        raise ValueError('Sources changed during freeze preparation')
    write_new(FREEZE, {'id': 'N13-option-skew-preparation-freeze-v1',
        'frozenAtUtc': datetime.now(timezone.utc).isoformat(), 'historicalAssumption': True,
        'sha256': {k: io.sha(p) for k, p in source_roles(identity, metadata).items()},
        'hashes': before,
        'auditPaths': {'identityAudit': relative(identity), 'metadataAudit': relative(metadata)},
        'marketAudit': audit, 'signalCountsPreviouslyViewed': False,
        'performancePreviouslyViewed': False, 'validated': False})


def verify_freeze():
    frozen = io.read(FREEZE)
    identity = ROOT / frozen['auditPaths']['identityAudit']
    metadata = ROOT / frozen['auditPaths']['metadataAudit']
    if (frozen.get('id') != 'N13-option-skew-preparation-freeze-v1'
            or frozen.get('historicalAssumption') is not True
            or frozen.get('signalCountsPreviouslyViewed') is not False
            or frozen.get('performancePreviouslyViewed') is not False
            or frozen['hashes'] != snapshot(identity, metadata)
            or frozen['sha256'] != {k: io.sha(p) for k, p in source_roles(identity, metadata).items()}):
        raise ValueError('Frozen inputs changed or invalid trial provenance')
    source_gate(identity, metadata)
    return frozen


def load_series():
    manifest = io.read(DAILY)
    if manifest.get('freezeSha256') != io.sha(FREEZE) or set(manifest['series']) != set(SYMBOLS):
        raise ValueError('Daily features do not belong to this freeze')
    output = {}
    expected = list(range(io.epoch('2021-10-02'), END + 1, DAY))
    for symbol in SYMBOLS:
        record = manifest['series'][symbol]
        rows = io.read(io.checked_file(record['cachePath'], record['sha256']))
        if (len(rows) != record['rows'] or [r['time'] for r in rows] != expected
                or any(r.get('coverage_complete') is not True for r in rows)):
            raise ValueError('Incomplete or duplicated daily feature calendar')
        output[symbol] = rows
    return output


def counted(signals):
    return {'family': 'N13', 'freezeSha256': io.sha(FREEZE),
            'dailyManifestSha256': io.sha(DAILY), 'window': [START, END],
            'qualifyingDecisionDays': len(signals),
            'byPrioritySelectedSymbol': {s: sum(r['symbol'] == s for r in signals.values()) for s in SYMBOLS},
            'sampleUpperBoundReached': len(signals) >= 100,
            'interpretation': 'Triggers are an upper bound, not executed or closed trades.',
            'PnLComputed': False, 'laterWindowsEvaluated': False, 'validated': False}


def run_phase(phase):
    frozen = verify_freeze()
    signals = {t: r for t, r in generate_signals(load_series(), historical_assumption=True)['N13'].items()
               if START <= r['signal_close_time'] < END}
    sample = counted(signals)
    if phase == 'sample':
        write_new(SAMPLE, sample)
        return sample
    if phase != 'development':
        raise ValueError('Unknown phase')
    if io.read(SAMPLE) != sample or not sample['sampleUpperBoundReached']:
        raise ValueError('Matching sample of at least 100 triggers required before performance')
    paths = {s: ROOT / f'research/cache/goal-seven/N13-development-{s}.json' for s in ('base', 'stress')}
    if RESULT.exists() or any(p.exists() for p in paths.values()):
        raise ValueError('Trial already started: preserve existing results, do not rerun')
    perp, marks, funding, audit = load_data()
    if audit != frozen['marketAudit']:
        raise ValueError('Market audit changed')
    protocol = io.read(OUT / 'protocol.json')
    results = {}
    for scenario, path in paths.items():
        result = simulate(perp, marks, funding, signals, START, END, scenario)
        result['failures'] = io.gate(result, 100, scenario, protocol)
        write_new(path, result)
        results[scenario] = {k: v for k, v in result.items() if k not in ('trades', 'daily', 'data_quality_flags')}
        results[scenario].update(detail_path=relative(path), detail_sha256=io.sha(path),
                                data_quality_flag_count=len(result['data_quality_flags']))
    passed = all(not r['failures'] for r in results.values())
    report = {'family': 'N13', 'freezeSha256': io.sha(FREEZE), 'sampleSha256': io.sha(SAMPLE),
              'development': results, 'developmentPassed': passed, 'validated': False,
              'laterWindowsEvaluated': False, 'historicalPublicationAvailabilityAssumed': True,
              'decision': 'candidate_for_further_screening' if passed else 'rejected_in_development'}
    write_new(RESULT, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['prepare', 'sample', 'development'])
    parser.add_argument('--identity-audit', type=Path)
    parser.add_argument('--metadata-audit', type=Path)
    args = parser.parse_args()
    if args.phase == 'prepare':
        if args.identity_audit is None or args.metadata_audit is None:
            parser.error('prepare requires --identity-audit and --metadata-audit')
        freeze(args.identity_audit, args.metadata_audit)
        print('N13 frozen; no real features or performance computed.')
    else:
        print(json.dumps(run_phase(args.phase), indent=2))


if __name__ == '__main__':
    main()
