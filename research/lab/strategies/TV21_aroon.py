"""Aroon (Tushar Chande): cruzamento Aroon Up / Aroon Down."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV21_aroon",
    "name": "Aroon (Chande): cruzamento Up/Down",
    "family": "tendencia",
    "round": 2,
    "origin": "TradingView comunidade (Tushar Chande, indicador Aroon)",
    "sources": [
        "https://in.tradingview.com/support/solutions/43000501801",
        "https://help.ctrader.com/indicators/built-in/trend/aroon/",
        "https://www.oanda.jp/lab-education/tradingviewstrategy/basic/tradingview_aroon_setting",
    ],
    "rule": ("Aroon Up = 100*(n - candles desde a máxima de n+1 candles)/n; Aroon Down idem com a mínima (fórmula do Pine ta.aroon "
             "com highestbars(length+1)). Compra quando Aroon Up cruza acima de Aroon Down (opcional: Up >= nível, ex. 70, "
             "confirmando força como na leitura 'Up perto de 100 e Down abaixo de 50'); vende (side=both) no cruzamento inverso; "
             "sai no cruzamento oposto. Sem stop na fonte: stop de proteção k*ATR(14)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [14, 25, 50], "level": [0, 70], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def aroon(df, n):
    h, l = df.high.values, df.low.values
    since_h = pd.Series(h).rolling(n + 1).apply(lambda v: n - (len(v) - 1 - int(np.where(v == v.max())[0][-1])), raw=True).values
    since_l = pd.Series(l).rolling(n + 1).apply(lambda v: n - (len(v) - 1 - int(np.where(v == v.min())[0][-1])), raw=True).values
    return 100 * since_h / n, 100 * since_l / n


_cache = {}


def signals(df, p):
    key = (id(df), len(df), p["n"])
    if key not in _cache:
        _cache[key] = aroon(df, p["n"])
    up, dn = _cache[key]
    cu = ind.cross_above(up, dn)
    cd = ind.cross_below(up, dn)
    lv = p["level"]
    el = cu & (up >= lv)
    es = cd & (dn >= lv)
    entry = np.where(el, 1, np.where(es, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": cd, "exit_short": cu}
