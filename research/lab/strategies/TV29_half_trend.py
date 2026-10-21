"""HalfTrend (everget): troca de tendência."""
import numpy as np

import indicators as ind

META = {
    "id": "TV29_half_trend",
    "name": "HalfTrend (everget): sinal Buy/Sell",
    "family": "tendencia",
    "round": 3,
    "origin": "TradingView comunidade (everget)",
    "sources": [
        "https://www.tradingview.com/script/U1SJ8ubc-HalfTrend/",
        "https://github.com/everget/tradingview-pinescript-indicators/blob/master/trailing_stops/halftrend.pine",
        "https://www.marketcalls.in/amibroker/halftrend-amibroker-afl-code-better-than-supertrend.html",
    ],
    "rule": ("Pine original do everget (repositório GitHub do autor): highPrice/lowPrice = máxima/mínima das últimas 'amplitude' "
             "barras, highma/lowma = SMA(high/low, amplitude). Em alta, guarda minHighPrice; vira para alta quando lowma > "
             "minHighPrice e fechamento > máxima anterior. Em baixa, guarda maxLowPrice; vira para baixa quando highma < maxLowPrice "
             "e fechamento < mínima anterior. Compra no sinal Buy (trend 1->0), vende no Sell (0->1); sai/inverte no sinal oposto. "
             "channelDeviation só desenha o canal ATR e não altera sinais. Pine sem stop: stop de proteção k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"amplitude": [2, 3, 5, 8, 13, 21], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def halftrend(df, amp):
    h, l, c = df.high.values, df.low.values, df.close.values
    n = len(c)
    hp = ind.highest(h, amp)
    lp = ind.lowest(l, amp)
    hma = ind.sma(h, amp)
    lma = ind.sma(l, amp)
    trend = np.zeros(n, dtype=int)
    tr_ = 0
    nxt = 0
    maxlow = l[0]
    minhigh = h[0]
    for i in range(n):
        if np.isnan(hp[i]) or np.isnan(hma[i]):
            trend[i] = tr_
            continue
        pl = l[i - 1] if i else l[i]
        ph = h[i - 1] if i else h[i]
        if nxt == 1:
            maxlow = max(lp[i], maxlow)
            if hma[i] < maxlow and c[i] < pl:
                tr_, nxt, minhigh = 1, 0, hp[i]
        else:
            minhigh = min(hp[i], minhigh)
            if lma[i] > minhigh and c[i] > ph:
                tr_, nxt, maxlow = 0, 1, lp[i]
        trend[i] = tr_
    return trend


def signals(df, p):
    t = halftrend(df, p["amplitude"])
    pt = np.r_[0, t[:-1]]
    buy = (t == 0) & (pt == 1)
    sell = (t == 1) & (pt == 0)
    buy[: 100] = False  # Pine usa ATR(100) para desenhar; sem sinais no aquecimento
    sell[: 100] = False
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": sell, "exit_short": buy}
