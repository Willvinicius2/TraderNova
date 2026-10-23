"""L25 - Coppock Curve (Edwin Coppock, Barron's 1962)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L25_coppock",
    "name": "Coppock Curve: cruzamento da linha zero",
    "family": "momento",
    "round": 8,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/coppock-curve",
        "https://www.luxalgo.com/blog/coppock-curve-long-term-momentum-for-market-direction/",
    ],
    "rule": ("Coppock = WMA(10) de [ROC(14) + ROC(11)] (Coppock, períodos mensais no original; aqui todos os períodos "
             "multiplicados por 'scale' no tempo gráfico testado). StockCharts: compra quando a curva cruza de negativo para "
             "positivo; Coppock não usava sinal de venda, mas muitos analistas usam o cruzamento abaixo de zero para sair "
             "(side=long) ou vender (side=both). Filtro de regime opcional: compra só com fechamento > EMA(trend), venda só "
             "abaixo (0 = sem filtro). O cruzamento oposto sempre fecha. Sem stop no original: stop de proteção k*ATR14. "
             "Entrada na abertura seguinte."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"scale": [1, 2, 4, 8], "trend": [0, 200], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def wma(x, n):
    w = np.arange(1, n + 1, dtype=float)
    return pd.Series(x).rolling(n).apply(lambda v: np.dot(v, w) / w.sum(), raw=True).to_numpy(copy=True)


def roc(c, n):
    return 100.0 * (c / ind.prev(c, n) - 1.0)


def signals(df, p):
    c = df.close.values.astype(float)
    s = p["scale"]
    cop = wma(roc(c, 14 * s) + roc(c, 11 * s), 10 * s)
    z = np.zeros(len(c))
    up, dn = ind.cross_above(cop, z), ind.cross_below(cop, z)
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
