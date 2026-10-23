"""CCI de Donald Lambert (1980): regra de cruzamento de +100 / -100."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV23_cci",
    "name": "CCI (Lambert): rompimento de ±100",
    "family": "momento",
    "round": 2,
    "origin": "TradingView comunidade (Donald Lambert, indicador CCI)",
    "sources": [
        "https://www.barchart.com/trader/help/studies/cci.php",
        "https://fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/cci",
        "https://en.wikipedia.org/wiki/Commodity_channel_index",
        "https://kr.tradingview.com/script/5rwCAgVK-Commodity-Channel-Index-CCI",
    ],
    "rule": ("CCI = (TP - SMA(TP,n)) / (0,015 * desvio médio(TP,n)), TP = (máx+mín+fech)/3 (fonte padrão hlc3 do CCI do TradingView). "
             "Regra publicada de Lambert: compra quando o CCI cruza acima de +100 e fecha a compra quando volta abaixo de +100; "
             "vende (side=both) quando cruza abaixo de -100 e fecha quando volta acima de -100. Variante de saída 'zero': mantém "
             "até o CCI cruzar 0. Sem stop na fonte: stop de proteção k*ATR(14)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [14, 20, 30, 50], "exit": ["lambert", "zero"], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def cci(df, n):
    tp = ((df.high + df.low + df.close) / 3).values
    s = pd.Series(tp)
    ma = s.rolling(n).mean()
    md = s.rolling(n).apply(lambda v: np.mean(np.abs(v - v.mean())), raw=True)
    return ((s - ma) / (0.015 * md)).values


_cache = {}


def signals(df, p):
    key = (id(df), len(df), p["n"])
    if key not in _cache:
        _cache[key] = cci(df, p["n"])
    x = _cache[key]
    hi, lo, z = np.full(len(x), 100.0), np.full(len(x), -100.0), np.zeros(len(x))
    el = ind.cross_above(x, hi)
    es = ind.cross_below(x, lo)
    if p["exit"] == "lambert":
        xl, xs = ind.cross_below(x, hi), ind.cross_above(x, lo)
    else:
        xl, xs = ind.cross_below(x, z), ind.cross_above(x, z)
    entry = np.where(el, 1, np.where(es, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": xl, "exit_short": xs}
