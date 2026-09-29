"""Synthetic causal fixtures for N10 sample counting; no historical results."""

import importlib.util
import math
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location("goal_dated_sample", Path("scripts/goal_dated_sample.py"))
ENGINE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENGINE)
H, D = ENGINE.HOUR, ENGINE.DAY


def bar(close=100.0, open_price=None):
    opening = close if open_price is None else open_price
    return {"open": opening, "high": max(opening, close),
            "low": min(opening, close), "close": close}


class DatedSampleTests(unittest.TestCase):
    def test_nearest_expiry_inclusive_21_and_60_days(self):
        expiries = {"far": 60 * D, "near": 21 * D, "too_soon": 20 * D}
        self.assertEqual(ENGINE.nearest_contract(0, expiries), "near")
        self.assertEqual(ENGINE.nearest_contract(H, {"far": 60 * D, "too_soon": 20 * D}), "far")
        self.assertIsNone(ENGINE.nearest_contract(0, {"too_soon": 20 * D, "too_far": 61 * D}))

    def test_strict_entry_thresholds_and_inclusive_exit(self):
        self.assertFalse(ENGINE.qualifying_signal(100, 101.5, 36.5))  # annualized = 15%
        self.assertFalse(ENGINE.qualifying_signal(100, 101.14, 21))  # gain = 0.76%
        self.assertTrue(ENGINE.qualifying_signal(100, 101.15, 21))
        self.assertFalse(ENGINE.qualifying_signal(100, 101.15, 20.99))
        self.assertTrue(ENGINE.exit_basis_reached(100, 100.5, 36.5))  # annualized = 5%

    def test_closed_hour_entry_exit_and_no_same_open_reentry(self):
        spot = {t * H: bar() for t in range(-1, 3)}
        future = {-H: bar(102), 0: bar(100.1, 102), H: bar(102), 2 * H: bar(100.1, 102)}
        mark = {t: bar() for t in spot}
        out = ENGINE.sample(0, 3 * H, spot, {"C": future}, {"C": mark}, {"C": 40 * D})
        self.assertEqual(out["cleanClosedEpisodes"], 1)
        self.assertEqual(out["openAtBoundary"], 1)
        self.assertEqual(out["episodes"][0]["entryOpenMs"], 0)
        self.assertEqual(out["episodes"][0]["exitOpenMs"], H)
        self.assertEqual(out["episodes"][1]["entryOpenMs"], 2 * H)
        self.assertEqual(out["qualifyingFlatDecisions"], 2)

    def test_missing_next_joint_open_pends_then_fills_uncertain(self):
        spot = {-H: bar(), 0: bar(), H: bar()}
        future = {-H: bar(102), 0: bar(102), H: bar(102)}
        mark = {-H: bar(), H: bar()}  # no mark at the causal entry open 0
        out = ENGINE.sample(0, 2 * H, spot, {"C": future}, {"C": mark}, {"C": 40 * D})
        self.assertEqual(out["signalWithoutJointOpen"], 1)
        self.assertEqual(out["cleanClosedEpisodes"], 0)
        self.assertEqual(out["openAtBoundary"], 1)
        self.assertEqual(out["episodes"][0]["entryOpenMs"], H)
        self.assertIn("delayed-entry-open", out["episodes"][0]["uncertain"])
        self.assertEqual(out["pendingAtBoundary"], 0)

    def test_current_hour_future_high_low_close_cannot_change_entry_or_exit_open(self):
        spot = {-H: bar(), 0: bar(), H: bar()}
        future = {-H: bar(102), 0: bar(100.1, 102), H: bar()}
        mark = {-H: bar(), 0: bar(), H: bar()}
        baseline_entry = ENGINE.sample(0, H, spot, {"C": future}, {"C": mark}, {"C": 40 * D})
        changed_future = dict(future)
        changed_future[0] = {"open": 102, "high": math.nan, "low": math.inf, "close": math.nan}
        changed_mark = dict(mark)
        changed_mark[0] = {"open": 100, "high": math.nan, "low": math.nan, "close": math.nan}
        changed_entry = ENGINE.sample(0, H, spot, {"C": changed_future}, {"C": changed_mark}, {"C": 40 * D})
        self.assertEqual(baseline_entry["episodes"][0]["entryOpenMs"], 0)
        self.assertEqual(changed_entry["episodes"][0]["entryOpenMs"], 0)
        self.assertFalse(ENGINE.valid_bar(changed_future[0]))
        self.assertTrue(ENGINE.valid_open(changed_future[0]))
        self.assertFalse(ENGINE.valid_open({"open": math.inf}))

        changed_exit_bar = dict(future)
        changed_exit_bar[H] = {"open": 100.1, "high": math.nan, "low": math.inf, "close": math.nan}
        changed_mark_exit = dict(mark)
        changed_mark_exit[H] = {"open": 100, "high": math.nan, "low": math.nan, "close": math.nan}
        baseline_exit = ENGINE.sample(0, 2 * H, spot, {"C": future}, {"C": mark}, {"C": 40 * D})
        changed_exit = ENGINE.sample(0, 2 * H, spot, {"C": changed_exit_bar}, {"C": changed_mark_exit}, {"C": 40 * D})
        self.assertEqual(baseline_exit["episodes"][0]["exitOpenMs"], H)
        self.assertEqual(changed_exit["episodes"][0]["exitOpenMs"], H)

    def test_pending_signal_is_not_promoted_if_joint_open_stays_missing_until_d_minus_7(self):
        expiry = 21 * D
        end = expiry - 7 * D + H
        spot = {t: bar() for t in range(-H, end, H)}
        future = {t: bar(102) for t in range(-H, end, H)}
        mark = {-H: bar()}  # signal is known, but no subsequent joint open
        out = ENGINE.sample(0, end, spot, {"C": future}, {"C": mark}, {"C": expiry})
        self.assertEqual(out["signalWithoutJointOpen"], 1)
        self.assertEqual(out["cancelledPendingEntries"], 1)
        self.assertEqual(out["cleanClosedEpisodes"], 0)
        self.assertEqual(out["uncertainClosedEpisodes"], 0)
        self.assertEqual(out["pendingAtBoundary"], 0)

    def test_calendar_exit_needs_no_fresh_close_and_no_later_window_read(self):
        end = 33 * D + H
        spot = {t: bar() for t in range(-H, end, H)}
        future = {t: bar(102) for t in range(-H, end, H)}
        mark = {t: bar() for t in range(-H, end, H)}
        deadline = 33 * D
        del future[deadline - H]  # the D-7 rule is known without that close
        first = ENGINE.sample(0, end, spot, {"C": future}, {"C": mark}, {"C": 40 * D})
        self.assertEqual(first["episodes"][0]["exitOpenMs"], deadline)
        self.assertEqual(first["episodes"][0]["reason"], "D-minus-7")
        spot[end], future[end], mark[end] = bar(1), bar(1000), bar(1000)
        later = ENGINE.sample(0, end, spot, {"C": future}, {"C": mark}, {"C": 40 * D})
        self.assertEqual(first, later)


if __name__ == "__main__":
    unittest.main()
