"""Download and audit Binance Vision USD-M monthly N2 inputs (no backtest).

Run: python scripts/download-goal-funding.py
Only public archives and their adjacent official SHA-256 CHECKSUM files are used.
"""

from __future__ import annotations

import calendar
import argparse
import concurrent.futures
import csv
from decimal import Decimal
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import re
import threading
import time
import urllib.error
import urllib.request
import zipfile


BASE = "https://data.binance.vision/data/futures/um/monthly"
ROOT = Path("research/cache/funding-goal")
MANIFEST = Path("research/goal-seven/funding-data-manifest.json")
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
KINDS = ("perp_h1", "mark_h1", "funding")
FIRST = (2022, 1)
LAST = (2026, 8)
MAX_WORKERS = 4
STOP = threading.Event()
UTC = dt.timezone.utc
HOUR_MS = 3_600_000


def months():
    year, month = FIRST
    while (year, month) <= LAST:
        yield year, month
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)


def url_for(kind: str, symbol: str, year: int, month: int) -> str:
    ym = f"{year}-{month:02d}"
    if kind == "funding":
        return f"{BASE}/fundingRate/{symbol}/{symbol}-fundingRate-{ym}.zip"
    folder = "klines" if kind == "perp_h1" else "markPriceKlines"
    return f"{BASE}/{folder}/{symbol}/1h/{symbol}-1h-{ym}.zip"


def request(url: str) -> bytes:
    for attempt in range(3):
        if STOP.is_set():
            raise RuntimeError("stopped after persistent access or rate-limit error")
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "TraderNova-research-data/1.0"}),
                timeout=35,
            ) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise FileNotFoundError(url) from exc
            if exc.code in (403, 429) and attempt == 2:
                STOP.set()
                raise RuntimeError(f"persistent HTTP {exc.code}: {url}") from exc
            if exc.code not in (403, 429, 500, 502, 503, 504):
                raise
        except (TimeoutError, urllib.error.URLError):
            if attempt == 2:
                raise
        time.sleep(2**attempt)
    raise AssertionError("unreachable")


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".part")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def parse_checksum(raw: bytes, filename: str) -> str:
    match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)", raw.decode("utf-8").strip())
    if not match or Path(match.group(2)).name != filename:
        raise ValueError(f"invalid official CHECKSUM for {filename}")
    return match.group(1).lower()


def audit_zip(path: Path, kind: str, year: int, month: int) -> dict:
    start = int(dt.datetime(year, month, 1, tzinfo=UTC).timestamp() * 1000)
    following = dt.datetime(year + (month == 12), month % 12 + 1, 1, tzinfo=UTC)
    end = int(following.timestamp() * 1000)
    count = 0
    first = last = previous = None
    gaps = 0
    missing_ranges = []
    columns = None
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(names) != 1 or archive.testzip() is not None:
            raise ValueError(f"invalid ZIP CSV structure: {path}")
        with archive.open(names[0]) as source:
            reader = csv.reader(io.TextIOWrapper(source, encoding="utf-8-sig", newline=""))
            for row in reader:
                if not row:
                    continue
                if columns is None:
                    if kind == "funding":
                        columns = ["calc_time", "funding_interval_hours", "last_funding_rate"]
                    elif kind == "mark_h1":
                        columns = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]
                    else:
                        columns = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]
                    if row[0] in ("calc_time", "open_time"):
                        if row != columns:
                            raise ValueError(f"unexpected CSV header: {path}: {row}")
                        continue
                if len(row) != len(columns):
                    raise ValueError(f"wrong column count: {path}: {len(row)}")
                timestamp = int(row[0])
                if not start <= timestamp < end:
                    raise ValueError(f"row outside month: {path}: {timestamp}")
                if previous is not None:
                    if timestamp <= previous:
                        raise ValueError(f"nonincreasing timestamp: {path}")
                    if kind != "funding" and timestamp - previous != HOUR_MS:
                        gaps += 1
                        if timestamp - previous > HOUR_MS:
                            missing_ranges.append((previous + HOUR_MS, timestamp))
                elif kind != "funding" and timestamp > start:
                    missing_ranges.append((start, timestamp))
                first = timestamp if first is None else first
                last = previous = timestamp
                count += 1
    if count == 0:
        raise ValueError(f"empty CSV: {path}")
    result = {"rows": count, "firstTimestampMs": first, "lastTimestampMs": last, "columns": columns}
    if kind != "funding":
        expected = calendar.monthrange(year, month)[1] * 24
        if last < end - HOUR_MS:
            missing_ranges.append((last + HOUR_MS, end))
        result.update({
            "expectedH1Rows": expected,
            "gaps": gaps,
            "missingH1RangesUtc": [
                [dt.datetime.fromtimestamp(a / 1000, UTC).isoformat(), dt.datetime.fromtimestamp(b / 1000, UTC).isoformat()]
                for a, b in missing_ranges
            ],
            "completeH1": count == expected and gaps == 0 and first == start and last == end - HOUR_MS,
        })
    return result


def process(job: tuple[str, str, int, int]) -> dict:
    kind, symbol, year, month = job
    url = url_for(kind, symbol, year, month)
    filename = url.rsplit("/", 1)[1]
    target = ROOT / kind / symbol / filename
    checksum_path = target.with_name(filename + ".CHECKSUM")
    item = {"kind": kind, "symbol": symbol, "month": f"{year}-{month:02d}", "url": url, "checksumUrl": url + ".CHECKSUM", "cachePath": target.as_posix()}
    try:
        raw_checksum = checksum_path.read_bytes() if checksum_path.exists() else request(url + ".CHECKSUM")
        expected_sha = parse_checksum(raw_checksum, filename)
        if not checksum_path.exists():
            write_atomic(checksum_path, raw_checksum)
        if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != expected_sha:
            write_atomic(target, request(url))
        observed_sha = hashlib.sha256(target.read_bytes()).hexdigest()
        if observed_sha != expected_sha:
            raise ValueError(f"official checksum mismatch: {target}")
        item.update({"status": "verified", "sha256": observed_sha, "bytes": target.stat().st_size})
        item.update(audit_zip(target, kind, year, month))
    except FileNotFoundError as exc:
        item.update({"status": "missing-at-source", "error": str(exc)})
    except Exception as exc:
        item.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
    return item


def spot_cache_inventory() -> dict:
    """Audit existing spot ZIPs without changing or redownloading them."""
    series = {}
    for symbol in SYMBOLS:
        files = []
        for path in sorted(Path("research/cache").glob(f"{symbol}-1h-*.zip")):
            checksum_path = path.with_name(path.name + ".CHECKSUM")
            expected = parse_checksum(checksum_path.read_bytes(), path.name) if checksum_path.exists() else None
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            files.append({"cachePath": path.as_posix(), "sha256": actual, "officialChecksumMatch": actual == expected})
        series[symbol] = {
            "monthsCached": len(files),
            "firstFile": Path(files[0]["cachePath"]).name if files else None,
            "lastFile": Path(files[-1]["cachePath"]).name if files else None,
            "allOfficialChecksumsMatch": bool(files) and all(f["officialChecksumMatch"] for f in files),
            "files": files,
        }
    return {
        "market": "Binance spot USDT (distinct from Binance USD-M perpetual)",
        "cacheRoot": "research/cache",
        "modified": False,
        "series": series,
    }


def save_manifest(items: list[dict]) -> None:
    ordered = sorted(items, key=lambda item: (item["kind"], item["symbol"], item["month"]))
    summary = {}
    for kind in KINDS:
        for symbol in SYMBOLS:
            group = [item for item in ordered if item["kind"] == kind and item["symbol"] == symbol]
            summary[f"{kind}/{symbol}"] = {
                "verifiedMonths": sum(item["status"] == "verified" for item in group),
                "expectedMonths": 56,
                "missingMonths": [item["month"] for item in group if item["status"] == "missing-at-source"],
                "errorMonths": [item["month"] for item in group if item["status"] == "error"],
                "incompleteH1Months": [item["month"] for item in group if item["status"] == "verified" and item.get("completeH1") is False],
            }
    document = {
        "purpose": "N2 funding data acquisition only; no strategy, backtest, or performance result",
        "venue": "Binance",
        "market": "USD-M perpetual futures (um), USDT-margined",
        "source": "https://github.com/binance/binance-public-data/blob/master/README.md",
        "archiveRoot": BASE,
        "periodUtcInclusive": ["2022-01", "2026-08"],
        "retrievedAtUtc": dt.datetime.now(UTC).isoformat(),
        "spotReuse": spot_cache_inventory(),
        "contractCaveat": "Binance USD-M perpetual/USDT data; transferability to other venues, MT5 brokers or The5ers contracts is unproven.",
        "checksumMethod": "SHA-256 of each ZIP matched to the adjacent official .CHECKSUM file",
        "summary": summary,
        "files": ordered,
    }
    if MANIFEST.exists():
        previous = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if "apiFunding" in previous:
            document["apiFunding"] = previous["apiFunding"]
    write_atomic(MANIFEST, (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def official_monthly_funding(symbol: str) -> set[tuple[int, Decimal]]:
    rows = set()
    for year, month in months():
        path = ROOT / "funding" / symbol / f"{symbol}-fundingRate-{year}-{month:02d}.zip"
        with zipfile.ZipFile(path) as archive:
            with archive.open(archive.namelist()[0]) as source:
                for row in csv.reader(io.TextIOWrapper(source, encoding="utf-8-sig", newline="")):
                    if row and row[0] != "calc_time":
                        rows.add((int(row[0]), Decimal(row[2])))
    return rows


def download_api_funding() -> int:
    """Preserve public REST responses; markPrice may be absent in older records."""
    start = int(dt.datetime(2022, 1, 1, tzinfo=UTC).timestamp() * 1000)
    end_exclusive = int(dt.datetime(2026, 9, 1, tzinfo=UTC).timestamp() * 1000)
    endpoint = "https://fapi.binance.com/fapi/v1/fundingRate"
    results = {}
    for symbol in SYMBOLS:
        cursor = start
        pages = []
        events = []
        for number in range(1, 31):
            url = f"{endpoint}?symbol={symbol}&startTime={cursor}&endTime={end_exclusive - 1}&limit=1000"
            raw = request(url)
            records = json.loads(raw)
            if not isinstance(records, list):
                raise ValueError(f"unexpected REST response for {symbol}")
            target = ROOT / "api_funding" / symbol / f"page-{number:03d}.json"
            write_atomic(target, raw)
            pages.append({"url": url, "cachePath": target.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "rows": len(records)})
            if not records:
                break
            for record in records:
                if record.get("symbol") != symbol or not start <= int(record["fundingTime"]) < end_exclusive:
                    raise ValueError(f"out-of-range REST funding event for {symbol}")
                if events and int(record["fundingTime"]) <= int(events[-1]["fundingTime"]):
                    raise ValueError(f"nonincreasing REST funding events for {symbol}")
                events.append(record)
            if len(records) < 1000:
                break
            cursor = int(records[-1]["fundingTime"]) + 1
        else:
            raise ValueError(f"REST pagination exceeded bound for {symbol}")
        rest_pairs = {(int(event["fundingTime"]), Decimal(event["fundingRate"])) for event in events}
        monthly_pairs = official_monthly_funding(symbol)
        mark_available = sum(bool(event.get("markPrice")) and Decimal(event["markPrice"]) > 0 for event in events)
        results[symbol] = {
            "source": endpoint,
            "pages": pages,
            "events": len(events),
            "firstTimestampMs": int(events[0]["fundingTime"]) if events else None,
            "lastTimestampMs": int(events[-1]["fundingTime"]) if events else None,
            "markPricePositiveEvents": mark_available,
            "markPriceMissingOrNonpositiveEvents": len(events) - mark_available,
            "firstPositiveMarkTimestampMs": next((int(event["fundingTime"]) for event in events if event.get("markPrice") and Decimal(event["markPrice"]) > 0), None),
            "officialMonthlyEvents": len(monthly_pairs),
            "restEventsMissingFromMonthly": len(rest_pairs - monthly_pairs),
            "monthlyEventsMissingFromRest": len(monthly_pairs - rest_pairs),
            "matchedMonthlyArchive": rest_pairs == monthly_pairs,
            "note": "markPrice is the REST event field; blanks are left blank, never imputed from H1 mark candles.",
        }
        print(f"REST {symbol}: {len(events)} events, {mark_available} positive markPrice, monthly match={rest_pairs == monthly_pairs}", flush=True)
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    document["apiFunding"] = results
    document["retrievedAtUtc"] = dt.datetime.now(UTC).isoformat()
    write_atomic(MANIFEST, (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return 0 if all(result["matchedMonthlyArchive"] for result in results.values()) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-only", action="store_true", help="download public fundingRate REST records after monthly ZIPs")
    args = parser.parse_args()
    if args.api_only:
        return download_api_funding()
    jobs = [(kind, symbol, year, month) for kind in KINDS for symbol in SYMBOLS for year, month in months()]
    items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(process, job) for job in jobs]
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            item = future.result()
            items.append(item)
            if index % 20 == 0 or index == len(jobs):
                save_manifest(items)
                print(f"{index}/{len(jobs)} archives checked; latest {item['kind']}/{item['symbol']}/{item['month']}: {item['status']}", flush=True)
            if STOP.is_set():
                for pending in futures:
                    pending.cancel()
                break
    save_manifest(items)
    errors = [item for item in items if item["status"] != "verified"]
    incomplete = [item for item in items if item.get("completeH1") is False]
    print(f"verifiedArchives={len(items)-len(errors)} incompleteH1={len(incomplete)} errors={len(errors)} processed={len(items)}/{len(jobs)}", flush=True)
    return 1 if errors or len(items) != len(jobs) else 0


if __name__ == "__main__":
    raise SystemExit(main())
