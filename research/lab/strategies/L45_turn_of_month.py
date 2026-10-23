"""L45 - Turn of the month no BTC (Ariel 1987 / Lakonishok-Smidt 1988; QuantifiedStrategies 'end of month effect in bitcoin')."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L45_turn_of_month",
    "name": "Turn of the month no BTC (últimos dias do mês + primeiros do seguinte)",
    "family": "calendario",
    "round": 9,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://quantifiedstrategies.substack.com/p/bitcoin-the-end-of-month-effect",
        "https://www.quantifiedstrategies.com/end-of-month-effect-in-bitcoin/",
        "https://macrohive.com/hive-exclusives/does-turn-of-the-month-stock-trading-work-for-crypto",
        "Ariel (1987), 'A monthly effect in stock returns', JFE; Lakonishok & Smidt (1988), RFS",
    ],
    "rule": ("Janela do turn of the month (fonte: 'vento a favor' nos últimos dias do mês e nos primeiros do mês seguinte; a "
             "fonte não fixa os dias, então calibra-se a janela): comprado do início do dia UTC (dias_no_mês - before + 1) até "
             "o fechamento do dia 'after' do mês seguinte. Entrada na abertura D1 do primeiro dia da janela (decisão no "
             "fechamento do dia anterior, a data é calendário, não preço), saída na abertura do dia seguinte ao último da "
             "janela. side=both: vendido fora da janela (resto do mês), invertendo nas viradas. Stop de proteção k*ATR14 D1 "
             "(a fonte não tem). Difere do L17 (hora do dia): aqui é dia do mês."),
    "timeframes": ["D1"],
    "grid": {"before": [0, 1, 2, 3, 4, 5], "after": [1, 2, 3, 4, 5, 7], "k": [3.0, 5.0], "side": ["long", "both"]},
}


def _inwin(ts, before, after):
    d = ts.day.values
    dim = ts.days_in_month.values
    return (d > dim - before) | (d <= after)


def signals(df, p):
    t = df.index
    now = _inwin(t, p["before"], p["after"])
    nxt = _inwin(t + pd.Timedelta(days=1), p["before"], p["after"])  # calendário do dia seguinte
    start = (~now) & nxt
    end = now & (~nxt)
    entry = np.where(start, 1, 0)
    if p["side"] == "both":
        entry = np.where(end, -1, entry)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": end}
