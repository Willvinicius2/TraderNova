"""SSL Hybrid (Mihkel00): baseline HMA com canal de faixa, continuação pela SSL2 (JMA) e saída pela SSL3 (HMA)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV80_ssl_hybrid",
    "name": "SSL Hybrid (Mihkel00)",
    "family": "tendencia",
    "round": 6,
    "origin": "TradingView comunidade (Mihkel00)",
    "sources": [
        "https://www.tradingview.com/script/FyW6Gz4r-SSL-Hybrid/",
        "https://www.prorealcode.com/prorealtime-indicators/ssl-hybrid-indicator",
        "github.com/deepentropy/lightweight-charts-indicators src/community/ssl-hybrid.ts (port fiel do Pine, MPL-2.0)",
    ],
    "rule": ("Baseline = HMA(close, len); canal = baseline ± 0,2 × EMA(TR, len). SSL2 = linha SSL das JMA(5) de máximas/mínimas "
             "(fase 3, potência 1); continuação de compra (buy_atr do Pine) = fechamento acima da baseline e acima da SSL2, "
             "com a SSL2 a menos de 0,9 × ATR(14, WMA) do fechamento. Compra no primeiro candle em que o fechamento está acima do "
             "canal superior E a SSL2 confirma; venda (side=both) no espelho (abaixo do canal inferior e sell_atr). Sai quando o "
             "fechamento cruza a SSL3 de saída (linha SSL das HMA(len3) de máximas/mínimas) contra a posição, como as setas de "
             "saída do original. O indicador não tem stop: stop de proteção k × ATR14 (Wilder). Pine do TradingView não abre; "
             "lógica lida no port TS fiel do deepentropy."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"len": [30, 45, 60, 90], "len3": [10, 15, 25], "k": [1.5, 2.5], "side": ["long", "both"]},
}


def wma(x, n):
    x = np.asarray(x, float)
    w = np.arange(1, n + 1, dtype=float)
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    v = np.lib.stride_tricks.sliding_window_view(x, n)
    out[n - 1:] = v @ w / w.sum()
    return out


def hma(x, n):
    half = wma(x, int(n // 2))
    full = wma(x, n)
    return wma(2 * half - full, int(round(np.sqrt(n))))


def jma(x, n, phase=3, power=1):
    pr = 0.5 if phase < -100 else (2.5 if phase > 100 else phase / 100 + 1.5)
    beta = 0.45 * (n - 1) / (0.45 * (n - 1) + 2)
    alpha = beta ** power
    out = np.empty(len(x))
    e0 = e1 = e2 = j = 0.0
    a2, b2 = (1 - alpha) ** 2, alpha ** 2
    for i, s in enumerate(x):
        e0 = (1 - alpha) * s + alpha * e0
        e1 = (s - e0) * (1 - beta) + beta * e1
        e2 = (e0 + pr * e1 - j) * a2 + b2 * e2
        j = e2 + j
        out[i] = j
    return out


def ssl_line(c, hi, lo):
    out = np.full(len(c), np.nan)
    hlv = np.nan
    for i in range(len(c)):
        if c[i] > hi[i]:
            hlv = 1
        elif c[i] < lo[i]:
            hlv = -1
        out[i] = hi[i] if hlv < 0 else lo[i]
    return out


_CACHE = {}


def signals(df, p):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    key = (id(df), len(c))
    if key not in _CACHE:
        pc = np.r_[np.nan, c[:-1]]
        tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
        atr_w = wma(tr, 14)
        ssl2 = ssl_line(c, jma(h, 5), jma(l, 5))
        _CACHE.clear()
        _CACHE[key] = (tr, atr_w, ssl2, {})
    tr, atr_w, ssl2, memo = _CACHE[key]
    n = p["len"]
    if ("b", n) not in memo:
        memo[("b", n)] = (hma(c, n), pd.Series(tr).ewm(span=n, adjust=False).mean().to_numpy())
    base, rng = memo[("b", n)]
    if ("x", p["len3"]) not in memo:
        memo[("x", p["len3"])] = ssl_line(c, hma(h, p["len3"]), hma(l, p["len3"]))
    sx = memo[("x", p["len3"])]
    upk, lok = base + 0.2 * rng, base - 0.2 * rng
    buy_atr = (c - 0.9 * atr_w < ssl2) & (c > base) & (c > ssl2)
    sell_atr = (c + 0.9 * atr_w > ssl2) & (c < base) & (c < ssl2)
    cl = (c > upk) & buy_atr
    cs = (c < lok) & sell_atr
    up = cl & ~np.r_[False, cl[:-1]]
    dn = cs & ~np.r_[False, cs[:-1]]
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    ex_long = ind.cross_below(c, sx)
    ex_short = ind.cross_above(c, sx)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": ex_long, "exit_short": ex_short}
