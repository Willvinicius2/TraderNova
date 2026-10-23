"""Random Walk Index (Michael Poulos, TASC 1991), código Pine de everget."""
import numpy as np

import indicators as ind

META = {
    "id": "TV73_rwi",
    "name": "Random Walk Index (Poulos): cruzamento RWIhigh/RWIlow acima do limiar",
    "family": "tendencia",
    "round": 6,
    "origin": "TradingView comunidade (everget)",
    "sources": [
        "github.com/everget/tradingview-pinescript-indicators oscillators/random_walk_index.pine (GPL-3.0)",
        "https://tradingsim.com/blog/random-walk-index/",
        "https://www.tradingview.com/script/I271vJqF-Indicators-Chartmill-Value-Indicator-Random-Walk-Index",
    ],
    "sourceNote": "Pine de everget: RWIhigh = (H - L[n])/(ATR(n)*sqrt(n)), RWIlow = (H[n] - L)/(ATR(n)*sqrt(n)). Poulos: RWI acima de 1 "
                  "indica tendência que não é passeio aleatório. Indicador sem regra de saída nem stop: sai no cruzamento oposto, stop k*ATR14.",
    "rule": "Compra quando RWIhigh(n) cruza acima de RWIlow(n) com RWIhigh > thr; vende (both) quando RWIlow cruza acima de RWIhigh com "
            "RWIlow > thr. Sai/inverte no cruzamento oposto das linhas. Stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [10, 14, 20, 30], "thr": [0.8, 1.0, 1.2], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    h, l = df.high.values, df.low.values
    n = p["n"]
    den = ind.atr(df, n) * np.sqrt(n)
    with np.errstate(invalid="ignore", divide="ignore"):
        rh = (h - ind.prev(l, n)) / den
        rl = (ind.prev(h, n) - l) / den
        xu = ind.cross_above(rh, rl)
        xd = ind.cross_above(rl, rh)
        lg = xu & (rh > p["thr"])
        sh = xd & (rl > p["thr"])
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": xd, "exit_short": xu}
