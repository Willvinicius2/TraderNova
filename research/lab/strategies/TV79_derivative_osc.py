"""TV79 - Derivative Oscillator (Constance Brown; everget no TradingView)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV79_derivative_osc",
    "name": "Derivative Oscillator (Constance Brown/everget): RSI suavizado menos sua SMA9, cruzamento do zero",
    "family": "momento",
    "round": 6,
    "origin": "TradingView comunidade (everget)",
    "sources": [
        "https://github.com/everget/tradingview-pinescript-indicators (oscillators/derivative_oscillator.pine, Pine original de everget)",
        "https://help.tc2000.com/m/69445/l/755852-derivative-oscillator",
        "https://in.tradingview.com/script/6wfwJ6To-Indicator-Derivative-Oscillator",
    ],
    "rule": ("Pine everget: sRSI = EMA3(EMA5(RSI(rsi))); DOSC = sRSI - SMA9(sRSI); sinal = SMA9(DOSC). Brown (Technical "
             "Analysis for the Trading Professional): compra quando o DOSC cruza acima de 0, vende quando cruza abaixo "
             "(trig=zero) ou, variante, DOSC cruzando a linha de sinal (trig=signal). Filtro de regime opcional: compra só com "
             "fechamento > EMA(trend) e venda só abaixo (0 = sem filtro). O cruzamento oposto sempre fecha. O script não tem "
             "stop: stop k*ATR14. Entrada na abertura seguinte."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"rsi": [9, 14, 21], "trig": ["zero", "signal"], "trend": [0, 100, 200], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    c = df.close.values
    s = ind.ema(ind.ema(ind.rsi(c, p["rsi"]), 5), 3)
    d = s - ind.sma(s, 9)
    ref = np.zeros(len(c)) if p["trig"] == "zero" else ind.sma(d, 9)
    up, dn = ind.cross_above(d, ref), ind.cross_below(d, ref)
    buy, sell = up.copy(), dn.copy()
    if p["trend"]:
        e = ind.ema(c, p["trend"])
        buy &= c > e
        sell &= c < e
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": dn, "exit_short": up}
