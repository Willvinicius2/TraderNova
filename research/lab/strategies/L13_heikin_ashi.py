"""L13 - Tendência Heikin Ashi: sequência de velas HA sem pavio contra a direção."""
import numpy as np

import indicators as ind

META = {
    "id": "L13_heikin_ashi",
    "name": "Tendência Heikin Ashi (velas sem pavio contra)",
    "family": "padroes",
    "sources": [
        "https://www.xtb.com/en/education/heikin-ashi",
        "https://www.luxalgo.com/blog/heikin-ashi-charts-clear-strategies-for-traders/",
        "https://doc.stocksharp.com/en/api-examples/0012_Heikin_Ashi_Consecutive",
        "Dan Valcu, 'Using the Heikin-Ashi Technique', Technical Analysis of Stocks & Commodities, fev/2004",
    ],
    "rule": ("Calcula velas Heikin Ashi (fechHA=(A+M+m+F)/4, abertHA=(abertHA ant.+fechHA ant.)/2, máx/mín incluindo abertHA/fechHA). "
             "Compra quando as últimas n velas HA são de alta e sem sombra inferior (tendência forte de alta); venda no espelho "
             "(n velas de baixa sem sombra superior). Sai na primeira vela HA de cor oposta. Stop k*ATR14. Preços de execução são os reais."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [1, 2, 3, 4], "k": [1.5, 2.5, 3.5], "side": ["long", "both"]},
}


def heikin_ashi(df):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    hc = (o + h + l + c) / 4.0
    ho = np.empty_like(hc)
    ho[0] = (o[0] + c[0]) / 2.0
    for i in range(1, len(hc)):
        ho[i] = (ho[i - 1] + hc[i - 1]) / 2.0
    hh = np.maximum(h, np.maximum(ho, hc))
    hl = np.minimum(l, np.minimum(ho, hc))
    return ho, hh, hl, hc


def run_count(x):
    out = np.zeros(len(x), dtype=int)
    cnt = 0
    for i, v in enumerate(x):
        cnt = cnt + 1 if v else 0
        out[i] = cnt
    return out


def signals(df, p):
    ho, hh, hl, hc = heikin_ashi(df)
    tol = 1e-9 * np.abs(hc)
    green, red = hc > ho, hc < ho
    bull = green & (hl >= ho - tol)  # sem sombra inferior
    bear = red & (hh <= ho + tol)    # sem sombra superior
    n = p["n"]
    up = run_count(bull) == n  # dispara uma vez, ao completar n velas
    dn = run_count(bear) == n
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": red, "exit_short": green}
