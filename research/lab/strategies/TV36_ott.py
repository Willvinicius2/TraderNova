"""TV36 - Optimized Trend Tracker (OTT), Pine de KivancOzbilgic (criação de Anıl Özekşi)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV36_ott",
    "name": "Optimized Trend Tracker (OTT): linha de suporte VAR cruza a OTT",
    "family": "tendencia",
    "round": 4,
    "origin": "TradingView comunidade (KivancOzbilgic; indicador criado por Anıl Özekşi)",
    "sources": [
        "https://www.tradingview.com/script/zVhoDQME/",
        "Código: github.com/deepentropy/lightweight-charts-indicators src/community/optimized-trend-tracker.ts (port fiel do Pine)",
    ],
    "rule": ("Pine (fonte fechamento, período 2, percentual 1,4): VAR = média VIDYA com alfa 2/(n+1) multiplicado por |CMO de 9 candles|; "
             "longStop = VAR*(1-pct), só sobe enquanto VAR > longStop anterior; shortStop = VAR*(1+pct), só desce; direção vira quando a VAR "
             "atravessa o stop oposto; MT = stop da direção; OTT = MT*(200±pct)/200 (+ se VAR>MT). Sinal padrão do script (showsignalsk): "
             "compra quando a VAR (linha de suporte) cruza acima da OTT de 2 candles atrás, venda no cruzamento abaixo. Sai/inverte no "
             "sinal oposto; side=long só compra. Sem stop no script: stop de proteção k*ATR14 (Wilder)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"period": [2, 5, 10, 20], "percent": [0.7, 1.4, 2.8, 5.0], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def ott_lines(c, period, percent):
    n = len(c)
    a = 2.0 / (period + 1)
    d = np.diff(c, prepend=np.nan)
    ud = np.where(d > 0, d, 0.0)
    dd = np.where(d < 0, -d, 0.0)
    sud = ind.sma(ud, 9) * 9
    sdd = ind.sma(dd, 9) * 9
    with np.errstate(divide="ignore", invalid="ignore"):
        cmo = (sud - sdd) / (sud + sdd)
    cmo = np.where(np.isfinite(cmo), cmo, 0.0)
    var = np.zeros(n)
    for i in range(n):
        k = a * abs(cmo[i])
        var[i] = k * c[i] + (1 - k) * (var[i - 1] if i else 0.0)
    fark = var * percent * 0.01
    ls = var - fark
    ss = var + fark
    dr = np.ones(n)
    ott = np.zeros(n)
    for i in range(n):
        if i:
            if var[i] > ls[i - 1]:
                ls[i] = max(ls[i], ls[i - 1])
            if var[i] < ss[i - 1]:
                ss[i] = min(ss[i], ss[i - 1])
            dr[i] = dr[i - 1]
            if dr[i - 1] == -1 and var[i] > ss[i - 1]:
                dr[i] = 1
            elif dr[i - 1] == 1 and var[i] < ls[i - 1]:
                dr[i] = -1
        mt = ls[i] if dr[i] == 1 else ss[i]
        ott[i] = mt * (200 + percent) / 200 if var[i] > mt else mt * (200 - percent) / 200
    return var, ott


def signals(df, p):
    c = df.close.values
    var, ott = ott_lines(c, p["period"], p["percent"])
    ott2 = ind.prev(ott, 2)
    up = ind.cross_above(var, ott2)
    dn = ind.cross_below(var, ott2)
    up[:200] = False
    dn[:200] = False
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
