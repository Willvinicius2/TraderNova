"""L17 r1 - Sazonalidade intradiária do BTC só nos dias da semana mais fortes citados pela fonte."""
import numpy as np

import indicators as ind

META = {
    "id": "L17_btc_seasonality_r1",
    "refines": "L17_btc_seasonality",
    "refinement": ("No desenvolvimento a janela 21h-23h tem retorno bruto positivo (~+0,05R/operação sem custo), mas o custo de "
                   "0,10% por lado (0,20% ida e volta) é maior que o efeito. Restringe aos dias que a atualização da Quantpedia "
                   "aponta como mais fortes (sexta, depois quinta, depois sábado/domingo) para operar menos e só onde o efeito "
                   "seria maior."),
    "name": "Sazonalidade intradiária do BTC (21h-23h UTC) só em dias fortes",
    "family": "tempo_volume",
    "sources": [
        "https://quantpedia.com/are-there-seasonal-intraday-or-overnight-anomalies-in-bitcoin/",
        "https://quantpedia.com/the-seasonality-of-bitcoin/",
    ],
    "rule": ("Comprado na janela intradiária da fonte (entrada na abertura da hora 'entry_hour' UTC, saída após 'hold' horas), "
             "mas só nos dias citados como mais fortes: 'fri' = sexta; 'thu_fri' = quinta e sexta; 'thu_sun' = quinta a "
             "domingo. Só compra. Stop de proteção 2*ATR14 H1."),
    "timeframes": ["H1"],
    "grid": {"entry_hour": [20, 21, 22], "hold": [1, 2, 3], "days": ["fri", "thu_fri", "thu_sun"]},
}

DAYS = {"fri": {4}, "thu_fri": {3, 4}, "thu_sun": {3, 4, 5, 6}}


def signals(df, p):
    hours = df.index.hour.values
    sig_hour = (p["entry_hour"] - 1) % 24
    # dia da semana do candle de entrada (entry_hour); se entry_hour=0 seria o dia seguinte, aqui sempre >= 20
    dow = df.index.dayofweek.values
    ok_day = np.isin(dow, list(DAYS[p["days"]]))
    entry = np.where((hours == sig_hour) & ok_day, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": 2.0 * a, "max_hold": int(p["hold"])}
