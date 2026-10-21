"""TV05 - InSide Bar Strategy (estratégia embutida do TradingView)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV05_inside_bar",
    "name": "InSide Bar Strategy (TradingView)",
    "family": "padroes",
    "round": 2,
    "origin": "TradingView embutida",
    "sources": [
        "https://in.tradingview.com/support/solutions/43000591665-inside-bar-strategy/",
        "https://www.oanda.jp/lab-education/tradingviewstrategy/strategy/tradingview_inside_bar_strategy",
    ],
    "rule": ("Pine embutido: se high<high[1] e low>low[1] (candle interno), compra a mercado se o candle interno é de alta (close>open) "
             "e vende se é de baixa (close<open); sem parâmetros e sem stop, sempre posicionado (o sinal oposto inverte). "
             "Aqui: entrada na abertura seguinte; side=long fecha a compra no sinal de venda em vez de inverter; "
             "stop de proteção k*ATR14 (o Pine não tem stop, o motor exige)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"k": [1.5, 2.0, 3.0, 4.0, 6.0], "side": ["long", "both"]},
}


def signals(df, p):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    inside = (h < ind.prev(h)) & (l > ind.prev(l))
    lg = inside & (c > o)
    sh = inside & (c < o)
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": sh, "exit_short": lg}
