"""Pure preregistered N21/N22 signal conditions. No feeds, fills, or PnL."""
from datetime import timedelta
import math

from goal_five_signals import _time, _feature

USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _causal(meta, decision):
    try:
        p, r, e = (_time(meta[k]) for k in ("published_at", "received_at", "feature_end"))
        return e <= p <= r <= decision
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def n21_liquidity_resilience(d):
    """Input timestamps are ISO-8601 with offsets; bands must be fixed pre-shock."""
    try:
        decision = _time(d["decision_at"])
        shock_start, shock_end = _time(d["shock_start_at"]), _time(d["shock_end_at"])
        confirm_start, confirm_end = _time(d["confirm_start_at"]), _time(d["confirm_end_at"])
        if (shock_end - shock_start != timedelta(seconds=1)
                or confirm_end - confirm_start != timedelta(seconds=5)
                or confirm_start != shock_end or not 0 <= (decision-confirm_end).total_seconds() <= 1):
            return None
        for name, end_at in (("pre_meta",shock_start),("shock_meta",shock_end),("confirm_meta",confirm_end)):
            if not _causal(d.get(name,{}),decision) or _time(d[name]["feature_end"]) != end_at:
                return None
        if d.get("sequence_complete") is not True or not _num(d.get("feed_age_s")) or not 0 <= d["feed_age_s"] <= 1:
            return None
        numeric = ("mid_before", "mid_after", "best_bid_before", "best_bid_after",
                   "event_low", "confirm_low", "d0", "d5", "band_low_pre", "band_low_confirm", "band_high_pre", "band_high_confirm")
        if any(not _num(d.get(k)) for k in numeric):
            return None
        if min(d["mid_before"], d["mid_after"], d["best_bid_before"], d["best_bid_after"],
               d["event_low"], d["confirm_low"], d["d0"], d["band_low_pre"]) <= 0 or d["d5"] < 0:
            return None
        if (d["band_low_pre"] != d["band_low_confirm"] or d["band_high_pre"] != d["band_high_confirm"]
                or not math.isclose(d["band_high_pre"],d["mid_before"],rel_tol=1e-12)
                or not math.isclose(d["band_low_pre"],d["mid_before"]*.999,rel_tol=1e-12)
                or d["d5"] < 1.25 * d["d0"]):
            return None
        if d["mid_after"] / d["mid_before"] - 1 > -0.0005 or d["best_bid_after"] >= d["best_bid_before"]:
            return None
        if d["confirm_low"] < d["event_low"]:
            return None
        return {
            "family": "N21", "direction": "long", "decision_at": d["decision_at"],
            "entry_after": d["decision_at"], "horizon": "10 minutos",
            "stop": {"stop_price": d["event_low"] * 0.999},
            "cooldown": "30 minutos", "validated": False,
        }
    except (KeyError, TypeError, ValueError, OverflowError):
        return None


def n22_aave_credit_stress(d):
    """Input must be supervisor-verified finalized Ethereum-mainnet reserve samples."""
    try:
        decision = _time(d["decision_at"])
        start, end = _time(d["window_start"]), _time(d["window_end"])
        if end - start != timedelta(minutes=30) or end > decision:
            return None
        if d.get("finalized_block") is not True or not isinstance(d.get("chain_id"), int) or isinstance(d.get("chain_id"), bool) or d["chain_id"] != 1:
            return None
        if d.get("market") != "ethereum_core_v3" or d.get("deployment_verified") is not True or d.get("oracle_valid") is not True or d.get("reorganized") is not False:
            return None
        for key in ("start_block","end_block"):
            if not isinstance(d.get(key),int) or isinstance(d[key],bool) or d[key]<0:
                return None
        if d["end_block"] <= d["start_block"] or not _feature(d,"atr14_prior",True,d["window_start"]):
            return None
        if not _num(d.get("eth_return")) or d["eth_return"] > -0.005:
            return None
        if not _causal(d.get("eth_meta", {}), decision) or _time(d["eth_meta"]["feature_end"]) != end:
            return None
        reserves = d.get("reserves")
        if not isinstance(reserves, dict) or set(reserves) != {USDC, WETH}:
            return None
        values = {}
        for address in (USDC, WETH):
            r = reserves[address]
            if not isinstance(r, dict) or r.get("reserve_id", "").lower() != address:
                return None
            if r.get("active") is not True or r.get("paused") is not False or r.get("frozen") is not False or r.get("start_block") != d["start_block"] or r.get("end_block") != d["end_block"]:
                return None
            if not _causal(r.get("meta", {}), decision) or _time(r["meta"]["feature_end"]) != end:
                return None
            for k in ("util_start", "util_end", "apy_start", "apy_end"):
                if not _num(r.get(k)) or not 0 <= r[k] <= 1:
                    return None
            if r["meta"].get("window_start") != d["window_start"]:
                return None
            values[address] = r
        if any(values[a]["util_end"] - values[a]["util_start"] < 0.05 for a in (USDC, WETH)):
            return None
        if max(values[a]["apy_end"] - values[a]["apy_start"] for a in (USDC, WETH)) < 0.01:
            return None
        return {
            "family": "N22", "direction": "short", "decision_at": d["decision_at"],
            "entry_after": d["decision_at"], "horizon": "6 horas",
            "stop": {"distance": d["atr14_prior"]["value"], "unit": "preço"},
            "cooldown": "6 horas", "validated": False,
        }
    except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
        return None



