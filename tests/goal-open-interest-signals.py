"""Deterministic N11 rule, input-integrity, and causal-prefix fixtures; no PnL."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.goal_open_interest_signals import generate_signals


HOUR = 3600
ASSETS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")


def bar(open_time=0, close="99.5"):
    return {"time": open_time, "open": "100", "high": "100", "low": close,
            "close": close, "received_at": open_time + HOUR}


def point(time, quantity, received_at):
    return {"observation_end": time, "sum_open_interest": quantity,
            "sum_open_interest_value": "999999999", "received_at": received_at}


def fixture():
    perp = {asset: [bar()] for asset in ASSETS}
    oi = {asset: [point(0, "1000", 0), point(HOUR, "995", HOUR + 3300)]
          for asset in ASSETS}
    return perp, oi


def signals(perp, oi, **kwargs):
    return generate_signals(perp, oi, **kwargs)["N11"]


class OpenInterestSignalsTest(unittest.TestCase):
    def test_inclusive_boundaries_and_executor_clock(self):
        perp, oi = fixture()
        self.assertEqual(signals(perp, oi), {HOUR: {
            "symbol": "BTCUSDT", "direction": 1, "stop_pct": 0.015,
            "hold_hours": 4, "signal_close_time": 2 * HOUR,
            "feature_end": HOUR, "decision_time": HOUR + 3300,
            "availability_mode": "observed_receipt",
            "reason": "oi_quantity_contraction_price_shock_recovery",
        }})
        perp["BTCUSDT"][0]["close"] = "99.501"
        perp["BTCUSDT"][0]["low"] = "99.501"
        self.assertEqual(signals(perp, oi)[HOUR]["symbol"], "ETHUSDT")
        perp["BTCUSDT"][0] = bar()
        oi["BTCUSDT"][1]["sum_open_interest"] = "995.001"
        self.assertEqual(signals(perp, oi)[HOUR]["symbol"], "ETHUSDT")

    def test_quantity_not_notional_and_priority(self):
        perp, oi = fixture()
        for asset in ASSETS:
            oi[asset][1]["sum_open_interest_value"] = "1"
        oi["BTCUSDT"][1]["sum_open_interest"] = "1000"
        self.assertEqual(signals(perp, oi)[HOUR]["symbol"], "ETHUSDT")
        oi["ETHUSDT"][1]["sum_open_interest"] = "1000"
        self.assertEqual(signals(perp, oi)[HOUR]["symbol"], "SOLUSDT")
        oi["SOLUSDT"][1]["sum_open_interest"] = "1000"
        self.assertNotIn(HOUR, signals(perp, oi))

    def test_exact_hourly_points_and_one_hour_lag(self):
        perp, oi = fixture()
        oi["BTCUSDT"][1]["observation_end"] = HOUR - 300
        self.assertEqual(signals(perp, oi)[HOUR]["symbol"], "ETHUSDT")
        perp, oi = fixture()
        for asset in ASSETS:
            perp[asset] = [bar(HOUR)]
            oi[asset] = [point(HOUR, "1000", HOUR),
                         point(2 * HOUR, "995", 2 * HOUR + 3300)]
        self.assertNotIn(HOUR, signals(perp, oi))
        self.assertEqual(signals(perp, oi)[2 * HOUR]["signal_close_time"], 3 * HOUR)

    def test_missing_duplicates_invalid_and_endpoint_failure(self):
        perp, oi = fixture()
        oi["BTCUSDT"].pop(0)
        self.assertEqual(signals(perp, oi)[HOUR]["symbol"], "ETHUSDT")
        perp, oi = fixture()
        oi["BTCUSDT"].append(copy.deepcopy(oi["BTCUSDT"][1]))
        self.assertEqual(signals(perp, oi)[HOUR]["symbol"], "ETHUSDT")
        perp, oi = fixture()
        perp["BTCUSDT"].append(copy.deepcopy(perp["BTCUSDT"][0]))
        self.assertEqual(signals(perp, oi)[HOUR]["symbol"], "ETHUSDT")
        for bad in ("0", "NaN", "Infinity", "-3", True):
            perp, oi = fixture()
            oi["BTCUSDT"][1]["sum_open_interest"] = bad
            self.assertEqual(signals(perp, oi)[HOUR]["symbol"], "ETHUSDT")
        perp, oi = fixture()
        perp["BTCUSDT"][0]["high"] = "99"
        self.assertEqual(signals(perp, oi)[HOUR]["symbol"], "ETHUSDT")
        self.assertEqual(generate_signals(perp, None), {"N11": {}})
        self.assertEqual(signals(perp, {"BTCUSDT": None}), {})

    def test_receipt_timestamp_and_historical_assumption(self):
        perp, oi = fixture()
        oi["BTCUSDT"][1]["received_at"] = HOUR + 3301
        self.assertEqual(signals(perp, oi)[HOUR]["symbol"], "ETHUSDT")
        perp, oi = fixture()
        perp["BTCUSDT"][0]["received_at"] = HOUR + 3301
        self.assertEqual(signals(perp, oi)[HOUR]["symbol"], "ETHUSDT")
        perp, oi = fixture()
        for asset in ASSETS:
            perp[asset][0].pop("received_at")
            for row in oi[asset]:
                row.pop("received_at")
        self.assertEqual(signals(perp, oi), {})
        assumed = signals(perp, oi, historical_assumption=True)
        self.assertEqual(assumed[HOUR]["availability_mode"], "assumed_historical")
        oi["BTCUSDT"][1]["received_at"] = HOUR + 3301
        self.assertEqual(signals(perp, oi, historical_assumption=True)[HOUR]["symbol"], "ETHUSDT")
        oi["BTCUSDT"][1]["received_at"] = HOUR - 1
        self.assertEqual(signals(perp, oi, historical_assumption=True)[HOUR]["symbol"], "ETHUSDT")

    def test_prefix_future_invariance(self):
        perp, oi = fixture()
        initial = signals(perp, oi)
        later_perp, later_oi = copy.deepcopy(perp), copy.deepcopy(oi)
        for asset in ASSETS:
            later_perp[asset].append(bar(HOUR, "1"))
            later_oi[asset].append(point(2 * HOUR, "1", 2 * HOUR + 3300))
        self.assertEqual({t: s for t, s in signals(later_perp, later_oi).items()
                          if t <= HOUR}, initial)
        later_perp["BTCUSDT"][1]["close"] = "99999"
        later_perp["BTCUSDT"][1]["high"] = "99999"
        self.assertEqual({t: s for t, s in signals(later_perp, later_oi).items()
                          if t <= HOUR}, initial)


if __name__ == "__main__":
    unittest.main()
