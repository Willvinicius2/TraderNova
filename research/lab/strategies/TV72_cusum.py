"""Change-Point Detection (CUSUM) [LuxAlgo], traduzido do Pine (port DE change-point-detection.ts)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV72_cusum",
    "name": "Change-Point Detection (CUSUM) LuxAlgo: opera a mudança de regime",
    "family": "regime",
    "round": 6,
    "origin": "TradingView comunidade (LuxAlgo)",
    "sources": [
        "https://www.luxalgo.com/library/indicator/change-point-detection-cusum/",
        "https://www.tradingview.com/scripts/cusum/",
        "github.com/deepentropy/lightweight-charts-indicators src/community/change-point-detection.ts (port fiel do Pine, MPL-2.0)",
    ],
    "sourceNote": "Indicador (não estratégia). Lógica copiada do port do Pine: z = (logret - SMA(logret,L)) / desvio(logret,L); "
                  "sPos = max(0, sPos + z - k), sNeg = min(0, sNeg + z + k); mudança para cima se sPos > h, para baixo se sNeg < -h; "
                  "na mudança as duas somas voltam a 0. Não repinta (só usa o candle fechado). Sem stop no original: k*ATR14.",
    "rule": "Compra no fechamento em que o CUSUM confirma mudança para cima (sPos > h) e vende (both) quando confirma mudança para baixo "
            "(sNeg < -h). Sai/inverte na mudança oposta. Stop de proteção stopk*ATR14. Entrada na abertura seguinte.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"length": [30, 50, 100], "h": [3.0, 4.0, 5.0], "slack": [0.25, 0.5, 0.75], "stopk": [2.0, 3.0], "side": ["long", "both"]},
}


def cusum(c, length, h, slack):
    lr = np.log(c / np.r_[c[0], c[:-1]])
    m = ind.sma(lr, length)
    sd = ind.stdev(lr, length)
    n = len(c)
    up = np.zeros(n, bool)
    dn = np.zeros(n, bool)
    sp = sn = 0.0
    for i in range(n):
        s = sd[i]
        if np.isnan(s):
            continue
        z = (lr[i] - m[i]) / (1.0 if abs(s) <= 1e-10 else s)
        sp = max(0.0, sp + z - slack)
        sn = min(0.0, sn + z + slack)
        u, d = sp > h, sn < -h
        if u or d or i == length:
            sp = sn = 0.0
        up[i], dn[i] = u, d
    return up, dn


def signals(df, p):
    c = df.close.values
    up, dn = cusum(c, p["length"], p["h"], p["slack"])
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["stopk"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
