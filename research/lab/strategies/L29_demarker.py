"""DeMarker de Tom DeMark: saída das zonas de sobrecompra/sobrevenda."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L29_demarker",
    "name": "DeMarker (DeMark): saída das zonas 0,3/0,7",
    "family": "oscilador",
    "round": 8,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://capital.com/en-gb/learn/technical-analysis/demarker-indicator",
        "https://roboforex.com/blog/education/defining-the-market-state-and-possible-reversals-with-demarker-indicator/",
        "https://www.tradingview.com/script/CF1kNGYo-DeMarker-DeM",
        "Thomas R. DeMark, The New Science of Technical Analysis (Wiley, 1994)",
    ],
    "rule": ("DeMax = máx - máx[1] se positivo, senão 0; DeMin = mín[1] - mín se positivo, senão 0; "
             "DeM = SMA(DeMax,n)/(SMA(DeMax,n)+SMA(DeMin,n)). Zonas de DeMark: sobrevenda < lo (0,3), sobrecompra > 1-lo (0,7). "
             "Compra quando o DeM sai da sobrevenda (cruza de volta acima de lo); vende (side=both) quando sai da sobrecompra "
             "(cruza abaixo de 1-lo). Saída 'opp': compra sai quando o DeM sai da sobrecompra (e vice-versa, com inversão); "
             "saída 'mid': compra sai quando o DeM cruza abaixo de 0,5 (momento virou) ou quando sai da sobrecompra; venda no espelho. "
             "Fonte sem stop fixo (sugere estrutura de preço): stop de proteção k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [8, 14, 21], "lo": [0.2, 0.3], "exit": ["opp", "mid"], "k": [2.0, 3.0], "side": ["long", "both"]},
}

_cache = {}


def demarker(df, n):
    h, l = df.high.values, df.low.values
    dmax = np.maximum(h - ind.prev(h), 0.0)
    dmin = np.maximum(ind.prev(l) - l, 0.0)
    a, b = ind.sma(dmax, n), ind.sma(dmin, n)
    with np.errstate(invalid="ignore", divide="ignore"):
        return a / (a + b)


def signals(df, p):
    key = (id(df), len(df), p["n"])
    if key not in _cache:
        _cache[key] = (demarker(df, p["n"]), ind.atr(df, 14))
    d, a = _cache[key]
    N = len(d)
    lo, hi = np.full(N, p["lo"]), np.full(N, 1 - p["lo"])
    el = ind.cross_above(d, lo)
    es = ind.cross_below(d, hi)
    entry = np.where(el, 1, np.where(es, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    if p["exit"] == "opp":
        xl, xs = es, el
    else:
        mid = np.full(N, 0.5)
        # 'mid': compra sai se o DeM perde 0,5 (momento virou) ou ao sair da sobrecompra
        xl = ind.cross_below(d, mid) | es
        xs = ind.cross_above(d, mid) | el
    return {"entry": entry, "stop": p["k"] * a, "exit_long": xl, "exit_short": xs}
