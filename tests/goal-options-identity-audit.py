"""Synthetic N13 identity audit fixtures; never reads the real options corpus."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest import mock
from urllib.parse import urlencode


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/audit-goal-options-trades.py'
SPEC = importlib.util.spec_from_file_location('option_identity_audit', SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)

START = 1633046400000  # 2021-10-01 00:00 UTC
MID = START + 43_200_000
END = START + 86_400_000


def trade(trade_id, stamp, instrument='BTC-30DEC21-60000-C'):
    return {'trade_id': trade_id, 'timestamp': stamp, 'instrument_name': instrument,
            'price': 0.01}  # Hashed as raw identity, never indexed as a price.


def make_record(cache_root, policy, lo, hi, trades, has_more):
    count = 1000 if policy == 'v1' else 10000
    name = f'BTC-{lo}-{hi}-c{count}.json.gz'
    directory = cache_root if policy == 'v1' else cache_root.with_name(cache_root.name + '-v2')
    directory.mkdir(parents=True, exist_ok=True)
    url = AUDIT.SOURCE + '?' + urlencode({
        'currency': 'BTC', 'kind': 'option', 'start_timestamp': lo,
        'end_timestamp': hi - 1, 'count': count, 'sorting': 'asc', 'include_old': 'true'})
    body = json.dumps({'jsonrpc': '2.0', 'result': {'trades': trades, 'has_more': has_more}},
                      separators=(',', ':')).encode()
    packed = gzip.compress(body, mtime=0)
    receipt = {'symbol': 'BTC', 'lo': lo, 'hi': hi, 'file': name,
               'receiptFile': name.replace('.json.gz', '.receipt.json'), 'url': url,
               'sentAtUtc': '2026-09-29T00:00:00Z',
               'receivedAtUtc': '2026-09-29T00:00:01Z', 'httpStatus': 200,
               'rawBytes': len(body), 'rawSha256': hashlib.sha256(body).hexdigest(),
               'gzipBytes': len(packed), 'gzipSha256': hashlib.sha256(packed).hexdigest(),
               'partial': False}
    (directory / name).write_bytes(packed)
    (directory / receipt['receiptFile']).write_text(json.dumps(receipt) + '\n', encoding='utf-8')
    return {**receipt, 'records': len(trades), 'hasMore': has_more,
            'sourceCache': policy, 'sourcePolicy': policy + '-count' + str(count)}


def fixture(root, version='v2', leaf_b=None, parent=None, left_extra=None):
    cache = root / 'options-trades'
    a = trade('A', START + 1000)
    b = leaf_b or trade('B', MID + 1000)
    parent_trades = parent if parent is not None else [a, b]
    leaf_policy = 'v1' if version == 'v1' else 'v2'
    left = make_record(cache, leaf_policy, START, MID, [a] + (left_extra or []), False)
    right = make_record(cache, leaf_policy, MID, END, [b], False)
    split = make_record(cache, 'v1', START, END, parent_trades, True)
    manifest = {'id': 'N13-deribit-option-trades-data-' + version,
                'source': AUDIT.SOURCE,
                'scope': {'symbols': ['BTC'], 'startInclusive': '2021-10-01T00:00:00+00:00',
                          'endExclusive': '2021-10-02T00:00:00+00:00', 'kind': 'option'},
                'pending': [], 'leaves': [left, right], 'splits': [split],
                'fatalGaps': [], 'inFlight': None, 'coverageComplete': True,
                'state': 'coverage_complete_audit_pending', 'runningPid': None}
    path = root / 'manifest.json'
    path.write_text(json.dumps(manifest) + '\n', encoding='utf-8')
    return path, cache, manifest


class IdentityTests(unittest.TestCase):
    def test_parent_leaf_identity_and_v1_v2_receipts(self):
        for version in ('v1', 'v2'):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as temporary:
                path, cache, _ = fixture(Path(temporary), version)
                report = AUDIT.audit(path, cache)
                self.assertEqual(report['state'], 'identity_complete_metadata_pending')
                self.assertTrue(report['coverageComplete'])
                self.assertTrue(report['fullIdentityAuditComplete'])
                self.assertFalse(report['fullDataAuditComplete'])
                self.assertFalse(report['dataApproved'])
                self.assertEqual(report['rawPagesAudited'], 3)
                self.assertEqual(report['uniqueLeafTradeIds'], 2)
                self.assertEqual(report['parentMissingInLeaves'], 0)
                self.assertEqual(report['identityConflicts'], 0)
                self.assertEqual(report['inputInventoryClaims'], 3)
                self.assertEqual(report['inventoryFilesVerified'], 3)
                self.assertFalse(list(cache.glob('identity-audit-*.sqlite')))

    def test_parent_missing_and_conflicting_payload_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            a = trade('A', START + 1000)
            unmatched = trade('X', MID + 1000)
            path, cache, _ = fixture(root, parent=[a, unmatched])
            report = AUDIT.audit(path, cache)
            self.assertEqual(report['parentMissingInLeaves'], 1)
            self.assertEqual(report['identityConflicts'], 0)
            self.assertFalse(report['fullIdentityAuditComplete'])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            a = trade('A', START + 2000)  # Same currency/id, different timestamp and hash.
            b = trade('B', MID + 1000)
            path, cache, _ = fixture(root, parent=[a, b])
            report = AUDIT.audit(path, cache)
            self.assertEqual(report['identityConflicts'], 1)
            self.assertEqual(report['timestampConflicts'], 1)
            self.assertEqual(report['parentMissingInLeaves'], 1)
            self.assertFalse(report['fullIdentityAuditComplete'])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            variant = trade('A', START + 2000)
            path, cache, _ = fixture(root, parent=[variant, trade('B', MID + 1000)],
                                     left_extra=[variant])
            report = AUDIT.audit(path, cache)
            self.assertEqual(report['identityConflicts'], 1)
            self.assertEqual(report['uniqueLeafTradeIds'], 2)
            self.assertEqual(report['parentMissingInLeaves'], 0)

    def test_disjoint_leaf_duplicate_and_partial_scope(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path, cache, manifest = fixture(root, leaf_b=trade('A', MID + 1000))
            report = AUDIT.audit(path, cache)
            self.assertEqual(report['disjointLeafDuplicateIds'], 1)
            self.assertEqual(report['identityConflicts'], 1)
            self.assertFalse(report['fullIdentityAuditComplete'])
            manifest['runningPid'] = 1234
            path.write_text(json.dumps(manifest) + '\n', encoding='utf-8')
            partial = AUDIT.audit(path, cache)
            self.assertEqual(partial['state'], 'scope_partial')
            self.assertFalse(partial['coverageComplete'])
            self.assertFalse(partial['fullIdentityAuditComplete'])

    def test_disjoint_pair_hidden_by_first_broad_leaf(self):
        with sqlite3.connect(':memory:') as connection:
            AUDIT.init_db(connection)
            counters = {'leafOccurrences': 0, 'parentOccurrences': 0,
                        'identicalLeafDuplicates': 0}
            for name, lo, hi, stamp in (
                    ('broad', START, END, MID + 1000),
                    ('left', START, MID, START + 1000),
                    ('right', MID, END, MID + 1000)):
                record = {'symbol': 'BTC', 'lo': lo, 'hi': hi,
                          '_section': 'leaves', '_policy': 'v2', 'file': name}
                AUDIT.index_trade(connection, record, trade('A', stamp), counters)
            count = connection.execute('SELECT COUNT(*) FROM disjoint_leaf_duplicates').fetchone()[0]
            self.assertEqual(count, 1)

    def test_gzip_tamper_and_changed_manifest_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path, cache, manifest = fixture(root)
            record = manifest['leaves'][0]
            raw_path = cache.with_name(cache.name + '-v2') / record['file']
            raw_path.write_bytes(raw_path.read_bytes() + b'changed')
            bad = AUDIT.audit(path, cache)
            self.assertEqual(bad['sourceIntegrityErrorCount'], 1)
            self.assertFalse(bad['fullIdentityAuditComplete'])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path, cache, manifest = fixture(root)
            record = manifest['leaves'][0]
            directory = cache.with_name(cache.name + '-v2')
            raw_path = directory / record['file']
            modified = gzip.decompress(raw_path.read_bytes()).replace(b'"price":0.01', b'"price":0.02')
            packed = gzip.compress(modified, mtime=0)
            raw_path.write_bytes(packed)
            record['gzipBytes'] = len(packed)
            record['gzipSha256'] = hashlib.sha256(packed).hexdigest()
            receipt_path = directory / record['receiptFile']
            receipt = json.loads(receipt_path.read_text())
            receipt['gzipBytes'] = record['gzipBytes']
            receipt['gzipSha256'] = record['gzipSha256']
            receipt_path.write_text(json.dumps(receipt) + '\n', encoding='utf-8')
            path.write_text(json.dumps(manifest) + '\n', encoding='utf-8')
            bad_raw = AUDIT.audit(path, cache)
            self.assertEqual(bad_raw['sourceIntegrityErrorCount'], 1)
            self.assertIn('decompressed raw', bad_raw['sourceIntegrityErrorSamples'][0]['error'])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path, cache, _ = fixture(root)
            original = Path.read_bytes
            calls = {'manifest': 0}
            def changed(self):
                data = original(self)
                if self == path:
                    calls['manifest'] += 1
                    if calls['manifest'] > 1:
                        return data + b' '
                return data
            with mock.patch.object(Path, 'read_bytes', changed):
                report = AUDIT.audit(path, cache)
            self.assertTrue(report['inputManifestChangedDuringAudit'])
            self.assertEqual(report['state'], 'scope_partial')
            self.assertFalse(report['fullIdentityAuditComplete'])


if __name__ == '__main__':
    unittest.main()
