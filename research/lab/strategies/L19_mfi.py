"""L19 - Money Flow Index (Quong & Soudack): saída da sobrevenda/sobrecompra."""
import numpy as np

import indicators as ind

META = {
    "id": "L19_mfi",
    "name": "Money Flow Index: volta da sobrevenda/sobrecompra",
    "family": "tempo_volume",
    "sources": [
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/money-flow-index-mfi",
        "https://help.ctrader.com/indicators/built-in/volume/money-flow-index/",
    ],
    "rule": ("MFI(n) de Quong & Soudack: preço típico (H+L+C)/3 vezes volume; razão entre fluxo positivo e negativo de n "
             "candles; MFI = 100 - 100/(1+razão). Níveis da fonte 20/80 (extremos 10/90). Compra quando o MFI volta a "
             "cruzar para cima do nível de sobrevenda (lo); venda quando volta a cruzar para baixo de 100-lo. Saída quando "
             "o MFI chega a 50 ('mid') ou ao nível oposto ('opposite'); stop k*ATR14. Volume é só do Bitstamp."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [10, 14, 20], "lo": [10, 20], "exit": ["mid", "opposite"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def mfi(df, n):
    tp = (df.high.values + df.low.values + df.close.values) / 3.0
    rmf = tp * df.volume.values
    dtp = np.diff(tp, prepend=np.nan)
    pos = np.where(dtp > 0, rmf, 0.0)
    neg = np.where(dtp < 0, rmf, 0.0)
    ps = ind.sma(pos, n) * n
    ns = ind.sma(neg, n) * n
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(ns > 0, 100 - 100 / (1 + ps / ns), np.where(ps > 0, 100.0, 50.0))
    out[: n] = np.nan
    return out


def signals(df, p):
    m = mfi(df, p["n"])
    lo, hi = p["lo"], 100 - p["lo"]
    up = ind.cross_above(m, np.full(len(m), lo))
    dn = ind.cross_below(m, np.full(len(m), hi))
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    if p["exit"] == "mid":
        exl, exs = m >= 50, m <= 50
    else:
        exl, exs = m >= hi, m <= lo
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": exl, "exit_short": exs}
