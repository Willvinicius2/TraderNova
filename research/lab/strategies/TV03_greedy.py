"""TV03 - Greedy Strategy (estratégia embutida do TradingView)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV03_greedy",
    "name": "Greedy Strategy (TradingView)",
    "family": "padroes",
    "round": 2,
    "origin": "TradingView embutida",
    "sources": [
        "https://www.tradingview.com/support/solutions/43000599876-greedy-strategy/",
        "https://www.oanda.jp/lab-education/?p=31673",
    ],
    "rule": ("Pine original: se a vela abre com gap acima da máxima anterior (abert > máx[1]) coloca compra stop em máx[1]; "
             "gap abaixo da mínima anterior (abert < mín[1]) coloca venda stop em mín[1]; alvo e stop fixos em ticks a partir do preço "
             "médio, e adiciona ordens a favor enquanto a cor da vela confirma (pirâmide, até 5 por dia). Aproximação: a ordem stop "
             "é preenchida na abertura seguinte (o preço já está além do nível depois do gap); sem pirâmide (o motor tem uma posição); "
             "alvo/stop de 10 ticks não fazem sentido no BTC, então viram tp*ATR14 e sl*ATR14. Em BTC 24/7 'gap' só aparece em "
             "intraday (buracos/saltos entre candles), por isso M15/H1/H4."),
    "timeframes": ["M15", "H1", "H4"],
    "grid": {"sl": [1.0, 1.5, 2.0, 3.0], "tp": [1.0, 2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def signals(df, p):
    o, h, l = df.open.values, df.high.values, df.low.values
    up = o > ind.prev(h)
    dn = o < ind.prev(l)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["sl"] * a, "target": p["tp"] * a}
