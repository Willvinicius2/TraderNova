"""Gaussian Channel (DonovanWall) com a regra de estratégia popular: filtro verde + fechamento acima da banda alta."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV30_gaussian_channel",
    "name": "Gaussian Channel (DonovanWall): rompimento da banda com filtro subindo",
    "family": "tendencia",
    "round": 3,
    "origin": "TradingView comunidade (DonovanWall)",
    "sources": [
        "https://www.tradingview.com/script/WpVY7GKW-Gaussian-Channel-DW/",
        "https://www.tradingview.com/script/erJi1tWf-Gaussian-Channel-Strategy/",
        "https://www.mql5.com/en/job/239460",
    ],
    "rule": ("Indicador de DonovanWall (padrões: fonte hlc3, polos N=4, período 144, mult 1,414, sem modos lag/fast): "
             "beta=(1-cos(2pi/per))/(1,414^(2/N)-1), alpha=-beta+sqrt(beta²+2beta); filtro gaussiano de N polos = N EMAs em "
             "cascata com esse alpha (equivalente exato à recursão f_filt9x); bandas = filtro ± filtro(TR)*mult. Regra das "
             "estratégias públicas baseadas nele (ex.: 'Gaussian Channel Strategy'): compra quando o filtro sobe (verde) e o "
             "fechamento está acima da banda alta; sai quando o fechamento volta abaixo da banda alta (ou o filtro fica vermelho). "
             "Venda no espelho com a banda baixa (opcional). Stop inicial = distância até a banda oposta (a estratégia pública usa "
             "a banda baixa como stop), com mínimo de 1 ATR14. TradingView inacessível ao WebFetch: fórmulas conferidas nos "
             "resumos de busca e no port MQL5."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"poles": [2, 4, 6], "per": [72, 144, 216, 288], "mult": [1.0, 1.414, 2.0], "side": ["long", "both"]},
}


def gauss(x, alpha, poles):
    y = pd.Series(x)
    for _ in range(poles):
        y = y.ewm(alpha=alpha, adjust=False).mean()
    return y.to_numpy(copy=True)


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    src = (h + l + c) / 3.0
    pc = ind.prev(c)
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    N, per = p["poles"], p["per"]
    beta = (1 - np.cos(2 * np.pi / per)) / (1.414 ** (2.0 / N) - 1)
    alpha = -beta + np.sqrt(beta * beta + 2 * beta)
    f = gauss(src, alpha, N)
    ftr = gauss(tr, alpha, N)
    warm = 3 * per
    f[:warm] = np.nan
    hb = f + ftr * p["mult"]
    lb = f - ftr * p["mult"]
    pf = ind.prev(f)
    green = f > pf
    red = f < pf
    longc = green & (c > hb)
    shortc = red & (c < lb)
    a = ind.atr(df, 14)
    stop = np.where(longc, np.maximum(c - lb, a), np.where(shortc, np.maximum(hb - c, a), a))
    entry = np.where(longc, 1, np.where(shortc, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    exit_long = (c < hb) | red
    exit_short = (c > lb) | green
    return {"entry": entry, "stop": stop, "exit_long": exit_long, "exit_short": exit_short}
