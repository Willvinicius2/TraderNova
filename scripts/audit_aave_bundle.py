#!/usr/bin/env python3
"""Offline integrity audit and conservative decoding of one Aave raw bundle."""
import argparse
import hashlib
import json
import re
import sys
from decimal import Decimal, localcontext
from pathlib import Path

MAX_ITEM = 128 * 1024
MAX_BUNDLE = 1024 * 1024
POOL = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
PROVIDER = "0x7B4EB56E7CD4b454BA8ff71E4518426369a138A3"
RESERVES = (("USDC", "0xA0b86991c6218b36c1d19D4A2e9Eb0cE3606eB48", "0x98c23e9d8f34fefb1b7bd6a91b7ff122f4e16f5c", 6),
            ("WETH", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "0x4d5f47fa6a74757f35c14fd3a6ef8e3c9bc514e8", 18))
GET_RESERVE_DATA, BALANCE_OF = "0x35ea6a75", "0x70a08231"
APPROVALS = ("utc_clock", "costs", "feed", "strategy", "financial")


class AuditError(ValueError):
    pass


def _need(cond, message):
    if not cond:
        raise AuditError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        _need(key not in result, 'duplicate JSON object key')
        result[key] = value
    return result


def _hex_int(value, label):
    _need(isinstance(value, str) and re.fullmatch(r"0x[0-9a-fA-F]{1,16}", value) is not None, f"invalid hex {label}")
    return int(value, 16)


def _header(value, label):
    _need(isinstance(value, dict), f"missing {label}")
    for k in ("number", "timestamp"):
        _hex_int(value.get(k), f"{label}.{k}")
    for k in ("hash", "parentHash"):
        _need(isinstance(value.get(k), str) and re.fullmatch(r"0x[0-9a-fA-F]{64}", value[k]), f"invalid {label}.{k}")
    return value


def _raw(bundle, name, seen):
    _need(isinstance(name, str) and name and not Path(name).is_absolute(), "invalid raw path")
    path = (bundle / name).resolve()
    _need(path.is_relative_to(bundle.resolve()), "raw path escapes bundle")
    _need(path not in seen, "duplicate raw-file reference")
    seen.add(path)
    try:
        with path.open('rb') as stream:
            data = stream.read(MAX_ITEM + 1)
    except OSError as exc:
        raise AuditError(f"missing raw file: {name}") from exc
    _need(len(data) <= MAX_ITEM, f"raw file exceeds 128 KiB: {name}")
    return data


def audit_bundle(bundle_dir):
    bundle = Path(bundle_dir).resolve()
    _need(bundle.is_dir(), "bundle directory missing")
    entries = []
    for item in bundle.rglob('*'):
        _need(len(entries) < 128 and not item.is_symlink(), 'bundle file count or symlink invalid')
        entries.append(item)
    total = sum(p.stat().st_size for p in entries if p.is_file())
    _need(total <= MAX_BUNDLE, "bundle exceeds 1 MiB")
    try:
        with (bundle / 'manifest.json').open('rb') as stream:
            raw_manifest = stream.read(MAX_ITEM + 1)
        _need(len(raw_manifest) <= MAX_ITEM, 'manifest exceeds bound')
        manifest = json.loads(raw_manifest, object_pairs_hook=unique_object)
    except (OSError, ValueError) as exc:
        raise AuditError("manifest missing or malformed") from exc
    _need(isinstance(manifest, dict) and manifest.get("schema") == "tradernova.aave-finalized-raw.v1", "unexpected manifest schema")
    _need(manifest.get("status") == "captured_raw_only", "bundle is not a completed raw capture")
    approvals = manifest.get("approval")
    _need(isinstance(approvals, dict) and all(approvals.get(k) is False for k in APPROVALS), "approval flags must all remain false")
    _need(manifest.get("chain_id") == 1 and manifest.get("chain_id_expected") == 1, "chain ID is not frozen Ethereum mainnet")
    deployment = manifest.get("deployment", {})
    _need(deployment.get("pool", "").lower() == POOL.lower() and deployment.get("data_provider", "").lower() == PROVIDER.lower(), "deployment mismatch")
    _need(deployment.get("selectors") == {"getReserveData(address)": GET_RESERVE_DATA, "balanceOf(address)": BALANCE_OF}, "selector mismatch")
    expected_reserves = [{"symbol": s, "asset": a, "a_token": t} for s, a, t, _ in RESERVES]
    _need(deployment.get("reserves") == expected_reserves, "reserve list mismatch")

    reqs = manifest.get("requests")
    _need(isinstance(reqs, list) and 1 <= len(reqs) <= 12, "invalid request count")
    ids, seen, parsed = set(), set(), []
    for item in reqs:
        _need(isinstance(item, dict), "invalid request record")
        rid = item.get("id")
        _need(type(rid) is int and rid > 0 and rid not in ids, "duplicate or invalid request id")
        ids.add(rid)
        files = item.get("raw_files")
        _need(isinstance(files, list) and len(files) == 3, "request must reference request/headers/response raw files")
        raw = [_raw(bundle, f, seen) for f in files]
        hashes = [hashlib.sha256(x).hexdigest() for x in raw]
        _need(hashes[0] == item.get("request_sha256"), "request hash mismatch")
        _need(hashes[1] == item.get("headers_sha256"), "headers hash mismatch")
        _need(hashes[2] == item.get("saved_response_sha256", item.get("response_sha256")), "response hash mismatch")
        _need(not item.get("raw_truncated_to_limit") and hashes[2] == item.get("response_sha256") and item.get("response_bytes") == len(raw[2]), "response truncated or full hash mismatch")
        _need(len(raw[0]) <= MAX_ITEM and len(raw[1]) <= MAX_ITEM and len(raw[2]) <= MAX_ITEM, "raw byte bound exceeded")
        try:
            rq, rs = json.loads(raw[0],object_pairs_hook=unique_object), json.loads(raw[2],object_pairs_hook=unique_object)
        except ValueError as exc:
            raise AuditError("raw request/response is malformed JSON") from exc
        _need(isinstance(rq,dict) and isinstance(rs,dict), 'request and response must be objects')
        _need(type(rq.get('id')) is int and type(rs.get('id')) is int and rq.get("id") == rid and rs.get("id") == rid and rs.get("jsonrpc") == "2.0" and rq.get('jsonrpc') == '2.0', "JSON-RPC id/version mismatch")
        _need(isinstance(rq.get('params'),list), 'request params must be an array')
        if rq.get('method') == 'eth_call':
            _need(len(rq['params']) == 2 and isinstance(rq['params'][0],dict), 'invalid eth_call shape')
        _need(item.get("http_status") == 200 and "error" not in rs and "result" in rs, "HTTP or JSON-RPC request failed")
        _need(rq.get("method") == item.get("method") and rq.get("params") == item.get("params"), "manifest request differs from raw request")
        parsed.append((item, rq, rs))

    _need(len(seen) == sum(len(x.get("raw_files", [])) for x in reqs), "duplicate raw file references")
    chain = next((rs["result"] for it, rq, rs in parsed if rq["method"] == "eth_chainId"), None)
    _need(chain == "0x1", "raw chainId response is not 1")
    expected_methods = ["eth_chainId", "eth_getBlockByNumber"] + ["eth_call"] * 6 + ["eth_getBlockByNumber", "eth_getBlockByNumber"]
    _need([rq["method"] for _, rq, _ in parsed] == expected_methods, "unexpected request sequence")
    _need(parsed[0][1]["params"] == [] and parsed[1][1]["params"] == ["finalized", False], "initial finalized request mismatch")
    number, block_hash = manifest.get("block_number"), manifest.get("block_hash")
    _need(isinstance(number, str) and _hex_int(number, "block_number") >= 0, "invalid captured block number")
    initial = _header(manifest.get("block_header"), "block_header")
    checked = _header(manifest.get("revalidation_header"), "revalidation_header")
    finalized = _header(manifest.get("finalized_revalidation_header"), "finalized_revalidation_header")
    _need(initial["number"] == number and initial["hash"] == block_hash, "initial finalized header mismatch")
    _need(checked["number"] == number and checked["hash"] == block_hash and manifest.get("block_hash_match") is True, "captured block hash mismatch")
    _need(_hex_int(finalized["number"], "finalized height") >= _hex_int(number, "captured block") and
          (_hex_int(finalized["number"], "finalized height") > _hex_int(number, "captured block") or finalized["hash"] == block_hash), "finalized height/hash invalid")
    # Compare only the frozen header fields; the raw RPC header retains every field.
    def summary(raw):
        _need(isinstance(raw, dict), "raw header response malformed")
        return {k: raw.get(k) for k in ("number", "hash", "parentHash", "timestamp")}
    _need(summary(parsed[1][2]["result"]) == initial, "raw initial finalized header mismatch")
    _need(parsed[-2][1]["params"] == [number, False] and summary(parsed[-2][2]["result"]) == checked, "raw numbered revalidation mismatch")
    _need(parsed[-1][1]["params"] == ["finalized", False] and summary(parsed[-1][2]["result"]) == finalized, "raw finality revalidation mismatch")

    calls = [rq for _, rq, _ in parsed if rq["method"] == "eth_call"]
    _need(len(calls) == 6, "expected exactly six eth_call requests")
    _need(all(rq.get("params", [None, None])[1] == number for rq in calls), "eth_call block mismatch")
    decoded = []
    for symbol, asset, atoken, decimals in RESERVES:
        arg = asset.lower().removeprefix("0x").rjust(64, "0")
        token_arg = atoken.lower().removeprefix("0x").rjust(64, "0")
        group = [(rq, rs["result"]) for _, rq, rs in parsed if rq["method"] == "eth_call" and rq["params"][0].get("data", "").endswith(arg)]
        provider = next((value for rq, value in group if rq["params"][0].get("to", "").lower() == PROVIDER.lower()), None)
        pool = next((value for rq, value in group if rq["params"][0].get("to", "").lower() == POOL.lower()), None)
        balance = next((rs["result"] for _, rq, rs in parsed if rq["method"] == "eth_call" and rq["params"][0].get("to", "").lower() == asset.lower() and rq["params"][0].get("data") == BALANCE_OF + token_arg), None)
        _need(provider is not None and pool is not None and balance is not None, f"missing frozen eth_call for {symbol}")
        _need(any(rq["params"][0].get("to", "").lower() == PROVIDER.lower() and rq["params"][0].get("data") == GET_RESERVE_DATA + arg for rq, _ in group), f"provider selector/address mismatch for {symbol}")
        _need(any(rq["params"][0].get("to", "").lower() == POOL.lower() and rq["params"][0].get("data") == GET_RESERVE_DATA + arg for rq, _ in group), f"pool selector/address mismatch for {symbol}")
        # Pool bytes were integrity-checked above and intentionally remain opaque.
        _need(isinstance(pool,str) and re.fullmatch(r'0x(?:[0-9a-fA-F]{64})+',pool), 'pool result must contain ABI words')
        _need(re.fullmatch(r"0x[0-9a-fA-F]{64}", balance) is not None, f"invalid balanceOf result for {symbol}")
        _need(re.fullmatch(r"0x(?:[0-9a-fA-F]{64}){12}", provider) is not None, f"provider tuple is not exactly 12 ABI words for {symbol}")
        words = [int(provider[2 + i * 64:2 + (i + 1) * 64], 16) for i in range(12)]
        stable_raw, variable_raw, apr_ray = words[3], words[4], words[6]
        liquidity_raw = int(balance[2:], 16)
        debt = stable_raw + variable_raw
        with localcontext() as context:
            context.prec = 100
            utilization = Decimal(debt) / Decimal(debt + liquidity_raw) if debt + liquidity_raw else None
            apr = Decimal(apr_ray) / Decimal(10**27)
        decoded.append({"symbol": symbol, "decimals": decimals,
                        "total_stable_debt_raw": str(stable_raw), "total_variable_debt_raw": str(variable_raw),
                        "underlying_balance_raw": str(liquidity_raw), "variable_borrow_rate_ray": str(apr_ray),
                        "variable_borrow_rate_apr": str(apr),
                        "utilization": str(utilization) if utilization is not None else None,
                        "pool_tuple_decoding": "unknown_abi_not_decoded"})
    return {"schema": "tradernova.aave-bundle-audit.v1", "bundle_integrity": "passed",
            "block_number": number, "block_hash": block_hash, "decoded_unverified": True,
            "utc_approved": False, "financial_approved": False, "feed_approved": False,
            "costs_approved": False, "strategy_approved": False, "reserves": decoded, 'decimal_precision': 100,
            "limitation": "Raw integrity and selected ABI words only; timestamp causality and financial utility remain unverified."}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle_dir")
    ap.add_argument("--output")
    args = ap.parse_args(argv)
    try:
        report = audit_bundle(args.bundle_dir)
        text = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output:
            path = Path(args.output)
            with path.open("x", encoding="utf-8") as f:
                f.write(text)
        else:
            print(text, end="")
        return 0
    except (AuditError, OSError) as exc:
        print(f"audit failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
