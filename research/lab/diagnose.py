"""Diagnóstico de fragilidade das CANDIDATAS: resultado sem a maior operação e comparação com comprar e segurar.
Não muda vereditos (protocolo lab-v1); entra no relatório como alerta.  Uso: python research/lab/diagnose.py"""
import json
import sys
from pathlib import Path

import pandas as pd

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))
import calibrate as C  # noqa: E402
import engine  # noqa: E402

out = {}
for p in sorted((LAB / "results").glob("*.json")):
    r = json.loads(p.read_text())
    if r["verdict"] != "CANDIDATA":
        continue
    mod, _ = C.load_strategy(r["strategy"])
    s = r["selected"]
    cfg = C.PROTOCOL["assets"][r["asset"]]
    df = C.load_bars(r["asset"], s["tf"])
    d = {}
    for stage in ("development", "validation", "reserve"):
        a, b = cfg["periods"][stage]
        tr, m = C.evaluate(mod, df, s["params"], cfg["costSide"]["base"], a, b)
        rs = sorted((t.r for t in tr), reverse=True)
        seg = df[(df.index >= pd.Timestamp(a, tz="UTC")) & (df.index < pd.Timestamp(b, tz="UTC"))]
        d[stage] = {"trades": m["trades"], "netR": m["netR"], "semMaiorR": round(sum(rs[1:]), 2),
                    "maiorR": round(rs[0], 2) if rs else None, "retPct05": m["retPct"], "ddPct05": m["maxDDPct"],
                    "buyHoldPct": round((seg.close.iloc[-1] / seg.open.iloc[0] - 1) * 100, 1)}
    d["fragil"] = any(v["semMaiorR"] <= 0 for v in d.values())
    out[r["strategy"]] = d
    print(r["strategy"], json.dumps(d, ensure_ascii=False))
(LAB / "results" / "_diagnostico_candidatas.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
