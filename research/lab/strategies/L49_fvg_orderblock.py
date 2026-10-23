"""L49 - ICT Fair Value Gap com retorno ao gap (sem olhar o futuro)."""
import numpy as np

import indicators as ind

META = {
    "id": "L49_fvg_orderblock",
    "name": "ICT Fair Value Gap: retorno ao gap com rejeição no meio (CE)",
    "family": "estrutura",
    "round": 9,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://www.luxalgo.com/library/concept/fair-value-gap/",
        "https://ninjatrader.com/futures/blogs/fair-value-gaps/",
        "Pine 'ICT FVG Buy/Sell Signals' (svmstellarvisionmedia, MPL-2.0), porte em github.com/deepentropy/lightweight-charts-indicators src/community/ict-fvg-buy-sell-signals.ts",
        "Michael J. Huddleston (ICT): FVG, consequent encroachment (CE) e order block = candle 1 do deslocamento",
    ],
    "rule": ("FVG de alta formado no fechamento do 3º candle i: mínima[i] > máxima[i-2], com o candle do meio de alta e corpo "
             ">= disp*ATR14 (deslocamento). Zona = [máxima[i-2], mínima[i]], CE = meio da zona; o candle i-2 é tratado como o "
             "order block e sua mínima é o nível de invalidação. Só o gap mais recente de cada lado fica ativo, por até 'wait' "
             "candles. Entrada: num candle posterior que toca a zona (mínima <= topo do gap) e fecha acima do CE (rejeição), "
             "compra na abertura seguinte. Gap invalidado se fechar abaixo do fundo do gap. Stop: mínima do candle 1 (order block) "
             "- 0,1*ATR (mínimo 0,25*ATR); alvo fixo target_r em R. Filtro opcional trend=ema200 (só compra acima da EMA200, só "
             "vende abaixo). Venda espelhada (side=both). Aproximação: o ICT usa ordem limitada no gap; aqui a entrada é na abertura "
             "após o candle de rejeição."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"disp": [0.5, 1.0, 1.5], "wait": [5, 10, 20], "target_r": [1.5, 2.0, 3.0], "trend": ["none", "ema200"],
             "side": ["long", "both"]},
}


def signals(df, p):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    n = len(c)
    a = ind.atr(df, 14)
    e = ind.ema(c, 200)
    body = np.abs(c - o)
    entry = np.zeros(n, dtype=np.int8)
    stop = np.full(n, np.nan)
    bull = None  # (top, bot, ce, inval, t)
    bear = None
    W, D = p["wait"], p["disp"]
    for i in range(2, n):
        if np.isnan(a[i]) or np.isnan(a[i - 1]):
            continue
        # 1) usa gaps formados até i-1 (sinal no candle i)
        sig = 0
        if bull is not None:
            top, bot, ce, inv, t = bull
            if i - t > W or c[i] < bot:
                bull = None
            elif l[i] <= top and c[i] > ce:
                ok = p["trend"] == "none" or (not np.isnan(e[i]) and c[i] > e[i])
                if ok:
                    sig = 1
                    stop[i] = max(c[i] - (inv - 0.1 * a[i]), 0.25 * a[i])
                bull = None
        if sig == 0 and bear is not None and p["side"] == "both":
            top, bot, ce, inv, t = bear
            if i - t > W or c[i] > top:
                bear = None
            elif h[i] >= bot and c[i] < ce:
                ok = p["trend"] == "none" or (not np.isnan(e[i]) and c[i] < e[i])
                if ok:
                    sig = -1
                    stop[i] = max((inv + 0.1 * a[i]) - c[i], 0.25 * a[i])
                bear = None
        entry[i] = sig
        # 2) formação de novos gaps no fechamento de i (ficam ativos a partir de i+1)
        disp_ok = body[i - 1] >= D * a[i - 1]
        if l[i] > h[i - 2] and c[i - 1] > o[i - 1] and disp_ok:
            bull = (l[i], h[i - 2], (l[i] + h[i - 2]) / 2, l[i - 2], i)
        if h[i] < l[i - 2] and c[i - 1] < o[i - 1] and disp_ok:
            bear = (l[i - 2], h[i], (l[i - 2] + h[i]) / 2, h[i - 2], i)
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0).astype(np.int8)
    return {"entry": entry, "stop": stop, "target_r": p["target_r"]}
