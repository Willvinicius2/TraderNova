"""Elder Impulse System (Alexander Elder) como estratégia: entra quando o candle fica verde/vermelho."""
import numpy as np

import indicators as ind

META = {
    "id": "TV12_elder_impulse",
    "name": "Elder Impulse System (EMA13 + histograma MACD)",
    "family": "tendencia",
    "round": 2,
    "origin": "TradingView comunidade (LazyBear e outros, script Jut6HUJb; regra de Alexander Elder)",
    "sources": [
        "https://www.tradingview.com/script/Jut6HUJb/",
        "https://www.luxalgo.com/library/indicator/elder-impulse-system/",
        "https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-types/elder-impulse-system",
    ],
    "rule": ("Impulso de Elder: verde quando a EMA(n) sobe e o histograma MACD(12,26,9) sobe no mesmo candle; vermelho quando os dois "
             "caem; azul nos demais. Compra no primeiro candle verde após um não-verde; vende (side=both) no primeiro vermelho após um "
             "não-vermelho. Saída: exit='blue' sai quando o candle deixa de ser da cor da posição; exit='red' só quando fica da cor oposta. "
             "O script do TradingView é só indicador (sem stop): stop de proteção k*ATR14 (exigido pelo motor)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"ema_n": [8, 13, 21, 34], "exit": ["blue", "red"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def impulse(df, n):
    c = df.close.values
    e = ind.ema(c, n)
    macd = ind.ema(c, 12) - ind.ema(c, 26)
    hist = macd - ind.ema(macd, 9)
    eu, hu = e > ind.prev(e), hist > ind.prev(hist)
    ed, hd = e < ind.prev(e), hist < ind.prev(hist)
    col = np.where(eu & hu, 1, np.where(ed & hd, -1, 0))
    col[np.isnan(hist) | np.isnan(ind.prev(hist))] = 0
    return col


def signals(df, p):
    col = impulse(df, p["ema_n"])
    pc = np.r_[0, col[:-1]]
    green = (col == 1) & (pc != 1)
    red = (col == -1) & (pc != -1)
    entry = np.where(green, 1, np.where(red, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    if p["exit"] == "blue":
        exl, exs = col != 1, col != -1
    else:
        exl, exs = col == -1, col == 1
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
