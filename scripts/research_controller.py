"""Bounded research ledger, not an AI service, executor or financial approver.

Quota readings must be supplied by the supervising Codex tool. The controller
checks their freshness, not their authenticity. Locks are never probed with
os.kill on Windows and stale locks require explicit human/supervisor inspection.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
import os
from pathlib import Path

LIMITS = json.loads((Path(__file__).resolve().parents[1] / 'research/validation/supervision.json').read_text(encoding='utf-8'))['limits']


class Blocked(ValueError):
    pass


def now():
    return datetime.now(timezone.utc)


def parse_time(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise Blocked('Timezone required')
    return d


def day(t):
    return t.astimezone(timezone(timedelta(hours=-3))).date().isoformat()


def read(path, default=None):
    if not path.exists() and default is not None:
        return default
    return json.loads(path.read_text(encoding='utf-8-sig'))


@contextmanager
def locked(cache):
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / 'controller.lock'
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise Blocked('Controller lock exists; inspect owner, never start a duplicate')
    try:
        os.write(fd, str(os.getpid()).encode())
        yield
    finally:
        os.close(fd)
        path.unlink()


def write(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
    os.replace(tmp, path)


def file_hash(root, value):
    p = (root / value).resolve()
    if not p.is_relative_to(root) or not p.is_file():
        raise Blocked('Research input must be a real file inside the project')
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def quota(used, observed, t):
    if isinstance(used, bool) or not isinstance(used, (int, float)) or not math.isfinite(used) or not 0 <= used <= 100:
        raise Blocked('Current measured quota is required')
    if observed is None or not 0 <= (t-parse_time(observed)).total_seconds() <= 300:
        raise Blocked('Quota observation must be timezone-aware and no older than five minutes')
    if used >= LIMITS['weeklyUsedCeiling']:
        raise Blocked('Conservative weekly usage ceiling reached')


def operate(root, action, **args):
    root = Path(root).resolve()
    if not root.is_dir():
        raise Blocked('Project root missing')
    cache = root / 'research/cache/validation'
    with locked(cache):
        path = cache / 'controller-state.json'
        state = read(path, {'attempts': [], 'rounds': [], 'active': None, 'pauseDay': None})
        t = now()
        def summary():
            active = next((a for a in state['attempts'] if a['id']==state['active']), None)
            return {'validatedCount': 0, 'active': state['active'],
                    'overdue': bool(active and t>parse_time(active['deadlineAt'])),
                    'attempts': len(state['attempts']), 'rounds': len(state['rounds']),
                    'limits': LIMITS, 'automaticApproval': False}
        if action == 'status':
            return summary()
        if action in ('preflight', 'begin', 'round'):
            if (cache / 'STOP').exists():
                raise Blocked('STOP marker present')
            quota(args.get('weekly_used'), args.get('quota_observed_at'), t)
            if state['active']:
                raise Blocked('An attempt is active; inspect and finish it before resuming')
            if state['pauseDay'] == day(t):
                raise Blocked('Daily quota-delta pause')
            if sum(day(parse_time(a['startedAt']))==day(t) for a in state['attempts']) >= LIMITS['maxAttemptsPerDay']:
                raise Blocked('Daily attempt ceiling reached')
        if action == 'preflight':
            return {'ready': True, **summary()}
        if action == 'round':
            evidence = file_hash(root, args['evidence'])
            if any(day(parse_time(r['at']))==day(t) for r in state['rounds']):
                raise Blocked('A scheduled round was already recorded today')
            state['rounds'].append({'at': t.isoformat(), 'evidenceHash': evidence,
                                    'note': args.get('note', '')[:1000], 'weeklyUsed': args['weekly_used']})
        elif action == 'begin':
            registry = read(root / 'research/validation/candidates.json')['candidates']
            if len({c['family'] for c in registry}) != len(registry):
                raise Blocked('Duplicate mechanisms in the registered candidates')
            candidate = next((c for c in registry if c['id']==args['candidate']), None)
            if not candidate or candidate['status']!='ready_for_development':
                raise Blocked('Candidate must have audited data and supervisor-reviewed readiness')
            hashes = {k: file_hash(root, args[k]) for k in ('rule','data','costs','engine')}
            mechanism = candidate['family']
            for previous in state['attempts']:
                if previous['hashes']==hashes:
                    raise Blocked('Identical frozen inputs were already attempted')
                if previous['mechanism']==mechanism and previous.get('outcome') in ('rejected','candidate'):
                    raise Blocked('Development already evaluated for this mechanism; no automatic rerun')
                if previous['mechanism']==mechanism and previous['hashes']['rule']==hashes['rule'] and previous['hashes']['data']==hashes['data']:
                    raise Blocked('Same rule and data already attempted; no cost/engine rescue')
            item = {'id': os.urandom(12).hex(), 'candidate': candidate['id'], 'mechanism': mechanism,
                    'hashes': hashes, 'startedAt': t.isoformat(),
                    'deadlineAt': (t+timedelta(seconds=LIMITS['maxAgentSeconds'])).isoformat(),
                    'weeklyUsedStart': args['weekly_used'], 'outcome': None}
            state['attempts'].append(item)
            state['active'] = item['id']
        elif action == 'finish':
            if args.get('outcome') not in ('blocked','rejected','candidate'):
                raise Blocked('Automatic financial approval is forbidden')
            if not state['active'] or state['active']!=args.get('attempt_id'):
                raise Blocked('Attempt is not the active one')
            item = next(a for a in state['attempts'] if a['id']==state['active'])
            used = args.get('weekly_used')
            if not isinstance(used,(int,float)) or isinstance(used,bool) or not math.isfinite(used) or not 0<=used<=100:
                raise Blocked('Measured ending quota required')
            if used-item['weeklyUsedStart'] >= LIMITS['maxWeeklyDeltaPerRound']:
                state['pauseDay'] = day(t)
            outcome = 'blocked' if t>parse_time(item['deadlineAt']) else args['outcome']
            item.update(outcome=outcome, endedAt=t.isoformat(), weeklyUsedEnd=used,
                        note=args.get('note','')[:1000], validated=False)
            state['active'] = None
        else:
            raise Blocked('Unknown operation')
        write(path, state)
        return summary()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['status','preflight','round','begin','finish'])
    p.add_argument('--root', default=str(Path(__file__).resolve().parents[1]))
    for arg in ['quota-observed-at','evidence','candidate','rule','data','costs','engine','attempt-id','outcome','note']:
        p.add_argument('--'+arg)
    p.add_argument('--weekly-used', type=float)
    a = vars(p.parse_args())
    try:
        print(json.dumps(operate(a.pop('root'), a.pop('action'), **a), ensure_ascii=False))
    except (Blocked, KeyError, TypeError, ValueError, OSError) as e:
        print(json.dumps({'ready':False,'reason':str(e),'validated':False}, ensure_ascii=False))
        raise SystemExit(2)
