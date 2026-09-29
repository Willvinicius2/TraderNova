"""Bounded local N13 research queue. No model calls, parameter search or approval."""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/goal-seven'
CACHE = ROOT / 'research/cache/goal-seven/lab'
TRADE = OUT / 'options-trades-v2-data-manifest.json'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(p, value):
    temporary = p.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    for attempt in range(7):
        try:
            os.replace(temporary, p)
            return
        except PermissionError:
            if attempt == 6:
                raise
            time.sleep(.05 * 2**attempt)


@contextlib.contextmanager
def locked():
    import msvcrt
    CACHE.mkdir(parents=True, exist_ok=True)
    with (CACHE / 'worker.lock').open('a+b') as stream:
        if stream.seek(0, os.SEEK_END) == 0:
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def collection_state(m):
    if m.get('runningPid') or m.get('inFlight'):
        return 'waiting'
    if m.get('coverageComplete') is True and not m.get('pending') and not m.get('fatalGaps'):
        return 'ready'
    return 'incomplete_stopped'


def final_state(sample, result=None):
    if not sample.get('sampleUpperBoundReached'):
        return 'insufficient_sample'
    if result is None:
        return 'development_required'
    if result.get('validated') is not False or result.get('laterWindowsEvaluated') is not False:
        raise ValueError('Local worker cannot approve or evaluate later windows')
    return 'candidate_needs_review' if result.get('developmentPassed') else 'rejected_in_development'


def run(max_hours=16):
    if not 0 < max_hours <= 24:
        raise ValueError('Duration must be positive and <=24 hours')
    deadline = time.monotonic() + max_hours * 3600
    files = [ROOT / 'scripts' / n for n in (
        'goal-lab.py', 'audit-goal-options-trades.py', 'prepare-goal-options-skew.py',
        'run-goal-options-skew.py', 'goal_options_market.py', 'goal_options_skew_signals.py',
        'goal_execution_v4.py')]
    code = {p.relative_to(ROOT).as_posix(): sha(p) for p in files}
    with locked():
        run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8]
        status_path = CACHE / 'status.json'
        state = {'runId': run_id, 'startedAtUtc': utc(), 'pid': os.getpid(), 'state': 'waiting_for_data',
                 'maxHours': max_hours, 'codeHashes': code, 'steps': [], 'validated': False,
                 'modelCalls': 0, 'parameterCombinationsSearched': 0}
        save(CACHE / (run_id + '.launch.json'), state)

        def check():
            if (CACHE / 'STOP').exists():
                raise RuntimeError('Local STOP marker')
            if time.monotonic() >= deadline:
                raise TimeoutError('Local worker duration reached')
            if {n: sha(ROOT / n) for n in code} != code:
                raise RuntimeError('Worker source changed; review and relaunch')

        def step(label, *args):
            check()
            state.update(state=label, updatedAtUtc=utc())
            save(status_path, state)
            log = CACHE / (run_id + '-' + label + '.log')
            with log.open('xb') as stream:
                result = subprocess.run([sys.executable, *args], cwd=ROOT, stdout=stream,
                    stderr=subprocess.STDOUT, timeout=max(1, deadline-time.monotonic()),
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            state['steps'].append({'name': label, 'exitCode': result.returncode,
                                   'log': log.relative_to(ROOT).as_posix(), 'endedAtUtc': utc()})
            if result.returncode:
                raise RuntimeError(label + ' failed; inspect preserved log')

        try:
            save(status_path, state)
            while True:
                check()
                phase = collection_state(read(TRADE))
                if phase == 'ready':
                    break
                if phase == 'incomplete_stopped':
                    raise RuntimeError('Collector stopped with incomplete data; no automatic retry')
                time.sleep(min(30, max(0, deadline-time.monotonic())))
            digest = sha(TRADE)
            identity = OUT / ('options-identity-audit-' + digest[:16] + '.json')
            if not identity.exists():
                step('identity', 'scripts/audit-goal-options-trades.py')
            if read(identity).get('fullIdentityAuditComplete') is not True:
                raise RuntimeError('Identity audit failed')
            metadata_inputs = {'tradeManifestSha256': digest, 'identityAuditSha256': sha(identity),
                               'instrumentManifestSha256': sha(OUT / 'options-instruments-data-manifest.json')}
            metadata_digest = hashlib.sha256(json.dumps(metadata_inputs, sort_keys=True).encode()).hexdigest()
            metadata = OUT / ('options-metadata-audit-' + metadata_digest[:16] + '.json')
            if not metadata.exists():
                step('metadata', 'scripts/prepare-goal-options-skew.py', 'audit',
                     '--identity-audit', str(identity))
            if not (OUT / 'options-skew-freeze.json').exists():
                step('freeze', 'scripts/run-goal-options-skew.py', 'prepare',
                     '--identity-audit', str(identity), '--metadata-audit', str(metadata))
            if not (OUT / 'options-skew-daily-manifest.json').exists():
                step('aggregate', 'scripts/prepare-goal-options-skew.py', 'aggregate',
                     '--identity-audit', str(identity), '--metadata-audit', str(metadata),
                     '--freeze', str(OUT / 'options-skew-freeze.json'))
            sample_path, result_path = OUT / 'options-skew-sample.json', OUT / 'options-skew-results.json'
            if not sample_path.exists():
                step('sample', 'scripts/run-goal-options-skew.py', 'sample')
            # Reuse requires an exact source freeze, including code and audits.
            sys.path.insert(0, str(ROOT / 'scripts'))
            spec = importlib.util.spec_from_file_location('n13_runner', ROOT / 'scripts/run-goal-options-skew.py')
            runner = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(runner)
            runner.verify_freeze()
            sample = read(sample_path)
            if sample.get('freezeSha256') != sha(OUT / 'options-skew-freeze.json'):
                raise RuntimeError('Sample freeze mismatch')
            if final_state(sample) == 'development_required' and not result_path.exists():
                step('development', 'scripts/run-goal-options-skew.py', 'development')
            result = read(result_path) if result_path.exists() else None
            if result and (result.get('freezeSha256') != sha(OUT / 'options-skew-freeze.json')
                           or result.get('sampleSha256') != sha(sample_path)):
                raise RuntimeError('Result provenance mismatch')
            state['state'] = final_state(sample, result)
        except Exception as exc:
            state.update(state='needs_review', error=type(exc).__name__ + ': ' + str(exc))
        finally:
            state.update(endedAtUtc=utc(), pid=None)
            save(status_path, state)
            save(CACHE / (run_id + '.result.json'), state)
        return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run', 'status'])
    parser.add_argument('--max-hours', type=float, default=16)
    args = parser.parse_args()
    outcome = run(args.max_hours) if args.command == 'run' else read(CACHE / 'status.json')
    print(json.dumps(outcome, indent=2))
