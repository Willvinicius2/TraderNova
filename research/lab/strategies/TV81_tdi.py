"""Traders Dynamic Index (Dean Malone): cruzamento da linha de preço (SMA2 do RSI) sobre a linha de sinal (SMA7)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV81_tdi",
    "name": "Traders Dynamic Index (Dean Malone)",
    "family": "momentum",
    "round": 6,
    "origin": "TradingView comunidade (Goldminds / thienlovv)",
    "sources": [
        "https://www.luxalgo.com/library/concept/traders-dynamic-index/",
        "https://www.earnforex.com/es/indicadores/Traders-Dynamic-Index/",
        "github.com/deepentropy/lightweight-charts-indicators src/community/tdi-rsi.ts (port do 'TDI - Traders Dynamic Index [Goldminds]', MPL-2.0)",
    ],
    "rule": ("RSI(rsi) do fechamento (Wilder). Linha de preço = SMA2(RSI), linha de sinal = SMA7(RSI), linha base = SMA34(RSI) e "
             "bandas = base ± 1,6185 × desvio-padrão(RSI, 34). Compra quando a linha de preço cruza acima da linha de sinal com a "
             "linha de preço acima de 50 e abaixo da banda superior (dentro das bandas); com base=1 exige também a linha base acima "
             "de 50 (filtro de regime descrito pela LuxAlgo). Venda (side=both) no espelho (abaixo de 50, acima da banda inferior, "
             "base abaixo de 50). Saída: exit=cross sai no cruzamento oposto preço/sinal; exit=base sai quando a linha de preço "
             "cruza a linha base contra a posição. Indicador sem stop: stop de proteção k × ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"rsi": [8, 13, 21], "base": [0, 1], "exit": ["cross", "base"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    c = df.close.values
    r = ind.rsi(c, p["rsi"])
    pl, sg, mb = ind.sma(r, 2), ind.sma(r, 7), ind.sma(r, 34)
    sd = ind.stdev(r, 34)  # Pine ta.stdev é populacional
    ub, lb = mb + 1.6185 * sd, mb - 1.6185 * sd
    xu, xd = ind.cross_above(pl, sg), ind.cross_below(pl, sg)
    lo = xu & (pl > 50) & (pl < ub)
    sh = xd & (pl < 50) & (pl > lb)
    if p["base"]:
        lo &= mb > 50
        sh &= mb < 50
    entry = np.where(lo, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    if p["exit"] == "cross":
        exl, exs = xd, xu
    else:
        exl, exs = ind.cross_below(pl, mb), ind.cross_above(pl, mb)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
