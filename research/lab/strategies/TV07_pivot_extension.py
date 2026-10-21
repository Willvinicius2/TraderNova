"""TV07 - Pivot Extension Strategy (estratégia embutida do TradingView)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV07_pivot_extension",
    "name": "Pivot Extension Strategy (TradingView)",
    "family": "reversao",
    "round": 2,
    "origin": "TradingView embutida",
    "sources": [
        "https://in.tradingview.com/support/solutions/43000599888-pivot-extension-strategy/",
        "https://www.oanda.jp/lab-education/?p=33258",
    ],
    "rule": ("Pine embutido (leftBars=4, rightBars=2): ph=ta.pivothigh(left,right), pl=ta.pivotlow(left,right) (pivôs de swing, "
             "não pivôs diários). Quando um pivô de baixa é confirmado (right candles depois), compra a mercado; quando um pivô de alta "
             "é confirmado, vende; sempre posicionado (doten). Se os dois confirmam no mesmo candle, nada. Entrada na abertura seguinte; "
             "side=long fecha no pivô de alta em vez de inverter; stop de proteção k*ATR14 (o Pine não tem stop)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"left": [2, 4, 6, 8], "right": [1, 2, 3], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def pivots(h, l, left, right):
    """ta.pivothigh/ta.pivotlow do Pine, causal: em i dá o pivô do candle j=i-right (confirmado no fechamento de i), senão NaN.
    Pivô de alta: high[j] estritamente maior que os 'left' candles anteriores e os 'right' seguintes."""
    hj, lj = ind.prev(h, right), ind.prev(l, right)
    lmax = ind.prev(ind.highest(h, left), right + 1)
    lmin = ind.prev(ind.lowest(l, left), right + 1)
    rmax, rmin = ind.highest(h, right), ind.lowest(l, right)
    with np.errstate(invalid="ignore"):
        ph = np.where((hj > lmax) & (hj > rmax), hj, np.nan)
        pl = np.where((lj < lmin) & (lj < rmin), lj, np.nan)
    return ph, pl


def signals(df, p):
    h, l = df.high.values, df.low.values
    ph, pl = pivots(h, l, p["left"], p["right"])
    lg = ~np.isnan(pl) & np.isnan(ph)
    sh = ~np.isnan(ph) & np.isnan(pl)
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": sh, "exit_short": lg}
