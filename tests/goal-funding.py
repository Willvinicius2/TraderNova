"""Causal, accounting and risk fixtures for the frozen N2 engine."""

import importlib.util
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location("goal_funding", Path("scripts/goal_funding.py"))
ENGINE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENGINE)
H = ENGINE.HOUR


def bar(open_price=100.0, low=None, high=None):
    return {"open": open_price, "high": high if high is not None else open_price,
            "low": low if low is not None else open_price, "close": open_price}


def event(t, rate="0.0001", mark="100"):
    return {"symbol": "BTCUSDT", "fundingTime": t, "fundingRate": rate,
            "markPrice": mark, "funding_interval_hours": 8}


class FundingTests(unittest.TestCase):
    def test_21_events_do_not_need_168_hour_span_and_future_is_excluded(self):
        bars = {t * H: bar() for t in range(169)}
        past = [event(t * H) for t in range(0, 161, 8)]
        decision = 168 * H
        self.assertEqual(len(past), 21)
        self.assertTrue(ENGINE.eligible(decision, bars, bars, bars, past, [e["fundingTime"] for e in past]))
        future = past + [event(decision, "-0.5")]
        self.assertTrue(ENGINE.eligible(decision, bars, bars, bars, future, [e["fundingTime"] for e in future]))
        missing = dict(bars)
        del missing[47 * H]
        self.assertFalse(ENGINE.eligible(decision, missing, bars, bars, past, [e["fundingTime"] for e in past]))
        past[0]["fundingRate"] = "0.0000"
        self.assertFalse(ENGINE.eligible(decision, bars, bars, bars, past, [e["fundingTime"] for e in past]))

    def test_equal_quantity_and_both_legs_costed(self):
        base, stress = ENGINE.costs("base"), ENGINE.costs("stress")
        p = ENGINE.enter(100_000, 0, 100, 100, base)
        self.assertAlmostEqual(p["qty"], 450)
        self.assertGreater(p["cash"], 0)
        final, record = ENGINE.close(p, H, 100, 100, base, "test")
        self.assertLess(final, 100_000)
        self.assertAlmostEqual(record["pnl"], final - 100_000)
        q = ENGINE.enter(100_000, 0, 100, 100, stress)
        stressed, _ = ENGINE.close(q, H, 100, 100, stress, "test")
        self.assertLess(stressed, final)

    def test_funding_exact_bound_and_timing(self):
        base = ENGINE.costs("base")
        p = ENGINE.enter(100_000, 0, 100, 100, base)
        self.assertEqual(ENGINE.funding_mark(event(H, mark=""), bar(low=97, high=104), bar())[0], 97)
        self.assertEqual(ENGINE.funding_mark(event(H, "-0.0001", ""), bar(low=97, high=104), bar())[0], 104)
        self.assertEqual(ENGINE.funding_mark(event(H, mark="101"), bar(low=97, high=104), bar())[0], 101)
        before = p["cash"]
        ENGINE.apply_funding(p, event(1, "0.0001", "101"), bar(), bar(), True, False)
        self.assertEqual(p["cash"], before)
        self.assertIn("entry-funding-timing", p["uncertain"])
        ENGINE.apply_funding(p, event(H, "-0.0001", "101"), bar(), bar(), False, False)
        self.assertAlmostEqual(p["cash"] - before, -p["qty"] * 101 * 0.0001)
        before = p["cash"]
        ENGINE.apply_funding(p, event(2 * H, "0.0001", "101"), bar(), bar(), False, True)
        self.assertEqual(p["cash"], before)

    def test_margin_and_intrabar_exit_at_next_observed_open(self):
        base = ENGINE.costs("base")
        p = ENGINE.enter(100_000, 0, 100, 100, base)
        _, breach = ENGINE.risk_bound(p, bar(low=90), bar(), bar(), base)
        self.assertTrue(breach)
        _, breach = ENGINE.risk_bound(p, bar(), bar(high=250), bar(high=250), base)
        self.assertTrue(breach)
        spot = {t * H: bar() for t in range(171)}
        perp = {t * H: bar() for t in range(171)}
        mark = {t * H: bar() for t in range(171)}
        spot[169 * H] = bar(low=90)
        spot[170 * H] = bar(open_price=95)
        past = [event(t * H) for t in range(0, 161, 8)]
        result = ENGINE.simulate(0, 170 * H, "base", spot, perp, mark, past)
        self.assertEqual(result["trades"], 1)
        trade = result["tradeRecords"][0]
        self.assertEqual(trade["entry"], 168 * H)
        self.assertEqual(trade["exit"], 170 * H)
        self.assertEqual(trade["reason"], "intrabar-risk-next-open")
        self.assertLess(trade["pnl"], 0)

    def test_gap_exits_first_joint_open_and_flags_uncertainty(self):
        spot = {t * H: bar() for t in range(172)}
        perp = {t * H: bar() for t in range(172)}
        mark = {t * H: bar() for t in range(172)}
        del mark[169 * H]
        past = [event(t * H) for t in range(0, 161, 8)]
        result = ENGINE.simulate(0, 170 * H, "base", spot, perp, mark, past)
        self.assertEqual(result["trades"], 1)
        trade = result["tradeRecords"][0]
        self.assertEqual(trade["exit"], 170 * H)
        self.assertEqual(trade["reason"], "data-gap")
        self.assertIn("active-H1-data-gap", trade["uncertain"])

    def test_missing_joint_open_at_window_boundary_cannot_report_old_equity(self):
        spot = {t * H: bar() for t in range(170)}
        perp = dict(spot)
        mark = dict(spot)
        del mark[169 * H]
        past = [event(t * H) for t in range(0, 161, 8)]
        result = ENGINE.simulate(0, 169 * H, "base", spot, perp, mark, past)
        self.assertEqual(result["trades"], 0)
        self.assertTrue(result["unclosedPosition"])
        self.assertIsNone(result["netPct"])
        self.assertIsNone(result["profitFactor"])
        self.assertFalse(result["capitalReconciled"])
        self.assertIn("unclosed-at-window-boundary", result["uncertaintyFlags"])

    def test_capital_reconciles_with_closed_trade_cash_flows(self):
        spot = {t * H: bar() for t in range(171)}
        perp = dict(spot)
        mark = dict(spot)
        past = [event(t * H) for t in range(0, 161, 8)]
        result = ENGINE.simulate(0, 170 * H, "base", spot, perp, mark, past)
        self.assertEqual(result["trades"], 1)
        self.assertFalse(result["unclosedPosition"])
        self.assertTrue(result["capitalReconciled"])
        self.assertAlmostEqual(result["capitalReconciliationError"], 0, places=6)
        self.assertAlmostEqual(result["netPct"], result["tradeRecords"][0]["pnl"] / 100_000 * 100)

    def test_drawdown_uses_favorable_high_before_adverse_low(self):
        spot = {t * H: bar() for t in range(171)}
        perp = {t * H: bar() for t in range(171)}
        mark = {t * H: bar() for t in range(171)}
        spot[169 * H] = bar(high=120, low=90)
        perp[169 * H] = bar(high=110, low=80)
        mark[169 * H] = bar(high=110, low=80)
        past = [event(t * H) for t in range(0, 161, 8)]
        result = ENGINE.simulate(0, 170 * H, "base", spot, perp, mark, past)
        p = ENGINE.enter(100_000, 168 * H, 100, 100, ENGINE.costs("base"))
        high, low = ENGINE.intrabar_equity_envelope(
            p, spot[169 * H], perp[169 * H], mark[169 * H], ENGINE.costs("base"), p["cash"], 0, 0)
        self.assertGreater(high, 100_000)
        self.assertLess(low, 100_000)
        self.assertGreaterEqual(result["maxConservativeDrawdownPct"], 100 * (high - low) / high - 1e-9)

    def test_gate_blocks_stress_sample_account_breach_and_reconciliation(self):
        passing = {"trades": 100, "netPct": 1, "profitFactor": 1.3,
                   "maxConservativeDrawdownPct": 5, "maxConservativeDailyLossPct": 1,
                   "accountBreach": False, "unclosedPosition": False,
                   "capitalReconciled": True, "intrabarEnvelopeComplete": True,
                   "uncertaintyFlags": []}
        self.assertTrue(ENGINE.development_gate(passing, passing))
        stress = dict(passing, trades=99)
        self.assertFalse(ENGINE.development_gate(passing, stress))
        self.assertFalse(ENGINE.development_gate(dict(passing, accountBreach=True), passing))
        self.assertFalse(ENGINE.development_gate(passing, dict(passing, capitalReconciled=False)))

    def test_funding_debit_before_credit_envelope_and_breach_detection(self):
        config = ENGINE.costs("base")
        p = ENGINE.enter(100_000, 0, 100, 100, config)
        high, low = ENGINE.intrabar_equity_envelope(
            p, bar(), bar(), bar(), config, p["cash"], 100, -50)
        self.assertAlmostEqual(high - low, 150)
        spot = {t * H: bar() for t in range(171)}
        perp = {t * H: bar() for t in range(171)}
        mark = {t * H: bar() for t in range(171)}
        spot[169 * H] = bar(low=70)
        past = [event(t * H) for t in range(0, 161, 8)]
        result = ENGINE.simulate(0, 170 * H, "base", spot, perp, mark, past)
        self.assertTrue(result["accountBreach"])
        self.assertFalse(ENGINE.development_gate(result, result))


if __name__ == "__main__":
    unittest.main()
