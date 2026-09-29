"""Synthetic causality, source, sample and immutable-trial tests for N14."""
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('miner', ROOT / 'scripts/run-goal-miner-pressure.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MinerTests(unittest.TestCase):
    def rows(self):
        return [{'time': i*m.DAY, 'hashrate': '100' if i<23 else '80',
                 'received_at': (i+1)*m.DAY} for i in range(30)]

    def test_rule_timing_strictness_and_missing_receipts(self):
        rows = self.rows()
        signals = m.generate(rows)
        self.assertEqual(len(signals), 1)
        decision, signal = next(iter(signals.items()))
        self.assertEqual(decision, 32*m.DAY)
        self.assertEqual(signal['signal_close_time'], 32*m.DAY+m.HOUR)
        self.assertEqual(signal['feature_end'], 30*m.DAY)
        self.assertEqual(signal['direction'], -1)
        self.assertFalse(m.generate([{**r, 'hashrate': '100'} for r in rows]))
        self.assertFalse(m.generate([{k: v for k,v in r.items() if k!='received_at'} for r in rows]))
        late = [{**r} for r in rows]
        late[0]['received_at'] = 3*m.DAY+1
        self.assertFalse(m.generate(late))

    def test_future_values_do_not_change_earlier_decision(self):
        rows = self.rows()
        before = m.generate(rows)
        future = rows + [{'time': 30*m.DAY, 'hashrate': '100000000', 'received_at': 31*m.DAY}]
        after = m.generate(future)
        self.assertEqual({t:r for t,r in after.items() if t in before}, before)
        self.assertFalse(m.generate(rows[:10]+rows[11:]))
        with self.assertRaises(ValueError):
            m.generate(rows+[rows[0]])

    def test_complete_source_and_decimal_values(self):
        data = {'data': [{'asset': 'btc', 'time': datetime.fromtimestamp(t, timezone.utc).isoformat(),
                          'HashRate': '123.456'} for t in range(m.SOURCE_START,m.END,m.DAY)]}
        output = m.normalize(data)
        self.assertEqual(len(output), (m.END-m.SOURCE_START)//m.DAY)
        self.assertEqual(output[0]['hashrate'], '123.456')
        with self.assertRaises(ValueError):
            m.normalize({**data, 'next_page_url': 'unfetched'})
        with self.assertRaises(ValueError):
            m.normalize({'data': data['data'][:-1]})
        with self.assertRaises(ValueError):
            m.normalize({'data': data['data']+[data['data'][0]]})

    def test_sample_gate_blocks_simulator(self):
        with patch.object(m, 'inputs', return_value=([], {}, {}, {}, {})), \
                patch.object(m, 'hashes', return_value={}), \
                patch.object(m.io, 'sha', return_value='frozen'), \
                patch.object(m.io, 'read', side_effect=[{'hashes': {}, 'marketAudit': {}}, {}]), \
                patch.object(m, 'simulate') as simulate:
            with self.assertRaisesRegex(ValueError, 'sample'):
                m.run('development')
            simulate.assert_not_called()

    def test_immutable_results(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'result.json'
            m.write_new(p, {'failed': True})
            with self.assertRaises(FileExistsError):
                m.write_new(p, {'passed': True})


if __name__ == '__main__':
    unittest.main()
