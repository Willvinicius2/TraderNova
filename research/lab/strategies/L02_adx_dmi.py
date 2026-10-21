"""Sistema direcional de Wilder (DMI + ADX)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L02_adx_dmi",
    "name": "Sistema direcional de Wilder (DI+/DI- com ADX)",
    "family": "tendencia",
    "sources": [
        "https://www.barchart.com/trader/help/studies/adx.php",
        "https://www.metatrader5.com/en/terminal/help/indicators/trend_indicators/admi",
        "Wilder, J. W. (1978), New Concepts in Technical Trading Systems (definição clássica)",
    ],
    "rule": ("DI+ e DI- de Wilder (suavização de Wilder, período n) e ADX. Compra quando DI+ cruza acima de DI- com ADX >= limiar; "
             "vende (side=both) quando DI- cruza acima de DI+ com ADX >= limiar. Sai no cruzamento oposto dos DIs (independe do ADX). "
             "Stop inicial k*ATR(14)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [10, 14, 20], "adx_min": [15, 20, 25, 30], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def wilder(x, n):
    return pd.Series(x).ewm(alpha=1 / n, adjust=False, min_periods=n).mean().values


def dmi(df, n):
    h, l, c = df.high.values, df.low.values, df.close.values
    uh = np.r_[np.nan, h[1:] - h[:-1]]
    dl = np.r_[np.nan, l[:-1] - l[1:]]
    pdm = np.where((uh > dl) & (uh > 0), uh, 0.0)
    mdm = np.where((dl > uh) & (dl > 0), dl, 0.0)
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    pdm[0] = mdm[0] = 0.0
    atr_ = wilder(tr, n)
    pdi = 100 * wilder(pdm, n) / atr_
    mdi = 100 * wilder(mdm, n) / atr_
    dx = 100 * np.abs(pdi - mdi) / (pdi + mdi)
    adx = wilder(np.nan_to_num(dx, nan=0.0), n)
    adx = adx.copy()
    adx[: 2 * n] = np.nan
    return pdi, mdi, adx


def signals(df, p):
    pdi, mdi, adx = dmi(df, p["n"])
    up = ind.cross_above(pdi, mdi)
    dn = ind.cross_below(pdi, mdi)
    strong = adx >= p["adx_min"]
    entry = np.where(up & strong, 1, np.where(dn & strong, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": dn, "exit_short": up}
