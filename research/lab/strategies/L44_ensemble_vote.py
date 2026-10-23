"""L44 - Ensemble de votação de 5 indicadores clássicos (ratings próprios).

Diferença do TV11_technical_ratings: lá são 26 componentes (15 médias + 11 osciladores, média de dois grupos, Strong
Buy > 0,5, stop móvel ativado por lucro). Aqui são só 5 votos de peso igual, escolhidos entre os componentes do
"Ensemble Voting of Signals" do LuxAlgo, com zona neutra de 5 pontos nos osciladores, placar de -100 a +100 suavizado
por EMA, entrada no cruzamento do limiar e saída quando o placar perde o consenso (sem stop móvel).
"""
import numpy as np

import indicators as ind

META = {
    "id": "L44_ensemble_vote",
    "name": "Ensemble de votação de 5 indicadores clássicos",
    "family": "tendencia",
    "round": 9,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://www.luxalgo.com/library/indicator/ensemble-voting-of-signals/ (votos de cruzamento EMA 20/50, preço x SMA200, RSI14, MACD 12/26/9, Estocástico %K 14/3 e outros; zona neutra 5 em torno de 50; placar -100..+100 suavizado por EMA 3; limiar 20 Buy, 60 Strong Buy)",
        "https://www.tradingview.com/script/Ztmvs25e-Ensemble-Consensus-System/ (consenso de indicadores, script público)",
    ],
    "rule": ("Cinco votos (+1/0/-1): EMA20 > EMA50; fechamento > SMA200; RSI14 > 55 (+1) ou < 45 (-1); linha MACD(12,26,9) "
             "acima/abaixo do sinal; Estocástico %K(14, suavizado 3) > 55 ou < 45. Placar = 100*soma/5 suavizado por EMA(sm). "
             "Compra quando o placar cruza acima de +thr e vende quando cruza abaixo de -thr (inverte). Sai da compra quando o "
             "placar fica abaixo de ex e da venda quando fica acima de -ex. A fonte não define stop: stop k*ATR14. "
             "side=long só compra."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"thr": [20, 40, 60], "ex": [-20, 0, 20], "sm": [3], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def _v(cond_up, cond_dn):
    return np.where(cond_up, 1, np.where(cond_dn, -1, 0))


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    e20, e50, s200 = ind.ema(c, 20), ind.ema(c, 50), ind.sma(c, 200)
    r = ind.rsi(c, 14)
    macd = ind.ema(c, 12) - ind.ema(c, 26)
    sig = ind.ema(macd, 9)
    hh, ll = ind.highest(h, 14), ind.lowest(l, 14)
    with np.errstate(divide="ignore", invalid="ignore"):
        fk = np.where(hh > ll, 100 * (c - ll) / (hh - ll), 50.0)
    k = ind.sma(fk, 3)
    votes = (_v(e20 > e50, e20 < e50) + _v(c > s200, c < s200) + _v(r > 55, r < 45)
             + _v(macd > sig, macd < sig) + _v(k > 55, k < 45))
    valid = ~(np.isnan(s200) | np.isnan(sig) | np.isnan(k) | np.isnan(r))
    score = np.where(valid, 100.0 * votes / 5.0, np.nan)
    sc = ind.ema(score, p["sm"])
    t = np.full(len(c), float(p["thr"]))
    up = ind.cross_above(sc, t)
    dn = ind.cross_below(sc, -t)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": sc < p["ex"], "exit_short": sc > -p["ex"]}
