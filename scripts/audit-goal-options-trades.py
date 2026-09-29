"""Read-only N13 option-trade identity audit; no signal, pricing or PnL code.

Processes one verified gzip response at a time and indexes only trade identity
metadata in a temporary SQLite database. Never changes a collector manifest.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
V1_MANIFEST = ROOT / 'research/goal-seven/options-trades-data-manifest.json'
V2_MANIFEST = ROOT / 'research/goal-seven/options-trades-v2-data-manifest.json'
CACHE_BASE = ROOT / 'research/cache/goal-seven/options-trades'
REPORT_DIR = ROOT / 'research/goal-seven'
SOURCE = 'https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time'


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def iso_ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp() * 1000)


def cache_paths(record: dict, base: Path) -> tuple[Path, Path]:
    roots = ([base] if record.get('sourceCache') == 'v1' else
             [base, base.with_name(base.name + '-v2')])
    matches = []
    for root in roots:
        raw, receipt = root / record['file'], root / record['receiptFile']
        if raw.is_file() and receipt.is_file():
            matches.append((raw, receipt))
    for raw, receipt in matches:
        if digest(raw.read_bytes()) == record['gzipSha256']:
            return raw, receipt
    if matches:
        return matches[0]  # Verification will report the changed bytes.
    raise FileNotFoundError(f"Missing raw/receipt pair for {record['file']}")


def request_contract(record: dict, receipt: dict, policy: str) -> list[str]:
    errors = []
    receipt_fields = ('symbol', 'lo', 'hi', 'file', 'receiptFile', 'url', 'sentAtUtc',
                      'receivedAtUtc', 'httpStatus', 'rawBytes', 'rawSha256',
                      'gzipBytes', 'gzipSha256', 'partial')
    if set(receipt) != set(receipt_fields):
        errors.append('receipt has unexpected/missing fields')
    for field in receipt_fields:
        if receipt.get(field) != record.get(field):
            errors.append(f'receipt field differs: {field}')
    expected_count = '1000' if policy == 'v1' else '10000'
    parsed = urlparse(record['url'])
    query = parse_qs(parsed.query)
    expected = {'currency': record['symbol'], 'kind': 'option',
                'start_timestamp': str(record['lo']),
                'end_timestamp': str(record['hi'] - 1),
                'count': expected_count, 'sorting': 'asc', 'include_old': 'true'}
    if parsed.scheme + '://' + parsed.netloc + parsed.path != SOURCE:
        errors.append('request endpoint differs')
    for name, value in expected.items():
        if query.get(name) != [value]:
            errors.append(f'request query differs: {name}')
    if set(query) != set(expected):
        errors.append('request has unexpected/missing query fields')
    try:
        if iso_ms(record['sentAtUtc']) > iso_ms(record['receivedAtUtc']):
            errors.append('PC receipt precedes send')
    except (TypeError, ValueError):
        errors.append('invalid PC send/receive timestamp')
    if record['httpStatus'] != 200 or record['partial']:
        errors.append('non-200 or partial accepted response')
    return errors


def verified_page(record: dict, base: Path, policy: str) -> tuple[dict, dict]:
    """Verify gzip, decompressed raw and receipt before decoding trade JSON."""
    raw_path, receipt_path = cache_paths(record, base)
    packed = raw_path.read_bytes()
    if len(packed) != record['gzipBytes'] or digest(packed) != record['gzipSha256']:
        raise ValueError('gzip byte/hash mismatch')
    body = gzip.decompress(packed)
    if len(body) != record['rawBytes'] or digest(body) != record['rawSha256']:
        raise ValueError('decompressed raw byte/hash mismatch')
    receipt_raw = receipt_path.read_bytes()
    receipt = json.loads(receipt_raw)
    errors = request_contract(record, receipt, policy)
    if errors:
        raise ValueError('; '.join(errors))
    message = json.loads(body)
    result = message.get('result') if isinstance(message, dict) else None
    if (not isinstance(result, dict) or message.get('error')
            or not isinstance(result.get('trades'), list)
            or not isinstance(result.get('has_more'), bool)):
        raise ValueError('invalid JSON-RPC trade response shape')
    if (len(result['trades']) != record['records']
            or result['has_more'] != record['hasMore']):
        raise ValueError('raw trade count/has_more differs from manifest')
    stamps = []
    seen_ids = {}
    identical = conflicting = 0
    for trade in result['trades']:
        if not isinstance(trade, dict) or type(trade.get('timestamp')) is not int:
            raise ValueError('trade/timestamp shape invalid')
        stamps.append(trade['timestamp'])
        trade_id = trade.get('trade_id')
        payload_hash = digest(canonical(trade))
        if trade_id in seen_ids:
            if seen_ids[trade_id] == payload_hash:
                identical += 1
            else:
                conflicting += 1
        else:
            seen_ids[trade_id] = payload_hash
    if any(right < left for left, right in zip(stamps, stamps[1:])):
        raise ValueError('timestamps descend despite sorting=asc')
    observations = {'firstTimestampMs': stamps[0] if stamps else None,
                    'lastTimestampMs': stamps[-1] if stamps else None,
                    'minTimestampMs': min(stamps) if stamps else None,
                    'maxTimestampMs': max(stamps) if stamps else None,
                    'timestampsNondecreasingInSourceOrder': True,
                    'uniqueTradeIds': len(seen_ids),
                    'identicalDuplicates': identical,
                    'duplicateConflicts': conflicting}
    for key, actual in observations.items():
        if key in record and record[key] != actual:
            raise ValueError(f'raw timestamp/duplicate evidence differs from manifest: {key}')
    proof = {'section': record['_section'], 'sourceCache': record.get('sourceCache', policy),
             'file': record['file'], 'lo': record['lo'], 'hi': record['hi'],
             'gzipSha256': digest(packed), 'rawSha256': digest(body),
             'receiptSha256': digest(receipt_raw), 'receiptFile': record['receiptFile']}
    return result, proof


def coverage(manifest: dict) -> tuple[bool, list[str]]:
    errors = []
    if manifest.get('pending'):
        errors.append('pending intervals')
    if manifest.get('fatalGaps'):
        errors.append('fatal gaps')
    if manifest.get('inFlight'):
        errors.append('in-flight request')
    if not manifest.get('coverageComplete'):
        errors.append('collector coverageComplete=false')
    scope = manifest['scope']
    lo, hi = iso_ms(scope['startInclusive']), iso_ms(scope['endExclusive'])
    for currency in scope['symbols']:
        cursor = lo
        leaves = sorted((r for r in manifest['leaves'] if r['symbol'] == currency),
                        key=lambda r: (r['lo'], r['hi']))
        for leaf in leaves:
            if (leaf['lo'] != cursor or leaf['hi'] <= leaf['lo'] or
                    leaf.get('hasMore') or leaf.get('partial')):
                errors.append(f'leaf interval/truncation gap for {currency}')
                break
            cursor = leaf['hi']
        if cursor != hi:
            errors.append(f'leaf chain incomplete for {currency}')
    return not errors, errors


def init_db(connection: sqlite3.Connection) -> None:
    connection.executescript('''
        CREATE TABLE identity_rows(currency TEXT, trade_id TEXT, payload_hash TEXT,
            timestamp_ms INTEGER, instrument TEXT, first_source TEXT,
            PRIMARY KEY(currency, trade_id));
        CREATE TABLE leaf_rows(currency TEXT, trade_id TEXT, payload_hash TEXT,
            timestamp_ms INTEGER, instrument TEXT, first_source TEXT,
            first_lo INTEGER, first_hi INTEGER, PRIMARY KEY(currency, trade_id));
        CREATE TABLE leaf_payloads(currency TEXT, trade_id TEXT, payload_hash TEXT,
            PRIMARY KEY(currency, trade_id, payload_hash));
        CREATE TABLE leaf_occurrences(currency TEXT, trade_id TEXT, source TEXT,
            lo INTEGER, hi INTEGER,
            PRIMARY KEY(currency, trade_id, source));
        CREATE TABLE parent_rows(currency TEXT, trade_id TEXT, payload_hash TEXT,
            timestamp_ms INTEGER, instrument TEXT, first_source TEXT,
            PRIMARY KEY(currency, trade_id, payload_hash));
        CREATE TABLE conflicts(currency TEXT, trade_id TEXT, first_hash TEXT,
            other_hash TEXT, first_source TEXT, other_source TEXT,
            timestamp_diff INTEGER, PRIMARY KEY(currency, trade_id, other_hash));
        CREATE TABLE disjoint_leaf_duplicates(currency TEXT, trade_id TEXT,
            first_source TEXT, other_source TEXT, PRIMARY KEY(currency, trade_id));
    ''')


def index_trade(connection: sqlite3.Connection, record: dict, trade: dict,
                counters: dict) -> None:
    currency, trade_id = record['symbol'], trade.get('trade_id')
    stamp, instrument = trade.get('timestamp'), trade.get('instrument_name')
    if (not isinstance(trade_id, str) or not trade_id or type(stamp) is not int
            or not record['lo'] <= stamp < record['hi']
            or not isinstance(instrument, str) or not instrument):
        raise ValueError('trade identity/time/instrument invalid for response window')
    payload_hash = digest(canonical(trade))
    source = record['_policy'] + ':' + record['file']
    old = connection.execute('SELECT payload_hash,timestamp_ms,first_source FROM identity_rows '
                             'WHERE currency=? AND trade_id=?', (currency, trade_id)).fetchone()
    if old is None:
        connection.execute('INSERT INTO identity_rows VALUES (?,?,?,?,?,?)',
                           (currency, trade_id, payload_hash, stamp, instrument, source))
    elif old[0] != payload_hash:
        connection.execute('INSERT OR IGNORE INTO conflicts VALUES (?,?,?,?,?,?,?)',
                           (currency, trade_id, old[0], payload_hash, old[2], source,
                            int(old[1] != stamp)))
    if record['_section'] == 'leaves':
        counters['leafOccurrences'] += 1
        connection.execute('INSERT OR IGNORE INTO leaf_payloads VALUES (?,?,?)',
                           (currency, trade_id, payload_hash))
        disjoint = connection.execute('''SELECT source FROM leaf_occurrences
            WHERE currency=? AND trade_id=? AND source<>?
              AND (hi<=? OR ?<=lo) LIMIT 1''',
            (currency, trade_id, source, record['lo'], record['hi'])).fetchone()
        if disjoint:
            connection.execute('INSERT OR IGNORE INTO disjoint_leaf_duplicates VALUES (?,?,?,?)',
                               (currency, trade_id, disjoint[0], source))
        connection.execute('INSERT OR IGNORE INTO leaf_occurrences VALUES (?,?,?,?,?)',
                           (currency, trade_id, source, record['lo'], record['hi']))
        prior = connection.execute('SELECT payload_hash,first_source,first_lo,first_hi '
                                   'FROM leaf_rows WHERE currency=? AND trade_id=?',
                                   (currency, trade_id)).fetchone()
        if prior is None:
            connection.execute('INSERT INTO leaf_rows VALUES (?,?,?,?,?,?,?,?)',
                               (currency, trade_id, payload_hash, stamp, instrument, source,
                                record['lo'], record['hi']))
        else:
            if prior[0] == payload_hash:
                counters['identicalLeafDuplicates'] += 1
    else:
        counters['parentOccurrences'] += 1
        connection.execute('INSERT OR IGNORE INTO parent_rows VALUES (?,?,?,?,?,?)',
                           (currency, trade_id, payload_hash, stamp, instrument, source))


def audit(manifest_path: Path, cache_root: Path) -> dict:
    initial_raw = manifest_path.read_bytes()
    manifest_sha = digest(initial_raw)
    manifest = json.loads(initial_raw)
    if manifest.get('id') not in ('N13-deribit-option-trades-data-v1',
                                  'N13-deribit-option-trades-data-v2'):
        raise ValueError('Unknown N13 collector manifest version')
    version = manifest['id'].rsplit('-', 1)[-1]
    if manifest.get('source') != SOURCE or manifest['scope'].get('kind') != 'option':
        raise ValueError('Unexpected source/scope')
    report = {'id': 'N13-option-trade-identity-audit-v1',
              'inputManifestPath': str(manifest_path), 'inputManifestSha256': manifest_sha,
              'inputManifestVersion': version, 'inputManifestState': manifest.get('state'),
              'inputCollectorRunning': bool(manifest.get('runningPid') or manifest.get('state') == 'running'),
              'scope': manifest['scope'], 'rawPagesAudited': 0,
              'sourceIntegrityErrorCount': 0, 'sourceIntegrityErrorSamples': [],
              'leafOccurrences': 0, 'parentOccurrences': 0,
              'identicalLeafDuplicates': 0, 'httpHeadersPreserved': False,
              'fullDataAuditComplete': False, 'dataApproved': False}
    inventory = []
    claims = [{key: item.get(key) for key in
               ('file', 'receiptFile', 'sourceCache', 'symbol', 'lo', 'hi',
                'gzipSha256', 'rawSha256', 'records', 'hasMore')}
              | {'section': section}
              for section in ('leaves', 'splits') for item in manifest[section]]
    report['inputInventoryClaimRootSha256'] = digest(canonical(sorted(
        claims, key=lambda x: (x['section'], x['sourceCache'] or version, x['file']))))
    report['inputInventoryClaims'] = len(claims)
    sent_by_policy: dict[str, list[int]] = {'v1': [], 'v2': []}
    cache_root.mkdir(parents=True, exist_ok=True)
    descriptor, db_name = tempfile.mkstemp(prefix='identity-audit-', suffix='.sqlite', dir=cache_root)
    os.close(descriptor)
    try:
        with closing(sqlite3.connect(db_name)) as connection:
            init_db(connection)
            for section in ('leaves', 'splits'):
                for item in manifest[section]:
                    record = dict(item, _section=section)
                    policy = 'v1' if record.get('sourceCache') == 'v1' or version == 'v1' else 'v2'
                    record['_policy'] = policy
                    try:
                        page, proof = verified_page(record, cache_root, policy)
                        inventory.append(proof)
                        sent_by_policy[policy].append(iso_ms(record['sentAtUtc']))
                        page_counters = {'leafOccurrences': 0, 'parentOccurrences': 0,
                                         'identicalLeafDuplicates': 0}
                        with connection:
                            for trade in page['trades']:
                                if not isinstance(trade, dict):
                                    raise ValueError('non-object trade record')
                                index_trade(connection, record, trade, page_counters)
                        for key, value in page_counters.items():
                            report[key] += value
                        report['rawPagesAudited'] += 1
                    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError,
                            gzip.BadGzipFile, EOFError) as exc:
                        report['sourceIntegrityErrorCount'] += 1
                        if len(report['sourceIntegrityErrorSamples']) < 20:
                            report['sourceIntegrityErrorSamples'].append(
                                {'section': section, 'file': record.get('file'),
                                 'error': f'{type(exc).__name__}: {exc}'})
            connection.commit()
            scalar = lambda sql: connection.execute(sql).fetchone()[0]
            report['uniqueLeafTradeIds'] = scalar('SELECT COUNT(*) FROM leaf_rows')
            report['uniqueParentIdentities'] = scalar('SELECT COUNT(*) FROM parent_rows')
            report['identityConflicts'] = scalar('''SELECT COUNT(*) FROM
                (SELECT currency,trade_id FROM conflicts GROUP BY currency,trade_id)''')
            report['timestampConflicts'] = scalar('SELECT COUNT(*) FROM conflicts WHERE timestamp_diff=1')
            report['disjointLeafDuplicateIds'] = scalar('SELECT COUNT(*) FROM disjoint_leaf_duplicates')
            report['parentMissingInLeaves'] = scalar('''SELECT COUNT(*) FROM parent_rows p
                LEFT JOIN leaf_payloads l ON l.currency=p.currency AND l.trade_id=p.trade_id
                    AND l.payload_hash=p.payload_hash WHERE l.trade_id IS NULL''')
            report['identityConflictSamples'] = [
                {'currency': row[0], 'tradeId': row[1], 'firstHash': row[2],
                 'otherHash': row[3], 'firstSource': row[4], 'otherSource': row[5]}
                for row in connection.execute('SELECT currency,trade_id,first_hash,other_hash,'
                                              'first_source,other_source FROM conflicts LIMIT 20')]
            report['parentMissingSamples'] = [
                {'currency': row[0], 'tradeId': row[1], 'payloadHash': row[2], 'parentSource': row[3]}
                for row in connection.execute('''SELECT p.currency,p.trade_id,p.payload_hash,p.first_source
                    FROM parent_rows p LEFT JOIN leaf_payloads l
                    ON l.currency=p.currency AND l.trade_id=p.trade_id
                    AND l.payload_hash=p.payload_hash WHERE l.trade_id IS NULL LIMIT 20''')]
        report['inventoryRootSha256'] = digest(canonical(sorted(
            inventory, key=lambda x: (x['section'], x['sourceCache'], x['file']))))
        report['inventoryFilesVerified'] = len(inventory)
        report['requestCadence'] = {}
        for policy, sent in sent_by_policy.items():
            intervals = [b - a for a, b in zip(sorted(sent), sorted(sent)[1:])]
            report['requestCadence'][policy] = {
                'requests': len(sent),
                'minimumPcSendSeparationMs': min(intervals) if intervals else None,
                'below900msCount': sum(x < 900 for x in intervals)}
        covered, coverage_errors = coverage(manifest)
        report['coverageErrors'] = coverage_errors
        changed = digest(manifest_path.read_bytes()) != manifest_sha
        report['inputManifestChangedDuringAudit'] = changed
        running = report['inputCollectorRunning'] or changed or manifest.get('inFlight') is not None
        report['coverageComplete'] = bool(covered and not running)
        report['fullIdentityAuditComplete'] = bool(
            report['coverageComplete'] and report['sourceIntegrityErrorCount'] == 0
            and report['identityConflicts'] == 0 and report['disjointLeafDuplicateIds'] == 0
            and report['parentMissingInLeaves'] == 0)
        report['state'] = ('scope_partial' if running else
                           'coverage_incomplete' if not report['coverageComplete'] else
                           'identity_conflicts' if not report['fullIdentityAuditComplete'] else
                           'identity_complete_metadata_pending')
        report['limitation'] = ('Identity only: no currency/instrument metadata join, '
                                'feature audit, signal, pricing or PnL. HTTP response headers '
                                'were not preserved by v1/v2 collectors; PC cadence is descriptive.')
        return report
    finally:
        Path(db_name).unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path,
                        default=V2_MANIFEST if V2_MANIFEST.exists() else V1_MANIFEST)
    parser.add_argument('--cache-root', type=Path, default=CACHE_BASE)
    parser.add_argument('--report-dir', type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    report = audit(args.manifest, args.cache_root)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    target = args.report_dir / ('options-identity-audit-'
                                + report['inputManifestSha256'][:16] + '.json')
    raw = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False).encode('utf-8') + b'\n'
    if target.exists():
        if target.read_bytes() != raw:
            raise ValueError(f'Immutable audit report differs: {target}')
    else:
        with target.open('xb') as output:
            output.write(raw)
    print(json.dumps({'report': str(target), 'state': report['state'],
                      'coverageComplete': report['coverageComplete'],
                      'fullIdentityAuditComplete': report['fullIdentityAuditComplete'],
                      'fullDataAuditComplete': False}, indent=2))


if __name__ == '__main__':
    main()
