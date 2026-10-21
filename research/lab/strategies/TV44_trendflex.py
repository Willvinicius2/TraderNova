"""Reflex & Trendflex (John Ehlers, TASC fev/2020), script da comunidade TradingView de e2e4."""
import numpy as np

import indicators as ind

META = {
    "id": "TV44_trendflex",
    "name": "Trendflex de Ehlers: cruzamento da linha zero",
    "family": "tendencia",
    "round": 4,
    "origin": "TradingView comunidade (e2e4; indicador de John F. Ehlers, TASC 2020)",
    "sources": [
        "https://www.tradingview.com/script/6tSfPE3W-Reflex-Trendflex/",
        "Ehlers, J. F. 'Reflex: A New Zero-Lag Indicator', Technical Analysis of Stocks & Commodities, fev/2020",
        "Código Pine traduzido: github.com/deepentropy/lightweight-charts-indicators src/community/reflex-trendflex.ts",
    ],
    "sourceNote": "Fórmula reproduzida do código traduzido (SuperSmoother de 2 polos, soma móvel, normalização RMS 0,04/0,96). "
                  "O script é indicador com alertas de cruzamento de zero; a regra de operação usa esses alertas do Trendflex.",
    "rule": "ss = SuperSmoother(fechamento, N); Trendflex = (N*ss - soma(ss[1..N]))/N, normalizado por sqrt(rms), rms = 0,04*v² + 0,96*rms anterior. "
            "Compra quando o Trendflex cruza acima de 0; vende quando cruza abaixo; sai no cruzamento oposto (inverte se 'both'). "
            "Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [10, 20, 30, 40], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def super_smoother(src, period):
    a = np.sqrt(2.0) * np.pi / (0.5 * period)
    decay = np.exp(-a)
    f1 = 2.0 * decay * np.cos(a)
    f2 = -decay * decay
    ci = (1.0 - f1 - f2) / 2.0
    s = np.nan_to_num(src)
    out = np.zeros(len(s))
    for i in range(len(s)):
        s1 = s[i - 1] if i > 0 else 0.0
        o1 = out[i - 1] if i > 0 else 0.0
        o2 = out[i - 2] if i > 1 else 0.0
        out[i] = ci * (s[i] + s1) + f1 * o1 + f2 * o2
    return out


def trendflex(src, n):
    sm = super_smoother(src, n)
    cs = np.r_[0.0, np.cumsum(sm)]  # cs[j] = soma de sm[0..j-1]
    idx = np.arange(len(sm))
    lo = np.maximum(idx - n, 0)
    sums = cs[idx] - cs[lo]  # soma de sm[i-n..i-1]
    v = (n * sm - sums) / n
    out = np.full(len(v), np.nan)
    rms = 0.0
    for i in range(len(v)):
        rms = 0.04 * v[i] * v[i] + 0.96 * rms
        if rms > 0:
            out[i] = v[i] / np.sqrt(rms)
    out[: 4 * n] = np.nan  # aquecimento dos filtros
    return out


def signals(df, p):
    tf = trendflex(df.close.values, p["n"])
    up = ind.cross_above(tf, 0 * tf)
    dn = ind.cross_below(tf, 0 * tf)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
