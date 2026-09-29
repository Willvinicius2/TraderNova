"""Snapshot official CFTC Gold futures-only positioning; count triggers, not PnL.

The archives carry as-of report dates, not actual release timestamps/vintages.
Existing raw ZIP files are never silently overwritten if upstream bytes change.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "research/cache/goal-seven/cot"
MANIFEST = ROOT / "research/goal-seven/cot-data-manifest.json"
BASE = "https://www.cftc.gov/files/dea/history/"
SOURCES = (
    ("fut_disagg_txt_hist_2006_2016.zip", BASE + "fut_disagg_txt_hist_2006_2016.zip"),
    *((f"fut_disagg_txt_{year}.zip", BASE + f"fut_disagg_txt_{year}.zip")
      for year in range(2017, 2027)),
)
GOLD_CODE = "088691"
GOLD_NAME = "GOLD - COMMODITY EXCHANGE INC."
FIELDS = (
    "Report_Date_as_YYYY-MM-DD", "CFTC_Contract_Market_Code", "Market_and_Exchange_Names",
    "Open_Interest_All", "M_Money_Positions_Long_All", "M_Money_Positions_Short_All",
)
WINDOWS = {
    "development2011_2015": ("2011-01-01", "2016-01-01", 100),
    "validation2016_2020": ("2016-01-01", "2021-01-01", 100),
    "recent2021_aug2026": ("2021-01-01", "2026-09-01", 50),
}


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def download(url: str) -> bytes:
    response = requests.get(url, timeout=60, headers={"User-Agent": "TraderNova COT source audit/1.0"})
    response.raise_for_status()
    if response.headers.get("Content-Type", "").lower().startswith("text/html"):
        raise ValueError(f"HTML response instead of ZIP: {url}")
    return response.content


def parse_zip(content: bytes, label: str) -> tuple[list[dict], str]:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".txt")]
        if len(names) != 1:
            raise ValueError(f"Expected one text file in {label}, got {names}")
        inner = names[0]
        with archive.open(inner) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1", newline=""))
            if reader.fieldnames is None or not set(FIELDS) <= set(reader.fieldnames):
                raise ValueError(f"Unexpected Disaggregated Futures-Only schema in {label}")
            rows = []
            for row in reader:
                if row["CFTC_Contract_Market_Code"].strip() != GOLD_CODE:
                    continue
                if row["Market_and_Exchange_Names"].strip() != GOLD_NAME:
                    raise ValueError(f"Contract code {GOLD_CODE} changed market name in {label}")
                date = row["Report_Date_as_YYYY-MM-DD"].strip()
                datetime.strptime(date, "%Y-%m-%d")
                oi, long, short = (int(row[field].strip()) for field in FIELDS[3:])
                if oi <= 0 or min(long, short) < 0 or max(long, short) > oi:
                    raise ValueError(f"Invalid Gold positioning {date} in {label}")
                rows.append({"reportDate": date, "openInterest": oi,
                             "managedMoneyLong": long, "managedMoneyShort": short})
    if not rows or len({row["reportDate"] for row in rows}) != len(rows):
        raise ValueError(f"Empty/duplicate Gold report dates in {label}")
    return rows, inner


def count_h3(rows: list[dict]) -> dict:
    """Count report-date triggers only; not release-time-valid entries or trades."""
    p = [(row["managedMoneyLong"] - row["managedMoneyShort"]) / row["openInterest"]
         for row in rows]
    triggers = []
    for i in range(104, len(rows)):
        prior = sorted(p[i - 104:i])
        # Fixed nearest-rank cutoffs: ceil(.10*104)=11th; ceil(.90*104)=94th.
        lower, upper = prior[math.ceil(.10 * 104) - 1], prior[math.ceil(.90 * 104) - 1]
        direction = -1 if p[i] > upper and p[i] < p[i - 1] < p[i - 2] else (
            1 if p[i] < lower and p[i] > p[i - 1] > p[i - 2] else 0)
        if direction:
            triggers.append({"reportDate": rows[i]["reportDate"], "direction": direction})
    counts = {}
    for label, (start, end, minimum) in WINDOWS.items():
        reports = [row for row in rows if start <= row["reportDate"] < end]
        selected = [one for one in triggers if start <= one["reportDate"] < end]
        counts[label] = {
            "reportRows": len(reports), "triggerUpperBound": len(selected),
            "longTriggers": sum(one["direction"] == 1 for one in selected),
            "shortTriggers": sum(one["direction"] == -1 for one in selected),
            "minimumTradesGate": minimum,
            "minimumReachableEvenIfEveryReportTraded": len(reports) >= minimum,
            "minimumReachableWithFixedH3Trigger": len(selected) >= minimum,
            "interpretation": "Upper bound by as-of report date; actual release availability and overlapping five-session positions may reduce entries further.",
        }
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="verify saved ZIPs/CSV/manifest without network")
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    sources = []
    by_date: dict[str, dict] = {}
    for filename, url in SOURCES:
        path = CACHE / filename
        if args.verify:
            content = path.read_bytes()
        else:
            content = download(url)
            if path.exists():
                if path.read_bytes() != content:
                    raise ValueError(f"Upstream changed; preserve old snapshot before refreshing {path}")
            else:
                path.write_bytes(content)
        rows, inner = parse_zip(content, filename)
        for row in rows:
            if row["reportDate"] in by_date:
                raise ValueError(f"Overlapping report date {row['reportDate']}")
            by_date[row["reportDate"]] = row
        sources.append({"file": path.relative_to(ROOT).as_posix(), "url": url,
                        "sha256": sha256(content), "bytes": len(content),
                        "innerFile": inner, "goldRows": len(rows),
                        "firstReportDate": min(x["reportDate"] for x in rows),
                        "lastReportDate": max(x["reportDate"] for x in rows)})
    ordered = [by_date[key] for key in sorted(by_date)]
    if ordered[0]["reportDate"] > "2006-06-13" or ordered[-1]["reportDate"] < "2026-08-25":
        raise ValueError("Gold report-date coverage insufficient")
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(("report_date_as_of", "cftc_contract_code", "open_interest_all",
                     "managed_money_long_all", "managed_money_short_all"))
    writer.writerows((row["reportDate"], GOLD_CODE, row["openInterest"],
                      row["managedMoneyLong"], row["managedMoneyShort"]) for row in ordered)
    normalized = CACHE / "gold-disaggregated-futures-only-asof-2006-2026.csv"
    normalized_bytes = out.getvalue().encode("utf-8")
    if args.verify:
        if not normalized.exists() or normalized.read_bytes() != normalized_bytes:
            raise ValueError("Normalized CSV absent/different")
    else:
        normalized.write_bytes(normalized_bytes)
    counts = count_h3(ordered)
    manifest = {
        "id": "goal-seven-N8-CFTC-Gold-disaggregated-futures-only",
        "retrievedAtUTC": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sourceIndex": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm",
        "market": GOLD_NAME, "cftcContractCode": GOLD_CODE,
        "sourceFiles": sources,
        "normalized": {"file": normalized.relative_to(ROOT).as_posix(),
                       "sha256": sha256(normalized_bytes), "bytes": len(normalized_bytes),
                       "rows": len(ordered), "firstReportDate": ordered[0]["reportDate"],
                       "lastReportDate": ordered[-1]["reportDate"]},
        "actualReleaseTimestampsPresent": False,
        "pointInTimeVintagesVerified": False,
        "reportDateIsPublicationDate": False,
        "historyWarning": "CFTC archive is a current snapshot keyed by position as-of date; exceptions and corrections prevent inferring exact historical public availability from the usual Friday schedule.",
        "h3TriggerCountOnlyNoPnl": {"rule": "P=(Managed Money Long-Short)/OI; strict >90th/<10th nearest-rank of 104 prior reports and two consecutive P declines/rises; one candidate per report date; five-session holding overlap can only lower entries",
                                   "windowsByAsOfReportDate": counts},
        "inspectionDisclosure": "Development-only sequencing was breached: H3 trigger counts in validation 2016-2020 and recent 2021-Aug 2026 were also inspected after the development gate was already unreachable. No prices or PnL were queried. These later windows are not untouched holdouts for H3; parameters remain unchanged.",
        "approval": "No backtest, causal replay, profit, drawdown, validation or strategy approval from this data audit.",
    }
    if args.verify:
        saved = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if ([(x["sha256"], x["goldRows"]) for x in saved["sourceFiles"]]
                != [(x["sha256"], x["goldRows"]) for x in sources]
                or saved["normalized"]["sha256"] != manifest["normalized"]["sha256"]
                or saved["h3TriggerCountOnlyNoPnl"]["windowsByAsOfReportDate"] != counts
                or saved.get("inspectionDisclosure") != manifest["inspectionDisclosure"]):
            raise ValueError("COT manifest/source mismatch")
    else:
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"CFTC Gold: {len(ordered)} report-date rows; H3 trigger upper bounds "
          + ", ".join(f"{k}={v['triggerUpperBound']}/{v['minimumTradesGate']}"
                      for k, v in counts.items()) + "; PIT unverified")


if __name__ == "__main__":
    main()
