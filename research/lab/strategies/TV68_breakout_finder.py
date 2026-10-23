"""Breakout Finder (LonesomeTheBlue), versão de estratégia."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV68_breakout_finder",
    "name": "Breakout Finder (LonesomeTheBlue)",
    "family": "rompimento",
    "round": 6,
    "origin": "TradingView comunidade (LonesomeTheBlue)",
    "sources": [
        "https://www.tradingview.com/script/EvkXjgyw-Breakout-Finder/",
        "https://www.luxalgo.com/library/indicator/EvkXjgyw-breakout-finder/",
        "github.com/deepentropy/lightweight-charts-indicators src/community/breakout-finder.ts (tradução do Pine, MPL-2.0)",
    ],
    "rule": ("Pine 'Breakout Finder': guarda pivôs de alta/baixa (pivothigh/low(prd,prd), confirmados prd candles depois) dos últimos "
             "200 candles. Compra quando um candle de alta fecha acima da máxima dos prd candles anteriores e acima de um grupo de "
             ">= mintest pivôs de alta que ficam numa faixa de largura cw% do range de 300 candles abaixo do maior pivô rompido "
             "(abertura <= topo da faixa e máxima anterior < topo). Venda no espelho com pivôs de baixa. O indicador não tem saída: "
             "stop inicial e stop móvel k*ATR14, sinal oposto inverte. Entrada na abertura seguinte."),
    "timeframes": ["H1", "H4"],
    "grid": {"prd": [3, 5, 8], "cw": [2.0, 3.0, 5.0], "mintest": [2, 3], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def pivots(h, l, L):
    """Valor do pivô no candle de confirmação i (centro em i-L); NaN se não houver."""
    n = len(h)
    ph = np.full(n, np.nan)
    pl = np.full(n, np.nan)
    for i in range(2 * L, n):
        c = i - L
        wh = h[c - L:i + 1]
        wl = l[c - L:i + 1]
        if h[c] >= wh.max() and (h[c - L:c] < h[c]).all():
            ph[i] = h[c]
        if l[c] <= wl.min() and (l[c - L:c] > l[c]).all():
            pl[i] = l[c]
    return ph, pl


def breakout_finder(df, prd, cw, mintest, boLen=200):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    n = len(c)
    ph, pl = pivots(h, l, prd)
    hp = ind.prev(ind.highest(h, prd))
    lp = ind.prev(ind.lowest(l, prd))
    h300 = pd.Series(h).rolling(300, min_periods=1).max().values
    l300 = pd.Series(l).rolling(300, min_periods=1).min().values
    cwu = cw / 100
    phv, phl, plv, pll = [], [], [], []
    bo = np.zeros(n, bool)
    bd = np.zeros(n, bool)
    for i in range(n):
        chw = (h300[i] - l300[i]) * cwu
        if not np.isnan(ph[i]):
            phv.insert(0, ph[i]); phl.insert(0, i - prd)
            while len(phv) > 1 and i - phl[-1] > boLen:
                phv.pop(); phl.pop()
        if not np.isnan(pl[i]):
            plv.insert(0, pl[i]); pll.insert(0, i - prd)
            while len(plv) > 1 and i - pll[-1] > boLen:
                plv.pop(); pll.pop()
        hg = hp[i]
        if len(phv) >= mintest and c[i] > o[i] and c[i] > hg:
            bomax = phv[0]; xx = 0
            for x in range(len(phv)):
                if phv[x] >= c[i]:
                    break
                xx = x; bomax = max(bomax, phv[x])
            if xx >= mintest and o[i] <= bomax:
                num = sum(1 for x in range(xx + 1) if bomax - chw <= phv[x] <= bomax)
                if num >= mintest and not hg >= bomax:
                    bo[i] = True
        lw = lp[i]
        if len(plv) >= mintest and c[i] < o[i] and c[i] < lw:
            bomin = plv[0]; xx = 0
            for x in range(len(plv)):
                if plv[x] <= c[i]:
                    break
                xx = x; bomin = min(bomin, plv[x])
            if xx >= mintest and o[i] >= bomin:
                num = sum(1 for x in range(xx + 1) if bomin <= plv[x] <= bomin + chw)
                if num >= mintest and not lw <= bomin:
                    bd[i] = True
    return bo, bd


_cache = {}


def signals(df, p):
    key = (id(df), len(df), p["prd"], p["cw"], p["mintest"])
    if key not in _cache:
        _cache[key] = breakout_finder(df, p["prd"], p["cw"], p["mintest"])
    bo, bd = _cache[key]
    entry = np.where(bo, 1, np.where(bd, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "trail": p["k"] * a}
