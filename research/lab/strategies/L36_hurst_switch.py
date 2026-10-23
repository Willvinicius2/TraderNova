"""L36 - Expoente de Hurst (R/S, janela deslizante só com passado) como interruptor tendência/reversão."""
import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as swv

import indicators as ind

META = {
    "id": "L36_hurst_switch",
    "name": "Hurst exponent como interruptor tendência/reversão",
    "family": "regime",
    "round": 8,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://www.mql5.com/en/code/76439 (HurstExponentRegimeSwitch: R/S em 200 candles, bloco mínimo 8, 6 dobras, EMA 5, tendência >= 0,55, reversão <= 0,45)",
        "https://www.luxalgo.com/library/concept/hurst-exponent/ (H > 0,5 favorece seguir tendência, H < 0,5 favorece reversão, perto de 0,5 ficar de fora)",
        "https://backtrader.readthedocs.io/en/latest/_modules/backtrader/indicators/hurst.html",
        "Hurst (1951); Mandelbrot & Wallis (1969), análise R/S; Anis & Lloyd (1976) sobre o viés do R/S em amostras curtas",
    ],
    "rule": ("Hurst por R/S clássico (como o indicador mql5): retornos log dos últimos W candles (só passado, até o fechamento de i), "
             "blocos de 8, 16, 32... (até W/2), média de R/S dos blocos não sobrepostos que terminam em i, H = inclinação de "
             "log(R/S) contra log(tamanho), suavizado por EMA 5. Correção de viés: o R/S em janela curta dá ~0,57 num passeio "
             "aleatório, então subtraímos a mediana do mesmo estimador em passeio aleatório gaussiano simulado (semente fixa, sem "
             "usar o BTC) e somamos 0,5. Regime: H >= 0,5+band = tendência; H <= 0,5-band = reversão; no meio não abre nada "
             "(band=0,05 é o 0,55/0,45 publicado). Regras de cada regime (clássicas, não ajustadas ao resultado): tendência = "
             "rompimento de Donchian (fechamento acima da máxima de N candles anteriores compra, abaixo da mínima vende), saída no "
             "rompimento contrário de N/2 candles (exceto se o regime virou reversão); reversão = z-score do fechamento contra a "
             "SMA(N) <= -2 compra, >= +2 vende, alvo na SMA. Stop k*ATR14 nos dois regimes. side=long só compra."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"W": [128, 256, 512], "band": [0.03, 0.05, 0.08], "N": [20, 55], "k": [2.0, 3.0], "side": ["long", "both"]},
}

_CACHE = {}


def _rs_chunk(r, s):
    out = np.full(len(r), np.nan)
    w = swv(r, s)
    m = w.mean(1, keepdims=True)
    z = np.cumsum(w - m, 1)
    R = z.max(1) - z.min(1)
    S = w.std(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        out[s - 1:] = np.where(S > 0, R / S, np.nan)
    return out


def _hurst_raw(r, W, minc=8, steps=6):
    sizes = [minc * 2 ** k for k in range(steps) if minc * 2 ** k <= W // 2]
    n = len(r)
    X, Y = [], []
    for s in sizes:
        rs = _rs_chunk(r, s)
        k = W // s
        acc = rs.copy()
        for j in range(1, k):
            acc = acc + np.r_[np.full(j * s, np.nan), rs[: n - j * s]]
        X.append(np.log(s))
        Y.append(np.log(acc / k))
    X = np.array(X)
    Y = np.vstack(Y)
    Xc = X - X.mean()
    h = (Xc[:, None] * (Y - Y.mean(0))).sum(0) / (Xc ** 2).sum()
    h[: W + 1] = np.nan
    return h


def _rw_bias(W):
    key = ("rw", W)
    if key not in _CACHE:
        rng = np.random.default_rng(12345)
        r = rng.standard_normal(40000)
        _CACHE[key] = float(np.nanmedian(_hurst_raw(r, W)))
    return _CACHE[key]


def hurst(close, W):
    key = (len(close), float(close[0]), float(close[-1]), W)
    if key not in _CACHE:
        r = np.nan_to_num(np.r_[np.nan, np.diff(np.log(close))])
        h = _hurst_raw(r, W) - _rw_bias(W) + 0.5
        _CACHE[key] = pd.Series(h).ewm(span=5, adjust=False, min_periods=5).mean().to_numpy()
    return _CACHE[key]


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    H = hurst(c, p["W"])
    hi, lo = 0.5 + p["band"], 0.5 - p["band"]
    N = p["N"]
    with np.errstate(invalid="ignore"):
        trend = H >= hi
        rev = H <= lo
        dh, dl = ind.prev(ind.highest(h, N)), ind.prev(ind.lowest(l, N))
        xh, xl = ind.prev(ind.highest(h, N // 2)), ind.prev(ind.lowest(l, N // 2))
        m = ind.sma(c, N)
        sd = ind.stdev(c, N)
        z = (c - m) / sd
        tl, ts = trend & (c > dh), trend & (c < dl)
        rl, rsh = rev & (z <= -2.0), rev & (z >= 2.0)
        exl = (c < xl) & ~rev
        exs = (c > xh) & ~rev
    entry = np.where(tl | rl, 1, np.where(ts | rsh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    tgt = np.where(rl | rsh, np.abs(m - c), 0.0)
    return {"entry": entry, "stop": p["k"] * a, "target": tgt, "exit_long": exl, "exit_short": exs}
