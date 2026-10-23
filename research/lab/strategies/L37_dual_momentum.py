"""Dual Momentum (Gary Antonacci, 'Dual Momentum Investing', 2014), adaptado a um ativo só."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L37_dual_momentum",
    "name": "Dual Momentum (Antonacci) adaptado: momentum absoluto + relativo à própria história",
    "family": "tendencia",
    "round": 9,
    "origin": "FILA.md (autor)",
    "sources": [
        "Gary Antonacci, Dual Momentum Investing (McGraw-Hill, 2014); https://www.optimalmomentum.com",
        "https://awealthofcommonsense.com/2015/07/my-thoughts-on-gary-antonaccis-dual-momentum/",
        "https://www.tradingview.com/script/7IWRmmC9-12M-Return-Strategy",
    ],
    "sourceNote": ("Antonacci (GEM): todo mês compara o retorno de 12 meses entre ativos (momentum relativo) e o do vencedor contra "
                   "T-bills (momentum absoluto); se o absoluto falha vai para renda fixa. Aqui só há um ativo por teste, então: "
                   "absoluto = retorno de 'look' dias > 0 (caixa rende ~0); relativo = o retorno de 'look' dias atual é maior que a média "
                   "desse mesmo retorno nos últimos 'rel' dias (o ativo contra a própria história de momentum, já que não há outro ativo). "
                   "Só o absoluto já foi testado no L04_tsmom; a exigência dos dois filtros ao mesmo tempo e a saída para caixa quando "
                   "qualquer um falha é o que diferencia. Sem stop no original: stop de proteção k*ATR(14 dias)."),
    "rule": ("A cada 'rebal' dias (fim de bloco, decisão no fechamento) calcula R = retorno de 'look' dias e M = média de R nos últimos "
             "'rel' dias. Compra se R>0 e R>M; vende (both) se R<0 e R<M; senão fica em caixa. Sai no rebalanceamento em que a condição "
             "do lado aberto deixa de valer. Stop k*ATR de 14 dias."),
    "timeframes": ["H4", "D1"],
    "grid": {"look": [90, 180, 365], "rel": [90, 180, 365], "rebal": [7, 30], "k": [3.0, 5.0], "side": ["long", "both"]},
}


def signals(df, p):
    step = (df.index[1:] - df.index[:-1]).to_series().median()
    bpd = max(1, int(round(86400 / step.total_seconds())))
    c = df.close.values
    R = c / ind.prev(c, p["look"] * bpd) - 1
    M = pd.Series(R).rolling(p["rel"] * bpd, min_periods=p["rel"] * bpd).mean().to_numpy()
    ok = ~(np.isnan(R) | np.isnan(M))
    up = ok & (R > 0) & (R > M)
    dn = ok & (R < 0) & (R < M)
    day = (df.index.normalize() - df.index[0].normalize()).days.values
    nxt = np.r_[day[1:], day[-1] + 1]
    rb = (nxt // p["rebal"]) != (day // p["rebal"])
    entry = np.where(rb & up, 1, np.where(rb & dn, -1, 0)).astype(int)
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14 * bpd)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": rb & ~up, "exit_short": rb & ~dn}
