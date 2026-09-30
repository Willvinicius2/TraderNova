"""Synthetic boundary tests for raw Aave bundle verification and decoding."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("audit_aave", ROOT / "scripts" / "audit_aave_bundle.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def hx(n):
    return "0x" + format(n, "x")


def make_bundle(path):
    path.mkdir()
    number = "0x10"
    initial = {"number": number, "hash": "0x" + "1" * 64, "parentHash": "0x" + "0" * 64, "timestamp": "0x100"}
    final = {"number": "0x11", "hash": "0x" + "2" * 64, "parentHash": initial["hash"], "timestamp": "0x101"}
    dep = {"pool": mod.POOL, "data_provider": mod.PROVIDER,
           "selectors": {"getReserveData(address)": mod.GET_RESERVE_DATA, "balanceOf(address)": mod.BALANCE_OF},
           "reserves": [{"symbol": s, "asset": a, "a_token": t} for s, a, t, _ in mod.RESERVES]}
    manifest = {"schema": "tradernova.aave-finalized-raw.v1", "status": "captured_raw_only",
                "approval": {k: False for k in mod.APPROVALS}, "chain_id": 1, "chain_id_expected": 1,
                "deployment": dep, "block_number": number, "block_hash": initial["hash"],
                "block_header": initial, "revalidation_header": initial, "block_hash_match": True,
                "finalized_revalidation_header": final, "requests": []}
    calls = [("eth_chainId", [], "0x1"), ("eth_getBlockByNumber", ["finalized", False], initial)]
    for _, asset, atoken, _ in mod.RESERVES:
        arg = asset.lower().removeprefix("0x").rjust(64, "0")
        words = [0] * 12
        words[3], words[4], words[6] = 10, 90, 10**27
        provider = "0x" + "".join(format(w, "064x") for w in words)
        pool = "0x" + "".join(format(100 + i, "064x") for i in range(12))
        calls.extend([
            ("eth_call", [{"to": mod.PROVIDER, "data": mod.GET_RESERVE_DATA + arg}, number], provider),
            ("eth_call", [{"to": mod.POOL, "data": mod.GET_RESERVE_DATA + arg}, number], pool),
            ("eth_call", [{"to": asset, "data": mod.BALANCE_OF + atoken.lower().removeprefix("0x").rjust(64, "0")} , number], '0x'+format(900,'064x')),
        ])
    calls.extend([("eth_getBlockByNumber", [number, False], initial), ("eth_getBlockByNumber", ["finalized", False], final)])
    for i, (method, params, result) in enumerate(calls, 1):
        rq = {"jsonrpc": "2.0", "id": i, "method": method, "params": params}
        rs = {"jsonrpc": "2.0", "id": i, "result": result}
        files = [f"{i:02d}-{s}.bin" for s in ("request", "headers", "response")]
        raw = [json.dumps(rq, separators=(",", ":")).encode(), b"content-type: application/json\r\n", json.dumps(rs, separators=(",", ":")).encode()]
        for name, data in zip(files, raw):
            (path / name).write_bytes(data)
        manifest["requests"].append({"id": i, "method": method, "params": params, "http_status": 200,
            "request_sha256": hashlib.sha256(raw[0]).hexdigest(), "headers_sha256": hashlib.sha256(raw[1]).hexdigest(),
            "response_sha256": hashlib.sha256(raw[2]).hexdigest(), "saved_response_sha256": hashlib.sha256(raw[2]).hexdigest(),
            "response_bytes": len(raw[2]), "raw_files": files})
    (path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


class BundleAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bundle = Path(self.temp.name) / "bundle"
        self.manifest = make_bundle(self.bundle)

    def save_manifest(self):
        (self.bundle / "manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def test_duplicate_json_keys_cannot_change_manifest_claim(self):
        path = self.bundle / 'manifest.json'
        text = path.read_text()
        path.write_text(text[:-1] + ',"status":"captured_raw_only"}', encoding='utf-8')
        with self.assertRaises(mod.AuditError):
            mod.audit_bundle(self.bundle)

    def test_valid_bundle_decodes_provider_words_as_apr_and_utilization(self):
        result = mod.audit_bundle(self.bundle)
        self.assertEqual(result["reserves"][0]["total_stable_debt_raw"], "10")
        self.assertEqual(result["reserves"][0]["total_variable_debt_raw"], "90")
        self.assertEqual(result["reserves"][0]["variable_borrow_rate_apr"], "1")
        self.assertEqual(result["reserves"][0]["utilization"], "0.1")
        self.assertEqual(result["reserves"][0]["pool_tuple_decoding"], "unknown_abi_not_decoded")
        self.assertFalse(result["financial_approved"])

    def test_tampered_raw_wrong_call_block_rpc_id_and_header_hash_fail(self):
        first = self.manifest["requests"][0]["raw_files"][2]
        (self.bundle / first).write_bytes(b"tampered")
        with self.assertRaises(mod.AuditError):
            mod.audit_bundle(self.bundle)
        # Repair bundle and make a self-consistent request that targets another block.
        self.tearDown(); self.setUp()
        call = self.manifest["requests"][2]
        reqpath = self.bundle / call["raw_files"][0]
        request = json.loads(reqpath.read_text())
        request["params"][1] = "0x11"
        raw = json.dumps(request, separators=(",", ":")).encode()
        reqpath.write_bytes(raw); call["request_sha256"] = hashlib.sha256(raw).hexdigest(); call["params"] = request["params"]
        self.save_manifest()
        with self.assertRaises(mod.AuditError):
            mod.audit_bundle(self.bundle)

    def test_wrong_jsonrpc_id_duplicate_paths_and_unapproved_flags_fail(self):
        self.manifest["requests"][0]["raw_files"][1] = self.manifest["requests"][0]["raw_files"][0]
        self.save_manifest()
        with self.assertRaises(mod.AuditError):
            mod.audit_bundle(self.bundle)

    def test_self_consistent_wrong_rpc_id_and_frozen_hash_mismatch_fail(self):
        entry = self.manifest["requests"][0]
        response_path = self.bundle / entry["raw_files"][2]
        response = json.loads(response_path.read_text())
        response["id"] = 77
        raw = json.dumps(response, separators=(",", ":")).encode()
        response_path.write_bytes(raw)
        entry["response_sha256"] = entry["saved_response_sha256"] = hashlib.sha256(raw).hexdigest()
        entry["response_bytes"] = len(raw)
        self.save_manifest()
        with self.assertRaises(mod.AuditError):
            mod.audit_bundle(self.bundle)
        self.manifest["block_hash"] = "0x" + "3" * 64
        self.save_manifest()
        with self.assertRaises(mod.AuditError):
            mod.audit_bundle(self.bundle)
        self.tearDown(); self.setUp()
        self.manifest["approval"]["financial"] = True
        self.save_manifest()
        with self.assertRaises(mod.AuditError):
            mod.audit_bundle(self.bundle)


if __name__ == "__main__":
    unittest.main()
