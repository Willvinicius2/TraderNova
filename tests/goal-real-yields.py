"""Synthetic causal fixtures for N7; no historical performance is calculated."""

import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import goal_real_yields as study
import gold_h1_execution as engine
from gold_signals import DTYPE


def fixture_bars():
    start = datetime(2024, 1, 16, tzinfo=timezone.utc)
    return np.array([
        (int((start + timedelta(hours=i)).timestamp()), 100., 101., 99., 100., 0)
        for i in range(5 * 24)
    ], dtype=DTYPE)


def fixture_yields():
    first = date(2024, 1, 1)
    rows = [(first + timedelta(days=i), 2.0) for i in range(14)]
    rows[12] = (rows[12][0], 1.85)  # Jan 13, last eligible on Jan 20
    rows[13] = (rows[13][0], 9.0)   # Jan 14, only six calendar days old
    return rows


class RealYieldSignalsTest(unittest.TestCase):
    def test_calendar_lag_and_exact_delta_boundary(self):
        bars, yields = fixture_bars(), fixture_yields()
        signals = study.make_signals(bars, yields)
        i = next(i for i, b in enumerate(bars) if study.stamp_day(int(b["time"])) == date(2024, 1, 20)
                 and int(b["time"]) % 86400 == 8 * 3600)
        one = signals[i]
        self.assertEqual(one["treasuryObservationDate"], "2024-01-13")
        self.assertEqual(one["treasuryDeltaPctPoints"], -0.15)
        self.assertEqual((one["direction"], one["stop"], one["target"]), (1, 96., 108.))
        self.assertEqual((one["reward"], one["holdBars"], one["maxTradesPerDay"]), (2., 8, 1))
        self.assertTrue(all(s is None for j, s in enumerate(signals) if int(bars["time"][j]) % 86400 != 8 * 3600))

    def test_five_prior_observations_not_five_calendar_days(self):
        dates = [date(2024, 1, n) for n in (1, 2, 3, 5, 8, 10, 13, 14)]
        values = [2., 2., 2., 2., 1.85, 2., 1.85, 9.]
        chosen = study.select_observation(date(2024, 1, 20), list(zip(dates, values)))
        self.assertEqual(chosen, (6, study.Decimal("-0.15")))

    def test_age_limit_and_no_future_yield(self):
        yields = [(date(2023, 12, 28) + timedelta(days=n), 2.0) for n in range(9)]
        self.assertIsNone(study.select_observation(date(2024, 1, 20), yields))
        baseline = study.select_observation(date(2024, 1, 20), fixture_yields())
        changed = fixture_yields()
        changed[-1] = (changed[-1][0], -100.)
        self.assertEqual(study.select_observation(date(2024, 1, 20), changed), baseline)

    def test_future_price_perturbation_and_prefix(self):
        bars, yields = fixture_bars(), fixture_yields()
        i = next(i for i, b in enumerate(bars) if study.stamp_day(int(b["time"])) == date(2024, 1, 20)
                 and int(b["time"]) % 86400 == 8 * 3600)
        full = study.make_signals(bars, yields)
        self.assertEqual(study.make_signals(bars[:i + 1], yields), full[:i + 1])
        altered = bars.copy()
        altered["close"][i + 1:] = 200.
        altered["high"][i + 1:] = 200.
        self.assertEqual(study.make_signals(altered, yields)[:i + 1], full[:i + 1])

    def test_synthetic_decision_links_to_next_broker_open(self):
        bars, yields = fixture_bars(), fixture_yields()
        signals = study.make_signals(bars, yields)
        previous = engine.MAX_LEVERAGE
        try:
            engine.MAX_LEVERAGE = 1.0
            result = engine.simulate(bars, signals, int(bars["time"][0]),
                                     int(bars["time"][-1]) + 3600, "base")
        finally:
            engine.MAX_LEVERAGE = previous
        self.assertEqual(len(result["trades"]), 1)
        trade = result["trades"][0]
        self.assertEqual(trade["entryTime"], trade["signalCloseTime"])
        self.assertEqual(trade["entryTime"] - trade["signalTime"], 3600)
        self.assertEqual(trade["entryTime"] % 86400, 9 * 3600)
        self.assertLessEqual(trade["entry"] * trade["quantityOz"], 100000)


if __name__ == "__main__":
    unittest.main()
