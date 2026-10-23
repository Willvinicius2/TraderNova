"""TV42 - Trend Continuation Factor (M. H. Pee, TASC mar/2002) / everget.

Pine (everget, GPL-3.0, oscillators/trend_continuation_factor.pine, commit 8385cc4):
plusChange = max(Δfech,0); minusChange = max(-Δfech,0); plusCF acumula plusChange enquanto ele não zera (minusCF idem);
+TCF = soma(plusChange − minusCF, n); −TCF = soma(minusChange − plusCF, n).
Regra de Pee: comprado quando +TCF > 0, vendido quando −TCF > 0 (os dois negativos = lateral). Entrada quando o estado liga.
Saída "neutral": fecha quando o próprio lado deixa de ser positivo; "opposite": só quando o lado oposto fica positivo.
Stop de proteção k*ATR(14).
"""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV42_tcf",
    "name": "Trend Continuation Factor (Pee / everget)",
    "family": "tendencia",
    "round": 4,
    "origin": "TradingView comunidade (everget)",
    "sources": [
        "https://github.com/everget/tradingview-pinescript-indicators/blob/master/oscillators/trend_continuation_factor.pine",
        "https://www.traders.com/Documentation/FEEDbk_docs/2002/03/Abstracts_new/Pee/pee.html",
        "https://www.tradingview.com/script/ymW2vLS6/",
    ],
    "rule": ("+TCF = soma em n candles de (alta do candle − sequência acumulada de quedas); −TCF espelhado. Compra quando +TCF passa a "
             "ser > 0, vende quando −TCF passa a ser > 0. Saída: quando o próprio lado deixa de ser positivo (neutral) ou só quando "
             "o lado oposto fica positivo (opposite). Stop de proteção k*ATR(14) (o original não tem stop)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [20, 35, 50], "exit": ["neutral", "opposite"], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def tcf(c, n):
    d = np.r_[np.nan, np.diff(c)]
    pc = np.where(d > 0, d, 0.0)
    mc = np.where(d > 0, 0.0, -np.nan_to_num(d))
    pcf = np.zeros(len(c))
    mcf = np.zeros(len(c))
    for i in range(1, len(c)):
        pcf[i] = 0.0 if pc[i] == 0 else pc[i] + pcf[i - 1]
        mcf[i] = 0.0 if mc[i] == 0 else mc[i] + mcf[i - 1]
    plus = pd.Series(pc - mcf).rolling(n).sum().to_numpy()
    minus = pd.Series(mc - pcf).rolling(n).sum().to_numpy()
    return plus, minus


def signals(df, p):
    plus, minus = tcf(df.close.values, p["n"])
    bull = np.nan_to_num(plus, nan=-1) > 0
    bear = np.nan_to_num(minus, nan=-1) > 0
    pb, pr = np.r_[False, bull[:-1]], np.r_[False, bear[:-1]]
    up = bull & ~pb
    dn = bear & ~pr
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    if p["exit"] == "neutral":
        exl, exs = ~bull, ~bear
    else:
        exl, exs = bear, bull
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
