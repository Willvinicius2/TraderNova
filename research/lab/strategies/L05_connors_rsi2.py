"""RSI(2) de Larry Connors com filtro SMA200 (Connors & Alvarez, 'Short Term Trading Strategies That Work', 2008)."""
import numpy as np

import indicators as ind

META = {
    "id": "L05_connors_rsi2",
    "name": "RSI(2) de Connors com filtro SMA200",
    "family": "reversao",
    "sources": [
        "https://www.luxalgo.com/library/concept/rsi-2/",
        "https://backtrex.com/en/backtests/connors-rsi-2-sp-500",
        "Connors & Alvarez (2008), Short Term Trading Strategies That Work, cap. RSI(2)",
    ],
    "rule": "Compra quando o fechamento está acima da SMA200 e o RSI(2) fecha abaixo do limiar (5/10/15); sai quando fecha acima da SMA5 "
            "(ou abaixo da SMA200). Venda espelhada: abaixo da SMA200 e RSI(2) acima de 100-limiar, sai ao fechar abaixo da SMA5. "
            "Stop de proteção k*ATR14 (a fonte não usa stop; o motor exige um).",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"thr": [5, 10, 15], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def signals(df, p):
    c = df.close.values
    r = ind.rsi(c, 2)
    s200, s5 = ind.sma(c, 200), ind.sma(c, 5)
    with np.errstate(invalid="ignore"):
        lg = (c > s200) & (r < p["thr"])
        sh = (c < s200) & (r > 100 - p["thr"])
        exl = (c > s5) | (c < s200)
        exs = (c < s5) | (c > s200)
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
