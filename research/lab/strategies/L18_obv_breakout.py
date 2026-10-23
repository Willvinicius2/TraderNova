"""L18 - Rompimento do On-Balance Volume (Granville)."""
import numpy as np

import indicators as ind

META = {
    "id": "L18_obv_breakout",
    "name": "Rompimento do OBV (Granville) confirmado pelo preço",
    "family": "tempo_volume",
    "sources": [
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/on-balance-volume-obv",
        "https://www.incrediblecharts.com/indicators/on_balance_volume.php",
        "https://www.metatrader4.com/en/trading-platform/help/analytics/tech_indicators/on_balance_volume",
    ],
    "rule": ("OBV de Granville (soma o volume do candle se fecha acima do anterior, subtrai se fecha abaixo). Compra quando o "
             "OBV fecha acima da máxima dos N candles anteriores (rompimento do OBV, que segundo Granville antecede o preço) "
             "e o preço confirma fechando acima da EMA(N). Venda no espelho (OBV abaixo da mínima de N e preço abaixo da EMA). "
             "Sai quando o OBV cruza de volta sua média SMA(N). Stop k*ATR14. Volume é só do Bitstamp (uma corretora)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [20, 40, 80], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def obv(df):
    c = df.close.values
    v = df.volume.values
    d = np.sign(np.diff(c, prepend=c[0]))
    return np.cumsum(d * v)


def signals(df, p):
    n = p["n"]
    c = df.close.values
    o = obv(df)
    hi = ind.prev(ind.highest(o, n))
    lo = ind.prev(ind.lowest(o, n))
    e = ind.ema(c, n)
    m = ind.sma(o, n)
    up = (o > hi) & (c > e)
    dn = (o < lo) & (c < e)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": o < m, "exit_short": o > m}
