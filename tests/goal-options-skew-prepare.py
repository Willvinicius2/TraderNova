"""Synthetic-only N13 preparation gates; no real option trades are read."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/prepare-goal-options-skew.py'
spec = importlib.util.spec_from_file_location('skew_prepare', SCRIPT)
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
fixture_spec = importlib.util.spec_from_file_location(
    'identity_fixture', ROOT / 'tests/goal-options-identity-audit.py')
F = importlib.util.module_from_spec(fixture_spec)
fixture_spec.loader.exec_module(F)
DAY = F.START
MID = F.MID
END = F.END


def write_json(path, value):
    path.write_text(json.dumps(value) + '\n', encoding='utf-8')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def option_trade(identity, stamp, side):
    name = f'BTC-30DEC21-{90 if side == "put" else 110}-{side[0].upper()}'
    return {'trade_id': identity, 'timestamp': stamp, 'instrument_name': name,
            'iv': 0.6 if side == 'put' else 0.4, 'index_price': 100}


def descriptor(side, *, created=DAY - 1, expiry=END + 14 * 86_400_000):
    name = f'BTC-30DEC21-{90 if side == "put" else 110}-{side[0].upper()}'
    return {'instrument_name': name, 'kind': 'option', 'base_currency': 'BTC',
            'quote_currency': 'BTC', 'settlement_currency': 'BTC',
            'price_index': 'btc_usd', 'strike': str(90 if side == 'put' else 110),
            'option_type': side, 'creation_timestamp': created,
            'expiration_timestamp': expiry, 'contract_size': '1'}


def setup(root):
    cache = root / 'options-trades'
    puts = [option_trade(f'P{i}', DAY + 1000 + i, 'put') for i in range(5)]
    calls = [option_trade(f'C{i}', MID + 1000 + i, 'call') for i in range(5)]
    left = F.make_record(cache, 'v2', DAY, MID, [puts[0], puts[0]] + puts[1:], False)
    right = F.make_record(cache, 'v2', MID, END, calls, False)
    eth = F.make_record(cache, 'v2', DAY, END, [], False)
    eth['symbol'] = 'ETH'
    eth['url'] = eth['url'].replace('currency=BTC', 'currency=ETH')
    eth_receipt = cache.with_name(cache.name + '-v2') / eth['receiptFile']
    receipt_data = json.loads(eth_receipt.read_text())
    receipt_data['symbol'], receipt_data['url'] = eth['symbol'], eth['url']
    write_json(eth_receipt, receipt_data)
    trades = {'id': 'N13-deribit-option-trades-data-v2', 'source': P.IDENTITY.SOURCE,
              'scope': {'symbols': ['BTC', 'ETH'], 'kind': 'option',
                        'startInclusive': '2021-10-01T00:00:00+00:00',
                        'endExclusive': '2025-01-01T00:00:00+00:00'},
              'runningPid': None, 'inFlight': None, 'coverageComplete': True,
              'leaves': [left, right, eth], 'splits': []}
    trades_path = root / 'trades.json'
    trades_sha = write_json(trades_path, trades)
    identity_path = root / 'identity.json'
    write_json(identity_path, {'id': 'N13-option-trade-identity-audit-v1',
                               'inputManifestSha256': trades_sha,
                               'coverageComplete': True, 'fullIdentityAuditComplete': True,
                               'inputCollectorRunning': False,
                               'inputManifestChangedDuringAudit': False,
                               'sourceIntegrityErrorCount': 0, 'identityConflicts': 0,
                               'parentMissingInLeaves': 0,
                               'disjointLeafDuplicateIds': 0})
    responses = []
    for symbol in ('BTC', 'ETH'):
        rows = [descriptor('put', created=DAY + 1000),
                descriptor('call', created=MID + 1000)] if symbol == 'BTC' else []
        raw_rows = []
        for row in rows:
            original = dict(row)
            original['strike'] = int(original['strike'])
            original['contract_size'] = int(original['contract_size'])
            raw_rows.append(original)
        body = json.dumps({'result': raw_rows}).encode()
        packed = gzip.compress(body, mtime=0)
        raw_path = root / f'{symbol}.json.gz'
        norm_path = root / f'{symbol}.normalized.json'
        raw_path.write_bytes(packed)
        write_json(norm_path, rows)
        responses.append({'symbol': symbol, 'httpStatus': 200,
                          'rawGzipPath': str(raw_path.relative_to(ROOT)) if raw_path.is_relative_to(ROOT) else str(raw_path),
                          'normalizedPath': str(norm_path.relative_to(ROOT)) if norm_path.is_relative_to(ROOT) else str(norm_path),
                          'gzipSha256': P.sha(packed), 'rawSha256': P.sha(body),
                          'normalizedSha256': P.file_sha(norm_path), 'normalizedRows': len(rows)})
    catalog = {'id': 'N13-deribit-option-instruments-v1',
               'normalization': {'allRecordsPreserved': True,
                                 'duplicateNamesDropped': False}, 'responses': responses}
    catalog_path = root / 'catalog.json'
    write_json(catalog_path, catalog)
    grouped = {('BTC', DAY): [left, right], ('ETH', DAY): [eth]}
    return trades_path, identity_path, catalog_path, cache, grouped


class PrepareTests(unittest.TestCase):
    def test_metadata_audit_and_causal_boundary(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'research/cache/goal-seven') as temporary:
            root = Path(temporary)
            trades, identity, catalog, cache, grouped = setup(root)
            with mock.patch.object(P, 'leaves_by_day', return_value=(DAY, END, grouped)):
                path, report = P.metadata_audit(trades, identity, catalog, cache, root)
            self.assertTrue(report['fullMetadataAuditComplete'])
            self.assertEqual(report['tradeOccurrencesInLeaves'], 11)
            self.assertEqual(report['matchedInstrumentNames'], 2)
            self.assertEqual(path.read_bytes(), path.read_bytes())
            # Expiry at the trade timestamp is excluded; creation at timestamp is allowed.
            data = json.loads(catalog.read_text())
            btc_record = data['responses'][0]
            btc_norm = Path(btc_record['normalizedPath'])
            btc_raw = Path(btc_record['rawGzipPath'])
            rows = json.loads(btc_norm.read_text())
            rows[0]['expiration_timestamp'] = DAY + 1000
            write_json(btc_norm, rows)
            raw = json.loads(gzip.decompress(btc_raw.read_bytes()))
            raw['result'][0]['expiration_timestamp'] = DAY + 1000
            body = json.dumps(raw).encode()
            packed = gzip.compress(body, mtime=0)
            btc_raw.write_bytes(packed)
            btc_record['gzipSha256'] = P.sha(packed)
            btc_record['rawSha256'] = P.sha(body)
            btc_record['normalizedSha256'] = P.file_sha(btc_norm)
            write_json(catalog, data)
            with mock.patch.object(P, 'leaves_by_day', return_value=(DAY, END, grouped)):
                _, bad = P.metadata_audit(trades, identity, catalog, cache, root)
            self.assertEqual(bad['invalidInstrumentNames'], 1)
            self.assertFalse(bad['fullMetadataAuditComplete'])

    def test_incomplete_identity_and_catalog_tamper_block(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'research/cache/goal-seven') as temporary:
            root = Path(temporary)
            trades, identity, catalog, cache, grouped = setup(root)
            report = json.loads(identity.read_text())
            report['fullIdentityAuditComplete'] = False
            write_json(identity, report)
            with self.assertRaisesRegex(ValueError, 'full identity'):
                P.metadata_audit(trades, identity, catalog, cache, root)
            report['fullIdentityAuditComplete'] = True
            write_json(identity, report)
            item = json.loads(catalog.read_text())['responses'][0]
            Path(item['normalizedPath']).write_bytes(b'changed')
            with mock.patch.object(P, 'leaves_by_day', return_value=(DAY, END, grouped)):
                with self.assertRaisesRegex(ValueError, 'hash'):
                    P.metadata_audit(trades, identity, catalog, cache, root)

    def test_frozen_split_day_duplicate_and_no_pre_freeze_iv_read(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'research/cache/goal-seven') as temporary:
            root = Path(temporary)
            trades, identity, catalog, cache, grouped = setup(root)
            with mock.patch.object(P, 'leaves_by_day', return_value=(DAY, END, grouped)):
                metadata_path, metadata = P.metadata_audit(trades, identity, catalog, cache, root)
            self.assertTrue(metadata['fullMetadataAuditComplete'])
            files = {'prepareScript': SCRIPT, 'prepareTests': Path(__file__),
                     'signalGenerator': ROOT / 'scripts/goal_options_skew_signals.py',
                     'protocol': P.PROTOCOL, 'tradeManifest': trades,
                     'identityAudit': identity, 'instrumentManifest': catalog,
                     'metadataAudit': metadata_path}
            freeze_path = root / 'freeze.json'
            freeze = {'id': 'N13-option-skew-preparation-freeze-v1',
                      'historicalAssumption': True,
                      'sha256': {key: P.file_sha(path) for key, path in files.items()},
                      'hashes': {'research/goal-seven/options-skew-protocol.json':
                                 P.file_sha(P.PROTOCOL)},
                      'auditPaths': {'identityAudit': identity.relative_to(root).as_posix(),
                                     'metadataAudit': metadata_path.relative_to(root).as_posix()}}
            freeze['auditPaths'] = {key: (root / value).relative_to(ROOT).as_posix()
                                    for key, value in freeze['auditPaths'].items()}
            write_json(freeze_path, freeze)
            with mock.patch.object(P, 'page', side_effect=AssertionError('IV read before freeze')):
                bad = dict(freeze)
                bad['sha256'] = dict(freeze['sha256'], protocol='0' * 64)
                write_json(freeze_path, bad)
                with self.assertRaisesRegex(ValueError, 'Freeze hash mismatch'):
                    P.aggregate(trades, identity, catalog, metadata_path, freeze_path,
                                cache, root / 'daily.json', root / 'daily-manifest.json')
                bad = dict(freeze)
                bad['hashes'] = dict(freeze['hashes'],
                                     **{'research/goal-seven/options-skew-protocol.json': '0' * 64})
                write_json(freeze_path, bad)
                with self.assertRaisesRegex(ValueError, 'Freeze path hash mismatch'):
                    P.aggregate(trades, identity, catalog, metadata_path, freeze_path,
                                cache, root / 'daily.json', root / 'daily-manifest.json')
            write_json(freeze_path, freeze)
            # Test the aggregate against its own synthetic paths, without weakening production gates.
            with mock.patch.object(P, 'leaves_by_day', return_value=(DAY, END, grouped)):
                manifest_path, output = P.aggregate(trades, identity, catalog, metadata_path,
                    freeze_path, cache, root / 'daily.json', root / 'daily-manifest.json')
            self.assertFalse(output['validated'])
            self.assertFalse(output['signalsComputed'])
            self.assertEqual(output['series']['BTCUSDT']['rows'], 1)
            rows = json.loads((ROOT / output['series']['BTCUSDT']['cachePath']).read_text())
            self.assertEqual(rows[0]['put_count'], 5)  # Duplicate counts once.
            self.assertEqual(rows[0]['call_count'], 5)
            self.assertEqual(rows[0]['skew'], '0.2')
            self.assertTrue(manifest_path.exists())


if __name__ == '__main__':
    unittest.main()
