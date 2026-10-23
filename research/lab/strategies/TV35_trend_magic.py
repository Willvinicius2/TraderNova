"""TV35 - Trend Magic (CCI + ATR), versão Pine de KivancOzbilgic (TradingView comunidade)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV35_trend_magic",
    "name": "Trend Magic (CCI + ATR): virada da linha",
    "family": "tendencia",
    "round": 3,
    "origin": "TradingView comunidade (KivancOzbilgic, portado do MetaTrader)",
    "sources": [
        "https://www.tradingview.com/script/kRIjThLZ-Trend-Magic/",
        "https://www.luxalgo.com/library/indicator/kRIjThLZ-trend-magic/",
        "https://it.tradingview.com/script/uRqGTZOw",
    ],
    "rule": ("Pine (CCI período 20, coeficiente 1, ATR período 5): ATR=SMA(TR,5); upT=mín-ATR*coef; downT=máx+ATR*coef; "
             "MagicTrend = se CCI(fech,n)>=0: max(upT, MagicTrend[1]) (só sobe); senão min(downT, MagicTrend[1]) (só desce). "
             "Cor azul/verde com CCI>=0 e vermelha/rosa com CCI<0. Sinais do script: compra quando a mínima cruza acima da linha "
             "(crossover(low,MagicTrend)) e venda quando a máxima cruza abaixo (crossunder(high,MagicTrend)) = modo 'alerta'; "
             "modo 'cor' entra na troca de cor (CCI cruza 0). Sai/inverte no sinal oposto do mesmo modo. side=long só compra. "
             "Sem stop no script: stop de proteção k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [14, 20, 30, 50], "coef": [1.0, 1.5, 2.0], "mode": ["alerta", "cor"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def cci(x, n):
    s = pd.Series(x)
    ma = s.rolling(n).mean()
    md = s.rolling(n).apply(lambda v: np.mean(np.abs(v - v.mean())), raw=True)
    return ((s - ma) / (0.015 * md)).values


def magic(h, l, c, cc, coef, ap=5):
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    atr = ind.sma(tr, ap)
    up, dn = l - atr * coef, h + atr * coef
    mt = np.full(len(c), np.nan)
    last = 0.0  # nz(MagicTrend[1])
    for i in range(len(c)):
        if np.isnan(cc[i]) or np.isnan(atr[i]):
            continue
        if cc[i] >= 0:
            last = last if up[i] < last else up[i]
        else:
            last = last if dn[i] > last else dn[i]
        mt[i] = last
    return mt


_cci, _mt = {}, {}


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    k1 = (id(df), len(df), p["n"])
    if k1 not in _cci:
        _cci[k1] = cci(c, p["n"])
    cc = _cci[k1]
    k2 = k1 + (p["coef"],)
    if k2 not in _mt:
        _mt[k2] = magic(h, l, c, cc, p["coef"])
    mt = _mt[k2]
    warm = np.arange(len(c)) < 3 * p["n"]
    if p["mode"] == "alerta":
        lg, sh = ind.cross_above(l, mt), ind.cross_below(h, mt)
    else:
        z = np.zeros(len(c))
        lg = (cc >= 0) & (ind.prev(cc) < 0)
        sh = (cc < 0) & (ind.prev(cc) >= 0)
    lg, sh = lg & ~warm, sh & ~warm
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": sh, "exit_short": lg}
