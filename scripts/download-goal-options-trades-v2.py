"""Resumable, data-only Deribit option trade archive for N13; never computes signals.

coverageComplete only proves non-truncated time leaves. `complete` remains false
until a separate cross-page/parent-leaf identity and full data audit is frozen.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import contextlib
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'research/cache/goal-seven/options-trades-v2'
MANIFEST = ROOT / 'research/goal-seven/options-trades-v2-data-manifest.json'
V1_CACHE = ROOT / 'research/cache/goal-seven/options-trades'
V1_MANIFEST = ROOT / 'research/goal-seven/revisions/options-trades-v1/options-trades-data-manifest.json'
V1_MANIFEST_SHA256 = '7ff6065b571662798e201c44b6796ce1c111dc13476fabc0918012252a1bb04e'
API = 'https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time'
START = datetime(2021, 10, 1, tzinfo=timezone.utc)
END = datetime(2025, 1, 1, tzinfo=timezone.utc)
SYMBOLS = ('BTC', 'ETH')
COUNT = 10000  # Official limit on history.deribit.com, distinct from common API.
CACHE_CAP = 5_000_000_000
MAX_RESPONSE_BYTES = 16_000_000
RESERVE_BYTES = 64_000  # gzip expansion plus receipt, before the exact cap check.


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_ACTIVE_LOCKS = set()


@contextlib.contextmanager
def exclusive_lock():
    """One writer per cache, including across Windows processes."""
    import msvcrt
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / '.collector.lock'
    key = str(path.resolve()).lower()
    if key in _ACTIVE_LOCKS:
        raise RuntimeError('Collector already running in this process')
    with path.open('a+b') as stream:
        if stream.seek(0, os.SEEK_END) == 0:
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise RuntimeError('Collector lock held by another process') from exc
        _ACTIVE_LOCKS.add(key)
        try:
            yield
        finally:
            _ACTIVE_LOCKS.remove(key)
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def tasks():
    output = []
    day = START
    while day < END:
        lo = int(day.timestamp() * 1000)
        hi = int((day + timedelta(days=1)).timestamp() * 1000)
        output.extend({'symbol': symbol, 'lo': lo, 'hi': hi} for symbol in SYMBOLS)
        day += timedelta(days=1)
    return output


def filename(task):
    return f"{task['symbol']}-{task['lo']}-{task['hi']}-c10000.json.gz"


def url_for(task):
    parameters = {'currency': task['symbol'], 'kind': 'option',
                  'start_timestamp': task['lo'], 'end_timestamp': task['hi'] - 1,
                  'count': COUNT, 'sorting': 'asc', 'include_old': 'true'}
    return API + '?' + urllib.parse.urlencode(parameters)


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def initial_manifest():
    old_bytes = V1_MANIFEST.read_bytes()
    if digest(old_bytes) != V1_MANIFEST_SHA256:
        raise ValueError('Changed v1 predecessor manifest')
    old = json.loads(old_bytes)
    if (old.get('id') != 'N13-deribit-option-trades-data-v1' or old.get('inFlight')
            or old.get('fatalGaps') or len(old.get('leaves', [])) != 4
            or len(old.get('splits', [])) != 6 or len(old.get('pending', [])) != 2378):
        raise ValueError('Unexpected v1 predecessor state')
    def inherited(items):
        return [{**record, 'sourcePolicy': 'v1-count1000', 'sourceCache': 'v1'}
                for record in old[items]]
    inherited_records = {key: inherited(key) for key in ('leaves', 'splits', 'rejected', 'errors')}
    result = {'id': 'N13-deribit-option-trades-data-v2', 'createdAtUtc': utc_now(),
            'source': API, 'scope': {'symbols': list(SYMBOLS), 'startInclusive': START.isoformat(),
                                    'endExclusive': END.isoformat(), 'kind': 'option'},
            'request': {'count': COUNT, 'sorting': 'asc', 'include_old': True,
                        'windowConvention': '[lo,hi), API end_timestamp=hi-1'},
            'predecessor': {'path': str(V1_MANIFEST.relative_to(ROOT)).replace('\\', '/'),
                            'sha256': V1_MANIFEST_SHA256,
                            'requestCount': 1000, 'importedLeaves': 4,
                            'importedSplits': 6, 'importedPending': 2378},
            'pending': old['pending'], **inherited_records,
            'fatalGaps': old['fatalGaps'],
            'httpGetCount': old['httpGetCount'], 'rawResponseBytes': old['rawResponseBytes'],
            'cacheBytes': old['cacheBytes'],
            'lastGetSentEpoch': old['lastGetSentEpoch'], 'inFlight': None,
            'runSerial': 0, 'runningPid': None, 'runningStartedAtUtc': None,
            'lastRunEndedAtUtc': None, 'lastRunPid': None,
            'coverageComplete': False, 'crossPageIdentityAuditComplete': False,
            'fullDataAuditComplete': False, 'complete': False,
            'state': 'pending', 'lastError': old.get('lastError')}
    check_manifest(result)
    return result


def check_manifest(manifest):
    if (manifest.get('id') != 'N13-deribit-option-trades-data-v2'
            or manifest.get('source') != API
            or manifest.get('request') != {'count': COUNT, 'sorting': 'asc', 'include_old': True,
                                           'windowConvention': '[lo,hi), API end_timestamp=hi-1'}
            or manifest.get('scope') != {'symbols': list(SYMBOLS),
                                         'startInclusive': START.isoformat(),
                                         'endExclusive': END.isoformat(), 'kind': 'option'}
            or manifest.get('predecessor', {}).get('sha256') != V1_MANIFEST_SHA256):
        raise ValueError('Manifest scope/policy mismatch')
    if digest(V1_MANIFEST.read_bytes()) != V1_MANIFEST_SHA256:
        raise ValueError('Changed v1 predecessor manifest')
    for record in manifest['leaves'] + manifest['splits'] + manifest['rejected'] + manifest['errors']:
        source_cache = V1_CACHE if record.get('sourceCache') == 'v1' else CACHE
        raw_path = source_cache / record['file']
        receipt_path = source_cache / record['receiptFile']
        if not raw_path.exists() or not receipt_path.exists():
            raise ValueError(f'Missing immutable probe: {record["file"]}')
        packed = raw_path.read_bytes()
        if digest(packed) != record['gzipSha256'] or digest(gzip.decompress(packed)) != record['rawSha256']:
            raise ValueError(f'Changed immutable probe: {record["file"]}')
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        if any(record.get(key) != value for key, value in receipt.items()):
            raise ValueError(f'Changed receipt: {record["receiptFile"]}')


def inspect(body: bytes, task):
    message = json.loads(body)
    if not isinstance(message, dict):
        raise ValueError('Invalid JSON-RPC response object')
    if message.get('error') or not isinstance(message.get('result'), dict):
        raise ValueError(f'Deribit error response: {message.get("error")}')
    result = message['result']
    trades = result.get('trades')
    has_more = result.get('has_more')
    if not isinstance(trades, list) or not isinstance(has_more, bool) or len(trades) > COUNT:
        raise ValueError('Invalid trade page shape/count')
    seen = {}
    identical = conflicts = 0
    previous = None
    ascending = True
    minimum = maximum = None
    for trade in trades:
        if not isinstance(trade, dict):
            raise ValueError('Invalid trade record object')
        stamp, trade_id = trade.get('timestamp'), trade.get('trade_id')
        instrument = trade.get('instrument_name')
        if (not isinstance(stamp, int) or isinstance(stamp, bool)
                or not task['lo'] <= stamp < task['hi']
                or not isinstance(trade_id, str) or not trade_id
                or not isinstance(instrument, str)
                or not instrument.startswith(task['symbol'] + '-')
                or not instrument.endswith(('-C', '-P'))):
            raise ValueError('Trade outside requested currency/option/time scope or missing ID')
        if previous is not None and stamp < previous:
            ascending = False
        previous = stamp
        minimum = stamp if minimum is None else min(minimum, stamp)
        maximum = stamp if maximum is None else max(maximum, stamp)
        canonical = json.dumps(trade, sort_keys=True, separators=(',', ':'))
        if trade_id in seen:
            if seen[trade_id] == canonical:
                identical += 1
            else:
                conflicts += 1
        else:
            seen[trade_id] = canonical
    return {'records': len(trades), 'uniqueTradeIds': len(seen),
            'identicalDuplicates': identical, 'duplicateConflicts': conflicts,
            'hasMore': has_more, 'firstTimestampMs': trades[0]['timestamp'] if trades else None,
            'lastTimestampMs': trades[-1]['timestamp'] if trades else None,
            'minTimestampMs': minimum, 'maxTimestampMs': maximum,
            'timestampsNondecreasingInSourceOrder': ascending}


def validate_coverage(manifest):
    if manifest['pending'] or manifest['fatalGaps']:
        return False
    expected = tasks()
    leaves = sorted(manifest['leaves'], key=lambda x: (x['symbol'], x['lo']))
    if any(x['hasMore'] or x['duplicateConflicts'] or x['partial'] for x in leaves):
        return False
    for symbol in SYMBOLS:
        chain = [x for x in leaves if x['symbol'] == symbol]
        cursor = int(START.timestamp() * 1000)
        for leaf in chain:
            if leaf['lo'] != cursor or leaf['hi'] <= leaf['lo']:
                return False
            cursor = leaf['hi']
        if cursor != int(END.timestamp() * 1000):
            return False
    return len(expected) > 0


def fetch(url, remaining_bytes):
    sent = utc_now()
    request = urllib.request.Request(url, headers={'User-Agent': 'TraderNova-N13-data-only/1.0'})
    try:
        response = urllib.request.urlopen(request, timeout=10)
    except urllib.error.HTTPError as exc:
        response = exc  # Preserve the actual server error body, including 403/429/5xx.
    with response:
        status = response.status
        body = response.read(remaining_bytes)
    received = utc_now()
    # Exact-cap responses are conservatively partial: no extra byte is downloaded.
    partial = len(body) == remaining_bytes
    return body, status, sent, received, partial


def store_response(manifest, task, body, status, sent, received, *, partial=False,
                   error=False, saved_receipt=None):
    name = filename(task) if not error else filename(task).replace(
        '.json.gz', f'-error-{manifest["httpGetCount"]}.json.gz')
    raw_path = CACHE / name
    receipt_path = CACHE / name.replace('.json.gz', '.receipt.json')
    if saved_receipt is None and (raw_path.exists() or receipt_path.exists()):
        raise ValueError(f'Immutable response already exists: {name}')
    packed = gzip.compress(body, compresslevel=6, mtime=0)
    receipt = {**task, 'file': name, 'receiptFile': receipt_path.name,
               'url': url_for(task), 'sentAtUtc': sent, 'receivedAtUtc': received,
               'httpStatus': status, 'rawBytes': len(body), 'rawSha256': digest(body),
               'gzipBytes': len(packed), 'gzipSha256': digest(packed), 'partial': partial}
    encoded_receipt = (json.dumps(receipt, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    if manifest['cacheBytes'] + len(packed) + len(encoded_receipt) > CACHE_CAP:
        raise RuntimeError('Total cache cap reached before saving response')
    if saved_receipt is None:
        CACHE.mkdir(parents=True, exist_ok=True)
        with raw_path.open('xb') as stream:
            stream.write(packed)
        with receipt_path.open('xb') as stream:
            stream.write(encoded_receipt)
    elif saved_receipt != receipt or raw_path.read_bytes() != packed or receipt_path.read_bytes() != encoded_receipt:
        raise ValueError(f'Changed orphan response: {name}')
    manifest['cacheBytes'] += raw_path.stat().st_size + receipt_path.stat().st_size
    manifest['rawResponseBytes'] += len(body)
    return receipt


def preserve_error(manifest, task, body, status, sent, received, reason, *, partial=False,
                   partial_state='round_raw_byte_limit'):
    receipt = store_response(manifest, task, body, status, sent, received,
                             partial=partial, error=True)
    record = {**receipt, 'validationError': reason}
    manifest['errors'].append(record)
    manifest['lastError'] = {'timeUtc': utc_now(), 'url': receipt['url'],
                             'httpStatus': status, 'message': reason,
                             'partial': partial, 'receiptFile': receipt['receiptFile']}
    manifest['state'] = ('blocked_403' if status == 403 else
                         partial_state if partial else
                         f'stopped_http_{status}' if status is not None else 'stopped_transport')
    manifest['inFlight'] = None
    atomic_json(MANIFEST, manifest)


def commit_response(manifest, task, body, status, sent, received, saved_receipt=None):
    receipt = store_response(manifest, task, body, status, sent, received,
                             saved_receipt=saved_receipt)
    try:
        if status != 200:
            raise ValueError(f'HTTP {status}')
        page = inspect(body, task)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        manifest['pending'].pop(0)
        manifest['rejected'].append({**receipt, 'validationError': str(exc)})
        manifest['fatalGaps'].append({**task, 'issue': 'invalid_response_schema'})
        manifest['state'] = 'fatal'
        manifest['inFlight'] = None
        atomic_json(MANIFEST, manifest)
        return
    record = {**receipt, **page}
    manifest['pending'].pop(0)
    if page['duplicateConflicts']:
        manifest['rejected'].append(record)
        manifest['fatalGaps'].append({**task, 'issue': 'conflicting_duplicate_trade_id'})
        manifest['state'] = 'fatal'
    elif page['hasMore']:
        manifest['splits'].append(record)
        if task['hi'] - task['lo'] <= 1:
            manifest['fatalGaps'].append({**task, 'issue': 'truncated_one_millisecond'})
            manifest['state'] = 'fatal'
        else:
            midpoint = task['lo'] + (task['hi'] - task['lo']) // 2
            manifest['pending'][0:0] = [{**task, 'lo': task['lo'], 'hi': midpoint},
                                         {**task, 'lo': midpoint, 'hi': task['hi']}]
    else:
        manifest['leaves'].append(record)
    manifest['coverageComplete'] = validate_coverage(manifest)
    # Cross-page/parent-leaf identity and full source audits are separate gates.
    manifest['complete'] = False
    if manifest['coverageComplete']:
        manifest['state'] = 'coverage_complete_audit_pending'
    manifest['inFlight'] = None
    atomic_json(MANIFEST, manifest)


def _run_locked(max_requests=20, max_raw_bytes=10_000_000, max_duration=3600, client=fetch,
                sleep=time.sleep, monotonic=time.monotonic, wall=time.time):
    if not 1 <= max_requests or not 1 <= max_raw_bytes or not 1 <= max_duration <= 86400:
        raise ValueError('Positive limits and duration <=24h required')
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
        check_manifest(manifest)
        if manifest['state'] in ('blocked_403', 'fatal'):
            return {'state': manifest['state'], 'complete': False, 'coverageComplete': False,
                    'getCountThisRound': 0, 'rawBytesThisRound': 0,
                    'leafCount': len(manifest['leaves']), 'splitCount': len(manifest['splits']),
                    'remainingIntervals': len(manifest['pending']),
                    'fatalGapCount': len(manifest['fatalGaps'])}
    else:
        manifest = initial_manifest()
        atomic_json(MANIFEST, manifest)
    manifest['runSerial'] += 1
    manifest['runningPid'] = os.getpid()
    manifest['runningStartedAtUtc'] = utc_now()
    atomic_json(MANIFEST, manifest)
    deadline = monotonic() + max_duration
    sent_in_round = bytes_in_round = 0
    last_sent_monotonic = None
    manifest['state'] = 'running'
    manifest['lastError'] = None
    atomic_json(MANIFEST, manifest)
    while manifest['pending'] and sent_in_round < max_requests and monotonic() < deadline:
        if (CACHE / 'STOP').exists():
            manifest['state'] = 'stopped_marker'
            atomic_json(MANIFEST, manifest)
            break
        if manifest['fatalGaps']:
            manifest['state'] = 'fatal'
            break
        task = manifest['pending'][0]
        name = filename(task)
        existing_raw, existing_receipt = CACHE / name, CACHE / name.replace('.json.gz', '.receipt.json')
        if existing_raw.exists() or existing_receipt.exists():
            if not existing_raw.exists() or not existing_receipt.exists():
                raise ValueError(f'Incomplete immutable response pair: {name}')
            receipt = json.loads(existing_receipt.read_text(encoding='utf-8'))
            body = gzip.decompress(existing_raw.read_bytes())
            if digest(body) != receipt['rawSha256'] or digest(existing_raw.read_bytes()) != receipt['gzipSha256']:
                raise ValueError(f'Changed orphan response: {name}')
            # Crash recovery: reapply the saved bytes without touching either immutable file.
            commit_response(manifest, task, body, receipt['httpStatus'], receipt['sentAtUtc'],
                            receipt['receivedAtUtc'], saved_receipt=receipt)
            continue
        if manifest['inFlight'] is not None:
            manifest['state'] = 'unresolved_inflight_request'
            atomic_json(MANIFEST, manifest)
            break
        remaining = max_raw_bytes - bytes_in_round
        if remaining <= 0:
            manifest['state'] = 'round_raw_byte_limit'
            break
        cache_headroom = CACHE_CAP - manifest['cacheBytes'] - RESERVE_BYTES
        response_limit = min(remaining, MAX_RESPONSE_BYTES, cache_headroom)
        if response_limit <= 0:
            manifest['state'] = 'total_cache_cap'
            break
        limit_state = ('total_cache_cap' if response_limit == cache_headroom else
                       'response_byte_limit' if response_limit == MAX_RESPONSE_BYTES else
                       'round_raw_byte_limit')
        if manifest['lastGetSentEpoch'] is not None:
            elapsed = (monotonic() - last_sent_monotonic if last_sent_monotonic is not None
                       else wall() - manifest['lastGetSentEpoch'])
            if elapsed < 0:
                manifest['state'] = 'clock_regression'
                manifest['lastError'] = {'timeUtc': utc_now(),
                                         'message': 'Clock moved backward; rate limit cannot be proved'}
                break
            wait = max(0.0, 1.0 - elapsed)
            time_left = max(0.0, deadline - monotonic())
            if wait:
                sleep(min(wait, time_left))
            if wait >= time_left:
                manifest['state'] = 'round_duration_limit'
                break
        if (CACHE / 'STOP').exists():
            manifest['state'] = 'stopped_marker'
            atomic_json(MANIFEST, manifest)
            break
        if monotonic() >= deadline:
            manifest['state'] = 'round_duration_limit'
            break
        url = url_for(task)
        sent_in_round += 1
        manifest['httpGetCount'] += 1
        manifest['lastGetSentEpoch'] = wall()
        last_sent_monotonic = monotonic()
        manifest['inFlight'] = {'task': task, 'url': url, 'sentAtUtc': utc_now()}
        atomic_json(MANIFEST, manifest)
        try:
            answer = client(url, response_limit)
            body, status, sent, received = answer[:4]
            partial = answer[4] if len(answer) == 5 else len(body) >= response_limit
            if len(body) > response_limit:
                body, partial = body[:response_limit], True
            bytes_in_round += len(body)
            if partial or status != 200:
                preserve_error(manifest, task, body, status, sent, received,
                               f'partial_response_at_{limit_state}' if partial else f'HTTP {status}',
                               partial=partial, partial_state=limit_state)
                break
            commit_response(manifest, task, body, status, sent, received)
            if manifest['state'] == 'fatal':
                break
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError, ValueError) as exc:
            # Even a transport failure gets a receipt; there was no complete body.
            preserve_error(manifest, task, b'', getattr(exc, 'code', None),
                           utc_now(), utc_now(), str(exc))
            break
    if manifest['state'] == 'running':
        manifest['state'] = ('coverage_complete_audit_pending' if manifest['coverageComplete']
                             else 'round_limit')
    atomic_json(MANIFEST, manifest)
    return {'state': manifest['state'], 'complete': manifest['complete'],
            'coverageComplete': manifest['coverageComplete'],
            'getCountThisRound': sent_in_round, 'rawBytesThisRound': bytes_in_round,
            'leafCount': len(manifest['leaves']), 'splitCount': len(manifest['splits']),
            'remainingIntervals': len(manifest['pending']), 'fatalGapCount': len(manifest['fatalGaps'])}


def run(max_requests=20, max_raw_bytes=10_000_000, max_duration=3600, client=fetch,
        sleep=time.sleep, monotonic=time.monotonic, wall=time.time):
    with exclusive_lock():
        try:
            return _run_locked(max_requests, max_raw_bytes, max_duration, client,
                               sleep, monotonic, wall)
        finally:
            if MANIFEST.exists():
                state = json.loads(MANIFEST.read_text(encoding='utf-8'))
                if state.get('runningPid') == os.getpid():
                    state['lastRunPid'] = state['runningPid']
                    state['runningPid'] = None
                    state['lastRunEndedAtUtc'] = utc_now()
                    atomic_json(MANIFEST, state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-requests', type=int, default=20)
    parser.add_argument('--max-raw-bytes', type=int, default=10_000_000)
    parser.add_argument('--max-duration', type=int, default=3600)
    args = parser.parse_args()
    print(json.dumps(run(args.max_requests, args.max_raw_bytes, args.max_duration), indent=2))


if __name__ == '__main__':
    main()
