"""Synthetic N13 archive tests; no network, option signals or market results."""
import gzip
import importlib.util
import json
import tempfile
import unittest
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/download-goal-options-trades.py'
spec = importlib.util.spec_from_file_location('option_archive', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def response(task, *, more=False, duplicate=False, conflict=False):
    trade = {'timestamp': task['lo'], 'trade_id': '7', 'instrument_name': 'TEST-C',
             'iv': 30.0, 'index_price': 100.0}
    trades = [trade]
    if duplicate or conflict:
        other = dict(trade)
        if conflict:
            other['iv'] = 31.0
        trades.append(other)
    return json.dumps({'result': {'trades': trades, 'has_more': more}}).encode()


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = (mod.CACHE, mod.MANIFEST, mod.START, mod.END, mod.CACHE_CAP)
        root = Path(self.temp.name)
        mod.CACHE = root / 'cache'
        mod.MANIFEST = root / 'manifest.json'
        mod.START = datetime(2021, 10, 1, tzinfo=timezone.utc)
        mod.END = mod.START + timedelta(days=1)
        mod.CACHE_CAP = 2_000_000_000

    def tearDown(self):
        mod.CACHE, mod.MANIFEST, mod.START, mod.END, mod.CACHE_CAP = self.old
        self.temp.cleanup()

    def test_half_open_url_and_duplicate_audit(self):
        task = {'symbol': 'BTC', 'lo': 100, 'hi': 102}
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(mod.url_for(task)).query)
        self.assertEqual((query['start_timestamp'], query['end_timestamp']), (['100'], ['101']))
        self.assertEqual((query['count'], query['sorting'], query['include_old']),
                         (['1000'], ['asc'], ['true']))
        info = mod.inspect(response(task, duplicate=True), task)
        self.assertEqual((info['records'], info['uniqueTradeIds'], info['identicalDuplicates'],
                          info['duplicateConflicts']), (2, 1, 1, 0))
        self.assertEqual(mod.inspect(response(task, conflict=True), task)['duplicateConflicts'], 1)
        bad = json.dumps({'result': {'trades': [{'timestamp': 102, 'trade_id': '9'}],
                                     'has_more': False}}).encode()
        with self.assertRaisesRegex(ValueError, 'outside requested'):
            mod.inspect(bad, task)

    def test_split_persists_raw_receipt_and_one_ms_is_fatal(self):
        state = mod.initial_manifest()
        task = {'symbol': 'BTC', 'lo': 100, 'hi': 104}
        state['pending'] = [task]
        body = response(task, more=True)
        mod.commit_response(state, task, body, 200, 'send', 'receive')
        self.assertEqual(state['pending'], [{'symbol': 'BTC', 'lo': 100, 'hi': 102},
                                             {'symbol': 'BTC', 'lo': 102, 'hi': 104}])
        saved = mod.CACHE / mod.filename(task)
        self.assertEqual(gzip.decompress(saved.read_bytes()), body)
        self.assertEqual(state['splits'][0]['rawSha256'], mod.digest(body))
        fatal = {'symbol': 'BTC', 'lo': 200, 'hi': 201}
        state['pending'] = [fatal]
        mod.commit_response(state, fatal, response(fatal, more=True), 200, 'send', 'receive')
        self.assertEqual(state['fatalGaps'][0]['issue'], 'truncated_one_millisecond')
        self.assertFalse(state['complete'])

    def test_resume_without_refetch_or_raw_mutation_and_rate_limit(self):
        calls = []
        clock = [0.0]
        sleeps = []
        def client(url, remaining):
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            task = {'symbol': query['currency'][0], 'lo': int(query['start_timestamp'][0]),
                    'hi': int(query['end_timestamp'][0]) + 1}
            calls.append(task['symbol'])
            return response(task), 200, 'send', 'receive'
        def pause(seconds):
            sleeps.append(seconds)
            clock[0] += seconds
        first = mod.run(max_requests=1, client=client, sleep=pause,
                        monotonic=lambda: clock[0], wall=lambda: clock[0])
        saved = (mod.CACHE / mod.filename(mod.tasks()[0])).read_bytes()
        second = mod.run(max_requests=1, client=client, sleep=pause,
                         monotonic=lambda: clock[0], wall=lambda: clock[0])
        self.assertEqual(calls, ['BTC', 'ETH'])
        self.assertEqual((first['complete'], second['complete'], second['coverageComplete']),
                         (False, False, True))
        self.assertEqual((mod.CACHE / mod.filename(mod.tasks()[0])).read_bytes(), saved)
        self.assertGreaterEqual(sleeps[-1], 1.0)  # rate limit persists across rounds
        # A two-request round must wait at least one second between sends.
        mod.MANIFEST.unlink()
        mod.CACHE = Path(self.temp.name) / 'other-cache'
        mod.MANIFEST = Path(self.temp.name) / 'other-manifest.json'
        mod.run(max_requests=2, client=client, sleep=pause,
                monotonic=lambda: clock[0], wall=lambda: clock[0])
        self.assertGreaterEqual(sleeps[-1], 1.0)

    def test_limits_and_conflicting_duplicate_fail_closed(self):
        task = mod.tasks()[0]
        state = mod.initial_manifest()
        state['pending'] = [task]
        mod.commit_response(state, task, response(task, conflict=True), 200, 'send', 'receive')
        self.assertEqual(state['state'], 'fatal')
        self.assertFalse(state['complete'])
        mod.CACHE = Path(self.temp.name) / 'other-cache'
        mod.MANIFEST = Path(self.temp.name) / 'other-manifest.json'
        def oversized(url, remaining):
            return b'x' * (remaining + 1), 200, 'send', 'receive'
        outcome = mod.run(max_requests=1, max_raw_bytes=10, client=oversized)
        self.assertEqual(outcome['state'], 'round_raw_byte_limit')
        self.assertEqual(outcome['leafCount'], 0)
        self.assertEqual(outcome['getCountThisRound'], 1)
        partial = json.loads(mod.MANIFEST.read_text())['errors'][0]
        self.assertTrue(partial['partial'])
        self.assertEqual(gzip.decompress((mod.CACHE / partial['file']).read_bytes()), b'x' * 10)

    def test_http_403_preserves_body_and_blocks_resume(self):
        calls = []
        def forbidden(url, remaining):
            calls.append(url)
            return b'{"error":"forbidden"}', 403, 'send', 'receive'
        first = mod.run(max_requests=1, client=forbidden)
        record = json.loads(mod.MANIFEST.read_text())['errors'][0]
        self.assertEqual(first['state'], 'blocked_403')
        self.assertEqual(gzip.decompress((mod.CACHE / record['file']).read_bytes()),
                         b'{"error":"forbidden"}')
        self.assertEqual(mod.digest((mod.CACHE / record['file']).read_bytes()), record['gzipSha256'])
        second = mod.run(max_requests=1, client=forbidden)
        self.assertEqual(second['getCountThisRound'], 0)
        self.assertEqual(len(calls), 1)

    def test_invalid_schema_response_is_preserved_before_rejection(self):
        task = mod.tasks()[0]
        state = mod.initial_manifest()
        state['pending'] = [task]
        body = b'{"result":{"trades":[null],"has_more":false}}'
        mod.commit_response(state, task, body, 200, 'send', 'receive')
        record = state['rejected'][0]
        self.assertEqual(gzip.decompress((mod.CACHE / record['file']).read_bytes()), body)
        self.assertEqual(record['rawSha256'], mod.digest(body))
        self.assertEqual(state['state'], 'fatal')
        self.assertFalse(state['coverageComplete'])
        self.assertFalse(state['complete'])


if __name__ == '__main__':
    unittest.main()
