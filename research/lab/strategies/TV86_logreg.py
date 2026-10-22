"""Machine Learning: Logistic Regression v.3 (capissimo), modo padrão 'Use Price Data for Signal Generation'."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV86_logreg",
    "name": "Machine Learning: Logistic Regression (capissimo)",
    "family": "aprendizado_maquina",
    "round": 7,
    "origin": "TradingView comunidade (capissimo)",
    "sources": [
        "https://www.prorealcode.com/topic/machine-learning-logistic-regression/ (código Pine v.3 de capissimo colado no fórum)",
        "https://usethinkscript.com/threads/machine-learning-logistic-regression-for-thinkorswim.17134/",
    ],
    "rule": ("Pine v.3 com os padrões (Optional Calculation = sim, Use Price Data = sim): X = time, Y = fechamento, janela p. "
             "Na função do original a hipótese é sigmoid(dot(X, 0.0, p)) = 0,5 fixa (o peso não entra no treino), então "
             "loss = -1/p × soma_p( soma_p(Y × (log 0,5 + 1 - Y)) × log 0,5 ), uma série só do passado. scaled_loss = minimax(loss, "
             "nlbk) reescalado para [mínimo, máximo] do fechamento nos últimos nlbk candles. Sinal: fech > scaled_loss (e filtro) = "
             "COMPRA; fech < scaled_loss (e filtro) = VENDA; senão mantém. Entra quando o sinal muda; sai após hold candles sem "
             "mudança (holding period do original) ou no sinal oposto (inverte). Filtro 'vol' = ATR(1) > ATR(10) do original. "
             "Sem stop no original: stop de proteção k_atr × ATR14. A previsão (sigmoid de X·w com X = tempo) satura e só é usada "
             "no modo de cruzamento, que não é o padrão."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"lookback": [2, 3, 5], "nlbk": [2, 10, 120], "hold": [5, 10, 20], "filter": ["none", "vol"],
             "k_atr": [3.0], "side": ["long", "both"]},
}

EPS = 1e-10


def rsum(x, n):
    return pd.Series(x).rolling(n).sum().to_numpy()


def signals(df, p):
    c = df.close.values
    n, nl = p["lookback"], p["nlbk"]
    h = 0.5
    inner = rsum(c * (np.log(h) + (1 - c)), n)
    loss = -1.0 / n * rsum(inner * np.log(1 - h), n)
    hi, lo = ind.highest(loss, nl), ind.lowest(loss, nl)
    with np.errstate(invalid="ignore", divide="ignore"):
        scaled = (ind.highest(c, nl) - ind.lowest(c, nl)) * (loss - lo) / (hi - lo) + ind.lowest(c, nl)
    filt = np.ones(len(c), bool)
    if p["filter"] == "vol":
        filt = ind.atr(df, 1) - ind.atr(df, 10) > EPS
    buy = (c - scaled > EPS) & filt
    sell = (scaled - c > EPS) & filt
    raw = np.where(sell, -1.0, np.where(buy, 1.0, np.nan))
    sig = pd.Series(raw).ffill().fillna(0).to_numpy()
    ps = np.r_[0, sig[:-1]]
    ch = sig != ps
    entry = np.where(ch & (sig == 1), 1, np.where(ch & (sig == -1), -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k_atr"] * ind.atr(df, 14), "max_hold": p["hold"]}
