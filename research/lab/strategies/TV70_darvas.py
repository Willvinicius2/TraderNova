"""Darvas Box (Nicolas Darvas), versão Pine da comunidade TradingView."""
import numpy as np

import indicators as ind

META = {
    "id": "TV70_darvas",
    "name": "Darvas Box (caixa confirmada)",
    "family": "rompimento",
    "round": 6,
    "origin": "TradingView comunidade (script 'DARVAS BOX')",
    "sources": [
        "https://prorealcode.com/topic/darvas-boxes-de-trading-viex",
        "https://www.investopedia.com/terms/d/darvasboxtheory.asp",
        "Nicolas Darvas, 'How I Made $2,000,000 in the Stock Market' (1960)",
        "github.com/deepentropy/lightweight-charts-indicators src/community/darvas-box.ts (versão simplificada, não usada)",
    ],
    "rule": ("Pine 'DARVAS BOX' (boxp): NH = última máxima que superou a máxima dos boxp candles anteriores; a caixa é confirmada "
             "quando passam boxp-2 candles sem nova máxima e highest(high,boxp-2) < highest(high,boxp-1): topo = NH, fundo = "
             "lowest(low,boxp) nesse candle. Compra quando o fechamento cruza acima do topo confirmado; sai (ou vende, em 'both') "
             "quando o fechamento cruza abaixo do fundo. Stop de proteção k*ATR14 (o Pine não tem). Entrada na abertura seguinte. "
             "A tradução do deepentropy é simplificada (sem confirmação) e não foi usada; segui o Pine clássico do script."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"boxp": [4, 5, 6, 8, 10, 13], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def darvas(df, boxp):
    h, l, c = df.high.values, df.low.values, df.close.values
    n = len(c)
    LL = ind.lowest(l, boxp)
    k1 = ind.highest(h, boxp)
    k2 = ind.highest(h, boxp - 1)
    k3 = ind.highest(h, boxp - 2)
    newhigh = h > ind.prev(k1)
    top = np.full(n, np.nan)
    bot = np.full(n, np.nan)
    NH = np.nan
    since = 10 ** 9
    T = B = np.nan
    for i in range(n):
        if newhigh[i]:
            NH = h[i]; since = 0
        else:
            since += 1
        if since == boxp - 2 and k3[i] < k2[i]:
            T = NH; B = LL[i]
        top[i] = T; bot[i] = B
    return top, bot


def signals(df, p):
    c = df.close.values
    top, bot = darvas(df, p["boxp"])
    up = ind.cross_above(c, top)
    dn = ind.cross_below(c, bot)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": dn, "exit_short": up}
