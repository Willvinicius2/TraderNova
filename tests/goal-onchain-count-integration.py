"""Synthetic feature timing, actual H1 execution and fail-closed input checks."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from goal_onchain_count_signals import DAY, HOUR, generate_signals
from goal_execution_v3 import simulate
spec = importlib.util.spec_from_file_location('runner', ROOT / 'scripts/run-goal-onchain-count.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class Integration(unittest.TestCase):
    def test_source_label_to_fill_and_twelve_hour_hold(self):
        daily = [dict(time=i * DAY, count=str(i + 1)) for i in range(91)]
        signals = generate_signals({'BTCUSDT': daily}, historical_assumption=True)['N12']
        entry = 93 * DAY + HOUR
        start, end = entry - HOUR, entry + 14 * HOUR
        bars = [dict(time=t, open=100., high=100., low=100., close=100.) for t in range(start, end, HOUR)]
        result = simulate({'BTCUSDT': bars}, {'BTCUSDT': bars}, {'BTCUSDT': []}, signals, start, end)
        self.assertEqual(result['trade_count'], 1)
        self.assertEqual(result['trades'][0]['entry_time'], entry)
        self.assertEqual(result['trades'][0]['exit_time'], entry + 12 * HOUR)
        self.assertFalse(result['data_quality_flags'])
        self.assertAlmostEqual(result['net_cash'], result['trades'][0]['pnl'])

    def test_daily_audit_detects_missing_manifest_mismatch_and_duplicates(self):
        rows = [dict(time=t, count='1') for t in range(runner.SOURCE_START, runner.END, DAY)]
        self.assertTrue(runner.audit_daily(rows, len(rows))['complete'])
        removed = rows.pop(10)
        self.assertEqual(runner.audit_daily(rows, len(rows))['missingDays'], [removed['time']])
        with self.assertRaises(ValueError):
            runner.audit_daily(rows, len(rows) + 1)
        with self.assertRaises(ValueError):
            runner.audit_daily(rows + [rows[0]], len(rows) + 1)
        with self.assertRaises(ValueError):
            runner.audit_daily([dict(time=runner.END, count='1')], 1)

    def test_every_execution_quality_flag_fails_gate(self):
        fake = dict(trade_count=100, net_cash=1000, profit_factor=2, max_drawdown_pct=1,
                    max_daily_loss_pct=.1, account_breach=False, data_quality_flags=[])
        protocol = runner.io.read(runner.OUT / 'protocol.json')
        self.assertEqual(runner.io.gate(fake, 100, 'base', protocol), [])
        for issue in ('missing_entry_trade', 'missing_entry_mark', 'unpriced_funding'):
            fake['data_quality_flags'] = [dict(issue=issue)]
            self.assertIn('incomplete_active_source', runner.io.gate(fake, 100, 'base', protocol))


if __name__ == '__main__':
    unittest.main()
