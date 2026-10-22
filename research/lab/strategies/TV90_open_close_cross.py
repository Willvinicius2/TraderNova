"""Open Close Cross Strategy R5.1 (JustUncleL), versão sem repintura: média do fechamento x média da abertura."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV90_open_close_cross",
    "name": "Open Close Cross Strategy R5.1 NoRepaint (JustUncleL)",
    "family": "tendencia",
    "round": 7,
    "origin": "TradingView comunidade (JustUncleL)",
    "sources": [
        "https://www.tradingview.com/script/9wda3yUw-Open-Close-Cross-Strategy-NoRepaint-Version-by-JustUncleL",
        "https://www.tradingview.com/script/BLY1wfiD-Open-Close-Cross-Alerts-NoRepaint-Version-by-JustUncleL",
        "https://github.com/deepentropy/lightweight-charts-indicators (src/community/open-close-cross.ts)",
    ],
    "rule": ("closeMA = média(tipo, len) do fechamento; openMA = mesma média da abertura. Compra quando closeMA cruza acima de "
             "openMA; venda (side=both) quando cruza abaixo; a estratégia inverte no cruzamento oposto (só compra: sai nele). "
             "O original usa um tempo gráfico maior (multiplicador 6 sobre período 8) com o candle anterior fechado (NoRepaint); "
             "aqui, como no port do deepentropy, o multiplicador vira período efetivo len = 8 × mult no próprio tempo gráfico, "
             "sem dados do candle em formação. Tipos de média do script: SMA, EMA, DEMA, SMMA, ZEMA. SL/TP do script vêm "
             "desligados: stop de proteção k × ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"ma": ["SMA", "EMA", "DEMA", "SMMA", "ZEMA"], "len": [16, 32, 48, 80], "k": [2.0, 3.5], "side": ["long", "both"]},
}


def smma(x, n):
    return pd.Series(x).ewm(alpha=1 / n, adjust=False, min_periods=n).mean().to_numpy(copy=True)


def variant(x, n, t):
    if t == "SMA":
        return ind.sma(x, n)
    if t == "EMA":
        return ind.ema(x, n)
    if t == "DEMA":
        e1 = ind.ema(x, n)
        e2 = pd.Series(e1).ewm(span=n, adjust=False, min_periods=n).mean().to_numpy()
        return 2 * e1 - e2
    if t == "SMMA":
        return smma(x, n)
    if t == "ZEMA":
        lag = (n - 1) // 2
        adj = x + (x - ind.prev(x, lag))
        adj[:lag] = x[:lag]
        return ind.ema(adj, n)
    raise ValueError(t)


def signals(df, p):
    o, c = df.open.values, df.close.values
    cm, om = variant(c, p["len"], p["ma"]), variant(o, p["len"], p["ma"])
    up = ind.cross_above(cm, om)
    dn = ind.cross_below(cm, om)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
