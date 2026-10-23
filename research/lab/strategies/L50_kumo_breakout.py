"""L50 - Ichimoku Kumo breakout (rompimento da nuvem com Chikou e nuvem futura)."""
import numpy as np

import indicators as ind

META = {
    "id": "L50_kumo_breakout",
    "name": "Ichimoku Kumo breakout com Chikou e nuvem futura",
    "family": "tendencia",
    "round": 9,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://www.oanda.com/bvi-en/skills-and-insights/education/technical-analysis/indicators-and-oscillators/ichimoku-cloud-trading-guide-key-strategies/",
        "https://www.luxalgo.com/library/concept/ichimoku-signals.md",
        "Goichi Hosoda, Ichimoku Kinko Hyo (definições 9/26/52)",
    ],
    "rule": ("Linhas como no L03 (Tenkan 9*s, Kijun 26*s, Senkou B 52*s, nuvem deslocada 26*s: a nuvem em i usa dados até "
             "i-26*s). Diferente do L03 (que entra no cruzamento Tenkan/Kijun): aqui o gatilho é o FECHAMENTO cruzar acima do topo "
             "da nuvem (antes estava em ou abaixo dele), com Chikou confirmando (fechamento > fechamento de 26*s atrás) e, se "
             "future=yes, nuvem futura de alta (Senkou A > Senkou B calculados agora, sem deslocamento). Venda espelhada abaixo do "
             "fundo da nuvem. Saída: exit=kijun fecha do lado errado da Kijun; exit=cloud volta para dentro/além da nuvem "
             "(fechamento abaixo do fundo da nuvem na compra). Stop inicial k*ATR14 (a fonte não define stop)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"s": [1, 2, 3], "future": ["no", "yes"], "exit": ["kijun", "cloud"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def mid(df, n):
    return (ind.highest(df.high.values, n) + ind.lowest(df.low.values, n)) / 2


def signals(df, p):
    s = p["s"]
    c = df.close.values
    tk, kj, sb = mid(df, 9 * s), mid(df, 26 * s), mid(df, 52 * s)
    sa = (tk + kj) / 2
    disp = 26 * s
    A, B = ind.prev(sa, disp), ind.prev(sb, disp)
    top, bot = np.fmax(A, B), np.fmin(A, B)
    pc = ind.prev(c)
    up = (c > top) & (pc <= ind.prev(top))
    dn = (c < bot) & (pc >= ind.prev(bot))
    c_back = ind.prev(c, disp)
    lg = up & (c > c_back)
    sh = dn & (c < c_back)
    if p["future"] == "yes":
        lg &= sa > sb
        sh &= sa < sb
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    if p["exit"] == "kijun":
        exl, exs = c < kj, c > kj
    else:
        exl, exs = c < bot, c > top
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": exl, "exit_short": exs}
