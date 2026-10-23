"""Relative Volatility Index (Donald Dorsey, TASC 1993/1995), código Pine de everget (versão refinada)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV74_rvi",
    "name": "Relative Volatility Index refinado (Dorsey): cruzamento do nível com filtro de tendência",
    "family": "volatilidade",
    "round": 6,
    "origin": "TradingView comunidade (everget)",
    "sources": [
        "github.com/everget/tradingview-pinescript-indicators oscillators/relative_volatility_index.pine (GPL-3.0)",
        "https://www.luxalgo.com/library/concept/relative-volatility-index/",
    ],
    "sourceNote": "Pine de everget (refinado 1995): RVI = média de RVI(máxima) e RVI(mínima); RVI(x) = 100*EMA14(desvio10 se x subiu)/(EMA14(desvio10 se subiu)+EMA14(desvio10 se caiu)), "
                  "desvio populacional de 10. Dorsey usa o RVI como confirmação (comprar só acima de 50, vender abaixo de 50; 60/40 como níveis de reforço). "
                  "Indicador sem stop: k*ATR14.",
    "rule": "Compra quando o RVI cruza acima de lvl (50 = regra simples; 55/60 = confirmação mais forte) e, se trend>0, fechamento acima da EMA(trend); "
            "vende (both) quando cruza abaixo de 100-lvl e fechamento abaixo da EMA(trend). Sai da compra quando o RVI cruza abaixo de 50 "
            "(venda: acima de 50). Stop k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"lvl": [50, 55, 60], "trend": [0, 100, 200], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def rvi_one(x, sd, n=14):
    ch = np.r_[np.nan, np.diff(x)]
    u = np.where(ch >= 0, sd, 0.0)
    d = np.where(ch >= 0, 0.0, sd)
    u[np.isnan(sd) | np.isnan(ch)] = np.nan
    d[np.isnan(sd) | np.isnan(ch)] = np.nan
    eu = pd.Series(u).ewm(span=n, adjust=False, min_periods=n, ignore_na=True).mean().to_numpy()
    ed = pd.Series(d).ewm(span=n, adjust=False, min_periods=n, ignore_na=True).mean().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        return 100 * eu / (eu + ed)


def rvi(df):
    h, l = df.high.values, df.low.values
    return (rvi_one(h, ind.stdev(h, 10)) + rvi_one(l, ind.stdev(l, 10))) / 2


def signals(df, p):
    c = df.close.values
    r = rvi(df)
    lvl = p["lvl"]
    if p["trend"]:
        e = ind.ema(c, p["trend"])
        tu, td = c > e, c < e
    else:
        tu = td = np.ones(len(c), bool)
    lg = ind.cross_above(r, np.full(len(c), lvl)) & tu
    sh = ind.cross_below(r, np.full(len(c), 100 - lvl)) & td
    exl = ind.cross_below(r, np.full(len(c), 50.0))
    exs = ind.cross_above(r, np.full(len(c), 50.0))
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
