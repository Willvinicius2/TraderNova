"""L24 - Trend Intensity Index (M. H. Pee, S&C jun/2002)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L24_tii",
    "name": "Trend Intensity Index (M. H. Pee): cruzamento dos níveis extremos",
    "family": "tendencia",
    "round": 8,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://www.traders.com/Documentation/FEEDbk_docs/2002/06/Abstracts_new/Pee/pee.html",
        "https://linnsoft.com/techind/trend-intensity-index-tii",
        "https://c.mql5.com/forextsd/forum/75/trend_intensity_index_-_m.h.pee.pdf",
    ],
    "rule": ("MA = SMA(fech, P) (Pee: P=60); nos últimos P/2 candles, SDPOS = soma de (fech-MA) quando positivo, SDNEG = soma de (MA-fech) quando "
             "positivo; TII = 100*SDPOS/(SDPOS+SDNEG). Linnsoft: compra quando TII cruza acima de 80, vende quando cruza abaixo de 20, fica até o "
             "sinal oposto. Grade: nível = 70/80/90 (venda em 100-nível); saída 'oposto' (sinal oposto, regra da fonte) ou '50' (TII volta a cruzar 50). "
             "Sem stop na fonte: stop de proteção k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"P": [30, 60, 120], "level": [70, 80, 90], "exit": ["oposto", "50"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def tii(c, P):
    ma = ind.sma(c, P)
    d = c - ma
    m = P // 2
    pos = pd.Series(np.where(d > 0, d, 0.0)).rolling(m).sum().to_numpy()
    neg = pd.Series(np.where(d < 0, -d, 0.0)).rolling(m).sum().to_numpy()
    tot = pos + neg
    out = np.where(tot > 0, 100 * pos / np.where(tot > 0, tot, 1), 50.0)
    out[np.isnan(ma)] = np.nan
    out[: P + m - 1] = np.nan
    return out


def signals(df, p):
    c = df.close.values
    t = tii(c, p["P"])
    N = len(c)
    hi = np.full(N, float(p["level"]))
    lo = np.full(N, 100.0 - p["level"])
    up = ind.cross_above(t, hi)
    dn = ind.cross_below(t, lo)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    if p["exit"] == "50":
        mid = np.full(N, 50.0)
        exl, exs = ind.cross_below(t, mid), ind.cross_above(t, mid)
    else:
        exl, exs = dn, up
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": exl, "exit_short": exs}
