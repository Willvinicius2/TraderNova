"""TV59 - Accelerator Oscillator (Bill Williams). Código: everget/tradingview-pinescript-indicators."""
import numpy as np

import indicators as ind

META = {
    "id": "TV59_accelerator",
    "name": "Accelerator Oscillator (Bill Williams): 2 barras verdes acima de 0 ou 3 abaixo",
    "family": "tendencia",
    "round": 5,
    "origin": "TradingView comunidade (everget, Accelerator Oscillator; regra de Bill Williams, New Trading Dimensions, 1998)",
    "sources": [
        "https://www.metatrader5.com/en/mobile-trading/iphone/help/chart/indicators/bw_indicators/accelerator_oscillator",
        "https://github.com/everget/tradingview-pinescript-indicators/blob/master/oscillators/accelerator_oscillator.pine",
        "https://www.luxalgo.com/library/indicator/accelerator-oscillator/",
    ],
    "sourceNote": "Regra do manual do MetaTrader 5 (Bill Williams' Indicators): com AC acima de zero bastam duas colunas verdes para comprar; "
                  "abaixo de zero são precisas três colunas verdes; venda espelhada; não comprar com coluna vermelha. Fórmula e cor do Pine do everget.",
    "rule": ("AO = SMA(5) - SMA(34) da mediana; AC = AO - SMA(5) do AO; coluna verde = AC > AC anterior. Compra com 2 colunas verdes seguidas "
             "com as duas acima de 0, ou 3 verdes seguidas com as três abaixo de 0. Venda espelhada (2 vermelhas abaixo de 0 ou 3 vermelhas "
             "acima). Saída exit='red1': primeira coluna da cor contrária (regra de Williams de não ficar contra a cor); exit='red2': duas "
             "colunas contrárias seguidas; exit='opp': só no sinal oposto. Alvo opcional em R. Sem stop no original: stop k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"exit": ["red1", "red2", "opp"], "target": [0, 2.0], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def accel(df):
    m = (df.high.values + df.low.values) / 2
    a = ind.sma(m, 5) - ind.sma(m, 34)
    return a - ind.sma(a, 5)


def signals(df, p):
    ac = accel(df)
    a1, a2, a3 = ind.prev(ac, 1), ind.prev(ac, 2), ind.prev(ac, 3)
    g0, g1, g2 = ac > a1, a1 > a2, a2 > a3
    r0, r1, r2 = ac < a1, a1 < a2, a2 < a3
    buy = (g0 & g1 & (ac > 0) & (a1 > 0)) | (g0 & g1 & g2 & (ac < 0) & (a1 < 0) & (a2 < 0))
    sell = (r0 & r1 & (ac < 0) & (a1 < 0)) | (r0 & r1 & r2 & (ac > 0) & (a1 > 0) & (a2 > 0))
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    if p["exit"] == "red1":
        exl, exs = r0, g0
    elif p["exit"] == "red2":
        exl, exs = r0 & r1, g0 & g1
    else:
        exl, exs = sell, buy
    out = {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
    if p["target"]:
        out["target_r"] = p["target"]
    return out
