"""L11 - NR7 (Toby Crabel)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L11_nr7",
    "name": "NR7 de Toby Crabel",
    "family": "volatilidade",
    "sources": [
        "https://quantifiedstrategies.substack.com/p/nr7-trading-strategy-explained-for",
        "https://www.luxalgo.com/library/concept/nr4-nr7-narrow-range-bars/",
        "Toby Crabel, Day Trading with Short Term Price Patterns and Opening Range Breakout (1990)",
    ],
    "rule": ("Candle NR7 = range (máx-mín) menor que o de cada um dos 6 anteriores. Nos 'window' candles seguintes, "
             "o primeiro fechamento acima da máxima do NR7 compra e o primeiro abaixo da mínima vende (aproximação, no fechamento, "
             "da ordem stop de rompimento de Crabel, pois o motor só entra na abertura seguinte). "
             "Stop: 'bar' = lado oposto do NR7 (distância do fechamento até ele, mínimo 0,5×ATR14) ou 'atr' = 1×ATR14. "
             "Saída rápida por tempo: hold candles."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"window": [1, 2, 3], "hold": [1, 3, 6], "stop": ["bar", "atr"], "side": ["long", "both"]},
}


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    rng = h - l
    prev_min = pd.Series(rng).shift(1).rolling(6).min().values
    nr = rng < prev_min
    a = ind.atr(df, 14)
    n = len(c)
    entry = np.zeros(n, dtype=np.int8)
    stop = np.full(n, np.nan)
    last = -10**9
    nh = nl = np.nan
    used = True
    for i in range(n):
        if i - last >= 1 and i - last <= p["window"] and not used:
            d = 1 if c[i] > nh else (-1 if c[i] < nl else 0)
            if d:
                entry[i] = d
                used = True
                if p["stop"] == "bar":
                    dist = c[i] - nl if d > 0 else nh - c[i]
                    stop[i] = max(dist, 0.5 * a[i]) if not np.isnan(a[i]) else np.nan
                else:
                    stop[i] = a[i]
        if nr[i]:
            last, nh, nl, used = i, h[i], l[i], False
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": stop, "max_hold": p["hold"]}
