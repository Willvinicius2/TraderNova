"""Rate of Change em unidades de volatilidade ex-ante (Moskowitz, Ooi & Pedersen 2012, vol scaling)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L38_roc_voltarget",
    "name": "ROC com volatilidade-alvo (Moskowitz vol scaling): momentum em desvios ex-ante com zona neutra",
    "family": "tendencia",
    "round": 9,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://papers.ssrn.com/abstract=2089463",
        "https://alphaarchitect.com/time-series-momentum-and-volatility-scaling/",
        "https://quantpedia.com/deconstructing-the-time-series-momentum-strategy/",
    ],
    "sourceNote": ("MOP 2012: posição = sinal(retorno de 12m) x 40%/sigma_ex-ante, sigma = EWMA dos retornos diários ao quadrado com "
                   "centro de massa 60 dias. O L04_tsmom já testou o sinal do retorno (sem vol scaling, rebalanceando a cada N dias). "
                   "Como o motor mede tudo em R com risco fixo, o vol scaling vira: (1) o stop é k x sigma ex-ante diária (posição "
                   "inversamente proporcional à volatilidade, como na volatilidade-alvo); (2) o sinal é o ROC dividido pela volatilidade "
                   "esperada no horizonte (ROC/(sigma*sqrt(L))), com zona neutra z0, decidido a cada candle; (3) opcional: não abrir quando "
                   "sigma está acima de vmax x a mediana de 1 ano (com alvo de volatilidade a exposição cairia muito)."),
    "rule": ("z = ROC(look dias) / (sigma_diária_EWMA(com 60d) * sqrt(look)). Compra quando z cruza acima de z0; vende (both) quando cruza "
             "abaixo de -z0; sai quando z volta a cruzar 0. Se vmax>0, só abre se sigma <= vmax * mediana de sigma em 365 dias. "
             "Stop k * sigma_diária * preço."),
    "timeframes": ["H4", "D1"],
    "grid": {"look": [30, 60, 120, 250], "z0": [0.5, 1.0, 1.5], "k": [2.0, 3.0], "vmax": [0, 1.5], "side": ["long", "both"]},
}


def signals(df, p):
    step = (df.index[1:] - df.index[:-1]).to_series().median()
    bpd = max(1, int(round(86400 / step.total_seconds())))
    c = df.close.values
    r = np.r_[np.nan, np.log(c[1:] / c[:-1])]
    var_bar = pd.Series(r ** 2).ewm(com=60 * bpd, adjust=False, min_periods=20 * bpd, ignore_na=True).mean().to_numpy()
    sd = np.sqrt(var_bar * bpd)  # sigma diária
    L = p["look"] * bpd
    roc = np.log(c / ind.prev(c, L))
    with np.errstate(invalid="ignore", divide="ignore"):
        z = roc / (sd * np.sqrt(p["look"]))
    z0 = p["z0"]
    zero = np.zeros(len(c))
    lg = ind.cross_above(z, zero + z0)
    sh = ind.cross_below(z, zero - z0)
    if p["vmax"]:
        med = pd.Series(sd).rolling(365 * bpd, min_periods=180 * bpd).median().to_numpy()
        okv = sd <= p["vmax"] * med
        lg &= okv
        sh &= okv
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * sd * c,
            "exit_long": ind.cross_below(z, zero), "exit_short": ind.cross_above(z, zero)}
