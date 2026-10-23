"""M1 (time UTC, open, high, low, close, volume) -> <out>/<ATIVO>_{H1,H4,D1}.csv.gz, mesmas regras do data.py --fxdata.
volume: se a fonte não tem volume (tudo 0), usa o número de minutos com cotação."""
import sys, pandas as pd
src, asset, out = sys.argv[1], sys.argv[2], sys.argv[3]
start = sys.argv[4] if len(sys.argv) > 4 else None
m = pd.read_csv(src, index_col=0, parse_dates=True)
if start:
    m = m[m.index >= start]
if m.volume.sum() == 0:
    m["volume"] = 1
AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
for tf, rule in {"H1": "1h", "H4": "4h", "D1": "1D"}.items():
    if tf == "D1":
        key = m.index.normalize() + pd.to_timedelta((m.index.dayofweek == 6).astype(int), unit="D")
        r = m.groupby(key).agg(AGG); r.index.name = "time"
    else:
        r = m.resample(rule).agg(AGG).dropna()
    r = r[r.volume > 0]
    r.to_csv(f"{out}/{asset}_{tf}.csv.gz", float_format="%.8g")
    print(asset, tf, len(r), r.index.min(), r.index.max())
