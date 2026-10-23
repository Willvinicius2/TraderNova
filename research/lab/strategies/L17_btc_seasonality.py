"""L17 - Sazonalidade intradiária do bitcoin (Quantpedia: comprar 21:00 UTC, vender 23:00 UTC)."""
import numpy as np

import indicators as ind

META = {
    "id": "L17_btc_seasonality",
    "name": "Sazonalidade intradiária do BTC (21h-23h UTC)",
    "family": "tempo_volume",
    "sources": [
        "https://quantpedia.com/are-there-seasonal-intraday-or-overnight-anomalies-in-bitcoin/",
        "https://quantpedia.com/strategies/intraday-seasonality-in-bitcoin",
    ],
    "rule": ("Regra da fonte: comprado em BTC só na janela de horas de retorno mais forte (fonte: compra às 21:00 UTC e "
             "vende às 23:00 UTC, todos os dias; fora disso, caixa). Só compra. Entrada na abertura do candle H1 da hora "
             "'entry_hour', saída por tempo após 'hold' horas. Stop de proteção fixo 2*ATR14 (H1), que a fonte não tem; "
             "calibra-se só a janela (hora de entrada e duração)."),
    "timeframes": ["H1"],
    "grid": {"entry_hour": [19, 20, 21, 22], "hold": [1, 2, 3]},
}


def signals(df, p):
    hours = df.index.hour.values
    # decisão no fechamento do candle da hora anterior -> entrada na abertura do candle de entry_hour
    sig_hour = (p["entry_hour"] - 1) % 24
    entry = np.where(hours == sig_hour, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": 2.0 * a, "max_hold": int(p["hold"])}
