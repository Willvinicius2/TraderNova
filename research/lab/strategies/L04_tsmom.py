"""Momentum de série temporal (Moskowitz, Ooi & Pedersen, 2012)."""
import numpy as np

import indicators as ind

META = {
    "id": "L04_tsmom",
    "name": "Momentum de série temporal (TSMOM)",
    "family": "tendencia",
    "sources": [
        "https://papers.ssrn.com/abstract=2089463",
        "https://fairmodel.econ.yale.edu/ec439/jpde.pdf",
        "https://quantpedia.com/deconstructing-the-time-series-momentum-strategy/",
    ],
    "rule": ("A cada 'rebal' dias (convertidos em candles do tempo gráfico, ancorados no início do dia UTC) olha o retorno dos últimos "
             "'look' dias: positivo = comprado, negativo = vendido (side=both) ou fora (side=long). Mantém a posição até o próximo "
             "rebalanceamento que mude o sinal. Sem volatility scaling (resultado já é medido em R). Stop de proteção k*ATR com ATR "
             "de 14 dias (14*candles por dia); depois de um stop só reentra no próximo rebalanceamento."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"look": [30, 60, 90, 180, 365], "rebal": [1, 7, 30], "k": [2.0, 4.0], "side": ["long", "both"]},
}



def signals(df, p):
    step = (df.index[1:] - df.index[:-1]).to_series().median()
    bpd = max(1, int(round(86400 / step.total_seconds())))
    c = df.close.values
    L = p["look"] * bpd
    ret = c / ind.prev(c, L) - 1
    # rebalanceamento: último candle de cada bloco de 'rebal' dias (decisão no fechamento, executa na abertura seguinte)
    day = (df.index.normalize() - df.index[0].normalize()).days.values
    nxt_day = np.r_[day[1:], day[-1] + 1]
    rb = ((nxt_day // p["rebal"]) != (day // p["rebal"]))
    sgn = np.sign(np.nan_to_num(ret, nan=0.0))
    entry = np.where(rb, sgn, 0).astype(int)
    exl = rb & (sgn < 0)
    exs = rb & (sgn > 0)
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14 * bpd)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": exl, "exit_short": exs}
