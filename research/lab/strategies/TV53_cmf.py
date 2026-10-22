"""Chaikin Money Flow (Marc Chaikin; versão comunidade "CMF [Yield]"). Rompimento de +th / -th."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV53_cmf",
    "name": "Chaikin Money Flow (CMF [Yield]): cruza acima de +limiar compra, abaixo de -limiar vende",
    "family": "volume",
    "round": 5,
    "origin": "TradingView comunidade (Yield, 'Chaikin Money Flow [Yield]'; Marc Chaikin)",
    "sources": [
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/chaikin-money-flow-cmf/",
        "https://github.com/f13end/tradingview-custom-indicators/blob/master/indicators/CMF%20%5BYield%5D",
    ],
    "sourceNote": "Pine 'CMF [Yield]' do repositório f13end (clonado em /home/user/labdata/pine). Usamos o mf cru "
                  "(Σ AD / Σ vol, sem a suavização ALMA de exibição). Limiares ±0,05 conforme StockCharts (zona neutra "
                  "perto de zero); a grade também testa 0 e 0,10.",
    "rule": "AD = ((2C-L-H)/(H-L))*vol (0 se H=L); CMF = Σ(AD,n)/Σ(vol,n). Compra quando o CMF cruza acima de +th; vende "
            "(side=both) quando cruza abaixo de -th. Saída 'opposite': no sinal contrário (cruza abaixo de -th / acima de +th); "
            "saída 'zero': quando o CMF cruza o zero contra a posição. Sem stop na fonte: stop k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [10, 20, 30], "th": [0.0, 0.05, 0.10], "exit": ["opposite", "zero"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def cmf(df, n):
    h, l, c, v = (df[k].values for k in ("high", "low", "close", "volume"))
    rng = h - l
    ad = np.where(rng > 0, (2 * c - l - h) / np.where(rng > 0, rng, 1) * v, 0.0)
    sv = pd.Series(v).rolling(n).sum().to_numpy()
    sa = pd.Series(ad).rolling(n).sum().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(sv > 0, sa / np.where(sv > 0, sv, 1), np.nan)


def signals(df, p):
    m = cmf(df, p["n"])
    th = p["th"]
    up = ind.cross_above(m, np.full(len(m), th))
    dn = ind.cross_below(m, np.full(len(m), -th))
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    if p["exit"] == "zero":
        z = np.zeros(len(m))
        exl, exs = ind.cross_below(m, z) | dn, ind.cross_above(m, z) | up
    else:
        exl, exs = dn, up
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
