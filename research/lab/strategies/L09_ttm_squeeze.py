"""L09 - TTM Squeeze (John Carter)."""
import numpy as np

import indicators as ind

META = {
    "id": "L09_ttm_squeeze",
    "name": "TTM Squeeze (John Carter)",
    "family": "volatilidade",
    "sources": [
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/ttm-squeeze",
        "https://www.luxalgo.com/library/concept/ttm-squeeze/",
        "John F. Carter, Mastering the Trade (McGraw-Hill, 2005/2012), cap. 'The Squeeze'",
    ],
    "rule": ("Squeeze ligado quando a Bollinger(20, 2 desvios) fica inteira dentro do Keltner(EMA20 ± kc×ATR20). "
             "Quando o squeeze desliga (dispara) depois de ao menos min_sq candles ligado, entra na direção do momentum "
             "(regressão linear de 20 candles do preço menos a média entre ponto médio Donchian 20 e SMA20, como no histograma de Carter). "
             "Saída: 'fade' = momentum perde força por 2 candles seguidos (mudança de cor do histograma); 'zero' = momentum cruza o zero. "
             "Stop inicial stop_k×ATR20."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"kc": [1.25, 1.5, 2.0], "min_sq": [1, 6], "exit": ["fade", "zero"], "stop_k": [1.5, 2.5], "side": ["long", "both"]},
}

N = 20


def linreg_end(y, n):
    """Valor da regressão linear no último ponto da janela (causal)."""
    y = np.asarray(y, float)
    out = np.full(len(y), np.nan)
    ok = ~np.isnan(y)
    yy = np.where(ok, y, 0.0)
    x = np.arange(n, dtype=float)
    sx, sxx = x.sum(), (x * x).sum()
    sy = np.convolve(yy, np.ones(n), "full")[: len(y)]
    sxy = np.convolve(yy, x[::-1], "full")[: len(y)]  # peso n-1 para o mais recente
    slope = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    icpt = (sy - slope * sx) / n
    val = icpt + slope * (n - 1)
    valid = np.convolve(ok.astype(float), np.ones(n), "full")[: len(y)] == n
    out[valid] = val[valid]
    return out


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    mid = ind.sma(c, N)
    sd = ind.stdev(c, N)
    em = ind.ema(c, N)
    a = ind.atr(df, N)
    sq_on = (mid + 2 * sd < em + p["kc"] * a) & (mid - 2 * sd > em - p["kc"] * a)
    # quantos candles seguidos o squeeze está ligado até i-1
    run = np.zeros(len(c))
    for i in range(1, len(c)):
        run[i] = run[i - 1] + 1 if sq_on[i - 1] else 0
    fired = (~sq_on) & (run >= p["min_sq"]) & ~np.isnan(a)
    base = (ind.highest(h, N) + ind.lowest(l, N)) / 2
    mom = linreg_end(c - (base + mid) / 2, N)
    pm, pm2 = ind.prev(mom), ind.prev(mom, 2)
    entry = np.where(fired & (mom > 0), 1, np.where(fired & (mom < 0), -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    if p["exit"] == "fade":
        exl = (mom < pm) & (pm < pm2)
        exs = (mom > pm) & (pm > pm2)
    else:
        exl = mom < 0
        exs = mom > 0
    return {"entry": entry, "stop": p["stop_k"] * a, "exit_long": exl, "exit_short": exs}
