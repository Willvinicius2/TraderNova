"""TASC 2026.01 The Reversion Index (John F. Ehlers), script PineCodersTASC no TradingView."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV45_reversion_index",
    "name": "Reversion Index de Ehlers: Smooth cruza Trigger em zona extrema",
    "family": "reversao",
    "round": 4,
    "origin": "TradingView comunidade (PineCodersTASC; John F. Ehlers, TASC jan/2026)",
    "sources": [
        "https://www.tradingview.com/script/V35NeC45-TASC-2026-01-The-Reversion-Index",
        "https://www.prorealcode.com/topic/reversion-index/",
        "Código Pine traduzido: github.com/deepentropy/lightweight-charts-indicators src/community/tasc-2026-01-the-reversion-index.ts",
    ],
    "sourceNote": "Fórmula do código traduzido. A descrição diz que os sinais vêm do cruzamento Trigger/Smooth para operar reversão em mercado lateral; "
                  "a exigência de zona (Smooth < -nível para compra, > +nível para venda) segue a fila (FILA_TRADINGVIEW.md).",
    "rule": "d = fech - fech[1]; razão = soma(d, L)/soma(|d|, L); Smooth = SuperSmoother(razão, 8); Trigger = SuperSmoother(razão, 4) "
            "(cada um filtra a média de 2 candles). Compra quando o Smooth cruza acima do Trigger com Smooth < -nível; vende quando cruza abaixo com Smooth > +nível. "
            "Sai no cruzamento oposto. Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"L": [10, 14, 20, 30, 40], "lvl": [0.0, 0.2, 0.4], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def ss8(x, period):
    a = np.pi * np.sqrt(2.0) / period
    b = np.exp(-a)
    c2 = -b * b
    c1 = np.cos(a) * 2.0 * b
    c0 = 1.0 - c1 - c2
    out = np.zeros(len(x))
    for i in range(len(x)):
        p = x[i - 1] if i > 0 else x[i]
        sma2 = (x[i] + p) / 2
        out[i] = c0 * sma2 + c1 * (out[i - 1] if i > 0 else 0.0) + c2 * (out[i - 2] if i > 1 else 0.0)
    return out


def rev_index(close, L):
    d = pd.Series(close).diff()
    ds = d.rolling(L).sum().to_numpy()
    ads = d.abs().rolling(L).sum().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.where(np.isfinite(ads) & (np.abs(ads) > 1e-10), ds / ads, 0.0)
    sm, tr = ss8(r, 8), ss8(r, 4)
    sm[: L + 40] = np.nan
    tr[: L + 40] = np.nan
    return sm, tr


def signals(df, p):
    sm, tr = rev_index(df.close.values, p["L"])
    up = ind.cross_above(sm, tr)
    dn = ind.cross_below(sm, tr)
    with np.errstate(invalid="ignore"):
        lg = up & (sm < -p["lvl"])
        sh = dn & (sm > p["lvl"])
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
