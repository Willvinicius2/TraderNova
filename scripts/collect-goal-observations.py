"""Read-only Binance USD-M observation collector; never sends orders.

Run from repository root. One bounded network smoke: --cycles 1.
Raw response bytes are preserved verbatim as UTF-8 text in an append-only
hash-chained JSONL journal. This is observational evidence, not a PIT-certified
exchange feed or a strategy result.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
import uuid


BASE = "https://fapi.binance.com"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
ROOT = Path("research/cache/goal-seven/observations")
MAX_BYTES = 1_073_741_824
ZERO_HASH = "0" * 64
JUMP_NS = 1_000_000_000
USER_AGENT = "TraderNova-research-observations/1.0"


def utc_iso(wall_ns: int) -> str:
    return dt.datetime.fromtimestamp(wall_ns / 1e9, dt.timezone.utc).isoformat(timespec="microseconds")


def canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def storage_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file()) if root.exists() else 0


def check_capacity(root: Path, growth: int, max_bytes: int) -> None:
    if growth < 0 or storage_bytes(root) + growth > max_bytes:
        raise RuntimeError(f"observation cache disk limit {max_bytes} bytes reached")


class ExclusiveLock:
    """Operating-system exclusive lock; the lock file itself is retained."""

    def __init__(self, path: Path):
        self.path = path
        self.file = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open("a+b")
        self.file.seek(0, os.SEEK_END)
        if self.file.tell() == 0:
            self.file.write(b"0")
            self.file.flush()
        self.file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as exc:
            self.file.close()
            self.file = None
            raise RuntimeError(f"another observation collector holds {self.path}") from exc
        return self

    def __exit__(self, *_):
        if self.file is not None:
            self.file.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
            self.file.close()


class Journal:
    def __init__(self, root: Path, max_bytes: int = MAX_BYTES):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = root / "observations.jsonl"
        self.max_bytes = max_bytes
        self.seq = 0
        self.tip = ZERO_HASH
        self.last_cycle_start_wall_ns = None
        self.last_cycle_start_mono_ns = None
        self.last_cycle_run_id = None
        self.last_calibration = None
        self.last_oi_timestamp = {}
        self.completed_cycles = 0
        self.last_cycle_summary = None
        self.last_payload = None
        self._verify_existing()

    def _verify_existing(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("rb") as source:
            for raw in source:
                if not raw.endswith(b"\n"):
                    raise RuntimeError("journal has incomplete final line; preserve it for audit")
                row = json.loads(raw)
                stated_hash = row.pop("recordHash")
                if row["seq"] != self.seq + 1 or row["prevHash"] != self.tip:
                    raise RuntimeError("journal sequence/hash-chain discontinuity")
                actual_hash = hashlib.sha256(bytes.fromhex(self.tip) + canonical(row)).hexdigest()
                if actual_hash != stated_hash:
                    raise RuntimeError("journal content hash mismatch")
                if row["kind"] == "request":
                    original = (row["rawBodyUtf8"].encode("utf-8") if row["rawBodyUtf8"] is not None
                                else bytes.fromhex(row["rawBodyHex"]))
                    if len(original) != row["rawBytes"] or hashlib.sha256(original).hexdigest() != row["rawSha256"]:
                        raise RuntimeError("journal raw response SHA/length mismatch")
                self.seq += 1
                self.tip = stated_hash
                self._remember(row)

    def _remember(self, row: dict) -> None:
        if row["kind"] == "cycle-start":
            self.last_cycle_start_wall_ns = row["startWallNs"]
            self.last_cycle_start_mono_ns = row["startMonotonicNs"]
            self.last_cycle_run_id = row["runId"]
        elif row["kind"] == "cycle-end":
            self.completed_cycles += 1
            self.last_cycle_summary = row
        elif row["kind"] == "request" and row.get("endpoint") == "time" and row.get("calibration"):
            self.last_calibration = row["calibration"]
        elif row["kind"] == "request" and row.get("endpoint") == "openInterestHist":
            latest = row.get("latestDataTimestampMs")
            if latest is not None:
                self.last_oi_timestamp[row["symbol"]] = latest

    def append(self, payload: dict) -> dict:
        row = dict(payload, seq=self.seq + 1, prevHash=self.tip)
        digest = hashlib.sha256(bytes.fromhex(self.tip) + canonical(row)).hexdigest()
        row["recordHash"] = digest
        line = canonical(row) + b"\n"
        check_capacity(self.root, len(line), self.max_bytes)
        descriptor = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            written = os.write(descriptor, line)
            if written != len(line):
                raise RuntimeError("partial journal write; stop and inspect evidence")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        self.seq += 1
        self.tip = digest
        self.last_payload = payload
        self._remember(payload)
        return row


def endpoints() -> list[tuple[str, str | None, str]]:
    specs = [("time", None, BASE + "/fapi/v1/time")]
    for symbol in SYMBOLS:
        specs.extend([
            ("openInterestHist", symbol, BASE + f"/futures/data/openInterestHist?symbol={symbol}&period=5m&limit=12"),
            ("klines", symbol, BASE + f"/fapi/v1/klines?symbol={symbol}&interval=1h&limit=3"),
            ("bookTicker", symbol, BASE + f"/fapi/v1/ticker/bookTicker?symbol={symbol}"),
            ("premiumIndex", symbol, BASE + f"/fapi/v1/premiumIndex?symbol={symbol}"),
        ])
    return specs


def fetch_once(url: str, timeout_sec: float, opener=urllib.request.urlopen) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    send_wall = time.time_ns()
    send_mono = time.monotonic_ns()
    status = None
    raw = b""
    error = None
    try:
        with opener(request, timeout=timeout_sec) as response:
            status = response.status
            raw = response.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read()
        error = f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        error = f"{type(exc).__name__}: {exc}"
    receive_mono = time.monotonic_ns()
    receive_wall = time.time_ns()
    try:
        body = raw.decode("utf-8")
    except UnicodeDecodeError:
        body = None
        error = error or "response is not UTF-8 JSON"
    parsed = None
    json_valid = False
    if body is not None and raw:
        try:
            parsed = json.loads(body)
            json_valid = True
        except (json.JSONDecodeError, ValueError) as exc:
            error = error or f"invalid JSON: {exc}"
    elif not raw and status == 200:
        error = "empty JSON response"
    if status != 200 and error is None:
        error = f"HTTP {status}"
    clock_delta = (receive_wall - send_wall) - (receive_mono - send_mono)
    return {
        "status": status, "rawBodyUtf8": body, "rawBodyHex": raw.hex() if body is None else None,
        "rawSha256": hashlib.sha256(raw).hexdigest(), "rawBytes": len(raw),
        "jsonValid": json_valid, "parsed": parsed, "error": error,
        "sendWallNs": send_wall, "receiveWallNs": receive_wall,
        "sendUtc": utc_iso(send_wall), "receiveUtc": utc_iso(receive_wall),
        "sendMonotonicNs": send_mono, "receiveMonotonicNs": receive_mono,
        "clockJumpDuringRequest": abs(clock_delta) > JUMP_NS,
        "wallMinusMonotonicElapsedNs": clock_delta,
    }


def calibration_from_time(result: dict, previous: dict | None) -> dict | None:
    body = result["parsed"]
    if result["status"] != 200 or not isinstance(body, dict) or type(body.get("serverTime")) is not int:
        return None
    server_ms = body["serverTime"]
    lower = server_ms - result["receiveWallNs"] / 1_000_000
    upper = server_ms - result["sendWallNs"] / 1_000_000
    if lower > upper:
        return None  # Clock moved backwards; the response is still journaled.
    calibration = {
        "serverTimeMs": server_ms,
        "offsetLowerMs": lower,
        "offsetUpperMs": upper,
        "roundTripMonotonicMs": (result["receiveMonotonicNs"] - result["sendMonotonicNs"]) / 1_000_000,
        "receiveWallNs": result["receiveWallNs"],
        "receiveMonotonicNs": result["receiveMonotonicNs"],
        "clockJumpDuringRequest": result["clockJumpDuringRequest"],
        "clockJumpSincePriorCalibration": False,
        "offsetShiftOverOneSecond": False,
        "largeAbsoluteOffset": lower > 5000 or upper < -5000,
    }
    if previous is not None:
        wall_elapsed = result["receiveWallNs"] - previous["receiveWallNs"]
        monotonic_elapsed = result["receiveMonotonicNs"] - previous["receiveMonotonicNs"]
        # Monotonic values are only comparable within the same boot; a huge
        # disagreement is flagged rather than interpreted as certified time.
        calibration["clockJumpSincePriorCalibration"] = abs(wall_elapsed - monotonic_elapsed) > JUMP_NS
        calibration["offsetShiftOverOneSecond"] = (
            lower > previous["offsetUpperMs"] + 1000 or upper < previous["offsetLowerMs"] - 1000)
    return calibration


def data_timestamp_notes(endpoint: str, symbol: str | None, parsed, prior_oi: dict) -> dict:
    if endpoint == "openInterestHist":
        if not isinstance(parsed, list):
            return {"dataShapeError": "expected OI array"}
        if not parsed:
            return {"dataShapeError": "empty OI array", "dataRows": 0}
        try:
            timestamps = [int(item["timestamp"]) for item in parsed]
        except (TypeError, KeyError, ValueError):
            return {"dataShapeError": "OI timestamp missing/invalid"}
        internal_gap = any(right - left != 300_000 for left, right in zip(timestamps, timestamps[1:]))
        prior = prior_oi.get(symbol)
        between_gap = prior is not None and timestamps and timestamps[0] > prior + 300_000
        return {"dataRows": len(parsed), "firstDataTimestampMs": timestamps[0] if timestamps else None,
                "latestDataTimestampMs": timestamps[-1] if timestamps else None,
                "internal5mGap": internal_gap, "gapSincePrior5m": between_gap}
    if endpoint == "klines":
        if not isinstance(parsed, list):
            return {"dataShapeError": "expected kline array"}
        if not parsed:
            return {"dataShapeError": "empty kline array", "dataRows": 0}
        try:
            stamps = [int(item[0]) for item in parsed]
        except (TypeError, IndexError, ValueError):
            return {"dataShapeError": "kline open time missing/invalid"}
        return {"dataRows": len(parsed), "latestKlineOpenTimeMs": stamps[-1] if stamps else None,
                "internalH1Gap": any(right - left != 3_600_000 for left, right in zip(stamps, stamps[1:]))}
    return {}


def request_and_record(journal: Journal, cycle_id: str, endpoint: str, symbol: str | None,
                       url: str, timeout_sec: float, retries: int,
                       opener=urllib.request.urlopen) -> tuple[bool, dict | None, bool]:
    """Return (success, calibration, rate/access stop). Every attempt is saved."""
    for attempt in range(retries + 1):
        check_capacity(journal.root, 65_536, journal.max_bytes)
        result = fetch_once(url, timeout_sec, opener)
        prior_calibration = journal.last_calibration
        calibration = calibration_from_time(result, prior_calibration) if endpoint == "time" else None
        calibration_error = None
        if endpoint == "time" and calibration is None and result["status"] == 200 and result["jsonValid"]:
            calibration_error = ("PC wall clock regressed during calibration"
                                 if result["receiveWallNs"] < result["sendWallNs"]
                                 else "invalid serverTime calibration payload")
        notes = data_timestamp_notes(endpoint, symbol, result["parsed"], journal.last_oi_timestamp) if result["parsed"] is not None else {}
        row = {
            "kind": "request", "cycleId": cycle_id, "endpoint": endpoint,
            "symbol": symbol, "url": url, "method": "GET", "attempt": attempt + 1,
            **{key: value for key, value in result.items() if key != "parsed"},
            **notes,
            "calibration": calibration,
            "calibrationError": calibration_error,
        }
        journal.append(row)
        success = result["status"] == 200 and result["jsonValid"] and not notes.get("dataShapeError")
        if endpoint == "time":
            success = success and calibration is not None
        if success:
            return True, calibration, False
        if attempt == retries or result["status"] not in (None, 403, 429, 500, 502, 503, 504) and result["jsonValid"]:
            return False, None, result["status"] in (403, 429)
        time.sleep(min(2 ** attempt, 4))
    raise AssertionError("unreachable")


def write_status(journal: Journal, status: dict) -> None:
    target = journal.root / "status.json"
    payload = canonical(status) + b"\n"
    old_size = target.stat().st_size if target.exists() else 0
    check_capacity(journal.root, max(0, len(payload) - old_size) + len(payload), journal.max_bytes)
    temporary = target.with_name("status.json.tmp")
    with temporary.open("wb") as out:
        out.write(payload)
        out.flush()
        os.fsync(out.fileno())
    os.replace(temporary, target)


def run_cycle(journal: Journal, run_id: str, interval_sec: float, timeout_sec: float,
              retries: int, stop_file: Path, deadline_mono_ns: int,
              planned_start_mono_ns: int) -> tuple[dict, bool]:
    start_wall = time.time_ns()
    start_mono = time.monotonic_ns()
    prior_wall = journal.last_cycle_start_wall_ns
    prior_mono = journal.last_cycle_start_mono_ns
    prior_run = journal.last_cycle_run_id
    wall_gap = None if prior_wall is None else (start_wall - prior_wall) / 1e9
    late_sec = max(0.0, (start_mono - planned_start_mono_ns) / 1e9)
    flags = []
    if wall_gap is not None and (wall_gap < 0 or wall_gap > 1.5 * interval_sec):
        flags.append("pc-wall-observation-gap")
    if prior_run == run_id and prior_wall is not None and prior_mono is not None:
        if abs((start_wall - prior_wall) - (start_mono - prior_mono)) > JUMP_NS:
            flags.append("pc-clock-jump-between-cycles")
    cycle_id = f"{utc_iso(start_wall)}-{uuid.uuid4().hex[:8]}"
    journal.append({"kind": "cycle-start", "cycleId": cycle_id, "runId": run_id,
                    "startWallNs": start_wall, "startUtc": utc_iso(start_wall),
                    "startMonotonicNs": start_mono,
                    "lateFromPlannedSeconds": late_sec,
                    "missedIntervals": int(late_sec // interval_sec)})
    succeeded = 0
    attempted_endpoints = 0
    failed = []
    calibration = None
    stop_reason = None
    for endpoint, symbol, url in endpoints():
        if stop_file.exists():
            stop_reason = "stop-file"
            break
        if time.monotonic_ns() >= deadline_mono_ns:
            stop_reason = "max-hours"
            break
        attempted_endpoints += 1
        success, current_calibration, access_stop = request_and_record(
            journal, cycle_id, endpoint, symbol, url, timeout_sec, retries)
        latest = journal.last_payload
        if latest.get("clockJumpDuringRequest"):
            flags.append("pc-clock-jump-during-request")
        if latest.get("internal5mGap") or latest.get("gapSincePrior5m"):
            flags.append("open-interest-5m-gap")
        if latest.get("internalH1Gap"):
            flags.append("kline-H1-gap")
        if success:
            succeeded += 1
            if endpoint == "time":
                calibration = current_calibration
                if calibration["clockJumpSincePriorCalibration"] or calibration["offsetShiftOverOneSecond"]:
                    flags.append("calibration-clock-or-offset-shift")
                if calibration["largeAbsoluteOffset"]:
                    flags.append("pc-clock-offset-over-five-seconds")
        else:
            failed.append(f"{endpoint}/{symbol or 'server'}")
            if endpoint == "time":
                flags.append("calibration-lost")
        if access_stop:
            stop_reason = "persistent-403-or-429"
            break
    if calibration is None and "calibration-lost" not in flags:
        flags.append("calibration-lost")
    end_wall = time.time_ns()
    summary = {"kind": "cycle-end", "cycleId": cycle_id, "runId": run_id,
               "endWallNs": end_wall, "endUtc": utc_iso(end_wall),
               "endMonotonicNs": time.monotonic_ns(),
               "expectedEndpoints": 13, "attemptedEndpoints": attempted_endpoints,
               "successfulEndpoints": succeeded, "failedEndpoints": failed,
               "calibrationAvailable": calibration is not None,
               "offsetLowerMs": calibration["offsetLowerMs"] if calibration else None,
               "offsetUpperMs": calibration["offsetUpperMs"] if calibration else None,
               "flags": sorted(set(flags)), "stopReason": stop_reason}
    journal.append(summary)
    return summary, stop_reason is not None


def next_scheduled_start(previous_start_ns: int, interval_ns: int, now_ns: int) -> tuple[int, int]:
    """Skip missed slots after an overlong cycle; never run a catch-up burst."""
    due = previous_start_ns + interval_ns
    skipped = max(0, (now_ns - due + interval_ns - 1) // interval_ns)
    return due + skipped * interval_ns, skipped


def status_snapshot(journal: Journal, lifecycle: dict) -> dict:
    summary = journal.last_cycle_summary
    return {**lifecycle,
            "purpose": "public Binance USD-M observations only; no signals, PnL or orders",
            "cyclesCompleted": journal.completed_cycles,
            "lastCycle": ({key: value for key, value in summary.items()
                           if key not in ("kind", "runId", "endWallNs", "endMonotonicNs")}
                          if summary else None),
            "journalRecords": journal.seq, "journalTipHash": journal.tip,
            "cacheBytes": storage_bytes(journal.root)}


def collect(root: Path = ROOT, cycles: int | None = None, interval_sec: float = 300,
            max_hours: float = 24, max_bytes: int = MAX_BYTES,
            timeout_sec: float = 8, retries: int = 1,
            stop_file: Path | None = None) -> int:
    if cycles is not None and cycles < 1:
        raise ValueError("--cycles must be positive")
    if not 60 <= interval_sec or not 0 < max_hours <= 24:
        raise ValueError("interval must be at least 60s and max-hours in (0,24]")
    if not 0 < max_bytes <= MAX_BYTES or not 1 <= timeout_sec <= 30 or not 0 <= retries <= 2:
        raise ValueError("invalid disk/timeout/retry bound")
    stop_file = stop_file or root / "STOP"
    with ExclusiveLock(root / "collector.lock"):
        journal = Journal(root, max_bytes)
        run_id = uuid.uuid4().hex
        deadline = time.monotonic_ns() + int(max_hours * 3600 * 1e9)
        next_due = time.monotonic_ns()
        start_wall = time.time_ns()
        lifecycle = {"running": True, "pid": os.getpid(), "runId": run_id,
                     "startedUtc": utc_iso(start_wall), "startedWallNs": start_wall,
                     "endedUtc": None, "endedWallNs": None, "stopReason": None,
                     "maxHours": max_hours, "intervalSeconds": interval_sec,
                     "runCyclesCompleted": 0, "skippedScheduledStarts": 0}
        done = 0
        had_failures = False
        interrupted = False
        try:
            write_status(journal, status_snapshot(journal, lifecycle))
            while cycles is None or done < cycles:
                if stop_file.exists() or time.monotonic_ns() >= deadline:
                    break
                while time.monotonic_ns() < next_due:
                    if stop_file.exists() or time.monotonic_ns() >= deadline:
                        break
                    remaining_ns = next_due - time.monotonic_ns()
                    if remaining_ns > 0:
                        time.sleep(min(1.0, remaining_ns / 1e9))
                if stop_file.exists() or time.monotonic_ns() >= deadline:
                    break
                summary, stop = run_cycle(journal, run_id, interval_sec, timeout_sec,
                                          retries, stop_file, deadline, next_due)
                done += 1
                lifecycle["runCyclesCompleted"] = done
                had_failures |= bool(summary["failedEndpoints"] or summary["flags"] or summary["attemptedEndpoints"] != 13)
                write_status(journal, status_snapshot(journal, lifecycle))
                print(f"cycle {done}: {summary['successfulEndpoints']}/13 responses; flags={','.join(summary['flags']) or 'none'}", flush=True)
                if stop:
                    lifecycle["stopReason"] = summary["stopReason"]
                    break
                next_due, skipped = next_scheduled_start(
                    journal.last_cycle_start_mono_ns, int(interval_sec * 1e9), time.monotonic_ns())
                lifecycle["skippedScheduledStarts"] += skipped
            if lifecycle["stopReason"] is None:
                lifecycle["stopReason"] = ("stop-file" if stop_file.exists() else
                                            "max-hours" if time.monotonic_ns() >= deadline else "cycle-limit")
        except KeyboardInterrupt:
            interrupted = True
            lifecycle["stopReason"] = "keyboard-interrupt"
        except Exception as exc:
            lifecycle["stopReason"] = f"failed:{type(exc).__name__}"
            raise
        finally:
            end_wall = time.time_ns()
            lifecycle.update(running=False, endedUtc=utc_iso(end_wall), endedWallNs=end_wall)
            try:
                write_status(journal, status_snapshot(journal, lifecycle))
            except Exception as exc:
                print(f"could not write terminal status: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 130 if interrupted else 1 if had_failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles", type=int, default=None, help="finite number of cycles, e.g. 1 for smoke")
    parser.add_argument("--interval-sec", type=float, default=300)
    parser.add_argument("--max-hours", type=float, default=24)
    parser.add_argument("--max-bytes", type=int, default=MAX_BYTES)
    parser.add_argument("--timeout-sec", type=float, default=8)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--stop-file", type=Path, default=None)
    args = parser.parse_args()
    return collect(cycles=args.cycles, interval_sec=args.interval_sec,
                   max_hours=args.max_hours, max_bytes=args.max_bytes,
                   timeout_sec=args.timeout_sec, retries=args.retries,
                   stop_file=args.stop_file)


if __name__ == "__main__":
    raise SystemExit(main())
