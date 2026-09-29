"""Acquire/checksum-audit Binance USD-M daily open-interest metrics, 2021-12-31 warmup + 2022-2024.

Run from repository root: python scripts/download-goal-open-interest.py
Use --verify for local-only checksum and normalization verification.
No API keys, trading, returns, signals, or performance calculations.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
from decimal import Decimal, InvalidOperation
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
from collections import Counter


S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
DATA = "https://data.binance.vision"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
START = dt.date(2021, 12, 31)  # one warmup day
DEVELOPMENT_START = dt.date(2022, 1, 1)
END_EXCLUSIVE = dt.date(2025, 1, 1)
EXPECTED_PER_DAY = 288
STEP_SECONDS = 300
LEGACY_SOL_NORMALIZED_SHA256 = "2fbb5cb2b8ea7ffee36dd66458037ef2c3bd9146720b05b4f5f27b97e6b84d8f"
GRID_REVISION = {
    "date": "2026-09-28",
    "previousSOLNormalizedSha256": LEGACY_SOL_NORMALIZED_SHA256,
    "previousRule": "Parsed timestamp/date and positive finite OI were retained unless duplicated; source seconds were not required to align to the 300-second grid.",
    "newRule": "Exclude any create_time whose seconds are not divisible by 300 or which has fractional seconds; never round or truncate.",
    "knownExcludedSOLTimes": ["2024-04-02T02:30:02Z", "2024-04-02T06:00:01Z"],
}
ROOT = Path("research/cache/goal-seven/open-interest")
MANIFEST = Path("research/goal-seven/open-interest-data-manifest.json")
REPORT = Path("research/goal-seven/OPEN_INTEREST_ACQUISITION.md")
STOP = threading.Event()
NS = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}
METRIC_RE = re.compile(r"(?P<symbol>[A-Z0-9]+)-metrics-(?P<date>\d{4}-\d{2}-\d{2})\.zip$")
CHECKSUM_RE = re.compile(r"([0-9a-fA-F]{64})\s+\*?(.+)")
REQUIRED = ("create_time", "symbol", "sum_open_interest", "sum_open_interest_value")


def request(url: str) -> bytes:
    for attempt in range(3):
        if STOP.is_set():
            raise RuntimeError("stopped after persistent access/rate-limit error")
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "TraderNova-research-data/1.0"}), timeout=35
            ) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise FileNotFoundError(url) from exc
            if exc.code in (403, 429) and attempt == 2:
                STOP.set()
                raise RuntimeError(f"persistent HTTP {exc.code}; stopped without workaround: {url}") from exc
            if exc.code not in (403, 429, 500, 502, 503, 504):
                raise
        except (TimeoutError, urllib.error.URLError):
            if attempt == 2:
                raise
        time.sleep(2**attempt)
    raise AssertionError("unreachable")


def list_objects(prefix: str) -> list[str]:
    keys: list[str] = []
    token = None
    while True:
        query = {"list-type": "2", "prefix": prefix, "max-keys": 1000}
        if token:
            query["continuation-token"] = token
        root = ET.fromstring(request(S3 + "?" + urllib.parse.urlencode(query)))
        keys.extend(item.text for item in root.findall("s:Contents/s:Key", NS) if item.text)
        if root.findtext("s:IsTruncated", namespaces=NS) != "true":
            return keys
        token = root.findtext("s:NextContinuationToken", namespaces=NS)
        if not token:
            raise ValueError("S3 truncated listing without continuation token")


def write_new(path: Path, raw: bytes) -> None:
    """Create a new immutable cache file; never replace existing bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError(f"immutable cache conflict: {path.as_posix()}")
        return
    temporary = path.with_name(path.name + ".part")
    if temporary.exists():
        raise ValueError(f"stale temporary cache file; inspect manually: {temporary.as_posix()}")
    temporary.write_bytes(raw)
    try:
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def parse_checksum(raw: bytes, filename: str) -> str:
    match = CHECKSUM_RE.fullmatch(raw.decode("utf-8").strip())
    if not match or Path(match.group(2)).name != filename:
        raise ValueError(f"invalid official checksum for {filename}")
    return match.group(1).lower()


def parse_time(text: str) -> dt.datetime:
    # Binance's public metrics CSV stores create_time as a naive string. No
    # explicit timezone is present in that schema; UTC is an assumption and is
    # disclosed as a point-in-time limitation in the manifest/report.
    try:
        value = dt.datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        value = dt.datetime.fromisoformat(text)
        if value.tzinfo is not None:
            raise ValueError("create_time must be timezone-naive in the archive schema")
    return value.replace(tzinfo=dt.timezone.utc)


def on_five_minute_grid(when: dt.datetime) -> bool:
    return when.microsecond == 0 and int(when.timestamp()) % STEP_SECONDS == 0


def compress_missing(values: list[dt.datetime]) -> list[list[str]]:
    if not values:
        return []
    values = sorted(set(values))
    out: list[list[str]] = []
    first = last = values[0]
    step = dt.timedelta(seconds=STEP_SECONDS)
    for value in values[1:]:
        if value == last + step:
            last = value
        else:
            out.append([first.isoformat(), last.isoformat()])
            first = last = value
    out.append([first.isoformat(), last.isoformat()])
    return out


def inspect_zip(path: Path, symbol: str, day: dt.date) -> tuple[dict, list[dict]]:
    quality = {
        "rows": 0, "validOiRows": 0, "invalidOiRows": 0,
        "invalidTimestampRows": 0, "invalidTimestampGridRows": 0, "wrongSymbolRows": 0,
        "duplicateTimestampRows": 0, "outOfOrderRows": 0,
        "intervalGaps": [], "missingExpectedIntervals": [],
        "firstUtc": None, "lastUtc": None, "columns": [],
    }
    parsed: list[tuple[dt.datetime, str, str, str]] = []
    timestamps: list[dt.datetime] = []
    previous = None
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(names) != 1 or archive.testzip() is not None:
            raise ValueError("ZIP must contain one valid CSV member")
        with archive.open(names[0]) as stream:
            reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig", newline=""))
            columns = reader.fieldnames or []
            quality["columns"] = columns
            if len(columns) != len(set(columns)) or not set(REQUIRED).issubset(columns):
                raise ValueError(f"missing/duplicate metrics columns: {columns}")
            for row in reader:
                quality["rows"] += 1
                if None in row or any(row.get(k) is None for k in REQUIRED):
                    quality["invalidOiRows"] += 1
                    continue
                try:
                    when = parse_time(row["create_time"])
                except (ValueError, TypeError):
                    quality["invalidTimestampRows"] += 1
                    continue
                if when.date() != day:
                    quality["invalidTimestampRows"] += 1
                    continue
                if previous is not None and when <= previous:
                    quality["outOfOrderRows"] += 1
                previous = when
                if not on_five_minute_grid(when):
                    quality["invalidTimestampGridRows"] += 1
                    continue
                timestamps.append(when)
                if row["symbol"] != symbol:
                    quality["wrongSymbolRows"] += 1
                    continue
                try:
                    oi = Decimal(row["sum_open_interest"])
                    value = Decimal(row["sum_open_interest_value"])
                    if not oi.is_finite() or not value.is_finite() or oi <= 0 or value <= 0:
                        raise InvalidOperation
                except (InvalidOperation, ValueError):
                    quality["invalidOiRows"] += 1
                    continue
                parsed.append((when, row["sum_open_interest"], row["sum_open_interest_value"], row["symbol"]))
    counts = Counter(timestamps)
    duplicate_times = {when for when, count in counts.items() if count > 1}
    quality["duplicateTimestampRows"] = sum(counts[x] for x in duplicate_times)
    unique_times = sorted(counts)
    quality["firstUtc"] = unique_times[0].isoformat() if unique_times else None
    quality["lastUtc"] = unique_times[-1].isoformat() if unique_times else None
    quality["intervalGaps"] = [
        {"afterUtc": a.isoformat(), "beforeUtc": b.isoformat(), "missingIntervals": int((b-a).total_seconds()/STEP_SECONDS)-1}
        for a, b in zip(unique_times, unique_times[1:])
        if (b-a).total_seconds() != STEP_SECONDS
    ]
    expected = {dt.datetime.combine(day, dt.time(), dt.timezone.utc) + dt.timedelta(seconds=STEP_SECONDS*i)
                for i in range(EXPECTED_PER_DAY)}
    absent = sorted(expected - set(unique_times))
    quality["missingExpectedIntervalCount"] = len(absent)
    quality["missingExpectedIntervals"] = compress_missing(absent)
    valid = [x for x in parsed if x[0] not in duplicate_times]
    quality["validOiRows"] = len(valid)
    quality["excludedDuplicateRowsFromNormalized"] = len(parsed) - len(valid)
    return quality, [{"time": int(t.timestamp()), "sum_open_interest": oi,
                      "sum_open_interest_value": value} for t, oi, value, _ in valid]


def selected_inventory() -> tuple[dict, list[dict]]:
    expected_dates = [START + dt.timedelta(days=i) for i in range((END_EXCLUSIVE-START).days)]
    discovery = {}
    jobs = []
    for symbol in SYMBOLS:
        listed = list_objects(f"data/futures/um/daily/metrics/{symbol}/")
        counts: dict[dt.date, list[str]] = {}
        later = []
        listed_dates = []
        for key in listed:
            name = key.rsplit("/", 1)[-1]
            match = METRIC_RE.fullmatch(name)
            if not match or match.group("symbol") != symbol or not name.endswith(".zip"):
                continue
            day = dt.date.fromisoformat(match.group("date"))
            listed_dates.append(day)
            if day >= END_EXCLUSIVE:
                later.append(day)
            if START <= day < END_EXCLUSIVE:
                counts.setdefault(day, []).append(key)
        discovery[symbol] = {
            "listedMetricZipCount": sum(
                1 for k in listed
                if (m := METRIC_RE.fullmatch(k.rsplit("/", 1)[-1])) and m.group("symbol") == symbol
            ),
            "firstListedDate": min(listed_dates).isoformat() if listed_dates else None,
            "lastListedDate": max(listed_dates).isoformat() if listed_dates else None,
            "laterOnlyInventory": {"count": len(later), "firstDate": min(later).isoformat() if later else None,
                                    "lastDate": max(later).isoformat() if later else None,
                                    "downloaded": False, "read": False},
        }
        for day in expected_dates:
            keys = counts.get(day, [])
            if not keys:
                jobs.append({"symbol": symbol, "date": day.isoformat(), "cachePath": None,
                             "sha256": None, "status": "missing-at-source", "quality": None})
            elif len(keys) != 1:
                jobs.append({"symbol": symbol, "date": day.isoformat(), "cachePath": None,
                             "sha256": None, "status": "ambiguous-listed-keys", "quality": {"keys": len(keys)}})
            else:
                key = keys[0]
                filename = key.rsplit("/", 1)[-1]
                jobs.append({"symbol": symbol, "date": day.isoformat(), "key": key,
                             "checksumListed": key + ".CHECKSUM" in listed,
                             "url": DATA + "/" + key, "checksumUrl": DATA + "/" + key + ".CHECKSUM",
                             "cachePath": (ROOT / "raw" / symbol / filename).as_posix(),
                             "checksumCachePath": (ROOT / "raw" / symbol / (filename + ".CHECKSUM")).as_posix(),
                             "sha256": None, "status": "pending", "quality": None})
    return discovery, jobs


def acquire(item: dict) -> dict:
    result = dict(item)
    try:
        if not item["checksumListed"]:
            raise ValueError("official .CHECKSUM key absent from S3 listing")
        path = Path(item["cachePath"])
        checksum_path = Path(item["checksumCachePath"])
        filename = item["key"].rsplit("/", 1)[-1]
        remote_checksum = request(item["checksumUrl"])
        expected = parse_checksum(remote_checksum, filename)
        if checksum_path.exists():
            cached_check = checksum_path.read_bytes()
            if parse_checksum(cached_check, filename) != expected:
                raise ValueError(f"official checksum changed; immutable cache conflict: {checksum_path.as_posix()}")
        else:
            write_new(checksum_path, remote_checksum)
        if path.exists():
            raw = path.read_bytes()
            observed = hashlib.sha256(raw).hexdigest()
            if observed != expected:
                raise ValueError(f"immutable ZIP checksum conflict: {path.as_posix()}")
        else:
            raw = request(item["url"])
            observed = hashlib.sha256(raw).hexdigest()
            if observed != expected:
                raise ValueError(f"official ZIP checksum mismatch: {item['key']}")
            write_new(path, raw)
        quality, _ = inspect_zip(path, item["symbol"], dt.date.fromisoformat(item["date"]))
        result.update({"sha256": observed, "bytes": path.stat().st_size,
                       "status": "verified", "quality": quality})
    except Exception as exc:
        result.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
    return result


def relative_path(path: Path) -> Path:
    resolved = path.resolve()
    root = Path.cwd().resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"path escapes repository: {path}")
    return resolved


def normalized_bytes(symbol: str, files: list[dict], output=None) -> dict:
    digest = hashlib.sha256()
    count = 0
    excluded_cross_file_rows = 0
    excluded_off_grid_rows = 0
    first = last = None
    def emit(b: bytes):
        digest.update(b)
        if output is not None:
            output.write(b)
    all_points: list[dict] = []
    for item in sorted((x for x in files if x["symbol"] == symbol and x["status"] == "verified"), key=lambda x: x["date"]):
        day = dt.date.fromisoformat(item["date"])
        _, points = inspect_zip(relative_path(Path(item["cachePath"])), symbol, day)
        on_grid = [point for point in points if point["time"] % STEP_SECONDS == 0]
        excluded_off_grid_rows += len(points) - len(on_grid)
        all_points.extend(on_grid)
    timestamp_counts = Counter(point["time"] for point in all_points)
    duplicate_times = {stamp for stamp, n in timestamp_counts.items() if n > 1}
    excluded_cross_file_rows = sum(timestamp_counts[stamp] for stamp in duplicate_times)
    development_start = int(dt.datetime(2021, 12, 31, 23, 55, tzinfo=dt.timezone.utc).timestamp())
    development_last = int(dt.datetime(2024, 12, 31, 22, 55, tzinfo=dt.timezone.utc).timestamp())
    expected_hourly = set(range(development_start, development_last + 1, 3600))
    if len(expected_hourly) != 26304:
        raise AssertionError("unexpected exact-hour coverage grid")
    present_hourly = {point["time"] for point in all_points
                      if point["time"] in expected_hourly and point["time"] not in duplicate_times}
    missing_hourly = sorted(expected_hourly - present_hourly)
    emit(b"[")
    sep = b""
    for point in sorted(all_points, key=lambda p: p["time"]):
        when = point["time"]
        if when in duplicate_times:
            continue  # Exclude every copy; never choose an arbitrary winner.
        if last is not None and when <= last:
            raise ValueError(f"non-increasing unique timestamps in {symbol}: {when}")
        payload = json.dumps(point, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        emit(sep + payload)
        sep = b","; count += 1
        first = when if first is None else first
        last = when
    emit(b"]\n")
    return {"rows": count, "first": first, "last": last, "sha256": digest.hexdigest(),
            "excludedCrossFileRows": excluded_cross_file_rows,
            "excludedOffGridRows": excluded_off_grid_rows,
            "expectedExactHourlyCreateTime": len(expected_hourly),
            "presentExactHourlyCreateTime": len(present_hourly),
            "missingExactHourlyCreateTime": len(missing_hourly),
            "firstMissingExactHourlyCreateTime": missing_hourly[0] if missing_hourly else None,
            "lastMissingExactHourlyCreateTime": missing_hourly[-1] if missing_hourly else None}


def save_manifest(document: dict) -> None:
    path = Path(MANIFEST)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".part")
    temp.write_text(json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def make_manifest(discovery: dict, files: list[dict], normalized: dict | None = None) -> dict:
    expected_days = (END_EXCLUSIVE - START).days
    counts = {}
    for symbol in SYMBOLS:
        rows = [x for x in files if x["symbol"] == symbol]
        verified = [x for x in rows if x["status"] == "verified"]
        counts[symbol] = {
            "expectedDaysIncludingWarmup": expected_days,
            "verifiedArchives": len(verified),
            "missingAtSourceDays": [x["date"] for x in rows if x["status"] == "missing-at-source"],
            "errors": [{"date": x["date"], "status": x["status"], "error": x.get("error")}
                       for x in rows if x["status"] not in ("verified", "missing-at-source")],
            "rowsObserved": sum((x.get("quality") or {}).get("rows", 0) for x in verified),
            "invalidOiRows": sum((x.get("quality") or {}).get("invalidOiRows", 0) for x in verified),
            "invalidTimestampGridRows": sum((x.get("quality") or {}).get("invalidTimestampGridRows", 0) for x in verified),
            "duplicateTimestampRows": sum((x.get("quality") or {}).get("duplicateTimestampRows", 0) for x in verified),
            "missingExpectedIntervals": sum(len((x.get("quality") or {}).get("missingExpectedIntervals", []))
                                             for x in verified),
            "missingExpected5mPoints": sum((x.get("quality") or {}).get("missingExpectedIntervalCount", 0)
                                            for x in verified),
            "normalized": (normalized or {}).get(symbol),
        }
    return {
        "id": "goal-seven-N11-open-interest-v1",
        "purpose": "Official Binance USD-M open-interest acquisition and integrity audit only; no signals, parameters, returns, or performance",
        "venue": "Binance USD-M perpetual, BTCUSDT/ETHUSDT/SOLUSDT",
        "source": S3,
        "archiveBase": DATA,
        "archivePrefix": "data/futures/um/daily/metrics/{symbol}/",
        "scope": {"warmupDate": START.isoformat(), "developmentStartInclusive": DEVELOPMENT_START.isoformat(),
                  "developmentEndInclusive": (END_EXCLUSIVE-dt.timedelta(days=1)).isoformat(),
                  "postEvaluationDownloaded": False, "postEvaluationRead": False},
        "discoverySummary": discovery,
        "timezone": {
            "csvField": "create_time, naive YYYY-MM-DD HH:MM:SS",
            "normalization": "Interpreted as UTC; output epoch seconds.",
            "evidence": "Official REST Open Interest Statistics documents a millisecond timestamp; static archive schema has a naive create_time string but does not explicitly specify its timezone.",
            "status": "UTC assumption; point-in-time use blocked pending explicit confirmation of the archive timezone and publication lag.",
        },
        "sources": {
            "archiveDocumentation": "https://github.com/binance/binance-public-data",
            "usdMOpenInterestRestDocumentation": "https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data",
            "archiveTimezoneEvidence": "UTC is used as an evidenced working convention: the root audit found REST timestamp = UTC-interpreted create_time + 300 s for 11/11 overlapping non-midnight samples per asset (33 total, BTC/ETH/SOL; 2026-09-27). The 00:00 REST sample requires the prior archive day, which was outside that comparison. This is exploratory evidence, not a guarantee of a stable publication/alignment rule.",
            "publicationTimingEvidence": "The official public-data repository documents daily archive availability on the following day; exact intraday publication time is not established here.",
        },
        "cadence": {"expectedSeconds": STEP_SECONDS, "expectedRowsPerFullDay": EXPECTED_PER_DAY,
                    "missingDataPolicy": "Record absent days/gaps; exclude invalid or duplicate points; never interpolate."},
        "checksumPolicy": "Each ZIP SHA-256 must match Binance's adjacent official .CHECKSUM; cache files are immutable and changed official bytes are rejected.",
        "rawFields": "Full original ZIP CSV is retained unchanged; normalized JSON retains only time, sum_open_interest, sum_open_interest_value per symbol.",
        "files": sorted(files, key=lambda x: (x["symbol"], x["date"])),
        "crossFileQuality": (normalized or {}),
        "normalizationRevision": GRID_REVISION,
        "series": counts,
    }


def write_report(document: dict) -> None:
    lines = [
        "# Open interest acquisition — N11",
        "",
        "Aquisição de métricas públicas Binance USD-M para BTCUSDT, ETHUSDT e SOLUSDT. Somente warmup 31/12/2021 e desenvolvimento 2022–2024 foram baixados/lidos. Nenhum resultado, preço de retorno, sinal ou PnL foi calculado.",
        "",
        "| Símbolo | ZIP verificados / esperados | Dias ausentes | Linhas raw | OI inválido | Off-grid excluídos | Duplicatas timestamp | Pontos 5m ausentes | H1 exatos presentes / esperados | Série normalizada |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for symbol, row in document["series"].items():
        norm = row.get("normalized") or {}
        lines.append(f"| {symbol} | {row['verifiedArchives']} / {row['expectedDaysIncludingWarmup']} | {len(row['missingAtSourceDays'])} | {row['rowsObserved']} | {row['invalidOiRows']} | {row['invalidTimestampGridRows']} | {row['duplicateTimestampRows']} | {row['missingExpected5mPoints']} | {norm.get('presentExactHourlyCreateTime', 0)} / {norm.get('expectedExactHourlyCreateTime', 26304)} | {norm.get('rows', 0)} pontos |")
    lines += [
        "",
        "A auditoria diária marca intervalos de 300 s ausentes e pontos inválidos; valores OI não positivos ou não finitos, timestamps fora da grade exata de 300 s (inclusive frações de segundo) e timestamps duplicados são excluídos somente da série normalizada, sem arredondar, truncar ou interpolar. Os ZIPs raw permanecem intactos no cache ignorado `research/cache/goal-seven/open-interest/raw/`; arrays JSON normalizados ficam em `research/cache/goal-seven/open-interest/normalized/`.",
        "## Revisão da regra de timestamp",
        "Série SOL anterior, antes desta correção: SHA-256 `2fbb5cb2b8ea7ffee36dd66458037ef2c3bd9146720b05b4f5f27b97e6b84d8f`. A regra anterior não exigia alinhamento de `create_time` à grade de 300 s. A regra agora exclui qualquer timestamp com segundos não divisíveis por 300 ou fração de segundo. Foram identificados para exclusão `2024-04-02T02:30:02Z` e `2024-04-02T06:00:01Z`; os ZIPs raw permanecem inalterados.",
        "",
        "`create_time` é texto sem timezone no schema do CSV. A auditoria comparativa da tarefa principal encontrou timestamp REST oficial = create_time interpretado UTC + 300 s em 11/11 amostras sobrepostas por ativo (33 total, BTC/ETH/SOL; 2026-09-27). A amostra REST 00:00 exigiria o arquivo do dia anterior, fora daquela comparação. Isso apoia UTC como convenção de trabalho, mas não prova regra estável nem atraso de publicação para todos os anos; point-in-time permanece bloqueado. A normalização aqui mantém o create_time sem deslocamento; observation-end +300 s pertence à integração principal. A cobertura warmup inclui create_time de 31/12/2021; a primeira falta H1 observada é 07/03/2022 15:55 UTC, não no warmup. Arquivos pós-2024 aparecem apenas no resumo de listagem; não foram baixados nem lidos.",
        "",
        "`python scripts/download-goal-open-interest.py --verify` verifica somente arquivos locais.",
        "",
    ]
    Path(REPORT).write_text("\n".join(lines), encoding="utf-8")


def verify_local() -> int:
    document = json.loads(Path(MANIFEST).read_text(encoding="utf-8"))
    if document.get("scope", {}).get("developmentEndInclusive") != "2024-12-31":
        raise ValueError("unexpected manifest evaluation scope")
    files = document.get("files", [])
    expected = (END_EXCLUSIVE - START).days * len(SYMBOLS)
    if len(files) != expected:
        raise ValueError(f"manifest rows {len(files)} != expected {expected}")
    for item in files:
        day = dt.date.fromisoformat(item["date"])
        if day < START or day >= END_EXCLUSIVE:
            raise ValueError("out-of-scope archive listed in acquisition manifest")
        if item["status"] != "verified":
            continue
        path = relative_path(Path(item["cachePath"]))
        check = relative_path(Path(item["checksumCachePath"]))
        name = item["key"].rsplit("/", 1)[-1]
        expected_hash = parse_checksum(check.read_bytes(), name)
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected_hash != observed or observed != item["sha256"]:
            raise ValueError(f"local hash mismatch: {item['cachePath']}")
        quality, _ = inspect_zip(path, item["symbol"], day)
        if quality != item["quality"]:
            raise ValueError(f"local audit changed: {item['cachePath']}")
    for symbol in SYMBOLS:
        record = normalized_bytes(symbol, files)
        expected_norm = document["series"][symbol]["normalized"]
        path = relative_path(Path(expected_norm["path"]))
        if record != {k: expected_norm[k] for k in record}:
            raise ValueError(f"normalized manifest mismatch: {symbol}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError(f"normalized cache hash mismatch: {symbol}")
    print("local verification passed; no network access or files changed")
    return 0


def audit_local_manifest() -> int:
    """Refresh derived quality/coverage metadata from verified local raw archives only."""
    document = json.loads(Path(MANIFEST).read_text(encoding="utf-8"))
    if document.get("scope", {}).get("developmentEndInclusive") != "2024-12-31":
        raise ValueError("unexpected manifest evaluation scope")
    files = document.get("files", [])
    expected = (END_EXCLUSIVE - START).days * len(SYMBOLS)
    if len(files) != expected:
        raise ValueError(f"manifest rows {len(files)} != expected {expected}")
    for item in files:
        if item["status"] != "verified":
            continue
        day = dt.date.fromisoformat(item["date"])
        path = relative_path(Path(item["cachePath"]))
        checksum_path = relative_path(Path(item["checksumCachePath"]))
        name = item["key"].rsplit("/", 1)[-1]
        expected_hash = parse_checksum(checksum_path.read_bytes(), name)
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        if observed != expected_hash or observed != item["sha256"]:
            raise ValueError(f"local hash mismatch: {item['cachePath']}")
        quality, _ = inspect_zip(path, item["symbol"], day)
        item["quality"] = quality
    normalized = {}
    for symbol in SYMBOLS:
        path = relative_path(ROOT / "normalized" / f"{symbol}.json")
        if path.exists():
            old_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            record = normalized_bytes(symbol, files)
            if old_hash != record["sha256"]:
                if symbol != "SOLUSDT" or old_hash != LEGACY_SOL_NORMALIZED_SHA256:
                    raise ValueError(f"normalized cache hash mismatch: {symbol}; refusing to rewrite immutable cache")
                temp = path.with_name(path.name + ".part")
                if temp.exists():
                    raise ValueError(f"stale temporary normalized file; inspect manually: {temp.as_posix()}")
                with temp.open("wb") as stream:
                    record = normalized_bytes(symbol, files, stream)
                if hashlib.sha256(temp.read_bytes()).hexdigest() != record["sha256"]:
                    raise ValueError("new SOL normalized hash mismatch")
                os.replace(temp, path)
        else:
            raise FileNotFoundError(f"expected existing normalized cache: {path}")
        normalized[symbol] = {"path": Path(os.path.relpath(path, Path.cwd())).as_posix(), **record}
    refreshed = make_manifest(document["discoverySummary"], files, normalized)
    refreshed["acquisitionComplete"] = all(x["status"] == "verified" for x in files)
    refreshed["pointInTimeEligible"] = False
    save_manifest(refreshed)
    write_report(refreshed)
    print("local audit metadata refreshed; no network access or cache changes")
    return 0


def acquire_all() -> int:
    discovery, jobs = selected_inventory()
    document = make_manifest(discovery, jobs)
    save_manifest(document)
    listed = sum(1 for x in jobs if x.get("key"))
    print(f"listed in-scope ZIPs={listed}; expected={len(jobs)}; S3 post-scope inventory only, no post-scope downloads/reads", flush=True)
    pending = [x for x in jobs if x.get("key") and x.get("status") == "pending"]
    completed = [x for x in jobs if not x.get("key") or x.get("status") != "pending"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(acquire, item) for item in pending]
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            completed.append(future.result())
            if index % 40 == 0 or index == len(futures):
                document = make_manifest(discovery, completed)
                save_manifest(document)
                print(f"processed={index}/{len(futures)} verified={sum(x['status']=='verified' for x in completed)}", flush=True)
            if STOP.is_set():
                for pending_future in futures:
                    pending_future.cancel()
                break
    if len(completed) < len(jobs):
        done_keys = {(x["symbol"], x["date"]) for x in completed}
        for item in jobs:
            if (item["symbol"], item["date"]) not in done_keys:
                completed.append({"symbol": item["symbol"], "date": item["date"], "cachePath": item.get("cachePath"),
                                  "sha256": None, "status": "not-run-after-persistent-error", "quality": None})
    completed.sort(key=lambda x: (x["symbol"], x["date"]))
    normalized = {}
    for symbol in SYMBOLS:
        path = ROOT / "normalized" / f"{symbol}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(path.name + ".part")
        if temp.exists():
            raise ValueError(f"stale temporary normalized file; inspect manually: {temp.as_posix()}")
        with temp.open("wb") as stream:
            record = normalized_bytes(symbol, completed, stream)
        if path.exists():
            try:
                if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
                    raise ValueError(f"immutable normalized cache conflict: {path.as_posix()}")
            finally:
                temp.unlink(missing_ok=True)
        else:
            os.replace(temp, path)
        normalized[symbol] = {"path": Path(os.path.relpath(path, Path.cwd())).as_posix(), **record}
    document = make_manifest(discovery, completed, normalized)
    document["acquisitionComplete"] = all(x["status"] == "verified" for x in completed)
    document["pointInTimeEligible"] = False
    save_manifest(document)
    write_report(document)
    print("verified by symbol:", {s: document["series"][s]["verifiedArchives"] for s in SYMBOLS})
    print("missing days:", {s: len(document["series"][s]["missingAtSourceDays"]) for s in SYMBOLS})
    return 1 if STOP.is_set() or any(x["status"] not in ("verified", "missing-at-source") for x in completed) else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="verify the existing manifest/cache only; no network")
    parser.add_argument("--audit-local", action="store_true", help="recompute coverage metadata from local verified cache only")
    args = parser.parse_args()
    if args.verify:
        return verify_local()
    if args.audit_local:
        return audit_local_manifest()
    return acquire_all()


if __name__ == "__main__":
    raise SystemExit(main())
