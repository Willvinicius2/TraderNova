"""Trendlines with Breaks (LuxAlgo), sem backpaint."""
import numpy as np

import indicators as ind

META = {
    "id": "TV69_trendline_breaks",
    "name": "Trendlines with Breaks (LuxAlgo, sem backpaint)",
    "family": "rompimento",
    "round": 6,
    "origin": "TradingView comunidade (LuxAlgo)",
    "sources": [
        "https://www.tradingview.com/script/IYL88A1N-Trendlines-with-Breaks-LuxAlgo/",
        "github.com/deepentropy/lightweight-charts-indicators src/community/trendlines-with-breaks.ts (tradução do Pine)",
    ],
    "rule": ("Pine 'Trendlines with Breaks' com backpaint=false (versão sem repintura): no pivô de alta (pivothigh(len,len), confirmado "
             "len candles depois) a linha de baixa parte do pivô e cai slope = ATR(len)/len*mult por candle; o valor de hoje é "
             "upper - slope*len. Compra quando o fechamento passa acima da linha de baixa (upos sobe de 0 para 1); vende quando "
             "o fechamento passa abaixo da linha de alta dos pivôs de baixa (dnos sobe). Sinal oposto inverte. Pine sem stop: "
             "stop de proteção k*ATR14. Entrada na abertura seguinte."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"length": [7, 10, 14, 20, 28], "mult": [0.5, 1.0, 1.5], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def pivots(h, l, L):
    n = len(h)
    ph = np.full(n, np.nan)
    pl = np.full(n, np.nan)
    for i in range(2 * L, n):
        c = i - L
        if h[c] >= h[c - L:i + 1].max() and (h[c - L:c] < h[c]).all():
            ph[i] = h[c]
        if l[c] <= l[c - L:i + 1].min() and (l[c - L:c] > l[c]).all():
            pl[i] = l[c]
    return ph, pl


def breaks(df, L, mult):
    h, l, c = df.high.values, df.low.values, df.close.values
    n = len(c)
    slope = ind.atr(df, L) / L * mult
    ph, pl = pivots(h, l, L)
    upper = lower = sph = spl = 0.0
    upos = np.zeros(n)
    dnos = np.zeros(n)
    for i in range(n):
        if not np.isnan(ph[i]):
            sph = slope[i]; upper = ph[i]
        else:
            upper -= sph
        if not np.isnan(pl[i]):
            spl = slope[i]; lower = pl[i]
        else:
            lower += spl
        pu = upos[i - 1] if i else 0
        pd_ = dnos[i - 1] if i else 0
        if not np.isnan(ph[i]):
            upos[i] = 0
        elif c[i] > upper - sph * L:
            upos[i] = 1
        else:
            upos[i] = pu
        if not np.isnan(pl[i]):
            dnos[i] = 0
        elif c[i] < lower + spl * L:
            dnos[i] = 1
        else:
            dnos[i] = pd_
    up = upos > ind.prev(upos)
    dn = dnos > ind.prev(dnos)
    return up, dn


_cache = {}


def signals(df, p):
    key = (id(df), len(df), p["length"], p["mult"])
    if key not in _cache:
        _cache[key] = breaks(df, p["length"], p["mult"])
    up, dn = _cache[key]
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": dn}
