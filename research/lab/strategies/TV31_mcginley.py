"""McGinley Dynamic: virada da inclinação."""
import numpy as np

import indicators as ind

META = {
    "id": "TV31_mcginley",
    "name": "McGinley Dynamic: virada da inclinação",
    "family": "tendencia",
    "round": 3,
    "origin": "TradingView comunidade (everget) / embutida",
    "sources": [
        "https://www.tradingview.com/script/9l0vfJdy-McGinley-Dynamic/",
        "https://github.com/everget/tradingview-pinescript-indicators/blob/master/movings/mcginley_dynamic.pine",
        "https://www.investopedia.com/terms/m/mcginley-dynamic.asp",
    ],
    "rule": ("McGinley Dynamic (Pine do everget): MD = MD[1] + (C - MD[1]) / (K * N * (C/MD[1])^4), semente = fechamento "
             "(K=1 equivale à versão embutida do TradingView; everget usa K=0,6). Compra quando a inclinação da linha vira de "
             "caindo para subindo (MD>MD[1] depois de MD[1]<=MD[2]); vende na virada para baixo; sai/inverte na virada oposta. "
             "Não é cruzamento de duas médias nem de preço com média. Pine sem stop: stop de proteção k*ATR14. A razão C/MD[1] é "
             "limitada a [0,5; 2] (correção numérica do 'Improved McGinley Dynamic'), sem efeito em condições normais."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"length": [10, 14, 21, 34, 55], "kmd": [0.6, 1.0], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def mcginley(c, n, k):
    md = np.full(len(c), np.nan)
    md[0] = c[0]
    for i in range(1, len(c)):
        r = min(max(c[i] / md[i - 1], 0.5), 2.0)
        md[i] = md[i - 1] + (c[i] - md[i - 1]) / (k * n * r ** 4)
    md[: 3 * n] = np.nan
    return md


def signals(df, p):
    c = df.close.values
    md = mcginley(c, p["length"], p["kmd"])
    d = md - ind.prev(md)
    pd_ = ind.prev(d)
    up = (d > 0) & (pd_ <= 0)
    dn = (d < 0) & (pd_ >= 0)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
