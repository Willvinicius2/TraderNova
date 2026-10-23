"""TV67 - Rally Base Drop Signals (LuxAlgo): sequências de fases Rally/Base/Drop."""
import numpy as np

import indicators as ind

META = {
    "id": "TV67_rbd",
    "name": "Rally Base Drop Signals (LuxAlgo): DBR compra, RBD vende",
    "family": "padroes",
    "round": 5,
    "origin": "TradingView comunidade (LuxAlgo)",
    "sources": [
        "https://www.tradingview.com/scripts/rallybasedrop/",
        "https://github.com/deepentropy/lightweight-charts-indicators (src/community/rally-base-drop-signals.ts, port fiel do Pine, commit f8e1b0e)",
    ],
    "rule": ("Pine LuxAlgo: vela verde = fech > abert, vermelha = fech < abert. Rally = vela verde com a anterior verde; Drop = vermelha "
             "com a anterior vermelha; Base = qualquer outra. Guarda as 3 últimas fases distintas (só muda quando a fase atual difere "
             "da última guardada). Sinal no candle em que a sequência passa a ser Drop-Base-Rally (compra) ou Rally-Base-Drop "
             "(venda); com cont=True também Rally-Base-Rally compra e Drop-Base-Drop vende (os 4 sinais do script). Entrada na "
             "abertura seguinte. O indicador não tem stop nem saída: stop de proteção k*ATR14, alvo tr*R (0 = sem alvo) e o sinal "
             "oposto fecha (side=long) ou inverte (side=both)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"cont": [False, True], "k": [1.0, 1.5, 2.0, 3.0], "tr": [0.0, 1.5, 2.0, 3.0], "side": ["long", "both"]},
}


def phases(o, c):
    n = len(c)
    seq = ["", "", ""]
    prev = None
    g1 = r1 = False
    out = {k: np.zeros(n, bool) for k in ("RBD", "RBR", "DBD", "DBR")}
    for i in range(n):
        g, r = c[i] > o[i], c[i] < o[i]
        rally, drop = g and g1, r and r1
        base = not rally and not drop
        g1, r1 = g, r
        ph = "B" if base else ("R" if rally else "D")
        if seq[-1] != ph:
            seq = seq[1:] + [ph]
        s = "".join(seq)
        if s in out and s != prev:
            out[s][i] = True
        prev = s
    return out


def signals(df, p):
    o, c = df.open.values, df.close.values
    ph = phases(o, c)
    buy = ph["DBR"] | (ph["RBR"] if p["cont"] else False)
    sell = ph["RBD"] | (ph["DBD"] if p["cont"] else False)
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "target_r": p["tr"], "exit_long": sell, "exit_short": buy}
