"""Synthetic-only checks for N13 historical option-trade collector v2."""
import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch
import urllib.parse
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/download-goal-options-trades-v2.py'
spec = importlib.util.spec_from_file_location('options_v2', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class CollectorV2Tests(unittest.TestCase):
    def test_windows_transient_replace_retries_and_preserves_old_file(self):
        destination = Path(self.tmp.name) / 'atomic.json'
        destination.write_text('{"old":true}', encoding='utf-8')
        original = mod.os.replace
        attempts = []
        def replace(source, target):
            attempts.append(1)
            if len(attempts) < 3:
                self.assertEqual(json.loads(destination.read_text()), {'old': True})
                raise PermissionError('sharing violation fixture')
            original(source, target)
        with patch.object(mod.os, 'replace', side_effect=replace), patch.object(mod.time, 'sleep') as wait:
            mod.atomic_json(destination, {'new': True})
        self.assertEqual(json.loads(destination.read_text()), {'new': True})
        self.assertEqual(wait.call_count, 2)
        with patch.object(mod.os, 'replace', side_effect=PermissionError('permanent')), patch.object(mod.time, 'sleep') as wait:
            with self.assertRaises(PermissionError):
                mod.atomic_json(destination, {'uncommitted': True})
        self.assertEqual(wait.call_count, 6)
        self.assertEqual(json.loads(destination.read_text()), {'new': True})

    def test_unexpected_failure_has_durable_state_and_keeps_uncertain_request(self):
        def crash(*args):
            raise KeyError('unexpected fixture')
        with self.assertRaises(KeyError):
            mod.run(max_requests=1, client=crash)
        state = json.loads(mod.MANIFEST.read_text())
        self.assertEqual(state['state'], 'stopped_exception')
        self.assertIsNone(state['runningPid'])
        self.assertIsNotNone(state['inFlight'])
        self.assertIn('KeyError', state['lastError']['message'])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = mod.CACHE, mod.MANIFEST
        mod.CACHE = Path(self.tmp.name) / 'new-cache'
        mod.MANIFEST = Path(self.tmp.name) / 'v2-manifest.json'

    def tearDown(self):
        mod.CACHE, mod.MANIFEST = self.old
        self.tmp.cleanup()

    def test_migration_reuses_verified_v1_bytes_and_retains_history(self):
        before = mod.digest(mod.V1_MANIFEST.read_bytes())
        state = mod.initial_manifest()
        self.assertEqual((len(state['leaves']), len(state['splits']), len(state['pending'])),
                         (4, 6, 2378))
        self.assertEqual(state['httpGetCount'], 10)
        self.assertTrue(all(x['sourceCache'] == 'v1' for x in state['leaves'] + state['splits']))
        self.assertTrue(all('count=1000' in x['url'] for x in state['leaves'] + state['splits']))
        self.assertEqual(mod.digest(mod.V1_MANIFEST.read_bytes()), before)
        mod.check_manifest(state)

    def test_count_10000_and_unsorted_complete_page(self):
        task = {'symbol': 'BTC', 'lo': 100, 'hi': 104}
        url = mod.url_for(task)
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        self.assertEqual(query['count'], ['10000'])
        self.assertEqual(query['end_timestamp'], ['103'])
        trades = [{'timestamp': x, 'trade_id': str(i), 'instrument_name': 'BTC-1JAN30-100-C'}
                  for i, x in enumerate((103, 100, 102))]
        info = mod.inspect(json.dumps({'result': {'trades': trades, 'has_more': False}}).encode(), task)
        self.assertEqual((info['firstTimestampMs'], info['lastTimestampMs'],
                          info['minTimestampMs'], info['maxTimestampMs']), (103, 102, 100, 103))
        self.assertFalse(info['timestampsNondecreasingInSourceOrder'])
        wrong = [{'timestamp': 100, 'trade_id': 'id', 'instrument_name': 'ETH-1JAN30-100-C'}]
        with self.assertRaisesRegex(ValueError, 'scope'):
            mod.inspect(json.dumps({'result': {'trades': wrong, 'has_more': False}}).encode(), task)

    def test_lock_and_stop_marker_prevent_requests(self):
        with mod.exclusive_lock():
            with self.assertRaisesRegex(RuntimeError, 'already running'):
                mod.run(max_requests=1, client=lambda *_: self.fail('GET under lock'))
        mod.CACHE.mkdir(parents=True, exist_ok=True)
        (mod.CACHE / 'STOP').write_text('operator stop\n', encoding='utf-8')
        outcome = mod.run(max_requests=1, client=lambda *_: self.fail('GET after STOP'))
        self.assertEqual((outcome['state'], outcome['getCountThisRound']), ('stopped_marker', 0))
        saved = json.loads(mod.MANIFEST.read_text(encoding='utf-8'))
        self.assertEqual(saved['runSerial'], 1)
        self.assertIsNone(saved['runningPid'])
        self.assertIsNotNone(saved['lastRunEndedAtUtc'])

    def test_split_and_new_receipt_are_separate_from_v1(self):
        state = mod.initial_manifest()
        task = state['pending'][0]
        trade = {'timestamp': task['lo'], 'trade_id': 'test',
                 'instrument_name': task['symbol'] + '-1JAN30-100-C'}
        body = json.dumps({'result': {'trades': [trade], 'has_more': True}}).encode()
        mod.commit_response(state, task, body, 200, 'sent', 'received')
        self.assertEqual(len(state['splits']), 7)
        record = state['splits'][-1]
        self.assertIn('-c10000.json.gz', record['file'])
        self.assertIn('count=10000', record['url'])
        self.assertNotEqual(record['file'], state['splits'][0]['file'])
        self.assertEqual(state['pending'][0]['lo'], task['lo'])
        self.assertEqual(state['pending'][1]['hi'], task['hi'])
        mod.check_manifest(state)
        self.assertFalse(state['complete'])
        self.assertFalse(state['crossPageIdentityAuditComplete'])

    def test_http_403_is_preserved_and_resume_is_blocked(self):
        calls = []
        def forbidden(url, remaining):
            calls.append(url)
            return b'{"error":"forbidden"}', 403, 'sent', 'received'
        first = mod.run(max_requests=1, client=forbidden)
        second = mod.run(max_requests=1, client=forbidden)
        self.assertEqual((first['state'], second['state']), ('blocked_403', 'blocked_403'))
        self.assertEqual(len(calls), 1)
        state = json.loads(mod.MANIFEST.read_text(encoding='utf-8'))
        self.assertEqual(len(state['errors']), 1)
        mod.check_manifest(state)

    def test_large_round_budget_does_not_block_small_response(self):
        def small_page(url, limit):
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            stamp = int(query['start_timestamp'][0])
            symbol = query['currency'][0]
            trade = {'timestamp': stamp, 'trade_id': 'synthetic',
                     'instrument_name': symbol + '-1JAN30-100-C'}
            return json.dumps({'result': {'trades': [trade], 'has_more': False}}).encode(), 200, 's', 'r'
        old_cap = mod.CACHE_CAP
        try:
            mod.CACHE_CAP = 5_000_000_000
            result = mod.run(max_requests=1, max_raw_bytes=20_000_000_000,
                             client=small_page)
            self.assertEqual(result['getCountThisRound'], 1)
            self.assertEqual(result['leafCount'], 5)
        finally:
            mod.CACHE_CAP = old_cap

    def test_near_cache_cap_saves_partial_then_stops_without_overflow(self):
        state = mod.initial_manifest()
        mod.atomic_json(mod.MANIFEST, state)
        old_cap = mod.CACHE_CAP
        try:
            mod.CACHE_CAP = state['cacheBytes'] + mod.RESERVE_BYTES + 100
            calls = []
            def oversized(url, limit):
                calls.append(limit)
                return b'x' * (limit + 5), 200, 's', 'r'
            result = mod.run(max_requests=2, max_raw_bytes=20_000_000_000,
                             client=oversized)
            self.assertEqual(calls, [100])
            self.assertEqual(result['state'], 'total_cache_cap')
            saved = json.loads(mod.MANIFEST.read_text(encoding='utf-8'))
            self.assertEqual(saved['state'], result['state'])
            self.assertTrue(saved['errors'][0]['partial'])
            self.assertEqual(saved['errors'][0]['rawBytes'], 100)
            self.assertLessEqual(saved['cacheBytes'], mod.CACHE_CAP)
            mod.check_manifest(saved)
        finally:
            mod.CACHE_CAP = old_cap

    def test_regressed_clock_fails_without_long_sleep_or_get(self):
        state = mod.initial_manifest()
        state['lastGetSentEpoch'] = 86400.0
        mod.atomic_json(mod.MANIFEST, state)
        result = mod.run(max_requests=1, client=lambda *_: self.fail('GET with bad clock'),
                         sleep=lambda _: self.fail('Unbounded sleep'), wall=lambda: 0.0)
        self.assertEqual(result['state'], 'clock_regression')
        self.assertEqual(result['getCountThisRound'], 0)
        self.assertEqual(json.loads(mod.MANIFEST.read_text())['state'], 'clock_regression')

    def test_rate_wait_is_bounded_by_round_deadline(self):
        state = mod.initial_manifest()
        state['lastGetSentEpoch'] = 0.0
        mod.atomic_json(mod.MANIFEST, state)
        clock = [0.0]
        waits = []
        def pause(seconds):
            waits.append(seconds)
            clock[0] += seconds
        result = mod.run(max_requests=1, max_duration=1,
                         client=lambda *_: self.fail('GET after deadline'),
                         sleep=pause, wall=lambda: 0.0, monotonic=lambda: clock[0])
        self.assertEqual(result['state'], 'round_duration_limit')
        self.assertEqual(waits, [1.0])
        self.assertEqual(json.loads(mod.MANIFEST.read_text())['state'], 'round_duration_limit')

    def test_round_raw_limit_and_total_cache_cap_states_are_durable(self):
        state = mod.initial_manifest()
        mod.atomic_json(mod.MANIFEST, state)
        old_cap = mod.CACHE_CAP
        try:
            mod.CACHE_CAP = state['cacheBytes'] + mod.RESERVE_BYTES
            result = mod.run(max_requests=1, client=lambda *_: self.fail('GET at cache cap'))
            self.assertEqual(result['state'], 'total_cache_cap')
            self.assertEqual(json.loads(mod.MANIFEST.read_text())['state'], 'total_cache_cap')
        finally:
            mod.CACHE_CAP = old_cap
        mod.MANIFEST.unlink()
        mod.CACHE = Path(self.tmp.name) / 'second-cache'
        sample = mod.initial_manifest()['pending'][0]
        trade = {'timestamp': sample['lo'], 'trade_id': 'synthetic',
                 'instrument_name': sample['symbol'] + '-1JAN30-100-C'}
        body = json.dumps({'result': {'trades': [trade], 'has_more': False}}).encode()
        result = mod.run(max_requests=2, max_raw_bytes=len(body),
                         client=lambda url, limit: (body, 200, 's', 'r', False))
        self.assertEqual(result['state'], 'round_raw_byte_limit')
        self.assertEqual(json.loads(mod.MANIFEST.read_text())['state'], 'round_raw_byte_limit')


if __name__ == '__main__':
    unittest.main()
