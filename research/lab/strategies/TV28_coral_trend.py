"""Coral Trend Indicator (LazyBear): virada de cor da linha Coral."""
import numpy as np

import indicators as ind

META = {
    "id": "TV28_coral_trend",
    "name": "Coral Trend (LazyBear): virada de cor",
    "family": "tendencia",
    "round": 3,
    "origin": "TradingView comunidade (LazyBear)",
    "sources": [
        "https://www.tradingview.com/script/qyUwc2Al-Coral-Trend-Indicator-LazyBear/",
        "https://www.tradingview.com/script/AzQo1gRi-Coral-Trend-Indicator-LazyBear-pine-v4/",
        "https://community.tradovate.com/t/coral-trend-indicator/4276",
        "https://www.marketcalls.in/amibroker/coral-trend-indicator-amibroker-afl-code.html",
    ],
    "rule": ("Pine de LazyBear (sm=21, cd=0,4 por padrão): di=(sm-1)/2+1, c1=2/(di+1); seis EMAs em cascata i1..i6 do fechamento "
             "com c1; bfr = -cd^3*i6 + c3*i5 + c4*i4 + c5*i3 (c3=3(cd²+cd³), c4=-3(2cd²+cd+cd³), c5=3cd+1+cd³+3cd²), filtro tipo T3 de "
             "Tillson. Cor verde quando bfr>bfr[1], vermelha quando bfr<bfr[1]. Compra quando a cor vira para verde, venda quando "
             "vira para vermelha (sinais Buy/Sell da versão pine-v4); sai/inverte na virada oposta. O Pine não tem stop: stop de "
             "proteção k*ATR14. TradingView inacessível ao WebFetch: código conferido em cópias citadas pela busca (Tradovate, "
             "MarketCalls AFL)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"sm": [13, 21, 34, 55], "cd": [0.2, 0.4, 0.6], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def coral(c, sm, cd):
    di = (sm - 1.0) / 2.0 + 1.0
    c1 = 2.0 / (di + 1.0)
    c2 = 1.0 - c1
    c3 = 3.0 * (cd * cd + cd * cd * cd)
    c4 = -3.0 * (2.0 * cd * cd + cd + cd * cd * cd)
    c5 = 3.0 * cd + 1.0 + cd * cd * cd + 3.0 * cd * cd
    n = len(c)
    st = np.zeros(6)  # nz(i[1]) = 0 no início, como no Pine
    bfr = np.full(n, np.nan)
    for t in range(n):
        x = c[t]
        for j in range(6):
            st[j] = c1 * x + c2 * st[j]
            x = st[j]
        bfr[t] = -cd ** 3 * st[5] + c3 * st[4] + c4 * st[3] + c5 * st[2]
    bfr[: int(6 * sm)] = np.nan  # aquecimento (Pine começa em zero)
    return bfr


def signals(df, p):
    c = df.close.values
    b = coral(c, p["sm"], p["cd"])
    pb = ind.prev(b)
    col = np.where(b > pb, 1, np.where(b < pb, -1, 0))
    # cor azul (igual) mantém a anterior para fins de virada
    for i in range(1, len(col)):
        if col[i] == 0:
            col[i] = col[i - 1]
    pcol = np.r_[0, col[:-1]]
    up = (col == 1) & (pcol == -1)
    dn = (col == -1) & (pcol == 1)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
