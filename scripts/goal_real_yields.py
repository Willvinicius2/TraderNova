"""Frozen N7 real-yield/XAU H1 development screen; never opens 2016+ data for PnL."""

from __future__ import annotations

import argparse
import bisect
import csv
import gzip
import hashlib
import json
import math
from decimal import Decimal
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from gold_signals import atr, read_bars
import gold_h1_execution as engine


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path("D:/openclaude/Nova pasta/SNIPER_XAUUSD/calibration")
GOLD_PATH = SOURCE_DIR / "XAUUSD_H1.csv"
YIELD_PATH = ROOT / "research/cache/goal-seven/real-yields/treasury-real-yield-10yr-2009-2026.csv"
YIELD_MANIFEST = ROOT / "research/goal-seven/real-yields-manifest.json"
PROTOCOL_PATH = ROOT / "research/goal-seven/real-yield-protocol.json"
FREEZE_PATH = ROOT / "research/goal-seven/real-yield-freeze.json"
RESULT_PATH = ROOT / "research/goal-seven/real-yield-results.json"
DETAIL_DIR = ROOT / "research/cache/goal-seven/real-yields"
HOUR = 3600
START = int(datetime(2010, 1, 1, tzinfo=timezone.utc).timestamp())
END = int(datetime(2016, 1, 1, tzinfo=timezone.utc).timestamp())


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp_day(seconds: int) -> date:
    """Interpret exported seconds as broker calendar labels, not verified UTC."""
    return datetime.fromtimestamp(seconds, timezone.utc).date()


def load_yields(path: Path = YIELD_PATH) -> list[tuple[date, float]]:
    result: list[tuple[date, float]] = []
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["date", "real_yield_10yr_pct"]:
            raise ValueError("Unexpected Treasury normalized schema")
        for row in reader:
            when = date.fromisoformat(row["date"])
            value = float(row["real_yield_10yr_pct"])
            if not math.isfinite(value) or (result and when <= result[-1][0]):
                raise ValueError("Nonfinite, duplicate or unordered Treasury yield")
            result.append((when, value))
    if len(result) < 6:
        raise ValueError("Fewer than six Treasury observations")
    return result


def select_observation(broker_date: date, yields: list[tuple[date, float]]) -> tuple[int, Decimal] | None:
    """Index and five-observation yield delta, using only dates 7–14 days old."""
    dates = [row[0] for row in yields]
    last_allowed = broker_date - timedelta(days=7)
    earliest_allowed = broker_date - timedelta(days=14)
    index = bisect.bisect_right(dates, last_allowed) - 1
    if index < 5 or dates[index] < earliest_allowed:
        return None
    return index, Decimal(str(yields[index][1])) - Decimal(str(yields[index - 5][1]))


def make_signals(bars: np.ndarray, yields: list[tuple[date, float]]) -> list[dict | None]:
    """One decision after each observed 08:00 broker H1; no future prices/yields."""
    output: list[dict | None] = [None] * len(bars)
    if not len(bars):
        return output
    a = atr(bars)
    for i, candle in enumerate(bars):
        t = int(candle["time"])
        if t % 86400 != 8 * HOUR or not math.isfinite(float(a[i])) or a[i] <= 0:
            continue
        chosen = select_observation(stamp_day(t), yields)
        if chosen is None:
            continue
        index, delta = chosen
        direction = 1 if delta <= Decimal("-0.15") else -1 if delta >= Decimal("0.15") else 0
        if direction == 0:
            continue
        signal_close = float(candle["close"])
        distance = 2 * float(a[i])
        output[i] = {
            "id": "N7", "direction": direction,
            "stop": signal_close - direction * distance,
            "target": signal_close + direction * 2 * distance,
            "atr": float(a[i]), "reward": 2.0, "minRewardR": 2.0,
            "holdBars": 8, "maxTradesPerDay": 1,
            "treasuryObservationDate": yields[index][0].isoformat(),
            "treasuryDeltaPctPoints": float(round(delta, 10)),
        }
    return output


def current_hashes() -> dict:
    selected = json.loads((ROOT / "research/gold-h1-v2-selection.json").read_text(encoding="utf-8"))
    original = json.loads((SOURCE_DIR / "selection.json").read_text(encoding="utf-8"))
    gold_hash = digest(GOLD_PATH)
    if gold_hash != selected["sourceHashes"]["H1"] or gold_hash != original["data_sha256"]["H1"]:
        raise ValueError("XAU H1 SHA-256 differs from original selections")
    manifest = json.loads(YIELD_MANIFEST.read_text(encoding="utf-8"))
    yield_hash = digest(YIELD_PATH)
    if yield_hash != manifest["derivedFile"]["sha256"] or manifest["pointInTimeVintagesVerified"]:
        raise ValueError("Treasury source hash or vintage status changed")
    if engine.COSTS != {
        "base": {"spread": 0.6, "slippage": 0.1, "commissionPerLotRT": 10.0},
        "stress": {"spread": 1.2, "slippage": 0.25, "commissionPerLotRT": 20.0},
    } or engine.RISK_PER_TRADE != 250 or engine.INITIAL_CAPITAL != 100000:
        raise ValueError("Legacy execution costs or capital/risk constants changed")
    paths = {
        "protocol": PROTOCOL_PATH,
        "runner": Path(__file__).resolve(),
        "goldSignals": ROOT / "scripts/gold_signals.py",
        "goldExecution": ROOT / "scripts/gold_h1_execution.py",
        "goldH1": GOLD_PATH,
        "sourceSelection": SOURCE_DIR / "selection.json",
        "priorGoldSelection": ROOT / "research/gold-h1-v2-selection.json",
        "treasury10Year": YIELD_PATH,
        "treasuryManifest": YIELD_MANIFEST,
    }
    return {name: digest(path) for name, path in paths.items()}


def freeze() -> None:
    if FREEZE_PATH.exists() or RESULT_PATH.exists():
        raise FileExistsError("N7 freeze/results already exist; do not overwrite this trial")
    record = {
        "id": "goal-seven-N7-real-yield-XAU-H1-v1",
        "frozenAtUTC": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hashes": current_hashes(),
        "development": ["2010-01-01", "2016-01-01"],
        "laterPerformanceViewed": False,
        "pointInTimeVintagesVerified": False,
        "maxLeverageRuntime": 1.0,
    }
    FREEZE_PATH.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("N7 inputs and rule frozen; no performance run")


def concise(run: dict) -> dict:
    return {key: (len(value) if key == "trades" else value) for key, value in run.items()
            if key not in ("curve", "daily")}


def develop() -> None:
    if RESULT_PATH.exists():
        raise FileExistsError("N7 development result already exists; refusing a second trial")
    frozen = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    if frozen["hashes"] != current_hashes() or frozen["maxLeverageRuntime"] != 1.0:
        raise ValueError("Frozen sources/rules changed before performance")
    yields = load_yields()
    bars = read_bars(GOLD_PATH)
    sample = bars[bars["time"] < END]
    signals = make_signals(sample, yields)
    engine.MAX_LEVERAGE = 1.0
    reports = {scenario: engine.simulate(sample, signals, START, END, scenario)
               for scenario in ("base", "stress")}
    if frozen["hashes"] != current_hashes():
        raise ValueError("Frozen files changed during performance")
    gates = []
    for name, run in reports.items():
        dd_cap = 8000 if name == "base" else 10000
        daily_cap = 2000 if name == "base" else 3000
        checks = {
            "tradesAtLeast100": len(run["trades"]) >= 100,
            "positiveNet": run["net"] > 0,
            "profitFactorAtLeast1_2": run["profitFactor"] is not None and run["profitFactor"] >= 1.2,
            "drawdownProxyUnderCap": run["conservativeDrawdown"] <= dd_cap,
            "dailyAdverseLossUnderCap": run["maxDailyConservativeEquityLoss"] <= daily_cap,
            "noUnpricedOvernight": run["overnightUnpriced"] == 0,
            "noAccountBreach": not run["accountBreached"],
        }
        gates.append({"scenario": name, "checks": checks, "screenPass": all(checks.values())})
    DETAIL_DIR.mkdir(parents=True, exist_ok=True)
    details = {}
    for scenario, run in reports.items():
        path = DETAIL_DIR / f"N7-development-{scenario}.json.gz"
        with gzip.open(path, "wt", encoding="utf-8") as stream:
            json.dump(run, stream, allow_nan=False, separators=(",", ":"))
        details[scenario] = {"file": path.relative_to(ROOT).as_posix(), "sha256": digest(path)}
    result = {
        "id": frozen["id"], "freezeSha256": digest(FREEZE_PATH),
        "phase": "development-only-2010-2015", "laterPeriodsEvaluated": False,
        "historicalDevelopmentScreenPass": all(g["screenPass"] for g in gates),
        "gateResults": gates,
        "base": concise(reports["base"]), "stress": concise(reports["stress"]),
        "detailFiles": details, "pointInTimeVerified": False,
        "drawdownMaximumRealVerified": False,
        "operationallyApproved": False, "validated": False,
        "goalSevenApprovedCountIncrement": 0,
        "interpretation": "Retrospective development only. Treasury vintage, broker clock, true intrabar DD and executable costs remain unverified.",
    }
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"N7 development: base {reports['base']['net']:.2f}, stress {reports['stress']['net']:.2f}, "
          f"trades {len(reports['base']['trades'])}, screen={result['historicalDevelopmentScreenPass']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("freeze", "develop"), required=True)
    args = parser.parse_args()
    if args.phase == "freeze":
        freeze()
    else:
        develop()


if __name__ == "__main__":
    main()
