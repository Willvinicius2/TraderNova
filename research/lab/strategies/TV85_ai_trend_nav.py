"""AI Trend Navigator [K-Neighbor] (Zeiierman): média kNN do preço cruzando a própria média."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV85_ai_trend_nav",
    "name": "AI Trend Navigator [K-Neighbor] (Zeiierman)",
    "family": "aprendizado_maquina",
    "round": 7,
    "origin": "TradingView comunidade (Zeiierman)",
    "sources": [
        "https://www.tradingview.com/script/30aLnPNh-AI-Trend-Navigator-K-Neighbor/",
        "https://github.com/deepentropy/lightweight-charts-indicators (commit f8e1b0e, src/community/ai-trend-navigator.ts, porte linha a linha do Pine, MPL-2.0)",
    ],
    "rule": ("Valor = SMA(hl2, maLen); alvo = RMA(fech, targetLen) (Price Action, padrão do Pine; aqui targetLen = maLen, os dois 5 no padrão). Em cada candle, dos últimos "
             "30 valores (candles 1..30 atrás, só passado) pega os k mais próximos do alvo atual e kNN_MA = soma/k. Linha kNN = "
             "WMA(5) de kNN_MA; média kNN = RMA(kNN_MA, suavização). Compra quando a linha kNN cruza acima da média kNN; venda "
             "(side=both) no cruzamento para baixo; sai no cruzamento oposto. O classificador de 10 vizinhos do Pine só pinta o "
             "fundo e não entra na regra. Indicador sem stop: stop de proteção k_atr × ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"k": [3, 5, 10], "smooth": [20, 50, 100], "maLen": [5, 10], "k_atr": [3.0], "side": ["long", "both"]},
}

WIN = 30


def wma(x, n):
    w = np.arange(1, n + 1, dtype=float)
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1:] = np.lib.stride_tricks.sliding_window_view(x, n) @ w / w.sum()
    return out


def rma(x, n):
    s = pd.Series(x)
    return s.ewm(alpha=1 / n, adjust=False, min_periods=n).mean().to_numpy()


def knn_ma(value, target, k):
    n = len(value)
    win = max(k, WIN)
    lag = np.full((n, win), np.nan)
    for j in range(1, win + 1):
        lag[j:, j - 1] = value[:-j]
    d = np.abs(target[:, None] - lag)
    d = np.where(np.isnan(d), np.inf, d)
    idx = np.argsort(d, axis=1, kind="stable")[:, :k]
    dv = np.take_along_axis(d, idx, 1)
    vv = np.take_along_axis(lag, idx, 1)
    vv = np.where(np.isinf(dv), 0.0, vv)
    out = vv.sum(1) / k
    out[np.isnan(target)] = np.nan
    return out


def signals(df, p):
    c = df.close.values
    hl2 = (df.high.values + df.low.values) / 2
    value = ind.sma(hl2, p["maLen"])
    target = rma(c, p["maLen"])
    km = knn_ma(value, target, p["k"])
    line = wma(km, 5)
    avg = rma(km, p["smooth"])
    up = ind.cross_above(line, avg)
    dn = ind.cross_below(line, avg)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k_atr"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
