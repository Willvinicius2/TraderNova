"""Ichimoku Kinko Hyo (Goichi Hosoda): cruzamento Tenkan/Kijun filtrado por nuvem e Chikou."""
import numpy as np

import indicators as ind

META = {
    "id": "L03_ichimoku",
    "name": "Ichimoku: cruzamento Tenkan/Kijun com nuvem e Chikou",
    "family": "tendencia",
    "sources": [
        "https://en.wikipedia.org/wiki/Ichimoku_Kink%C5%8D_Hy%C5%8D",
        "https://www.luxalgo.com/library/concept/ichimoku-signals.md",
    ],
    "rule": ("Tenkan=(máx+mín)/2 de 9*s, Kijun de 26*s, Senkou A=(Tenkan+Kijun)/2 e Senkou B=(máx+mín)/2 de 52*s, ambos deslocados "
             "26*s candles à frente (a nuvem em i usa dados até i-26*s). Chikou confirma quando o fechamento atual está acima (abaixo) "
             "do fechamento de 26*s candles atrás. Compra: Tenkan cruza acima da Kijun com fechamento acima da nuvem e Chikou acima; "
             "venda (side=both) espelhada. Saída: cruzamento oposto Tenkan/Kijun (exit=tk) ou fechamento do lado errado da Kijun "
             "(exit=kijun). Stop inicial k*ATR(14). s=1 é o padrão 9/26/52; s=2 e 3 alongam (comum em cripto 24/7)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"s": [1, 2, 3], "exit": ["tk", "kijun"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def mid(df, n):
    return (ind.highest(df.high.values, n) + ind.lowest(df.low.values, n)) / 2


def signals(df, p):
    s = p["s"]
    c = df.close.values
    tk, kj, sb = mid(df, 9 * s), mid(df, 26 * s), mid(df, 52 * s)
    sa = (tk + kj) / 2
    disp = 26 * s
    A, B = ind.prev(sa, disp), ind.prev(sb, disp)
    top, bot = np.fmax(A, B), np.fmin(A, B)
    c_back = ind.prev(c, disp)
    up = ind.cross_above(tk, kj)
    dn = ind.cross_below(tk, kj)
    lg = up & (c > top) & (c > c_back)
    sh = dn & (c < bot) & (c < c_back)
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    if p["exit"] == "tk":
        exl, exs = dn, up
    else:
        exl, exs = c < kj, c > kj
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": exl, "exit_short": exs}
