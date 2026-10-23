"""TV02 - Consecutive Up/Down Strategy (estratégia embutida do TradingView)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV02_consecutive",
    "name": "Consecutive Up/Down Strategy (TradingView)",
    "family": "tendencia",
    "round": 2,
    "origin": "TradingView embutida",
    "sources": [
        "https://www.tradingview.com/support/solutions/43000599836-consecutive-up-down-strategy/",
        "https://www.tradingview.com/support/folders/43000587406-built-in-strategies/",
    ],
    "rule": ("Pine original: conta fechamentos seguidos maiores que o anterior (ups) e menores (dns). Compra quando ups >= N, "
             "vende quando dns >= N (padrão N=3 nos dois lados). Sempre posicionado; sinal oposto inverte. Entrada a mercado na "
             "abertura seguinte. O Pine não tem stop: usamos stop de proteção k*ATR14; após stop, reentra enquanto a sequência continuar."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [2, 3, 4, 5], "k": [2.0, 3.0, 4.5, 6.0], "side": ["long", "both"]},
}


def run_count(x):
    out = np.zeros(len(x), dtype=int)
    cnt = 0
    for i, v in enumerate(x):
        cnt = cnt + 1 if v else 0
        out[i] = cnt
    return out


def signals(df, p):
    c = df.close.values
    pc = ind.prev(c)
    ups = run_count(c > pc)
    dns = run_count(c < pc)
    up = ups >= p["n"]
    dn = dns >= p["n"]
    entry = np.where(up, 1, np.where(dn, -1, 0))
    exl = None
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
        exl = dn
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": exl}
