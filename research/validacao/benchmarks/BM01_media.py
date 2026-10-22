"""Referência ingênua: fica do lado do preço em relação à média simples (seguidor de tendência mais simples possível)."""
import numpy as np

import indicators as ind

META = {
    "id": "BM01_media",
    "name": "Referência: preço acima/abaixo da média simples",
    "family": "referencia",
    "sources": ["Regra de manual (média móvel de n candles)"],
    "rule": "Compra quando o fechamento cruza acima da SMA(n), vende (both) quando cruza abaixo; sai no cruzamento oposto. Stop k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [20, 50, 100, 200], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def signals(df, p):
    c = df.close.values
    m = ind.sma(c, p["n"])
    up, dn = ind.cross_above(c, m), ind.cross_below(c, m)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
