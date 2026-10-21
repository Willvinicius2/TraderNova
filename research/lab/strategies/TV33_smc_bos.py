"""TV33 - Smart Money Concepts (LuxAlgo): rompimento de estrutura (BOS/CHoCH) com swings confirmados."""
import numpy as np

import indicators as ind

META = {
    "id": "TV33_smc_bos",
    "name": "Smart Money Concepts (LuxAlgo): BOS/CHoCH da estrutura de swing",
    "family": "rompimento",
    "round": 3,
    "origin": "TradingView comunidade (LuxAlgo)",
    "sources": [
        "https://www.tradingview.com/script/CnB3fSph-Smart-Money-Concepts-SMC-LuxAlgo/",
        "https://www.luxalgo.com/library/indicator/smart-money-concepts-smc/",
        "https://www.scribd.com/document/846054813/ict-code-indicator (cópia do Pine 'Smart Money Concepts [LuxAlgo]')",
    ],
    "rule": ("Lógica do Pine LuxAlgo (reproduzida da definição do script; WebFetch/GitHub não abriram o código, só resumos): "
             "leg(size): se high[size] > maior máxima dos 'size' candles seguintes começa perna de baixa; se low[size] < menor mínima "
             "dos 'size' seguintes começa perna de alta. Início de perna de baixa = topo de swing confirmado em high[size] (nível novo, "
             "'crossed'=falso); início de perna de alta = fundo de swing em low[size]. Rompimento: ta.crossover(close, topo) com topo "
             "ainda não cruzado -> se o viés era de baixa é CHoCH, senão BOS; o viés vira alta e o topo fica marcado como cruzado "
             "(espelho com crossunder do fundo). Swings só existem 'size' candles depois, então não há repintura. "
             "Regra testada: modo 'choch' entra só na mudança de caráter (virada do viés); modo 'bos' entra só no BOS de "
             "continuação a favor do viés; modo 'todos' entra em qualquer rompimento. Compra sai (e side=both inverte) no "
             "rompimento de baixa (que é sempre CHoCH contra o viés de alta). Sem stop no indicador: stop de proteção k*ATR14. "
             "Diferente da TV08 (Pivot Reversal): níveis de swing da perna LuxAlgo, cruzamento pelo fechamento, cada nível vale uma "
             "vez e a entrada depende do viés de estrutura (BOS x CHoCH)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"size": [5, 10, 20, 35, 50], "mode": ["choch", "bos", "todos"], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def structure(h, l, c, size):
    """Devolve arrays (por candle i, decididos no fechamento de i): rompimento de alta/baixa e tipo (1=BOS, 2=CHoCH)."""
    n = len(c)
    # newLegHigh em i: high[i-size] > max(high[i-size+1..i]); newLegLow análogo.
    hs, ls = ind.prev(h, size), ind.prev(l, size)
    hh, ll = ind.highest(h, size), ind.lowest(l, size)
    with np.errstate(invalid="ignore"):
        nlh = hs > hh
        nll = ls < ll
    up_brk = np.zeros(n, np.int8)
    dn_brk = np.zeros(n, np.int8)
    leg = 0  # Pine: var leg = 0 (BEARISH_LEG=0, BULLISH_LEG=1)
    top = bot = np.nan
    top_x = bot_x = True
    bias = 0  # 0 sem viés, 1 alta, -1 baixa
    prev_top = prev_bot = np.nan
    for i in range(n):
        new_leg = leg
        if nlh[i]:
            new_leg = 0
        elif nll[i]:
            new_leg = 1
        ch = new_leg - leg
        leg = new_leg
        cur_top, cur_bot = prev_top, prev_bot  # níveis do candle anterior (para crossover)
        if ch == -1:  # começo de perna de baixa -> topo de swing
            top, top_x = hs[i], False
        elif ch == 1:  # começo de perna de alta -> fundo de swing
            bot, bot_x = ls[i], False
        if i > 0 and not np.isnan(top) and not top_x and c[i] > top and c[i - 1] <= (top if np.isnan(cur_top) else cur_top):
            up_brk[i] = 2 if bias == -1 else 1
            top_x = True
            bias = 1
        if i > 0 and not np.isnan(bot) and not bot_x and c[i] < bot and c[i - 1] >= (bot if np.isnan(cur_bot) else cur_bot):
            dn_brk[i] = 2 if bias == 1 else 1
            bot_x = True
            bias = -1
        prev_top, prev_bot = top, bot
    return up_brk, dn_brk


_cache = {}


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    key = (id(df), len(df), p["size"])
    if key not in _cache:
        _cache[key] = structure(h, l, c, p["size"])
    ub, db = _cache[key]
    if p["mode"] == "choch":
        lg, sh = ub == 2, db == 2
    elif p["mode"] == "bos":
        lg, sh = ub == 1, db == 1
    else:
        lg, sh = ub > 0, db > 0
    lg, sh = lg & ~sh, sh & ~lg
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": db > 0, "exit_short": ub > 0}
