"""Ease of Movement (Richard W. Arms Jr.; indicador embutido do TradingView). Cruzamento do zero."""
import numpy as np

import indicators as ind

META = {
    "id": "TV54_eom",
    "name": "Ease of Movement (Arms): SMA do EMV cruza o zero",
    "family": "volume",
    "round": 5,
    "origin": "TradingView embutida (Ease of Movement; Richard W. Arms Jr.)",
    "sources": [
        "https://in.tradingview.com/support/solutions/43000502256",
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/ease-of-movement-emv",
        "https://github.com/deepentropy/lightweight-charts-indicators/blob/main/src/standard/ease-of-movement.ts",
    ],
    "sourceNote": "Fórmula do port do indicador embutido (deepentropy, clonado em /home/user/labdata/pine): "
                  "EOM = SMA(n) de Δhl2 * (H-L)/(vol/divisor). O divisor (10000) não muda o sinal. A regra 'compra acima de 0, "
                  "vende abaixo' é a leitura clássica descrita no Help Center e na StockCharts.",
    "rule": "EMV = (hl2 - hl2[1]) * (H-L) / volume (candle sem volume = 0); EOM = SMA(n) do EMV. Compra quando o EOM cruza "
            "acima de 0, vende (side=both) quando cruza abaixo; sai no cruzamento oposto. Filtro 'sma200': compra só acima "
            "da SMA200 e vende só abaixo. Sem stop na fonte: stop k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [7, 14, 28], "filt": ["none", "sma200"], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def eom(df, n):
    h, l, v = df.high.values, df.low.values, df.volume.values
    hl2 = (h + l) / 2
    d = hl2 - ind.prev(hl2)
    with np.errstate(divide="ignore", invalid="ignore"):
        raw = np.where(v > 0, d * (h - l) / np.where(v > 0, v, 1), 0.0)
    raw[0] = 0.0
    return ind.sma(raw, n)


def signals(df, p):
    e = eom(df, p["n"])
    z = np.zeros(len(e))
    up, dn = ind.cross_above(e, z), ind.cross_below(e, z)
    c = df.close.values
    bu, bd = up.copy(), dn.copy()
    if p["filt"] == "sma200":
        t = ind.sma(c, 200)
        bu &= c > t
        bd &= c < t
    entry = np.where(bu, 1, np.where(bd, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
