"""TV41 - Trend Trigger Factor (M. H. Pee, TASC dez/2004) / everget e LazyBear.

Pine (everget, GPL-3.0, oscillators/trend_trigger_factor.pine, commit 8385cc4): hh = highest(high,n), ll = lowest(low,n);
buyPower = hh - ll[n]; sellPower = hh[n] - ll; TTF = 200*(BP-SP)/(BP+SP).
Regras do autor (citadas no script de LazyBear): TTF acima de +100 = comprado; abaixo de -100 = vendido; entre os níveis mantém a
posição atual. Aqui: entra no cruzamento do nível e só sai no cruzamento do nível oposto (inversão). Stop de proteção k*ATR(14).
"""
import numpy as np

import indicators as ind

META = {
    "id": "TV41_ttf",
    "name": "Trend Trigger Factor (Pee / everget)",
    "family": "tendencia",
    "round": 4,
    "origin": "TradingView comunidade (LazyBear / everget)",
    "sources": [
        "https://www.tradingview.com/script/wSMZKu7B-Indicator-Trend-Trigger-Factor/",
        "https://github.com/everget/tradingview-pinescript-indicators/blob/master/oscillators/trend_trigger_factor.pine",
    ],
    "rule": ("BP = maior máxima(n) − menor mínima(n) de n candles atrás; SP = maior máxima de n candles atrás − menor mínima(n); "
             "TTF = 200*(BP−SP)/(BP+SP). Compra quando o TTF cruza acima de +nível, vende quando cruza abaixo de −nível; entre os "
             "níveis mantém a posição (sai só no cruzamento oposto). Stop de proteção k*ATR(14) (o original não tem stop)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [10, 15, 20, 30], "level": [75, 100, 125], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def signals(df, p):
    n = p["n"]
    hh = ind.highest(df.high.values, n)
    ll = ind.lowest(df.low.values, n)
    bp = hh - ind.prev(ll, n)
    sp = ind.prev(hh, n) - ll
    with np.errstate(invalid="ignore", divide="ignore"):
        ttf = 200 * (bp - sp) / (bp + sp)
    lv = np.full(len(ttf), float(p["level"]))
    up = ind.cross_above(ttf, lv)
    dn = ind.cross_below(ttf, -lv)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
