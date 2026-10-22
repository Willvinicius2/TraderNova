"""Absolute Strength Index (Zeiierman): retorno do período normalizado entre os percentis de vencedores e perdedores."""
import math

import numpy as np

import indicators as ind

META = {
    "id": "TV82_asi",
    "name": "Absolute Strength Index [ASI] (Zeiierman)",
    "family": "momentum",
    "round": 6,
    "origin": "TradingView comunidade (Zeiierman)",
    "sources": [
        "https://www.tradingview.com/scripts/asi/",
        "github.com/deepentropy/lightweight-charts-indicators src/community/absolute-strength-index.ts (port fiel do Pine, MPL-2.0)",
    ],
    "rule": ("Para cada candle, os L retornos de 1 candle anteriores (close[i]/close[i+1]-1, i=1..L) são ordenados; o retorno no "
             "percentil 85% é o limiar dos vencedores e o do percentil 15% o dos perdedores. ASI = (retorno de L candles - perdedor) "
             "/ (vencedor - perdedor) × 2 - 1; sinal = SMA(ASI, ma). Compra quando o ASI cruza acima do sinal; venda (side=both) "
             "quando cruza abaixo; sai no cruzamento oposto. Indicador sem stop: stop de proteção k × ATR14. Página do TradingView "
             "vista só pelo resumo de busca; fórmula lida no port TS do deepentropy."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"L": [10, 15, 25, 40], "ma": [7, 14, 21], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def asi(c, L, top=0.15, bot=0.15):
    n = len(c)
    r = np.r_[np.nan, c[1:] / c[:-1] - 1]
    out = np.zeros(n)
    if n <= L + 1:
        return out
    win = np.sort(np.lib.stride_tricks.sliding_window_view(r[1:], L), axis=1)  # janela k cobre r[k+1..k+L]
    wi, li = math.ceil(L * (1 - top)) - 1, math.ceil(L * bot) - 1
    tw, tl = win[:, wi], win[:, li]
    b = np.arange(L + 1, n)  # janela termina em b-1 -> índice da janela = b-1-L
    cur = c[b] / c[b - L] - 1
    rngv = tw[b - 1 - L] - tl[b - 1 - L]
    with np.errstate(invalid="ignore", divide="ignore"):
        v = np.where(rngv != 0, (cur - tl[b - 1 - L]) / rngv * 2 - 1, 0.0)
    out[b] = v
    return out


def signals(df, p):
    c = df.close.values
    a = asi(c, p["L"])
    s = ind.sma(a, p["ma"])
    up, dn = ind.cross_above(a, s), ind.cross_below(a, s)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
