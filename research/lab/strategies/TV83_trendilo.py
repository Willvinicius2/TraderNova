"""Trendilo (dudeowns): ALMA da variação % comparada com a banda RMS."""
import numpy as np

import indicators as ind

META = {
    "id": "TV83_trendilo",
    "name": "Trendilo (dudeowns)",
    "family": "tendencia",
    "round": 6,
    "origin": "TradingView comunidade (dudeowns)",
    "sources": [
        "https://jp.tradingview.com/script/h5kMWewu-Trendilo-OPEN-SOURCE",
        "https://prorealcode.com/prorealtime-indicators/trendilo",
    ],
    "rule": ("pch = (close - close[1]) / close × 100; avpch = ALMA(pch, len, offset 0,85, sigma 6); rms = bmult × raiz(soma(avpch², len)/len). "
             "Estado +1 quando avpch > rms, -1 quando avpch < -rms, 0 entre as bandas. Compra quando o estado vira +1; venda "
             "(side=both) quando vira -1. Saída: exit=neutral sai quando o estado deixa de ser o da posição (volta para dentro da "
             "banda); exit=flip só sai no estado oposto. Indicador sem stop: stop de proteção k × ATR14. Pine original no TradingView "
             "(não abre aqui); fórmula conferida no port ProBuilder da ProRealCode."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"len": [20, 35, 50, 80], "bmult": [0.8, 1.0, 1.2], "exit": ["neutral", "flip"], "k": [2.5], "side": ["long", "both"]},
}


def alma(x, n, offset=0.85, sigma=6.0):
    m = offset * (n - 1)
    s = n / sigma
    w = np.exp(-((np.arange(n) - m) ** 2) / (2 * s * s))
    w /= w.sum()
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1:] = np.lib.stride_tricks.sliding_window_view(x, n) @ w  # w[0] no candle mais antigo
    return out


def signals(df, p):
    c = df.close.values
    pch = np.r_[np.nan, np.diff(c)] / c * 100
    av = alma(pch, p["len"])
    rms = p["bmult"] * np.sqrt(ind.sma(av * av, p["len"]))
    st = np.where(av > rms, 1, np.where(av < -rms, -1, 0))
    ps = np.r_[0, st[:-1]]
    up = (st == 1) & (ps != 1)
    dn = (st == -1) & (ps != -1)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    if p["exit"] == "neutral":
        exl, exs = st != 1, st != -1
    else:
        exl, exs = st == -1, st == 1
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
