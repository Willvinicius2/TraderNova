"""Archive official Treasury daily real 10-year yields; no trading or backtest.

Raw downloads live under ignored research/cache/goal-seven/real-yields/. Existing
raw bytes are never overwritten: a changed upstream response raises an error so
that this snapshot cannot silently acquire a different historical vintage.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "research/cache/goal-seven/real-yields"
MANIFEST = ROOT / "research/goal-seven/real-yields-manifest.json"
BASE = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates"
SOURCES = (
    ("treasury-real-yields-2003-2023.csv",
     BASE + "/daily-treasury-rate-archives/par-real-yield-curve-rates-2003-2023.csv"),
    *((f"treasury-real-yields-{year}.csv",
       BASE + f"/daily-treasury-rates.csv/{year}/all?field_tdr_date_value={year}&type=daily_treasury_real_yield_curve&page&_format=csv")
      for year in (2024, 2025, 2026)),
)


def download(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "TraderNova research source audit/1.0"})
    with urlopen(request, timeout=60) as response:
        if response.status != 200:
            raise ValueError(f"HTTP {response.status}: {url}")
        content = response.read()
        if not content or "html" in response.headers.get("Content-Type", "").lower():
            raise ValueError(f"Not a CSV response: {url}")
        return content


def parse(content: bytes, label: str) -> dict[str, str]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError(f"Missing CSV header: {label}")
    fields = {field.strip().lower(): field for field in reader.fieldnames}
    if "date" not in fields or "10 yr" not in fields:
        raise ValueError(f"Missing date or 10-year yield column: {label}")
    rows: dict[str, str] = {}
    for number, row in enumerate(reader, 2):
        date = datetime.strptime(row[fields["date"]].strip(), "%m/%d/%Y").date().isoformat()
        value = row[fields["10 yr"]].strip()
        if not value or not math.isfinite(float(value)):
            raise ValueError(f"Missing/invalid 10-year yield {label}:{number}")
        if date in rows:
            raise ValueError(f"Duplicate observation {date} in {label}")
        rows[date] = value
    if not rows:
        raise ValueError(f"No rows: {label}")
    return rows


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="verify saved files without network")
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    records = []
    consolidated: dict[str, str] = {}
    for name, url in SOURCES:
        path = CACHE / name
        if args.verify:
            content = path.read_bytes()
        else:
            content = download(url)
            if path.exists():
                if path.read_bytes() != content:
                    raise ValueError(f"Source changed; existing raw snapshot preserved: {path}")
            else:
                path.write_bytes(content)
        rows = parse(content, name)
        for date, value in rows.items():
            if date < "2009-01-01":
                continue
            if date in consolidated:
                raise ValueError(f"Overlapping source date {date}")
            consolidated[date] = value
        records.append({
            "file": path.relative_to(ROOT).as_posix(), "url": url,
            "sha256": sha256(content), "bytes": len(content), "rows": len(rows),
            "firstDate": min(rows), "lastDate": max(rows),
            "rowsFrom2009": sum(date >= "2009-01-01" for date in rows),
        })
    if min(consolidated) > "2009-01-02" or max(consolidated) < "2026-09-01":
        raise ValueError("Expected 2009 through September 2026 coverage not present")
    normalized = CACHE / "treasury-real-yield-10yr-2009-2026.csv"
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(("date", "real_yield_10yr_pct"))
    writer.writerows((date, consolidated[date]) for date in sorted(consolidated))
    normalized_bytes = buffer.getvalue().encode("utf-8")
    if args.verify:
        if not normalized.exists() or normalized.read_bytes() != normalized_bytes:
            raise ValueError("Normalized cache missing or does not match source files")
    else:
        normalized.write_bytes(normalized_bytes)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest = {
        "id": "goal-seven-us-treasury-real-yield-10yr",
        "retrievedAtUTC": now,
        "sourceOrganization": "U.S. Department of the Treasury",
        "sourceIndex": BASE + "/daily-treasury-rate-archives",
        "currentSourcePage": BASE + "/TextView?type=daily_treasury_real_yield_curve",
        "sourceFiles": records,
        "derivedFile": {"file": normalized.relative_to(ROOT).as_posix(),
                        "sha256": sha256(normalized_bytes), "bytes": len(normalized_bytes),
                        "rows": len(consolidated), "firstDate": min(consolidated),
                        "lastDate": max(consolidated), "unit": "percent per year"},
        "observationDateIsPublicationTimestamp": False,
        "historicalPublicationTimestampsVerified": False,
        "pointInTimeVintagesVerified": False,
        "revisionAudit": "Current official archive/current CSV snapshot only; no dated historical vintages or per-observation publication timestamps were established.",
        "useLimit": "Source audit only. A 48-US-business-hour lag is a conservative proposal, not proof that these retrospectively downloadable values were known then. No XAU backtest or approval claim from this manifest.",
    }
    if not args.verify:
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        saved = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if [(x["sha256"], x["rows"]) for x in saved["sourceFiles"]] != [
            (x["sha256"], x["rows"]) for x in records
        ] or saved["derivedFile"]["sha256"] != manifest["derivedFile"]["sha256"]:
            raise ValueError("Manifest hash/row mismatch")
    print(f"Treasury real yield: {len(consolidated)} observations, {min(consolidated)} to {max(consolidated)}; PIT unverified")


if __name__ == "__main__":
    main()
