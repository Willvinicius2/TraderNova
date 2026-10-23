"""Renko Candles Overlay (LonesomeTheBlue): tijolos Renko de tamanho ATR sobre candles fechados; opera a virada."""
import math

import numpy as np

import indicators as ind

META = {
    "id": "TV91_renko_atr",
    "name": "Renko ATR overlay: virada de tijolo (LonesomeTheBlue)",
    "family": "tendencia",
    "round": 7,
    "origin": "TradingView comunidade (LonesomeTheBlue)",
    "sources": [
        "https://www.tradingview.com/script/rZs7YdMI-Renko-Candles-Overlay",
        "https://www.luxalgo.com/library/indicator/rZs7YdMI-renko-candles-overlay",
        "https://github.com/deepentropy/lightweight-charts-indicators (src/community/renko-candles-overlay.ts)",
    ],
    "rule": ("Lógica do overlay: tamanho do tijolo = ATR(atrlen) arredondado a número 'redondo' (2 dígitos significativos) e "
             "dividido por div (ATR, ATR/2, ATR/4); só muda quando entram tijolos novos. Usa o fechamento de cada candle já fechado "
             "(sem repintura): com tendência de alta, cada tamanho acima do último tijolo soma tijolos; 2 tamanhos contra viram a "
             "tendência. Compra quando a tendência Renko vira para alta (nbrick=1) ou quando, depois da virada, o 2º tijolo de alta "
             "se forma (nbrick=2); venda (side=both) no espelho. Sai/inverte na virada oposta. Indicador sem stop: stop k × ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"div": [4, 2, 1], "atrlen": [14, 50], "nbrick": [1, 2], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def nice(x):
    if math.isnan(x):
        return x
    if x < 1:
        return max(round(x * 100) / 100, 0.01)
    pw = 10 ** max(len(str(int(x))) - 2, 1) if x >= 10 else 1
    return max(round(x / pw) * pw, 0.01)


def renko(df, atrlen, div):
    o, c = df.open.values, df.close.values
    n = len(c)
    a = ind.atr(df, atrlen)
    trend = np.zeros(n, int)
    cnt = np.zeros(n, int)  # tijolos seguidos na direção atual
    boxs = math.nan
    last = math.nan
    tr, k = 0, 0
    for i in range(n):
        bs = nice(a[i]) / div if not math.isnan(a[i]) else math.nan
        if math.isnan(boxs):
            if math.isnan(bs):
                continue
            boxs = bs
            last = math.floor(o[i] / boxs) * boxs
        cp = c[i]
        num = int(abs(last - cp) // boxs)
        old = last
        if num > 0:
            if tr == 0:
                if num >= 2:
                    tr = 1 if cp > last else -1
                    last = last + tr * num * boxs
                    k = num
            elif (cp - last) * tr > 0:
                last = last + tr * num * boxs
                k += num
            elif num >= 2:
                tr = -tr
                last = last + tr * num * boxs  # (num-1) tijolos a partir de last + tr*boxs
                k = num - 1
            if last != old and not math.isnan(bs):
                boxs = bs
        trend[i], cnt[i] = tr, k
    return trend, cnt


def signals(df, p):
    tr, cnt = renko(df, p["atrlen"], p["div"])
    ptr, pcnt = ind.prev(tr.astype(float)), ind.prev(cnt.astype(float))
    flip_up = (tr == 1) & (ptr == -1)
    flip_dn = (tr == -1) & (ptr == 1)
    if p["nbrick"] == 1:
        up, dn = flip_up, flip_dn
    else:
        up = (tr == 1) & (cnt >= 2) & ((ptr == -1) | ((ptr == 1) & (pcnt < 2)))
        dn = (tr == -1) & (cnt >= 2) & ((ptr == 1) | ((ptr == -1) & (pcnt < 2)))
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": flip_dn, "exit_short": flip_up}
