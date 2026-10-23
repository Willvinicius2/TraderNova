"""L21 - Kaufman Adaptive Moving Average (KAMA) com filtro de Efficiency Ratio."""
import numpy as np

import indicators as ind

META = {
    "id": "L21_kama",
    "name": "Kaufman KAMA: entrada na virada da KAMA com filtro de Efficiency Ratio",
    "family": "tendencia",
    "round": 8,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/kaufmans-adaptive-moving-average-kama",
        "https://ta-lib.org/functions/er.html",
        "Perry J. Kaufman, Smarter Trading (1995) / Trading Systems and Methods: regra de filtro da AMA (virada maior que f x desvio-padrão das variações da AMA)",
    ],
    "rule": ("ER = |fech - fech[n]| / soma(|Δfech|, n); SC = (ER*(2/3 - 2/31) + 2/31)^2; KAMA = KAMA[1] + SC*(fech - KAMA[1]). "
             "Virada para cima (regra de filtro de Kaufman): KAMA sobe mais que f x desvio-padrão(ΔKAMA, 20) acima da mínima da KAMA "
             "desde a última virada para baixo (f=0: qualquer subida). Compra na virada para cima se ER(n) >= er_min; vende (both) na virada "
             "para baixo com o mesmo filtro. Sai na virada oposta (inverte se 'both' e o filtro de ER deixar). Sem stop no original: stop de proteção k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [10, 20], "f": [0.0, 0.5, 1.0], "er_min": [0.0, 0.2, 0.3], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def kama(c, n, fast=2, slow=30):
    c = np.asarray(c, float)
    N = len(c)
    change = np.full(N, np.nan)
    change[n:] = np.abs(c[n:] - c[:-n])
    vol = ind.sma(np.r_[np.nan, np.abs(np.diff(c))], n) * n
    er = np.where(vol > 0, change / vol, 0.0)
    er[np.isnan(change)] = np.nan
    fs, ss = 2.0 / (fast + 1), 2.0 / (slow + 1)
    sc = (er * (fs - ss) + ss) ** 2
    out = np.full(N, np.nan)
    if N <= n:
        return out, er
    out[n] = np.mean(c[1:n + 1])
    for i in range(n + 1, N):
        s = sc[i] if not np.isnan(sc[i]) else ss * ss
        out[i] = out[i - 1] + s * (c[i] - out[i - 1])
    return out, er


def signals(df, p):
    c = df.close.values
    k_, er = kama(c, p["n"])
    dk = np.r_[np.nan, np.diff(k_)]
    sd = ind.stdev(dk, 20)
    N = len(c)
    up = np.zeros(N, bool)
    dn = np.zeros(N, bool)
    state = 0
    lo = hi = np.nan
    for i in range(N):
        if np.isnan(k_[i]) or np.isnan(sd[i]):
            continue
        thr = p["f"] * sd[i]
        if state <= 0:
            lo = k_[i] if np.isnan(lo) else min(lo, k_[i])
            if k_[i] - lo > thr and dk[i] > 0:
                up[i] = True
                state = 1
                hi = k_[i]
                lo = np.nan
                continue
        if state >= 0:
            hi = k_[i] if np.isnan(hi) else max(hi, k_[i])
            if hi - k_[i] > thr and dk[i] < 0:
                dn[i] = True
                state = -1
                lo = k_[i]
                hi = np.nan
    ok = np.nan_to_num(er, nan=0.0) >= p["er_min"]
    entry = np.where(up & ok, 1, np.where(dn & ok, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": dn, "exit_short": up}
