"""CM Williams Vix Fix (ChrisMoody, TradingView comunidade): compra no pico de medo."""
import numpy as np

import indicators as ind

META = {
    "id": "TV24_vix_fix",
    "name": "CM Williams Vix Fix (ChrisMoody): compra em pico de medo",
    "family": "reversao",
    "round": 3,
    "origin": "TradingView comunidade (ChrisMoody)",
    "sources": [
        "https://www.tradingview.com/script/og7JPrRA-CM-Williams-Vix-Fix-Finds-Market-Bottoms/",
        "https://www.luxalgo.com/library/indicator/og7JPrRA-cm-williams-vix-fix-finds-market-bottoms",
    ],
    "sourceNote": "TradingView inacessível; fórmula e padrões do Pine (pd=22, bbl=20, mult=2, lb=50, ph=0,85) conferidos via WebSearch (resumos do script e cópias republicadas). Larry Williams é o autor da ideia.",
    "rule": "Pine de ChrisMoody: wvf = (máxima dos fechamentos em pd - mínima)/máxima dos fechamentos em pd * 100; banda = SMA(wvf,bbl) + mult*desvio(wvf,bbl); "
            "rangeHigh = máx(wvf, lb)*ph. Pico de medo (barra verde) quando wvf >= banda ou wvf >= rangeHigh. "
            "Gatilho 'spike': compra no fechamento da primeira barra verde; 'fade': compra quando a sequência verde termina (primeira barra não verde após verde). "
            "O script é só indicador, sem saída nem stop: saída por tempo (hold candles) e stop de proteção k*ATR14. Só compra (o indicador só mede medo de queda).",
    "timeframes": ["H4", "D1"],
    "grid": {"pd": [22], "mult": [2.0], "ph": [0.85], "trigger": ["spike", "fade"], "hold": [5, 10, 20], "k": [2.0, 3.0, 4.0]},
}


def signals(df, p):
    c, l = df.close.values, df.low.values
    hc = ind.highest(c, p["pd"])
    wvf = (hc - l) / hc * 100
    upper = ind.sma(wvf, 20) + p["mult"] * ind.stdev(wvf, 20)
    rh = ind.highest(wvf, 50) * p["ph"]
    with np.errstate(invalid="ignore"):
        green = (wvf >= upper) | (wvf >= rh)
    pg = np.r_[False, green[:-1]]
    trig = (green & ~pg) if p["trigger"] == "spike" else (~green & pg)
    entry = np.where(trig, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "max_hold": p["hold"]}
