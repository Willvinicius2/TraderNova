"""L23 - Ehlers MAMA/FAMA (MESA Adaptive Moving Average, S&C set/2001)."""
import math

import numpy as np

import indicators as ind

META = {
    "id": "L23_mama_fama",
    "name": "Ehlers MAMA/FAMA: cruzamento MAMA x FAMA",
    "family": "tendencia",
    "round": 8,
    "origin": "FILA.md (autor)",
    "sources": [
        "John F. Ehlers, 'MESA Adaptive Moving Averages', Technical Analysis of Stocks & Commodities, set/2001 (código EasyLanguage do autor)",
        "https://prorealcode.com/prorealtime-indicators/john-ehlers-mama-the-mother-of-adaptive-moving-average",
        "https://www.luxalgo.com/library/indicator/qF12FAVo-mama-ehlers-mesa-adaptive-moving-average/",
        "/home/user/labdata/pine/deepentropy_lightweight-charts-indicators/src/community/mama-fama.ts (porte do Pine 'MAMA - FAMA (Ehlers) [KN]')",
    ],
    "rule": ("Preço (máx+mín)/2. Transformada de Hilbert de Ehlers (Smooth 4-3-2-1, Detrender, I1/Q1, jI/jQ, discriminador homódino) dá o período "
             "do ciclo e a fase = atan(Q1/I1); DeltaPhase = max(fase[1]-fase, 1); alpha = max(fast/DeltaPhase, slow) (máx. fast). "
             "MAMA = alpha*preço + (1-alpha)*MAMA[1]; FAMA = 0,5*alpha*MAMA + (1-0,5*alpha)*FAMA[1]. Ehlers: o cruzamento MAMA/FAMA é o sistema. "
             "Compra quando MAMA cruza acima da FAMA; vende (both) quando cruza abaixo; sai/inverte no cruzamento oposto. "
             "Sem stop no original: stop de proteção k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"fast": [0.3, 0.5, 0.7], "slow": [0.02, 0.05, 0.1], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}

_CACHE = {}


def _hilbert(x):
    v = 0.0962, 0.5769
    return lambda a, i, adj: (v[0] * a[i] + v[1] * a[i - 2] - v[1] * a[i - 4] - v[0] * a[i - 6]) * adj


def delta_phase(price):
    """Fase de Ehlers (EasyLanguage original). Só depende do preço, então é guardada em cache."""
    key = (len(price), float(price[0]), float(price[-1]), float(np.nansum(price[::97])))
    if key in _CACHE:
        return _CACHE[key]
    N = len(price)
    sm = np.zeros(N); det = np.zeros(N); i1 = np.zeros(N); q1 = np.zeros(N)
    i2 = np.zeros(N); q2 = np.zeros(N); re = np.zeros(N); im = np.zeros(N)
    per = np.zeros(N); ph = np.zeros(N); dph = np.full(N, np.nan)
    h = _hilbert(None)
    for i in range(N):
        if i < 6:
            per[i] = 6.0 if i == 0 else per[i - 1]
            continue
        sm[i] = (4 * price[i] + 3 * price[i - 1] + 2 * price[i - 2] + price[i - 3]) / 10.0
        adj = 0.075 * per[i - 1] + 0.54
        det[i] = h(sm, i, adj)
        q1[i] = h(det, i, adj)
        i1[i] = det[i - 3]
        ji = h(i1, i, adj)
        jq = h(q1, i, adj)
        i2[i] = 0.2 * (i1[i] - jq) + 0.8 * i2[i - 1]
        q2[i] = 0.2 * (q1[i] + ji) + 0.8 * q2[i - 1]
        re[i] = 0.2 * (i2[i] * i2[i - 1] + q2[i] * q2[i - 1]) + 0.8 * re[i - 1]
        im[i] = 0.2 * (i2[i] * q2[i - 1] - q2[i] * i2[i - 1]) + 0.8 * im[i - 1]
        p = per[i - 1]
        if im[i] != 0 and re[i] != 0:
            p = 360.0 / math.degrees(math.atan(im[i] / re[i]))
        p = min(p, 1.5 * per[i - 1]); p = max(p, 0.67 * per[i - 1])
        p = min(max(p, 6.0), 50.0)
        per[i] = 0.2 * p + 0.8 * per[i - 1]
        ph[i] = math.degrees(math.atan(q1[i] / i1[i])) if i1[i] != 0 else ph[i - 1]
        dph[i] = max(ph[i - 1] - ph[i], 1.0)
    dph[:50] = np.nan  # aquecimento do discriminador
    _CACHE.clear()
    _CACHE[key] = dph
    return dph


def mama_fama(price, fast, slow):
    dph = delta_phase(price)
    N = len(price)
    m = np.full(N, np.nan); f = np.full(N, np.nan)
    pm = pf = np.nan
    for i in range(N):
        if np.isnan(dph[i]):
            continue
        a = min(max(fast / dph[i], slow), fast)
        if np.isnan(pm):
            pm = pf = price[i]
        pm = a * price[i] + (1 - a) * pm
        pf = 0.5 * a * pm + (1 - 0.5 * a) * pf
        m[i], f[i] = pm, pf
    return m, f


def signals(df, p):
    price = (df.high.values + df.low.values) / 2.0
    m, f = mama_fama(price, p["fast"], p["slow"])
    up = ind.cross_above(m, f)
    dn = ind.cross_below(m, f)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": dn, "exit_short": up}
