"""N11 signal-to-fill clock and observed-availability integration fixtures."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from goal_execution_v2 import simulate
from goal_open_interest_signals import generate_signals

H = 3600
S = 'BTCUSDT'
SPEC = importlib.util.spec_from_file_location('oi_runner', Path(__file__).resolve().parents[1] / 'scripts/run-goal-open-interest.py')
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def fixture():
    bars = [{'time': h * H, 'open': 200.0, 'high': 200.0, 'low': 200.0,
             'close': 200.0, 'received_at': (h + 1) * H} for h in range(8)]
    bars[0].update(open=100.0, high=100.0, low=99.5, close=99.5)
    oi = [{'observation_end': 0, 'sum_open_interest': '1000', 'received_at': 0},
          {'observation_end': H, 'sum_open_interest': '995', 'received_at': H + 3300}]
    return {S: bars}, {S: copy.deepcopy(bars)}, {S: oi}


class N11ExecutionIntegration(unittest.TestCase):
    def test_archive_slot_start_is_aligned_before_hourly_selection(self):
        raw = [{'time': t, 'sum_open_interest': '1000', 'sum_open_interest_value': '100000'}
               for t in (3300, 3600, 6900)]
        with patch.multiple(RUNNER, START=3600, END=10800):
            hourly, audit = RUNNER.align_and_audit_oi(raw, 3)
        self.assertEqual([row['observation_end'] for row in hourly], [3600, 7200])
        self.assertEqual([row['time'] for row in hourly], [3300, 6900])
        self.assertTrue(audit['requiredHourlyComplete'])
        self.assertEqual(audit['missingFiveMinutePoints'], 21)

    def test_input_count_duplicates_invalid_values_and_missing_hours(self):
        raw = [{'time': 3300, 'sum_open_interest': '1000', 'sum_open_interest_value': '100000'}]
        with patch.multiple(RUNNER, START=3600, END=10800):
            with self.assertRaises(ValueError):
                RUNNER.align_and_audit_oi(raw, 2)
            with self.assertRaises(ValueError):
                RUNNER.align_and_audit_oi(raw + raw, 2)
            with self.assertRaises(ValueError):
                RUNNER.align_and_audit_oi([dict(raw[0], sum_open_interest='NaN')], 1)
            _, audit = RUNNER.align_and_audit_oi(raw, 1)
        self.assertFalse(audit['requiredHourlyComplete'])
        self.assertEqual(audit['firstMissingHourlyPoints'], [7200])

    def test_delayed_fill_four_hour_exit_and_funding(self):
        perp, marks, oi = fixture()
        decisions = generate_signals(perp, oi)['N11']
        funding = {S: [{'time_ms': 2 * H * 1000 + 1, 'rate': .001, 'mark_price': 200}]}
        result = simulate(perp, marks, funding, decisions, 0, 8 * H)
        self.assertEqual(result['trade_count'], 1)
        trade = result['trades'][0]
        self.assertEqual(trade['entry_time'], 2 * H)
        self.assertEqual(trade['exit_time'], 6 * H)
        self.assertAlmostEqual(trade['entry'], 200 * 1.0002)
        self.assertAlmostEqual(trade['funding_pnl'], -trade['qty'] * .2)
        self.assertAlmostEqual(trade['risk_budget'], 250)
        self.assertEqual(result['data_quality_flags'], [])

    def test_intervening_hour_return_never_changes_earlier_decision_or_fill(self):
        perp, marks, oi = fixture()
        baseline = simulate(perp, marks, {S: []}, generate_signals(perp, oi)['N11'], 0, 8 * H)
        perp[S][1].update(high=1000.0, low=1.0, close=1.0)
        marks[S][1].update(high=1000.0, low=1.0, close=1.0)
        perturbed = simulate(perp, marks, {S: []}, generate_signals(perp, oi)['N11'], 0, 8 * H)
        self.assertEqual(baseline, perturbed)

    def test_prospective_missing_receipts_cannot_enter(self):
        perp, marks, oi = fixture()
        for point in oi[S]:
            point.pop('received_at')
        observed = generate_signals(perp, oi)['N11']
        self.assertEqual(simulate(perp, marks, {S: []}, observed, 0, 8 * H)['trade_count'], 0)
        exploratory = generate_signals(perp, oi, historical_assumption=True)['N11']
        self.assertEqual(simulate(perp, marks, {S: []}, exploratory, 0, 8 * H)['trade_count'], 1)


if __name__ == '__main__':
    unittest.main()
