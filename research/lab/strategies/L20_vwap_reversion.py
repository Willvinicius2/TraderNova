"""L20 - Reversão ao VWAP (ancorado no dia UTC ou rolante de 24h)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L20_vwap_reversion",
    "name": "Reversão ao VWAP diário/rolante",
    "family": "tempo_volume",
    "sources": [
        "https://www.tradingview.com/script/mthvTwSg-VWAP-Intraday-Weekly-Monthly/",
        "https://www.tradingview.com/script/HBa1RdfD-Institutional-VWAP-Bands-JOAT/",
        "https://www.luxalgo.com/library/indicator/CzQ5lLHJ-vwap-strategy/",
    ],
    "rule": ("VWAP = soma(preço típico*volume)/soma(volume), ancorado na meia-noite UTC ('day', exige 4h de sessão) ou "
             "rolante de 24h ('rolling'). Compra quando o fechamento fica abaixo de VWAP - d*ATR14 (esticado demais, "
             "convenção de 'fade the extreme' das bandas de VWAP); venda no espelho. Alvo: preço volta ao VWAP (saída no "
             "candle seguinte ao fechamento além do VWAP); stop k*ATR14; saída por tempo em 24h. Volume só do Bitstamp."),
    "timeframes": ["M15", "H1"],
    "grid": {"anchor": ["day", "rolling"], "d": [1.5, 2.0, 2.5, 3.0], "k": [1.5, 2.5], "side": ["long", "both"]},
}


def vwap(df, anchor):
    tp = (df.high.values + df.low.values + df.close.values) / 3.0
    v = df.volume.values
    pv = tp * v
    step = (df.index[1:] - df.index[:-1]).min()
    per_day = int(pd.Timedelta("1D") / step)
    if anchor == "rolling":
        num = pd.Series(pv).rolling(per_day).sum().values
        den = pd.Series(v).rolling(per_day).sum().values
        ok = np.ones(len(v), bool)
    else:
        day = df.index.floor("D")
        num = pd.Series(pv).groupby(day).cumsum().values
        den = pd.Series(v).groupby(day).cumsum().values
        hrs_in = (df.index - day) / pd.Timedelta("1h")
        ok = np.asarray(hrs_in) >= 3.99  # pelo menos ~4h de sessão
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(den > 0, num / den, np.nan)
    out[~ok] = np.nan
    return out, per_day


def signals(df, p):
    c = df.close.values
    vw, per_day = vwap(df, p["anchor"])
    a = ind.atr(df, 14)
    up = c < vw - p["d"] * a
    dn = c > vw + p["d"] * a
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": c >= vw, "exit_short": c <= vw, "max_hold": per_day}
