"""Ehlers Roofing Filter (everget, TradingView comunidade). Fonte Pine: everget/tradingview-pinescript-indicators."""
import math

import numpy as np

import indicators as ind

META = {
    "id": "TV51_roofing",
    "name": "Ehlers Roofing Filter (everget): cruzamento do zero ou do próprio valor 2 candles atrás",
    "family": "reversao",
    "round": 4,
    "origin": "TradingView comunidade (everget; John F. Ehlers, Stocks & Commodities V.32:1, 2014)",
    "sources": [
        "https://www.tradingview.com/script/rVixuZKT-Ehlers-Roofing-Filter/",
        "https://github.com/everget/tradingview-pinescript-indicators/blob/master/oscillators/ehlers_roofing_filter.pine",
    ],
    "sourceNote": "TradingView inacessível pelo WebFetch; resumo pelo WebSearch e código Pine do repositório do autor. "
                  "O indicador não traz regra de trade; usamos as duas leituras da FILA (zero e Roof[2], esta como em Ehlers 2014).",
    "rule": "HP = passa-alta de 2 polos (período hp); Roof = SuperSmoother 2 polos (período ssf) de (HP+HP1)/2. "
            "Modo 'zero': compra quando Roof cruza acima de 0, vende abaixo. Modo 'lag2': compra quando Roof cruza acima de Roof[2], vende abaixo. "
            "Sai no sinal oposto. Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"hp": [32, 48, 64, 80], "ssf": [10, 14], "mode": ["zero", "lag2"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def roof(x, hpl, ssfl):
    x = np.asarray(x, float)
    n = len(x)
    a = 2 * math.pi / (hpl * math.sqrt(2))
    al = (math.cos(a) + math.sin(a) - 1) / math.cos(a)
    c1, c2, c3 = (1 - al / 2) ** 2, 2 * (1 - al), -(1 - al) ** 2
    hp = np.zeros(n)
    for i in range(2, n):
        hp[i] = c1 * (x[i] - 2 * x[i - 1] + x[i - 2]) + c2 * hp[i - 1] + c3 * hp[i - 2]
    arg = math.sqrt(2) * math.pi / ssfl
    a1 = math.exp(-arg)
    b2 = 2 * a1 * math.cos(arg)
    b3 = -a1 * a1
    b1 = 1 - b2 - b3
    src = hp.copy()
    src[1:] = (hp[1:] + hp[:-1]) / 2
    out = np.zeros(n)
    for i in range(2, n):
        out[i] = b1 * src[i] + b2 * out[i - 1] + b3 * out[i - 2]
    return out


def signals(df, p):
    r = roof(df.close.values, p["hp"], p["ssf"])
    ref = np.zeros(len(r)) if p["mode"] == "zero" else ind.prev(r, 2)
    up, dn = ind.cross_above(r, ref), ind.cross_below(r, ref)
    warm = np.arange(len(r)) < 3 * p["hp"]
    up &= ~warm
    dn &= ~warm
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
