"""Adversarial synthetic tests for pure N21 causal feature gating."""
import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("n21_features", ROOT / "scripts" / "n21_signal_features.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def state(ts, mid, bid, ask, seq, levels, lower="99.8", utc=True, age="0.2"):
    return {"timestamp": ts, "mid": mid, "bid": bid, "ask": ask,
            "sequence_marker": seq, "bid_levels": levels,
            "known_bid_lower_bound": lower, "source": "binance_spot_l2",
            "connection_id": "conn-1", "utc_verified": utc,
            "event_age_s": age}


def trio():
    before = state("2026-09-30T00:00:00Z", "100", "99.99", "100.01", 100,
                   [["99.99", "10"], ["99.95", "5"]])
    current = state("2026-09-30T00:00:01Z", "99.95", "99.94", "99.96", 105,
                    [["99.94", "8"]])
    confirm = state("2026-09-30T00:00:06Z", "99.96", "99.95", "99.97", 200,
                    [["99.95", "18.75"]])
    confirm["min_mid_between"] = "99.95"
    return before, current, confirm


def evaluate(before, current, confirm, *, min_mid_between=None, **kwargs):
    # Minimum of the complete interval is a caller-prepared field, not a future array.
    confirm = copy.deepcopy(confirm)
    if min_mid_between is not None:
        confirm['min_mid_between'] = min_mid_between
    return mod.evaluate_n21(before, current, confirm, **kwargs)


class N21FeatureTests(unittest.TestCase):
    def test_signal_requires_strict_causal_criteria_and_never_approves(self):
        result = evaluate(*trio(), continuity_verified=True)
        self.assertEqual(result["status"], "hypothesis_signal")
        self.assertEqual(result["decision_at"], "2026-09-30T00:00:06Z")
        self.assertEqual(result["source"], "Binance_aux")
        self.assertFalse(result["validated"])
        self.assertFalse(result["execution"])
        self.assertFalse(result["externally_attested"])
        self.assertTrue(result['requires_verified_adapter'])
        self.assertTrue(result["cooldown_not_enforced"])

    def test_fixed_absolute_band_rejects_recomposition_outside_band(self):
        before, current, confirm = trio()
        confirm["bid_levels"] = [["99.95", "1"], ["99.89", "100"]]
        result = evaluate(before, current, confirm, continuity_verified=True)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["blocked_reason"], "fixed_band_recovery_below_1_25x")

    def test_bad_utc_missing_coverage_or_sequence_gap_blocks(self):
        before, current, confirm = trio()
        current["utc_verified"] = False
        self.assertEqual(evaluate(before, current, confirm, continuity_verified=True)["status"], "blocked")
        before, current, confirm = trio()
        confirm["known_bid_lower_bound"] = "99.91"
        self.assertEqual(evaluate(before, current, confirm, continuity_verified=True)["blocked_reason"], "band_not_fully_covered")
        before, current, confirm = trio()
        self.assertEqual(evaluate(before, current, confirm, continuity_verified=False)["blocked_reason"], "continuity_not_verified_by_caller")

    def test_continuous_minute_and_interval_cannot_be_looked_ahead(self):
        before, current, confirm = trio()
        confirm["min_mid_between"] = "99.94"
        result = evaluate(before, current, confirm, continuity_verified=True)
        self.assertEqual(result["blocked_reason"], "new_low_during_confirmation")
        before, current, confirm = trio()
        current["timestamp"] = "2026-09-30T00:00:02Z"
        self.assertEqual(evaluate(before, current, confirm, continuity_verified=True)["blocked_reason"], "shock_interval_not_exactly_1s")
        before, current, confirm = trio()
        confirm["sequence_marker"] = 99
        self.assertEqual(evaluate(before, current, confirm, continuity_verified=True)["blocked_reason"], "sequence_gap_or_nonmonotonic")

    def test_crossed_quotes_source_mismatch_and_nonfinite_inputs_block(self):
        before, current, confirm = trio()
        current["ask"] = "99.93"
        self.assertEqual(evaluate(before, current, confirm, continuity_verified=True)["blocked_reason"], "crossed_or_invalid_quote")
        before, current, confirm = trio()
        confirm["connection_id"] = "other"
        self.assertEqual(evaluate(before, current, confirm, continuity_verified=True)["blocked_reason"], "source_or_connection_mismatch")
        before, current, confirm = trio()
        current["mid"] = "Infinity"
        self.assertEqual(evaluate(before, current, confirm, continuity_verified=True)["blocked_reason"], "nonfinite_mid")
        self.assertEqual(evaluate([before, current], current, confirm, continuity_verified=True)["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
