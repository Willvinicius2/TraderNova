"""TV06 - OutSide Bar Strategy (estratégia embutida do TradingView)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV06_outside_bar",
    "name": "OutSide Bar Strategy (TradingView)",
    "family": "padroes",
    "round": 2,
    "origin": "TradingView embutida",
    "sources": [
        "https://www.tradingview.com/support/folders/43000587406-built-in-strategies/ (OutSide Bar Strategy; página não abriu no WebFetch)",
        "https://www.oanda.jp/lab-education/?p=33250 (OutSide Bar Strategy)",
    ],
    "rule": ("Pine embutido: se high>high[1] e low<low[1] (candle externo), compra a mercado se o candle externo é de alta (close>open) "
             "e vende se é de baixa (close<open); sem parâmetros e sem stop, sempre posicionado (o sinal oposto inverte). "
             "Aqui: entrada na abertura seguinte; side=long fecha a compra no sinal de venda em vez de inverter; "
             "stop de proteção k*ATR14 (o Pine não tem stop, o motor exige)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"k": [1.5, 2.0, 3.0, 4.0, 6.0], "side": ["long", "both"]},
}


def signals(df, p):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    outside = (h > ind.prev(h)) & (l < ind.prev(l))
    lg = outside & (c > o)
    sh = outside & (c < o)
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": sh, "exit_short": lg}
