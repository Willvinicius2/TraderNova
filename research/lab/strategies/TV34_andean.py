"""TV34 - Andean Oscillator (alexgrover / Alex Pierrefeu, TradingView comunidade)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV34_andean",
    "name": "Andean Oscillator (alexgrover): cruzamento Bull/Bear",
    "family": "tendencia",
    "round": 3,
    "origin": "TradingView comunidade (alexgrover)",
    "sources": [
        "https://www.tradingview.com/script/x9qYvBYN-Andean-Oscillator/",
        "https://alpaca.markets/learn/andean-oscillator-a-new-technical-indicator-based-on-an-online-algorithm-for-trend-analysis/",
        "https://www.prorealcode.com/prorealtime-indicators/andean-oscillator/",
    ],
    "rule": ("Pine de alexgrover (lido via resumo do WebSearch; o WebFetch não abriu as páginas): alpha=2/(n+1); envelopes 'online' "
             "up1=max(C,O,up1[1]-(up1[1]-C)*alpha), up2=max(C²,O²,up2[1]-(up2[1]-C²)*alpha), dn1=min(C,O,dn1[1]+(C-dn1[1])*alpha), "
             "dn2=min(C²,O²,dn2[1]+(C²-dn2[1])*alpha); Bull=sqrt(dn2-dn1²), Bear=sqrt(up2-up1²), Signal=EMA(max(Bull,Bear),9). "
             "Leitura do autor: Bull>Bear = tendência de alta, e o componente acima da linha de sinal indica tendência forte. "
             "Regra testada: compra quando Bull cruza acima de Bear (modo 'cruz') ou quando Bull>Bear e Bull>Signal começam a valer juntos "
             "(modo 'sinal'); venda no espelho (side=both); sai quando a condição oposta aparece (Bear cruza acima de Bull). "
             "O script é indicador, sem stop: stop de proteção k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [25, 50, 100, 200], "mode": ["cruz", "sinal"], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}

_cache = {}


def andean(o, c, n, sig_n=9):
    a = 2.0 / (n + 1)
    N = len(c)
    bull, bear = np.full(N, np.nan), np.full(N, np.nan)
    up1 = up2 = dn1 = dn2 = 0.0
    for i in range(N):
        C, O = c[i], o[i]
        C2, O2 = C * C, O * O
        if i == 0:  # no 1º candle up1[1] é na e o nz(...) do Pine devolve C / C²
            up1, up2, dn1, dn2 = C, C2, C, C2
        else:
            up1 = max(C, O, up1 - (up1 - C) * a)
            up2 = max(C2, O2, up2 - (up2 - C2) * a)
            dn1 = min(C, O, dn1 + (C - dn1) * a)
            dn2 = min(C2, O2, dn2 + (C2 - dn2) * a)
        bull[i] = np.sqrt(max(dn2 - dn1 * dn1, 0.0))
        bear[i] = np.sqrt(max(up2 - up1 * up1, 0.0))
    sig = ind.ema(np.maximum(bull, bear), sig_n)
    return bull, bear, sig


def signals(df, p):
    key = (id(df), len(df), p["n"])
    if key not in _cache:
        _cache[key] = andean(df.open.values, df.close.values, p["n"])
    bull, bear, sg = _cache[key]
    warm = np.arange(len(bull)) < 3 * p["n"]  # envelopes ainda convergindo
    if p["mode"] == "cruz":
        lg, sh = ind.cross_above(bull, bear), ind.cross_below(bull, bear)
    else:
        cl = (bull > bear) & (bull > sg)
        cs = (bear > bull) & (bear > sg)
        lg = cl & ~np.r_[False, cl[:-1]]
        sh = cs & ~np.r_[False, cs[:-1]]
    lg, sh = lg & ~warm, sh & ~warm
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    xl, xs = ind.cross_above(bear, bull), ind.cross_above(bull, bear)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": xl, "exit_short": xs}
