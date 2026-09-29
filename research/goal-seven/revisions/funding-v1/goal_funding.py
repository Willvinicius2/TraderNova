"""Frozen N2 BTC spot + USD-M perpetual funding-carry research engine.

No exchange credentials or orders. Run tests and write the freeze snapshot before
using ``--development``. Later windows require a development gate pass.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import zipfile


HOUR = 3_600_000
DAY = 24 * HOUR
ROOT = Path("research/cache/funding-goal")
SPOT = Path("research/cache/v3/BTCUSDT-1h.json")
MANIFEST = Path("research/goal-seven/funding-data-manifest.json")
PROTOCOL = Path("research/goal-seven/funding-protocol.json")
FREEZE = Path("research/goal-seven/funding-freeze.json")
RESULTS = Path("research/goal-seven/funding-results.json")
DETAILS = Path("research/cache/goal-seven")
UTC = dt.timezone.utc


def epoch(date: str) -> int:
    return int(dt.datetime.fromisoformat(date).replace(tzinfo=UTC).timestamp() * 1000)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_sources() -> tuple[dict, dict, dict, list[dict]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected_spot = next(p["sha256"] for p in json.loads(Path("research/cache/v3/manifest.json").read_text(encoding="utf-8"))["series"] if p["file"] == "BTCUSDT-1h.json")
    if sha(SPOT) != expected_spot:
        raise ValueError("spot cache SHA mismatch")
    spot_rows = json.loads(SPOT.read_text(encoding="utf-8"))
    spot = {int(row["time"]): {key: float(row[key]) for key in ("open", "high", "low", "close")} for row in spot_rows}
    series = {}
    for kind in ("perp_h1", "mark_h1"):
        rows = {}
        listed = [item for item in manifest["files"] if item["kind"] == kind and item["symbol"] == "BTCUSDT"]
        if len(listed) != 56:
            raise ValueError(f"incomplete {kind} manifest")
        for item in listed:
            path = Path(item["cachePath"])
            if item["status"] != "verified" or sha(path) != item["sha256"]:
                raise ValueError(f"unverified {path}")
            with zipfile.ZipFile(path) as archive:
                with archive.open(archive.namelist()[0]) as source:
                    for values in csv.reader(io.TextIOWrapper(source, encoding="utf-8-sig", newline="")):
                        if not values or values[0] == "open_time":
                            continue
                        timestamp = int(values[0])
                        if timestamp in rows:
                            raise ValueError(f"duplicate {kind} H1 {timestamp}")
                        rows[timestamp] = dict(zip(("open", "high", "low", "close"), map(float, values[1:5])))
        series[kind] = rows
    funding = []
    api = manifest["apiFunding"]["BTCUSDT"]
    if not api["matchedMonthlyArchive"]:
        raise ValueError("REST funding disagrees with official monthly archives")
    for page in api["pages"]:
        path = Path(page["cachePath"])
        if sha(path) != page["sha256"]:
            raise ValueError(f"REST page SHA mismatch: {path}")
        funding.extend(json.loads(path.read_text(encoding="utf-8")))
    if len(funding) != api["events"] or len({int(e["fundingTime"]) for e in funding}) != len(funding):
        raise ValueError("funding event count or uniqueness mismatch")
    intervals = {}
    for item in manifest["files"]:
        if item["kind"] != "funding" or item["symbol"] != "BTCUSDT":
            continue
        path = Path(item["cachePath"])
        if item["status"] != "verified" or sha(path) != item["sha256"]:
            raise ValueError(f"unverified funding archive {path}")
        with zipfile.ZipFile(path) as archive:
            with archive.open(archive.namelist()[0]) as source:
                for row in csv.reader(io.TextIOWrapper(source, encoding="utf-8-sig", newline="")):
                    if row and row[0] != "calc_time":
                        intervals[int(row[0])] = (float(row[1]), Decimal(row[2]))
    for event in funding:
        interval, monthly_rate = intervals[int(event["fundingTime"])]
        if Decimal(event["fundingRate"]) != monthly_rate:
            raise ValueError("REST/monthly funding rate mismatch")
        event["funding_interval_hours"] = interval
    return spot, series["perp_h1"], series["mark_h1"], funding


def eligible(decision_open: int, spot: dict, perp: dict, mark: dict, events: list[dict], times: list[int]) -> bool:
    """Use only observations strictly before the proposed entry open."""
    if decision_open not in spot or decision_open not in perp or decision_open not in mark:
        return False
    for t in range(decision_open - 7 * DAY, decision_open, HOUR):
        if t not in spot or t not in perp or t not in mark:
            return False
    index = bisect.bisect_left(times, decision_open)
    if index < 21:
        return False
    past = events[index - 21:index]
    if decision_open - int(past[-1]["fundingTime"]) > (float(past[-1]["funding_interval_hours"]) + 1) * HOUR:
        return False
    for left, right in zip(past, past[1:]):
        elapsed = int(right["fundingTime"]) - int(left["fundingTime"])
        announced = float(right["funding_interval_hours"]) * HOUR
        if elapsed <= 0 or abs(elapsed - announced) > 60_000:
            return False
    return sum(Decimal(event["fundingRate"]) for event in past) / 21 >= Decimal("0.0001")


def costs(scenario: str) -> dict:
    config = json.loads(PROTOCOL.read_text(encoding="utf-8"))["costsBpsPerSide"][scenario]
    return {key: value / 10_000 for key, value in config.items()}


def enter(equity: float, timestamp: int, spot_open: float, perp_open: float, config: dict) -> dict:
    qty = 0.45 * equity / spot_open
    spot_fill = spot_open * (1 + config["spotAdverseSlippage"])
    perp_fill = perp_open * (1 - config["perpAdverseSlippage"])
    cash = equity - qty * spot_fill * (1 + config["spotFee"]) - qty * perp_fill * config["perpFee"]
    return {"entry": timestamp, "entryEquity": equity, "qty": qty, "spotFill": spot_fill,
            "perpFill": perp_fill, "cash": cash, "funding": 0.0, "fundingEvents": 0,
            "nonpositiveStreak": 0, "uncertain": [], "pendingExit": None}


def close(position: dict, timestamp: int, spot_open: float, perp_open: float, config: dict, reason: str) -> tuple[float, dict]:
    qty = position["qty"]
    spot_fill = spot_open * (1 - config["spotAdverseSlippage"])
    perp_fill = perp_open * (1 + config["perpAdverseSlippage"])
    equity = (position["cash"] + qty * spot_fill * (1 - config["spotFee"])
              + qty * (position["perpFill"] - perp_fill) - qty * perp_fill * config["perpFee"])
    trade = {"entry": position["entry"], "exit": timestamp, "reason": reason,
             "pnl": equity - position["entryEquity"], "entryEquity": position["entryEquity"],
             "exitEquity": equity, "fundingNet": position["funding"],
             "fundingEvents": position["fundingEvents"], "uncertain": sorted(set(position["uncertain"]))}
    return equity, trade


def exit_value(position: dict, spot_price: float, perp_price: float, config: dict) -> float:
    """Estimated net liquidation value, including both closing costs."""
    qty = position["qty"]
    spot_sell = spot_price * (1 - config["spotAdverseSlippage"])
    perp_cover = perp_price * (1 + config["perpAdverseSlippage"])
    return (position["cash"] + qty * spot_sell * (1 - config["spotFee"])
            + qty * (position["perpFill"] - perp_cover) - qty * perp_cover * config["perpFee"])


def risk_bound(position: dict, spot_bar: dict, perp_bar: dict, mark_bar: dict, config: dict) -> tuple[float, bool]:
    worst_mark = mark_bar["high"]
    worst_exit = max(perp_bar["high"], worst_mark)
    worst_equity = exit_value(position, spot_bar["low"], worst_exit, config)
    margin = position["cash"] + position["qty"] * (position["perpFill"] - worst_mark)
    margin_breach = margin <= 0.10 * position["qty"] * worst_mark
    return worst_equity, worst_equity <= 0.98 * position["entryEquity"] or margin_breach


def funding_mark(event: dict, mark_bar: dict | None, perp_bar: dict | None) -> tuple[float | None, bool]:
    rate = Decimal(event["fundingRate"])
    exact = event.get("markPrice")
    if exact and Decimal(exact) > 0:
        return float(exact), False
    if mark_bar is not None:
        return mark_bar["low"] if rate > 0 else mark_bar["high"], False
    # Not a certified mark bound. The trade is marked inconclusive and exited.
    return (perp_bar["high"] if perp_bar is not None and rate <= 0 else None), True


def apply_funding(position: dict, event: dict, mark_bar: dict | None, perp_bar: dict | None,
                  entry_boundary: bool, risk_bar: bool) -> None:
    rate = float(event["fundingRate"])
    price, unknown = funding_mark(event, mark_bar, perp_bar)
    if unknown:
        position["uncertain"].append("missing-event-mark-bound")
        position["pendingExit"] = position["pendingExit"] or "data-gap"
    if rate > 0 and (entry_boundary or risk_bar or price is None):
        if entry_boundary:
            position["uncertain"].append("entry-funding-timing")
        if risk_bar:
            position["uncertain"].append("risk-bar-funding-timing")
        return
    if price is None:
        return
    payment = position["qty"] * price * rate
    position["cash"] += payment
    position["funding"] += payment
    position["fundingEvents"] += 1
    position["nonpositiveStreak"] = position["nonpositiveStreak"] + 1 if rate <= 0 else 0
    if position["nonpositiveStreak"] >= 3:
        position["pendingExit"] = position["pendingExit"] or "three-nonpositive-funding"


def simulate(start: int, end: int, scenario: str, spot: dict, perp: dict,
             mark: dict, events: list[dict], initial: float = 100_000.0) -> dict:
    config = costs(scenario)
    times = [int(event["fundingTime"]) for event in events]
    by_hour: dict[int, list[dict]] = {}
    for event in events:
        by_hour.setdefault(int(event["fundingTime"]) // HOUR * HOUR, []).append(event)
    equity = initial
    position = None
    trades = []
    peak = initial
    max_dd = max_daily = 0.0
    day = None
    day_start = initial
    last_close_equity = initial
    last_exit_open = None
    for t in range(start, end + HOUR, HOUR):
        today = t // DAY
        if today != day:
            day, day_start = today, last_close_equity
        s, p, m = spot.get(t), perp.get(t), mark.get(t)
        joint = s is not None and p is not None and m is not None
        if position and not joint:
            position["uncertain"].append("active-H1-data-gap")
            position["pendingExit"] = "data-gap"
            for event in by_hour.get(t, []):
                apply_funding(position, event, m, p, False, True)
            continue
        if position and joint:
            reason = position["pendingExit"] or ("time-limit" if t >= position["entry"] + 720 * HOUR else None)
            reason = reason or ("window-end" if t >= end else None)
            open_equity = exit_value(position, s["open"], p["open"], config)
            open_margin = position["cash"] + position["qty"] * (position["perpFill"] - m["open"])
            if not reason and (open_equity <= 0.98 * position["entryEquity"]
                               or open_margin <= 0.10 * position["qty"] * m["open"]):
                reason = "risk-at-observed-open"
            if reason:
                # Exact exit-time funding cannot produce a proven credit. A
                # possible simultaneous debit is charged conservatively.
                for event in by_hour.get(t, []):
                    if int(event["fundingTime"]) == t and Decimal(event["fundingRate"]) < 0:
                        apply_funding(position, event, m, p, False, False)
                        position["uncertain"].append("exit-funding-timing")
                equity, trade = close(position, t, s["open"], p["open"], config, reason)
                trades.append(trade)
                position = None
                last_exit_open = t
                peak = max(peak, equity)
                max_dd = max(max_dd, 100 * (peak - equity) / peak)
                max_daily = max(max_daily, 100 * (day_start - equity) / day_start)
                last_close_equity = equity
        if t >= end:
            break
        if position is None and joint and last_exit_open != t and eligible(t, spot, perp, mark, events, times):
            position = enter(equity, t, s["open"], p["open"], config)
        if position is None or not joint:
            last_close_equity = equity
            continue
        pre_worst, risk = risk_bound(position, s, p, m, config)
        if risk:
            position["pendingExit"] = position["pendingExit"] or "intrabar-risk-next-open"
            position["uncertain"].append("intrabar-risk-time")
        for event in by_hour.get(t, []):
            when = int(event["fundingTime"])
            if when < position["entry"]:
                continue
            entry_boundary = when - position["entry"] <= 1000
            apply_funding(position, event, m, p, entry_boundary, risk)
        post_worst, post_risk = risk_bound(position, s, p, m, config)
        if post_risk:
            position["pendingExit"] = position["pendingExit"] or "intrabar-risk-next-open"
            position["uncertain"].append("intrabar-risk-time")
        worst = min(pre_worst, post_worst)
        peak = max(peak, exit_value(position, s["close"], p["close"], config))
        max_dd = max(max_dd, 100 * (peak - worst) / peak)
        max_daily = max(max_daily, 100 * (day_start - worst) / day_start)
        last_close_equity = exit_value(position, s["close"], p["close"], config)
    wins = sum(trade["pnl"] for trade in trades if trade["pnl"] > 0)
    losses = -sum(trade["pnl"] for trade in trades if trade["pnl"] < 0)
    uncertain = sorted({flag for trade in trades for flag in trade["uncertain"]})
    return {"scenario": scenario, "trades": len(trades), "netPct": 100 * (equity / initial - 1),
            "profitFactor": wins / losses if losses else None,
            "maxConservativeDrawdownPct": max_dd, "maxConservativeDailyLossPct": max_daily,
            "uncertaintyFlags": uncertain, "tradeRecords": trades}


def run_development() -> None:
    if not FREEZE.exists():
        raise RuntimeError("funding-freeze.json must exist before performance")
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))["hashes"]
    for name, expected in frozen.items():
        if sha(Path(name)) != expected:
            raise RuntimeError(f"frozen SHA changed: {name}")
    spot, perp, mark, funding = checked_sources()
    start, end = epoch("2022-01-01"), epoch("2025-01-01")
    outcomes = {name: simulate(start, end, name, spot, perp, mark, funding) for name in ("base", "stress")}
    DETAILS.mkdir(parents=True, exist_ok=True)
    for name, outcome in outcomes.items():
        path = DETAILS / f"funding-development-{name}-trades.json"
        path.write_text(json.dumps(outcome.pop("tradeRecords"), indent=2) + "\n", encoding="utf-8")
        outcome["tradesPath"] = path.as_posix()
    base, stress = outcomes["base"], outcomes["stress"]
    gate = (base["trades"] >= 100 and base["netPct"] > 0 and stress["netPct"] > 0
            and base["profitFactor"] is not None and base["profitFactor"] >= 1.2
            and base["maxConservativeDrawdownPct"] <= 8
            and stress["maxConservativeDrawdownPct"] <= 10
            and base["maxConservativeDailyLossPct"] <= 2
            and stress["maxConservativeDailyLossPct"] <= 3
            and not base["uncertaintyFlags"] and not stress["uncertaintyFlags"])
    result = {"family": "N2", "validated": False, "window": ["2022-01-01", "2025-01-01"],
              "developmentGatePassed": gate, "nextWindowsRun": False,
              "reason": "Development gate failed; validation and recent windows withheld" if not gate else "Development screen passed; independent approval remains unmet",
              "outcomes": outcomes, "freezeSha256": sha(FREEZE)}
    RESULTS.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--development", action="store_true")
    args = parser.parse_args()
    if args.development:
        run_development()
