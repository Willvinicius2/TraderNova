"""L16 - Engolfo a favor da tendência (filtro de média longa)."""
import numpy as np

import indicators as ind

META = {
    "id": "L16_engulfing_trend",
    "name": "Engolfo a favor da tendência (SMA longa)",
    "family": "padroes",
    "sources": [
        "https://www.tradingview.com/script/HDIiStyH-Optimized-Engulfing-Strategy/",
        "https://ungeracademy.com/blog/how-to-test-patterns-with-trading-systems-example-test-on-engulfing",
        "Steve Nison, Japanese Candlestick Charting Techniques (1991) - definição do engolfo",
    ],
    "rule": ("Engolfo de alta: candle anterior de baixa e candle atual de alta cujo corpo cobre o corpo anterior "
             "(abertura <= fechamento anterior e fechamento >= abertura anterior), corpo atual >= minbody*ATR. "
             "Só compra com fechamento acima da SMA(L); venda no espelho (engolfo de baixa abaixo da SMA(L)). "
             "Stop além da mínima/máxima dos dois candles do padrão (mínimo 0,5*ATR); alvo tr*R; saída por tempo após 20 candles."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"L": [100, 200], "minbody": [0.0, 0.5], "tr": [1.5, 2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    po, pc = ind.prev(o), ind.prev(c)
    a = ind.atr(df, 14)
    body = np.abs(c - o)
    big = body >= p["minbody"] * a
    bull = (pc < po) & (c > o) & (o <= pc) & (c >= po) & (body > np.abs(pc - po)) & big
    bear = (pc > po) & (c < o) & (o >= pc) & (c <= po) & (body > np.abs(pc - po)) & big
    m = ind.sma(c, p["L"])
    bull &= c > m
    bear &= c < m
    entry = np.where(bull, 1, np.where(bear, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    lo2 = np.minimum(l, ind.prev(l))
    hi2 = np.maximum(h, ind.prev(h))
    floor = 0.5 * a
    stop = np.where(entry > 0, np.maximum(c - lo2, floor), np.where(entry < 0, np.maximum(hi2 - c, floor), a))
    return {"entry": entry, "stop": stop, "target_r": p["tr"], "max_hold": 20}
