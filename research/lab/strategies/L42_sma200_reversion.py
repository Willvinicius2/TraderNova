"""L42 - Filtro de regime pela SMA 200 diária aplicado a uma reversão nova: banda da faixa média + IBS
(QuantifiedStrategies, "3 best mean reversion strategies"; regra testada lá em XLP).

Regra central nova no registry: a banda = maior máxima de n candles - mult x média de (máx-mín) de n candles
(não é Bollinger, z-score, RSI, IBS sozinho nem VWAP) combinada com IBS < limiar, saída quando fecha acima da máxima
anterior. O L06_ibs testou só o IBS; aqui o IBS é filtro secundário.
"""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L42_sma200_reversion",
    "name": "Reversão à banda da faixa média + IBS com regime SMA200 diária",
    "family": "reversao",
    "round": 9,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://quantifiedstrategies.substack.com/p/3-best-mean-reversion-trading-strategies (média de H-L de 25 dias; banda = máxima de 25 dias - 2,25 x essa média; compra no fechamento se fechar abaixo da banda e IBS < 0,6; sai quando o fechamento passa da máxima de ontem)",
        "https://doc.stocksharp.com/en/api-examples/0541_Average_High_Low_Range_IBS_Reversal (mesma regra portada)",
        "Filtro SMA200 diária: regra clássica de regime (Faber 2007; Connors & Alvarez, 'Short Term Trading Strategies That Work', 2008)",
    ],
    "rule": ("Média da faixa A = SMA(máx-mín, n). Banda de compra = maior máxima de n candles - mult*A; IBS = (fech-mín)/(máx-mín). "
             "Compra quando fecha abaixo da banda, IBS < ibs e o fechamento está acima da SMA200 dos fechamentos diários "
             "(em H1/H4 usa a SMA200 até o dia anterior completo). Sai quando o fechamento passa da máxima do candle anterior. "
             "Venda espelhada (side=both): banda = menor mínima de n + mult*A, IBS > 1-ibs, fechamento abaixo da SMA200 "
             "diária, sai quando fecha abaixo da mínima anterior. A fonte compra no fechamento; aqui entra na abertura seguinte. "
             "A fonte não tem stop: stop de proteção k*ATR14 e saída por tempo em 20 candles."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [15, 25, 40], "mult": [1.75, 2.25, 2.75], "ibs": [0.3, 0.6], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def daily_sma200(df):
    idx = df.index
    d = df.close.resample("1D").last().dropna()
    s = d.rolling(200).mean()
    step = (idx[1:] - idx[:-1]).min() if len(idx) > 1 else pd.Timedelta(days=1)
    if step < pd.Timedelta(days=1):
        s = s.shift(1)  # intradiário: só o dia anterior completo
    return s.reindex(idx.floor("D")).to_numpy()


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    n = p["n"]
    A = ind.sma(h - l, n)
    rng = h - l
    with np.errstate(divide="ignore", invalid="ignore"):
        ibs = np.where(rng > 0, (c - l) / rng, 0.5)
    sma = daily_sma200(df)
    up = c > sma
    dn = c < sma
    lband = ind.highest(h, n) - p["mult"] * A
    uband = ind.lowest(l, n) + p["mult"] * A
    el = up & (c < lband) & (ibs < p["ibs"])
    es = dn & (c > uband) & (ibs > 1 - p["ibs"])
    entry = np.where(el, 1, np.where(es, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a,
            "exit_long": c > ind.prev(h), "exit_short": c < ind.prev(l), "max_hold": 20}
