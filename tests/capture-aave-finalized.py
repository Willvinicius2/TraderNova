"""Mock-only boundary tests for the one-shot raw Aave capture."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("capture_aave", ROOT / "scripts" / "capture_aave_finalized.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class MockRPC:
    def __init__(self, mismatch=False, oversize_at=None):
        self.calls, self.mismatch, self.oversize_at = [], mismatch, oversize_at

    def __call__(self, endpoint, payload, timeout):
        req = json.loads(payload)
        self.calls.append(req)
        n = len(self.calls)
        if n == self.oversize_at:
            return 200, b"x: y\r\n", b"z" * (mod.MAX_RESPONSE + 20)
        if req["method"] == "eth_chainId":
            result = "0x1"
        elif req["method"] == "eth_getBlockByNumber":
            if req["params"][0] == "finalized":
                result = {"number": "0x100", "hash": "0x"+'a'*64, "timestamp": "0x1", "parentHash": "0x"+'d'*64}
            else:
                result = {"number": "0x100", "hash": "0x"+('b' if self.mismatch else 'a')*64, "timestamp": "0x1", "parentHash": "0x"+'d'*64}
        else:
            result = "0x" + "0" * 64
        return 200, b"content-type: application/json\r\n", json.dumps({"jsonrpc": "2.0", "id": req["id"], "result": result}).encode()


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.stop = self.base / "STOP"

    def test_sequential_calls_pin_one_block_and_revalidate(self):
        mock = MockRPC()
        target = self.base / "capture"
        self.assertTrue(mod.execute(target, call=mock, stop_path=self.stop))
        calls = mock.calls
        block = "0x100"
        call_requests = [c for c in calls if c["method"] == "eth_call"]
        self.assertEqual(len(call_requests), 6)
        self.assertTrue(all(c["params"][1] == block for c in call_requests))
        self.assertEqual(calls[-2]["params"], [block, False])
        self.assertEqual(calls[-1]["params"], ["finalized", False])
        self.assertTrue((target / "manifest.json").exists())

    def test_stop_existing_lock_and_hash_mismatch_fail_safely(self):
        self.stop.touch()
        dest = self.base / "stopped"
        self.assertFalse(mod.execute(dest, call=MockRPC(), stop_path=self.stop))
        self.stop.unlink()
        lock = self.base / "aave-capture.lock"
        lock.write_text("owned by someone else")
        with self.assertRaises(mod.CaptureFailure):
            mod.execute(self.base / "locked", call=MockRPC(), stop_path=self.stop)
        self.assertEqual(lock.read_text(), "owned by someone else")
        lock.unlink()
        self.assertFalse(mod.execute(self.base / "mismatch", call=MockRPC(mismatch=True), stop_path=self.stop))

    def test_oversize_response_is_bounded_and_digest_recorded(self):
        target = self.base / "oversize"
        self.assertFalse(mod.execute(target, call=MockRPC(oversize_at=1), stop_path=self.stop))
        manifest = json.loads((target / "manifest.json").read_text())
        entry = manifest["requests"][0]
        self.assertEqual(entry["response_bytes"], mod.MAX_RESPONSE + 20)
        self.assertTrue(entry["raw_truncated_to_limit"])
        self.assertEqual((target / entry["raw_files"][2]).stat().st_size, mod.MAX_RESPONSE)

    def test_partial_cache_and_rpc_identity_are_fail_closed(self):
        partial = self.base / 'incomplete'; partial.mkdir()
        (partial / 'raw.bin').write_bytes(b'0' * mod.MAX_CACHE)
        with self.assertRaises(mod.CaptureFailure):
            mod.execute(self.base / 'new', call=MockRPC(), stop_path=self.stop)
        (partial / 'raw.bin').unlink()
        mock = MockRPC()
        def bad_id(endpoint,payload,timeout):
            status, headers, body = mock(endpoint,payload,timeout)
            doc = json.loads(body); doc['id']=999
            return status,headers,json.dumps(doc).encode()
        self.assertFalse(mod.execute(self.base / 'wrong-id',call=bad_id,stop_path=self.stop))


if __name__ == "__main__":
    unittest.main()
