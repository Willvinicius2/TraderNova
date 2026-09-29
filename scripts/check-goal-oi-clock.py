"""Compare one recent public OI archive with official Unix-timestamped REST.

This audits the timestamp/unit mapping only, never returns, signals or PnL.
Contemporary equality corroborates UTC for this sample, not historical vintages.
"""
from datetime import datetime, timezone
from decimal import Decimal
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'research/cache/goal-seven/open-interest-clock'
OUTPUT = ROOT / 'research/goal-seven/open-interest-clock-audit.json'
OFFSET_OUTPUT = ROOT / 'research/goal-seven/open-interest-clock-offset-audit.json'
DAY = '2026-09-27'


def acquire(url, filename):
    path = CACHE / filename
    if path.exists():
        raw = path.read_bytes()
    else:
        with urllib.request.urlopen(url, timeout=30) as response:
            raw = response.read()
        path.write_bytes(raw)
    return raw, {'url': url, 'path': path.relative_to(ROOT).as_posix(),
                 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def main():
    if OUTPUT.exists():
        raise ValueError('Existing immutable audit; do not overwrite')
    CACHE.mkdir(parents=True, exist_ok=True)
    results = {}
    start = int(datetime.fromisoformat(DAY).replace(tzinfo=timezone.utc).timestamp())
    for symbol in ('BTCUSDT', 'ETHUSDT', 'SOLUSDT'):
        name = f'{symbol}-metrics-{DAY}.zip'
        url = f'https://data.binance.vision/data/futures/um/daily/metrics/{symbol}/{name}'
        raw, archive = acquire(url, name)
        checksum, checksum_record = acquire(url + '.CHECKSUM', name + '.CHECKSUM')
        if archive['sha256'] != checksum.decode().split()[0]:
            raise ValueError('Official archive checksum mismatch')
        query = urllib.parse.urlencode({'symbol': symbol, 'period': '5m',
                                        'startTime': start * 1000,
                                        'endTime': (start + 3600) * 1000 - 1, 'limit': 500})
        response, api = acquire('https://fapi.binance.com/futures/data/openInterestHist?' + query,
                                f'{symbol}-{DAY}-first-hour-rest.json')
        points = json.loads(response)
        if not isinstance(points, list) or len(points) != 12:
            raise ValueError(f'Expected 12 five-minute observations: {symbol}')
        with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
            if len(zipped.namelist()) != 1:
                raise ValueError('Unexpected archive contents')
            records = list(csv.DictReader(io.TextIOWrapper(zipped.open(zipped.namelist()[0]), encoding='utf-8-sig')))
        by_time = {int(datetime.fromisoformat(row['create_time']).replace(tzinfo=timezone.utc).timestamp()) * 1000: row
                   for row in records}
        comparisons = []
        for row in points:
            stamp = int(row['timestamp'])
            archived = by_time.get(stamp)
            comparisons.append({'timestampMs': stamp, 'archiveTimestampPresent': archived is not None,
                                'quantityEqual': archived is not None and Decimal(archived['sum_open_interest']) == Decimal(row['sumOpenInterest']),
                                'notionalEqual': archived is not None and Decimal(archived['sum_open_interest_value']) == Decimal(row['sumOpenInterestValue'])})
        results[symbol] = {'archive': archive, 'checksum': checksum_record, 'api': api,
                           'comparisons': comparisons,
                           'allQuantitiesEqualAtUTC': all(row['quantityEqual'] for row in comparisons)}
    result = {'purpose': 'Contemporary archive create_time / REST Unix timestamp and quantity correspondence only',
              'acquiredAtUtc': datetime.now(timezone.utc).isoformat(), 'sampleDay': DAY,
              'symbols': results, 'historicalTimezoneProven': False, 'pointInTimeAvailabilityProven': False,
              'returnsOrSignalsExamined': False}
    OUTPUT.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({s: {'points': len(v['comparisons']), 'quantityMatchesUTC': v['allQuantitiesEqualAtUTC']}
                      for s, v in results.items()}))


def offset_audit(verify=False):
    if OFFSET_OUTPUT.exists() and not verify:
        raise ValueError('Existing offset audit; do not overwrite')
    original = json.loads(OUTPUT.read_text())
    results = {}
    for symbol, evidence in original['symbols'].items():
        for key in ('archive', 'checksum', 'api'):
            item = evidence[key]
            if hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() != item['sha256']:
                raise ValueError('Original audit source changed')
        with zipfile.ZipFile(ROOT / evidence['archive']['path']) as zipped:
            rows = list(csv.DictReader(io.TextIOWrapper(zipped.open(zipped.namelist()[0]), encoding='utf-8-sig')))
        # The discovered offset is a timestamp-semantics audit, not strategy tuning.
        by_end = {int(datetime.fromisoformat(row['create_time']).replace(tzinfo=timezone.utc).timestamp()) * 1000 + 300000: row
                  for row in rows}
        api_rows = json.loads((ROOT / evidence['api']['path']).read_text())
        overlaps = []
        absent = []
        for point in api_rows:
            stamp = int(point['timestamp'])
            archived = by_end.get(stamp)
            if archived is None:
                absent.append(stamp)
                continue
            overlaps.append({'apiTimestampMs': stamp, 'archiveCreateTime': archived['create_time'],
                             'quantityEqual': Decimal(archived['sum_open_interest']) == Decimal(point['sumOpenInterest']),
                             'notionalEqual': Decimal(archived['sum_open_interest_value']) == Decimal(point['sumOpenInterestValue'])})
        results[symbol] = {'comparisons': overlaps, 'apiTimesOutsideArchiveDayAfterShift': absent,
                           'allOverlappingQuantitiesEqual': bool(overlaps) and all(x['quantityEqual'] for x in overlaps),
                           'allOverlappingNotionalsEqual': bool(overlaps) and all(x['notionalEqual'] for x in overlaps)}
    result = {'sampleDay': DAY, 'priorZeroOffsetAuditSha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
              'archiveCreateTimeInterpretation': 'UTC-labeled five-minute slot start; REST statistical timestamp corresponds to start+300 seconds in this sample',
              'mappingSeconds': 300, 'symbols': results,
              'historicalMappingProven': False, 'historicalPublicationAvailabilityProven': False,
              'returnsOrSignalsExamined': False}
    if verify:
        if json.loads(OFFSET_OUTPUT.read_text()) != result:
            raise ValueError('Saved clock comparison differs from preserved raw evidence')
    else:
        OFFSET_OUTPUT.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({s: {'overlappingPoints': len(v['comparisons']),
                          'quantityEqual': v['allOverlappingQuantitiesEqual'],
                          'notionalEqual': v['allOverlappingNotionalsEqual']} for s, v in results.items()}))


if __name__ == '__main__':
    offset_audit(verify='--verify' in sys.argv) if '--offset-audit' in sys.argv else main()
