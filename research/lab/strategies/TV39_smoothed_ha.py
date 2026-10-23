"""TV39 - Trend Indicator A-V2 (nuvem Heikin Ashi suavizada), Pine de DZIV."""
import numpy as np

import indicators as ind

META = {
    "id": "TV39_smoothed_ha",
    "name": "Trend Indicator A-V2: cor da Heikin Ashi suavizada por EMA",
    "family": "tendencia",
    "round": 4,
    "origin": "TradingView comunidade (DZIV)",
    "sources": [
        "https://www.tradingview.com/scripts/dziv/",
        "https://www.mql5.com/en/job/250638",
        "Código: github.com/deepentropy/lightweight-charts-indicators src/community/trend-indicator-a-v2.ts (port fiel do Pine v2.3)",
    ],
    "rule": ("Pine v2.3 (média EMA, período 9): velas Heikin Ashi do próprio tempo gráfico (fech=(A+M+m+F)/4; abertura=(abertHA[1]+fechHA[1])/2); "
             "EMA(n) da abertura HA e EMA(n) do fechamento HA. A nuvem fica positiva quando a EMA do fechamento HA está acima da EMA da "
             "abertura HA. Compra quando a EMA do fechamento HA cruza acima da EMA da abertura HA; venda no cruzamento abaixo. "
             "O script é só indicador (sem ordens): sai/inverte na troca de cor; side=long só compra; stop de proteção k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [5, 9, 14, 21, 30], "k": [1.5, 2.0, 3.0], "side": ["long", "both"]},
}


def ha(df):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    hc = (o + h + l + c) / 4
    ho = np.empty(len(c))
    ho[0] = (o[0] + c[0]) / 2
    for i in range(1, len(c)):
        ho[i] = (ho[i - 1] + hc[i - 1]) / 2
    return ho, hc


def signals(df, p):
    ho, hc = ha(df)
    mo, mc = ind.ema(ho, p["n"]), ind.ema(hc, p["n"])
    up = ind.cross_above(mc, mo)
    dn = ind.cross_below(mc, mo)
    up[:200] = False
    dn[:200] = False
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
