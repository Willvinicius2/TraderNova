"""TV56 - Elder-Ray (Bull/Bear Power) em pullback (Alexander Elder; indicador embutido "Bull Bear Power" do TradingView)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV56_elder_ray",
    "name": "Elder-Ray: pullback com Bear/Bull Power",
    "family": "tendencia",
    "round": 5,
    "origin": "TradingView embutida (Bull Bear Power; regra de Alexander Elder, Trading for a Living, 1993)",
    "sources": [
        "https://www.daytrading.com/elder-ray-index",
        "https://doc.stocksharp.com/en/topics/api/indicators/list_of_indicators/elder_ray",
        "https://www.luxalgo.com/library/indicator/elder-ray/",
        "https://github.com/deepentropy/lightweight-charts-indicators/blob/main/src/standard/bull-bear-power.ts",
    ],
    "sourceNote": "TradingView não abre no WebFetch; fórmula do port do indicador embutido (deepentropy, standard/bull-bear-power.ts: "
                  "Bull = máxima - EMA, Bear = mínima - EMA) e regra de compra/venda de Elder resumida em daytrading.com e StockSharp.",
    "rule": ("Bull Power = máxima - EMA(n); Bear Power = mínima - EMA(n). Compra quando a EMA(n) sobe (EMA > EMA anterior) e o Bear Power "
             "está negativo mas maior que no candle anterior (pullback perdendo força). Venda espelhada: EMA caindo e Bull Power positivo "
             "mas menor que no candle anterior. Saída exit='ema': quando a EMA vira contra a posição; exit='opp': só no sinal oposto (inversão). "
             "O indicador não tem stop: stop de proteção k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [13, 21, 34], "exit": ["ema", "opp"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    e = ind.ema(c, p["n"])
    pe = ind.prev(e)
    bull, bear = h - e, l - e
    up, dn = e > pe, e < pe
    buy = up & (bear < 0) & (bear > ind.prev(bear))
    sell = dn & (bull > 0) & (bull < ind.prev(bull))
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    out = {"entry": entry, "stop": p["k"] * ind.atr(df, 14)}
    if p["exit"] == "ema":
        out["exit_long"], out["exit_short"] = dn, up
    else:
        out["exit_long"], out["exit_short"] = sell, buy
    return out
