"""Acrescenta curvas de capital (R acumulado) a resultados antigos que não têm, sem mudar veredito nem seleção.
Uso: python research/lab/curves.py"""
import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))
import calibrate as C  # noqa: E402
import engine  # noqa: E402

for p in sorted((LAB / "results").glob("*.json")):
    if p.name.startswith("_"):
        continue
    r = json.loads(p.read_text())
    if r.get("curves"):
        continue
    mod, _ = C.load_strategy(r["strategy"])
    per = C.PROTOCOL["assets"][r["asset"]]["periods"]
    cost = C.PROTOCOL["assets"][r["asset"]]["costSide"]["base"]
    s = r.get("selected")
    if s:
        tf, params = s["tf"], s["params"]
        stages = ["development"] + [k for k in ("validation", "reserve") if k in s]
    elif r["topDevelopment"]:
        tf, params, stages = r["topDevelopment"][0]["tf"], r["topDevelopment"][0]["params"], ["development"]
    else:
        continue
    df = C.load_bars(r["asset"], tf)
    r["curves"] = {st: engine.curve(C.evaluate(mod, df, params, cost, *per[st])[0]) for st in stages}
    p.write_text(json.dumps(r, indent=1, ensure_ascii=False))
    print(r["strategy"], {k: len(v) for k, v in r["curves"].items()})
