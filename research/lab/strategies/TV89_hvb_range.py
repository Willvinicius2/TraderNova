"""Highest Volume Bar Range (tradeswithashish): rompimento da faixa do candle de maior volume."""
import numpy as np

import indicators as ind

META = {
    "id": "TV89_hvb_range",
    "name": "Highest Volume Bar Range (tradeswithashish)",
    "family": "rompimento",
    "round": 7,
    "origin": "TradingView comunidade (tradeswithashish)",
    "sources": [
        "https://www.tradingview.com/script/KJB8dEnc",
        "https://github.com/f13end/tradingview-custom-indicators (strategies/Volume Bar Breakout and Breakdown)",
    ],
    "rule": ("Pine v5: highestvol = maior volume dos últimos 'lookback' candles (inclui o atual); se algum dos candles 1..lookback "
             "atrás tem esse volume, a faixa passa a ser a máxima/mínima desse candle (se o maior é o atual, a faixa anterior fica). "
             "Compra quando o fechamento cruza acima da máxima da faixa com volume > SMA20(volume), volume > volume anterior e "
             "fechamento na metade de cima do candle; venda (side=both) quando cruza abaixo da mínima com volume nas mesmas condições "
             "e fechamento na metade de baixo. Indicador sem saída: sai no sinal oposto (inversão) ou no alvo target_r (0 = sem alvo); "
             "stop de proteção k × ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"lookback": [50, 75, 100, 150], "target_r": [0, 2.0, 3.0], "k": [1.5, 2.5], "side": ["long", "both"]},
}


def hvb_levels(h, l, v, lb):
    n = len(v)
    hv = ind.highest(v, lb)
    hi = np.full(n, np.nan)
    lo = np.full(n, np.nan)
    ch, cl = h[0], l[0]
    if n > lb:
        win = np.lib.stride_tricks.sliding_window_view(v, lb)  # win[s] = v[s..s+lb-1]
    for i in range(n):
        if i >= lb and v[i] > 0:
            w = win[i - lb]  # v[i-lb..i-1]
            m = w == hv[i]
            if m.any():
                j = i - lb + int(np.argmax(m))  # o laço do Pine fica com o mais antigo em empate
                ch, cl = h[j], l[j]
        hi[i], lo[i] = ch, cl
    return hi, lo


def signals(df, p):
    h, l, c, v = df.high.values, df.low.values, df.close.values, df.volume.values
    hi, lo = hvb_levels(h, l, v, p["lookback"])
    vma = ind.sma(v, 20)
    rng = h - l
    with np.errstate(divide="ignore", invalid="ignore"):
        pos = np.where(rng > 0, (c - l) / rng, 0.5)
    volok = (v > vma) & (v > ind.prev(v))
    up = ind.cross_above(c, hi) & volok & (pos > 0.5)
    dn = ind.cross_below(c, lo) & volok & (pos < 0.5)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    out = {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn}
    if p["target_r"]:
        out["target_r"] = p["target_r"]
    return out
