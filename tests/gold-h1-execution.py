"""Synthetic execution/risk checks only. No historical data or profitability run."""
import unittest
from datetime import datetime, timedelta, timezone

import numpy as np

import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from gold_h1_execution import simulate, daily_risk_reference, execution_parameters

DTYPE = [('time', 'i8'), ('open', 'f8'), ('high', 'f8'), ('low', 'f8'), ('close', 'f8')]
DAY = datetime(2024, 1, 2, tzinfo=timezone.utc)


def stamp(hour=8, day=0):
    return int((DAY + timedelta(days=day, hours=hour)).timestamp())


def bars(n=4, hour=8, day=0, price=2000.):
    return np.array([(stamp(hour, day) + 3600 * i, price, price + .01, price - .01, price)
                     for i in range(n)], dtype=DTYPE)


def signal(direction=1, **options):
    result = {'id': 'toy', 'direction': direction,
              'stop': 1990 if direction == 1 else 2010,
              'target': 2020 if direction == 1 else 1980, 'holdBars': 32}
    result.update(options)
    return result


def run(data, signs, scenario='base', start=None, end=None):
    return simulate(data, signs, int(data['time'][0]) if start is None else start,
                    int(data['time'][-1]) + 3600 if end is None else end, scenario)


class H1ExecutionTests(unittest.TestCase):
    def assert_reconciled(self, result):
        self.assertAlmostEqual(result['net'], sum(t['net'] for t in result['trades']), places=6)
        self.assertAlmostEqual(result['endingBalance'], 100000 + result['net'], places=6)
        if result['curve']:
            self.assertAlmostEqual(result['curve'][-1]['equity'], result['endingBalance'], places=6)
        self.assertFalse(result['valid'])
        self.assertEqual(result['barSeconds'], 3600)
        self.assertGreaterEqual(result['conservativeDrawdown'] + 1e-7, result['observedClosedDrawdown'])

    def test_causal_next_hour_signal_close_and_suffix(self):
        data = bars(3)
        result = run(data, [signal(), None, None])
        trade = result['trades'][0]
        self.assertEqual(trade['entryTime'], stamp(9))
        self.assertEqual(trade['signalCloseTime'], trade['signalTime'] + 3600)
        self.assertEqual(run(data, [None, None, signal()])['trades'], [])
        extended = bars(6)
        other = run(extended, [signal()] + [None] * 5, end=stamp(11))
        self.assertEqual(result, other)
        self.assertEqual(run(data, [signal(), None, None], start=stamp(9))['trades'], [])
        self.assert_reconciled(result)

    def test_long_short_costs_base_stress_cash(self):
        for direction in (1, -1):
            for scenario, cost_per_oz, lots in [('base', .9, .22), ('stress', 1.9, .21)]:
                result = run(bars(3), [signal(direction), None, None], scenario)
                trade = result['trades'][0]
                self.assertEqual(trade['lots'], lots)
                self.assertAlmostEqual(trade['net'], -lots * 100 * cost_per_oz, places=7)
                self.assertLessEqual(trade['plannedRisk'], 250)
                self.assert_reconciled(result)

    def test_gap_through_stop_uncapped_and_target_gap_capped(self):
        for direction, opening, exit_fill in [(1, 1980, 1979.9), (-1, 2020, 2020.7)]:
            data = bars(4)
            data[2] = (stamp(10), opening, opening + .01, opening - .01, opening)
            result = run(data, [signal(direction), None, None, None])
            trade = result['trades'][0]
            self.assertEqual(trade['reason'], 'stop_gap')
            self.assertAlmostEqual(trade['exit'], exit_fill)
            self.assertGreater(-trade['net'], 250)
            self.assert_reconciled(result)
        for direction, opening, exit_fill in [(1, 2040, 2019.9), (-1, 1960, 1980.7)]:
            data = bars(4)
            data[2] = (stamp(10), opening, opening + .01, opening - .01, opening)
            trade = run(data, [signal(direction), None, None, None])['trades'][0]
            self.assertEqual(trade['reason'], 'target_gap_capped')
            self.assertAlmostEqual(trade['exit'], exit_fill)

    def test_intrabar_adverse_bound_capped_at_stop_both_sides(self):
        for direction in (1, -1):
            data = bars(3)
            data['high'][1], data['low'][1] = 2500, 1500
            result = run(data, [signal(direction), None, None])
            trade = result['trades'][0]
            self.assertEqual(trade['reason'], 'stop')
            self.assertAlmostEqual(-trade['net'], trade['plannedRisk'], places=6)
            self.assertAlmostEqual(result['conservativeDrawdown'], trade['plannedRisk'], places=6)
            self.assertFalse(result['accountBreached'])
            self.assert_reconciled(result)

    def test_intrabar_drawdown_separate_from_closed_drawdown(self):
        data = bars(3)
        data[1] = (stamp(9), 2000, 2010, 1995, 2005)
        data[2] = (stamp(10), 2005, 2006, 2004, 2005)
        result = run(data, [signal(), None, None])
        self.assertAlmostEqual(result['observedClosedDrawdown'], 0)
        self.assertAlmostEqual(result['conservativeDrawdown'], 129.8, places=6)
        self.assertGreater(result['maxDailyConservativeEquityLoss'], result['maxDailyClosedEquityLoss'])
        self.assert_reconciled(result)

    def test_favorable_future_extreme_does_not_raise_peak_or_size(self):
        data = bars(3)
        data['low'][1] = 1995
        baseline = run(data, [signal(target=2100), None, None])
        data['high'][1] = 2070
        other = run(data, [signal(target=2100), None, None])
        self.assertEqual(baseline, other)

    def test_reference_max_balance_or_marked_floating_profit_loss(self):
        for last_close, expected_reference in [(2010., 100203.5), (1995., 99998.9)]:
            data = np.array([
                (stamp(18), 2000, 2000.01, 1999.99, 2000),
                (stamp(19), 2000, max(2000, last_close) + .01,
                 min(2000, last_close) - .01, last_close),
                (stamp(0, 1), 2000, 2000.01, 1999.99, 2000),
                (stamp(1, 1), 2000, 2000.01, 1999.99, 2000),
            ], dtype=DTYPE)
            result = run(data, [signal(target=3000), None, None, None])
            reference = result['daily'][1]
            self.assertAlmostEqual(reference['referenceEquity'], expected_reference, places=6)
            self.assertAlmostEqual(reference['referenceBalance'], 99998.9, places=6)
            self.assertAlmostEqual(reference['referenceMarkedEquity'],
                                   99998.9 + (last_close - 2000.7) * 22, places=6)
            self.assertAlmostEqual(reference['lossLimit'], min(3000, .03 * expected_reference), places=6)
            self.assertEqual(result['overnightUnpriced'], 1)
            self.assert_reconciled(result)

    def test_daily_limit_percentage_and_3000_cap(self):
        lower = daily_risk_reference(96000, 95000)
        self.assertEqual(lower['referenceEquity'], 96000)
        self.assertEqual(lower['lossLimit'], 2880)
        self.assertEqual(lower['equityFloor'], 93120)
        upper = daily_risk_reference(110000, 120000)
        self.assertEqual(upper['referenceEquity'], 120000)
        self.assertEqual(upper['lossLimit'], 3000)
        self.assertEqual(upper['equityFloor'], 117000)

    def test_daily_breach_permanent_across_days_no_limit_price_fill(self):
        data = np.array([
            (stamp(8), 2000, 2000.01, 1999.99, 2000),
            (stamp(9), 2000, 2000.01, 1999.99, 2000),
            (stamp(10), 1850, 1850.01, 1849.99, 1850),
            (stamp(11), 1850, 1850.01, 1849.99, 1850),
            (stamp(8, 1), 1850, 1850.01, 1849.99, 1850),
            (stamp(9, 1), 1850, 1850.01, 1849.99, 1850),
        ], dtype=DTYPE)
        result = run(data, [signal(), None, None, None,
                            signal(id='newday', stop=1840, target=1870), None])
        self.assertEqual(len(result['trades']), 1)
        trade = result['trades'][0]
        self.assertEqual(trade['reason'], 'stop_gap')
        self.assertAlmostEqual(trade['exit'], 1849.9)
        self.assertAlmostEqual(trade['net'], -3319.8, places=6)
        self.assertTrue(result['accountBreached'])
        self.assertTrue(result['dailyLossBreached'])
        self.assertFalse(result['totalLossBreached'])
        self.assertTrue(result['permanentRiskBlock'])
        self.assertTrue(result['rejectedForRiskBreach'])
        self.assertEqual(result['daily'][1]['entries'], 0)
        self.assertGreater(result['skipped']['risk_pause'], 0)
        self.assertEqual(result['breaches'][0]['kind'], 'daily_loss')
        self.assert_reconciled(result)

    def test_total_floor_breach_and_no_next_day_reset(self):
        data = bars(4)
        data[2] = (stamp(10), 1400, 1400.01, 1399.99, 1400)
        data[3] = (stamp(9, 1), 2000, 2000.01, 1999.99, 2000)
        result = run(data, [signal(), None, None, None])
        self.assertTrue(result['accountBreached'])
        self.assertTrue(result['totalLossBreached'])
        self.assertLess(result['endingBalance'], 90000)
        self.assertTrue(result['curve'][-1]['accountBreached'])
        self.assert_reconciled(result)

    def test_cutoff_at_20_open_precedes_candle_extremes_and_no_20_entry(self):
        data = bars(4, hour=18)
        data[2] = (stamp(20), 2002, 2500, 1500, 2000)
        result = run(data, [signal(), signal(), None, None])
        self.assertEqual(len(result['trades']), 1)
        self.assertEqual(result['trades'][0]['exitTime'], stamp(20))
        self.assertEqual(result['trades'][0]['reason'], 'session_cutoff')
        self.assertAlmostEqual(result['trades'][0]['exit'], 2001.9)
        self.assertFalse(result['accountBreached'])
        self.assertEqual(run(bars(2, hour=19), [signal(), None])['trades'], [])
        self.assert_reconciled(result)

    def test_missing_cutoff_is_never_invisible_overnight(self):
        data = bars(3, hour=18)
        data['time'][2] = stamp(8, 1)
        result = run(data, [signal(), None, None])
        self.assertEqual(result['trades'][0]['reason'], 'data_gap')
        self.assertEqual(result['trades'][0]['exitTime'], stamp(8, 1))
        self.assertTrue(result['trades'][0]['overnightUnknownCost'])
        self.assertEqual(result['overnightUnpriced'], 1)
        self.assert_reconciled(result)

    def test_budget_full_250_and_lot_rounding_limits(self):
        data = np.concatenate([bars(13, hour=8, day=d) for d in range(4)])
        data['low'] = 1989
        signs = [signal(id=f'family{i}') for i in range(len(data))]
        result = run(data, signs)
        self.assertEqual([d['entries'] for d in result['daily']], [11, 11, 11, 8])
        self.assertGreater(result['endingBalance'], 90000)
        self.assertLess(result['endingBalance'] - 90000, 250)
        self.assertFalse(result['accountBreached'])
        self.assertGreater(result['skipped']['insufficient_full_risk_budget'], 0)
        self.assert_reconciled(result)

    def test_metadata_validation_and_tick_rounding(self):
        parameters = execution_parameters('base')
        self.assertEqual(parameters['barSeconds'], 3600)
        self.assertEqual(parameters['cutoff'], '20:00')
        self.assertEqual(parameters['dailyLossFraction'], .03)
        for direction, stop, target, expected_stop, expected_target in [
                (1, 1990.003, 2020.001, 1990, 2020.01),
                (-1, 2009.997, 1979.999, 2010, 1979.99)]:
            trade = run(bars(2), [signal(direction, stop=stop, target=target), None])['trades'][0]
            self.assertEqual(trade['stop'], expected_stop)
            self.assertEqual(trade['target'], expected_target)
        with self.assertRaises(ValueError):
            run(bars(2), [None, None], start=stamp() + 900)


if __name__ == '__main__':
    unittest.main(verbosity=2)
