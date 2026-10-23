"""Hull Suite (InSilico, TradingView comunidade): cor/inclinação da Hull MA (HULL > HULL[2])."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV20_hull_suite",
    "name": "Hull Suite (InSilico): virada da Hull MA",
    "family": "tendencia",
    "round": 2,
    "origin": "TradingView comunidade (InSilico)",
    "sources": [
        "https://www.tradingview.com/script/hg92pFwS-Hull-Suite/",
        "https://il.tradingview.com/script/hg92pFwS-Hull-Suite",
    ],
    "rule": ("Reproduz o Pine do Hull Suite: HULL = HMA(close, len) (modo 'Hma'; WMA(2*WMA(len/2)-WMA(len), round(sqrt(len)))) "
             "ou EHMA (mesma fórmula com EMA). A cor fica verde quando HULL > HULL[2] e vermelha quando HULL < HULL[2]. "
             "Compra quando a cor vira para verde, vende (side=both) quando vira para vermelho; sai na virada oposta. "
             "O script original é indicador sem stop: usamos stop de proteção k*ATR(14)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"mode": ["hma", "ehma"], "length": [34, 55, 89, 144], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def wma(x, n):
    n = int(n)
    x = np.asarray(x, dtype=float)
    w = np.arange(1, n + 1, dtype=float)
    out = np.full(len(x), np.nan)
    ok = ~np.isnan(x)
    if ok.sum() < n:
        return out
    j0 = int(np.argmax(ok))  # NaN só no início (aquecimento)
    v = np.convolve(x[j0:], w[::-1], mode="valid") / w.sum()  # out[i] = soma w_k * x[i-n+k], peso maior no mais recente
    out[j0 + n - 1:] = v
    return out


def hull(c, length, mode):
    half, sq = int(length / 2), int(round(np.sqrt(length)))
    if mode == "hma":
        return wma(2 * wma(c, half) - wma(c, length), sq)
    raw = 2 * ind.ema(c, half) - ind.ema(c, length)
    return pd.Series(raw).ewm(span=sq, adjust=False, min_periods=sq).mean().values


_cache = {}


def signals(df, p):
    c = df.close.values
    key = (id(df), len(c), p["mode"], p["length"])
    if key not in _cache:
        _cache[key] = hull(c, p["length"], p["mode"])
    h = _cache[key]
    h2 = ind.prev(h, 2)
    green = h > h2
    red = h < h2
    pg, pr = np.r_[False, green[:-1]], np.r_[False, red[:-1]]
    up = green & ~pg
    dn = red & ~pr
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
