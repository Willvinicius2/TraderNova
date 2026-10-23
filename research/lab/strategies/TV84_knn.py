"""Machine Learning: kNN-based Strategy (capissimo), treino em janela deslizante (só passado)."""
from collections import deque

import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV84_knn",
    "name": "Machine Learning: kNN-based Strategy (capissimo)",
    "family": "aprendizado_maquina",
    "round": 7,
    "origin": "TradingView comunidade (capissimo)",
    "sources": [
        "https://usethinkscript.com/threads/machine-learning-knn-based-indicator-for-thinkorswim.16778/ (descrição e porte do script de capissimo; a página do TradingView não abre aqui)",
        "https://github.com/deepentropy/lightweight-charts-indicators commit f8e1b0e, src/community/ml-knn-strategy.ts, porte linha a linha do Pine, MPL-2.0)",
    ],
    "rule": ("Duas variáveis do indicador escolhido (RSI, CCI ou ROC do fechamento com períodos longo 28 e curto 14, ou 'All' = média "
             "de RSI, CCI, ROC e volume minimax 0-99). Em cada candle guarda (f1, f2, rótulo) com rótulo = sinal(fech[1] - fech), "
             "como no Pine (rótulo do próprio candle, já conhecido no fechamento). Varre os pontos guardados do mais antigo ao mais "
             "novo e, sempre que um ponto fica MAIS LONGE do ponto atual que todos os anteriores (lógica literal do original), "
             "empurra o rótulo numa fila dos últimos k = floor(raiz(K)) rótulos, mantida entre candles. Previsão = soma da fila; "
             ">0 compra, <0 vende, com filtro opcional ATR(10) > ATR(40). Entra quando o sinal muda para compra/venda; sai quando "
             "o sinal deixa de ser o da posição (neutro ou oposto). Diferença do original: o Pine guarda todos os candles desde 2000; "
             "aqui só os últimos W=1000 candles até o atual (janela deslizante, sem futuro, para caber no tempo). Original sem stop: "
             "stop de proteção k_atr × ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"indicator": ["RSI", "CCI", "ROC", "All"], "K": [100, 252, 400], "filter": [False, True],
             "k_atr": [3.0], "side": ["long", "both"]},
}

W = 1000
EPS = 1e-10
_cache = {}


def rsi(c, n):
    return ind.rsi(c, n)


def cci(c, n):
    s = pd.Series(c)
    m = s.rolling(n).mean()
    md = s.rolling(n).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return ((s - m) / (0.015 * md)).to_numpy()


def roc(c, n):
    p = ind.prev(c, n)
    return 100 * (c - p) / p


def minimax(x, n, lo_v, hi_v):
    hi, lo = ind.highest(x, n), ind.lowest(x, n)
    return (hi_v - lo_v) * (x - lo) / (hi - lo) + lo_v


def features(df, which, L=28, S=14):
    c = df.close.values
    if which == "RSI":
        return rsi(c, L), rsi(c, S)
    if which == "CCI":
        return cci(c, L), cci(c, S)
    if which == "ROC":
        return roc(c, L), roc(c, S)
    v = df.volume.values.astype(float)
    f1 = (rsi(c, L) + cci(c, L) + roc(c, L) + minimax(v, L, 0, 99)) / 4
    f2 = (rsi(c, S) + cci(c, S) + roc(c, S) + minimax(v, S, 0, 99)) / 4
    return f1, f2


def prediction(df, which, K):
    key = (len(df), str(df.index[0]), str(df.index[-1]), which, K)
    if key in _cache:
        return _cache[key]
    c = df.close.values
    f1, f2 = features(df, which)
    lab = np.r_[np.nan, np.sign(c[:-1] - c[1:])]
    k = int(np.floor(np.sqrt(K)))
    n = len(c)
    pred = np.full(n, np.nan)
    q = deque(maxlen=k)
    valid = ~(np.isnan(f1) | np.isnan(f2))
    for i in range(n):
        if valid[i]:
            a = max(0, i - W + 1)
            d = np.sqrt((f1[i] - f1[a:i + 1]) ** 2 + (f2[i] - f2[a:i + 1]) ** 2)
            dd = np.where(np.isnan(d), -np.inf, d)
            rm = np.maximum.accumulate(dd)
            prevmax = np.r_[-999.0, rm[:-1]]
            prevmax = np.maximum(prevmax, -999.0)
            rec = np.nonzero(dd - prevmax > EPS)[0]
            if len(rec) > k:
                rec = rec[-k:]
            q.extend(lab[a + rec])
        if q:
            arr = np.array(q)
            arr = arr[~np.isnan(arr)]
            if len(arr):
                pred[i] = arr.sum()
    _cache[key] = pred
    return pred


def signals(df, p):
    pred = prediction(df, p["indicator"], p["K"])
    filt = np.ones(len(df), bool)
    if p["filter"]:
        filt = ind.atr(df, 10) - ind.atr(df, 40) > EPS
    sig = np.where((pred > EPS) & filt, 1, np.where((pred < -EPS) & filt, -1, 0))
    ps = np.r_[0, sig[:-1]]
    ch = sig != ps
    entry = np.where(ch & (sig == 1), 1, np.where(ch & (sig == -1), -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k_atr"] * ind.atr(df, 14), "exit_long": sig != 1, "exit_short": sig != -1}
