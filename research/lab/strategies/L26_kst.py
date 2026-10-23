"""L26 - Know Sure Thing (Martin Pring)."""
import numpy as np

import indicators as ind

META = {
    "id": "L26_kst",
    "name": "Know Sure Thing (Pring): KST cruza a linha de sinal",
    "family": "momento",
    "round": 8,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://www.optuma.com/kb/tools/price/pring-know-sure-thing-kst",
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/know-sure-thing-kst (não abriu; citado pelo nome)",
        "Martin Pring, 'Technical Analysis Explained' (KST de curto prazo/diário)",
    ],
    "rule": ("KST diário de Pring: KST = 1*SMA10(ROC10) + 2*SMA10(ROC15) + 3*SMA10(ROC20) + 4*SMA15(ROC30); sinal = SMA9(KST) "
             "(todos os períodos multiplicados por 'scale'). Compra quando o KST cruza acima do sinal (histograma cruza acima "
             "de zero); vende (side=both) quando cruza abaixo; o cruzamento oposto sempre fecha. Filtro opcional 'zero' de Pring "
             "(KST acima de zero confirma alta): zf=1 exige KST>0 na compra e KST<0 "
             "na venda (cruzamento a favor da tendência do próprio KST). Filtro de regime opcional EMA(trend). "
             "Sem stop no original: stop de proteção k*ATR14. Entrada na abertura seguinte."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"scale": [1, 2, 4], "zf": [0, 1], "trend": [0, 200], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def roc(c, n):
    return 100.0 * (c / ind.prev(c, n) - 1.0)


def signals(df, p):
    c = df.close.values.astype(float)
    s = p["scale"]
    kst = (ind.sma(roc(c, 10 * s), 10 * s) + 2 * ind.sma(roc(c, 15 * s), 10 * s)
           + 3 * ind.sma(roc(c, 20 * s), 10 * s) + 4 * ind.sma(roc(c, 30 * s), 15 * s))
    sig = ind.sma(kst, 9 * s)
    up, dn = ind.cross_above(kst, sig), ind.cross_below(kst, sig)
    buy, sell = up.copy(), dn.copy()
    if p["zf"]:
        buy &= kst > 0
        sell &= kst < 0
    if p["trend"]:
        e = ind.ema(c, p["trend"])
        buy &= c > e
        sell &= c < e
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": dn, "exit_short": up}
