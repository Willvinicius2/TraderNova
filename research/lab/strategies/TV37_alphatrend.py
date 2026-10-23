"""TV37 - AlphaTrend, Pine de KivancOzbilgic."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV37_alphatrend",
    "name": "AlphaTrend (MFI + ATR): cruzamento com a própria linha de 2 candles atrás",
    "family": "tendencia",
    "round": 4,
    "origin": "TradingView comunidade (KivancOzbilgic)",
    "sources": [
        "https://www.tradingview.com/script/o50NYLAZ-AlphaTrend/",
        "Código: github.com/deepentropy/lightweight-charts-indicators src/community/alpha-trend.ts (port fiel do Pine)",
    ],
    "rule": ("Pine (coeficiente 1, período 14): ATR = SMA(TR, período); upT = mínima - ATR*coef; downT = máxima + ATR*coef; "
             "AlphaTrend = se MFI(hlc3, período) >= 50 (ou RSI com novol): max(upT, AT[1]) senão min(downT, AT[1]). "
             "Compra quando AT cruza acima de AT[2] e a última venda bruta é mais recente que a compra bruta anterior "
             "(filtro de alternância O1>K2 do script); venda no espelho. Sai/inverte no sinal oposto; side=long só compra. "
             "Sem stop no script: stop de proteção k*ATR14 (Wilder)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"coef": [0.5, 1.0, 1.5, 2.0], "period": [7, 14, 21], "filt": ["mfi", "rsi"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def mfi(df, n):
    tp = (df.high.values + df.low.values + df.close.values) / 3.0
    rmf = tp * df.volume.values
    dtp = np.diff(tp, prepend=np.nan)
    ps = ind.sma(np.where(dtp > 0, rmf, 0.0), n) * n
    ns = ind.sma(np.where(dtp < 0, rmf, 0.0), n) * n
    with np.errstate(divide="ignore", invalid="ignore"):
        out = 100 - 100 / (1 + ps / ns)
    out[: n] = np.nan
    return out


def alphatrend(df, coef, period, filt):
    h, l, c = df.high.values, df.low.values, df.close.values
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    atr = ind.sma(tr, period)
    f = mfi(df, period) if filt == "mfi" else ind.rsi(c, period)
    upT, dnT = l - atr * coef, h + atr * coef
    at = np.full(len(c), np.nan)
    for i in range(len(c)):
        pv = at[i - 1] if i and not np.isnan(at[i - 1]) else 0.0
        if f[i] >= 50:  # NaN compara falso, como no Pine
            at[i] = pv if upT[i] < pv else upT[i]
        else:
            at[i] = pv if dnT[i] > pv else dnT[i]
    return at


def signals(df, p):
    at = alphatrend(df, p["coef"], p["period"], p["filt"])
    at2 = ind.prev(at, 2)
    bk = ind.cross_above(at, at2)
    sk = ind.cross_below(at, at2)
    n = len(at)
    buy = np.zeros(n, bool)
    sell = np.zeros(n, bool)
    lb = ls = -1  # última compra/venda bruta antes do candle atual
    for i in range(n):
        if bk[i] and lb >= 0 and ls >= 0 and ls > lb:  # O1 (barssince compra anterior) > K2 (barssince venda)
            buy[i] = True
        if sk[i] and lb >= 0 and ls >= 0 and lb > ls:
            sell[i] = True
        if bk[i]:
            lb = i
        if sk[i]:
            ls = i
    buy[:200] = False
    sell[:200] = False
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": sell, "exit_short": buy}
