"""Relative Vigor Index (John Ehlers, TASC jan/2002 'Something Old, Something New')."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L39_relative_vigor",
    "name": "Relative Vigor Index (Ehlers): cruzamento com a linha de sinal, filtro de tendência e zona",
    "family": "oscilador",
    "round": 9,
    "origin": "FILA.md (autor)",
    "sources": [
        "John F. Ehlers, 'Something Old, Something New', Technical Analysis of Stocks & Commodities, jan/2002",
        "https://www.luxalgo.com/library/indicator/relative-vigor-index/",
        "https://capital.com/en-gb/learn/technical-analysis/relative-vigor-index",
        "TradingView embutido RVGI (Pine: rvi = sum(swma(close-open),len)/sum(swma(high-low),len); sig = swma(rvi)), "
        "port em github.com/deepentropy/lightweight-charts-indicators src/standard/rvi.ts",
    ],
    "sourceNote": ("Não é duplicata do TV74_rvi: o TV74 é o Relative VOLATILITY Index de Dorsey (desvio padrão de máximas/mínimas). "
                   "Este é o Relative VIGOR Index de Ehlers (fechamento-abertura sobre máxima-mínima, média simétrica 1-2-2-1). "
                   "A triagem em massa (triagem-v1) já rodou o cruzamento puro RVGI x sinal com len=10 e stop 2ATR (reprovou: H4 no "
                   "desenvolvimento, D1 na validação); aqui a regra central de Ehlers (cruzamento com o sinal, mais forte a favor da "
                   "tendência) recebe filtro de tendência EMA e a opção de zona (compra só com RVGI abaixo de 0 = recuo na alta). "
                   "A combinação len=10, trend=0, zona=0, k=2, both equivale à da triagem. Sem stop no original: k*ATR14."),
    "rule": ("RVGI = soma(len) de swma(C-O) / soma(len) de swma(H-L), sinal = swma(RVGI), swma=(x+2x1+2x2+x3)/6. Compra quando RVGI cruza "
             "acima do sinal (se trend>0: fechamento acima da EMA(trend); se zona=1: RVGI<0 no cruzamento); vende (both) no espelho. "
             "Sai no cruzamento oposto. Stop k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"len": [10, 20], "trend": [0, 100, 200], "zona": [0, 1], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def swma(x):
    x = pd.Series(x)
    return ((x + 2 * x.shift(1) + 2 * x.shift(2) + x.shift(3)) / 6).to_numpy()


def signals(df, p):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    n = p["len"]
    num = pd.Series(swma(c - o)).rolling(n).sum().to_numpy()
    den = pd.Series(swma(h - l)).rolling(n).sum().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        rv = np.where(den > 0, num / den, np.nan)
    sg = swma(rv)
    up, dn = ind.cross_above(rv, sg), ind.cross_below(rv, sg)
    lg, sh = up.copy(), dn.copy()
    if p["trend"]:
        e = ind.ema(c, p["trend"])
        lg &= c > e
        sh &= c < e
    if p["zona"]:
        lg &= rv < 0
        sh &= rv > 0
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
