"""L47 - Crash-buying: reversão após queda de N desvios em H1."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L47_crash_buying",
    "name": "Crash-buying: compra após queda de N desvios em H1",
    "family": "reversao",
    "round": 9,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://philippdubach.com/posts/crypto-mean-reversion-trading/",
        "https://www.theseus.fi/handle/10024/902903",
    ],
    "rule": ("Fonte (Dubach): compra quando o preço cai mais de 4 desvios-padrão numa janela de 2 horas e vende por tempo "
             "após 2 horas. Aqui: retorno log de m candles H1 (m=1 ou 2) dividido por (desvio-padrão dos retornos log de 1 "
             "candle nos 'look' candles ANTERIORES à janela × raiz(m)); compra quando z < -N; side=both também vende quando "
             "z > +N (pico de alta). Saída por tempo após 'hold' candles; stop de proteção k*ATR14 H1 (a fonte não tem). "
             "Difere do L32 (z-score do preço contra a SMA): aqui o gatilho é um choque de retorno de 1-2 horas."),
    "timeframes": ["H1"],
    "grid": {"m": [1, 2], "N": [3.0, 4.0, 5.0], "look": [168, 720], "hold": [2, 6, 24], "k": [2.0, 4.0],
             "side": ["long", "both"]},
}


def signals(df, p):
    c = df.close.values.astype(float)
    lr = np.r_[np.nan, np.diff(np.log(c))]
    m = p["m"]
    rm = pd.Series(np.log(c)).diff(m).to_numpy()
    sd = pd.Series(lr).rolling(p["look"]).std().shift(m).to_numpy()
    z = rm / (sd * np.sqrt(m))
    buy = z < -p["N"]
    sell = z > p["N"]
    entry = np.where(buy, 1, 0)
    if p["side"] == "both":
        entry = np.where(sell, -1, entry)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "max_hold": int(p["hold"])}
