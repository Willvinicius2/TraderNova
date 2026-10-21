"""L12 - Rompimento do canal de Keltner com saída na média."""
import numpy as np

import indicators as ind

META = {
    "id": "L12_keltner_breakout",
    "name": "Rompimento do canal de Keltner",
    "family": "volatilidade",
    "sources": [
        "https://doc.stocksharp.com/en/designer-gallery/Keltner_Channel_Breakout",
        "https://www.babypips.com/forexpedia/keltner-channel",
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/keltner-channels",
    ],
    "rule": ("Canal de Keltner moderno: EMA(n) ± k×ATR(n). Compra quando o fechamento cruza acima da banda superior; "
             "vende quando cruza abaixo da inferior. Sai quando o fechamento volta para o outro lado da EMA central. "
             "Stop inicial stop_k×ATR(n)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [20, 50], "k": [1.5, 2.0, 2.5, 3.0], "stop_k": [1.5, 2.5, 3.5], "side": ["long", "both"]},
}


def signals(df, p):
    c = df.close.values
    n = p["n"]
    e = ind.ema(c, n)
    a = ind.atr(df, n)
    up, dn = e + p["k"] * a, e - p["k"] * a
    lo = ind.cross_above(c, up)
    sh = ind.cross_below(c, dn)
    entry = np.where(lo, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["stop_k"] * a, "exit_long": c < e, "exit_short": c > e}
