"""Mass Index reversal bulge (Donald Dorsey, 1992), indicador do everget no TradingView."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV63_mass_index",
    "name": "Mass Index 'reversal bulge' (Dorsey/everget): entra contra a EMA(9)",
    "family": "reversao",
    "round": 5,
    "origin": "TradingView comunidade (everget; Donald Dorsey, Technical Analysis of Stocks & Commodities, 1992)",
    "sources": [
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/mass-index",
        "https://github.com/everget/tradingview-pinescript-indicators/blob/master/oscillators/mass_index.pine",
        "https://en.wikipedia.org/wiki/Mass_index",
    ],
    "sourceNote": "Fórmula do Pine do everget (soma(25) de EMA9(H-L)/EMA9(EMA9(H-L)), nível 27 e confirmação 26,5). StockCharts: o bulge "
                  "é subir acima de 27 e voltar abaixo de 26,5; a direção vem de outra análise (reversão contra a tendência). Usamos a "
                  "leitura clássica (Dorsey/Wikipedia): direção da EMA(9) do fechamento; EMA subindo -> venda, caindo -> compra. "
                  "A fonte não define saída: saída por tempo (hold candles) e alvo em R.",
    "rule": "MI = soma(25) de EMA9(H-L)/EMA9(EMA9(H-L)). Bulge armado quando MI > brk; sinal quando, depois disso, MI fecha abaixo de brk-0,5. "
            "Se a EMA(9) do fechamento subiu no candle do sinal, vende; se caiu, compra. Sai após hold candles ou alvo 2R; "
            "stop k*ATR14 (a fonte não tem stop).",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"brk": [26.0, 26.5, 27.0], "hold": [10, 20, 40], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def mass_index(df, sm=9, sl=25):
    hl = df.high.values - df.low.values
    e1 = ind.ema(hl, sm)
    e2 = ind.ema(e1, sm)
    return pd.Series(e1 / e2).rolling(sl).sum().to_numpy()


def signals(df, p):
    c = df.close.values
    mi = mass_index(df)
    e9 = ind.ema(c, 9)
    n = len(c)
    sig = np.zeros(n, dtype=int)
    armed = False
    for i in range(1, n):
        if np.isnan(mi[i]) or np.isnan(e9[i]) or np.isnan(e9[i - 1]):
            continue
        if mi[i] > p["brk"]:
            armed = True
        elif armed and mi[i] < p["brk"] - 0.5:
            armed = False
            sig[i] = -1 if e9[i] > e9[i - 1] else 1
    if p["side"] == "long":
        sig = np.where(sig > 0, 1, 0)
    return {"entry": sig, "stop": p["k"] * ind.atr(df, 14), "target_r": 2.0, "max_hold": p["hold"]}
