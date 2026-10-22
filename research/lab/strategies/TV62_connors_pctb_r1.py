"""%b de Connors (Connors & Alvarez, High Probability ETF Trading, 2009)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV62_connors_pctb_r1",
    "refines": "TV62_connors_pctb",
    "refinement": "No desenvolvimento, poucas operações e só 3/5 anos positivos; trades longos (17 candles no H4) esperando %b > 0,8 devolvem o ganho. Saída alternativa na banda do meio (%b > 0,5) e filtro de tendência 100/200.",
    "name": "%b de Connors: fechamentos seguidos com %B(20,2) baixo acima da SMA200",
    "family": "reversao",
    "round": 5,
    "origin": "TradingView comunidade (regra do livro de Connors & Alvarez 2009)",
    "sources": [
        "https://quantifiedstrategies.substack.com/p/larry-connors-b-strategy-bollinger-eb7",
        "https://doc.stocksharp.com/es/api-examples/0968_Larry_Connors_Bollinger_PercentB",
        "https://www.tradingview.com/script/yXkWPSlU",
        "Connors & Alvarez (2009), High Probability ETF Trading, cap. %b",
    ],
    "sourceNote": "Regras detalhadas atrás de paywall nas páginas web; usada a definição clássica do livro (acima da SMA200, %b < 0,2 por 3 "
                  "fechamentos seguidos, sai com %b > 0,8), que é também a da FILA.",
    "rule": "Igual ao TV62, com SMA de tendência trend (100/200) e saída em %B > xb (0,5 ou 0,8; venda espelhada sai com %B < 1-xb). %B = (fechamento - banda inferior)/(banda superior - banda inferior), Bollinger(20,2). Compra quando fechamento > SMA200 e %B < lo "
            "nos últimos d fechamentos seguidos; sai quando %B > 1-lo (0,8 no original). Venda espelhada (both) abaixo da SMA200 com %B > 1-lo "
            "por d candles, sai com %B < lo. Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4"],
    "grid": {"trend": [100, 200], "d": [2, 3, 4], "lo": [0.1, 0.2, 0.3], "xb": [0.5, 0.8], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    c = df.close.values
    m, sd = ind.sma(c, 20), ind.stdev(c, 20)
    up, dn = m + 2 * sd, m - 2 * sd
    with np.errstate(invalid="ignore", divide="ignore"):
        b = (c - dn) / (up - dn)
        low = pd.Series((b < p["lo"]).astype(float)).rolling(p["d"]).sum().to_numpy() == p["d"]
        high = pd.Series((b > 1 - p["lo"]).astype(float)).rolling(p["d"]).sum().to_numpy() == p["d"]
        s200 = ind.sma(c, p["trend"])
        lg = (c > s200) & low
        sh = (c < s200) & high
        exl = b > p["xb"]
        exs = b < 1 - p["xb"]
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
