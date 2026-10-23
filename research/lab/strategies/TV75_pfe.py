"""Polarized Fractal Efficiency (Hans Hannula, TASC jan/1994)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV75_pfe",
    "name": "Polarized Fractal Efficiency (Hannula): cruzamento do limiar",
    "family": "tendencia",
    "round": 6,
    "origin": "TradingView comunidade (definição clássica de Hannula)",
    "sources": [
        "https://www.luxalgo.com/library/concept/polarized-fractal-efficiency/",
        "https://cn.tradingview.com/script/OESOW4zd-Polarized-Fractal-Efficiency",
        "https://indicators.agenatrader.com/standard-indicators/polarized-fractal-efficiency-pfe",
        "Hannula, H. (1994), Polarized Fractal Efficiency, Technical Analysis of Stocks & Commodities, jan/1994",
    ],
    "sourceNote": "Código Pine não clonado (o TradingView não abre); fórmula da LuxAlgo/Hannula: PFE bruto = sinal(C-C[n]) * 100*sqrt(dC_n^2 + n^2) / soma_{n candles} sqrt(dC^2 + 1), "
                  "suavizado por EMA(m), n = 10 e m = 5 no original. Usada a variante em variação percentual (dC em % do preço), comum nos scripts do TradingView, "
                  "porque em dólares o termo n^2 some no preço do BTC. Indicador sem stop: k*ATR14.",
    "rule": "Compra quando o PFE(n, EMA m) cruza acima de +thr (thr=0: linha zero, regra simples); vende (both) quando cruza abaixo de -thr. "
            "Sai da compra quando o PFE cruza abaixo de 0 (venda: acima de 0). Stop k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [10, 14, 20], "m": [5, 8], "thr": [0, 25, 50], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def pfe(c, n, m):
    r1 = 100 * (c / ind.prev(c, 1) - 1)
    rn = 100 * (c / ind.prev(c, n) - 1)
    path = pd.Series(np.sqrt(r1 ** 2 + 1)).rolling(n).sum().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        raw = np.sign(rn) * 100 * np.sqrt(rn ** 2 + n ** 2) / path
    return pd.Series(raw).ewm(span=m, adjust=False, min_periods=m, ignore_na=True).mean().to_numpy()


def signals(df, p):
    c = df.close.values
    x = pfe(c, p["n"], p["m"])
    t = float(p["thr"])
    N = len(c)
    lg = ind.cross_above(x, np.full(N, t))
    sh = ind.cross_below(x, np.full(N, -t))
    exl = ind.cross_below(x, np.zeros(N))
    exs = ind.cross_above(x, np.zeros(N))
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
