"""Full Candle [Alorse]: vela 'cheia' (sombra do lado do fechamento pequena) a favor da EMA."""
import numpy as np

import indicators as ind

META = {
    "id": "TV88_full_candle",
    "name": "Full Candle [Alorse]",
    "family": "padroes",
    "round": 7,
    "origin": "TradingView comunidade (Alorse)",
    "sources": [
        "https://github.com/Alorse/pinescript-strategies/blob/main/strategies/other/Full%20Candle.pine",
        "https://doc.stocksharp.com/en/api-examples/0424_Full_Candle",
    ],
    "rule": ("Pine v5 do Alorse: sombra = máx - fech (vela de alta) ou fech - mín (vela de baixa); sPer = sombra/(máx-mín)×100. "
             "Compra quando fech > abert, fech > EMA(lenA) e sPer <= shadow%; venda (side=both) no espelho (fech < abert, fech < EMA). "
             "Saída da compra: primeira vela de alta que fecha acima do preço de entrada × (1 + exitpct%); da venda: vela de baixa "
             "fechando abaixo do preço de entrada × (1 - exitpct%) (original: 0,2%; a grade também testa 1% e 2% porque 0,2% "
             "é menor que o custo de ida e volta). Sinal oposto inverte (strategy.entry). O Pine tem SL/TP desligados por padrão: "
             "stop de proteção k × ATR14. O preço de entrada é seguido por uma simulação local igual à do motor (entrada na abertura "
             "seguinte, stop tocado zera a posição)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"lenA": [10, 20, 50, 100], "shadow": [5, 10, 20], "exitpct": [0.2, 1.0, 2.0], "k": [2.5], "side": ["long", "both"]},
}


def signals(df, p):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    n = len(c)
    e = ind.ema(c, p["lenA"])
    rng = h - l
    shadow = np.where(c > o, h - c, c - l)
    with np.errstate(divide="ignore", invalid="ignore"):
        sper = np.where(rng > 0, shadow * 100 / rng, np.inf)
    el = (c > o) & (c > e) & (sper <= p["shadow"])
    es = (c < o) & (c < e) & (sper <= p["shadow"])
    if p["side"] == "long":
        es = np.zeros(n, bool)
    entry = np.where(el, 1, np.where(es, -1, 0)).astype(np.int8)
    stop = p["k"] * ind.atr(df, 14)
    thr = p["exitpct"] / 100
    exl = np.zeros(n, bool)
    exs = np.zeros(n, bool)
    # simulação local do estado do motor para saber o preço de entrada
    pos, ep, sp, pend, pstop = 0, 0.0, 0.0, 0, 0.0
    for i in range(1, n):
        if pend and pos == 0:
            pos, ep = pend, o[i]
            sp = ep - pos * pstop
            pend = 0
        if pos > 0 and (o[i] <= sp or l[i] <= sp):
            pos = 0
        elif pos < 0 and (o[i] >= sp or h[i] >= sp):
            pos = 0
        if i + 1 >= n:
            break
        if pos > 0:
            if c[i] > ep * (1 + thr) and c[i] > o[i]:
                exl[i] = True
                pos = 0
            elif entry[i] == -1 and stop[i] > 0:
                pos, pend, pstop = 0, -1, stop[i]
        elif pos < 0:
            if c[i] < ep * (1 - thr) and c[i] < o[i]:
                exs[i] = True
                pos = 0
            elif entry[i] == 1 and stop[i] > 0:
                pos, pend, pstop = 0, 1, stop[i]
        elif entry[i] and stop[i] > 0:
            pend, pstop = int(entry[i]), stop[i]
    return {"entry": entry, "stop": stop, "exit_long": exl, "exit_short": exs}
