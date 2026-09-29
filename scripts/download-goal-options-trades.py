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
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'research/cache/goal-seven/options-trades'
MANIFEST = ROOT / 'research/goal-seven/options-trades-data-manifest.json'
API = 'https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time'
START = datetime(2021, 10, 1, tzinfo=timezone.utc)
END = datetime(2025, 1, 1, tzinfo=timezone.utc)
SYMBOLS = ('BTC', 'ETH')
COUNT = 1000  # Published API limit, even if the history host permits more.
CACHE_CAP = 2_000_000_000


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
    return f"{task['symbol']}-{task['lo']}-{task['hi']}.json.gz"


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
    return {'id': 'N13-deribit-option-trades-data-v1', 'createdAtUtc': utc_now(),
            'source': API, 'scope': {'symbols': list(SYMBOLS), 'startInclusive': START.isoformat(),
                                    'endExclusive': END.isoformat(), 'kind': 'option'},
            'request': {'count': COUNT, 'sorting': 'asc', 'include_old': True,
                        'windowConvention': '[lo,hi), API end_timestamp=hi-1'},
            'pending': tasks(), 'leaves': [], 'splits': [], 'rejected': [], 'errors': [],
            'fatalGaps': [],
            'httpGetCount': 0, 'rawResponseBytes': 0, 'cacheBytes': 0,
            'lastGetSentEpoch': None, 'inFlight': None,
            'coverageComplete': False, 'crossPageIdentityAuditComplete': False,
            'fullDataAuditComplete': False, 'complete': False,
            'state': 'pending', 'lastError': None}


def check_manifest(manifest):
    expected = initial_manifest()
    for key in ('id', 'source', 'scope', 'request'):
        if manifest.get(key) != expected[key]:
            raise ValueError(f'Manifest scope mismatch: {key}')
    for record in manifest['leaves'] + manifest['splits'] + manifest['rejected'] + manifest['errors']:
        raw_path = CACHE / record['file']
        receipt_path = CACHE / record['receiptFile']
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
    for trade in trades:
        if not isinstance(trade, dict):
            raise ValueError('Invalid trade record object')
        stamp, trade_id = trade.get('timestamp'), trade.get('trade_id')
        if (not isinstance(stamp, int) or isinstance(stamp, bool)
                or not task['lo'] <= stamp < task['hi'] or not isinstance(trade_id, str)):
            raise ValueError('Trade outside requested half-open interval or missing ID')
        if previous is not None and stamp < previous:
            raise ValueError('Trade page not timestamp-ascending')
        previous = stamp
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
            'lastTimestampMs': trades[-1]['timestamp'] if trades else None}


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


def preserve_error(manifest, task, body, status, sent, received, reason, *, partial=False):
    receipt = store_response(manifest, task, body, status, sent, received,
                             partial=partial, error=True)
    record = {**receipt, 'validationError': reason}
    manifest['errors'].append(record)
    manifest['lastError'] = {'timeUtc': utc_now(), 'url': receipt['url'],
                             'httpStatus': status, 'message': reason,
                             'partial': partial, 'receiptFile': receipt['receiptFile']}
    manifest['state'] = ('blocked_403' if status == 403 else
                         'round_raw_byte_limit' if partial else
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


def run(max_requests=20, max_raw_bytes=10_000_000, max_duration=3600, client=fetch,
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
    deadline = monotonic() + max_duration
    sent_in_round = bytes_in_round = 0
    manifest['state'] = 'running'
    manifest['lastError'] = None
    atomic_json(MANIFEST, manifest)
    while manifest['pending'] and sent_in_round < max_requests and monotonic() < deadline:
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
        if CACHE_CAP - manifest['cacheBytes'] < remaining + 10_000:
            manifest['state'] = 'total_cache_cap'
            break
        if manifest['lastGetSentEpoch'] is not None:
            sleep(max(0.0, 1.0 - (wall() - manifest['lastGetSentEpoch'])))
        if monotonic() >= deadline:
            break
        url = url_for(task)
        sent_in_round += 1
        manifest['httpGetCount'] += 1
        manifest['lastGetSentEpoch'] = wall()
        manifest['inFlight'] = {'task': task, 'url': url, 'sentAtUtc': utc_now()}
        atomic_json(MANIFEST, manifest)
        try:
            answer = client(url, remaining)
            body, status, sent, received = answer[:4]
            partial = answer[4] if len(answer) == 5 else len(body) > remaining
            if len(body) > remaining:
                body, partial = body[:remaining], True
            bytes_in_round += len(body)
            if partial or status != 200:
                preserve_error(manifest, task, body, status, sent, received,
                               'partial_response_due_to_raw_byte_limit' if partial else f'HTTP {status}',
                               partial=partial)
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-requests', type=int, default=20)
    parser.add_argument('--max-raw-bytes', type=int, default=10_000_000)
    parser.add_argument('--max-duration', type=int, default=3600)
    args = parser.parse_args()
    print(json.dumps(run(args.max_requests, args.max_raw_bytes, args.max_duration), indent=2))


if __name__ == '__main__':
    main()
