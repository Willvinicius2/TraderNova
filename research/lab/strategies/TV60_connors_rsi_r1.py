"""Connors RSI (Connors & Alvarez / Connors Research), indicador embutido do TradingView."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV60_connors_rsi_r1",
    "refines": "TV60_connors_rsi",
    "refinement": "No desenvolvimento, thr=10 no H1 dá trades suficientes mas vizinhos fracos e só 3/5 anos positivos; a SMA200 no H1/H4 cobre poucos dias e deixa comprar em quedas de mercado de baixa. Filtro de tendência mais lento (SMA trend de 200/400/800 candles) e grade de limiar mais fina.",
    "name": "Connors RSI (CRSI) extremo com filtro SMA200",
    "family": "reversao",
    "round": 5,
    "origin": "TradingView embutida (Connors RSI; Connors & Alvarez, Connors Research 2012)",
    "sources": [
        "https://www.tradingview.com/support/solutions/43000502017-connors-rsi-crsi/",
        "https://www.luxalgo.com/library/concept/connors-rsi.md",
        "https://github.com/deepentropy/lightweight-charts-indicators/blob/main/src/standard/connors-rsi.ts",
        "Connors, Alvarez & Radtke (2012), An Introduction to ConnorsRSI",
    ],
    "sourceNote": "TradingView não abre no WebFetch; fórmula do código traduzido do indicador embutido (deepentropy) e regras de trade do "
                  "resumo da LuxAlgo (entra no extremo <10 / >90 com filtro de 200 períodos; sai na volta a 50) e da FILA (saída em 70).",
    "rule": "Igual ao TV60 com SMA de tendência de comprimento trend (200/400/800). CRSI = média de RSI(3) do fechamento, RSI(2) da sequência de altas/baixas e PercentRank(100) do retorno de 1 candle. "
            "Compra quando fechamento > SMA200 e CRSI < limiar; sai quando CRSI > nível de saída. Venda espelhada (both): fechamento < SMA200 "
            "e CRSI > 100-limiar, sai quando CRSI < 100-saída. Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4"],
    "grid": {"trend": [200, 400, 800], "thr": [5, 7.5, 10, 12.5], "exit": [50, 70], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def streak(c):
    ud = np.zeros(len(c))
    for i in range(1, len(c)):
        if c[i] > c[i - 1]:
            ud[i] = 1 if ud[i - 1] <= 0 else ud[i - 1] + 1
        elif c[i] < c[i - 1]:
            ud[i] = -1 if ud[i - 1] >= 0 else ud[i - 1] - 1
    return ud


def percentrank(x, n):
    """Pine ta.percentrank: % dos n valores anteriores <= valor atual."""
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    from numpy.lib.stride_tricks import sliding_window_view
    if len(x) <= n:
        return out
    w = sliding_window_view(x[:-1], n)  # w[j] = x[j..j+n-1], anteriores de i=j+n
    cur = x[n:]
    with np.errstate(invalid="ignore"):
        out[n:] = (w <= cur[:, None]).sum(axis=1) / n * 100
    bad = np.isnan(w).any(axis=1) | np.isnan(cur)
    out[n:][bad] = np.nan
    return out


def crsi(c):
    roc = pd.Series(c).pct_change().to_numpy() * 100
    return (ind.rsi(c, 3) + ind.rsi(streak(c), 2) + percentrank(roc, 100)) / 3


def signals(df, p):
    c = df.close.values
    cr = crsi(c)
    s200 = ind.sma(c, p["trend"])
    with np.errstate(invalid="ignore"):
        lg = (c > s200) & (cr < p["thr"])
        sh = (c < s200) & (cr > 100 - p["thr"])
        exl = cr > p["exit"]
        exs = cr < 100 - p["exit"]
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
