"""L20 r2 - Reversão ao VWAP semanal (âncora mais longa) com recuperação da banda e tendência."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L20_vwap_reversion_r2",
    "refines": "L20_vwap_reversion",
    "refinement": ("r1 ficou perto de zero no desenvolvimento: no VWAP diário a distância até o alvo é pequena perto do custo "
                   "de 0,20% ida e volta. Segunda e última tentativa: âncora semanal (segunda 00:00 UTC) ou rolante de 7 dias, "
                   "em H1/H4, mantendo a entrada por recuperação da banda e o filtro de tendência EMA200."),
    "name": "Reversão ao VWAP semanal com recuperação da banda",
    "family": "tempo_volume",
    "sources": [
        "https://www.tradingview.com/script/mthvTwSg-VWAP-Intraday-Weekly-Monthly/",
        "https://www.tradingview.com/script/HBa1RdfD-Institutional-VWAP-Bands-JOAT/",
    ],
    "rule": ("VWAP semanal ancorado na segunda 00:00 UTC ('week', exige 1 dia de semana) ou rolante de 7 dias ('rolling'). "
             "Banda = VWAP +- d*ATR14. Compra quando o candle anterior fechou abaixo da banda inferior e o atual fecha de "
             "volta acima dela (ainda abaixo do VWAP), com fechamento acima da EMA200; venda no espelho. Alvo: VWAP; stop "
             "k*ATR14; saída por tempo em 7 dias. Volume só do Bitstamp."),
    "timeframes": ["H1", "H4"],
    "grid": {"anchor": ["week", "rolling"], "d": [1.5, 2.0, 2.5, 3.0], "k": [1.5, 2.5], "side": ["long", "both"]},
}


def vwap_week(df, anchor):
    tp = (df.high.values + df.low.values + df.close.values) / 3.0
    v = df.volume.values
    pv = tp * v
    step = (df.index[1:] - df.index[:-1]).min()
    per_week = int(pd.Timedelta("7D") / step)
    if anchor == "rolling":
        num = pd.Series(pv).rolling(per_week).sum().values
        den = pd.Series(v).rolling(per_week).sum().values
        ok = np.ones(len(v), bool)
    else:
        wk = (df.index - pd.to_timedelta(df.index.dayofweek, unit="D")).floor("D")
        num = pd.Series(pv).groupby(wk).cumsum().values
        den = pd.Series(v).groupby(wk).cumsum().values
        ok = np.asarray((df.index - wk) / pd.Timedelta("1h")) >= 23.99
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(den > 0, num / den, np.nan)
    out[~ok] = np.nan
    return out, per_week


def signals(df, p):
    c = df.close.values
    vw, per_week = vwap_week(df, p["anchor"])
    a = ind.atr(df, 14)
    lo = vw - p["d"] * a
    hi = vw + p["d"] * a
    t = ind.ema(c, 200)
    up = (ind.prev(c) < ind.prev(lo)) & (c > lo) & (c < vw) & (c > t)
    dn = (ind.prev(c) > ind.prev(hi)) & (c < hi) & (c > vw) & (c < t)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": c >= vw, "exit_short": c <= vw, "max_hold": per_week}
