"""Internal Bar Strength (IBS) = (close-low)/(high-low)."""
import numpy as np

import indicators as ind

META = {
    "id": "L06_ibs",
    "name": "Internal Bar Strength (IBS)",
    "family": "reversao",
    "sources": [
        "https://quantifiedstrategies.substack.com/p/the-internal-bar-strength-ibs-indicator",
        "https://doc.stocksharp.com/en/designer-gallery/Internal_Bar_Strength_IBS_Mean_Reversion",
    ],
    "rule": "IBS=(fechamento-mínima)/(máxima-mínima) do candle. Compra no fechamento quando IBS < limiar baixo (fonte: 0,2); "
            "sai quando IBS > limiar alto (fonte: 0,8). Venda espelhada (IBS > 1-baixo, sai com IBS < 1-alto). Stop k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"lo": [0.1, 0.15, 0.2, 0.25], "hi": [0.7, 0.8, 0.9], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    rng = h - l
    with np.errstate(invalid="ignore", divide="ignore"):
        ibs = np.where(rng > 0, (c - l) / rng, np.nan)
        lg = ibs < p["lo"]
        sh = ibs > 1 - p["lo"]
        exl = ibs > p["hi"]
        exs = ibs < 1 - p["hi"]
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
