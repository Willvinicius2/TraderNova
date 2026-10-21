"""Prepara os candles do laboratório em research/cache/lab (não versionado).

BTCUSD: Bitstamp 1 minuto do repositório público github.com/ff137/bitstamp-btcusd-minute-data.
  git clone --depth 1 --filter=blob:none --no-checkout https://github.com/ff137/bitstamp-btcusd-minute-data <dir>
  git -C <dir> checkout HEAD -- data/historical data/updates
  python research/lab/data.py --bitstamp <dir>
"""
import argparse
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "cache" / "lab"
RULES = {"M15": "15min", "H1": "1h", "H4": "4h", "D1": "1D"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bitstamp", required=True)
    a = ap.parse_args()
    d = Path(a.bitstamp) / "data"
    parts = [pd.read_csv(p) for p in sorted((d / "historical").glob("*.csv.gz")) + sorted((d / "updates").glob("*.csv"))]
    m = pd.concat(parts).drop_duplicates("timestamp").sort_values("timestamp")
    m.index = pd.to_datetime(m.timestamp, unit="s", utc=True)
    m = m[m.index >= "2014-01-01"]
    OUT.mkdir(parents=True, exist_ok=True)
    for tf, rule in RULES.items():
        r = m.resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
        r.to_csv(OUT / f"BTCUSD_{tf}.csv.gz")
        print(tf, len(r), r.index.min(), r.index.max())


if __name__ == "__main__":
    main()
