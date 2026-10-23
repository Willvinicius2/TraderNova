import sys, glob, pandas as pd
out = sys.argv[1]; dirs = sys.argv[2:]
fs = sorted(f for d in dirs for f in glob.glob(d + "/XAUUSD/1m/*/*/*.csv"))
m = pd.concat(pd.read_csv(f) for f in fs)
m["time"] = pd.to_datetime(m.timestamp, unit="ms", utc=True)  # relógio de parede da fonte (rotulado UTC)
m = m.drop(columns=["timestamp", "datetime_utc"]).drop_duplicates("time").set_index("time").sort_index()
print(len(fs), len(m), m.index.min(), m.index.max())
m.to_csv(out, float_format="%.8g")
