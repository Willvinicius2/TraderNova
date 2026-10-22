"""Negative Volume Index (Paul Dysart / Norman Fosback; Pine de everget). NVI contra a própria EMA."""
import numpy as np

import indicators as ind

META = {
    "id": "TV55_nvi",
    "name": "Negative Volume Index (everget): NVI cruza a própria EMA",
    "family": "volume",
    "round": 5,
    "origin": "TradingView comunidade (everget; Norman Fosback, Stock Market Logic, 1976)",
    "sources": [
        "https://github.com/everget/tradingview-pinescript-indicators/blob/master/volume/negative_volume_index.pine",
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/negative-volume-index-nvi",
        "https://en.wikipedia.org/wiki/Negative_volume_index",
    ],
    "sourceNote": "Código Pine do autor (everget, clonado em /home/user/labdata/pine). Fosback: NVI acima da média de 1 ano "
                  "(255 dias) indica mercado de alta. Na grade, o período da EMA vale em candles do tempo gráfico.",
    "rule": "NVI começa em 100 e só muda nos candles com volume menor que o anterior: NVI = NVI[1]*C/C[1]; senão repete. "
            "Sinal = EMA(sig) do NVI. Compra quando o NVI cruza acima do sinal; vende (side=both) quando cruza abaixo; sai no "
            "cruzamento oposto. Sem stop na fonte: stop k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"sig": [100, 255, 400], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def nvi(df):
    c, v = df.close.values, df.volume.values
    r = np.ones(len(c))
    dv = np.diff(v)
    r[1:] = np.where(dv < 0, c[1:] / c[:-1], 1.0)
    return 100 * np.cumprod(r)


def signals(df, p):
    x = nvi(df)
    s = ind.ema(x, p["sig"])
    up, dn = ind.cross_above(x, s), ind.cross_below(x, s)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
