"""TV43 - Ultimate RSI [LuxAlgo].

Lógica (tradução em deepentropy/lightweight-charts-indicators, src/community/ultimate-rsi.ts, commit f8e1b0e):
upper = highest(close,n), lower = lowest(close,n), r = upper-lower; diff = r se upper subiu, -r se lower caiu, senão Δfech;
aRSI = RMA(diff,n)/RMA(|diff|,n)*50+50; sinal = EMA(aRSI, m). Sem repintura.
LuxAlgo descreve o uso como tendência: aRSI acima de 50 = alta, cruzamento com o sinal = momento subindo/caindo.
Modos: "mid" compra no cruzamento acima de 50 e vende abaixo; "signal" compra no cruzamento acima do sinal e vende abaixo.
Inverte a mão no sinal oposto. Stop de proteção k*ATR(14).
"""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV43_ultimate_rsi",
    "name": "Ultimate RSI (LuxAlgo)",
    "family": "momento",
    "round": 4,
    "origin": "TradingView comunidade (LuxAlgo)",
    "sources": [
        "https://tradingview.com/script/17Jj7Vcg-Ultimate-RSI-LuxAlgo",
        "https://www.luxalgo.com/library/indicator/ultimate-rsi/",
        "https://github.com/deepentropy/lightweight-charts-indicators/blob/main/src/community/ultimate-rsi.ts",
    ],
    "rule": ("Diferença usada no RSI = amplitude máx−mín de n candles quando há nova máxima (positiva) ou nova mínima (negativa), "
             "senão a variação do fechamento; aRSI = RMA(diff)/RMA(|diff|)*50+50, sinal = EMA(aRSI,m). Modo mid: compra ao cruzar "
             "acima de 50, vende abaixo. Modo signal: compra ao cruzar acima do sinal, vende abaixo. Inverte no oposto; stop k*ATR(14)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [7, 14, 21, 28], "m": [7, 14, 21], "mode": ["mid", "signal"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def rma(x, n):
    return pd.Series(x).ewm(alpha=1 / n, adjust=False, min_periods=n).mean().to_numpy()


def arsi(c, n):
    up = ind.highest(c, n)
    lo = ind.lowest(c, n)
    r = up - lo
    d = np.r_[0.0, np.diff(c)]
    pu, pl = ind.prev(up), ind.prev(lo)
    diff = np.where(up > pu, r, np.where(lo < pl, -r, d))
    num, den = rma(diff, n), rma(np.abs(diff), n)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = num / den * 50 + 50
    out[:n] = np.nan
    return out


def signals(df, p):
    c = df.close.values
    a = arsi(c, p["n"])
    ref = np.full(len(c), 50.0) if p["mode"] == "mid" else ind.ema(a, p["m"])
    up = ind.cross_above(a, ref)
    dn = ind.cross_below(a, ref)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
