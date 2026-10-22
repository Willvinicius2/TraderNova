"""Referência clássica: rompimento de Donchian (tartarugas), saída no canal curto."""
import numpy as np

import indicators as ind

META = {
    "id": "BM02_donchian",
    "name": "Referência: rompimento de Donchian (tartarugas)",
    "family": "referencia",
    "sources": ["Curtis Faith, Way of the Turtle (2007)"],
    "rule": "Compra quando o fechamento passa a máxima dos n candles anteriores, vende (both) abaixo da mínima; sai no rompimento contrário de n/2. Stop k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [20, 55, 100], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    n, x = p["n"], max(2, p["n"] // 2)
    up = c > ind.prev(ind.highest(h, n))
    dn = c < ind.prev(ind.lowest(l, n))
    exl = c < ind.prev(ind.lowest(l, x))
    exs = c > ind.prev(ind.highest(h, x))
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
