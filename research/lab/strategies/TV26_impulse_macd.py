"""Impulse MACD (LazyBear, TradingView comunidade)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV26_impulse_macd",
    "name": "Impulse MACD (LazyBear)",
    "family": "tendencia",
    "round": 3,
    "origin": "TradingView comunidade (LazyBear)",
    "sources": [
        "https://www.tradingview.com/script/qt6xLfLi-Impulse-MACD-LazyBear/",
        "https://prorealcode.com/topic/conversion-indicateur-tradingview-impulse-macd-de-lazybear",
        "https://raw.githubusercontent.com/remiotore/freqtrade/44beaeb6a420cd8e9f2e4ea93e11d6cfa192ee03/strategies/ImpulseMACD.py",
    ],
    "sourceNote": "TradingView inacessível; fórmulas do Pine conferidas no porte freqtrade (GitHub remiotore/freqtrade) e na conversão ProRealCode.",
    "rule": "Pine de LazyBear: hi = SMMA(máxima, n), lo = SMMA(mínima, n), mi = ZLEMA(hlc3, n) (2*EMA - EMA(EMA)); md = mi-hi se mi>hi, mi-lo se mi<lo, senão 0; sinal = SMA(md, 9). "
            "Gatilho 'zero': compra quando md passa de <=0 para >0 (preço sai do canal SMMA por cima), vende no inverso; sai quando md volta a <=0 (>=0 na venda). "
            "Gatilho 'signal': compra quando md cruza acima do sinal com md>0, vende no inverso com md<0; sai no cruzamento oposto md/sinal. Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [21, 34, 55], "trigger": ["zero", "signal"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def smma(x, n):
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    out[n - 1] = x[:n].mean()
    for i in range(n, len(x)):
        out[i] = (out[i - 1] * (n - 1) + x[i]) / n
    return out


def signals(df, p):
    n = p["n"]
    src = (df.high.values + df.low.values + df.close.values) / 3
    hi, lo = smma(df.high.values, n), smma(df.low.values, n)
    e1 = ind.ema(src, n)
    e2 = ind.ema(e1, n)
    mi = 2 * e1 - e2
    with np.errstate(invalid="ignore"):
        md = np.where(mi > hi, mi - hi, np.where(mi < lo, mi - lo, 0.0))
    md = np.where(np.isnan(hi) | np.isnan(mi), np.nan, md)
    sb = ind.sma(md, 9)
    pm = ind.prev(md)
    with np.errstate(invalid="ignore"):
        if p["trigger"] == "zero":
            lg = (md > 0) & (pm <= 0)
            sh = (md < 0) & (pm >= 0)
            exl = md <= 0
            exs = md >= 0
        else:
            ca, cb = ind.cross_above(md, sb), ind.cross_below(md, sb)
            lg = ca & (md > 0)
            sh = cb & (md < 0)
            exl, exs = cb, ca
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
