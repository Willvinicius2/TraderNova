"""Machine Learning: kNN Trend Predictor (tkarolak), look-ahead adjustment desligado."""
import numpy as np

META = {
    "id": "TV87_knn_trend",
    "name": "Machine Learning: kNN Trend Predictor (tkarolak)",
    "family": "aprendizado_maquina",
    "round": 7,
    "origin": "TradingView comunidade (tkarolak)",
    "sources": [
        "https://www.tradingview.com/script/lhpm23En-Machine-Learning-kNN-Trend-Predictor/",
        "https://www.luxalgo.com/library/indicator/lhpm23En-machine-learning-knn-trend-predictor/",
        "https://github.com/deepentropy/lightweight-charts-indicators (commit f8e1b0e, src/community/machine-learning-knn-trend-predictor.ts, porte linha a linha do Pine, MPL-2.0)",
    ],
    "rule": ("A cada candle empurra d = |fech - fech[1]| num anel de K distâncias e o vizinho (fech[1] se d < menor distância "
             "guardada, senão fech) num anel de N vizinhos; curva = média dos N vizinhos. Como no Pine o d novo entra no anel ANTES "
             "do mínimo ser calculado, d < mínimo nunca é verdadeiro e o vizinho é sempre o fechamento: a curva é a SMA(N) do "
             "fechamento (reproduzido fielmente; K não tem efeito). Look-ahead desligado (ADJ=off): direção +1 quando curva < "
             "fech[1], -1 quando curva > fech[1]. Compra quando a direção vira +1, venda (side=both) quando vira -1; sai/inverte "
             "na direção oposta. Indicador sem stop: stop de proteção k_atr × ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"N": [20, 50, 100, 200], "K": [100], "k_atr": [2.0, 3.0], "side": ["long", "both"]},
}

EPS = 1e-10


def knn_curve(src, N, K):
    """Tradução literal dos anéis do Pine (vetorizada pelo fato de o vizinho ser sempre src)."""
    import pandas as pd
    d = np.abs(src - np.r_[np.nan, src[:-1]])
    dmin = pd.Series(d).rolling(K, min_periods=1).min().to_numpy()  # inclui o d atual, como no Pine
    nb = np.where(d - dmin < -EPS, np.r_[np.nan, src[:-1]], src)
    return pd.Series(nb).rolling(N, min_periods=1).mean().to_numpy()


def signals(df, p):
    import indicators as ind
    c = df.close.values
    curve = knn_curve(c, p["N"], p["K"])
    ref = np.r_[np.nan, c[:-1]]
    dr = np.where(ref - curve > EPS, 1, np.where(curve - ref > EPS, -1, 0))
    pd_ = np.r_[0, dr[:-1]]
    up = (dr == 1) & (pd_ != 1)
    dn = (dr == -1) & (pd_ != -1)
    up[: p["N"]] = dn[: p["N"]] = False
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k_atr"] * ind.atr(df, 14), "exit_long": dr == -1, "exit_short": dr == 1}
