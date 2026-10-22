"""L27 - TRIX (Jack Hutson, 1980)."""
import numpy as np

import indicators as ind

META = {
    "id": "L27_trix",
    "name": "TRIX: cruzamento da linha de sinal ou do zero",
    "family": "momento",
    "round": 8,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/trix",
        "https://rdrr.io/cran/TTR/man/TRIX.html",
    ],
    "rule": ("StockCharts: E3 = EMA(n) de EMA(n) de EMA(n) do fechamento; TRIX = variação % de 1 candle de E3; sinal = EMA9(TRIX). "
             "trig=signal: compra quando TRIX cruza acima do sinal, vende (side=both) quando cruza abaixo. trig=zero: compra "
             "quando TRIX cruza acima de zero (E3 passa a subir), vende quando cruza abaixo. O cruzamento oposto sempre fecha. "
             "Filtro de regime opcional EMA(trend). Sem stop na fonte: stop de proteção k*ATR14. Entrada na abertura seguinte."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [9, 15, 30], "trig": ["signal", "zero"], "trend": [0, 200], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    c = df.close.values.astype(float)
    n = p["n"]
    e3 = ind.ema(ind.ema(ind.ema(c, n), n), n)
    trix = 100.0 * (e3 / ind.prev(e3, 1) - 1.0)
    ref = np.zeros(len(c)) if p["trig"] == "zero" else ind.ema(trix, 9)
    up, dn = ind.cross_above(trix, ref), ind.cross_below(trix, ref)
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
