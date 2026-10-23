"""TV11 - Technical Ratings Strategy (estratégia embutida do TradingView, "Technicals Strategy").

Help Center (43000628415): entra comprado quando o Technical Rating marca Strong Buy e vendido em Strong Sell;
stop = 3*ATR(14); stop móvel ativado quando o lucro chega a 5*ATR(14) e depois fica 2*ATR(14) atrás do melhor preço.
Rating (Help Center 43000614331 e indicador aberto "Technical Ratings" do TradingView): 15 médias
(SMA/EMA 10,20,30,50,100,200; HMA9; VWMA20; Ichimoku 9/26/52) e 11 osciladores (RSI14, Estocástico 14/3/3,
CCI20, ADX/DMI 14, Awesome, Momentum10, MACD 12/26/9, StochRSI 3/3/14/14, Williams %R 14, Bull Bear Power 13,
Ultimate 7/14/28), cada um vale +1/0/-1; média dos dois grupos; Strong Buy > 0,5, Strong Sell < -0,5.
Regras de cada componente reproduzidas do código Pine aberto do indicador (de memória do código público,
ver notas). Tendência para StochRSI/BBP: fechamento acima/abaixo da SMA50.

Aproximações: o stop móvel do Pine é intra-candle (máxima); aqui o nível é recalculado no fechamento com a melhor
máxima/mínima desde a entrada e passa a valer a partir do candle seguinte. Para saber o preço de entrada, signals()
simula a mesma sequência de posições do motor (entrada na abertura seguinte, stop, inversão), de forma causal.
"""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV11_technical_ratings",
    "name": "Technical Ratings Strategy (TradingView)",
    "family": "tendencia",
    "round": 2,
    "origin": "TradingView embutida",
    "sources": [
        "https://www.tradingview.com/support/solutions/43000628415/",
        "https://www.tradingview.com/support/solutions/43000614331-technical-ratings/",
        "https://www.tradingview.com/script/Jdw7wW2g-Technical-Ratings/",
        "https://www.oanda.jp/lab-education/tradingviewstrategy/strategy/tradingview_technicals_strategy/",
    ],
    "rule": ("Rating técnico do TradingView (15 médias + 11 osciladores, cada um +1/0/-1, média dos grupos). "
             "Compra quando o rating passa de +thr (Strong Buy = 0,5) e vende quando fica abaixo de -thr (inverte). "
             "Stop 3*ATR(14); stop móvel ativado com lucro de act*ATR (padrão 5) e mantido 2*ATR atrás do melhor preço. "
             "group escolhe o rating usado: todos, só médias ou só osciladores. No modo só compra, Strong Sell fecha a compra."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"group": ["all", "mas", "osc"], "thr": [0.4, 0.5, 0.6], "act": [3.0, 5.0, 7.0], "side": ["long", "both"]},
}

_CACHE = {}


def _rma(x, n):
    return pd.Series(x).ewm(alpha=1 / n, adjust=False, min_periods=n).mean().values


def _wma(x, n):
    w = np.arange(1, n + 1, dtype=float)
    return pd.Series(x).rolling(n).apply(lambda v: np.dot(v, w) / w.sum(), raw=True).values


def _stoch(src, h, l, n):
    hh, ll = ind.highest(h, n), ind.lowest(l, n)
    with np.errstate(invalid="ignore", divide="ignore"):
        return 100 * (src - ll) / (hh - ll)


def _rate(buy, sell, valid):
    r = np.where(buy, 1.0, np.where(sell, -1.0, 0.0))
    return np.where(valid, r, np.nan)


def ratings(df):
    key = (len(df), float(df.close.values[-1]), str(df.index[0]))
    if key in _CACHE:
        return _CACHE[key]
    o, h, l, c, v = (df[k].values for k in ("open", "high", "low", "close", "volume"))
    p1 = ind.prev(c)
    # ---------- médias ----------
    ma = []
    for n in (10, 20, 30, 50, 100, 200):
        for m in (ind.sma(c, n), ind.ema(c, n)):
            ma.append(_rate(m < c, m > c, ~np.isnan(m)))
    hma = _wma(2 * _wma(c, 4) - _wma(c, 9), 3)
    ma.append(_rate(hma < c, hma > c, ~np.isnan(hma)))
    vw = pd.Series(c * v).rolling(20).sum().values / pd.Series(v).rolling(20).sum().values
    ma.append(_rate(vw < c, vw > c, np.isfinite(vw)))
    don = lambda n: (ind.highest(h, n) + ind.lowest(l, n)) / 2
    conv, base = don(9), don(26)
    lead1, lead2 = (conv + base) / 2, don(52)
    ic_b = (lead1 > lead2) & (c > lead1) & (c < base) & (p1 < conv) & (c > conv)
    ic_s = (lead2 > lead1) & (c < lead2) & (c > base) & (p1 > conv) & (c < conv)
    ma.append(_rate(ic_b, ic_s, ~np.isnan(lead2) & ~np.isnan(p1)))
    # ---------- osciladores ----------
    os_ = []
    sma50 = ind.sma(c, 50)
    upt, dnt = c > sma50, c < sma50
    r = ind.rsi(c, 14)
    r1 = ind.prev(r)
    os_.append(_rate((r < 30) & (r1 < r), (r > 70) & (r1 > r), ~np.isnan(r1)))
    k = ind.sma(_stoch(c, h, l, 14), 3)
    d = ind.sma(k, 3)
    os_.append(_rate((k < 20) & (d < 20) & (k > d), (k > 80) & (d > 80) & (k < d), ~np.isnan(d)))
    tp = c  # o rating usa ta.cci(close, 20)
    sm = ind.sma(tp, 20)
    md = pd.Series(tp).rolling(20).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True).values
    with np.errstate(invalid="ignore", divide="ignore"):
        cci = (tp - sm) / (0.015 * md)
    cci1 = ind.prev(cci)
    os_.append(_rate((cci < -100) & (cci > cci1), (cci > 100) & (cci < cci1), np.isfinite(cci1)))
    upm = np.r_[np.nan, np.diff(h)]
    dnm = -np.r_[np.nan, np.diff(l)]
    plus = np.where((upm > dnm) & (upm > 0), upm, 0.0)
    minus = np.where((dnm > upm) & (dnm > 0), dnm, 0.0)
    pc = ind.prev(c)
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    trr = _rma(tr[1:], 14)
    with np.errstate(invalid="ignore", divide="ignore"):
        pdi = np.r_[np.nan, 100 * _rma(plus[1:], 14) / trr]
        mdi = np.r_[np.nan, 100 * _rma(minus[1:], 14) / trr]
        dx = 100 * np.abs(pdi - mdi) / (pdi + mdi)
    adx = np.r_[np.full(1, np.nan), _rma(np.nan_to_num(dx[1:], nan=0.0), 14)]
    adx[: 28] = np.nan
    pdi1, mdi1 = ind.prev(pdi), ind.prev(mdi)
    os_.append(_rate((adx > 20) & (pdi1 < mdi1) & (pdi > mdi), (adx > 20) & (pdi1 > mdi1) & (pdi < mdi), ~np.isnan(adx) & ~np.isnan(pdi1)))
    hl2 = (h + l) / 2
    ao = ind.sma(hl2, 5) - ind.sma(hl2, 34)
    ao1, ao2 = ind.prev(ao), ind.prev(ao, 2)
    ao_b = ((ao > 0) & (ao1 <= 0)) | ((ao > 0) & (ao1 > 0) & (ao > ao1) & (ao2 > ao1))
    ao_s = ((ao < 0) & (ao1 >= 0)) | ((ao < 0) & (ao1 < 0) & (ao < ao1) & (ao2 < ao1))
    os_.append(_rate(ao_b, ao_s, ~np.isnan(ao2)))
    mom = c - ind.prev(c, 10)
    mom1 = ind.prev(mom)
    os_.append(_rate(mom > mom1, mom < mom1, ~np.isnan(mom1)))
    macd = ind.ema(c, 12) - ind.ema(c, 26)
    sig = ind.ema(macd, 9)
    os_.append(_rate(macd > sig, macd < sig, ~np.isnan(sig)))
    rk = ind.sma(_stoch(r, r, r, 14), 3)
    rd = ind.sma(rk, 3)
    os_.append(_rate(dnt & (rk < 20) & (rd < 20) & (rk > rd), upt & (rk > 80) & (rd > 80) & (rk < rd), ~np.isnan(rd) & ~np.isnan(sma50)))
    wr = -100 * (ind.highest(h, 14) - c) / (ind.highest(h, 14) - ind.lowest(l, 14))
    wr1 = ind.prev(wr)
    os_.append(_rate((wr < -80) & (wr > wr1), (wr > -20) & (wr < wr1), np.isfinite(wr1)))
    e13 = ind.ema(c, 13)
    bull, bear = h - e13, l - e13
    os_.append(_rate(upt & (bear < 0) & (bear > ind.prev(bear)), dnt & (bull > 0) & (bull < ind.prev(bull)),
                     ~np.isnan(ind.prev(e13)) & ~np.isnan(sma50)))
    bp = c - np.fmin(l, pc)
    trb = np.fmax(h, pc) - np.fmin(l, pc)
    av = lambda n: pd.Series(bp).rolling(n).sum().values / pd.Series(trb).rolling(n).sum().values
    uo = 100 * (4 * av(7) + 2 * av(14) + av(28)) / 7
    os_.append(_rate(uo > 70, uo < 30, np.isfinite(uo)))
    with np.errstate(invalid="ignore"):
        rm = np.nanmean(np.vstack(ma), axis=0)
        ro = np.nanmean(np.vstack(os_), axis=0)
    # exige todos os componentes disponíveis (aquecimento de 200 candles)
    ok = ~np.isnan(np.vstack(ma)).any(axis=0) & ~np.isnan(np.vstack(os_)).any(axis=0)
    rm, ro = np.where(ok, rm, np.nan), np.where(ok, ro, np.nan)
    out = {"mas": rm, "osc": ro, "all": (rm + ro) / 2}
    _CACHE.clear()
    _CACHE[key] = out
    return out


def _trail(df, entry, stopd, exl, exs, atr, act, off):
    """Simula a sequência de posições do motor para saber o preço de entrada e montar o stop móvel do Pine."""
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    n = len(c)
    trail = np.full(n, np.nan)
    pos = 0
    pending = 0
    pstop = 0.0
    ep = sp = best = 0.0
    i = 1
    while i < n:
        if pending and pos == 0:
            pos, ep = pending, o[i]
            sp = ep - pos * pstop
            best = ep
            pending = 0
        if pos:
            hit = (o[i] <= sp or l[i] <= sp) if pos > 0 else (o[i] >= sp or h[i] >= sp)
            if hit:
                pos = 0
            else:
                best = max(best, h[i]) if pos > 0 else min(best, l[i])
                if not np.isnan(atr[i]) and (best - ep) * pos >= act * atr[i]:
                    lvl = best - pos * off * atr[i]
                    trail[i] = (c[i] - lvl) * pos
                    sp = max(sp, lvl) if pos > 0 else min(sp, lvl)
        if i + 1 >= n:
            break
        if pos:
            want = (pos > 0 and exl[i]) or (pos < 0 and exs[i])
            flip = entry[i] == -pos
            if want or flip:
                pb = pos
                pos = 0
                if flip and stopd[i] > 0:
                    pending, pstop = -pb, stopd[i]
                i += 1
                continue
        elif entry[i] and stopd[i] > 0:
            pending, pstop = int(entry[i]), stopd[i]
        i += 1
    return trail


def signals(df, p):
    rt = ratings(df)[p["group"]]
    thr = p["thr"]
    buy = rt > thr
    sell = rt < -thr
    entry = np.where(buy, 1, np.where(sell, -1, 0)).astype(np.int8)
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0).astype(np.int8)
    a = ind.atr(df, 14)
    stop = np.nan_to_num(3.0 * a, nan=0.0)
    exl, exs = sell, buy
    trail = _trail(df, entry, stop, exl, exs, a, p["act"], 2.0)
    return {"entry": entry, "stop": stop, "trail": trail, "exit_long": exl, "exit_short": exs}
