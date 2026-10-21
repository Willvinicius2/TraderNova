"""Waddah Attar Explosion (LazyBear, TradingView comunidade)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV25_waddah_attar",
    "name": "Waddah Attar Explosion (LazyBear)",
    "family": "tendencia",
    "round": 3,
    "origin": "TradingView comunidade (LazyBear)",
    "sources": [
        "https://www.tradingview.com/script/iu3kKWDI-Waddah-Attar-Explosion-LazyBear/",
        "https://www.mql5.com/en/market/product/188997",
    ],
    "sourceNote": "TradingView inacessível pelo WebFetch; regra de entrada/saída das notas do autor obtida por WebSearch; Pine de LazyBear reproduzido pela definição conhecida (porte do indicador MT4 de Waddah Attar).",
    "rule": "Pine de LazyBear: t1 = (MACD(fech) - MACD(fech[1]))*sensibilidade, MACD = EMA20-EMA40; explosão e1 = largura das Bandas de Bollinger(20, 2); "
            "zona morta = RMA(TR,100)*dz (padrão 3,7). Barra verde = t1>0, vermelha = t1<0 (valor |t1|). Notas do autor: compra quando a barra verde fica acima da linha de explosão e acima da zona morta "
            "(entra na primeira barra em que isso acontece); sai quando a barra cai abaixo da linha de explosão. Venda simétrica com barra vermelha. Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"sens": [75, 150, 300], "dz": [2.0, 3.7], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    c = df.close.values
    macd = ind.ema(c, 20) - ind.ema(c, 40)
    t1 = (macd - ind.prev(macd)) * p["sens"]
    e1 = 2 * 2.0 * ind.stdev(c, 20)  # (sma+2sd) - (sma-2sd); Pine stdev é populacional
    h, l = df.high.values, df.low.values
    pc = ind.prev(c)
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    dead = pd.Series(tr).ewm(alpha=1 / 100, adjust=False, min_periods=100).mean().to_numpy() * p["dz"]
    up = np.where(t1 >= 0, t1, 0.0)
    dn = np.where(t1 < 0, -t1, 0.0)
    with np.errstate(invalid="ignore"):
        lon = (up > e1) & (up > dead)
        sho = (dn > e1) & (dn > dead)
        exl = up < e1
        exs = dn < e1
    lg = lon & ~np.r_[False, lon[:-1]]
    sh = sho & ~np.r_[False, sho[:-1]]
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
