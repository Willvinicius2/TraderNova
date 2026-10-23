"""Better Volume Indicator (LazyBear): barra de clímax contra a tendência como sinal de reversão."""
import numpy as np

import indicators as ind

META = {
    "id": "TV100_better_volume",
    "name": "Better Volume (LazyBear): clímax de volume no fim da tendência marca reversão",
    "family": "volume",
    "round": 7,
    "origin": "TradingView comunidade (LazyBear)",
    "sources": [
        "https://github.com/deepentropy/lightweight-charts-indicators/blob/main/src/community/better-volume.ts (port fiel do Pine \"Better Volume Indicator [LazyBear]\" do TradingView)",
        "https://www.luxalgo.com/library/concept/better-volume-classifications.md",
        "https://forum.esignal.com/filedata/fetch?id=246301",
    ],
    "sourceNote": "Classificação das barras portada linha a linha do port DE (inclusive a precedência estranha de v1 do original). "
                  "O indicador não tem regra de operação; a regra de reversão é montada a partir da leitura descrita nas fontes "
                  "(clímax após movimento estendido = exaustão; esperar confirmação).",
    "rule": "Barra 'climax up' (vermelha: alguma das medidas volume×range de compra no máximo de 'length' barras, barra de alta) "
            "com fechamento acima da EMA(trend) marca exaustão da alta: vende. Barra 'climax down' (branca) abaixo da EMA(trend): compra. "
            "confirm=1: só entra se nas 'length' barras seguintes o fechamento romper o extremo oposto da barra de clímax "
            "(mínima para venda, máxima para compra). Sem stop no original: stop k*ATR14, alvo target_r em R, saída por tempo 3*length barras.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"length": [8, 20], "trend": [50, 100, 200], "confirm": [0, 1], "k": [2.0, 3.0],
             "target_r": [1.5, 2.5], "side": ["long", "both"]},
}


def classify(df, length, use2=True):
    o, h, l, c = (df[k].values.astype(float) for k in ("open", "high", "low", "close"))
    vol = df.volume.values.astype(float)
    pc = ind.prev(c)
    rng = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    rng[0] = np.nan
    hh2, ll2 = ind.highest(h, 2), ind.lowest(l, 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        v1 = np.where(c >= o,
                      vol * (rng / ((2 + rng * rng / 10) * rng + (o - c))),
                      vol * (((rng + c - o) / (2 + rng * rng / 10)) * rng + (c - o)))
        v2 = vol - v1
        p = ind.prev
        v3 = v1 + v2
        v4 = v1 * rng
        v5 = (v1 - v2) * rng
        v6 = v2 * rng
        v7 = (v2 - v1) * rng
        nz = ~np.isnan(rng) & (rng != 0)
        v8 = np.where(nz, v1 / rng, 1.0)
        v9 = np.where(nz, (v1 - v2) / rng, 1.0)
        v10 = np.where(nz, v2 / rng, 1.0)
        v11 = np.where(nz, (v2 - v1) / rng, 1.0)
        v12 = np.where(nz, v3 / rng, 1.0)
        r2 = hh2 - ll2
        v13 = v3 + p(v3)
        v14 = (v1 + p(v1)) * r2
        v15 = (v1 + p(v1) - v2 - p(v2)) * r2
        v16 = (v2 + p(v2)) * r2
        v17 = (v2 + p(v2) - v1 - p(v1)) * r2
        two = ~np.isnan(r2) & (r2 != 0)
        v18 = np.where(two, (v1 + p(v1)) / r2, 1.0)
        v19 = np.where(two, (v1 + p(v1) - v2 - p(v2)) / r2, 1.0)
        v20 = np.where(two, (v2 + p(v2)) / r2, 1.0)
        v21 = np.where(two, (v2 + p(v2) - v1 - p(v1)) / r2, 1.0)
    clean = lambda x: np.where(np.isfinite(x), x, np.nan)  # noqa: E731

    def is_hi(x):
        x = clean(x)
        return x == ind.highest(x, length)

    def is_lo(x):
        x = clean(x)
        return x == ind.lowest(x, length)

    up, dn = c > o, o > c
    up1, dn1 = ind.prev(c) > ind.prev(o), ind.prev(o) > ind.prev(c)
    c2, c3 = is_hi(v4) & up, is_hi(v5) & up
    c4, c5 = is_hi(v6) & dn, is_hi(v7) & dn
    c6, c7 = is_lo(v8) & dn, is_lo(v9) & dn
    c8, c9 = is_lo(v10) & up, is_lo(v11) & up
    c12 = is_hi(v14) & up & up1
    c13 = is_hi(v15) & up & dn1
    c14 = is_lo(v16) & dn & dn1
    c15 = is_lo(v17) & dn & dn1
    c16 = is_lo(v18) & dn & dn1
    c17 = is_lo(v19) & up & dn1
    c18 = is_lo(v20) & up & up1
    c19 = is_lo(v21) & up & up1
    cl_up = c2 | c3 | c8 | c9 | c12 | c13 | c18 | c19
    cl_dn = (c4 | c5 | c6 | c7 | c14 | c15 | c16 | c17) & ~cl_up  # a cor vermelha tem prioridade no original
    return cl_up, cl_dn


def signals(df, p):
    L = p["length"]
    h, l, c = df.high.values, df.low.values, df.close.values
    cl_up, cl_dn = classify(df, L)
    e = ind.ema(c, p["trend"])
    with np.errstate(invalid="ignore"):
        sell_set = cl_up & (c > e)   # clímax de compra no alto da tendência de alta
        buy_set = cl_dn & (c < e)    # clímax de venda no fundo da tendência de baixa
    n = len(c)
    entry = np.zeros(n, dtype=np.int8)
    if p["confirm"] == 0:
        entry[buy_set] = 1
        entry[sell_set] = -1
    else:
        lvl_b = lvl_s = np.nan
        tb = ts = -1
        for i in range(n):
            if buy_set[i]:
                lvl_b, tb = h[i], i
            elif tb >= 0 and i - tb <= L and c[i] > lvl_b:
                entry[i] = 1
                tb = -1
            if sell_set[i]:
                lvl_s, ts = l[i], i
            elif ts >= 0 and i - ts <= L and c[i] < lvl_s:
                entry[i] = -1
                ts = -1
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "target_r": p["target_r"], "max_hold": 3 * L}
