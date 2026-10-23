"""TD Sequential de Tom DeMark: setup de 9 (com perfeição) como sinal de exaustão."""
import numpy as np

import indicators as ind

META = {
    "id": "L30_td_setup9_r1",
    "refines": "L30_td_setup9",
    "refinement": "No desenvolvimento o setup 9 contra qualquer tendência não teve vantagem em H1/H4 (PF ~1,0) e no D1 deu só 14 operações. Filtro de tendência: só aceita o setup de compra (exaustão de correção) com fechamento acima da SMA(trend) e o de venda abaixo dela, operando os dois lados.",
    "name": "TD Sequential (DeMark): setup 9 a favor da tendência SMA",
    "family": "reversao",
    "round": 8,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://www.luxalgo.com/library/concept/td-sequential/",
        "https://www.mql5.com/en/blogs/post/750147",
        "Thomas R. DeMark, The New Science of Technical Analysis (Wiley, 1994); Jason Perl, DeMark Indicators (Bloomberg, 2008)",
    ],
    "rule": ("Setup de compra: depois de uma virada de preço baixista (candle anterior com fech > fech de 4 candles antes e o "
             "atual com fech < fech[4]), 9 fechamentos seguidos menores que o fechamento de 4 candles antes; qualquer fech >= fech[4] "
             "zera a contagem. Perfeição (DeMark): mínima do candle 8 ou do 9 <= mínimas dos candles 6 e 7. Setup de venda no espelho "
             "(máximas do 8 ou 9 >= máximas do 6 e 7). Compra no fechamento do candle 9 do setup de compra (perfect=1 exige perfeição); "
             "vende (side=both) no 9 do setup de venda. Saída por tempo (hold candles) ou ao completar o setup oposto. Stop 'td' = "
             "TD Risk Level de Perl/DeMark: menor mínima do setup menos o range verdadeiro desse candle (venda: maior máxima + range), "
             "com piso de 0,5*ATR14; 'atr2'/'atr3' = k*ATR14. Sem countdown 13. Refinamento r1: setup de compra só vale com fech > SMA(trend) e o de venda com fech < SMA(trend)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"perfect": [0, 1], "hold": [5, 9, 13], "trend": [100, 200], "stop": ["td", "atr3"], "side": ["long", "both"]},
}

_cache = {}


def td_setups(df):
    c, h, l = df.close.values, df.high.values, df.low.values
    n = len(c)
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    buy9 = np.zeros(n, bool); sell9 = np.zeros(n, bool)
    bperf = np.zeros(n, bool); sperf = np.zeros(n, bool)
    brisk = np.full(n, np.nan); srisk = np.full(n, np.nan)
    bc = sc = 0
    for i in range(5, n):
        dn = c[i] < c[i - 4]
        up = c[i] > c[i - 4]
        # contagem de compra
        if dn:
            if bc > 0:
                bc += 1
            elif c[i - 1] > c[i - 5]:  # virada de preço baixista
                bc = 1
        else:
            bc = 0
        if up:
            if sc > 0:
                sc += 1
            elif c[i - 1] < c[i - 5]:  # virada de preço altista
                sc = 1
        else:
            sc = 0
        if bc == 9:
            buy9[i] = True
            bperf[i] = min(l[i], l[i - 1]) <= min(l[i - 3], l[i - 2])
            j = i - 8 + int(np.argmin(l[i - 8:i + 1]))
            brisk[i] = l[j] - tr[j]
            bc = 0  # o setup termina no 9 (não conta 18)
        if sc == 9:
            sell9[i] = True
            sperf[i] = max(h[i], h[i - 1]) >= max(h[i - 3], h[i - 2])
            j = i - 8 + int(np.argmax(h[i - 8:i + 1]))
            srisk[i] = h[j] + tr[j]
            sc = 0
    return buy9, sell9, bperf, sperf, brisk, srisk


def signals(df, p):
    key = (id(df), len(df))
    if key not in _cache:
        _cache[key] = (td_setups(df), ind.atr(df, 14))
    (buy9, sell9, bperf, sperf, brisk, srisk), a = _cache[key]
    c = df.close.values
    tma = ind.sma(c, p["trend"])
    lb = buy9 & (bperf if p["perfect"] else True) & (c > tma)
    ss = sell9 & (sperf if p["perfect"] else True) & (c < tma)
    entry = np.where(lb, 1, np.where(ss, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    if p["stop"] == "td":
        st = np.where(lb, c - brisk, np.where(ss, srisk - c, np.nan))
        st = np.maximum(st, 0.5 * a)
    else:
        st = (2.0 if p["stop"] == "atr2" else 3.0) * a
    return {"entry": entry, "stop": st, "exit_long": sell9, "exit_short": buy9, "max_hold": p["hold"]}
