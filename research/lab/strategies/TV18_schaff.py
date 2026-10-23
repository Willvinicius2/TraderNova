"""Schaff Trend Cycle (Doug Schaff), versão Pine de LazyBear no TradingView: cruzamento das linhas 25/75."""
import numpy as np

import indicators as ind

META = {
    "id": "TV18_schaff",
    "name": "Schaff Trend Cycle: saída das zonas 25/75",
    "family": "tendencia",
    "round": 2,
    "origin": "TradingView comunidade (LazyBear)",
    "sources": [
        "https://www.tradingview.com/script/eZwlb7PV/",
        "https://www.luxalgo.com/library/indicator/schaff-trend-cycle/",
        "https://forum.optuma.com/t/schaff-trend-cycle-indicator/2257",
    ],
    "sourceNote": "TradingView inacessível pelo WebFetch; parâmetros (23/50/10, fator 0,5, gatilhos 25/75) dos resumos do WebSearch (LuxAlgo, Optuma, ProRealCode).",
    "rule": "MACD = EMA(fech, rápida) - EMA(fech, lenta) (padrão 23/50). Estocástico do MACD em 'ciclo' candles (padrão 10), suavizado recursivamente com fator 0,5; "
            "segundo estocástico sobre esse resultado, de novo suavizado com 0,5 = STC (0-100). Compra quando o STC cruza acima de 25; vende quando cruza abaixo de 75. "
            "Sai da compra quando o STC cruza abaixo de 75 e da venda quando cruza acima de 25. Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"fast": [15, 23], "slow": [40, 50], "cyc": [8, 10, 12], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def stc(c, fast, slow, cyc, fac=0.5):
    m = ind.ema(c, fast) - ind.ema(c, slow)
    n = len(c)
    v1, v2 = ind.lowest(m, cyc), ind.highest(m, cyc)
    f1 = np.full(n, np.nan)
    pf = np.full(n, np.nan)
    for i in range(n):
        if np.isnan(v1[i]):
            continue
        rng = v2[i] - v1[i]
        prevf1 = f1[i - 1] if i > 0 and not np.isnan(f1[i - 1]) else 0.0
        f1[i] = (m[i] - v1[i]) / rng * 100 if rng > 0 else prevf1
        pf[i] = f1[i] if (i == 0 or np.isnan(pf[i - 1])) else pf[i - 1] + fac * (f1[i] - pf[i - 1])
    v3, v4 = ind.lowest(pf, cyc), ind.highest(pf, cyc)
    f2 = np.full(n, np.nan)
    out = np.full(n, np.nan)
    for i in range(n):
        if np.isnan(v3[i]):
            continue
        rng = v4[i] - v3[i]
        prevf2 = f2[i - 1] if i > 0 and not np.isnan(f2[i - 1]) else 0.0
        f2[i] = (pf[i] - v3[i]) / rng * 100 if rng > 0 else prevf2
        out[i] = f2[i] if np.isnan(out[i - 1]) else out[i - 1] + fac * (f2[i] - out[i - 1])
    return out


def signals(df, p):
    c = df.close.values
    s = stc(c, p["fast"], p["slow"], p["cyc"])
    lg = ind.cross_above(s, np.full(len(c), 25.0))
    sh = ind.cross_below(s, np.full(len(c), 75.0))
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": sh, "exit_short": lg}
