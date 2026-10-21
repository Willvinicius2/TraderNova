"""L15 - Pivôs clássicos de pregão (floor pivots) do dia anterior: rejeição ou rompimento."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L15_floor_pivots",
    "name": "Pivôs clássicos diários (P, R1, S1): rejeição ou rompimento",
    "family": "padroes",
    "sources": [
        "https://daytradingtoolkit.com/strategies/pivot-point-day-trading-strategy",
        "https://doc.stocksharp.com/en/designer-gallery/Pivot_Point_Reversal",
        "https://c.mql5.com/forextsd/forum/161/pivot_trading.pdf",
        "https://help.stockdoctor.com.au/hc/en-us/articles/360000099896-Pivot-Points",
    ],
    "rule": ("Com máxima M, mínima m e fechamento F do dia UTC anterior: P=(M+m+F)/3, R1=2P-m, S1=2P-M, R2=P+(M-m), S2=P-(M-m). "
             "Modo rejeição: compra quando o candle toca/fura S1 e fecha de volta acima de S1 com corpo de alta, alvo em P; venda no espelho em R1, alvo P. "
             "Modo rompimento: compra quando o fechamento cruza acima de R1, alvo R2; venda quando cruza abaixo de S1, alvo S2. "
             "Stop k*ATR14; saída por tempo após 'hold' horas. Não usa o extremo do dia anterior como gatilho de varredura."),
    "timeframes": ["M15", "H1", "H4"],
    "grid": {"mode": ["rejeicao", "rompimento"], "k": [1.0, 1.5, 2.0, 3.0], "hold": [12, 24, 48], "side": ["long", "both"]},
}

TF_H = {"M15": 0.25, "H1": 1.0, "H4": 4.0}


def daily_pivots(df):
    day = df.index.floor("D")
    d = df.groupby(day).agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    d = d.shift(1)  # dia anterior completo
    P = (d.high + d.low + d.close) / 3
    lv = pd.DataFrame({"P": P, "R1": 2 * P - d.low, "S1": 2 * P - d.high,
                       "R2": P + (d.high - d.low), "S2": P - (d.high - d.low)})
    return lv.reindex(day).values.T  # P, R1, S1, R2, S2 por candle


def signals(df, p):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    P, R1, S1, R2, S2 = daily_pivots(df)
    if p["mode"] == "rejeicao":
        lng = (l <= S1) & (c > S1) & (c > o) & (c < P)
        sht = (h >= R1) & (c < R1) & (c < o) & (c > P)
        tl, ts = P - c, c - P
    else:
        lng = ind.cross_above(c, R1)
        sht = ind.cross_below(c, S1)
        tl, ts = R2 - c, c - S2
    lng &= tl > 0
    sht &= ts > 0
    entry = np.where(lng, 1, np.where(sht, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    tgt = np.where(entry > 0, tl, np.where(entry < 0, ts, np.nan))
    a = ind.atr(df, 14)
    tf = getattr(df, "attrs", {}).get("tf")
    step = (df.index[1] - df.index[0]).total_seconds() / 3600.0 if len(df) > 1 else 1.0
    bars = max(1, int(round(p["hold"] / step)))
    return {"entry": entry, "stop": p["k"] * a, "target": tgt, "max_hold": bars}
