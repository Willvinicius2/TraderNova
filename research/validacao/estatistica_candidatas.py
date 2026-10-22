"""Correção de testes múltiplos para as 3 aproveitáveis (TV85, TV39, TV74), com a camada estatística compartilhada
de research/ferramentas/estatistica.py (PR #53: DSR, PBO por CSCV, SPA de Hansen e bootstrap dos trades).

Séries diárias: o resultado de cada operação (R × 0,5% da conta) entra no dia UTC da saída; dias sem saída = 0.
- DSR: série fora da amostra do walk-forward 2019–2026, N = 153 + combinações da grade. Duas versões da variância dos
  Sharpes: a da nula (1/(T-1), otimista) e a observada na grade no mesmo período (mais dura).
- PBO: matriz dia × combinação com a grade inteira (todos os tempos gráficos), 2016–2026, 16 blocos.
- SPA: (a) grade inteira contra ficar fora do mercado; (b) série do walk-forward contra a média móvel simples no mesmo
  walk-forward (BM01), a pergunta "a regra rende mais que o seguidor de tendência ingênuo?".
- Bootstrap: operações fora da amostra reamostradas, distribuição de queda e PF.

Carteira: média das 3 séries (risco dividido); DSR com N = 153 + todas as combinações das 3 grades.

Uso:  python research/validacao/estatistica_candidatas.py --ferramentas <pasta que contém research/ferramentas>
Grava research/validacao/results/_estatistica.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validar as V  # noqa: E402

ASSET = "BTCUSD"
MEMBROS = ["TV85_ai_trend_nav", "TV39_smoothed_ha", "TV74_rvi"]
N_LAB = 153  # estratégias já testadas no projeto (registro do laboratório), como pede o README das ferramentas
RISCO = 0.005


def daily(tx, r, dias):
    s = pd.Series(r * RISCO, index=pd.to_datetime(tx, unit="s", utc=True).normalize()).groupby(level=0).sum()
    return s.reindex(dias, fill_value=0.0).to_numpy()


def grid_and_wf(sid, variant="orig"):
    mod, _ = V.load_strategy(sid)
    a = V.CFG["assets"][ASSET]
    cb = a["costSide"]["base"]
    trs, grids = {}, {}
    for tf in mod.META["timeframes"]:
        df = V.load(ASSET, tf)
        g, combos = V.variant_grid(mod.META, variant)
        grids[tf] = g
        trs[tf] = {V.key(c): V.run_trades(mod, df, c, variant) for c in combos}
    tx, r = [], []
    for f in V.walk_forward(trs, grids, ASSET, V.CFG["trainYears"], V.CFG["minTradesPerYear"])["folds"]:
        if not f["chosen"]:
            continue
        y = f["testYear"]
        tr = trs[f["chosen"]["tf"]][V.key(f["chosen"]["params"])]
        m = (tr["t"] >= V.ts(f"{y}-01-01")) & (tr["t"] < V.ts(min(f"{y + 1}-01-01", a["end"])))
        tx.append(tr["tx"][m])
        r.append(tr["gross"][m] - tr["turn"][m] * cb)
    allv = [(tf, k, v["tx"], v["gross"] - v["turn"] * cb) for tf, d in trs.items() for k, v in d.items()]
    return np.concatenate(tx), np.concatenate(r), allv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ferramentas", required=True, help="pasta que contém research/ferramentas (ramo do PR #53)")
    a = ap.parse_args()
    sys.path.insert(0, str(Path(a.ferramentas) / "research" / "ferramentas"))
    import estatistica as est  # noqa: E402

    ac = V.CFG["assets"][ASSET]
    d_all = pd.date_range("2016-01-01", ac["end"], freq="D", tz="UTC", inclusive="left")
    d_oos = pd.date_range(f"{ac['wfFirstTest']}-01-01", ac["end"], freq="D", tz="UTC", inclusive="left")
    btx, br, _ = grid_and_wf("BM01_media")
    bench = daily(btx, br, d_oos)
    out = {"ativo": ASSET, "risco": RISCO, "nLab": N_LAB, "estrategias": {}}
    oos_series = []
    n_total = N_LAB
    for sid in MEMBROS:
        tx, r, allv = grid_and_wf(sid)
        wf = daily(tx, r, d_oos)
        oos_series.append(wf)
        mat_all = np.column_stack([daily(t, x, d_all) for _, _, t, x in allv])
        mat_oos = np.column_stack([daily(t, x, d_oos) for _, _, t, x in allv])
        srs = [est.sharpe(mat_oos[:, j]) for j in range(mat_oos.shape[1])]
        var_grade = float(np.nanvar([s for s in srs if np.isfinite(s)]))
        n = N_LAB + len(allv)
        n_total += len(allv)
        res = {
            "combinacoes": len(allv),
            "sharpeAnualOOS": round(est.sharpe_anual(wf, 365), 2),
            "dsrNula": est.dsr(wf, n),
            "dsrVarGrade": est.dsr(wf, n, var_grade),
            "pbo": est.pbo(mat_all, s=16),
            "spaGradeContraZero": est.spa(mat_oos, reps=5000),
            "spaWFContraMediaMovel": est.spa(wf, referencia=bench, reps=5000),
            "bootstrap": est.bootstrap_trades(r * RISCO),
        }
        out["estrategias"][sid] = res
        print(sid, json.dumps({k: (v if not isinstance(v, dict) else {kk: (round(vv, 3) if isinstance(vv, float) else vv)
                                                                       for kk, vv in v.items()}) for k, v in res.items()}))
    cart = np.mean(oos_series, axis=0)
    out["carteira"] = {"sharpeAnualOOS": round(est.sharpe_anual(cart, 365), 2),
                       "dsrNula": est.dsr(cart, n_total), "spaContraMediaMovel": est.spa(cart, referencia=bench, reps=5000),
                       "spaContraZero": est.spa(cart, reps=5000)}
    out["mediaMovelSharpeAnualOOS"] = round(est.sharpe_anual(bench, 365), 2)
    print("carteira", out["carteira"], "BM01", out["mediaMovelSharpeAnualOOS"])
    (HERE / "results" / "_estatistica.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
