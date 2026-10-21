"""Ehlers Center of Gravity (CG Oscillator, everget). Fonte Pine: everget/tradingview-pinescript-indicators."""
import numpy as np

import indicators as ind

META = {
    "id": "TV50_center_gravity",
    "name": "Ehlers Center of Gravity (everget): cruzamento CG/CG anterior",
    "family": "reversao",
    "round": 4,
    "origin": "TradingView comunidade (everget; John F. Ehlers, Cybernetic Analysis for Stocks and Futures)",
    "sources": [
        "https://www.tradingview.com/script/cbPsaSCd-CG-Oscillator-Center-of-Gravity/",
        "https://github.com/everget/tradingview-pinescript-indicators/blob/master/oscillators/center_of_gravity_oscillator.pine",
    ],
    "sourceNote": "TradingView inacessível pelo WebFetch; resumo pelo WebSearch e código Pine do repositório do autor.",
    "rule": "Fonte hl2. CG = -Σ_{i=0..L-1}(i+1)*src[i] / Σ src[i]; sinal = CG do candle anterior. "
            "Compra quando CG cruza acima do sinal, vende quando cruza abaixo; sai no cruzamento oposto. "
            "Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"length": [6, 8, 10, 14, 20], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def cgo(src, L):
    src = np.asarray(src, float)
    n = len(src)
    num = np.zeros(n)
    den = np.zeros(n)
    for i in range(L):
        sh = ind.prev(src, i) if i else src
        num += (i + 1) * sh
        den += sh
    out = -num / den
    out[: L - 1] = np.nan
    return out


def signals(df, p):
    hl2 = (df.high.values + df.low.values) / 2
    cg = cgo(hl2, p["length"])
    sg = ind.prev(cg)
    up, dn = ind.cross_above(cg, sg), ind.cross_below(cg, sg)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
