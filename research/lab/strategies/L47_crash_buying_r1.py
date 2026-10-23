"""L47 r1 - Crash-buying em H1 só a favor do regime (SMA longa)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L47_crash_buying_r1",
    "refines": "L47_crash_buying",
    "refinement": ("No desenvolvimento o melhor (m=2, N=4, look=720, hold=2, só compra) teve PF 1,35 mas só 3 de 5 anos "
                   "positivos e vizinhos fracos (PF mediano 0,98): comprar quedas em mercado de baixa (2018) pega faca caindo. "
                   "Filtro de regime publicado (comprar quedas só acima da média longa; vender picos só abaixo dela)."),
    "name": "Crash-buying H1 a favor do regime (SMA de N dias)",
    "family": "reversao",
    "round": 9,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://philippdubach.com/posts/crypto-mean-reversion-trading/",
        "https://www.theseus.fi/handle/10024/902903",
    ],
    "rule": ("Igual ao L47 (z = retorno log de m candles H1 / (desvio dos retornos de 1 candle nos 'look' candles anteriores "
             "× raiz(m)); compra se z < -N; side=both vende se z > +N), mas só compra com fechamento acima da SMA de "
             "'trend_days' dias (24×N candles H1) e só vende abaixo dela. Saída por tempo após 'hold' candles; stop 2×ATR14."),
    "timeframes": ["H1"],
    "grid": {"m": [1, 2], "N": [3.0, 4.0, 5.0], "hold": [2, 6, 24], "trend_days": [50, 100, 200],
             "side": ["long", "both"]},
}


def signals(df, p):
    c = df.close.values.astype(float)
    lr = np.r_[np.nan, np.diff(np.log(c))]
    m = p["m"]
    rm = pd.Series(np.log(c)).diff(m).to_numpy()
    sd = pd.Series(lr).rolling(720).std().shift(m).to_numpy()
    z = rm / (sd * np.sqrt(m))
    t = ind.sma(c, 24 * p["trend_days"])
    buy = (z < -p["N"]) & (c > t)
    sell = (z > p["N"]) & (c < t)
    entry = np.where(buy, 1, 0)
    if p["side"] == "both":
        entry = np.where(sell, -1, entry)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": 2.0 * a, "max_hold": int(p["hold"])}
