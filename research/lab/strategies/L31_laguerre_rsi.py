"""Laguerre RSI de John Ehlers (Time Warp - Without Space Travel; Cybernetic Analysis, 2004)."""
import numpy as np

import indicators as ind

META = {
    "id": "L31_laguerre_rsi",
    "name": "Laguerre RSI (Ehlers): cruzamento de 0,2/0,8",
    "family": "oscilador",
    "round": 8,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://backtrader.readthedocs.io/en/latest/_modules/backtrader/indicators/lrsi.html",
        "https://motivewave.com/studies/laguerre_rsi.htm",
        "https://www.luxalgo.com/library/indicator/w0hoT58L-laguerre-rsi/",
        "John F. Ehlers, Cybernetic Analysis for Stocks and Futures (Wiley, 2004), cap. 'Time Warp - Without Space Travel'",
        "/home/user/labdata/pine/deepentropy_lightweight-charts-indicators/src/community/laguerre-rsi.ts (TheLark, laguerre RSI v4)",
    ],
    "rule": ("Filtro de Laguerre de 4 estágios no fechamento: L0 = (1-g)*C + g*L0[1]; L1 = -g*L0 + L0[1] + g*L1[1]; "
             "L2 = -g*L1 + L1[1] + g*L2[1]; L3 = -g*L2 + L2[1] + g*L3[1]. CU = soma das diferenças positivas L0-L1, L1-L2, L2-L3; "
             "CD = soma das negativas; LRSI = CU/(CU+CD). Regra de Ehlers: compra quando o LRSI cruza acima de lo (0,2) e vende "
             "quando cruza abaixo de 1-lo (0,8). Saída 'opp': a compra sai no sinal de venda (cruza abaixo de 1-lo; inverte se side=both); "
             "'mid': sai também quando o LRSI cruza 0,5 contra a posição. Sem stop na fonte: stop de proteção k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"gamma": [0.5, 0.6, 0.7, 0.8], "lo": [0.15, 0.2], "exit": ["opp", "mid"], "k": [2.0, 3.0], "side": ["long", "both"]},
}

_cache = {}


def laguerre_rsi(c, g):
    n = len(c)
    out = np.full(n, np.nan)
    L0 = L1 = L2 = L3 = c[0]
    for i in range(n):
        p0, p1, p2 = L0, L1, L2
        L0 = (1 - g) * c[i] + g * p0
        L1 = -g * L0 + p0 + g * p1
        L2 = -g * L1 + p1 + g * p2
        L3 = -g * L2 + p2 + g * L3
        cu = max(L0 - L1, 0) + max(L1 - L2, 0) + max(L2 - L3, 0)
        cd = max(L1 - L0, 0) + max(L2 - L1, 0) + max(L3 - L2, 0)
        out[i] = cu / (cu + cd) if cu + cd > 0 else (out[i - 1] if i else 0.5)
    out[:20] = np.nan  # aquecimento
    return out


def signals(df, p):
    key = (id(df), len(df), p["gamma"])
    if key not in _cache:
        _cache[key] = (laguerre_rsi(df.close.values, p["gamma"]), ind.atr(df, 14))
    x, a = _cache[key]
    N = len(x)
    lo, hi = np.full(N, p["lo"]), np.full(N, 1 - p["lo"])
    el = ind.cross_above(x, lo)
    es = ind.cross_below(x, hi)
    entry = np.where(el, 1, np.where(es, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    xl, xs = es, el
    if p["exit"] == "mid":
        mid = np.full(N, 0.5)
        xl = xl | ind.cross_below(x, mid)
        xs = xs | ind.cross_above(x, mid)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": xl, "exit_short": xs}
