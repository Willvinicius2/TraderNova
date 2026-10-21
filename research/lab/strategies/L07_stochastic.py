"""Estocástico lento de George Lane: cruzamento %K/%D em zona de sobrevenda/sobrecompra."""
import numpy as np

import indicators as ind

META = {
    "id": "L07_stochastic",
    "name": "Estocástico de Lane (cruzamento %K/%D nas zonas)",
    "family": "reversao",
    "sources": [
        "https://help.trendspider.com/kb/indicators/lanes-stochastic-oscillator",
        "https://www.barchart.com/education/technical-indicators/stochastic_fast",
        "https://www.babypips.com/forexpedia/Stochastics",
    ],
    "rule": "Estocástico lento (%K = média 3 do %K rápido de n candles; %D = média 3 do %K). Compra quando %K cruza acima de %D "
            "com %D abaixo da zona de sobrevenda (Lane: 20); vende quando cruza abaixo com %D acima de 100-zona. "
            "Sai da compra quando %K passa de 100-zona (sobrecompra) e da venda quando %K cai abaixo da zona. Stop k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [9, 14, 21], "zone": [15, 20, 25], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    hh, ll = ind.highest(h, p["n"]), ind.lowest(l, p["n"])
    with np.errstate(invalid="ignore", divide="ignore"):
        fk = np.where(hh > ll, 100 * (c - ll) / (hh - ll), np.nan)
    k = ind.sma(fk, 3)
    d = ind.sma(k, 3)
    z = p["zone"]
    with np.errstate(invalid="ignore"):
        lg = ind.cross_above(k, d) & (d < z)
        sh = ind.cross_below(k, d) & (d > 100 - z)
        exl = k > 100 - z
        exs = k < z
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
