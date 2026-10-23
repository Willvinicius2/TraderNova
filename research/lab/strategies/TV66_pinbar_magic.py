"""TV66 - Pin Bar Magic v1 (ZenAndTheArtOfTrading, cópia no repositório Alorse)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV66_pinbar_magic",
    "name": "Pin Bar Magic v1: pin bar que fura a média com leque de médias alinhado",
    "family": "padroes",
    "round": 5,
    "origin": "TradingView comunidade (ZenAndTheArtOfTrading)",
    "sources": [
        "https://github.com/Alorse/pinescript-strategies (strategies/other/Pin Bar Magic v1.pine, commit 8fb3837)",
        "https://doc.stocksharp.com/de/api-examples/0439_Pin_Bar_Magic",
        "https://www.tradingview.com/scripts/pinbar/",
    ],
    "rule": ("Pine v4: SMA lenta 50, EMA média 18, EMA rápida 6 (variante '10/20/50' com EMA10/EMA20/SMA50 também testada). "
             "Pin bar de alta: sombra inferior (até o corpo) > 66% do range; de baixa espelhado. Leque de alta: EMA rápida > EMA média > "
             "SMA lenta. 'Pierce' de alta: a mínima fura uma das 3 médias com abertura e fechamento acima dela. Sinal = leque + pin bar + "
             "pierce. O Pine coloca compra stop na máxima do candle anterior ao pin bar (high[1]) com stop em low[1] - 0,5*ATR14[1] "
             "(fórmula do tamanho da posição) e cancela a ordem quando passam mais de 3 candles. Aproximação: compra na abertura "
             "seguinte quando um fechamento, do pin bar até 3 candles depois, fica acima de high[1]; stop = distância até "
             "low[1] - m*ATR14[1]. Saída do Pine: close_all quando a EMA rápida cruza abaixo da média (venda: acima) e trailing de "
             "1 ponto/1 ponto (quase nada; aqui trailing de tk*ATR14 sobre o fechamento, como na descrição da fila). O fechamento de "
             "sexta 16h do Pine (forex) não se aplica ao BTC 24/7 e foi omitido."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"emas": ["6/18/50", "10/20/50"], "m": [0.5, 1.0], "tk": [1.0, 2.0, 3.0, 5.0], "side": ["long", "both"]},
}


def signals(df, p):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    nf, nm, ns = (int(x) for x in p["emas"].split("/"))
    slow, med, fast = ind.sma(c, ns), ind.ema(c, nm), ind.ema(c, nf)
    rng = h - l
    bull_pin = ((c > o) & ((o - l) > 0.66 * rng)) | ((c < o) & ((c - l) > 0.66 * rng))
    bear_pin = ((c > o) & ((h - c) > 0.66 * rng)) | ((c < o) & ((h - o) > 0.66 * rng))
    fan_up = (fast > med) & (med > slow)
    fan_dn = (fast < med) & (med < slow)

    def pierce_up(x):
        return (l < x) & (o > x) & (c > x)

    def pierce_dn(x):
        return (h > x) & (o < x) & (c < x)

    bp = pierce_up(fast) | pierce_up(med) | pierce_up(slow)
    sp = pierce_dn(fast) | pierce_dn(med) | pierce_dn(slow)
    long_sig = fan_up & bull_pin & bp
    short_sig = fan_dn & bear_pin & sp
    if p["side"] == "long":
        short_sig = np.zeros(len(c), bool)
    a = ind.atr(df, 14)
    h1, l1, a1 = ind.prev(h, 1), ind.prev(l, 1), ind.prev(a, 1)
    n = len(c)
    entry = np.zeros(n, np.int8)
    stop = np.full(n, np.nan)
    LW = 3
    lv_l = st_l = lv_s = st_s = np.nan
    age_l = age_s = 99
    for i in range(n):
        if long_sig[i]:
            lv_l, st_l, age_l = h1[i], l1[i] - p["m"] * a1[i], 0
        if short_sig[i]:
            lv_s, st_s, age_s = l1[i], h1[i] + p["m"] * a1[i], 0
        if age_l <= LW and c[i] > lv_l and c[i] - st_l > 0:
            entry[i], stop[i] = 1, c[i] - st_l
            age_l = 99
        elif age_s <= LW and c[i] < lv_s and st_s - c[i] > 0:
            entry[i], stop[i] = -1, st_s - c[i]
            age_s = 99
        age_l += 1
        age_s += 1
    xdn = ind.cross_below(fast, med)
    xup = ind.cross_above(fast, med)
    return {"entry": entry, "stop": stop, "trail": p["tk"] * a, "exit_long": xdn, "exit_short": xup}
