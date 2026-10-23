"""L48 - CCI(20) com divergência confirmada (Lambert / StockSharp 0068 CCI Divergence)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L48_cci_divergence",
    "name": "CCI 20 com divergência confirmada (sem repintura)",
    "family": "reversao",
    "round": 9,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://stocksharp.com/en/store/strategies.0068_cci_divergence",
        "https://doc.stocksharp.com/en/api-examples/0068_CCI_Divergence",
        "https://en.wikipedia.org/wiki/Commodity_channel_index",
        "https://www.barchart.com/education/technical-indicators/commodity_channel_index",
    ],
    "rule": ("CCI(20) de Lambert sobre hlc3. Divergência de alta (StockSharp 0068): dois fundos de preço consecutivos (pivô de "
             "mínima com r candles de cada lado, só conhecido r candles depois, sem repintura), mínima do 2º < do 1º, mínimo "
             "do CCI em volta do 2º > em volta do 1º, CCI < -100 no 1º fundo, fundos a no máximo 'gap' candles. Compra na "
             "abertura seguinte à confirmação do 2º fundo. Venda espelhada (topos, CCI > +100). Saída quando o CCI cruza o "
             "zero (fonte); sinal oposto inverte. Stop k*ATR14 (fonte usa 2% fixo; aqui ATR para servir a vários tempos). "
             "Difere do TV23 (rompimento de ±100 sem divergência)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"r": [2, 3, 5], "gap": [20, 40, 80], "k": [1.5, 2.0, 3.0], "side": ["long", "both"]},
}


def cci(df, n=20):
    tp = ((df.high + df.low + df.close) / 3).values.astype(float)
    out = np.full(len(tp), np.nan)
    if len(tp) < n:
        return out
    w = np.lib.stride_tricks.sliding_window_view(tp, n)
    ma = w.mean(axis=1)
    md = np.abs(w - ma[:, None]).mean(axis=1)
    out[n - 1:] = (tp[n - 1:] - ma) / (0.015 * md)
    return out


def _div(price, osc, r, gap):
    """Divergência de alta (para baixa, passe -price e -osc). Sinal no candle em que o 2º pivô é confirmado."""
    n = len(price)
    out = np.zeros(n, dtype=bool)
    last = None
    for i in range(2 * r, n):
        j = i - r
        win = price[j - r:i + 1]
        if np.isnan(win).any() or np.argmin(win) != r:
            continue
        ow = osc[j - r:i + 1]
        if np.isnan(ow).all():
            continue
        om = np.nanmin(ow)
        if last is not None:
            pj, px, pom = last
            if j - pj <= gap and price[j] < px and om > pom and pom < -100:
                out[i] = True
        last = (j, price[j], om)
    return out


_cache = {}


def signals(df, p):
    key = (id(df), len(df))
    if key not in _cache:
        _cache[key] = cci(df, 20)
    x = _cache[key]
    lo, hi = df.low.values.astype(float), df.high.values.astype(float)
    buy = _div(lo, x, p["r"], p["gap"])
    sell = _div(-hi, -x, p["r"], p["gap"])
    z = np.zeros(len(x))
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14),
            "exit_long": ind.cross_below(x, z), "exit_short": ind.cross_above(x, z)}
