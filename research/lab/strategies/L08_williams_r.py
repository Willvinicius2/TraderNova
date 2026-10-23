"""Williams %R de Larry Williams, regra publicada por QuantifiedStrategies (entrada < -90, saída > -30 ou acima da máxima anterior)."""
import numpy as np

import indicators as ind

META = {
    "id": "L08_williams_r",
    "name": "Williams %R (-90 / -30)",
    "family": "reversao",
    "sources": [
        "https://quantifiedstrategies.substack.com/p/williams-r-trading-strategy-williams-203",
        "https://incrediblecharts.com/indicators/williams_percent_r.php",
    ],
    "rule": "%R(n) = -100*(máxima n - fechamento)/(máxima n - mínima n). Compra no fechamento quando %R < limiar de entrada (fonte: -90); "
            "sai quando fecha acima da máxima do candle anterior ou %R > limiar de saída (fonte: -30). Venda espelhada "
            "(%R > -100-entrada; sai abaixo da mínima anterior ou %R < -100-saída). Stop k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [2, 3, 5, 10], "ent": [-95, -90], "ext": [-40, -30, -20], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    hh, ll = ind.highest(h, p["n"]), ind.lowest(l, p["n"])
    with np.errstate(invalid="ignore", divide="ignore"):
        wr = np.where(hh > ll, -100 * (hh - c) / (hh - ll), np.nan)
        lg = wr < p["ent"]
        sh = wr > -100 - p["ent"]
        exl = (c > ind.prev(h)) | (wr > p["ext"])
        exs = (c < ind.prev(l)) | (wr < -100 - p["ext"])
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
