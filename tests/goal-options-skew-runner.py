"""Synthetic orchestration checks; never evaluates the real N13 corpus."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('runner', ROOT / 'scripts/run-goal-options-skew.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class RunnerTests(unittest.TestCase):
    def test_incomplete_corpus_blocks_freeze_before_prices(self):
        with patch.object(m.io, 'read', return_value={'coverageComplete': False}), \
                patch.object(m, 'load_data') as load:
            with self.assertRaisesRegex(ValueError, 'idle'):
                m.source_gate(Path('identity'), Path('metadata'))
            load.assert_not_called()

    def test_different_metadata_snapshot_blocks(self):
        rows = [{'coverageComplete': True}, {'fullIdentityAuditComplete': True, 'inputManifestSha256': 'same'},
                {'fullMetadataAuditComplete': True, 'tradeManifestSha256': 'different'}]
        with patch.object(m.io, 'read', side_effect=rows), patch.object(m.io, 'sha', return_value='same'):
            with self.assertRaisesRegex(ValueError, 'metadata'):
                m.source_gate(Path('identity'), Path('metadata'))

    def test_insufficient_sample_blocks_pnl(self):
        with patch.object(m, 'verify_freeze', return_value={}), patch.object(m, 'load_series', return_value={}), \
                patch.object(m, 'generate_signals', return_value={'N13': {}}), \
                patch.object(m, 'counted', return_value={'sampleUpperBoundReached': False}), \
                patch.object(m.io, 'read', return_value={'sampleUpperBoundReached': False}), \
                patch.object(m, 'simulate') as simulate:
            with self.assertRaisesRegex(ValueError, '100 triggers'):
                m.run_phase('development')
            simulate.assert_not_called()

    def test_existing_result_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            result = Path(folder) / 'result.json'
            result.write_text('original')
            with patch.object(m, 'RESULT', result), patch.object(m, 'verify_freeze', return_value={}), \
                    patch.object(m, 'load_series', return_value={}), \
                    patch.object(m, 'generate_signals', return_value={'N13': {}}), \
                    patch.object(m, 'counted', return_value={'sampleUpperBoundReached': True}), \
                    patch.object(m.io, 'read', return_value={'sampleUpperBoundReached': True}), \
                    patch.object(m, 'simulate') as simulate:
                with self.assertRaisesRegex(ValueError, 'already started'):
                    m.run_phase('development')
                simulate.assert_not_called()
            self.assertEqual(result.read_text(), 'original')

    def test_sample_is_upper_bound_and_never_approval(self):
        with patch.object(m.io, 'sha', return_value='fixture'):
            output = m.counted({i: {'symbol': 'BTCUSDT'} for i in range(100)})
        self.assertTrue(output['sampleUpperBoundReached'])
        self.assertFalse(output['validated'])
        self.assertFalse(output['PnLComputed'])

    def test_file_writer_preserves_previous_trial(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'trial.json'
            m.write_new(p, {'failed': True})
            with self.assertRaises(FileExistsError):
                m.write_new(p, {'failed': False})
            self.assertEqual(json.loads(p.read_text()), {'failed': True})


if __name__ == '__main__':
    unittest.main()
