"""TV78 - CM Stochastic POP (Jake Bernstein; ChrisMoody no TradingView): rompimento de zona do estocástico."""
import numpy as np

import indicators as ind

META = {
    "id": "TV78_stoch_pop",
    "name": "CM Stochastic POP (Bernstein/ChrisMoody): %K estoura a zona e segue o momento",
    "family": "momento",
    "round": 6,
    "origin": "TradingView comunidade (ChrisMoody)",
    "sources": [
        "https://github.com/deepentropy/lightweight-charts-indicators (src/community/stoch-pop-1.ts, port do 'CM_Stochastic POP Method 1' de ChrisMoody)",
        "https://www.luxalgo.com/library/concept/stochastic-pop.md (Bernstein; filtro ADX(14) < 20 de Steckler, TASC 2000)",
    ],
    "rule": ("%K = SMA5 do estocástico rápido de kLen. ChrisMoody: %K acima da linha superior U = compra, abaixo da inferior "
             "L = venda, entre elas = sem operação; as linhas são de entrada e de saída. Aqui: compra quando %K cruza acima de "
             "U, vende quando cruza abaixo de L = 100-U (zonas simétricas; o script usa 60/30 por padrão e Bernstein 80/20); "
             "a compra sai quando %K cruza de volta abaixo de U e a venda quando cruza acima de L. Filtro opcional de Steckler: "
             "só entra se o ADX14 do candle anterior < adx_max (100 = sem filtro). Sem stop no script: stop k*ATR14. "
             "Entrada na abertura seguinte."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"klen": [8, 14, 21], "up": [60, 70, 80], "adx_max": [20, 100], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def _adx(df):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("tv76_helper", Path(__file__).with_name("TV76_vzo.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.adx14(df)


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    hh, ll = ind.highest(h, p["klen"]), ind.lowest(l, p["klen"])
    with np.errstate(divide="ignore", invalid="ignore"):
        raw = 100 * (c - ll) / (hh - ll)
    raw[~np.isfinite(raw)] = np.nan
    k = ind.sma(raw, 5)
    U, L = float(p["up"]), 100.0 - p["up"]
    n = len(c)
    buy = ind.cross_above(k, np.full(n, U))
    sell = ind.cross_below(k, np.full(n, L))
    exl = ind.cross_below(k, np.full(n, U))
    exs = ind.cross_above(k, np.full(n, L))
    if p["adx_max"] < 100:
        ok = ind.prev(_adx(df)) < p["adx_max"]
        buy &= ok
        sell &= ok
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": exl, "exit_short": exs}
