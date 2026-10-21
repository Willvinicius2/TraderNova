"""TV01 - BarUpDn Strategy (estratégia embutida do TradingView)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV01_barupdn",
    "name": "BarUpDn Strategy (TradingView)",
    "family": "padroes",
    "round": 2,
    "origin": "TradingView embutida",
    "sources": [
        "https://www.tradingview.com/support/folders/43000587406-built-in-strategies/",
        "https://www.oanda.jp/lab-education/tradingviewstrategy/strategy/tradingview_barupdn_strategy",
        "https://www.tradingview.com/script/7IDDZNte-BarUpDn-Strategy/",
    ],
    "rule": ("Pine original: compra quando a vela fecha em alta (fech > abert) e abriu acima do fechamento anterior "
             "(abert > fech[1]); vende no espelho (fech < abert e abert < fech[1]). Sempre posicionado, cada sinal oposto inverte. "
             "Entrada na abertura seguinte (igual ao Pine, ordem a mercado). O Pine não tem stop (só 'max intraday loss' por % do capital, "
             "não reproduzível em R): usamos stop de proteção k*ATR14. Depois de um stop, reentra no próximo sinal."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"k": [1.5, 2.0, 3.0, 4.0, 6.0], "side": ["long", "both"]},
}


def signals(df, p):
    o, c = df.open.values, df.close.values
    pc = ind.prev(c)
    up = (c > o) & (o > pc)
    dn = (c < o) & (o < pc)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    exl = None
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
        exl = dn  # no modo só compra, o sinal de venda fecha a compra
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": exl}
