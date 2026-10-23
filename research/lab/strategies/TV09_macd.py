"""TV09 - MACD Strategy (estratégia embutida do TradingView).

Pine original (embutido): MACD = EMA(close,fast) - EMA(close,slow); aMACD = EMA(MACD,sinal);
delta = MACD - aMACD; ta.crossover(delta,0) -> strategy.entry long; ta.crossunder(delta,0) -> strategy.entry short.
É sempre posicionada (inverte a mão). O Pine não tem stop: aqui há stop de proteção k*ATR(14) exigido pelo motor.
"""
import numpy as np

import indicators as ind

META = {
    "id": "TV09_macd",
    "name": "MACD Strategy (TradingView)",
    "family": "tendencia",
    "round": 2,
    "origin": "TradingView embutida",
    "sources": [
        "https://www.tradingview.com/support/folders/43000587406-built-in-strategies/",
        "https://www.oanda.jp/lab-education/tradingviewstrategy/strategy/pine_script_macd_strategy/",
    ],
    "rule": ("Histograma do MACD (MACD - sinal, médias exponenciais rápida/lenta/sinal) cruza acima de zero: compra; "
             "cruza abaixo de zero: vende (inverte a posição, como o Pine embutido). Entrada na abertura seguinte. "
             "O Pine não tem stop; usamos stop de proteção k*ATR(14). No modo só compra, o cruzamento para baixo fecha a compra."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"fast": [8, 12, 16], "slow": [21, 26, 34], "signal": [7, 9, 11], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    c = df.close.values
    macd = ind.ema(c, p["fast"]) - ind.ema(c, p["slow"])
    sig = ind.ema(macd, p["signal"])
    delta = macd - sig
    zero = np.zeros(len(c))
    up = ind.cross_above(delta, zero)
    dn = ind.cross_below(delta, zero)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": dn, "exit_short": up}
