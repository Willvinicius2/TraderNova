"""L14 - Alligator de Bill Williams + rompimento de fractal."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L14_alligator_fractal",
    "name": "Alligator + rompimento de fractal (Bill Williams)",
    "family": "padroes",
    "sources": [
        "https://www.metatrader5.com/en/terminal/help/indicators/bw_indicators/alligator",
        "https://nepafx.yolasite.com/fractals.php",
        "https://doc.stocksharp.com/en/api-examples/2077_Bill_Williams",
        "Bill Williams, Trading Chaos (1995) / New Trading Dimensions (1998)",
    ],
    "rule": ("Alligator = SMMA da mediana (A+m)/2: mandíbula 13 deslocada 8, dentes 8 deslocados 5, lábios 5 deslocados 3 "
             "(deslocamento usa só valores passados). Fractal de alta = máxima maior que as 2 máximas de cada lado (confirmado 2 candles depois). "
             "Compra quando o fechamento rompe a máxima do último fractal de alta que está acima dos dentes; venda no espelho com fractal de baixa "
             "abaixo dos dentes. Opcional: exigir Alligator 'acordado' (lábios>dentes>mandíbula). Sai quando fecha do outro lado da linha de saída "
             "(lábios/dentes/mandíbula). Stop k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"align": [False, True], "exit_line": ["lips", "teeth", "jaw"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def smma(x, n):
    return pd.Series(x).ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean().values


def fractal_levels(h, l):
    """Nível do último fractal confirmado (valor em i usa só dados até i)."""
    n = len(h)
    up_lvl = np.full(n, np.nan)
    dn_lvl = np.full(n, np.nan)
    up_idx = np.full(n, -1)
    dn_idx = np.full(n, -1)
    cu = cd = np.nan
    iu = idn = -1
    for i in range(4, n):
        j = i - 2  # candidato confirmado no fechamento de i
        if h[j] > h[j - 1] and h[j] > h[j - 2] and h[j] > h[j + 1] and h[j] > h[j + 2]:
            cu, iu = h[j], j
        if l[j] < l[j - 1] and l[j] < l[j - 2] and l[j] < l[j + 1] and l[j] < l[j + 2]:
            cd, idn = l[j], j
        up_lvl[i], dn_lvl[i], up_idx[i], dn_idx[i] = cu, cd, iu, idn
    return up_lvl, dn_lvl, up_idx, dn_idx


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    med = (h + l) / 2.0
    jaw = ind.prev(smma(med, 13), 8)
    teeth = ind.prev(smma(med, 8), 5)
    lips = ind.prev(smma(med, 5), 3)
    up_lvl, dn_lvl, up_idx, dn_idx = fractal_levels(h, l)
    # dentes no candle do fractal
    tu = np.where(up_idx >= 0, teeth[np.clip(up_idx, 0, None)], np.nan)
    td = np.where(dn_idx >= 0, teeth[np.clip(dn_idx, 0, None)], np.nan)
    long_ok = ind.cross_above(c, up_lvl) & (up_lvl > tu)
    short_ok = ind.cross_below(c, dn_lvl) & (dn_lvl < td)
    if p["align"]:
        long_ok &= (lips > teeth) & (teeth > jaw)
        short_ok &= (lips < teeth) & (teeth < jaw)
    entry = np.where(long_ok, 1, np.where(short_ok, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    line = {"lips": lips, "teeth": teeth, "jaw": jaw}[p["exit_line"]]
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": c < line, "exit_short": c > line}
