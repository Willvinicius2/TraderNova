"""Causal sample-size triage for N10 BTC dated-future basis, with no PnL."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from decimal import Decimal
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile


HOUR = 3_600_000
DAY = 24 * HOUR
START = int(dt.datetime(2022, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
DEV_END = int(dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
SPOT = Path("research/cache/v3/BTCUSDT-1h.json")
DATA_MANIFEST = Path("research/goal-seven/dated-data-manifest.json")
FREEZE = Path("research/goal-seven/dated-sample-freeze.json")
RESULT = Path("research/goal-seven/dated-sample.json")
DETAIL = Path("research/cache/goal-seven/dated/sample-episodes.json")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expiry_ms(contract: str) -> int:
    date = dt.datetime.strptime(contract.rsplit("_", 1)[1], "%y%m%d").date()
    return int(dt.datetime.combine(date, dt.time(8), tzinfo=dt.timezone.utc).timestamp() * 1000)


def nearest_contract(timestamp: int, expiries: dict[str, int]) -> str | None:
    eligible = [(expiry, contract) for contract, expiry in expiries.items()
                if 21 * DAY <= expiry - timestamp <= 60 * DAY]
    return min(eligible)[1] if eligible else None


def valid_bar(bar: dict | None) -> bool:
    return (bar is not None and all(math.isfinite(bar[field]) for field in ("open", "high", "low", "close"))
            and bar["open"] > 0 and bar["close"] > 0
            and bar["low"] > 0 and bar["high"] >= max(bar["open"], bar["close"])
            and bar["low"] <= min(bar["open"], bar["close"]))


def valid_open(bar: dict | None) -> bool:
    """At a fill open, the rest of that H1 bar is still unknowable."""
    return bar is not None and math.isfinite(bar["open"]) and bar["open"] > 0


def qualifying_signal(spot_close: float, future_close: float, days_to_expiry: float) -> bool:
    if (not all(math.isfinite(value) for value in (spot_close, future_close, days_to_expiry))
            or spot_close <= 0 or future_close <= 0 or not 21 <= days_to_expiry <= 60):
        return False
    days = Decimal(str(days_to_expiry))
    basis = Decimal(str(future_close)) / Decimal(str(spot_close)) - 1
    annual = basis * 365 / days
    indicative_gain = basis * (days - 7) / days
    return annual > Decimal("0.15") and indicative_gain > Decimal("0.0076")


def exit_basis_reached(spot_close: float, future_close: float, days_to_expiry: float) -> bool:
    if (not all(math.isfinite(value) for value in (spot_close, future_close, days_to_expiry))
            or spot_close <= 0 or future_close <= 0 or days_to_expiry <= 0):
        return False
    basis = Decimal(str(future_close)) / Decimal(str(spot_close)) - 1
    return basis * 365 / Decimal(str(days_to_expiry)) <= Decimal("0.05")


def load_sources() -> tuple[dict, dict, dict, dict]:
    expected_spot = next(row["sha256"] for row in json.loads(Path("research/cache/v3/manifest.json").read_text(encoding="utf-8"))["series"] if row["file"] == SPOT.name)
    if sha(SPOT) != expected_spot:
        raise ValueError("spot v3 SHA mismatch")
    spot = {int(row["time"]): {field: float(row[field]) for field in ("open", "high", "low", "close")}
            for row in json.loads(SPOT.read_text(encoding="utf-8")) if int(row["time"]) < DEV_END}
    manifest = json.loads(DATA_MANIFEST.read_text(encoding="utf-8"))
    contracts = {row["contract"]: expiry_ms(row["contract"]) for row in manifest["discoveredContracts"]
                 if START < expiry_ms(row["contract"]) <= DEV_END}
    trade = {contract: {} for contract in contracts}
    mark = {contract: {} for contract in contracts}
    chosen = [row for row in manifest["files"] if row["contract"] in contracts]
    for item in chosen:
        path = Path(item["cachePath"])
        if item["status"] != "verified" or sha(path) != item["sha256"]:
            raise ValueError(f"dated source SHA mismatch: {path}")
        target = trade if item["kind"] == "trade_h1" else mark
        series = target[item["contract"]]
        with zipfile.ZipFile(path) as archive:
            with archive.open(archive.namelist()[0]) as source:
                for row in csv.reader(io.TextIOWrapper(source, encoding="utf-8-sig", newline="")):
                    if not row or row[0] == "open_time":
                        continue
                    timestamp = int(row[0])
                    if timestamp >= DEV_END:
                        continue
                    if timestamp in series:
                        raise ValueError(f"duplicate dated H1 {item['contract']} {timestamp}")
                    series[timestamp] = dict(zip(("open", "high", "low", "close"), map(float, row[1:5])))
    return spot, trade, mark, contracts


def sample(start: int, end: int, spot: dict, trade: dict, mark: dict,
           expiries: dict[str, int]) -> dict:
    """Count clean closed episodes; never multiply quantity by price changes."""
    position = None
    pending_entry = None
    last_exit = None
    episodes = []
    qualifying_decisions = 0
    valid_decisions = 0
    unavailable_decisions = 0
    signal_without_joint_open = 0
    cancelled_pending_entries = 0
    eligible_hours = 0
    for entry_open in range(start, end, HOUR):
        if position is not None:
            contract = position["contract"]
            s_now = spot.get(entry_open)
            f_now = trade[contract].get(entry_open)
            m_now = mark[contract].get(entry_open)
            joint_now = all(valid_open(bar) for bar in (s_now, f_now, m_now))
            if not joint_now:
                position["uncertain"].add("active-joint-H1-gap")
            if joint_now:
                days = (expiries[contract] - entry_open) / DAY
                deadline = entry_open >= expiries[contract] - 7 * DAY
                condition = False
                if not deadline:
                    s_prev = spot.get(entry_open - HOUR)
                    f_prev = trade[contract].get(entry_open - HOUR)
                    m_prev = mark[contract].get(entry_open - HOUR)
                    if not all(valid_bar(bar) for bar in (s_prev, f_prev, m_prev)):
                        position["uncertain"].add("active-decision-H1-gap")
                    else:
                        condition = exit_basis_reached(s_prev["close"], f_prev["close"], days)
                if deadline or condition:
                    episodes.append({"contract": contract, "entryOpenMs": position["entry"],
                                     "exitOpenMs": entry_open,
                                     "reason": "D-minus-7" if deadline else "annual-basis-at-most-5pct",
                                     "uncertain": sorted(position["uncertain"])})
                    position = None
                    last_exit = entry_open
        if position is not None or last_exit == entry_open:
            continue
        if pending_entry is not None:
            contract = pending_entry["contract"]
            if entry_open >= expiries[contract] - 7 * DAY:
                cancelled_pending_entries += 1
                pending_entry = None
                continue
            s_now = spot.get(entry_open)
            f_now = trade[contract].get(entry_open)
            m_now = mark[contract].get(entry_open)
            if all(valid_open(bar) for bar in (s_now, f_now, m_now)):
                if entry_open < pending_entry["signalCloseMs"]:
                    raise AssertionError("fill before completed signal")
                position = {"contract": contract, "entry": entry_open,
                            "uncertain": {"delayed-entry-open"}}
                pending_entry = None
            continue
        contract = nearest_contract(entry_open, expiries)
        if contract is None:
            continue
        eligible_hours += 1
        s_prev = spot.get(entry_open - HOUR)
        f_prev = trade[contract].get(entry_open - HOUR)
        m_prev = mark[contract].get(entry_open - HOUR)
        if not all(valid_bar(bar) for bar in (s_prev, f_prev, m_prev)):
            unavailable_decisions += 1
            continue
        valid_decisions += 1
        days = (expiries[contract] - entry_open) / DAY
        if not qualifying_signal(s_prev["close"], f_prev["close"], days):
            continue
        qualifying_decisions += 1
        s_now = spot.get(entry_open)
        f_now = trade[contract].get(entry_open)
        m_now = mark[contract].get(entry_open)
        if not all(valid_open(bar) for bar in (s_now, f_now, m_now)):
            signal_without_joint_open += 1
            pending_entry = {"contract": contract, "signalCloseMs": entry_open}
            continue
        position = {"contract": contract, "entry": entry_open, "uncertain": set()}
    if position is not None:
        episodes.append({"contract": position["contract"], "entryOpenMs": position["entry"],
                         "exitOpenMs": None, "reason": "open-at-development-boundary",
                         "uncertain": sorted(position["uncertain"] | {"unclosed"})})
    clean = [row for row in episodes if row["exitOpenMs"] is not None and not row["uncertain"]]
    uncertain = [row for row in episodes if row["exitOpenMs"] is not None and row["uncertain"]]
    open_count = sum(row["exitOpenMs"] is None for row in episodes)
    pending_at_boundary = int(pending_entry is not None)
    by_contract = {}
    for contract in sorted(expiries):
        by_contract[contract] = {"cleanClosed": sum(row["contract"] == contract for row in clean),
                                 "uncertainClosed": sum(row["contract"] == contract for row in uncertain),
                                 "openAtBoundary": sum(row["contract"] == contract and row["exitOpenMs"] is None for row in episodes)}
    return {"eligibleHours": eligible_hours, "validFlatDecisions": valid_decisions,
            "unavailableFlatDecisions": unavailable_decisions,
            "qualifyingFlatDecisions": qualifying_decisions,
            "signalWithoutJointOpen": signal_without_joint_open,
            "cancelledPendingEntries": cancelled_pending_entries,
            "pendingAtBoundary": pending_at_boundary,
            "cleanClosedEpisodes": len(clean), "uncertainClosedEpisodes": len(uncertain),
            "openAtBoundary": open_count, "byContract": by_contract,
            "episodes": episodes}


def run() -> None:
    if not FREEZE.exists():
        raise RuntimeError("dated-sample-freeze.json required before count")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    for name, expected in freeze["hashes"].items():
        if sha(Path(name)) != expected:
            raise RuntimeError(f"frozen SHA changed: {name}")
    spot, trade, mark, expiries = load_sources()
    output = sample(START, DEV_END, spot, trade, mark, expiries)
    DETAIL.parent.mkdir(parents=True, exist_ok=True)
    DETAIL.write_text(json.dumps(output.pop("episodes"), indent=2) + "\n", encoding="utf-8")
    result = {"family": "N10", "validated": False, "sampleOnly": True,
              "window": ["2022-01-01", "2025-01-01"],
              "sampleGatePassed": output["cleanClosedEpisodes"] >= 100,
              "PnLComputed": False, "laterWindowsOpened": False,
              "detailsPath": DETAIL.as_posix(), "freezeSha256": sha(FREEZE),
              "counts": output}
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", action="store_true")
    args = parser.parse_args()
    if args.sample:
        run()
