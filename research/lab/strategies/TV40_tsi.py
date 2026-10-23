"""TV40 - True Strength Index (William Blau) / everget.

Pine (everget, GPL-3.0, github.com/everget/tradingview-pinescript-indicators commit 8385cc4,
oscillators/tsi_true_strength_index.pine): mom = change(close); TSI = 100*EMA(EMA(mom,long),short)/EMA(EMA(|mom|,long),short);
signal = EMA(TSI, signalLength). O script é indicador (sem ordens); a regra de operação é a usual do TSI:
compra quando TSI cruza acima da linha de sinal (opcionalmente só se o cruzamento ocorre abaixo de 0), venda no inverso.
Sem stop no original: stop de proteção k*ATR(14).
"""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV40_tsi",
    "name": "True Strength Index (Blau / everget)",
    "family": "momento",
    "round": 4,
    "origin": "TradingView comunidade (everget)",
    "sources": [
        "https://github.com/everget/tradingview-pinescript-indicators/blob/master/oscillators/tsi_true_strength_index.pine",
        "https://kr.tradingview.com/script/JOaLTNxW-True-Strength-Index-with-Zones-Alerts",
        "https://school.stockcharts.com/doku.php?id=technical_indicators:true_strength_index",
    ],
    "rule": ("TSI = 100*EMA(EMA(Δfech,longo),curto)/EMA(EMA(|Δfech|,longo),curto); sinal = EMA(TSI). Compra quando o TSI cruza acima "
             "do sinal e vende quando cruza abaixo (inverte). Com filtro de zona, a compra só vale se o cruzamento ocorre com TSI < 0 "
             "(venda com TSI > 0); a saída é sempre o cruzamento oposto. Stop de proteção k*ATR(14) (o original não tem stop)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"long": [13, 25, 40], "short": [7, 13], "signal": [7, 13], "zone": [0, 1], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def tsi(c, lg, sh):
    mom = pd.Series(c).diff().to_numpy()
    num = ind.ema(ind.ema(mom, lg), sh)
    den = ind.ema(ind.ema(np.abs(mom), lg), sh)
    with np.errstate(invalid="ignore", divide="ignore"):
        return 100 * num / den


def signals(df, p):
    c = df.close.values
    t = tsi(c, p["long"], p["short"])
    s = ind.ema(t, p["signal"])
    up = ind.cross_above(t, s)
    dn = ind.cross_below(t, s)
    eu, ed = up.copy(), dn.copy()
    if p["zone"]:
        eu &= t < 0
        ed &= t > 0
    entry = np.where(eu, 1, np.where(ed, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
