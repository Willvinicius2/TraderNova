import sys, pandas as pd, numpy as np
asset, d = sys.argv[1], sys.argv[2]
h = pd.read_csv(f"{d}/{asset}_H1.csv.gz", index_col=0, parse_dates=True)
D = pd.read_csv(f"{d}/{asset}_D1.csv.gz", index_col=0, parse_dates=True)
bad = ((h.high < h.low) | (h[["open","close"]].max(axis=1) > h.high + 1e-9) | (h[["open","close"]].min(axis=1) < h.low - 1e-9)).sum()
print("H1 OHLC inconsistentes:", bad, " min/max close:", h.close.min(), h.close.max())
g = h.index.to_series().diff()
big = g[g > pd.Timedelta(hours=72)]
print("lacunas > 72h no H1:", len(big)); print(big.sort_values(ascending=False).head(15).to_string())
r = np.log(h.close).diff().abs()
print("maiores variações de 1h:"); print(r.sort_values(ascending=False).head(8).round(4).to_string())
# dias úteis faltando
bd = pd.bdate_range(D.index.min().tz_convert(None), D.index.max().tz_convert(None))
miss = bd.difference(D.index.tz_convert(None))
print("dias úteis sem candle D1:", len(miss)); print([str(x.date()) for x in miss if not ((x.month==12 and x.day==25) or (x.month==1 and x.day==1))][:60])
print("candles D1 por ano:", D.groupby(D.index.year).size().to_dict())
print("H1 por ano:", h.groupby(h.index.year).size().to_dict())
for day in sys.argv[3:]:
    print(day, D.loc[day, ["open","high","low","close"]].round(2).to_dict() if day in D.index.strftime("%Y-%m-%d") else "sem candle")
