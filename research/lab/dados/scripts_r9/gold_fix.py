import sys, pandas as pd
m = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)
wall = m.index.tz_convert(None) - pd.Timedelta(hours=7)  # servidor MT = Nova York + 7h (UTC+2 inverno / UTC+3 verão dos EUA)
t = wall.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").tz_convert("UTC")
m.index = t; m.index.name = "time"
print("descartados (troca de horário):", m.index.isna().sum())
m = m[m.index.notna()]; m = m[~m.index.duplicated()].sort_index()
m.to_csv(sys.argv[2], float_format="%.8g"); print(len(m), m.index.min(), m.index.max())
