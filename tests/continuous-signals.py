import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from datetime import datetime, timezone

from continuous_signals import USDC, WETH, n21_liquidity_resilience, n22_aave_credit_stress


def stamp(s): return f"2026-09-30T{s}:00Z"


class SignalTests(unittest.TestCase):
    def setUp(self):
        self.n21 = {
            "decision_at": "2026-09-30T03:04:06Z", "shock_start_at": "2026-09-30T03:04:00Z",
            "shock_end_at": "2026-09-30T03:04:01Z", "confirm_start_at": "2026-09-30T03:04:01Z",
            "confirm_end_at": "2026-09-30T03:04:06Z", "sequence_complete": True, "feed_age_s": 0.4,
            "mid_before": 100, "mid_after": 99.94, "best_bid_before": 99.99, "best_bid_after": 99.94,
            "event_low": 99.90, "confirm_low": 99.91, "d0": 100, "d5": 130,
            "band_low_pre": 99.90, "band_low_confirm": 99.90, "band_high_pre": 100, "band_high_confirm": 100,
        }
        for key,end in [('pre_meta',self.n21['shock_start_at']),('shock_meta',self.n21['shock_end_at']),('confirm_meta',self.n21['confirm_end_at'])]:
            self.n21[key]={'feature_end':end,'published_at':end,'received_at':end}
        self.n22 = {"decision_at": stamp("03:05"), "window_start": "2026-09-30T02:34:00Z",
                    "window_end": "2026-09-30T03:04:00Z", "finalized_block": True, "chain_id": 1,
                    "eth_return": -0.006, "eth_meta": {"published_at": "2026-09-30T03:04:00Z",
                    "received_at": "2026-09-30T03:04:01Z", "feature_end": "2026-09-30T03:04:00Z"}, "reserves": {}}
        self.n22.update(market='ethereum_core_v3',deployment_verified=True,oracle_valid=True,reorganized=False,start_block=100,end_block=200,
            atr14_prior={'value':25,'feature_end':self.n22['window_start'],'published_at':self.n22['window_start'],'received_at':self.n22['window_start']})
        for addr in (USDC, WETH):
            self.n22["reserves"][addr] = {"reserve_id": addr, "util_start": 0.50, "util_end": 0.56,
                "apy_start": 0.02, "apy_end": 0.031, "active":True,"paused":False,"frozen":False,"start_block":100,"end_block":200,
                "meta": {"published_at": "2026-09-30T03:04:00Z", "received_at": "2026-09-30T03:04:01Z",
                         "feature_end": "2026-09-30T03:04:00Z", "window_start": "2026-09-30T02:34:00Z"}}

    def test_n21_qualifies(self):
        s = n21_liquidity_resilience(self.n21)
        self.assertEqual((s["family"], s["direction"], s["horizon"]), ("N21", "long", "10 minutos"))
        self.assertAlmostEqual(s["stop"]["stop_price"], 99.8001)

    def test_n21_rejects_sequence_gap_stale_or_new_low(self):
        for patch in ({"sequence_complete": False}, {"feed_age_s": 1.01}, {"confirm_low": 99.89}):
            self.assertIsNone(n21_liquidity_resilience(self.n21 | patch))

    def test_n21_rejects_bool_nan_or_naive_timestamp(self):
        for patch in ({"d0": True}, {"d5": float("nan")}, {"shock_start_at": "2026-09-30T03:04:00"}):
            self.assertIsNone(n21_liquidity_resilience(self.n21 | patch))

    def test_n21_rejects_shifted_band_stale_decision_and_future_observation(self):
        for patch in ({'band_high_confirm':99.99},{'decision_at':stamp('03:05')},{'confirm_meta':self.n21['confirm_meta']|{'received_at':stamp('03:05')}}):
            self.assertIsNone(n21_liquidity_resilience(self.n21|patch))

    def test_n22_qualifies(self):
        s = n22_aave_credit_stress(self.n22)
        self.assertEqual((s["family"], s["direction"], s["horizon"]), ("N22", "short", "6 horas"))

    def test_n22_requires_both_reserves_finality_and_thresholds(self):
        self.assertIsNone(n22_aave_credit_stress(self.n22 | {"finalized_block": False}))
        bad = {**self.n22, "reserves": {k: dict(v) for k, v in self.n22["reserves"].items()}}
        bad["reserves"][WETH]["util_end"] = 0.54
        self.assertIsNone(n22_aave_credit_stress(bad))
        bad = {**self.n22, "reserves": {k: dict(v) for k, v in self.n22["reserves"].items()}}
        bad["reserves"][USDC]["reserve_id"] = WETH
        self.assertIsNone(n22_aave_credit_stress(bad))

    def test_n22_rejects_future_and_boolean_features(self):
        bad = {**self.n22, "eth_return": True}
        self.assertIsNone(n22_aave_credit_stress(bad))

    def test_n22_rejects_missing_atr_invalid_oracle_and_unsynchronized_blocks(self):
        for patch in ({'atr14_prior':{}},{'oracle_valid':False},{'reorganized':True}):
            self.assertIsNone(n22_aave_credit_stress(self.n22|patch))
        bad={**self.n22,'reserves':{k:dict(v) for k,v in self.n22['reserves'].items()}}
        bad['reserves'][USDC]['end_block']=199
        self.assertIsNone(n22_aave_credit_stress(bad))
        bad = {**self.n22, "decision_at": "2026-09-30T02:59:00Z"}
        self.assertIsNone(n22_aave_credit_stress(bad))


if __name__ == "__main__": unittest.main()

