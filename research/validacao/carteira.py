"""Carteira das sobreviventes no BTC: junta as operações fora da amostra do walk-forward (3 anos de calibração, 1 de operação)
de várias estratégias, dividindo o risco de 0,5% por operação igualmente entre elas, e compara com as referências ingênuas.

Uso:  python research/validacao/carteira.py
Grava research/validacao/results/_carteira.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validar as V  # noqa: E402

ASSET = "BTCUSD"
# (estratégia, variante) com veredito APROVEITÁVEL em RESUMO.md: passam no walk-forward com 2, 3 e 4 anos de calibração
# e rendem por drawdown pelo menos o mesmo que a melhor referência ingênua
MEMBROS = [("TV85_ai_trend_nav", "orig"), ("TV39_smoothed_ha", "orig"), ("TV74_rvi", "orig")]
REFS = [("BM01_media", "orig"), ("BM02_donchian", "orig")]


def oos_trades(sid, variant):
    """Repete o walk-forward de validar.py guardando as operações (horário de saída e R) dos anos fora da amostra."""
    mod, _ = V.load_strategy(sid)
    meta = mod.META
    a = V.CFG["assets"][ASSET]
    cb, cs = a["costSide"]["base"], a["costSide"]["stress"]
    trs = {}
    grids = {}
    for tf in meta["timeframes"]:
        df = V.load(ASSET, tf)
        g, combos = V.variant_grid(meta, variant)
        grids[tf] = g
        trs[tf] = {V.key(c): V.run_trades(mod, df, c, variant) for c in combos}
    ty, mpy = V.CFG["trainYears"], V.CFG["minTradesPerYear"]
    rows = []
    for f in V.walk_forward(trs, grids, ASSET, ty, mpy)["folds"]:
        y = f["testYear"]
        if not f["chosen"]:
            continue
        tr = trs[f["chosen"]["tf"]][V.key(f["chosen"]["params"])]
        te0, te1 = V.ts(f"{y}-01-01"), V.ts(min(f"{y + 1}-01-01", a["end"]))
        m = (tr["t"] >= te0) & (tr["t"] < te1)
        for tx, g, tu in zip(tr["tx"][m], tr["gross"][m], tr["turn"][m]):
            rows.append((int(tx), float(g - tu * cb), float(g - tu * cs)))
    return rows


def summary(rows, weight):
    rows = sorted(rows)
    out = {}
    for name, col in (("base", 1), ("stress", 2)):
        pct = np.array([r[col] for r in rows]) * 0.5 * weight  # % da conta
        eq = np.cumsum(pct)
        dd = float(np.max(np.maximum.accumulate(np.r_[0, eq])[1:] - eq)) if len(eq) else 0.0
        yrs = {}
        for r, p in zip(rows, pct):
            y = int(np.datetime64(r[0], "s").astype("datetime64[Y]").astype(int) + 1970)
            yrs[y] = round(yrs.get(y, 0.0) + float(p), 1)
        out[name] = {"retornoTotalPct": round(float(eq[-1]), 1) if len(eq) else 0.0, "maxDDPct": round(dd, 1),
                     "porAnoPct": yrs, "operacoes": len(rows)}
    return out


def main():
    res = {"risco": "0,5% da conta por operação dividido igualmente entre os membros; soma simples, sem juros compostos",
           "membros": {}, "referencias": {}}
    allrows = []
    for sid, v in MEMBROS:
        rows = oos_trades(sid, v)
        res["membros"][f"{sid}:{v}"] = summary(rows, 1.0)
        allrows += rows
        print(sid, v, res["membros"][f"{sid}:{v}"]["base"])
    res["carteira"] = summary(allrows, 1.0 / len(MEMBROS))
    for sid, v in REFS:
        res["referencias"][f"{sid}:{v}"] = summary(oos_trades(sid, v), 1.0)
    print("carteira", res["carteira"])
    print("refs", {k: x["base"] for k, x in res["referencias"].items()})
    (HERE / "results" / "_carteira.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
