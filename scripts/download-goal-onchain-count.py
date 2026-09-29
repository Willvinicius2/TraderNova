"""Acquire Coin Metrics Community TxTfrCnt daily metadata/data for registered N12 scope only."""

from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request


API = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
ASSETS = ("btc", "eth")
SYMBOLS = {"btc": "BTCUSDT", "eth": "ETHUSDT"}
METRIC = "TxTfrCnt"
START = dt.date(2021, 9, 1)
END = dt.date(2024, 12, 31)
PAGE_SIZE = 10_000
MAX_GETS = 20
MAX_BYTES = 10 * 1024 * 1024
ROOT = Path("research/cache/goal-seven/onchain-count")
MANIFEST = Path("research/goal-seven/onchain-count-data-manifest.json")
REPORT = Path("research/goal-seven/ONCHAIN_COUNT_DATA.md")
TIME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})T00:00:00(?:\.0+)?Z$")


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def save_manifest(document: dict) -> None:
    path = Path(MANIFEST)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".part")
    temp.write_text(json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def immutable_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError(f"immutable raw-cache conflict: {path.as_posix()}")
        return
    temp = path.with_name(path.name + ".part")
    if temp.exists():
        raise ValueError(f"stale temporary cache file: {temp.as_posix()}")
    temp.write_bytes(raw)
    os.replace(temp, path)


def decode_json(raw: bytes):
    def reject_constant(value):
        raise ValueError(f"nonstandard JSON numeric constant: {value}")
    return json.loads(raw.decode("utf-8"), parse_float=Decimal, parse_constant=reject_constant)


def parse_daily_time(value: object) -> tuple[str, int] | None:
    if not isinstance(value, str):
        return None
    match = TIME_RE.fullmatch(value)
    if not match:
        return None
    day = dt.date.fromisoformat(match.group(1))
    midnight = dt.datetime.combine(day, dt.time(), dt.timezone.utc)
    return day.isoformat(), int(midnight.timestamp())


def count_string(value: object) -> str | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number <= 0 or number != number.to_integral_value():
            return None
        return str(int(number))
    except (InvalidOperation, ValueError, OverflowError):
        return None


def canonical_series(rows: list[dict], asset: str) -> tuple[bytes, dict]:
    occurrences: dict[str, list[tuple[int, str | None]]] = {}
    invalid_time = 0
    invalid_count = 0
    out_of_scope = 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"asset", "time", METRIC}:
            raise ValueError(f"unexpected response fields for metric-only request: {sorted(row) if isinstance(row, dict) else type(row).__name__}")
        if row.get("asset") != asset:
            raise ValueError("response asset does not match its BTC/ETH page row")
        stamp = parse_daily_time(row.get("time"))
        if stamp is None:
            invalid_time += 1
            continue
        day, epoch = stamp
        date = dt.date.fromisoformat(day)
        if date < START or date > END:
            out_of_scope += 1
            continue
        count = count_string(row.get(METRIC))
        if count is None:
            invalid_count += 1
        occurrences.setdefault(day, []).append((epoch, count))
    duplicate_days = sorted(day for day, values in occurrences.items() if len(values) > 1)
    dup_rows = sum(len(occurrences[day]) for day in duplicate_days)
    valid = []
    for day, values in sorted(occurrences.items()):
        if day in duplicate_days:
            continue  # Drop every copy of a duplicated timestamp.
        epoch, count = values[0]
        if count is not None:
            valid.append({"time": epoch, "count": count})
    expected_days = [(START + dt.timedelta(days=i)).isoformat() for i in range((END - START).days + 1)]
    present_days = {dt.datetime.fromtimestamp(row["time"], dt.timezone.utc).date().isoformat() for row in valid}
    missing = [day for day in expected_days if day not in present_days]
    encoded = (json.dumps(valid, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    quality = {
        "sourceRows": sum(len(v) for v in occurrences.values()) + invalid_time + out_of_scope,
        "normalizedRows": len(valid),
        "invalidTimestampRows": invalid_time,
        "invalidCountRows": invalid_count,
        "duplicateTimestampRowsExcludedAllCopies": dup_rows,
        "duplicateDays": duplicate_days,
        "outOfScopeRows": out_of_scope,
        "missingDays": missing,
        "first": valid[0]["time"] if valid else None,
        "last": valid[-1]["time"] if valid else None,
    }
    return encoded, quality


def validate_next_url(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qs(parsed.query)
    if parsed.scheme != "https" or parsed.netloc != "community-api.coinmetrics.io" or parsed.path != "/v4/timeseries/asset-metrics":
        raise ValueError("refusing pagination URL outside official Community metric endpoint")
    if "api_key" in query:
        raise ValueError("pagination URL unexpectedly contains an API key")
    if query.get("metrics") != [METRIC] or query.get("assets") not in ([",".join(ASSETS)], ["btc,eth"], ["eth,btc"]):
        raise ValueError("pagination URL changed the requested metric/asset universe")


def request_once(url: str, page_number: int, total_bytes: int) -> tuple[dict, bytes]:
    if page_number > MAX_GETS:
        raise ValueError(f"GET cap exceeded ({MAX_GETS})")
    started = now_utc()
    record = {"page": page_number, "url": url, "requestStartedUtc": started, "status": None, "receivedUtc": None}
    req = urllib.request.Request(url, headers={"User-Agent": "TraderNova-N12-data/1.0", "Accept-Encoding": "identity"})
    try:
        response = urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as exc:
        body = exc.read(max(0, MAX_BYTES - total_bytes) + 1)
        record.update({"status": exc.code, "receivedUtc": now_utc(), "error": f"HTTP {exc.code}"})
        return record, body
    with response:
        body = response.read(max(0, MAX_BYTES - total_bytes) + 1)
        record.update({"status": response.status, "receivedUtc": now_utc()})
    if total_bytes + len(body) > MAX_BYTES:
        raise ValueError(f"response byte cap exceeded ({MAX_BYTES})")
    return record, body


def empty_manifest() -> dict:
    return {
        "id": "goal-seven-N12-onchain-count-acquisition-v1",
        "protocol": "research/goal-seven/onchain-count-protocol.json",
        "provider": "Coin Metrics Community API v4",
        "endpoint": API,
        "queryScope": {"assets": list(ASSETS), "metric": METRIC, "frequency": "1d",
                       "startInclusive": START.isoformat(), "endInclusive": END.isoformat(),
                       "endTimeSent": "2024-12-31T23:59:59Z", "pageSize": PAGE_SIZE, "apiKeyUsed": False},
        "limits": {"maxGets": MAX_GETS, "maxResponseBytes": MAX_BYTES},
        "pages": [],
        "series": {},
        "getCount": 0,
        "responseBytes": 0,
        "acquisitionComplete": False,
        "pitAvailabilityProven": False,
    }


def acquire() -> int:
    document = empty_manifest()
    query = urllib.parse.urlencode({"assets": ",".join(ASSETS), "metrics": METRIC, "frequency": "1d",
                                   "start_time": START.isoformat() + "T00:00:00Z",
                                   "end_time": END.isoformat() + "T23:59:59Z",
                                   "paging_from": "start", "page_size": str(PAGE_SIZE)})
    next_url = API + "?" + query
    save_manifest(document)
    aggregated = {asset: [] for asset in ASSETS}
    try:
        while next_url:
            if document["getCount"] >= MAX_GETS:
                raise ValueError("20-GET hard cap reached before pagination completed")
            if document["responseBytes"] >= MAX_BYTES:
                raise ValueError("10-MB response-byte hard cap reached before pagination completed")
            if document["getCount"]:
                validate_next_url(next_url)
            page_record, raw = request_once(next_url, document["getCount"] + 1, document["responseBytes"])
            document["getCount"] += 1
            document["responseBytes"] += len(raw)
            page_path = ROOT / "raw" / f"page-{document['getCount']:02d}-http-{page_record['status'] or 'none'}.json"
            immutable_write(page_path, raw)
            page_record.update({"rawPath": Path(os.path.relpath(page_path, Path.cwd())).as_posix(),
                                "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
            document["pages"].append(page_record)
            save_manifest(document)
            if page_record["status"] in (403, 429):
                document["stoppedReason"] = f"HTTP {page_record['status']}; stopped without workaround"
                save_manifest(document)
                print(document["stoppedReason"])
                return 1
            if page_record["status"] != 200:
                document["stoppedReason"] = page_record.get("error", f"HTTP {page_record['status']}")
                save_manifest(document)
                print(document["stoppedReason"])
                return 1
            payload = decode_json(raw)
            if set(payload) - {"data", "next_page_token", "next_page_url"} or not isinstance(payload.get("data"), list):
                raise ValueError("unexpected response envelope; expected only data and pagination metadata")
            for row in payload["data"]:
                if not isinstance(row, dict) or row.get("asset") not in ASSETS:
                    raise ValueError("response includes an unrequested asset or malformed row")
                aggregated[row["asset"]].append(row)
            next_url = payload.get("next_page_url")
            if next_url:
                validate_next_url(next_url)
        normalized = {}
        for asset in ASSETS:
            encoded, quality = canonical_series(aggregated[asset], asset)
            symbol = SYMBOLS[asset]
            path = ROOT / "normalized" / f"{symbol}.json"
            immutable_write(path, encoded)
            normalized[symbol] = {"normalized": {"cachePath": Path(os.path.relpath(path, Path.cwd())).as_posix(),
                                                   "sha256": hashlib.sha256(encoded).hexdigest(),
                                                   "rows": quality["normalizedRows"],
                                                   "first": quality["first"], "last": quality["last"]},
                                  **quality}
        document["series"] = normalized
        document["acquisitionComplete"] = True
        document["pitAvailabilityProven"] = False
        document["interpretation"] = "Daily label D conservatively means activity interval ends D+24h. This is a fixed convention, not proof of publication/revision availability at historical T+48h."
        save_manifest(document)
        write_report(document)
        print({symbol: {"rows": normalized[symbol]["normalized"]["rows"],
                        "missingDays": len(normalized[symbol]["missingDays"])} for symbol in SYMBOLS.values()})
        return 0
    except Exception as exc:
        document["stoppedReason"] = f"{type(exc).__name__}: {exc}"
        save_manifest(document)
        print(document["stoppedReason"])
        return 1


def write_report(document: dict) -> None:
    lines = [
        "# N12 `TxTfrCnt` acquisition and data-quality memo",
        "",
        "Coin Metrics Community API, metric-only request (`TxTfrCnt`, 1d), BTC and ETH, 2021-09-01 through 2024-12-31 inclusive. No prices, returns, signals, triggers, PnL or execution results were requested or calculated.",
        "",
        f"Requests: {document.get('getCount', 0)}/{MAX_GETS}; raw response bytes: {document.get('responseBytes', 0)}/{MAX_BYTES}; complete: {document.get('acquisitionComplete', False)}.",
        "",
        "| Asset | Rows normalized | Missing daily labels | Invalid time/count | Duplicate copies excluded | First/last UTC epoch | SHA-256 normalized |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for asset in ASSETS:
        row = document.get("series", {}).get(SYMBOLS[asset], {})
        norm = row.get("normalized", {})
        lines.append(f"| {asset.upper()} | {norm.get('rows', 0)} | {len(row.get('missingDays', []))} | {row.get('invalidTimestampRows', 0)}/{row.get('invalidCountRows', 0)} | {row.get('duplicateTimestampRowsExcludedAllCopies', 0)} | {norm.get('first')}/{norm.get('last')} | `{norm.get('sha256', '')}` |")
    lines += [
        "",
        "Every missing daily label is enumerated in the manifest. No gaps are filled. Duplicated timestamps are excluded in all copies; counts must be finite, positive integers and are stored as decimal strings. Source timestamps are preserved as UTC epoch seconds only when exactly on the daily midnight grid; no flooring/rounding is applied.",
        "",
        "Raw response bodies are retained byte-for-byte with URL, HTTP status, UTC receipt time, byte length and SHA-256 in the manifest. Only metric `TxTfrCnt` was requested. Raw and normalized files are in the ignored `research/cache/goal-seven/onchain-count/` cache.",
        "",
        "The protocol labels source day D conservatively and treats the activity interval as ending D+24h; its later decision and entry timing are fixed before looking at values. This archive does not contain original publication receipts or immutable historical vintages, so historical availability at the delayed decision remains unproven. `--verify` checks local hashes and coverage only; it makes no network requests.",
        "",
    ]
    Path(REPORT).write_text("\n".join(lines), encoding="utf-8")


def verify_local() -> int:
    doc = json.loads(Path(MANIFEST).read_text(encoding="utf-8"))
    if doc.get("queryScope") != empty_manifest()["queryScope"]:
        raise ValueError("manifest query scope mismatch")
    if doc.get("getCount", 0) != len(doc.get("pages", [])) or doc["getCount"] > MAX_GETS:
        raise ValueError("GET count/page ledger mismatch")
    if doc.get("responseBytes", 0) > MAX_BYTES:
        raise ValueError("manifest exceeds response byte cap")
    aggregated = {asset: [] for asset in ASSETS}
    total_bytes = 0
    for page in doc["pages"]:
        url = page["url"]
        parsed = urllib.parse.urlsplit(url)
        params = urllib.parse.parse_qs(parsed.query)
        if parsed.scheme != "https" or parsed.netloc != "community-api.coinmetrics.io" or parsed.path != "/v4/timeseries/asset-metrics":
            raise ValueError("nonofficial raw URL in manifest")
        if "api_key" in params or params.get("metrics") != [METRIC]:
            raise ValueError("manifest included key or non-metric-only request")
        path = Path(page["rawPath"])
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != page["sha256"] or len(raw) != page["bytes"] or page["status"] != 200:
            raise ValueError(f"raw page integrity/status mismatch: {path}")
        total_bytes += len(raw)
        payload = decode_json(raw)
        if set(payload) - {"data", "next_page_token", "next_page_url"}:
            raise ValueError("unexpected fields in saved metric response envelope")
        for row in payload["data"]:
            if not isinstance(row, dict) or row.get("asset") not in ASSETS:
                raise ValueError("unexpected asset in saved response")
            aggregated[row["asset"]].append(row)
    if total_bytes != doc["responseBytes"]:
        raise ValueError("response byte total mismatch")
    if doc.get("acquisitionComplete"):
        for asset in ASSETS:
            encoded, quality = canonical_series(aggregated[asset], asset)
            series_record = doc["series"][SYMBOLS[asset]]
            record = series_record["normalized"]
            if hashlib.sha256(encoded).hexdigest() != record["sha256"] or quality != {k: series_record[k] for k in quality}:
                raise ValueError(f"normalized hash/coverage mismatch: {asset}")
            if record["rows"] != quality["normalizedRows"]:
                raise ValueError(f"normalized row count mismatch: {asset}")
            if Path(record["cachePath"]).read_bytes() != encoded:
                raise ValueError(f"normalized bytes mismatch: {asset}")
    print("local verification passed; no network access or files changed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="local-only hashes and coverage verification")
    args = parser.parse_args()
    return verify_local() if args.verify else acquire()


if __name__ == "__main__":
    raise SystemExit(main())
