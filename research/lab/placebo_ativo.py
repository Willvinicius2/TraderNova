"""Teste placebo em qualquer ativo do protocolo (ATIVO=XAUUSD, padrão BTCUSD): mesmas saídas, stop e lados, entradas embaralhadas dentro de cada fase (20 sorteios).
Uso: ATIVO=NAS100 python research/lab/placebo_ativo.py <ID> <TF> '<params JSON>'"""
import sys, json, statistics
import numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import calibrate as C, engine
sid, tf = sys.argv[1], sys.argv[2]
import os; AS = os.environ.get("ATIVO", "BTCUSD")
params = json.loads(sys.argv[3])
mod, _ = C.load_strategy(sid)
per = C.PROTOCOL["assets"][AS]["periods"]
cb = C.PROTOCOL["assets"][AS]["costSide"]["base"]
df = C.load_bars(AS, tf); df = df[df.index >= pd.Timestamp(per["warmup"][0], tz="UTC")]
sig = mod.signals(df, dict(params))
t = df.index
rng = np.random.default_rng(12345)
res = {k: [] for k in ("development", "validation", "reserve")}
real = {}
for k in res:
    a, b = per[k]
    real[k] = engine.metrics(engine.run(df, sig, cb, a, b), 1)
idx = {k: (t.searchsorted(pd.Timestamp(per[k][0], tz="UTC")), t.searchsorted(pd.Timestamp(per[k][1], tz="UTC"))) for k in res}
for d in range(20):
    e = np.zeros(len(t), dtype=np.int8)
    for k, (i0, i1) in idx.items():
        seg = np.asarray(sig["entry"][i0:i1]).copy()
        e[i0:i1] = rng.permutation(seg)
    s2 = dict(sig); s2["entry"] = e
    for k in res:
        m = engine.metrics(engine.run(df, s2, cb, *per[k]), 1)
        res[k].append((m["netR"], m["pf"] or 0, m["trades"]))
for k in res:
    print(k, "real netR=%s PF=%s trades=%s" % (real[k]["netR"], real[k]["pf"], real[k]["trades"]),
          "| placebo mediana netR=%.2f PF=%.3f trades=%d" % (statistics.median(x[0] for x in res[k]), statistics.median(x[1] for x in res[k]), statistics.median(x[2] for x in res[k])),
          "| placebo >= real: %d/20" % sum(x[0] >= real[k]["netR"] for x in res[k]))
