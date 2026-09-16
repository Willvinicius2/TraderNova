"""Synthetic execution checks only; no broker data or strategy results."""
import unittest
from datetime import datetime, timedelta, timezone

import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from gold_execution import simulate

DTYPE = [('time', 'i8'), ('open', 'f8'), ('high', 'f8'), ('low', 'f8'), ('close', 'f8')]
DAY = datetime(2024, 1, 2, tzinfo=timezone.utc)


def stamp(hour=8, minute=0, day=0):
    return int((DAY + timedelta(days=day, hours=hour, minutes=minute)).timestamp())


def bars(n=5, first=None, price=2000.0):
    first = stamp() if first is None else first
    return np.array([(first + 900 * i, price, price + .01, price - .01, price)
                     for i in range(n)], dtype=DTYPE)


def signal(direction=1, **options):
    result = {'id': 'toy', 'direction': direction, 'stop': 1990 if direction == 1 else 2010,
              'target': 2020 if direction == 1 else 1980, 'holdBars': 32}
    result.update(options)
    return result


def run(data, signs, scenario='base', start=None, end=None):
    return simulate(data, signs, int(data['time'][0]) if start is None else start,
                    int(data['time'][-1]) + 900 if end is None else end, scenario)


class ExecutionTests(unittest.TestCase):
    def assert_reconciled(self, result):
        self.assertAlmostEqual(result['net'], sum(t['net'] for t in result['trades']), places=6)
        self.assertAlmostEqual(result['endingBalance'], 100000 + result['net'], places=6)
        if result['curve']:
            self.assertAlmostEqual(result['curve'][-1]['equity'], result['endingBalance'], places=6)
        self.assertFalse(result['valid'])

    def test_flat_long_short_costs_and_cash(self):
        for direction in (1, -1):
            for scenario, unit_cost, lots in [('base', .9, .22), ('stress', 1.9, .21)]:
                data = bars(3)
                result = run(data, [signal(direction), None, None], scenario)
                trade = result['trades'][0]
                self.assertEqual(trade['lots'], lots)
                self.assertAlmostEqual(trade['net'], -lots * 100 * unit_cost, places=7)
                self.assertAlmostEqual(trade['commission'], lots * (10 if scenario == 'base' else 20))
                self.assertLessEqual(trade['plannedRisk'], 250)
                self.assert_reconciled(result)

    def test_stop_first_both_directions_includes_cost(self):
        for direction in (1, -1):
            data = bars(3)
            data['high'][1], data['low'][1] = 2021, 1979
            result = run(data, [signal(direction), None, None])
            trade = result['trades'][0]
            self.assertEqual(trade['reason'], 'stop')
            self.assertEqual(trade['exitTimeKind'], 'intrabar_unknown')
            self.assertAlmostEqual(-trade['net'], trade['plannedRisk'], places=6)
            self.assert_reconciled(result)

    def test_adverse_gap_worsens_stop(self):
        for direction, opening in [(1, 1980), (-1, 2020)]:
            data = bars(4)
            data[2] = (data['time'][2], opening, opening + .01, opening - .01, opening)
            result = run(data, [signal(direction), None, None, None])
            trade = result['trades'][0]
            self.assertEqual(trade['reason'], 'stop_gap')
            expected = opening - .1 if direction == 1 else opening + .7
            self.assertAlmostEqual(trade['exit'], expected)
            self.assertGreater(-trade['net'], 250)
            self.assert_reconciled(result)

    def test_favorable_gap_target_capped(self):
        for direction, opening, fill in [(1, 2040, 2019.9), (-1, 1960, 1980.7)]:
            data = bars(4)
            data[2] = (data['time'][2], opening, opening + .01, opening - .01, opening)
            result = run(data, [signal(direction), None, None, None])
            trade = result['trades'][0]
            self.assertEqual(trade['reason'], 'target_gap_capped')
            self.assertAlmostEqual(trade['exit'], fill)
            self.assert_reconciled(result)

    def test_short_brackets_use_ask_conversion_once(self):
        data = bars(3)
        data['low'][1] = 1980
        result = run(data, [signal(-1), None, None])
        trade = result['trades'][0]
        self.assertEqual(trade['reason'], 'target')
        self.assertAlmostEqual(trade['entry'], 1999.9)
        self.assertAlmostEqual(trade['exit'], 1980.7)
        self.assertAlmostEqual(trade['net'], (19.2 * 100 - 10) * .22)

    def test_closed_signal_next_open_no_same_bar_or_future(self):
        data = bars(2)
        self.assertEqual(run(data, [None, signal()])['trades'], [])
        data['high'][0], data['low'][0] = 2021, 1989
        result = run(data, [signal(), None])
        self.assertEqual(result['trades'][0]['entryTime'], stamp(8, 15))
        self.assertEqual(result['trades'][0]['reason'], 'window_end')
        longer = bars(8)
        longer[:2] = data
        extended = run(longer, [signal()] + [None] * 7, end=stamp(8, 30))
        self.assertEqual(result, extended)

    def test_warmup_signal_cannot_cross_window_start(self):
        data = bars(3)
        result = run(data, [signal(), None, None], start=stamp(8, 15))
        self.assertEqual(result['trades'], [])

    def test_discontinuous_and_cross_day_entries_blocked(self):
        data = bars(2)
        data['time'][1] += 900
        result = run(data, [signal(), None])
        self.assertEqual(result['trades'], [])
        self.assertEqual(result['skipped']['discontinuous_or_cross_day_entry'], 1)
        data['time'] = [stamp(23, 45), stamp(0, 0, 1)]
        result = run(data, [signal(), None])
        self.assertEqual(result['trades'], [])

    def test_recomputed_reward_and_fixed_target(self):
        data = bars(3)
        data[1] = (data['time'][1], 2002, 2002.01, 2001.99, 2002)
        signs = [signal(reward=2, atr=10), None, None]
        result = run(data, signs)
        self.assertEqual(result['trades'][0]['target'], 2026)
        signs[0] = signal(atr=10)
        result = run(data, signs)
        self.assertEqual(result['trades'][0]['target'], 2020)

    def test_entry_gap_invalidates_bracket_atr_or_reward(self):
        for options, bid, skip in [({}, 1989, 'invalid_entry_bracket'),
                                   ({'atr': 10}, 1995, 'entry_stop_atr_range'),
                                   ({}, 2018, 'entry_reward_r')]:
            data = bars(2)
            data[1] = (data['time'][1], bid, bid + .01, bid - .01, bid)
            result = run(data, [signal(**options), None])
            self.assertEqual(result['trades'], [])
            self.assertEqual(result['skipped'][skip], 1)

    def test_trade_limit_counts_successful_entries_only(self):
        data = bars(7)
        data['low'][1:] = 1989
        signs = [signal(stop=2001, maxTradesPerDay=1), signal(maxTradesPerDay=1)]
        signs += [signal(maxTradesPerDay=1)] * 5
        result = run(data, signs)
        self.assertEqual(len(result['trades']), 1)
        self.assertEqual(result['trades'][0]['entryTime'], stamp(8, 30))
        self.assertEqual(result['daily'][0]['entries'], 1)
        result = run(data, [signal()] * len(data))
        self.assertEqual(len(result['trades']), 2)

    def test_hold_count_exits_at_next_open_after_n_bars(self):
        data = bars(6)
        result = run(data, [signal(holdBars=2)] + [None] * 5)
        trade = result['trades'][0]
        self.assertEqual(trade['exitTime'], stamp(8, 45))
        self.assertEqual(trade['barsHeld'], 2)
        self.assertEqual(trade['reason'], 'max_hold')

    def test_cutoff_2045_and_missing_cutoff(self):
        data = bars(7, stamp(19, 30))
        result = run(data, [signal()] + [None] * 6)
        self.assertEqual(result['trades'][0]['exitTime'], stamp(20, 45))
        self.assertEqual(result['trades'][0]['reason'], 'session_cutoff')
        reduced = data[[0, 1, 2, 3, 4, 6]]
        result = run(reduced, [signal()] + [None] * 5)
        self.assertEqual(result['trades'][0]['exitTime'], stamp(21))
        self.assertEqual(result['overnightUnpriced'], 0)
        reduced['time'][-1] = stamp(8, day=1)
        result = run(reduced, [signal()] + [None] * 5)
        self.assertEqual(result['trades'][0]['exitTime'], stamp(8, day=1))
        self.assertEqual(result['overnightUnpriced'], 1)
        self.assertTrue(result['trades'][0]['overnightUnknownCost'])

    def test_unexpected_intraday_gap_exits_without_overnight(self):
        data = bars(4)
        data['time'][2:] += 900
        result = run(data, [signal(), None, None, None])
        self.assertEqual(result['trades'][0]['reason'], 'data_gap')
        self.assertEqual(result['overnightUnpriced'], 0)

    def test_entry_hours(self):
        for opening, expected in [(stamp(7, 45), 1), (stamp(7, 30), 0),
                                  (stamp(19, 30), 1), (stamp(19, 45), 0)]:
            data = bars(2, opening)
            self.assertEqual(len(run(data, [signal(), None])['trades']), expected)

    def test_daily_budget_and_total_floor_without_partial_risk(self):
        data = np.concatenate([bars(30, stamp(day=d)) for d in range(4)])
        data['low'] = 1989
        signs = [signal(id=f'family{i}') for i in range(len(data))]
        result = run(data, signs)
        self.assertEqual([day['entries'] for day in result['daily']], [12, 12, 12, 5])
        self.assertEqual(len(result['trades']), 41)
        self.assertGreater(result['endingBalance'], 90000)
        self.assertLess(result['endingBalance'] - 90000, 250)
        self.assertLessEqual(result['maxDailyClosedEquityLoss'], 3000)
        self.assertGreater(result['skipped']['insufficient_full_risk_budget'], 0)
        for previous, following in zip(result['daily'], result['daily'][1:]):
            self.assertAlmostEqual(previous['endingEquity'], following['referenceEquity'])
        self.assert_reconciled(result)

    def test_gap_can_exceed_floor_then_permanently_block_entries(self):
        data = bars(5)
        data[2:] = [(t, 1000, 1000.01, 999.99, 1000) for t in data['time'][2:]]
        signs = [signal(), None, signal(stop=990, target=1020), None, None]
        result = run(data, signs)
        self.assertEqual(len(result['trades']), 1)
        self.assertTrue(result['totalRiskPaused'])
        self.assertLess(result['endingBalance'], 90000)
        self.assertGreater(result['skipped']['risk_pause'], 0)
        self.assert_reconciled(result)

    def test_notional_cap_and_cent_lots(self):
        data = bars(2, price=10000)
        data['high'], data['low'] = 10000.005, 9999.995
        result = run(data, [signal(stop=9999.90, target=10000.20), None])
        trade = result['trades'][0]
        self.assertEqual(trade['lots'], .99)
        self.assertLessEqual(trade['entry'] * trade['quantityOz'], 1000000)
        self.assertLessEqual(trade['plannedRisk'], 250)
        self.assert_reconciled(result)

    def test_tick_rounding_and_minimum_stop(self):
        data = bars(2)
        for direction, stop, target, expected_stop, expected_target in [(1,1990.003,2020.001,1990,2020.01),(-1,2009.997,1979.999,2010,1979.99)]:
            result=run(data,[signal(direction,stop=stop,target=target),None])
            self.assertEqual(result['trades'][0]['stop'],expected_stop)
            self.assertEqual(result['trades'][0]['target'],expected_target)
        self.assertEqual(len(run(data,[signal(stop=1999.95,target=2000.20),None])['trades']),0)

    def test_validation_and_empty_window(self):
        data = bars(3)
        with self.assertRaises(ValueError):
            simulate(data, [None], stamp(), stamp(9))
        malformed = data.copy()
        malformed['time'][1] = malformed['time'][0]
        with self.assertRaises(ValueError):
            run(malformed, [None] * 3)
        result = run(data, [None] * 3, start=stamp(12), end=stamp(13))
        self.assertEqual(result['net'], 0)
        self.assertEqual(result['curve'], [])
        self.assertIsNone(result['profitFactor'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
