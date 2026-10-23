"""Ehlers Decycler Oscillator (everget, TradingView comunidade). Fonte Pine: everget/tradingview-pinescript-indicators."""
import math

import numpy as np

import indicators as ind

META = {
    "id": "TV48_decycler",
    "name": "Ehlers Decycler Oscillator (everget): cruzamento das duas linhas ou do zero",
    "family": "tendencia",
    "round": 4,
    "origin": "TradingView comunidade (everget; indicador de John F. Ehlers, S&C set/2015 'Decyclers')",
    "sources": [
        "https://www.tradingview.com/script/5xelSGhd-Ehlers-Decycler-Oscillator/",
        "https://github.com/everget/tradingview-pinescript-indicators/blob/master/oscillators/ehlers_decycler_oscillator.pine",
    ],
    "sourceNote": "TradingView inacessível pelo WebFetch; resumo da página pelo WebSearch e código Pine do repositório público do autor (cópia local em /home/user/labdata/pine).",
    "rule": "HP(x,P,m): passa-alta de 2 polos com alpha=(cos a+sin a-1)/cos a, a=2pi/(m*P*sqrt2). "
            "Decycler = close - HP(close,P,1); Osc = 100*K*HP(Decycler,P,0,5)/close. Linha 1: P1, K=1; linha 2: P2=0,8*P1, K=1,2 (padrão 125/100). "
            "Modo 'cross' (descrição do autor): compra quando a linha 2 cruza acima da linha 1, vende no inverso. "
            "Modo 'zero' (FILA): compra quando a linha 1 cruza acima de 0, vende abaixo. Sai no sinal oposto. "
            "O Pine não tem stop: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"p1": [75, 100, 125, 150], "mode": ["cross", "zero"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def hp2(x, period, mult):
    a = 2 * math.pi / (mult * period * math.sqrt(2))
    al = (math.cos(a) + math.sin(a) - 1) / math.cos(a)
    c1, c2, c3 = (1 - al / 2) ** 2, 2 * (1 - al), -(1 - al) ** 2
    n = len(x)
    out = np.zeros(n)
    x = np.nan_to_num(np.asarray(x, float))
    for i in range(n):
        x1 = x[i - 1] if i >= 1 else 0.0
        x2 = x[i - 2] if i >= 2 else 0.0
        h1 = out[i - 1] if i >= 1 else 0.0
        h2 = out[i - 2] if i >= 2 else 0.0
        out[i] = c1 * (x[i] - 2 * x1 + x2) + c2 * h1 + c3 * h2
    return out


def decosc(c, P, K):
    dec = c - hp2(c, P, 1.0)
    return 100 * K * hp2(dec, P, 0.5) / c


def signals(df, p):
    c = df.close.values
    o1 = decosc(c, p["p1"], 1.0)
    o2 = decosc(c, int(round(0.8 * p["p1"])), 1.2)
    warm = np.arange(len(c)) < 4 * p["p1"]
    if p["mode"] == "cross":
        up, dn = ind.cross_above(o2, o1), ind.cross_below(o2, o1)
    else:
        z = np.zeros(len(c))
        up, dn = ind.cross_above(o1, z), ind.cross_below(o1, z)
    up &= ~warm
    dn &= ~warm
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
