"""Mock tests for the read-only observation collector; no network traffic."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location("goal_observations", Path("scripts/collect-goal-observations.py"))
ENGINE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENGINE)


class FakeResponse:
    status = 200

    def __init__(self, raw: bytes):
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def read(self):
        return self.raw


class ObservationTests(unittest.TestCase):
    def test_13_public_get_endpoints(self):
        specs = ENGINE.endpoints()
        self.assertEqual(len(specs), 13)
        self.assertEqual(specs[0][0], "time")
        self.assertEqual({symbol for _, symbol, _ in specs if symbol}, set(ENGINE.SYMBOLS))
        self.assertTrue(all(url.startswith("https://fapi.binance.com/") for _, _, url in specs))

    def test_append_chain_raw_sha_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            journal = ENGINE.Journal(root)
            a = journal.append({"kind": "cycle-start", "cycleId": "c1", "runId": "r",
                                "startWallNs": 1, "startMonotonicNs": 1})
            b = journal.append({"kind": "request", "cycleId": "c1", "endpoint": "time", "symbol": None,
                                "url": "https://fapi.binance.com/fapi/v1/time", "rawBodyUtf8": "{\"serverTime\":1}",
                                "rawBodyHex": None, "rawBytes": 16,
                                "rawSha256": ENGINE.hashlib.sha256(b'{"serverTime":1}').hexdigest(),
                                "calibration": None})
            self.assertEqual(b["prevHash"], a["recordHash"])
            reopened = ENGINE.Journal(root)
            self.assertEqual(reopened.seq, 2)
            self.assertEqual(reopened.tip, b["recordHash"])
            path = root / "observations.jsonl"
            lines = path.read_text(encoding="utf-8").splitlines()
            corrupt = json.loads(lines[1])
            corrupt["rawBodyUtf8"] = "altered"
            lines[1] = json.dumps(corrupt)
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                ENGINE.Journal(root)

    def test_duplicate_lock_and_disk_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with ENGINE.ExclusiveLock(root / "collector.lock"):
                with self.assertRaises(RuntimeError):
                    with ENGINE.ExclusiveLock(root / "collector.lock"):
                        pass
            journal = ENGINE.Journal(root, max_bytes=100)
            with self.assertRaisesRegex(RuntimeError, "disk limit"):
                journal.append({"kind": "cycle-start", "large": "x" * 200})

    def test_timeout_and_bad_json_are_explicit_and_bounded(self):
        def timeout(*_, **__):
            raise TimeoutError("mock timeout")

        failed = ENGINE.fetch_once("https://fapi.binance.com/fapi/v1/time", 1, timeout)
        self.assertIsNone(failed["status"])
        self.assertIn("TimeoutError", failed["error"])
        self.assertFalse(failed["jsonValid"])
        invalid = ENGINE.fetch_once("https://fapi.binance.com/fapi/v1/time", 1,
                                    lambda *_args, **_kwargs: FakeResponse(b"{broken"))
        self.assertEqual(invalid["status"], 200)
        self.assertFalse(invalid["jsonValid"])
        self.assertIn("invalid JSON", invalid["error"])
        with tempfile.TemporaryDirectory() as temporary:
            journal = ENGINE.Journal(Path(temporary))
            ok, calibration, access_stop = ENGINE.request_and_record(
                journal, "cycle", "time", None, "https://fapi.binance.com/fapi/v1/time",
                1, 0, timeout)
            self.assertFalse(ok)
            self.assertIsNone(calibration)
            self.assertFalse(access_stop)
            self.assertEqual(journal.seq, 1)

    def test_clock_offset_bounds_jump_and_oi_gap(self):
        sample = {"status": 200, "parsed": {"serverTime": 1100},
                  "sendWallNs": 1_000_000_000, "receiveWallNs": 1_200_000_000,
                  "sendMonotonicNs": 5_000_000_000, "receiveMonotonicNs": 5_200_000_000,
                  "clockJumpDuringRequest": False}
        cal = ENGINE.calibration_from_time(sample, None)
        self.assertEqual(cal["offsetLowerMs"], -100)
        self.assertEqual(cal["offsetUpperMs"], 100)
        self.assertFalse(cal["largeAbsoluteOffset"])
        far = dict(sample, sendWallNs=35_000_000_000, receiveWallNs=35_200_000_000)
        self.assertTrue(ENGINE.calibration_from_time(far, None)["largeAbsoluteOffset"])
        later = dict(sample, sendWallNs=5_000_000_000, receiveWallNs=5_200_000_000,
                     sendMonotonicNs=6_000_000_000, receiveMonotonicNs=6_200_000_000)
        changed = ENGINE.calibration_from_time(later, cal)
        self.assertTrue(changed["clockJumpSincePriorCalibration"])
        notes = ENGINE.data_timestamp_notes("openInterestHist", "BTCUSDT",
                                            [{"timestamp": 300_000}, {"timestamp": 900_000}], {})
        self.assertTrue(notes["internal5mGap"])
        self.assertIn("empty", ENGINE.data_timestamp_notes("openInterestHist", "BTCUSDT", [], {})["dataShapeError"])
        self.assertIn("empty", ENGINE.data_timestamp_notes("klines", "BTCUSDT", [], {})["dataShapeError"])

    def test_regressive_pc_clock_preserves_time_response(self):
        raw = b'{"serverTime":1100}'
        result = {"status": 200, "parsed": {"serverTime": 1100},
                  "rawBodyUtf8": raw.decode(), "rawBodyHex": None,
                  "rawSha256": ENGINE.hashlib.sha256(raw).hexdigest(), "rawBytes": len(raw),
                  "jsonValid": True, "error": None,
                  "sendWallNs": 2_000_000_000, "receiveWallNs": 1_000_000_000,
                  "sendMonotonicNs": 5_000_000_000, "receiveMonotonicNs": 5_200_000_000,
                  "clockJumpDuringRequest": True, "wallMinusMonotonicElapsedNs": -1_200_000_000}
        self.assertIsNone(ENGINE.calibration_from_time(result, None))
        with tempfile.TemporaryDirectory() as temporary:
            journal = ENGINE.Journal(Path(temporary))
            with mock.patch.object(ENGINE, "fetch_once", return_value=result):
                ok, calibration, stop = ENGINE.request_and_record(
                    journal, "cycle", "time", None, ENGINE.endpoints()[0][2], 1, 0)
            self.assertFalse(ok)
            self.assertIsNone(calibration)
            self.assertFalse(stop)
            row = json.loads(journal.path.read_text(encoding="utf-8"))
            self.assertIn("regressed", row["calibrationError"])
            self.assertEqual(row["rawSha256"], result["rawSha256"])
            self.assertEqual(ENGINE.Journal(Path(temporary)).seq, 1)

    def test_terminal_status_stop_file_finite_and_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "STOP").write_text("stop", encoding="utf-8")
            self.assertEqual(ENGINE.collect(root=root, cycles=1), 0)
            stopped = json.loads((root / "status.json").read_text(encoding="utf-8"))
            self.assertFalse(stopped["running"])
            self.assertEqual(stopped["stopReason"], "stop-file")
            self.assertEqual(stopped["maxHours"], 24)
            self.assertIsNotNone(stopped["endedUtc"])
            (root / "STOP").unlink()

            def fake_cycle(journal, run_id, *_args):
                journal.append({"kind": "cycle-start", "cycleId": "mock-cycle", "runId": run_id,
                                "startWallNs": ENGINE.time.time_ns(),
                                "startMonotonicNs": ENGINE.time.monotonic_ns()})
                summary = {"kind": "cycle-end", "cycleId": "mock-cycle", "runId": run_id,
                           "endUtc": ENGINE.utc_iso(ENGINE.time.time_ns()),
                           "successfulEndpoints": 13, "attemptedEndpoints": 13,
                           "failedEndpoints": [], "flags": [], "stopReason": None}
                journal.append(summary)
                return summary, False

            with mock.patch.object(ENGINE, "run_cycle", side_effect=fake_cycle):
                self.assertEqual(ENGINE.collect(root=root, cycles=1), 0)
            finite = json.loads((root / "status.json").read_text(encoding="utf-8"))
            self.assertFalse(finite["running"])
            self.assertEqual(finite["stopReason"], "cycle-limit")
            self.assertEqual(finite["runCyclesCompleted"], 1)
            self.assertEqual(finite["cyclesCompleted"], 1)

            with mock.patch.object(ENGINE, "run_cycle", side_effect=RuntimeError("mock failure")):
                with self.assertRaisesRegex(RuntimeError, "mock failure"):
                    ENGINE.collect(root=root, cycles=1)
            failed = json.loads((root / "status.json").read_text(encoding="utf-8"))
            self.assertFalse(failed["running"])
            self.assertEqual(failed["stopReason"], "failed:RuntimeError")

    def test_cycle_overrun_skips_catchup_slots(self):
        interval = 300_000_000_000
        self.assertEqual(ENGINE.next_scheduled_start(0, interval, 10_000_000_000), (interval, 0))
        self.assertEqual(ENGINE.next_scheduled_start(0, interval, 350_000_000_000), (2 * interval, 1))


if __name__ == "__main__":
    unittest.main()
