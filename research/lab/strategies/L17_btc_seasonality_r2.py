"""L17 r2 - Sazonalidade intradiária do BTC só em regime de alta (preço acima da média de N dias)."""
import numpy as np

import indicators as ind

META = {
    "id": "L17_btc_seasonality_r2",
    "refines": "L17_btc_seasonality",
    "refinement": ("r1 (só dias fortes) continuou negativo: o efeito bruto (~0,10% por janela) é menor que o custo de 0,20% "
                   "ida e volta. Segunda e última tentativa: operar a janela só em regime de alta (fechamento acima da média "
                   "de N dias), onde o retorno noturno do BTC tende a ser maior, cortando operações em mercado de baixa."),
    "name": "Sazonalidade intradiária do BTC (21h-23h UTC) em regime de alta",
    "family": "tempo_volume",
    "sources": [
        "https://quantpedia.com/are-there-seasonal-intraday-or-overnight-anomalies-in-bitcoin/",
        "https://quantpedia.com/strategies/intraday-seasonality-in-bitcoin",
    ],
    "rule": ("Comprado na janela da fonte (entrada na abertura da hora 'entry_hour' UTC, saída após 'hold' horas), só quando "
             "o fechamento H1 está acima da SMA de 'trend_days' dias (24*N candles H1). Só compra. Stop 2*ATR14 H1."),
    "timeframes": ["H1"],
    "grid": {"entry_hour": [20, 21, 22], "hold": [1, 2, 3], "trend_days": [10, 20, 50]},
}


def signals(df, p):
    c = df.close.values
    hours = df.index.hour.values
    sig_hour = (p["entry_hour"] - 1) % 24
    t = ind.sma(c, 24 * p["trend_days"])
    entry = np.where((hours == sig_hour) & (c > t), 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": 2.0 * a, "max_hold": int(p["hold"])}
