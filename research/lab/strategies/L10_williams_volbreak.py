"""L10 - Volatility breakout de Larry Williams (execução intradiária em H1/H4)."""
import numpy as np
import pandas as pd

import indicators as ind  # noqa: F401

META = {
    "id": "L10_williams_volbreak",
    "name": "Volatility breakout de Larry Williams",
    "family": "volatilidade",
    "sources": [
        "https://www.luxalgo.com/library/concept/volatility-breakout/",
        "Larry Williams, Long-Term Secrets to Short-Term Trading (Wiley, 1999), cap. sobre volatility breakout",
    ],
    "rule": ("Dia em UTC. Nível de compra = abertura do dia + k×(máx-mín do dia anterior); venda = abertura - k×range. "
             "Executado em candles intradiários (H1/H4): o primeiro fechamento do dia além do nível gera a entrada na abertura do "
             "candle seguinte (aproxima a ordem stop de Williams). Stop = sf×range do dia anterior. "
             "Saída por tempo: hold_days dias (24 candles H1 ou 6 H4 por dia), como a saída 'na abertura seguinte'/bailout curto de Williams. "
             "Escolha documentada: H1/H4 em vez de D1 para não usar a máxima do próprio dia como preço de entrada."),
    "timeframes": ["H1", "H4"],
    "grid": {"k": [0.3, 0.5, 0.7, 0.9], "sf": [0.5, 1.0], "hold_days": [1, 2, 3], "side": ["long", "both"]},
}


def signals(df, p):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    day = df.index.floor("D")
    g = pd.DataFrame({"o": o, "h": h, "l": l}, index=df.index).groupby(day)
    daily = pd.DataFrame({"o": g.o.first(), "rng": g.h.max() - g.l.min()})
    daily["prng"] = daily.rng.shift(1)
    dopen = daily.o.reindex(day).values
    prng = daily.prng.reindex(day).values
    up = dopen + p["k"] * prng
    dn = dopen - p["k"] * prng
    n = len(c)
    entry = np.zeros(n, dtype=np.int8)
    dvals = day.values
    done = False
    for i in range(n):
        if i == 0 or dvals[i] != dvals[i - 1]:
            done = False
        if done or np.isnan(prng[i]) or prng[i] <= 0:
            continue
        if c[i] > up[i]:
            entry[i], done = 1, True
        elif c[i] < dn[i]:
            entry[i], done = -1, True
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    secs = (df.index[1] - df.index[0]).total_seconds()
    bpd = int(round(86400 / secs))
    return {"entry": entry, "stop": p["sf"] * prng, "max_hold": p["hold_days"] * bpd}
