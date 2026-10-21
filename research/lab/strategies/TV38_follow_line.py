"""TV38 - Follow Line Indicator, Pine de Dreadblitz."""
import numpy as np

import indicators as ind

META = {
    "id": "TV38_follow_line",
    "name": "Follow Line (rompimento de Bollinger + ATR): virada da linha",
    "family": "tendencia",
    "round": 4,
    "origin": "TradingView comunidade (Dreadblitz)",
    "sources": [
        "https://www.tradingview.com/script/29iYBNku-Follow-Line-Indicator/",
        "https://it.tradingview.com/script/RwHWOeMU",
        "Código: github.com/deepentropy/lightweight-charts-indicators src/community/follow-line.ts (port fiel do Pine)",
    ],
    "rule": ("Pine (BB 21, desvio 1, filtro ATR ligado, ATR 5): fechamento acima de SMA+desv*DP leva a linha para mínima - ATR "
             "(nunca abaixo da linha anterior); fechamento abaixo de SMA-desv*DP leva a linha para máxima + ATR (nunca acima); dentro "
             "das bandas a linha fica. Tendência = +1 quando a linha sobe, -1 quando desce. Compra na virada para +1, venda na virada "
             "para -1 (alertas do script). Como no original, o ATR(5) de cada lado é uma RMA do TR calculada só nos candles em que é "
             "chamado. Sai/inverte na virada oposta; side=long só compra. Sem stop no script: stop de proteção k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"bb": [14, 21, 34], "dev": [0.75, 1.0, 1.5], "atrf": [0, 1], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def rma_when(mask, x, n):
    out = np.full(len(x), np.nan)
    cnt, s, v = 0, 0.0, np.nan
    for i in np.flatnonzero(mask):
        if np.isnan(x[i]):
            continue
        cnt += 1
        if cnt < n:
            s += x[i]
        elif cnt == n:
            s += x[i]
            v = s / n
        else:
            v = (v * (n - 1) + x[i]) / n
        out[i] = v
    return out


def follow_line(df, bb, dev, atrf, ap=5):
    h, l, c = df.high.values, df.low.values, df.close.values
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    m, sd = ind.sma(c, bb), ind.stdev(c, bb)
    sig = np.where(c > m + sd * dev, 1, np.where(c < m - sd * dev, -1, 0))
    au = rma_when(sig == 1, tr, ap) if atrf else np.zeros(len(c))
    ad = rma_when(sig == -1, tr, ap) if atrf else np.zeros(len(c))
    n = len(c)
    tl = np.full(n, np.nan)
    it = np.full(n, np.nan)
    for i in range(n):
        ptl = tl[i - 1] if i else np.nan
        t = ptl
        if sig[i] == 1:
            t = l[i] - au[i]
            if t < ptl:
                t = ptl
        elif sig[i] == -1:
            t = h[i] + ad[i]
            if t > ptl:
                t = ptl
        pit = it[i - 1] if i else np.nan
        x = pit
        if t > ptl:
            x = 1
        if t < ptl:
            x = -1
        tl[i], it[i] = t, x
    return tl, it


def signals(df, p):
    _, it = follow_line(df, p["bb"], p["dev"], p["atrf"])
    pit = ind.prev(it, 1)
    buy = (pit == -1) & (it == 1)
    sell = (pit == 1) & (it == -1)
    buy[:200] = False
    sell[:200] = False
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": sell, "exit_short": buy}
