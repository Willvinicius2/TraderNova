"""Causality and boundary checks for preregistered N5/N6 signal generation."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.goal_signals import generate_signals


HOUR = 3600


def bar(hour, open_price="100", close_price="100", volume="100", taker="60"):
    op, cl = float(open_price), float(close_price)
    return {
        "time": hour * HOUR,
        "open": open_price,
        "high": str(max(op, cl)),
        "low": str(min(op, cl)),
        "close": close_price,
        "quote_volume": volume,
        "taker_buy_quote_volume": taker,
    }


def fixture():
    spot = {asset: [bar(hour) for hour in range(25)] for asset in (
        "BTCUSDT", "ETHUSDT", "SOLUSDT"
    )}
    spot["BTCUSDT"][-1]["close"] = "100.25"
    spot["BTCUSDT"][-1]["high"] = "100.25"
    spot["ETHUSDT"][-1]["close"] = "100.20"
    spot["ETHUSDT"][-1]["high"] = "100.20"
    return spot


def leader_fixture():
    spot = fixture()
    spot["BTCUSDT"][-1]["close"] = "100.75"
    spot["BTCUSDT"][-1]["high"] = "100.75"
    return spot


class GoalSignalsTest(unittest.TestCase):
    def test_exact_boundaries_and_priority(self):
        signals = generate_signals(fixture())
        self.assertEqual(signals["N5"][24 * HOUR], {
            "symbol": "BTCUSDT", "direction": 1, "stop_pct": 0.01,
            "hold_hours": 2, "signal_close_time": 25 * HOUR,
            "reason": "taker_buy_pressure_continuation",
        })
        self.assertEqual(generate_signals(leader_fixture())["N6"][24 * HOUR], {
            "symbol": "ETHUSDT", "direction": 1, "stop_pct": 0.015,
            "hold_hours": 2, "signal_close_time": 25 * HOUR,
            "reason": "btc_leads_altcoin",
        })

    def test_n5_quote_fields_and_current_bar_excluded_from_median(self):
        spot = fixture()
        btc = spot["BTCUSDT"]
        for one in btc[:12]:
            one["quote_volume"] = "100"
        for one in btc[12:24]:
            one["quote_volume"] = "200"
            one["taker_buy_quote_volume"] = "120"
        btc[24]["quote_volume"] = "149"
        btc[24]["taker_buy_quote_volume"] = "89.4"
        btc[24]["volume"] = "999999"
        btc[24]["taker_buy_base_volume"] = "0"
        self.assertNotEqual(generate_signals(spot)["N5"][24 * HOUR]["symbol"], "BTCUSDT")
        btc[24]["quote_volume"] = "150"
        btc[24]["taker_buy_quote_volume"] = "90"
        self.assertEqual(generate_signals(spot)["N5"][24 * HOUR]["symbol"], "BTCUSDT")

    def test_n5_gap_and_invalid_data(self):
        spot = fixture()
        spot["BTCUSDT"].pop(7)
        self.assertNotEqual(generate_signals(spot)["N5"][24 * HOUR]["symbol"], "BTCUSDT")
        spot = fixture()
        spot["BTCUSDT"][-1]["quote_volume"] = "0"
        self.assertNotEqual(generate_signals(spot)["N5"][24 * HOUR]["symbol"], "BTCUSDT")
        spot = fixture()
        spot["BTCUSDT"][-1]["taker_buy_quote_volume"] = "NaN"
        self.assertNotEqual(generate_signals(spot)["N5"][24 * HOUR]["symbol"], "BTCUSDT")
        spot = fixture()
        spot["BTCUSDT"].append(copy.deepcopy(spot["BTCUSDT"][-1]))
        self.assertNotEqual(generate_signals(spot)["N5"][24 * HOUR]["symbol"], "BTCUSDT")

    def test_n6_follower_priority_and_missing_bar(self):
        spot = leader_fixture()
        self.assertEqual(generate_signals(spot)["N6"][24 * HOUR]["symbol"], "ETHUSDT")
        spot["ETHUSDT"][-1]["close"] = "100.21"
        spot["ETHUSDT"][-1]["high"] = "100.21"
        self.assertEqual(generate_signals(spot)["N6"][24 * HOUR]["symbol"], "SOLUSDT")
        spot["SOLUSDT"].pop()
        self.assertNotIn(24 * HOUR, generate_signals(spot)["N6"])

    def test_prefix_and_future_perturbation(self):
        spot = leader_fixture()
        baseline = generate_signals(spot)
        later = copy.deepcopy(spot)
        for asset in later:
            later[asset].extend([bar(25, "100", "1"), bar(26, "100", "1000")])
        self.assertEqual(
            {family: {t: signal for t, signal in signals.items() if t <= 24 * HOUR}
             for family, signals in generate_signals(later).items()}, baseline
        )
        later["ETHUSDT"][-1]["close"] = "5"
        later["ETHUSDT"][-1]["low"] = "5"
        self.assertEqual(
            {family: {t: signal for t, signal in signals.items() if t <= 24 * HOUR}
             for family, signals in generate_signals(later).items()}, baseline
        )

    def test_no_backward_or_short_branch(self):
        spot = leader_fixture()
        spot["BTCUSDT"][-1]["close"] = "99.25"
        spot["BTCUSDT"][-1]["low"] = "99.25"
        self.assertNotIn(24 * HOUR, generate_signals(spot)["N6"])


if __name__ == "__main__":
    unittest.main()
