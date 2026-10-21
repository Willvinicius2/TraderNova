"""Vortex Indicator (Botes & Siepman, 2010): cruzamento VI+ / VI-."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV22_vortex",
    "name": "Vortex Indicator: cruzamento VI+/VI-",
    "family": "tendencia",
    "round": 2,
    "origin": "TradingView comunidade (Botes & Siepman, indicador Vortex)",
    "sources": [
        "https://en.wikipedia.org/wiki/Vortex_indicator",
        "https://www.tradingview.com/script/Ol3XceHl/",
        "https://capital.com/en-ae/learn/technical-analysis/vortex-indicator",
    ],
    "rule": ("VI+ = soma(|máx - mín[1]|, n)/soma(TR, n); VI- = soma(|mín - máx[1]|, n)/soma(TR, n) (como no Pine do Vortex do "
             "TradingView). Compra quando VI+ cruza acima de VI-, vende (side=both) quando VI- cruza acima de VI+; sai no "
             "cruzamento oposto. Sem stop na fonte: stop de proteção k*ATR(14)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [14, 21, 28, 42], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def vortex(df, n):
    h, l, c = df.high.values, df.low.values, df.close.values
    ph, pl, pc = ind.prev(h), ind.prev(l), ind.prev(c)
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    s = lambda x: pd.Series(x).rolling(n).sum().values
    st = s(tr)
    return s(np.abs(h - pl)) / st, s(np.abs(l - ph)) / st


def signals(df, p):
    vp, vm = vortex(df, p["n"])
    up = ind.cross_above(vp, vm)
    dn = ind.cross_below(vp, vm)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
