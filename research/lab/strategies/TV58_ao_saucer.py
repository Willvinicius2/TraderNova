"""TV58 - Awesome Oscillator, padrão 'saucer' (Bill Williams). Código: everget/tradingview-pinescript-indicators."""
import numpy as np

import indicators as ind

META = {
    "id": "TV58_ao_saucer",
    "name": "Awesome Oscillator: saucer (Bill Williams)",
    "family": "tendencia",
    "round": 5,
    "origin": "TradingView comunidade (everget, Awesome Oscillator; regra de Bill Williams, New Trading Dimensions, 1998)",
    "sources": [
        "https://in.tradingview.com/support/solutions/43000501826",
        "https://github.com/everget/tradingview-pinescript-indicators/blob/master/oscillators/awesome_oscillator.pine",
        "https://www.cmcmarkets.com/en-gb/trading-guides/awesome-oscillator",
    ],
    "sourceNote": "Help Center do TradingView (AO) lido pelo WebFetch: saucer de alta = AO acima de zero, duas barras vermelhas seguidas "
                  "(a segunda mais baixa) e depois uma verde; de baixa é o espelho abaixo de zero. Cor como no Pine do everget (verde = AO > AO[1]).",
    "rule": ("AO = SMA(5) - SMA(34) da mediana (máx+mín)/2. Compra quando as 3 últimas barras do AO estão acima de 0, as duas primeiras "
             "são vermelhas (AO caindo) e a última é verde (AO subindo). Venda espelhada abaixo de 0. Saída exit='zero': quando o AO cruza "
             "o zero contra a posição; exit='color2': depois de duas barras seguidas da cor contrária. Alvo opcional em R (target=0 = sem alvo). "
             "Sem stop no original: stop de proteção k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"exit": ["zero", "color2"], "target": [0, 2.0, 3.0], "k": [1.5, 2.0, 3.0], "side": ["long", "both"]},
}


def ao(df):
    m = (df.high.values + df.low.values) / 2
    return ind.sma(m, 5) - ind.sma(m, 34)


def signals(df, p):
    a = ao(df)
    a1, a2, a3 = ind.prev(a, 1), ind.prev(a, 2), ind.prev(a, 3)
    g0, g1, g2 = a > a1, a1 > a2, a2 > a3
    r0, r1, r2 = a < a1, a1 < a2, a2 < a3
    buy = (a > 0) & (a1 > 0) & (a2 > 0) & r2 & r1 & g0
    sell = (a < 0) & (a1 < 0) & (a2 < 0) & g2 & g1 & r0
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    if p["exit"] == "zero":
        exl, exs = a < 0, a > 0
    else:
        exl, exs = r0 & r1, g0 & g1
    out = {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
    if p["target"]:
        out["target_r"] = p["target"]
    return out
