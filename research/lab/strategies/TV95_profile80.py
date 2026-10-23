"""TV95 - Market Profile, regra dos 80% (James Dalton), com a value area do perfil de LonesomeTheBlue."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV95_profile80",
    "name": "Regra dos 80% do Market Profile: volta à value area do dia anterior",
    "family": "reversao",
    "round": 7,
    "origin": "TradingView comunidade (LonesomeTheBlue, 'Market Profile'; regra dos 80% de James Dalton, Mind Over Markets, 1990)",
    "sources": [
        "https://github.com/deepentropy/lightweight-charts-indicators/blob/main/src/community/market-profile.ts",
        "https://www.metrotrade.com/what-is-the-80-rule-in-futures-trading/",
        "https://www.marketcalls.in/market-profile/market-profile-how-to-play-80-percentage-rule.html",
        "https://www.luxalgo.com/library/concept/80-percent-rule/",
    ],
    "sourceNote": "Perfil do port fiel (MPL 2.0) do Pine 'Market Profile' de LonesomeTheBlue: o range do dia UTC fechado é cortado em 20 canais, "
                  "cada canal conta os candles do dia que o tocam (o 1º candle do dia não conta, como no original), POC = canal mais alto com a "
                  "maior contagem e a value area cresce do POC para o vizinho maior até ter 'va'% das contagens. Regra dos 80% (Dalton; MetroTrade, "
                  "Marketcalls): se o dia abre fora da value area do dia anterior e volta para dentro dela por 2 períodos seguidos (2 TPOs de 30 min; "
                  "aqui 'conf' candles H1 fechando dentro), o alvo é o outro extremo da value area; stop logo fora do extremo de reentrada. "
                  "Usa só o perfil do dia anterior já fechado. Uma operação por dia; o sinal vale só no próprio dia.",
    "rule": "Value area (VAL, VAH) do dia UTC anterior pelo perfil de 20 canais. Se a abertura do dia > VAH e depois 'conf' candles H1 seguidos fecham "
            "dentro de [VAL, VAH], vende na abertura seguinte com alvo VAL e stop VAH + b*ATR14; se abre < VAL, espelho (compra, alvo VAH, stop VAL - b*ATR). "
            "Saída: saida='dia' fecha no fim do dia UTC; '24h' segura até 24 candles. Uma entrada por dia.",
    "timeframes": ["H1"],
    "grid": {"va": [65, 70, 75], "conf": [1, 2, 3], "b": [0.25, 0.5, 1.0], "saida": ["dia", "24h"], "side": ["long", "both"]},
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
    prev_val = np.r_[np.nan, val_d[:-1]][codes]
    prev_vah = np.r_[np.nan, vah_d[:-1]][codes]
    # só vale se o dia anterior for o dia de calendário imediatamente anterior
    gap = np.r_[False, (days[1:] - days[:-1]) == pd.Timedelta(days=1)][codes]
    prev_val[~gap] = np.nan
    prev_vah[~gap] = np.nan
    return prev_val, prev_vah, codes, starts


def signals(df, p):
    key = (len(df), str(df.index[0]), str(df.index[-1]), p["va"])
    if key not in _CACHE:
        _CACHE[key] = value_areas(df, p["va"])
    val, vah, codes, starts = _CACHE[key]
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
    for i in np.flatnonzero(trig & (above | below)):
        d = codes[i]
        if d in used or hour[i] == 23:
            continue
        used.add(d)
        if above[i] and p["side"] == "both":
            entry[i] = -1
            stop[i] = vah[i] + p["b"] * a[i] - c[i]
            tgt[i] = c[i] - val[i]
        elif below[i]:
            entry[i] = 1
            stop[i] = c[i] - (val[i] - p["b"] * a[i])
            tgt[i] = vah[i] - c[i]
    ok = (stop > 0) & (tgt > 0)
    entry = np.where(ok, entry, 0)
    sig = {"entry": entry, "stop": np.where(ok, stop, np.nan), "target": np.where(ok, tgt, np.nan)}
    if p["saida"] == "dia":
        last = hour == 23
        sig["exit_long"] = last
        sig["exit_short"] = last
        sig["max_hold"] = 24
    else:
        sig["max_hold"] = 24
    return sig
