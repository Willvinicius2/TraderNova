"""Local worker fixtures: sequence, failures, limits and no automatic approval."""
import importlib.util
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lab', ROOT / 'scripts/goal-lab.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class LabTests(unittest.TestCase):
    def test_collection_cannot_promote_incomplete_or_running_sources(self):
        self.assertEqual(m.collection_state({'coverageComplete': True, 'runningPid': 1}), 'waiting')
        self.assertEqual(m.collection_state({'coverageComplete': False}), 'incomplete_stopped')
        self.assertEqual(m.collection_state({'coverageComplete': True}), 'ready')

    def test_positive_backtest_is_only_candidate(self):
        self.assertEqual(m.final_state({'sampleUpperBoundReached': False}), 'insufficient_sample')
        self.assertEqual(m.final_state({'sampleUpperBoundReached': True},
            {'developmentPassed': True, 'validated': False, 'laterWindowsEvaluated': False}),
            'candidate_needs_review')
        with self.assertRaises(ValueError):
            m.final_state({'sampleUpperBoundReached': True}, {'validated': True})

    def test_bounded_offline_sequence_and_data_stop(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            out, cache = root / 'research/goal-seven', root / 'research/cache/goal-seven/lab'
            out.mkdir(parents=True)
            (root / 'scripts').mkdir()
            for name in ('goal-lab.py', 'audit-goal-options-trades.py', 'prepare-goal-options-skew.py',
                         'run-goal-options-skew.py', 'goal_options_market.py', 'goal_options_skew_signals.py',
                         'goal_execution_v4.py'):
                (root / 'scripts' / name).write_text('def verify_freeze(): pass\n')
            trade = out / 'options-trades-v2-data-manifest.json'
            trade.write_text('{"coverageComplete":true}')
            (out / 'options-instruments-data-manifest.json').write_text('{}')
            def save(name, data):
                (out / name).write_text(json.dumps(data))
            def child(command, **kwargs):
                script = command[1]
                if 'audit-goal-' in script:
                    save('options-identity-audit-' + m.sha(trade)[:16] + '.json', {'fullIdentityAuditComplete': True})
                elif command[2] == 'audit':
                    identity = out / ('options-identity-audit-' + m.sha(trade)[:16] + '.json')
                    inputs = {'tradeManifestSha256': m.sha(trade), 'identityAuditSha256': m.sha(identity),
                              'instrumentManifestSha256': m.sha(out / 'options-instruments-data-manifest.json')}
                    digest = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
                    save('options-metadata-audit-' + digest[:16] + '.json', {})
                elif command[2] == 'prepare':
                    save('options-skew-freeze.json', {})
                elif command[2] == 'aggregate':
                    save('options-skew-daily-manifest.json', {})
                elif command[2] == 'sample':
                    save('options-skew-sample.json', {'sampleUpperBoundReached': True,
                         'freezeSha256': m.sha(out / 'options-skew-freeze.json')})
                elif command[2] == 'development':
                    save('options-skew-results.json', {'developmentPassed': False, 'validated': False,
                        'laterWindowsEvaluated': False, 'freezeSha256': m.sha(out / 'options-skew-freeze.json'),
                        'sampleSha256': m.sha(out / 'options-skew-sample.json')})
                return SimpleNamespace(returncode=0)
            with patch.multiple(m, ROOT=root, OUT=out, CACHE=cache, TRADE=trade), \
                    patch.object(m.subprocess, 'run', side_effect=child) as run:
                result = m.run(.1)
                self.assertEqual(result['state'], 'rejected_in_development')
                self.assertEqual([s['name'] for s in result['steps']],
                                 ['identity', 'metadata', 'freeze', 'aggregate', 'sample', 'development'])
                self.assertFalse(result['validated'])
                self.assertEqual(result['modelCalls'], 0)
                trade.write_text('{"coverageComplete":false}')
                run.reset_mock()
                stopped = m.run(.1)
                self.assertEqual(stopped['state'], 'needs_review')
                run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
