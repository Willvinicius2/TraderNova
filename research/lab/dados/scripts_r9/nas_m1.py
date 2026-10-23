import json, sys, glob
import pandas as pd
src, out = sys.argv[1], sys.argv[2]
parts = []
for f in sorted(glob.glob(src + "/*.json")):
    d = pd.DataFrame(json.load(open(f)))
    parts.append(d)
m = pd.concat(parts)
wall = pd.to_datetime(m.timestamp, unit="ms")  # relógio de parede da fonte
# conferido nos payrolls (08:30 Nova York): a fonte segue o horário de Nova York COM horário de verão
m["time"] = wall.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")
print("minutos descartados na troca de horário:", m.time.isna().sum())
m = m.dropna(subset=["time"])
m = m.drop(columns="timestamp").drop_duplicates("time").set_index("time").sort_index()
print(len(m), m.index.min(), m.index.max(), m.volume.sum())
m.to_csv(out, float_format="%.8g")
