"""TV10 - Parabolic SAR Strategy (estratégia embutida do TradingView).

Pine original (embutido): calcula o SAR de Wilder (start, increment, maximum) barra a barra e, no fechamento,
coloca strategy.entry com stop=nextBarSAR na direção contrária à tendência atual (parar e inverter).
Aproximação neste motor:
- a virada do SAR (máxima/mínima toca o SAR, regra do próprio indicador) gera a entrada na nova direção na
  abertura do candle seguinte (o Pine executaria no próprio nível do SAR, dentro do candle);
- a saída da posição é o próprio SAR como stop móvel (trail = distância do fechamento ao SAR do próximo candle),
  executada dentro do candle quando tocada, como a ordem stop do Pine;
- stop inicial = distância do fechamento ao SAR do próximo candle (mínimo 0,25*ATR para nunca ser zero).
"""
import numpy as np

import indicators as ind

META = {
    "id": "TV10_parabolic_sar",
    "name": "Parabolic SAR Strategy (TradingView)",
    "family": "tendencia",
    "round": 2,
    "origin": "TradingView embutida",
    "sources": [
        "https://www.tradingview.com/support/solutions/43000645065-parabolic-sar-strategy/",
        "https://www.tradingview.com/support/folders/43000587406-built-in-strategies/",
    ],
    "rule": ("SAR parabólico de Wilder (aceleração inicial start, incremento inc, máximo max). Quando o SAR vira para baixo do "
             "preço (máxima toca o SAR de baixa) compra; quando vira para cima vende (parar e inverter, como o Pine embutido). "
             "Entrada na abertura seguinte à virada; a posição usa o próprio SAR como stop móvel. No modo só compra, a virada "
             "para baixo fecha a compra."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"start": [0.01, 0.02, 0.03], "inc": [0.01, 0.02, 0.03], "max": [0.1, 0.2, 0.3], "side": ["long", "both"]},
}


def psar(h, l, c, start, inc, mx):
    """Réplica do Pine embutido. Retorna (uptrend[i], nextBarSAR[i], flip[i]) calculados no fechamento de i."""
    n = len(c)
    up = np.zeros(n, dtype=bool)
    nxt = np.full(n, np.nan)
    flip = np.zeros(n, dtype=bool)
    if n < 3:
        return up, nxt, flip
    # barra 1: inicialização
    if c[1] > c[0]:
        u, ep, sar = True, h[1], l[0]
    else:
        u, ep, sar = False, l[1], h[0]
    sar = sar + start * (ep - sar)
    af = start
    for i in range(1, n):
        first = i == 1
        if i > 1:
            sar = nxt[i - 1]
        if u:
            if sar > l[i]:
                first, u, sar, ep, af = True, False, max(ep, h[i]), l[i], start
                flip[i] = i > 1
        else:
            if sar < h[i]:
                first, u, sar, ep, af = True, True, min(ep, l[i]), h[i], start
                flip[i] = i > 1
        if not first:
            if u and h[i] > ep:
                ep, af = h[i], min(af + inc, mx)
            elif (not u) and l[i] < ep:
                ep, af = l[i], min(af + inc, mx)
        if u:
            sar = min(sar, l[i - 1])
            if i > 1:
                sar = min(sar, l[i - 2])
        else:
            sar = max(sar, h[i - 1])
            if i > 1:
                sar = max(sar, h[i - 2])
        nxt[i] = sar + af * (ep - sar)
        up[i] = u
    return up, nxt, flip


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    up, nxt, flip = psar(h, l, c, p["start"], p["inc"], p["max"])
    go_long = flip & up
    go_short = flip & ~up
    entry = np.where(go_long, 1, np.where(go_short, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    dist = np.where(up, c - nxt, nxt - c)
    stop = np.maximum(dist, 0.25 * a)
    # stop móvel no SAR (o motor usa c - pos*trail); só vale quando a tendência do SAR é a da posição;
    # na virada o sinal oposto/saída fecha na abertura seguinte se o SAR não tiver sido tocado antes.
    trail = np.where((dist > 0) & ~flip, dist, np.nan)
    return {"entry": entry, "stop": stop, "trail": trail, "exit_long": go_short, "exit_short": go_long}
