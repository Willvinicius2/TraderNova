"""L22 - Linear Regression Slope (inclinação da regressão linear)."""
import numpy as np

import indicators as ind

META = {
    "id": "L22_linreg_slope",
    "name": "Linear Regression Slope: cruzamento de limiar da inclinação normalizada",
    "family": "tendencia",
    "round": 8,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/slope",
        "https://toslc.thinkorswim.com/center/reference/Tech-Indicators/studies-library/G-L/LinearRegressionSlope",
    ],
    "rule": ("Inclinação b da regressão linear de mínimos quadrados do fechamento nos últimos n candles; normalizada s = b*n/ATR14 "
             "(subida da reta na janela, em ATRs, para servir em qualquer preço). StockCharts: inclinação positiva = alta, cruzamento do zero = "
             "mudança de tendência. Compra quando s cruza acima de +thr (thr=0: cruzamento do zero); vende (both) quando cruza abaixo de -thr. "
             "Sai da compra quando s cruza abaixo de 0 (venda: acima de 0). Sem stop na fonte: stop de proteção k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [20, 50, 100], "thr": [0.0, 0.5, 1.0, 2.0], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def lr_slope(c, n):
    x = np.arange(n, dtype=float)
    xm = x.mean()
    w = (x - xm) / ((x - xm) ** 2).sum()
    out = np.full(len(c), np.nan)
    if len(c) >= n:
        win = np.lib.stride_tricks.sliding_window_view(np.asarray(c, float), n)
        out[n - 1:] = win @ w
    return out


def signals(df, p):
    c = df.close.values
    a = ind.atr(df, 14)
    s = lr_slope(c, p["n"]) * p["n"] / a
    thr = p["thr"]
    up = ind.cross_above(s, np.full(len(c), thr))
    dn = ind.cross_below(s, np.full(len(c), -thr))
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    z = np.zeros(len(c))
    return {"entry": entry, "stop": p["k"] * a, "exit_long": ind.cross_below(s, z), "exit_short": ind.cross_above(s, z)}
