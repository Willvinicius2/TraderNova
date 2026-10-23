"""TV95 refinamento 2 - regra dos 80% com filtro de rotação (r1), stop mais largo e alvo opcional no POC."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV95_profile80_r2",
    "name": "Regra dos 80% do Market Profile: filtro de rotação, stop largo e alvo no POC ou no outro extremo",
    "family": "reversao",
    "round": 7,
    "origin": "TradingView comunidade (LonesomeTheBlue, 'Market Profile'; regra dos 80% de James Dalton, Mind Over Markets, 1990)",
    "refines": "TV95_profile80",
    "refinement": "No r1 (filtro de rotação) o melhor do desenvolvimento ficou na borda b=1,0 ATR do stop, com acerto ~50% e PF ~1,16 sem robustez: "
                  "o stop logo fora da value area é tocado pelo ruído do H1 do BTC, e a travessia inteira da value area no mesmo dia é rara. "
                  "r2 mantém o filtro de eficiência de Kaufman (48h), testa stop b = 1,0/1,5/2,0 ATR e o alvo parcial citado pela MetroTrade "
                  "(POC do dia anterior) contra o alvo clássico (outro extremo). Saída fixa no fim do dia UTC.",
    "sources": [
        "https://github.com/deepentropy/lightweight-charts-indicators/blob/main/src/community/market-profile.ts",
        "https://www.metrotrade.com/what-is-the-80-rule-in-futures-trading/",
        "https://www.marketcalls.in/market-profile/market-profile-how-to-play-80-percentage-rule.html",
    ],
    "rule": "Como TV95_profile80 (value area do dia UTC anterior, abertura fora, 'conf' candles H1 fechando dentro, uma entrada por dia), "
            "só com eficiência de Kaufman de 48 candles <= er; stop b*ATR14 além do extremo de reentrada; alvo alvo='poc' no POC do dia anterior "
            "ou alvo='extremo' no outro extremo da value area; sai no fim do dia UTC.",
    "timeframes": ["H1"],
    "grid": {"va": [70, 75], "conf": [2, 3], "b": [1.0, 1.5, 2.0], "er": [0.25, 0.35], "alvo": ["poc", "extremo"], "side": ["long", "both"]},
}

_CACHE = {}


def value_areas(df, pct):
    """Para cada candle: VAL/VAH do dia UTC anterior (perfil de LonesomeTheBlue)."""
    day = df.index.floor("1D")
    h, l = df.high.values, df.low.values
    days = pd.Index(day.unique())
    codes = days.get_indexer(day)
    val_d = np.full(len(days), np.nan)
    vah_d = np.full(len(days), np.nan)
    poc_d = np.full(len(days), np.nan)
    starts = np.r_[0, np.flatnonzero(np.diff(codes)) + 1]
    ends = np.r_[starts[1:], len(codes)]
    for d, (a, b) in enumerate(zip(starts, ends)):
        hh, ll = h[a:b].max(), l[a:b].min()
        if b - a < 2 or hh <= ll:
            continue
        ch = (hh - ll) / 20
        lows = ll + np.arange(20) * ch
        ups = lows + ch
        bl, bh = l[a + 1 : b], h[a + 1 : b]  # o 1º candle do período não conta
        inc = ((lows[:, None] <= bl[None, :]) & (bl[None, :] <= ups[:, None])) | \
              ((lows[:, None] <= bh[None, :]) & (bh[None, :] <= ups[:, None])) | \
              ((bl[None, :] <= lows[:, None]) & (bh[None, :] >= ups[:, None]))
        cnt = np.r_[0, inc.sum(1), 0].astype(float)  # índices 1..20 como no Pine
        total = cnt[1:21].sum()
        poc = 1
        pv = 0
        for x in range(1, 21):
            if cnt[x] >= pv:
                pv, poc = cnt[x], x
        va, hi_i, lo_i = pv, poc, poc
        for _ in range(20):
            if va >= total * pct / 100:
                break
            up = cnt[hi_i + 1] if hi_i + 1 <= 21 else 0
            dn = cnt[lo_i - 1] if lo_i - 1 >= 0 else 0
            m = max(up, dn)
            if m == 0:
                break
            if up >= dn:
                hi_i += 1
            else:
                lo_i -= 1
            va += m
        val_d[d] = ll + (lo_i - 1) * ch
        vah_d[d] = ll + hi_i * ch
        poc_d[d] = ll + (poc - 0.5) * ch
    prev_val = np.r_[np.nan, val_d[:-1]][codes]
    prev_vah = np.r_[np.nan, vah_d[:-1]][codes]
    prev_poc = np.r_[np.nan, poc_d[:-1]][codes]
    # só vale se o dia anterior for o dia de calendário imediatamente anterior
    gap = np.r_[False, (days[1:] - days[:-1]) == pd.Timedelta(days=1)][codes]
    prev_val[~gap] = np.nan
    prev_vah[~gap] = np.nan
    prev_poc[~gap] = np.nan
    return prev_val, prev_vah, codes, starts, prev_poc


def signals(df, p):
    key = (len(df), str(df.index[0]), str(df.index[-1]), p["va"])
    if key not in _CACHE:
        _CACHE[key] = value_areas(df, p["va"])
    val, vah, codes, starts, poc = _CACHE[key]
    import pandas as _pd
    c0 = df.close.values
    net = np.abs(c0 - ind.prev(c0, 48))
    path = _pd.Series(np.abs(np.r_[np.nan, np.diff(c0)])).rolling(48).sum().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        er_ok = (net / path) <= p["er"]
    o, c = df.open.values, df.close.values
    n = len(c)
    a = ind.atr(df, 14)
    day_open = o[starts][codes]
    above = day_open > vah
    below = day_open < val
    inside = (c >= val) & (c <= vah)
    run = np.zeros(n, dtype=int)
    for i in range(n):
        if inside[i]:
            run[i] = run[i - 1] + 1 if i > 0 and codes[i - 1] == codes[i] else 1
    trig = run == p["conf"]
    entry = np.zeros(n, dtype=int)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    used = set()
    hour = df.index.hour
    for i in np.flatnonzero(trig & (above | below) & er_ok):
        d = codes[i]
        if d in used or hour[i] == 23:
            continue
        used.add(d)
        if above[i] and p["side"] == "both":
            entry[i] = -1
            stop[i] = vah[i] + p["b"] * a[i] - c[i]
            tgt[i] = c[i] - (poc[i] if p["alvo"] == "poc" else val[i])
        elif below[i]:
            entry[i] = 1
            stop[i] = c[i] - (val[i] - p["b"] * a[i])
            tgt[i] = (poc[i] if p["alvo"] == "poc" else vah[i]) - c[i]
    ok = (stop > 0) & (tgt > 0)
    entry = np.where(ok, entry, 0)
    sig = {"entry": entry, "stop": np.where(ok, stop, np.nan), "target": np.where(ok, tgt, np.nan)}
    if True:  # saída fixa no fim do dia UTC
        last = hour == 23
        sig["exit_long"] = last
        sig["exit_short"] = last
        sig["max_hold"] = 24
    else:
        sig["max_hold"] = 24
    return sig
