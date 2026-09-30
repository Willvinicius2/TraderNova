"""Adversarial unit fixtures for the offline CFD contract snapshot importer."""
import csv
import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cfd_import", ROOT / "scripts" / "import_cfd_contracts.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def fixture(status="ok", symbol="BTCUSD"):
    row = {name: "" for name in mod.HEADER}
    row.update(requested_symbol=symbol, selected="true", status=status,
               description='Bitcoin "spot" CFD', base_currency="BTC", profit_currency="USD",
               margin_currency="USD", contract_size="1", digits="2", point="0.01", tick_size="0.01",
               tick_value="0.01", tick_value_profit="0.01", tick_value_loss="0.01",
               volume_min="0.01", volume_step="0.01", volume_max="10", volume_limit="0",
               stops_level_points="0", freeze_level_points="0", trade_calc_mode="0", trade_mode="4",
               chart_mode="1", swap_mode="0", swap_long="0", swap_short="0", swap_rollover3days="3",
               bid="100.00", ask="100.03", last="100.02", tick_volume="1", tick_time_msc="123",
               tick_time_server_unverified="1970.01.01 00:00:00", spread_price="0.03", spread_points="3.00",
               commission="unknown_requires_broker_confirmation", commission_status="unknown", unavailable_fields="")
    return row


class ImporterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.csv_path = Path(self.tmp.name) / "snapshot.csv"
        self.meta_path = Path(self.tmp.name) / "snapshot_metadata.txt"

    def write(self, rows, metadata="capture_utc=2026.09.30 00:00:00Z\naccount_server=claimed\nutcClockApproved=false\nread_only=true\ntick_clock_source=tick.time_msc\ncommission=unknown_requires_broker_confirmation\n", residual=True):
        stream = io.StringIO(newline="")
        writer = csv.writer(stream, lineterminator="\r\n")
        writer.writerow(mod.HEADER)
        for row in rows:
            # Two plausible serializations; no actual MT5 fixture available.
            cooked = dict(row)
            if residual:
                for key in ("requested_symbol", "description", "unavailable_fields"):
                    val = cooked[key]
                    cooked[key] = '"' + val.replace('"', '""') + '"'
            writer.writerow([cooked[k] for k in mod.HEADER])
        self.csv_path.write_text(stream.getvalue(), encoding="utf-8", newline='')
        self.meta_path.write_text(metadata, encoding="utf-8")

    def test_preserves_hash_commission_blockers_and_single_unquote(self):
        self.write([fixture()])
        result = mod.import_snapshot(self.csv_path, self.meta_path)
        self.assertEqual(result["rows"][0]["description"], 'Bitcoin "spot" CFD')
        self.assertIn("unknown_requires_broker_confirmation", result["rows"][0]["commission"])
        self.assertFalse(any(result["approval"].values()))
        self.assertEqual(len(result["source"]["csv_sha256"]), 64)
        self.write([fixture()], residual=False)
        self.assertEqual(mod.import_snapshot(self.csv_path, self.meta_path)['rows'][0]['description'], 'Bitcoin "spot" CFD')
        missing = fixture("symbol_found_no_current_tick", "ETHUSD")
        self.write([missing])
        row = mod.import_snapshot(self.csv_path, self.meta_path)["rows"][0]
        self.assertIn("contract_or_tick_unavailable:symbol_found_no_current_tick", row["blockers"])

    def test_rejects_duplicate_symbols_nonfinite_crossed_and_bad_volume(self):
        for rows, field, value in [([fixture(), fixture()], None, None),
                                   ([fixture()], "tick_value", "NaN"),
                                   ([fixture()], "bid", "100.04"),
                                   ([fixture()], "volume_step", "0")]:
            if field:
                rows[0][field] = value
            self.write(rows)
            with self.assertRaises(mod.ImportErrorAudit):
                mod.import_snapshot(self.csv_path, self.meta_path)

    def test_rejects_spread_metadata_duplicate_keys_malformed_csv_and_oversize(self):
        row = fixture(); row["spread_points"] = "4.2"
        self.write([row])
        with self.assertRaises(mod.ImportErrorAudit):
            mod.import_snapshot(self.csv_path, self.meta_path)
        self.write([fixture()], "a=1\na=2\n")
        with self.assertRaises(mod.ImportErrorAudit):
            mod.import_snapshot(self.csv_path, self.meta_path)
        self.csv_path.write_text('"unterminated', encoding="utf-8")
        with self.assertRaises(mod.ImportErrorAudit):
            mod.import_snapshot(self.csv_path, self.meta_path)
        self.csv_path.write_bytes(b"x" * (mod.MAX_CSV + 1))
        with self.assertRaises(mod.ImportErrorAudit):
            mod.import_snapshot(self.csv_path, self.meta_path)

    def test_bounds_claims_and_output_no_overwrite(self):
        for field, value in [('digits', '-1'), ('digits', '999999'), ('tick_value', '1e999999'), ('bid', '0')]:
            row = fixture(); row[field] = value
            self.write([row])
            with self.assertRaises(mod.ImportErrorAudit):
                mod.import_snapshot(self.csv_path, self.meta_path)
        self.write([fixture()])
        result = mod.import_snapshot(self.csv_path, self.meta_path)
        self.assertIn('requested_symbol_missing:ETHUSD', result['blockers'])
        self.assertIn('sessions_missing', result['blockers'])
        output = Path(self.tmp.name) / 'result.json'
        output.write_text('keep')
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
            mod.main(['--csv',str(self.csv_path),'--metadata',str(self.meta_path),'--output',str(output)])
        self.assertEqual(output.read_text(), 'keep')


if __name__ == "__main__":
    unittest.main()
