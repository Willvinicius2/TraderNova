"""Chaikin Oscillator: cruzamento da linha zero."""
import numpy as np

import indicators as ind

META = {
    "id": "TV13_chaikin_osc",
    "name": "Chaikin Oscillator (cruzamento de zero)",
    "family": "volume",
    "round": 2,
    "origin": "TradingView comunidade / indicador embutido (Marc Chaikin)",
    "sources": [
        "https://www.tradingview.com/support/solutions/43000501979-chaikin-oscillator/",
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/chaikin-oscillator",
    ],
    "rule": ("Linha de Acumulação/Distribuição: soma de volume*((F-m)-(M-F))/(M-m). Chaikin = EMA(rápida) da ADL - EMA(lenta) da ADL "
             "(padrão 3/10). Compra quando o oscilador cruza acima de zero; vende (side=both) quando cruza abaixo; sai no cruzamento "
             "oposto. Fonte sem stop: stop de proteção k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"fast": [3, 6], "slow": [10, 20, 30], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def chaikin(df, fast, slow):
    h, l, c, v = (df[k].values for k in ("high", "low", "close", "volume"))
    rng = h - l
    mfm = np.where(rng > 0, ((c - l) - (h - c)) / np.where(rng > 0, rng, 1), 0.0)
    adl = np.cumsum(mfm * v)
    return ind.ema(adl, fast) - ind.ema(adl, slow)


def signals(df, p):
    osc = chaikin(df, p["fast"], p["slow"])
    z = np.zeros(len(osc))
    up, dn = ind.cross_above(osc, z), ind.cross_below(osc, z)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
