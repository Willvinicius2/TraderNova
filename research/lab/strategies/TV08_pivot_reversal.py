"""TV08 - Pivot Reversal Strategy (estratégia embutida do TradingView)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV08_pivot_reversal",
    "name": "Pivot Reversal Strategy (TradingView)",
    "family": "rompimento",
    "round": 2,
    "origin": "TradingView embutida",
    "sources": [
        "https://www.tradingview.com/support/folders/43000587406-built-in-strategies/ (Pivot Reversal Strategy)",
        "https://www.marketcalls.in/amibroker/pivot-reversal-strategy-tradingview-pinescript-to-amibroker-afl-conversion.html",
        "https://www.luxalgo.com/library/indicator/aqVvUNub-pivot-reversal-strategy/",
    ],
    "rule": ("Pine embutido (leftBars=4, rightBars=2): ao confirmar um pivô de alta (ta.pivothigh), guarda hprice e arma uma ordem "
             "stop de compra em hprice+tick, que fica ativa até a máxima passar de hprice (execução) ou surgir novo pivô de alta "
             "(novo nível); espelho para venda com pivô de baixa (ordem stop em lprice-tick). Sempre posicionado. A ordem stop é "
             "aproximada: trigger=close entra na abertura seguinte quando o fechamento passa do nível; trigger=touch entra na "
             "abertura seguinte ao candle cuja máxima/mínima tocou o nível (momento da execução no Pine, preço pior). "
             "side=long fecha no gatilho de venda em vez de inverter; stop de proteção k*ATR14 (o Pine não tem stop)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"left": [2, 4, 6], "right": [1, 2, 3], "k": [2.0, 3.0, 4.0], "side": ["long", "both"], "trigger": ["close", "touch"]},
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


def triggers(h, l, c, ph, pl, touch):
    n = len(h)
    lg = np.zeros(n, bool)
    sh = np.zeros(n, bool)
    le = se = False
    hp = lp = np.nan
    for i in range(n):
        # ordens armadas no fechamento de i-1 são testadas no candle i
        if le and (h[i] > hp if touch else c[i] > hp):
            lg[i] = True
            le = False
        if se and (l[i] < lp if touch else c[i] < lp):
            sh[i] = True
            se = False
        if not np.isnan(ph[i]):
            hp, le = ph[i], True
        if not np.isnan(pl[i]):
            lp, se = pl[i], True
    both = lg & sh
    return lg & ~both, sh & ~both


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    ph, pl = pivots(h, l, p["left"], p["right"])
    lg, sh = triggers(h, l, c, ph, pl, p["trigger"] == "touch")
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": sh, "exit_short": lg}
