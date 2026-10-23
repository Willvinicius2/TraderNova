"""TV64 - Three Bar Reversal Pattern (LuxAlgo): confirmação do padrão de reversão de 3 barras."""
import numpy as np

import indicators as ind

META = {
    "id": "TV64_three_bar",
    "name": "Three Bar Reversal Pattern (LuxAlgo): confirmação acima da 1ª barra",
    "family": "padroes",
    "round": 5,
    "origin": "TradingView comunidade (LuxAlgo)",
    "sources": [
        "https://www.tradingview.com/script/ct5E4FSn-Three-Bar-Reversal-Pattern-LuxAlgo/",
        "https://github.com/deepentropy/lightweight-charts-indicators (src/community/three-bar-reversal-pattern.ts, port fiel do Pine, commit f8e1b0e)",
    ],
    "rule": ("Pine LuxAlgo: padrão de alta = barra 1 de baixa, barra 2 de baixa com máxima e mínima menores que a barra 1, barra 3 de alta "
             "com máxima acima da máxima da barra 1 (espelho para baixa). Tipo 'Enhanced' exige que a barra 3 já feche além da máxima da "
             "barra 1; 'All' aceita os dois. Filtro de tendência opcional do script ('Aligned'): Supertrend(10, 3) ou Donchian(13) dos "
             "fechamentos. O padrão fica aberto até um fechamento acima da máxima da barra 1 (confirmação = compra) ou abaixo da menor "
             "mínima das barras 2-3 (falha), ou até aparecer o padrão oposto. O indicador marca a confirmação na barra seguinte "
             "(usa close[1]); aqui a decisão é tomada no próprio fechamento que confirma e a entrada é na abertura seguinte (mesma "
             "informação, sem olhar o futuro). Sem saída no indicador: stop na linha de falha (menor mínima das barras 2-3; mínimo "
             "0,25*ATR14), alvo em tr*R; confirmação oposta fecha (side=long) ou inverte (side=both). Detalhe não reproduzido: no lado "
             "vendido o Pine cancela a confirmação se um padrão de alta surge no candle seguinte (exigiria olhar 1 candle à frente)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"ptype": ["all", "enhanced"], "trend": ["none", "st", "dc"], "tr": [1.0, 1.5, 2.0, 3.0], "side": ["long", "both"]},
}


def supertrend_dir(df, factor=3.0, n=10):
    """Direção do ta.supertrend do Pine: -1 = alta, +1 = baixa (causal)."""
    h, l, c = df.high.values, df.low.values, df.close.values
    a = ind.atr(df, n)
    src = (h + l) / 2
    up0, dn0 = src - factor * a, src + factor * a
    m = len(c)
    lower = np.full(m, np.nan)
    upper = np.full(m, np.nan)
    d = np.ones(m)
    st_is_upper = True
    for i in range(m):
        if np.isnan(a[i]):
            continue
        pl, pu = lower[i - 1], upper[i - 1]
        lower[i] = up0[i] if (np.isnan(pl) or up0[i] > pl or c[i - 1] < pl) else pl
        upper[i] = dn0[i] if (np.isnan(pu) or dn0[i] < pu or c[i - 1] > pu) else pu
        if np.isnan(a[i - 1]):
            d[i] = 1
        elif st_is_upper:
            d[i] = -1 if c[i] > upper[i] else 1
        else:
            d[i] = 1 if c[i] < lower[i] else -1
        st_is_upper = d[i] == 1
    return d


def trend_ok(df, mode):
    m = len(df)
    if mode == "none":
        return np.ones(m, bool), np.ones(m, bool)
    if mode == "st":
        d = supertrend_dir(df)
        return d < 0, d > 0
    c = df.close.values
    up, lo = ind.highest(c, 13), ind.lowest(c, 13)
    os_ = np.zeros(m)
    v = 0
    for i in range(1, m):
        if up[i] > up[i - 1]:
            v = 1
        elif lo[i] < lo[i - 1]:
            v = 0
        os_[i] = v
    return os_ == 1, os_ == 0


def run_patterns(c, bull, bear, bull_lvl, bull_ext, bear_lvl, bear_ext):
    """Máquina de estados do LuxAlgo, decidida no fechamento: retorna sinais de confirmação e a linha de falha."""
    m = len(c)
    buy = np.zeros(m, bool)
    sell = np.zeros(m, bool)
    stop_lv = np.full(m, np.nan)
    ba = sa = False
    blv = bex = slv = sex = np.nan
    for i in range(m):
        if bear[i]:
            ba = False
        if bull[i]:
            sa = False
        if bull[i]:
            ba, blv, bex = True, bull_lvl[i], bull_ext[i]
        if bear[i]:
            sa, slv, sex = True, bear_lvl[i], bear_ext[i]
        if ba:
            if c[i] > blv:
                buy[i] = True
                stop_lv[i] = bex
                ba = False
            elif c[i] < bex:
                ba = False
        if sa:
            if c[i] < slv:
                sell[i] = True
                stop_lv[i] = sex
                sa = False
            elif c[i] > sex:
                sa = False
    return buy, sell, stop_lv


def signals(df, p):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    o1, h1, l1, c1 = (ind.prev(x, 1) for x in (o, h, l, c))
    o2, h2, l2, c2 = (ind.prev(x, 2) for x in (o, h, l, c))
    upok, dnok = trend_ok(df, p["trend"])
    bull = (c2 < o2) & (l1 < l2) & (h1 < h2) & (c1 < o1) & (c > o) & (h > h2) & upok
    bear = (c2 > o2) & (h1 > h2) & (l1 > l2) & (c1 > o1) & (c < o) & (l < l2) & dnok
    if p["ptype"] == "enhanced":
        bull &= c > h2
        bear &= c < l2
    bull_ext = np.fmin(l1, l)
    bear_ext = np.fmax(h1, h)
    buy, sell, slv = run_patterns(c, bull, bear, h2, bull_ext, l2, bear_ext)
    a = ind.atr(df, 14)
    dist = np.where(buy, c - slv, np.where(sell, slv - c, np.nan))
    stop = np.fmax(dist, 0.25 * a)
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": stop, "target_r": p["tr"], "exit_long": sell, "exit_short": buy}
