"""Acquire only five frozen BTC/ETH USD-M daily mark H1 gaps from Binance Vision.

No signals, returns, API keys, orders, or alteration of monthly archives.
Run once from repository root; --verify checks the preserved snapshot offline.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request
import zipfile


ROOT = Path('research/cache/goal-seven/mark-gaps')
MANIFEST = Path('research/goal-seven/mark-gap-data-manifest.json')
FREEZE = Path('research/goal-seven/open-interest-freeze.json')
BASE = 'https://data.binance.vision/data/futures/um/daily/markPriceKlines'
HOUR = 3600
MAX_GETS = 20
MAX_BYTES = 10_000_000
UTC = dt.timezone.utc


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def utc_now() -> str:
    return dt.datetime.now(UTC).isoformat()


def jobs(freeze: dict) -> list[tuple[str, str]]:
    """Infer exactly the full missing UTC days from the frozen monthly audit."""
    found = []
    for symbol in ('BTCUSDT', 'ETHUSDT'):
        for gap in freeze['dataAudit']['mark'][symbol]['gaps']:
            missing = list(range(gap['after'] + HOUR, gap['before'], HOUR))
            dates = {dt.datetime.fromtimestamp(t, UTC).date().isoformat() for t in missing}
            if len(missing) != 24 or len(dates) != 1:
                raise ValueError(f'Not exactly one full missing UTC day: {symbol} {gap}')
            found.append((symbol, dates.pop()))
    if len(found) != 5 or len(set(found)) != 5:
        raise ValueError('Expected exactly five distinct frozen BTC/ETH mark-gap days')
    return sorted(found)


def expected_times(day: str) -> list[int]:
    start = int(dt.datetime.fromisoformat(day).replace(tzinfo=UTC).timestamp())
    return [start + h * HOUR for h in range(24)]


def safe_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise RuntimeError(f'Conflicting source bytes; preserve old snapshot: {path}')
        return
    with path.open('xb') as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())


def get(url: str, path: Path, counters: dict) -> dict:
    if counters['gets'] >= MAX_GETS:
        raise RuntimeError('20-GET hard limit reached')
    remaining = MAX_BYTES - counters['bytes']
    if remaining <= 0:
        raise RuntimeError('10-MB response hard limit reached')
    counters['gets'] += 1
    status = None
    started = utc_now()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TraderNova-mark-gap-research/1.0'})
        with urllib.request.urlopen(req, timeout=20) as response:
            status = response.status
            raw = response.read(remaining + 1)
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read(remaining + 1)
    received = utc_now()
    if len(raw) > remaining:
        raise RuntimeError('10-MB response hard limit reached; oversized response not retained')
    counters['bytes'] += len(raw)
    saved = path if status == 200 else path.with_name(path.name + f'.HTTP-{status}.bin')
    safe_write(saved, raw)
    return {'url': url, 'status': status, 'sentUtcPc': started, 'receivedUtcPc': received,
            'bytes': len(raw), 'sha256': sha(raw), 'cachePath': saved.as_posix()}


def parse_checksum(raw: bytes, filename: str) -> str:
    match = re.fullmatch(r'([0-9a-fA-F]{64})\s+\*?(.+)', raw.decode('utf-8').strip())
    if not match or Path(match.group(2)).name != filename:
        raise ValueError('Malformed or mismatched official CHECKSUM')
    return match.group(1).lower()


def audit_zip(raw: bytes, day: str) -> dict:
    start = int(dt.datetime.fromisoformat(day).replace(tzinfo=UTC).timestamp() * 1000)
    times = []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = [name for name in archive.namelist() if name.endswith('.csv')]
        if len(names) != 1 or archive.testzip() is not None:
            raise ValueError('Invalid ZIP CSV structure')
        with archive.open(names[0]) as source:
            rows = csv.reader(io.TextIOWrapper(source, encoding='utf-8-sig', newline=''))
            for row in rows:
                if not row:
                    continue
                if row[0] == 'open_time':
                    continue
                if len(row) != 12:
                    raise ValueError('Unexpected mark H1 column count')
                stamp = int(row[0])
                prices = [Decimal(x) for x in row[1:5]]
                if (any(not x.is_finite() or x <= 0 for x in prices)
                        or prices[2] > min(prices[0], prices[3])
                        or prices[1] < max(prices[0], prices[3])):
                    raise ValueError('Invalid mark H1 OHLC')
                times.append(stamp)
    expected = [start + h * HOUR * 1000 for h in range(24)]
    if times != expected:
        raise ValueError(f'Daily mark H1 timestamps do not cover exactly 24 ordered hours: {day}')
    return {'rows': len(times), 'firstOpenTimeMs': times[0], 'lastOpenTimeMs': times[-1],
            'completeMissingDay': True, 'recoveredTimes': [t // 1000 for t in times]}


def verify(document: dict) -> None:
    freeze_raw = FREEZE.read_bytes()
    if sha(freeze_raw) != document['sourceFreezeSha256']:
        raise ValueError('Frozen source audit changed')
    if ([(item['symbol'], item['day']) for item in document['files']]
            != jobs(json.loads(freeze_raw))):
        raise ValueError('Manifest jobs differ from the frozen five missing days')
    for item in document['files']:
        if item['kind'] != 'mark_h1' or item['expectedMissingTimes'] != expected_times(item['day']):
            raise ValueError('Incorrect mark-gap type or expected timestamps')
        for request in item['requests']:
            if sha(Path(request['cachePath']).read_bytes()) != request['sha256']:
                raise ValueError(f'Raw response changed: {request["cachePath"]}')
        if item['status'] == 'verified':
            zip_request, checksum_request = item['requests']
            actual = sha(Path(zip_request['cachePath']).read_bytes())
            official = parse_checksum(Path(checksum_request['cachePath']).read_bytes(),
                                      Path(zip_request['cachePath']).name)
            if (actual != official or item['sha256'] != actual
                    or item['cachePath'] != zip_request['cachePath']):
                raise ValueError('Official CHECKSUM or manifest mismatch')
            audit = audit_zip(Path(zip_request['cachePath']).read_bytes(), item['day'])
            if item['recoveredTimes'] != audit['recoveredTimes'] or item['recoveredTimes'] != item['expectedMissingTimes']:
                raise ValueError('Recovered mark H1 hours differ from frozen gap')


def acquire() -> None:
    if MANIFEST.exists():
        verify(json.loads(MANIFEST.read_text(encoding='utf-8')))
        print('Existing immutable mark-gap snapshot verified; no network GETs')
        return
    freeze_raw = FREEZE.read_bytes()
    selected = jobs(json.loads(freeze_raw))
    counters = {'gets': 0, 'bytes': 0}
    files = []
    stopped = None
    for symbol, day in selected:
        filename = f'{symbol}-1h-{day}.zip'
        url = f'{BASE}/{symbol}/1h/{filename}'
        target = ROOT / symbol / filename
        item = {'symbol': symbol, 'day': day, 'kind': 'mark_h1',
                'status': 'not-attempted', 'cachePath': None, 'sha256': None,
                'expectedMissingTimes': expected_times(day), 'recoveredTimes': [],
                'requests': []}
        files.append(item)
        try:
            zip_response = get(url, target, counters)
            item['requests'].append(zip_response)
            if zip_response['status'] == 404:
                item['status'] = 'missing-at-source'
                continue
            if zip_response['status'] in (403, 429):
                item['status'] = 'access-denied-or-rate-limited'
                stopped = f'HTTP {zip_response["status"]}'
                break
            if zip_response['status'] != 200:
                item['status'] = 'http-error'
                continue
            checksum_response = get(url + '.CHECKSUM',
                                    target.with_name(filename + '.CHECKSUM'), counters)
            item['requests'].append(checksum_response)
            if checksum_response['status'] == 404:
                item['status'] = 'checksum-missing-at-source'
                continue
            if checksum_response['status'] in (403, 429):
                item['status'] = 'access-denied-or-rate-limited'
                stopped = f'HTTP {checksum_response["status"]}'
                break
            if checksum_response['status'] != 200:
                item['status'] = 'checksum-http-error'
                continue
            raw_zip = Path(zip_response['cachePath']).read_bytes()
            official = parse_checksum(Path(checksum_response['cachePath']).read_bytes(), filename)
            if sha(raw_zip) != official:
                raise ValueError('Official ZIP CHECKSUM mismatch')
            item.update(status='verified', cachePath=zip_response['cachePath'],
                        sha256=sha(raw_zip), zipSha256=sha(raw_zip), **audit_zip(raw_zip, day))
        except (ValueError, InvalidOperation, zipfile.BadZipFile, OSError, RuntimeError) as exc:
            item.update(status='invalid', error=f'{type(exc).__name__}: {exc}')
            stopped = 'invalid-source-or-local-error'
            break
    document = {'purpose': 'Only five frozen N12 prerequisite mark H1 gap days; no signals/PnL',
                'source': 'Binance Data Vision official public USD-M daily markPriceKlines',
                'sourceDocumentation': 'https://github.com/binance/binance-public-data/blob/master/README.md',
                'sourceFreezeSha256': sha(freeze_raw), 'retrievedAtUtcPc': utc_now(),
                'maxGets': MAX_GETS, 'maxResponseBytes': MAX_BYTES,
                'actualGets': counters['gets'], 'actualResponseBytes': counters['bytes'],
                'requested': [{'symbol': s, 'day': d} for s, d in selected],
                'files': files, 'allMissingRecovered': len(files) == 5 and
                all(item['status'] == 'verified' for item in files), 'stoppedReason': stopped,
                'contractCaveat': 'Binance USD-M mark H1; not broker/MT5 or historical execution evidence.'}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open('x', encoding='utf-8') as output:
        json.dump(document, output, ensure_ascii=False, indent=2, allow_nan=False)
        output.write('\n')
    verify(document)
    print(f"{sum(item['status'] == 'verified' for item in files)}/5 verified; "
          f"GETs={counters['gets']}; response bytes={counters['bytes']}; stop={stopped or 'none'}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='offline source/hash verification')
    args = parser.parse_args()
    if args.verify:
        verify(json.loads(MANIFEST.read_text(encoding='utf-8')))
        print('Mark-gap manifest and raw responses verified offline')
    else:
        acquire()
