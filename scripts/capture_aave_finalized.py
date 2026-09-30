#!/usr/bin/env python3
"""Capture one Ethereum finalized Aave reserve snapshot; raw evidence only."""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RPC = "https://ethereum-rpc.publicnode.com"
POOL = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
PROVIDER = "0x7B4EB56E7CD4b454BA8ff71E4518426369a138A3"
RESERVES = (("USDC", "0xA0b86991c6218b36c1d19D4A2e9Eb0cE3606eB48", "0x98c23e9d8f34fefb1b7bd6a91b7ff122f4e16f5c"),
            ("WETH", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "0x4d5f47fa6a74757f35c14fd3a6ef8e3c9bc514e8"))
GET_RESERVE_DATA = "0x35ea6a75"  # frozen selector getReserveData(address)
BALANCE_OF = "0x70a08231"       # frozen selector balanceOf(address)
MAX_CALLS, MAX_RESPONSE, MAX_CAPTURE, MAX_CACHE = 12, 128 * 1024, 1024 * 1024, 16 * 1024 * 1024
MANIFEST_RESERVE, REQUEST_TIMEOUT = 64 * 1024, 4
TOTAL_TIMEOUT = 120


class CaptureFailure(RuntimeError):
    pass


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rpc_call(endpoint, payload, timeout):
    req = urllib.request.Request(endpoint, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.headers.as_bytes(), resp.read(MAX_RESPONSE + 1)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.as_bytes() if exc.headers else b"", exc.read(MAX_RESPONSE + 1)


def _prior_cache_bytes(parent, exclude=None):
    total = 0
    for child in parent.iterdir():
        if exclude is not None and child.resolve() == Path(exclude).resolve():
            continue
        if child.is_symlink():
            raise CaptureFailure('cache symlink refused')
        for item in ([child] if child.is_file() else child.rglob('*')):
            if item.is_symlink():
                raise CaptureFailure('cache symlink refused')
            if item.is_file():
                total += item.stat().st_size
                if total >= MAX_CACHE:
                    return total
    return total


def valid_header(header):
    return (isinstance(header, dict) and all(isinstance(header.get(k), str) for k in ('number','hash','parentHash','timestamp'))
            and re.fullmatch(r'0x[0-9a-fA-F]{1,16}', header['number'])
            and re.fullmatch(r'0x[0-9a-fA-F]{1,16}', header['timestamp'])
            and all(re.fullmatch(r'0x[0-9a-fA-F]{64}', header[k]) for k in ('hash','parentHash')))


def header_summary(header):
    return {k: header[k] for k in ('number','hash','parentHash','timestamp')}


class Collector:
    def __init__(self, output_dir, rpc=RPC, call=rpc_call, stop_path=None, monotonic=time.monotonic):
        self.out = Path(output_dir)
        self.rpc, self.call, self.monotonic = rpc, call, monotonic
        self.stop_path = Path(stop_path) if stop_path else Path(__file__).resolve().parents[1] / "research/cache/validation/STOP"
        self.started_mono = monotonic()
        self.requests = []
        self.total_bytes = 0
        self.call_id = 0
        self.manifest = {"schema": "tradernova.aave-finalized-raw.v1", "endpoint": rpc,
                         "chain_id_expected": 1, "deployment": {"pool": POOL, "data_provider": PROVIDER,
                         "reserves": [{"symbol": s, "asset": a, "a_token": t} for s, a, t in RESERVES],
                         "selectors": {"getReserveData(address)": GET_RESERVE_DATA, "balanceOf(address)": BALANCE_OF}},
                         "requests": self.requests, "approval": {"utc_clock": False, "costs": False, "feed": False, "strategy": False, "financial": False}}

    def _check(self):
        if self.stop_path.exists():
            raise CaptureFailure("STOP present")
        if self.monotonic() - self.started_mono >= TOTAL_TIMEOUT:
            raise CaptureFailure("total timeout reached")
        if len(self.requests) >= MAX_CALLS:
            raise CaptureFailure("request limit reached")

    def request(self, method, params):
        self._check()
        self.call_id += 1
        req_obj = {"jsonrpc": "2.0", "id": self.call_id, "method": method, "params": params}
        req_raw = json.dumps(req_obj, separators=(",", ":")).encode()
        if len(req_raw) > MAX_RESPONSE:
            raise CaptureFailure("request exceeds per-response limit")
        start_utc, start_mono = utc_now(), self.monotonic()
        remaining = TOTAL_TIMEOUT - (start_mono - self.started_mono)
        try:
            status, headers, body = self.call(self.rpc, req_raw, max(.1, min(REQUEST_TIMEOUT, remaining)))
            received_mono, received_utc = self.monotonic(), utc_now()
        except Exception as exc:
            received_mono, received_utc = self.monotonic(), utc_now()
            entry = {"id": self.call_id, "method": method, "params": params, "started_utc": start_utc,
                     "received_utc": received_utc, "started_monotonic": start_mono,
                     "received_monotonic": received_mono, "transport_error": repr(exc)[:2048]}
            self.requests.append(entry)
            raise CaptureFailure(f"transport failure: {exc}") from exc
        oversized = len(body) > MAX_RESPONSE or len(headers) > MAX_RESPONSE
        saved_body, saved_headers = body[:MAX_RESPONSE], headers[:MAX_RESPONSE]
        entry = {"id": self.call_id, "method": method, "params": params, "http_status": status,
                 "started_utc": start_utc, "received_utc": received_utc,
                 "started_monotonic": start_mono, "received_monotonic": received_mono,
                 "request_sha256": hashlib.sha256(req_raw).hexdigest(),
                 "headers_sha256": hashlib.sha256(headers).hexdigest(),
                 "response_sha256": hashlib.sha256(body).hexdigest(),
                 "response_bytes": len(body), "headers_bytes": len(headers),
                 "headers_serialization": "urllib normalized headers, not original wire bytes"}
        if oversized:
            entry["raw_truncated_to_limit"] = True
            entry['digest_scope'] = 'observed bytes only; not full remote stream'
        entry['saved_response_sha256'] = hashlib.sha256(saved_body).hexdigest()
        try:
            parsed = json.loads(body.decode("utf-8"))
            entry["jsonrpc_error"] = repr(parsed.get("error"))[:2048] if parsed.get('error') is not None else None
        except Exception:
            parsed = None
            entry["parse_error"] = "response is not valid JSON"
        # Save raw bytes before interpreting transport/RPC success.
        stem = f"{self.call_id:02d}-{method.replace('_', '-') }"
        artifacts = (("request.bin", req_raw), ("headers.bin", saved_headers), ("response.bin", saved_body))
        proposed = sum(len(data) for _, data in artifacts)
        if self.total_bytes + proposed > MAX_CAPTURE - MANIFEST_RESERVE:
            entry["capture_limit_rejected"] = True
            self.requests.append(entry)
            raise CaptureFailure("capture byte limit would be exceeded; raw response not written")
        if _prior_cache_bytes(self.out.parent, exclude=self.out) + self.total_bytes + proposed + MANIFEST_RESERVE > MAX_CACHE:
            entry["cache_limit_rejected"] = True
            self.requests.append(entry)
            raise CaptureFailure("cumulative Aave cache limit would be exceeded; raw response not written")
        for suffix, data in artifacts:
            path = self.out / f"{stem}-{suffix}"
            with path.open("xb") as stream:
                stream.write(data)
            self.total_bytes += len(data)
        entry["raw_files"] = [f"{stem}-request.bin", f"{stem}-headers.bin", f"{stem}-response.bin"]
        self.requests.append(entry)
        if self.total_bytes > MAX_CAPTURE:
            raise CaptureFailure("capture exceeds 1 MiB")
        if oversized:
            raise CaptureFailure("response or headers exceed 128 KiB; bounded prefix and observed-byte digest preserved")
        if status != 200 or not isinstance(parsed, dict) or parsed.get("error") is not None or "result" not in parsed or parsed.get('id') != self.call_id or parsed.get('jsonrpc') != '2.0':
            raise CaptureFailure(f"RPC request failed: {method}")
        self._check()
        return parsed["result"]

    def run(self):
        if self.stop_path.exists():
            raise CaptureFailure("STOP present")
        chain = self.request("eth_chainId", [])
        if chain != "0x1":
            raise CaptureFailure("RPC chainId is not 1")
        header = self.request("eth_getBlockByNumber", ["finalized", False])
        if not valid_header(header):
            raise CaptureFailure("finalized block header malformed")
        number = header["number"]
        self.manifest.update({"chain_id": 1, "block_header": header_summary(header), "block_number": number,
                              "block_hash": header["hash"], "capture_started_utc": utc_now()})
        for symbol, asset, atoken in RESERVES:
            arg = asset.lower().removeprefix("0x").rjust(64, "0")
            for target in (PROVIDER, POOL):
                value = self.request("eth_call", [{"to": target, "data": GET_RESERVE_DATA + arg}, number])
                if not isinstance(value, str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{64})+', value):
                    raise CaptureFailure('invalid reserve ABI hex response')
            token_arg = atoken.lower().removeprefix("0x").rjust(64, "0")
            value = self.request("eth_call", [{"to": asset, "data": BALANCE_OF + token_arg}, number])
            if not isinstance(value, str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}', value):
                raise CaptureFailure('invalid balance ABI hex response')
        final_header = self.request("eth_getBlockByNumber", [number, False])
        self.manifest["revalidation_header"] = header_summary(final_header) if valid_header(final_header) else None
        self.manifest["block_hash_match"] = bool(valid_header(final_header) and final_header.get("hash") == header["hash"] and final_header['number'] == number)
        if not self.manifest["block_hash_match"]:
            raise CaptureFailure("block hash mismatch after calls")
        latest_finalized = self.request("eth_getBlockByNumber", ["finalized", False])
        self.manifest["finalized_revalidation_header"] = header_summary(latest_finalized) if valid_header(latest_finalized) else None
        if not valid_header(latest_finalized) or int(latest_finalized['number'],16) < int(number, 16) or (latest_finalized['number'] == number and latest_finalized['hash'] != header['hash']):
            raise CaptureFailure("finalized height regressed below captured block")
        self.manifest["capture_completed_utc"] = utc_now()
        self.manifest["capture_bytes"] = self.total_bytes
        return self.manifest


def execute(output_dir, rpc=RPC, call=rpc_call, stop_path=None):
    out = Path(output_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Refuse reuse and acquire a task-owned exclusive lock beside the new capture.
    if out.exists():
        raise CaptureFailure("output directory must not already exist")
    if _prior_cache_bytes(out.parent) + MANIFEST_RESERVE > MAX_CACHE:
        raise CaptureFailure('cache full before capture')
    lock = out.parent / "aave-capture.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise CaptureFailure("aave-capture.lock already exists") from exc
    owned = os.fstat(fd)
    try:
        os.write(fd, json.dumps({"pid": os.getpid(), "started_utc": utc_now(), "output": str(out)}).encode())
        os.close(fd)
        out.mkdir()
        collector = Collector(out, rpc, call, stop_path)
        try:
            manifest = collector.run()
            manifest["status"] = "captured_raw_only"
        except Exception as exc:
            manifest = collector.manifest
            manifest["status"] = "failed_raw_only"
            manifest["failure"] = str(exc)
            manifest["capture_bytes"] = collector.total_bytes
        # Keep an audit manifest even when a request fails; never delete captured bytes.
        raw = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        if len(raw) > MANIFEST_RESERVE or len(raw) + collector.total_bytes > MAX_CAPTURE:
            manifest["status"] = "failed_raw_only"
            manifest["failure"] = "capture plus manifest exceeds 1 MiB"
            raw = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
        tmp_manifest = out / "manifest.json.tmp"
        with tmp_manifest.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_manifest, out / "manifest.json")
        if _prior_cache_bytes(out.parent) > MAX_CACHE:
            raise CaptureFailure("cache exceeds 16 MiB")
        return manifest["status"] == "captured_raw_only"
    finally:
        try:
            current = lock.stat()
            if (current.st_dev, current.st_ino) == (owned.st_dev, owned.st_ino):
                lock.unlink()
        except FileNotFoundError:
            pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--rpc", default=RPC)
    args = parser.parse_args(argv)
    try:
        ok = execute(args.output_dir, args.rpc)
    except Exception as exc:
        print(f"capture failed: {exc}", file=sys.stderr)
        return 2
    print(f"capture {'complete' if ok else 'recorded failure'}: {args.output_dir}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
