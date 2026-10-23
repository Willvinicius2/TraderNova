"""Supertrend (Olivier Seban): virada de direção da linha ATR."""
import numpy as np

import indicators as ind

META = {
    "id": "L01_supertrend",
    "name": "Supertrend (virada de direção)",
    "family": "tendencia",
    "sources": [
        "https://help.ctrader.com/indicators/built-in/trend/supertrend/",
        "https://www.luxalgo.com/library/indicator/r6dAP7yi-supertrend/",
    ],
    "rule": ("Linha Supertrend = (máx+mín)/2 ± mult*ATR(n) com bandas finais que só apertam; direção vira para alta quando o "
             "fechamento passa acima da banda superior e para baixa quando fecha abaixo da inferior. Compra na virada para alta, "
             "vende (side=both) na virada para baixa; sai na virada oposta. Stop inicial na própria linha Supertrend do candle de sinal "
             "(mínimo 0,5*ATR)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"atr_n": [7, 10, 14, 20], "mult": [2.0, 2.5, 3.0, 3.5, 4.0], "side": ["long", "both"]},
}


def supertrend(df, n, mult):
    h, l, c = df.high.values, df.low.values, df.close.values
    a = ind.atr(df, n)
    hl2 = (h + l) / 2
    ub, lb = hl2 + mult * a, hl2 - mult * a
    N = len(c)
    fu, fl = np.full(N, np.nan), np.full(N, np.nan)
    d = np.zeros(N, dtype=np.int8)
    st = np.full(N, np.nan)
    for i in range(N):
        if np.isnan(a[i]):
            continue
        if i == 0 or np.isnan(fu[i - 1]):
            fu[i], fl[i], d[i] = ub[i], lb[i], 1
        else:
            fu[i] = ub[i] if (ub[i] < fu[i - 1] or c[i - 1] > fu[i - 1]) else fu[i - 1]
            fl[i] = lb[i] if (lb[i] > fl[i - 1] or c[i - 1] < fl[i - 1]) else fl[i - 1]
            if d[i - 1] == 1:
                d[i] = -1 if c[i] < fl[i] else 1
            else:
                d[i] = 1 if c[i] > fu[i] else -1
        st[i] = fl[i] if d[i] == 1 else fu[i]
    return d, st, a


def signals(df, p):
    c = df.close.values
    d, st, a = supertrend(df, p["atr_n"], p["mult"])
    pd_ = np.r_[0, d[:-1]]
    up = (d == 1) & (pd_ == -1)
    dn = (d == -1) & (pd_ == 1)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    stop = np.maximum(np.abs(c - st), 0.5 * a)
    return {"entry": entry, "stop": stop, "exit_long": dn, "exit_short": up}
