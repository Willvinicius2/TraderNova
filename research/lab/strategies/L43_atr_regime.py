"""L43 - Regime de volatilidade (percentil do ATR relativo) escolhendo entre rompimento e reversão.

Diferença do L36 (Hurst) e do L09/TTM/L12: o regime é o percentil do ATR14/fechamento dentro dos últimos L candles.
Expansão -> módulo de rompimento; compressão -> módulo de reversão (mapeamento do LuxAlgo, "Volatility Regime
Switches"); estresse (percentil extremo) opcionalmente fica de fora.
"""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L43_atr_regime",
    "name": "Regime de volatilidade (ATR percentil): rompimento x reversão",
    "family": "regime",
    "round": 9,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://www.luxalgo.com/library/concept/volatility-regime-switches/ (seguir tendência precisa de expansão de volatilidade; reversão se apoia em compressão; ficar de fora no estresse; regime por percentil móvel do ATR)",
        "https://www.luxalgo.com/library/concept/volatility-percentile-rank/ (percentil da volatilidade na janela passada)",
        "Rompimento de Donchian (Turtle) e RSI(2) de Connors como módulos clássicos, sem ajuste ao resultado",
    ],
    "rule": ("v = ATR14/fechamento; pct = fração dos últimos L valores de v (até o candle atual) menores ou iguais ao atual. "
             "Expansão (pct >= hi, e pct < stress se stress<1): compra quando o fechamento passa a maior máxima dos N candles "
             "anteriores, vende quando passa abaixo da menor mínima; sai no rompimento contrário de N/2 candles. "
             "Compressão (pct <= lo): RSI(2) < 10 compra, > 90 vende; sai quando o fechamento cruza a SMA(5) (acima na "
             "compra, abaixo na venda) enquanto o regime ainda é compressão; a saída do rompimento contrário de N/2 vale para qualquer posição. Entre lo e hi não abre nada. Stop k*ATR14. side=long só compra."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"L": [250, 500], "lo": [0.3, 0.5], "hi": [0.5, 0.7], "N": [20, 55], "k": [2.0, 3.0],
             "side": ["long", "both"], "stress": [0.95, 1.0]},
}


def pct_rank(x, L):
    s = pd.Series(x)
    return s.rolling(L, min_periods=L).apply(lambda w: (w <= w[-1]).mean(), raw=True).to_numpy()


_CACHE = {}


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    a = ind.atr(df, 14)
    key = (len(c), float(c[0]), float(c[-1]), p["L"])
    if key not in _CACHE:
        _CACHE[key] = pct_rank(a / c, p["L"])
    pr = _CACHE[key]
    N = p["N"]
    hh, ll = ind.prev(ind.highest(h, N)), ind.prev(ind.lowest(l, N))
    hx, lx = ind.prev(ind.highest(h, N // 2)), ind.prev(ind.lowest(l, N // 2))
    exp_ = (pr >= p["hi"]) & ((p["stress"] >= 1.0) | (pr < p["stress"]))
    comp = pr <= p["lo"]
    bl, bs = exp_ & (c > hh), exp_ & (c < ll)
    r2 = ind.rsi(c, 2)
    rl, rs = comp & (r2 < 10), comp & (r2 > 90)
    entry = np.where(bl | rl, 1, np.where(bs | rs, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    # saídas: a de rompimento (N/2) vale sempre; a da reversão (SMA5) só quando o regime atual é compressão
    m5 = ind.sma(c, 5)
    exit_long = (c < lx) | (comp & (c > m5))
    exit_short = (c > hx) | (comp & (c < m5))
    return {"entry": entry, "stop": p["k"] * a, "exit_long": exit_long, "exit_short": exit_short}
