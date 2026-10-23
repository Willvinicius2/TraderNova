"""Double 7's (Connors & Alvarez, Short Term Trading Strategies That Work, 2008)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV61_double7",
    "name": "Double 7's de Connors: mínima de 7 fechamentos acima da SMA200",
    "family": "reversao",
    "round": 5,
    "origin": "TradingView comunidade (várias versões; regra do livro de Connors & Alvarez 2008)",
    "sources": [
        "https://strategyquant.com/blog/larry-connors-double-7-strategy-tested-on-spy-and-8-other-markets/",
        "https://www.tradingview.com/script/DzVF4GvJ-Connors-Double-Seven-with-options",
        "Connors & Alvarez (2008), Short Term Trading Strategies That Work, cap. Double 7's",
    ],
    "sourceNote": "Regra do StrategyQuant (fechamento > SMA200 e fechamento <= menor fechamento de 7 candles; sai quando fechamento >= maior "
                  "fechamento de 7). O script do TradingView é protegido; usada a regra do livro.",
    "rule": "Compra quando fechamento > SMA200 e o fechamento é o menor dos últimos n (inclui o atual); sai quando o fechamento é o maior dos "
            "últimos n. Venda espelhada (both) abaixo da SMA200. Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [5, 7, 10], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def signals(df, p):
    c = df.close.values
    n = p["n"]
    lo, hi = ind.lowest(c, n), ind.highest(c, n)
    s200 = ind.sma(c, 200)
    with np.errstate(invalid="ignore"):
        lg = (c > s200) & (c <= lo)
        sh = (c < s200) & (c >= hi)
        exl = c >= hi
        exs = c <= lo
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
