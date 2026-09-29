"""Discover and checksum-verify only relevant Binance Vision dated BTC H1 ZIPs.

Run from repository root: python scripts/download-goal-dated.py
No API keys, orders, prices, signals or performance are produced.
"""

from __future__ import annotations

import concurrent.futures
import csv
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
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile


S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
DATA = "https://data.binance.vision"
ROOT = Path("research/cache/goal-seven/dated")
MANIFEST = Path("research/goal-seven/dated-data-manifest.json")
TYPES = {"trade_h1": "klines", "mark_h1": "markPriceKlines"}
START = dt.datetime(2022, 1, 1, tzinfo=dt.timezone.utc)
END = dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc)
HOUR = dt.timedelta(hours=1)
STOP = threading.Event()
NS = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}


def request(url: str) -> bytes:
    for attempt in range(3):
        if STOP.is_set():
            raise RuntimeError("stopped after persistent rate/access error")
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "TraderNova-research-data/1.0"}), timeout=35) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429) and attempt == 2:
                STOP.set()
                raise RuntimeError(f"persistent HTTP {exc.code}: {url}") from exc
            if exc.code not in (403, 429, 500, 502, 503, 504):
                raise
        except (TimeoutError, urllib.error.URLError):
            if attempt == 2:
                raise
        time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def list_objects(prefix: str, delimiter: str | None = None) -> tuple[list[str], list[str]]:
    keys, prefixes = [], []
    token = None
    while True:
        query = {"list-type": "2", "prefix": prefix, "max-keys": 1000}
        if delimiter:
            query["delimiter"] = delimiter
        if token:
            query["continuation-token"] = token
        root = ET.fromstring(request(S3 + "?" + urllib.parse.urlencode(query)))
        keys.extend(item.text for item in root.findall("s:Contents/s:Key", NS))
        prefixes.extend(item.text for item in root.findall("s:CommonPrefixes/s:Prefix", NS))
        if root.findtext("s:IsTruncated", namespaces=NS) != "true":
            break
        token = root.findtext("s:NextContinuationToken", namespaces=NS)
        if not token:
            raise ValueError("S3 truncated listing without token")
    return keys, prefixes


def expiry_of(contract: str) -> dt.datetime:
    match = re.fullmatch(r"BTCUSDT_(\d{6})", contract)
    if not match:
        raise ValueError(f"unexpected contract prefix: {contract}")
    date = dt.datetime.strptime(match.group(1), "%y%m%d").date()
    return dt.datetime.combine(date, dt.time(8), tzinfo=dt.timezone.utc)


def selected_month(key: str, expiry: dt.datetime) -> bool:
    match = re.search(r"-1h-(\d{4})-(\d{2})\.zip$", key)
    if not match:
        return False
    year, month = map(int, match.groups())
    month_start = dt.datetime(year, month, 1, tzinfo=dt.timezone.utc)
    month_end = dt.datetime(year + (month == 12), month % 12 + 1, 1, tzinfo=dt.timezone.utc)
    needed_start = max(START, expiry - dt.timedelta(days=60) - HOUR)
    needed_end = min(END, expiry - dt.timedelta(days=7) + HOUR)
    return month_start < needed_end and needed_start < month_end


def discover() -> tuple[list[dict], list[dict]]:
    contract_types = {}
    for kind, folder in TYPES.items():
        _, prefixes = list_objects(f"data/futures/um/monthly/{folder}/BTCUSDT_", "/")
        contract_types[kind] = {prefix.rstrip("/").split("/")[-1] for prefix in prefixes}
    contracts = sorted(contract_types["trade_h1"] | contract_types["mark_h1"])
    inventory = []
    selected = []
    for contract in contracts:
        expiry = expiry_of(contract)
        record = {"contract": contract, "expiryUtc": expiry.isoformat(),
                  "tradePrefixListed": contract in contract_types["trade_h1"],
                  "markPrefixListed": contract in contract_types["mark_h1"]}
        inventory.append(record)
        if expiry <= START or expiry - dt.timedelta(days=60) >= END:
            continue
        for kind, folder in TYPES.items():
            if contract not in contract_types[kind]:
                continue
            prefix = f"data/futures/um/monthly/{folder}/{contract}/1h/"
            keys, _ = list_objects(prefix)
            key_set = set(keys)
            for key in sorted(keys):
                if key.endswith(".zip") and selected_month(key, expiry):
                    selected.append({"kind": kind, "contract": contract, "expiryUtc": expiry.isoformat(),
                                     "key": key, "checksumListed": key + ".CHECKSUM" in key_set})
    return inventory, selected


def write_atomic(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".part")
    temporary.write_bytes(raw)
    os.replace(temporary, path)


def audit_zip(path: Path, key: str) -> dict:
    match = re.search(r"-1h-(\d{4})-(\d{2})\.zip$", key)
    year, month = map(int, match.groups())
    month_start = int(dt.datetime(year, month, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
    month_end = int(dt.datetime(year + (month == 12), month % 12 + 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
    count = 0
    first = last = previous = None
    gaps = 0
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(names) != 1 or archive.testzip() is not None:
            raise ValueError("invalid ZIP CSV structure")
        with archive.open(names[0]) as source:
            for row in csv.reader(io.TextIOWrapper(source, encoding="utf-8-sig", newline="")):
                if not row or row[0] == "open_time":
                    continue
                if len(row) != 12:
                    raise ValueError(f"unexpected CSV columns: {len(row)}")
                stamp = int(row[0])
                if not month_start <= stamp < month_end:
                    raise ValueError(f"row outside archive month: {stamp}")
                if previous is not None:
                    if stamp <= previous:
                        raise ValueError("nonincreasing timestamps")
                    if stamp - previous != 3_600_000:
                        gaps += 1
                first = stamp if first is None else first
                last = previous = stamp
                count += 1
    if count == 0:
        raise ValueError("empty H1 archive")
    return {"rows": count, "firstTimestampMs": first, "lastTimestampMs": last, "internalGaps": gaps}


def fetch(item: dict) -> dict:
    result = dict(item)
    key = item["key"]
    filename = key.rsplit("/", 1)[1]
    path = ROOT / item["kind"] / item["contract"] / filename
    check_path = path.with_name(filename + ".CHECKSUM")
    url = DATA + "/" + key
    result.update({"url": url, "checksumUrl": url + ".CHECKSUM", "cachePath": path.as_posix()})
    try:
        if not item["checksumListed"]:
            raise ValueError("official checksum missing from S3 listing")
        raw_check = check_path.read_bytes() if check_path.exists() else request(url + ".CHECKSUM")
        match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)", raw_check.decode("utf-8").strip())
        if not match or Path(match.group(2)).name != filename:
            raise ValueError("invalid official checksum contents")
        expected = match.group(1).lower()
        if not check_path.exists():
            write_atomic(check_path, raw_check)
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            write_atomic(path, request(url))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            raise ValueError("ZIP checksum mismatch")
        result.update({"status": "verified", "sha256": digest, "bytes": path.stat().st_size})
        result.update(audit_zip(path, key))
    except Exception as exc:
        result.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
    return result


def save(inventory: list[dict], selected: list[dict], completed: list[dict]) -> None:
    document = {
        "purpose": "N10 dated-future H1 data acquisition only; no signals or PnL",
        "source": S3,
        "archiveBase": DATA,
        "discoveredContracts": inventory,
        "selectedListedH1Archives": len(selected),
        "periodEndExclusiveUtc": END.isoformat(),
        "selection": "Only S3-listed 1h ZIPs whose month intersects D-60d-through-D-7d research window, bounded by 2022-01-01 and 2026-09-01; D expiry at 08:00 UTC",
        "checksum": "SHA-256 of ZIP matched adjacent official .CHECKSUM",
        "files": sorted(completed, key=lambda row: row["key"]),
    }
    write_atomic(MANIFEST, (json.dumps(document, indent=2) + "\n").encode("utf-8"))


def main() -> int:
    inventory, selected = discover()
    print(f"listedContracts={len(inventory)} selectedListedH1ZIPs={len(selected)}", flush=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(fetch, item) for item in selected]
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            results.append(future.result())
            if index % 20 == 0 or index == len(selected):
                save(inventory, selected, results)
                print(f"{index}/{len(selected)} verified={sum(x['status']=='verified' for x in results)}", flush=True)
            if STOP.is_set():
                for pending in futures:
                    pending.cancel()
                break
    save(inventory, selected, results)
    errors = [row for row in results if row["status"] != "verified"]
    print(f"verifiedArchives={len(results)-len(errors)} errors={len(errors)} selected={len(selected)}", flush=True)
    return 1 if errors or len(results) != len(selected) else 0


if __name__ == "__main__":
    raise SystemExit(main())
