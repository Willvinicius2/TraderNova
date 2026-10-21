"""Ehlers Cyber Cycle (everget, TradingView comunidade). Fonte Pine: everget/tradingview-pinescript-indicators."""
import numpy as np

import indicators as ind

META = {
    "id": "TV49_cyber_cycle",
    "name": "Ehlers Cyber Cycle (everget): cruzamento Cycle/Trigger",
    "family": "reversao",
    "round": 4,
    "origin": "TradingView comunidade (everget; John F. Ehlers, Cybernetic Analysis for Stocks and Futures, cap. 4)",
    "sources": [
        "https://www.tradingview.com/script/Rol6rD2Y-Ehlers-Cyber-Cycle/",
        "https://github.com/everget/tradingview-pinescript-indicators/blob/master/oscillators/ehlers_cyber_cycle.pine",
    ],
    "sourceNote": "TradingView inacessível pelo WebFetch; resumo pelo WebSearch e código Pine do repositório do autor. "
                  "O Pine do everget usa alpha=0,7 por padrão (o 'length' declarado não é usado); Ehlers usa 0,07 no livro. A grade cobre os dois.",
    "rule": "Smooth = (C + 2C1 + 2C2 + C3)/6; Cycle = (1-a/2)^2*(S-2S1+S2) + 2(1-a)*Cycle1 - (1-a)^2*Cycle2; Trigger = Cycle do candle anterior. "
            "Compra quando Cycle cruza acima do Trigger, vende quando cruza abaixo; sai no cruzamento oposto. "
            "Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"alpha": [0.05, 0.07, 0.1, 0.15, 0.3, 0.7], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def cyber(c, a):
    c = np.asarray(c, float)
    n = len(c)
    s = c.copy()
    s[3:] = (c[3:] + 2 * c[2:-1] + 2 * c[1:-2] + c[:-3]) / 6
    k1, k2, k3 = (1 - a / 2) ** 2, 2 * (1 - a), -(1 - a) ** 2
    out = np.zeros(n)
    for i in range(3, n):
        out[i] = k1 * (s[i] - 2 * s[i - 1] + s[i - 2]) + k2 * out[i - 1] + k3 * out[i - 2]
    return out


def signals(df, p):
    cy = cyber(df.close.values, p["alpha"])
    tr = ind.prev(cy)
    up, dn = ind.cross_above(cy, tr), ind.cross_below(cy, tr)
    warm = np.arange(len(cy)) < 50
    up &= ~warm
    dn &= ~warm
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
