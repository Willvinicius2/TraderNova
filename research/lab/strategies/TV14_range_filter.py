"""Range Filter (DonovanWall / 'Range Filter Buy and Sell')."""
import numpy as np

import indicators as ind

META = {
    "id": "TV14_range_filter",
    "name": "Range Filter (DonovanWall)",
    "family": "tendencia",
    "round": 2,
    "origin": "TradingView comunidade (DonovanWall)",
    "sources": [
        "https://www.tradingview.com/script/lut7sBgG-Range-Filter-DW/",
        "https://www.prorealcode.com/topic/range-filter-buy-sell",
        "https://www.marketcalls.in/amibroker/range-filter-trading-strategy-amibroker-better-trend-following-indicator.html",
    ],
    "rule": ("Pine 'Range Filter Buy and Sell': faixa = EMA(EMA(|F-F[1]|, per), 2*per-1)*mult; filtro só anda quando o fechamento "
             "se afasta mais que a faixa (filt = max(filt[1], F-faixa) se F>filt[1], senão min(filt[1], F+faixa)). Contadores upward/"
             "downward = candles seguidos com filtro subindo/caindo. Compra quando F>filtro e upward>0 e o estado anterior era vendido "
             "(CondIni[1]=-1); venda no espelho. Sai/inverte no sinal oposto. Pine sem stop: stop de proteção k*ATR14. TradingView "
             "fora do ar para o WebFetch: lógica conferida nos ports do ProRealCode/mql5 e resumo de busca."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"per": [25, 50, 100, 200], "mult": [2.0, 3.0, 4.0], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def range_filter(c, per, mult):
    rng = ind.ema(ind.ema(np.abs(c - ind.prev(c)), per), 2 * per - 1) * mult
    n = len(c)
    filt = np.full(n, np.nan)
    up = np.zeros(n)
    dn = np.zeros(n)
    for i in range(n):
        r = rng[i]
        if np.isnan(r):
            continue
        f0 = filt[i - 1] if i > 0 and not np.isnan(filt[i - 1]) else c[i]
        if c[i] > f0:
            filt[i] = f0 if c[i] - r < f0 else c[i] - r
        else:
            filt[i] = f0 if c[i] + r > f0 else c[i] + r
        if i > 0 and not np.isnan(filt[i - 1]):
            up[i] = up[i - 1] + 1 if filt[i] > filt[i - 1] else (0 if filt[i] < filt[i - 1] else up[i - 1])
            dn[i] = dn[i - 1] + 1 if filt[i] < filt[i - 1] else (0 if filt[i] > filt[i - 1] else dn[i - 1])
    return filt, up, dn


def signals(df, p):
    c = df.close.values
    filt, up, dn = range_filter(c, p["per"], p["mult"])
    pc = ind.prev(c)
    lc = (c > filt) & (((c > pc) & (up > 0)) | ((c < pc) & (up > 0)))
    sc = (c < filt) & (((c < pc) & (dn > 0)) | ((c > pc) & (dn > 0)))
    n = len(c)
    cond = np.zeros(n, dtype=int)
    for i in range(n):
        cond[i] = 1 if lc[i] else (-1 if sc[i] else (cond[i - 1] if i else 0))
    pcond = np.r_[0, cond[:-1]]
    longs = lc & (pcond == -1)
    shorts = sc & (pcond == 1)
    entry = np.where(longs, 1, np.where(shorts, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": shorts, "exit_short": longs}
