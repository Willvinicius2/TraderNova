"""TV77 - Price Zone Oscillator (Walid Khalil & David Steckler, TASC jun/2011; LazyBear no TradingView)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV77_pzo",
    "name": "Price Zone Oscillator (Khalil/Steckler, LazyBear): zonas com ADX e EMA60",
    "family": "momento",
    "round": 6,
    "origin": "TradingView comunidade (LazyBear)",
    "sources": [
        "https://www.traders.com/Documentation/FEEDbk_docs/2011/06/Khalil.html",
        "https://toslc.thinkorswim.com/center/reference/Tech-Indicators/strategies/L-P/PriceZoneOscillatorLE",
        "https://toslc.thinkorswim.com/center/reference/Tech-Indicators/strategies/L-P/PriceZoneOscillatorSX",
        "https://traders.com/Documentation/FEEDbk_docs/2011/05/TradersTips.html (mesmas zonas do VZO, que o artigo do PZO reutiliza)",
    ],
    "rule": ("PZO = 100*EMA_n(fechamento com sinal)/EMA_n(fechamento), sinal + se fechamento > anterior, senão -. Mesmas regras "
             "de zona do VZO (Khalil/Steckler; LE/SX do thinkorswim: -40, +15, 0, +40, -5, +-60), sem as saídas por divergência. Tendência = ADX14 > adx; "
             "com tendência e preço > EMA60: compra quando VZO cruza acima de -40 ou de 0; sai quando VZO cruza abaixo de 60 "
             "ou (preço < EMA60 e VZO < 0). Com tendência e preço < EMA60: vende quando cruza abaixo de +40 ou de 0; cobre "
             "quando cruza acima de -60 ou (preço > EMA60 e VZO > 0). Sem tendência (ADX <= adx): compra ao cruzar acima de -40 "
             "ou +15, sai ao cruzar abaixo de +40 ou -5; vende ao cruzar abaixo de +40 ou -5, cobre ao cruzar acima de -40 ou +15. "
             "O script não tem stop: stop de proteção k*ATR14. Entrada na abertura seguinte."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [10, 14, 21], "adx": [15, 18, 22], "k": [2.0, 3.0], "side": ["long", "both"]},
}

SRC = "close"


def wilder(x, n):
    return pd.Series(x).ewm(alpha=1 / n, adjust=False, min_periods=n).mean().values


def adx14(df, n=14):
    h, l, c = df.high.values, df.low.values, df.close.values
    uh = np.r_[np.nan, h[1:] - h[:-1]]
    dl = np.r_[np.nan, l[:-1] - l[1:]]
    pdm = np.where((uh > dl) & (uh > 0), uh, 0.0)
    mdm = np.where((dl > uh) & (dl > 0), dl, 0.0)
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    pdm[0] = mdm[0] = 0.0
    a = wilder(tr, n)
    pdi, mdi = 100 * wilder(pdm, n) / a, 100 * wilder(mdm, n) / a
    dx = 100 * np.abs(pdi - mdi) / (pdi + mdi)
    out = wilder(np.nan_to_num(dx, nan=0.0), n).copy()
    out[: 2 * n] = np.nan
    return out


def zone_osc(c, x, n):
    pc = np.r_[np.nan, c[:-1]]
    sgn = np.where(c > pc, 1.0, -1.0)
    den = ind.ema(x, n)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = 100 * ind.ema(sgn * x, n) / den
    z[~np.isfinite(z)] = np.nan
    return z


def zone_signals(df, p, src):
    c = df.close.values
    x = df.volume.values if src == "volume" else c
    z = zone_osc(c, x, p["n"])
    e = ind.ema(c, 60)
    ax = adx14(df)
    tr = ax > p["adx"]
    ca = lambda lv: ind.cross_above(z, np.full(len(z), lv))  # noqa: E731
    cb = lambda lv: ind.cross_below(z, np.full(len(z), lv))  # noqa: E731
    up, dn = tr & (c > e), tr & (c < e)
    flat = (~tr) & np.isfinite(ax)
    buy = (up & (ca(-40) | ca(0))) | (flat & (ca(-40) | ca(15)))
    sell = (dn & (cb(40) | cb(0))) | (flat & (cb(40) | cb(-5)))
    exl = (tr & (cb(60) | ((c < e) & (z < 0)))) | (flat & (cb(40) | cb(-5)))
    exs = (tr & (ca(-60) | ((c > e) & (z > 0)))) | (flat & (ca(-40) | ca(15)))
    valid = np.isfinite(z) & np.isfinite(e) & np.isfinite(ax)
    buy &= valid
    sell &= valid
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": exl, "exit_short": exs}


def signals(df, p):
    return zone_signals(df, p, SRC)
