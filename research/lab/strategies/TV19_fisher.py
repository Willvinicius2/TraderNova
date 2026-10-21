"""Fisher Transform de John Ehlers (indicador do TradingView / estratégia 'Fisher Crossover' da comunidade)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV19_fisher",
    "name": "Fisher Transform (Ehlers): cruzamento Fisher/Trigger em extremo",
    "family": "reversao",
    "round": 2,
    "origin": "TradingView comunidade (Fisher Crossover Strategy; indicador de John Ehlers)",
    "sources": [
        "https://www.tradingview.com/script/oVoigpVw-Fisher-Crossover-Strategy",
        "https://www.tradingview.com/support/solutions/43000589141-fisher-transform/",
        "https://www.luxalgo.com/library/indicator/fisher-transform/",
    ],
    "sourceNote": "TradingView inacessível pelo WebFetch; fórmula do indicador embutido (Pine de Ehlers) e regra de cruzamento com nível dos resumos do WebSearch.",
    "rule": "hl2 = (máx+mín)/2; v = 0,66*((hl2-mín_n)/(máx_n-mín_n)-0,5) + 0,67*v anterior, limitado a ±0,999; "
            "Fisher = 0,5*ln((1+v)/(1-v)) + 0,5*Fisher anterior; Trigger = Fisher do candle anterior. "
            "Compra quando Fisher cruza acima do Trigger estando abaixo de -nível; vende quando cruza abaixo estando acima de +nível. "
            "Sai no cruzamento oposto. Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [7, 9, 13], "lvl": [0.0, 0.5, 1.0, 1.5], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def fisher(df, n):
    hl2 = (df.high.values + df.low.values) / 2
    hh, ll = ind.highest(hl2, n), ind.lowest(hl2, n)
    N = len(hl2)
    v = np.zeros(N)
    fi = np.full(N, np.nan)
    pv, pfi = 0.0, 0.0
    for i in range(N):
        if np.isnan(hh[i]):
            continue
        rng = hh[i] - ll[i]
        x = 0.66 * (((hl2[i] - ll[i]) / rng if rng > 0 else 0.5) - 0.5) + 0.67 * pv
        x = min(max(x, -0.999), 0.999)
        f = 0.5 * np.log((1 + x) / (1 - x)) + 0.5 * pfi
        v[i], fi[i] = x, f
        pv, pfi = x, f
    return fi


def signals(df, p):
    f = fisher(df, p["n"])
    t = ind.prev(f)
    up = ind.cross_above(f, t)
    dn = ind.cross_below(f, t)
    with np.errstate(invalid="ignore"):
        lg = up & (f < -p["lvl"])
        sh = dn & (f > p["lvl"])
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
