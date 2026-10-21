"""L15 r1 - Rompimento de R1/S1 dos pivôs diários com filtro de tendência e saída na volta ao P."""
import numpy as np

import indicators as ind

import pandas as pd


def daily_pivots(df):
    """Igual a L15_floor_pivots: níveis do dia UTC anterior completo."""
    day = df.index.floor("D")
    d = df.groupby(day).agg(high=("high", "max"), low=("low", "min"), close=("close", "last")).shift(1)
    P = (d.high + d.low + d.close) / 3
    lv = pd.DataFrame({"P": P, "R1": 2 * P - d.low, "S1": 2 * P - d.high,
                       "R2": P + (d.high - d.low), "S2": P - (d.high - d.low)})
    return lv.reindex(day).values.T


META = {
    "id": "L15_floor_pivots_r1",
    "refines": "L15_floor_pivots",
    "refinement": ("No desenvolvimento só o modo rompimento comprado chegou perto de zero (PF ~1,04) e o alvo fixo em R2 cortava a tendência; "
                   "rejeição foi negativa em tudo. Refinamento: só rompimento, filtro de tendência (fechamento acima/abaixo da EMA L), "
                   "saída quando o fechamento volta para o outro lado do P (papel de suporte/resistência invertido) e alvo R2 opcional."),
    "name": "Pivôs diários: rompimento de R1/S1 com filtro de tendência",
    "family": "padroes",
    "sources": [
        "https://daytradingtoolkit.com/strategies/pivot-point-day-trading-strategy",
        "https://c.mql5.com/forextsd/forum/161/pivot_trading.pdf",
        "https://help.stockdoctor.com.au/hc/en-us/articles/360000099896-Pivot-Points",
    ],
    "rule": ("P=(M+m+F)/3 do dia UTC anterior, R1=2P-m, S1=2P-M, R2/S2=P±(M-m). Compra quando o fechamento cruza acima de R1 e está acima da EMA(L); "
             "venda quando cruza abaixo de S1 e está abaixo da EMA(L). Stop k*ATR14; sai se fechar do outro lado do P do dia, por alvo R2/S2 "
             "(se tgt='R2') ou por tempo após 'hold' horas."),
    "timeframes": ["M15", "H1", "H4"],
    "grid": {"L": [100, 200], "tgt": ["R2", "nenhum"], "k": [1.5, 2.0, 3.0], "hold": [24, 48, 96], "side": ["long", "both"]},
}


def signals(df, p):
    c = df.close.values
    P, R1, S1, R2, S2 = daily_pivots(df)
    e = ind.ema(c, p["L"])
    lng = ind.cross_above(c, R1) & (c > e) & (R2 - c > 0)
    sht = ind.cross_below(c, S1) & (c < e) & (c - S2 > 0)
    entry = np.where(lng, 1, np.where(sht, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    step = (df.index[1] - df.index[0]).total_seconds() / 3600.0
    out = {"entry": entry, "stop": p["k"] * a, "max_hold": max(1, int(round(p["hold"] / step))),
           "exit_long": c < P, "exit_short": c > P}
    if p["tgt"] == "R2":
        out["target"] = np.where(entry > 0, R2 - c, np.where(entry < 0, c - S2, np.nan))
    return out
