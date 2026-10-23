"""L46 - Efeito fim de semana / dia da semana no BTC (Caporale & Plastun 2017/2019)."""
import numpy as np

import indicators as ind

META = {
    "id": "L46_weekend_effect",
    "name": "Efeito fim de semana do BTC (sexta→segunda)",
    "family": "calendario",
    "round": 9,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://quantpedia.com/the-day-of-the-week-effect-in-the-crypto-currency-market/",
        "https://cesifo.org/DocDL/cesifo1_wp6716.pdf",
        "https://www.diw.de/de/diw_01.c.567282.de/publikationen/diskussionspapiere/2017_1694/the_day_of_the_week_effect_in_the_crypto_currency_market.html",
        "https://cointelegraph.com/markets/new-analysis-finds-that-mondays-are-the-best-days-to-buy-bitcoin",
    ],
    "rule": ("Caporale & Plastun acham retorno anormal positivo do BTC na segunda-feira (efeito dia da semana); o item da FILA "
             "pede sexta→segunda. Posição só na janela de dias da semana [first..last] (4=sexta, 5=sábado, 6=domingo, "
             "7=segunda, 8=terça): entra na abertura D1 (00:00 UTC) do dia 'first' e sai na abertura do dia seguinte a 'last'. "
             "side=long compra na janela; short vende na janela; both compra na janela e vende no resto da semana. Stop de "
             "proteção k*ATR14 D1 (a fonte não tem). Difere do L17 (hora do dia) e do L17_r1 (janela 21-23h só em certos dias)."),
    "timeframes": ["D1"],
    "grid": {"first": [4, 5, 6], "last": [6, 7, 8], "k": [3.0, 5.0], "side": ["long", "short", "both"]},
}


def _inwin(dow, first, last):
    # dow: 0=seg..6=dom; janela em escala 4..8 (7=seg, 8=ter)
    x = np.where(dow <= 1, dow + 7, dow)
    return (x >= first) & (x <= last)


def signals(df, p):
    dow = df.index.dayofweek.values
    now = _inwin(dow, p["first"], p["last"])
    nxt = _inwin((dow + 1) % 7, p["first"], p["last"])
    start = (~now) & nxt
    end = now & (~nxt)
    a = ind.atr(df, 14)
    if p["side"] == "long":
        return {"entry": np.where(start, 1, 0), "stop": p["k"] * a, "exit_long": end}
    if p["side"] == "short":
        return {"entry": np.where(start, -1, 0), "stop": p["k"] * a, "exit_short": end}
    entry = np.where(start, 1, np.where(end, -1, 0))
    return {"entry": entry, "stop": p["k"] * a, "exit_long": end}
