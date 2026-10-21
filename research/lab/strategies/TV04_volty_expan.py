"""TV04 - Volty Expan Close Strategy (estratégia embutida do TradingView)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV04_volty_expan",
    "name": "Volty Expan Close Strategy (TradingView)",
    "family": "volatilidade",
    "round": 2,
    "origin": "TradingView embutida",
    "sources": [
        "https://www.tradingview.com/support/solutions/43000599890-volty-expan-close-strategy/",
        "https://www.oanda.jp/lab-education/?p=34388",
        "https://www.tradingview.com/script/PRck7Phi-Volty-Expan-Close-Strategy-with-Backtest-Date-Range/",
    ],
    "rule": ("Pine original: atrs = SMA(TrueRange, length) * numATRs (padrão 5 e 0,75); a cada candle coloca compra stop em "
             "fech + atrs e venda stop em fech - atrs para o candle seguinte; sempre posicionado, inverte a cada rompimento. "
             "Aproximação do motor: sinal quando o fechamento do candle i passa de fech[i-1] ± atrs[i-1], entrada na abertura de i+1. "
             "O Pine não tem stop: usamos stop de proteção k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"length": [3, 5, 8, 13], "mult": [0.5, 0.75, 1.0, 1.5], "k": [2.0, 3.0, 4.5], "side": ["long", "both"]},
}


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    pc = ind.prev(c)
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    atrs = pd.Series(tr).rolling(p["length"]).mean().values * p["mult"]
    up_lvl = ind.prev(c + atrs)
    dn_lvl = ind.prev(c - atrs)
    up = c > up_lvl
    dn = c < dn_lvl
    entry = np.where(up, 1, np.where(dn, -1, 0))
    exl = None
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
        exl = dn
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": exl}
