"""Balance of Power (Igor Livshin/Levshin, TASC ago/2001)."""
import numpy as np

import indicators as ind

META = {
    "id": "L40_balance_of_power",
    "name": "Balance of Power (Livshin) suavizado: cruzamento de nível com filtro de tendência",
    "family": "momentum",
    "round": 9,
    "origin": "FILA.md (autor)",
    "sources": [
        "Igor Livshin, 'Balance of Market Power', Technical Analysis of Stocks & Commodities, ago/2001",
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/balance-of-power-bop",
        "https://www.luxalgo.com/library/concept/balance-of-power.md",
        "TradingView embutido BOP ((close-open)/(high-low)), port em github.com/deepentropy/lightweight-charts-indicators src/standard/bop.ts",
    ],
    "sourceNote": ("BOP = (C-O)/(H-L); o autor recomenda suavizar com SMA de 14; cruzar acima de zero = compra, abaixo = venda "
                   "(StockCharts). A triagem-v1 rodou o BOP cru (sem suavizar) x zero, que reprova por excesso de operações; aqui é o BOP "
                   "suavizado como o autor recomenda, com limiar opcional e filtro de tendência EMA. Sem stop no original: k*ATR14."),
    "rule": ("B = SMA(n) de (C-O)/(H-L) (0 quando H=L). Compra quando B cruza acima de +thr (se trend>0: fechamento acima da EMA(trend)); "
             "vende (both) quando cruza abaixo de -thr (fechamento abaixo da EMA). Sai da compra quando B cruza abaixo de 0 (venda: acima de 0). "
             "Stop k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [14, 28, 50], "thr": [0.0, 0.05, 0.1], "trend": [0, 200], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    rng = h - l
    with np.errstate(invalid="ignore", divide="ignore"):
        b = np.where(rng > 0, (c - o) / rng, 0.0)
    B = ind.sma(b, p["n"])
    z = np.zeros(len(c))
    lg = ind.cross_above(B, z + p["thr"])
    sh = ind.cross_below(B, z - p["thr"])
    if p["trend"]:
        e = ind.ema(c, p["trend"])
        lg &= c > e
        sh &= c < e
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14),
            "exit_long": ind.cross_below(B, z), "exit_short": ind.cross_above(B, z)}
