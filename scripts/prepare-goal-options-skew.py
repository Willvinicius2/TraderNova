"""N13 source metadata audit and frozen exploratory daily aggregation; no signals/PnL."""
from __future__ import annotations

import argparse
from contextlib import closing
from decimal import Decimal, InvalidOperation
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / 'research/goal-seven'
TRADE_MANIFEST = RESEARCH / 'options-trades-v2-data-manifest.json'
CATALOG_MANIFEST = RESEARCH / 'options-instruments-data-manifest.json'
PROTOCOL = RESEARCH / 'options-skew-protocol.json'
FREEZE = RESEARCH / 'options-skew-freeze.json'
DAILY = ROOT / 'research/cache/goal-seven/options-skew-daily.json'
DAILY_MANIFEST = RESEARCH / 'options-skew-daily-manifest.json'
TRADE_CACHE = ROOT / 'research/cache/goal-seven/options-trades'
DAY_MS = 86_400_000
FIELDS = ('instrument_name', 'kind', 'base_currency', 'quote_currency',
          'settlement_currency', 'price_index', 'strike', 'option_type',
          'creation_timestamp', 'expiration_timestamp', 'contract_size')


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


IDENTITY = module(ROOT / 'scripts/audit-goal-options-trades.py', 'option_identity')
SIGNALS = module(ROOT / 'scripts/goal_options_skew_signals.py', 'option_skew_signals')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    result = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def read_snapshot(path: Path) -> tuple[dict, str]:
    data = path.read_bytes()
    return json.loads(data), sha(data)


def immutable(path: Path, value: object) -> str:
    data = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f'Immutable output differs: {path}')
    else:
        with path.open('xb') as target:
            target.write(data)
    return sha(data)


def array_objects(source, key: str | None = None):
    """Decode one JSON array item at a time, for raw catalog or normalized file."""
    decoder = json.JSONDecoder(parse_float=Decimal)
    buffer = ''
    started = False
    eof = False
    while True:
        if not eof and len(buffer) < 65536:
            chunk = source.read(65536)
            if chunk:
                buffer += chunk
            else:
                eof = True
        if not started:
            if key:
                pos = buffer.find('"' + key + '"')
                if pos < 0:
                    if eof:
                        raise ValueError('Catalog result array missing')
                    buffer = buffer[-32:]
                    continue
                pos = buffer.find('[', pos)
            else:
                pos = buffer.find('[')
            if pos < 0:
                if eof:
                    raise ValueError('Catalog array missing')
                continue
            buffer = buffer[pos + 1:]
            started = True
        buffer = buffer.lstrip()
        if buffer.startswith(','):
            buffer = buffer[1:].lstrip()
        if buffer.startswith(']'):
            return
        if not buffer:
            if eof:
                raise ValueError('Truncated catalog array')
            continue
        try:
            item, end = decoder.raw_decode(buffer)
        except json.JSONDecodeError:
            if eof:
                raise
            chunk = source.read(65536)
            if chunk:
                buffer += chunk
            else:
                eof = True
            continue
        if not isinstance(item, dict):
            raise ValueError('Non-object catalog item')
        yield item
        buffer = buffer[end:]


def decimal_string(value):
    if isinstance(value, Decimal):
        return format(value, 'f')
    if type(value) is int:
        return str(value)
    return None


def catalog_rows(manifest: dict):
    if (manifest.get('id') != 'N13-deribit-option-instruments-v1'
            or manifest.get('normalization', {}).get('allRecordsPreserved') is not True
            or manifest.get('normalization', {}).get('duplicateNamesDropped') is not False
            or {r.get('symbol') for r in manifest.get('responses', [])} != {'BTC', 'ETH'}):
        raise ValueError('Unexpected catalog manifest')
    for record in manifest['responses']:
        raw = ROOT / record['rawGzipPath']
        norm = ROOT / record['normalizedPath']
        if (record.get('httpStatus') != 200 or file_sha(raw) != record['gzipSha256']
                or file_sha(norm) != record['normalizedSha256']):
            raise ValueError('Catalog compressed/normalized hash or HTTP status mismatch')
        with gzip.open(raw, 'rb') as zipped:
            digest = hashlib.sha256()
            for block in iter(lambda: zipped.read(1024 * 1024), b''):
                digest.update(block)
            if digest.hexdigest() != record['rawSha256']:
                raise ValueError('Catalog raw hash mismatch')
        with gzip.open(raw, 'rt', encoding='utf-8') as source, norm.open('r', encoding='utf-8') as target:
            originals = array_objects(source, 'result')
            normalized = array_objects(target)
            count = 0
            while True:
                original = next(originals, None)
                row = next(normalized, None)
                if original is None or row is None:
                    if original is not None or row is not None:
                        raise ValueError('Catalog raw/normalized row count mismatch')
                    break
                expected = {field: original.get(field) for field in FIELDS}
                for field in ('strike', 'contract_size'):
                    expected[field] = decimal_string(expected[field])
                if row != expected:
                    raise ValueError('Catalog normalization differs from raw response')
                if row.get('base_currency') != record['symbol']:
                    raise ValueError('Catalog currency mismatch')
                count += 1
                yield record['symbol'], row
            if count != record['normalizedRows']:
                raise ValueError('Catalog row count mismatch')


def prerequisites(trades_path: Path, identity_path: Path, catalog_path: Path):
    trades, trades_sha = read_snapshot(trades_path)
    identity, identity_sha = read_snapshot(identity_path)
    catalog, catalog_sha = read_snapshot(catalog_path)
    if (trades.get('id') not in ('N13-deribit-option-trades-data-v1',
                                 'N13-deribit-option-trades-data-v2')
            or trades.get('runningPid') or trades.get('inFlight')
            or trades.get('pending') or trades.get('fatalGaps')
            or trades.get('coverageComplete') is not True
            or identity.get('id') != 'N13-option-trade-identity-audit-v1'
            or identity.get('inputManifestSha256') != trades_sha
            or identity.get('coverageComplete') is not True
            or identity.get('fullIdentityAuditComplete') is not True
            or identity.get('inputCollectorRunning') is not False
            or identity.get('inputManifestChangedDuringAudit') is not False
            or identity.get('sourceIntegrityErrorCount') != 0
            or identity.get('identityConflicts') != 0
            or identity.get('parentMissingInLeaves') != 0
            or identity.get('disjointLeafDuplicateIds') != 0):
        raise ValueError('Complete stopped trade source and exact full identity audit required')
    if trades['scope'].get('symbols') != ['BTC', 'ETH'] or trades['scope'].get('kind') != 'option':
        raise ValueError('Unexpected trade scope')
    return trades, catalog, {'tradeManifestSha256': trades_sha,
                             'identityAuditSha256': identity_sha,
                             'instrumentManifestSha256': catalog_sha}


def leaves_by_day(trades: dict):
    scope = trades['scope']
    lo, hi = IDENTITY.iso_ms(scope['startInclusive']), IDENTITY.iso_ms(scope['endExclusive'])
    if (lo % DAY_MS or hi % DAY_MS or lo >= hi
            or lo != IDENTITY.iso_ms('2021-10-01T00:00:00Z')
            or hi != IDENTITY.iso_ms('2025-01-01T00:00:00Z')):
        raise ValueError('Unexpected N13 daily UTC scope')
    grouped = {}
    for record in trades['leaves']:
        if record['symbol'] not in ('BTC', 'ETH') or record['lo'] < lo or record['hi'] > hi:
            raise ValueError('Leaf outside N13 scope')
        day = record['lo'] // DAY_MS * DAY_MS
        if record['hi'] > day + DAY_MS:
            raise ValueError('Leaf crosses UTC day boundary')
        grouped.setdefault((record['symbol'], day), []).append(record)
    for records in grouped.values():
        records.sort(key=lambda r: (r['lo'], r['hi']))
    for currency in ('BTC', 'ETH'):
        for day in range(lo, hi, DAY_MS):
            cursor = day
            for record in grouped.get((currency, day), []):
                if (record['lo'] != cursor or record['hi'] <= cursor
                        or record.get('hasMore') or record.get('partial')):
                    raise ValueError('Incomplete/nonunique UTC day leaf chain')
                cursor = record['hi']
            if cursor != day + DAY_MS:
                raise ValueError('Missing UTC day leaf coverage')
    return lo, hi, grouped


def page(record: dict, cache_root: Path, version: str):
    policy = 'v1' if record.get('sourceCache') == 'v1' or version == 'v1' else 'v2'
    checked = dict(record, _section='leaves', _policy=policy)
    result, _ = IDENTITY.verified_page(checked, cache_root, policy)
    return result['trades']


def metadata_audit(trades_path: Path, identity_path: Path, catalog_path: Path,
                   cache_root: Path = TRADE_CACHE, report_dir: Path = RESEARCH):
    trades, catalog, hashes = prerequisites(trades_path, identity_path, catalog_path)
    _, _, grouped = leaves_by_day(trades)
    version = trades['id'].rsplit('-', 1)[-1]
    with tempfile.TemporaryDirectory(prefix='n13-metadata-') as temporary:
        with closing(sqlite3.connect(Path(temporary) / 'names.sqlite')) as db:
            db.execute('CREATE TABLE names(currency TEXT,name TEXT,earliest INTEGER,latest INTEGER,'
                       ' appearances INTEGER,PRIMARY KEY(currency,name))')
            appearances = 0
            for key in sorted(grouped):
                for record in grouped[key]:
                    for item in page(record, cache_root, version):
                        stamp, name = item.get('timestamp'), item.get('instrument_name')
                        if type(stamp) is not int or not isinstance(name, str) or not name:
                            raise ValueError('Invalid trade identity metadata')
                        db.execute('''INSERT INTO names VALUES (?,?,?,?,1)
                            ON CONFLICT(currency,name) DO UPDATE SET
                            earliest=min(earliest,excluded.earliest),
                            latest=max(latest,excluded.latest),appearances=appearances+1''',
                                   (key[0], name, stamp, stamp))
                        appearances += 1
                db.commit()
            invalid = []
            invalid_count = 0
            matched = 0
            catalog_names = set()
            for currency, descriptor in catalog_rows(catalog):
                name = descriptor.get('instrument_name')
                if (not isinstance(name, str) or not name
                        or (currency, name) in catalog_names):
                    raise ValueError('Missing/duplicate normalized instrument name')
                catalog_names.add((currency, name))
                row = db.execute('SELECT earliest,latest FROM names WHERE currency=? AND name=?',
                                 (currency, name)).fetchone()
                if row is None:
                    continue
                created, expiry = descriptor.get('creation_timestamp'), descriptor.get('expiration_timestamp')
                try:
                    strike = Decimal(str(descriptor.get('strike')))
                except (InvalidOperation, ValueError, TypeError):
                    strike = None
                valid = (descriptor.get('kind') == 'option'
                         and descriptor.get('base_currency') == currency
                         and descriptor.get('price_index') == currency.lower() + '_usd'
                         and descriptor.get('option_type') in ('put', 'call')
                         and strike is not None and strike.is_finite() and strike > 0
                         and type(created) is int and type(expiry) is int
                         and created <= row[0] <= row[1] < expiry)
                if not valid:
                    invalid_count += 1
                    if len(invalid) < 20:
                        invalid.append({'currency': currency, 'instrument': name})
                db.execute('DELETE FROM names WHERE currency=? AND name=?', (currency, name))
                matched += 1
            remaining = db.execute('SELECT COUNT(*) FROM names').fetchone()[0]
            missing = [{'currency': a, 'instrument': b} for a, b in db.execute(
                'SELECT currency,name FROM names LIMIT 20')]
    if any(file_sha(path) != expected for path, expected in
           ((trades_path, hashes['tradeManifestSha256']),
            (identity_path, hashes['identityAuditSha256']),
            (catalog_path, hashes['instrumentManifestSha256']))):
        raise ValueError('Source manifest/audit changed during metadata audit')
    snapshot = sha(json.dumps(hashes, sort_keys=True).encode())
    output = {'id': 'N13-option-metadata-audit-v1', 'snapshotSha256': snapshot, **hashes,
              'identityInputManifestSha256': hashes['tradeManifestSha256'],
              'tradeOccurrencesInLeaves': appearances, 'matchedInstrumentNames': matched,
              'missingInstrumentNames': remaining, 'invalidInstrumentNames': invalid_count,
              'missingExamples': missing, 'invalidExamples': invalid,
              'fullMetadataAuditComplete': remaining == 0 and invalid_count == 0,
              'fullDataAuditComplete': False, 'dataApproved': False,
              'historicalOnly': True}
    target = report_dir / ('options-metadata-audit-' + snapshot[:16] + '.json')
    immutable(target, output)
    return target, output


def freeze_inputs(freeze: dict, files: dict[str, Path]):
    if (freeze.get('id') != 'N13-option-skew-preparation-freeze-v1'
            or freeze.get('historicalAssumption') is not True
            or set(freeze.get('sha256', {})) != set(files)
            or not isinstance(freeze.get('hashes'), dict)):
        raise ValueError('Exact N13 historical freeze required')
    all_files = dict(files)
    for key in freeze['hashes']:
        candidate = Path(key)
        if candidate.is_absolute() or '..' in candidate.parts:
            raise ValueError('Unsafe freeze path')
        all_files[key] = ROOT / candidate
    for key, path in files.items():
        if file_sha(path) != freeze['sha256'][key]:
            raise ValueError(f'Freeze hash mismatch: {key}')
    for key in freeze['hashes']:
        if file_sha(all_files[key]) != freeze['hashes'][key]:
            raise ValueError(f'Freeze path hash mismatch: {key}')
    return all_files


def aggregate(trades_path: Path, identity_path: Path, catalog_path: Path,
              metadata_path: Path, freeze_path: Path = FREEZE,
              cache_root: Path = TRADE_CACHE, daily_path: Path = DAILY,
              manifest_path: Path = DAILY_MANIFEST):
    files = {'prepareScript': Path(__file__),
             'prepareTests': ROOT / 'tests/goal-options-skew-prepare.py',
             'signalGenerator': ROOT / 'scripts/goal_options_skew_signals.py',
             'protocol': PROTOCOL, 'tradeManifest': trades_path,
             'identityAudit': identity_path, 'instrumentManifest': catalog_path,
             'metadataAudit': metadata_path}
    freeze, freeze_sha = read_snapshot(freeze_path)
    paths = freeze.get('auditPaths')
    if (not isinstance(paths, dict) or set(paths) != {'identityAudit', 'metadataAudit'}
            or paths['identityAudit'] != identity_path.resolve().relative_to(ROOT).as_posix()
            or paths['metadataAudit'] != metadata_path.resolve().relative_to(ROOT).as_posix()):
        raise ValueError('Freeze audit paths differ from CLI inputs')
    all_files = freeze_inputs(freeze, files)  # Before reading raw trade IV.
    trades, catalog, hashes = prerequisites(trades_path, identity_path, catalog_path)
    metadata, metadata_sha = read_snapshot(metadata_path)
    if (metadata.get('id') != 'N13-option-metadata-audit-v1'
            or metadata.get('fullMetadataAuditComplete') is not True
            or any(metadata.get(key) != value for key, value in hashes.items())
            or metadata_sha != freeze['sha256']['metadataAudit']):
        raise ValueError('Exact completed metadata audit required')
    lo, hi, grouped = leaves_by_day(trades)
    instruments = {}
    for currency, row in catalog_rows(catalog):
        name = row.get('instrument_name')
        if name in instruments:
            raise ValueError('Duplicate instrument name in catalog')
        instruments[name] = row
    version = trades['id'].rsplit('-', 1)[-1]
    series = {'BTCUSDT': [], 'ETHUSDT': []}
    for currency, symbol in (('BTC', 'BTCUSDT'), ('ETH', 'ETHUSDT')):
        for day in range(lo, hi, DAY_MS):
            records = grouped.get((currency, day), [])
            cursor = day
            for record in records:
                if record['lo'] != cursor or record['hi'] <= cursor or record.get('hasMore'):
                    raise ValueError('Incomplete day leaf chain')
                cursor = record['hi']
            if cursor != day + DAY_MS:
                raise ValueError('Missing day leaf coverage')
            def day_trades():
                for record in records:
                    yield from page(record, cache_root, version)
            series[symbol].append(SIGNALS.daily_skew(
                day_trades(), instruments, currency, day // 1000,
                coverage_complete=True, historical_assumption=True))
    for key, path in files.items():
        if file_sha(path) != freeze['sha256'][key]:
            raise ValueError(f'Frozen input changed during aggregation: {key}')
    for key in freeze['hashes']:
        if file_sha(all_files[key]) != freeze['hashes'][key]:
            raise ValueError(f'Frozen path changed during aggregation: {key}')
    if file_sha(freeze_path) != freeze_sha:
        raise ValueError('Freeze changed during aggregation')
    series_paths = {}
    for symbol, rows in series.items():
        path = daily_path.with_name(daily_path.stem + '-' + symbol + daily_path.suffix)
        series_paths[symbol] = {'cachePath': path.resolve().relative_to(ROOT).as_posix(),
                                'sha256': immutable(path, rows),
                                'rows': len(rows)}
    output = {'id': 'N13-option-skew-daily-preparation-v1',
              'historicalAssumption': True, 'prospectiveEvidenceComplete': False,
              'freezeSha256': freeze_sha, 'inputSha256': freeze['sha256'],
              'series': series_paths, 'validated': False,
              'daysPerSymbol': (hi - lo) // DAY_MS,
              'signalsComputed': False, 'pnlComputed': False, 'dataApproved': False}
    immutable(manifest_path, output)
    return manifest_path, output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('audit', 'aggregate'))
    parser.add_argument('--trade-manifest', type=Path, default=TRADE_MANIFEST)
    parser.add_argument('--identity-audit', type=Path, required=True)
    parser.add_argument('--catalog-manifest', type=Path, default=CATALOG_MANIFEST)
    parser.add_argument('--metadata-audit', type=Path)
    parser.add_argument('--freeze', type=Path, default=FREEZE)
    args = parser.parse_args()
    if args.phase == 'audit':
        path, output = metadata_audit(args.trade_manifest, args.identity_audit,
                                      args.catalog_manifest)
    else:
        if args.metadata_audit is None:
            parser.error('--metadata-audit required for aggregate')
        path, output = aggregate(args.trade_manifest, args.identity_audit,
                                 args.catalog_manifest, args.metadata_audit, args.freeze)
    print(json.dumps({'output': str(path), 'status': output.get('fullMetadataAuditComplete',
                                                              'frozen_historical_daily')}))


if __name__ == '__main__':
    main()
