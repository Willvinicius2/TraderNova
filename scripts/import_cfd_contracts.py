#!/usr/bin/env python3
"""Offline, conservative importer for The5ersContractExport.mq5 snapshots."""
import argparse
import csv
import hashlib
import io
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

MAX_CSV = 1024 * 1024
MAX_META = 10 * 1024
MAX_ROWS = 32
HEADER = "requested_symbol selected status description base_currency profit_currency margin_currency contract_size digits point tick_size tick_value tick_value_profit tick_value_loss volume_min volume_step volume_max volume_limit stops_level_points freeze_level_points trade_calc_mode trade_mode chart_mode swap_mode swap_long swap_short swap_rollover3days bid ask last tick_volume tick_time_msc tick_time_server_unverified spread_price spread_points commission commission_status unavailable_fields".split()
NUMERIC = "contract_size point tick_size tick_value tick_value_profit tick_value_loss volume_min volume_step volume_max volume_limit swap_long swap_short bid ask last spread_price spread_points".split()
INTEGER = "digits stops_level_points freeze_level_points trade_calc_mode trade_mode chart_mode swap_mode swap_rollover3days tick_volume tick_time_msc".split()


class ImportErrorAudit(ValueError):
    pass


def _read(path, limit):
    with Path(path).open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ImportErrorAudit(f"input exceeds {limit} bytes: {path}")
    try:
        return data, data.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise ImportErrorAudit(f"input is not UTF-8: {path}") from exc


def _unexport_quote(value):
    # Only used when symbol fields prove there is a residual wrapper.
    if value.startswith('"') and value.endswith('"'):
        inner = value[1:-1]
        return inner.replace('""', '"')
    if '"' in value:
        raise ImportErrorAudit("malformed quote in field")
    return value


def _decimal(value, label):
    if len(value) > 64 or not re.fullmatch(r'-?\d+(?:\.\d+)?', value):
        raise ImportErrorAudit(f"unsupported decimal representation: {label}")
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ImportErrorAudit(f"invalid decimal: {label}")
    if not result.is_finite():
        raise ImportErrorAudit(f"non-finite decimal: {label}")
    return result


def import_snapshot(csv_path, metadata_path):
    csv_bytes, csv_text = _read(csv_path, MAX_CSV)
    meta_bytes, meta_text = _read(metadata_path, MAX_META)
    metadata = {}
    for line in meta_text.splitlines():
        if not line or "=" not in line:
            raise ImportErrorAudit("malformed metadata line")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", key) or key in metadata:
            raise ImportErrorAudit("invalid or duplicate metadata key")
        metadata[key] = value
    if not metadata:
        raise ImportErrorAudit("metadata is empty")
    required = {'capture_utc', 'account_server', 'utcClockApproved', 'read_only', 'tick_clock_source', 'commission'}
    if not required.issubset(metadata):
        raise ImportErrorAudit('required exporter metadata missing')

    try:
        reader = csv.reader(io.StringIO(csv_text, newline=""), strict=True)
        rows = list(reader)
    except csv.Error as exc:
        raise ImportErrorAudit("malformed CSV") from exc
    if not rows or rows[0] != HEADER:
        raise ImportErrorAudit("unexpected CSV header")
    if len(rows) < 2 or len(rows) - 1 > MAX_ROWS:
        raise ImportErrorAudit("CSV row count outside bounds")
    if any(len(row) != len(HEADER) for row in rows[1:]):
        raise ImportErrorAudit('wrong CSV field count')

    symbols, result_rows = set(), []
    residual_wrapping = rows[1][0].startswith('"')
    for line_no, values in enumerate(rows[1:], 2):
        if len(values) != len(HEADER):
            raise ImportErrorAudit(f"wrong field count on row {line_no}")
        row = dict(zip(HEADER, values))
        raw_fields = dict(row)
        if row['requested_symbol'].startswith('"') != residual_wrapping:
            raise ImportErrorAudit('inconsistent exporter quote wrappers')
        if residual_wrapping:
            for name in ("requested_symbol", "description", "unavailable_fields"):
                row[name] = _unexport_quote(row[name])
        symbol = row["requested_symbol"]
        if not re.fullmatch(r'[A-Za-z0-9_.#-]{1,128}', symbol) or symbol in symbols:
            raise ImportErrorAudit("empty or duplicate requested_symbol")
        symbols.add(symbol)
        if row["selected"] not in ("true", "false"):
            raise ImportErrorAudit(f"invalid selected flag on row {line_no}")
        if row["commission_status"] not in ("unknown", "available"):
            raise ImportErrorAudit(f"invalid commission status on row {line_no}")
        if row["commission_status"] != "unknown" or row["commission"] != "unknown_requires_broker_confirmation":
            raise ImportErrorAudit(f"unrecognized commission claim on row {line_no}")
        if row["status"] not in ("ok", "missing_on_server", "symbol_found_no_current_tick", "properties_incomplete"):
            raise ImportErrorAudit(f"unknown status on row {line_no}")
        for field in NUMERIC:
            row[field] = _decimal(row[field], f"row {line_no} {field}")
        for field in INTEGER:
            if len(row[field]) > 20 or not re.fullmatch(r"-?\d+", row[field]):
                raise ImportErrorAudit(f"invalid integer row {line_no} {field}")
            row[field] = int(row[field])
        if not 0 <= row['digits'] <= 12:
            raise ImportErrorAudit('digits outside supported bounds')

        blockers = []
        if row["status"] != "ok":
            blockers.append("contract_or_tick_unavailable:" + row["status"])
        if row["unavailable_fields"]:
            blockers.append("properties_reported_unavailable")
        if row['selected'] != 'true':
            blockers.append('symbol_not_selected')
        if row["status"] == "ok":
            if row["ask"] < row["bid"] or row['bid'] <= 0:
                raise ImportErrorAudit(f"crossed quote row {line_no}")
            if row["point"] <= 0 or row["tick_size"] <= 0 or row["contract_size"] <= 0:
                raise ImportErrorAudit(f"nonpositive contract scale row {line_no}")
            if not (row["volume_min"] > 0 and row["volume_step"] > 0 and row["volume_max"] >= row["volume_min"]):
                raise ImportErrorAudit(f"invalid volume limits row {line_no}")
            if row["volume_min"] > row["volume_max"]:
                raise ImportErrorAudit(f"invalid volume bounds row {line_no}")
            if any(row[f] < 0 for f in ('tick_value','tick_value_profit','tick_value_loss','volume_limit')) or any(row[f] < 0 for f in ('tick_time_msc','tick_volume','stops_level_points','freeze_level_points')):
                raise ImportErrorAudit('negative contract/tick properties')
            if row['tick_time_msc'] == 0:
                blockers.append('tick_timestamp_missing')
            price_tol = Decimal(1).scaleb(-row["digits"]) / 2
            point_tol = Decimal("0.005")
            actual = row["ask"] - row["bid"]
            if abs(actual - row["spread_price"]) > price_tol:
                raise ImportErrorAudit(f"spread_price mismatch row {line_no}")
            if abs(row["spread_points"] - actual / row["point"]) > point_tol + price_tol / row["point"]:
                raise ImportErrorAudit(f"spread_points mismatch row {line_no}")
        row["blockers"] = blockers
        row['raw_fields'] = raw_fields
        for f in NUMERIC:
            row[f] = str(row[f])
        result_rows.append(row)

    return {
        "schema": "tradernova.cfd-contract-snapshot.v1",
        "source": {"csv_sha256": hashlib.sha256(csv_bytes).hexdigest(), "metadata_sha256": hashlib.sha256(meta_bytes).hexdigest()},
        "identity": {"program_claim": "High Stakes", "program_verified": False,
                     "account_server_claim": metadata.get("account_server", ""), "account_server_verified": False},
        "metadata": metadata,
        "blockers": ['commission_unknown', 'utc_unverified', 'execution_feed_unverified', 'sessions_missing', 'program_and_server_unverified'] + ['requested_symbol_missing:' + s for s in ('BTCUSD','ETHUSD') if s not in symbols],
        "extra_symbols": sorted(symbols - {'BTCUSD', 'ETHUSD'}),
        "serialization": {'residual_quote_wrapper': residual_wrapping, 'actual_mt5_fixture_verified': False},
        "rows": result_rows,
        "approval": {"utc_clock": False, "costs": False, "feed": False, "financial": False,
                     "strategy": False},
        "notice": "Snapshot only. Missing contract/tick fields remain blockers; commission is unknown and is never inferred as zero. No approval is asserted."
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)
    paths = [Path(args.csv).resolve(), Path(args.metadata).resolve(), Path(args.output).resolve()]
    if paths[0] == paths[1] or paths[2] in paths[:2]:
        ap.error("output must differ from both inputs")
    if paths[2].exists():
        ap.error("output already exists; refusing overwrite")
    try:
        document = import_snapshot(paths[0], paths[1])
        # Exclusive create prevents replacing a file created after the check.
        with open(paths[2], "x", encoding="utf-8", newline="\n") as out:
            json.dump(document, out, ensure_ascii=False, indent=2, sort_keys=True)
            out.write("\n")
    except (ImportErrorAudit, OSError) as exc:
        print(f"import failed: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {paths[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
