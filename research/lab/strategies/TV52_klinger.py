"""Klinger Volume Oscillator (Stephen Klinger; Pine de everget). Cruzamento KVO x sinal com filtro de tendência opcional."""
import numpy as np

import indicators as ind

META = {
    "id": "TV52_klinger",
    "name": "Klinger Volume Oscillator (everget): KVO cruza o sinal, filtro EMA100 opcional",
    "family": "volume",
    "round": 5,
    "origin": "TradingView comunidade (everget; Stephen J. Klinger, Stocks & Commodities 1997)",
    "sources": [
        "https://github.com/everget/tradingview-pinescript-indicators/blob/master/volume/klinger_volume_oscillator.pine",
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/klinger-volume-oscillator",
        "https://de.tradingview.com/scripts/klinger/",
    ],
    "sourceNote": "TradingView não abre no WebFetch; código Pine copiado do repositório do autor (everget, clonado em /home/user/labdata/pine). "
                  "O indicador não traz regra de trade; usamos a da FILA/StockCharts (cruzamento do sinal EMA13, Klinger sugeria "
                  "operar a favor da tendência dada por uma média de 100 períodos).",
    "rule": "trend = sinal da variação do hlc3 (mantém o anterior se zero); dm = H-L; cm acumula dm enquanto trend não muda "
            "(reinicia em dm+dm[1] na virada); VF = 100*vol*trend*|2*dm/cm-1|; KVO = EMA34(VF)-EMA55(VF); sinal = EMA(sig) do KVO. "
            "Compra quando KVO cruza acima do sinal, vende (side=both) quando cruza abaixo; sai no cruzamento oposto. "
            "Filtro 'ema100': compra só com fechamento acima da EMA100 e vende só abaixo. Sem stop no original: stop k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"sig": [8, 13, 21], "filt": ["none", "ema100"], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def kvo(df, fast=34, slow=55):
    h, l, c, v = (df[k].values for k in ("high", "low", "close", "volume"))
    hlc3 = (h + l + c) / 3
    n = len(c)
    dm = h - l
    trend = np.zeros(n)
    cm = np.zeros(n)
    for i in range(1, n):
        mom = hlc3[i] - hlc3[i - 1]
        trend[i] = 1.0 if mom > 0 else (-1.0 if mom < 0 else trend[i - 1])
        cm[i] = cm[i - 1] + dm[i] if trend[i] == trend[i - 1] else dm[i] + dm[i - 1]
    with np.errstate(divide="ignore", invalid="ignore"):
        vf = np.where(cm != 0, 100 * v * trend * np.abs(2 * dm / np.where(cm != 0, cm, 1) - 1), 0.0)
    return ind.ema(vf, fast) - ind.ema(vf, slow)


def signals(df, p):
    k = kvo(df)
    s = ind.ema(k, p["sig"])
    up, dn = ind.cross_above(k, s), ind.cross_below(k, s)
    c = df.close.values
    bu, bd = up.copy(), dn.copy()
    if p["filt"] == "ema100":
        t = ind.ema(c, 100)
        bu &= c > t
        bd &= c < t
    entry = np.where(bu, 1, np.where(bd, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
