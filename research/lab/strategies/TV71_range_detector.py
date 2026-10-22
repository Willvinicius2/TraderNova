"""Range Detector (LuxAlgo): rompimento do range detectado."""
import numpy as np

import indicators as ind

META = {
    "id": "TV71_range_detector",
    "name": "Range Detector (LuxAlgo)",
    "family": "rompimento",
    "round": 6,
    "origin": "TradingView comunidade (LuxAlgo)",
    "sources": [
        "https://www.tradingview.com/script/QOuZIuvH-Range-Detector-LuxAlgo/",
        "github.com/deepentropy/lightweight-charts-indicators src/community/range-detector.ts (tradução do Pine)",
    ],
    "rule": ("Pine 'Range Detector': ma = SMA(close,len), faixa = ATR(atrLen)*mult. Há range quando nenhum dos len últimos fechamentos "
             "fica a mais de faixa da ma de hoje (count==0) e no candle anterior havia (count[1]!=0): se o range novo encosta no "
             "anterior, a caixa é ampliada; senão nova caixa topo=ma+faixa, fundo=ma-faixa. Compra quando o fechamento passa acima "
             "do topo da última caixa (estado os vira 1); vende quando passa abaixo do fundo (os vira -1). Sem saída no Pine: stop "
             "inicial e móvel k*ATR14, sinal oposto inverte. Entrada na abertura seguinte."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"length": [10, 15, 20, 30], "mult": [0.75, 1.0, 1.25], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}


def range_det(df, L, mult, atrLen=500):
    c = df.close.values
    n = len(c)
    a = ind.atr(df, atrLen) * mult
    ma = ind.sma(c, L)
    cnt = np.full(n, -1)
    for i in range(L - 1, n):
        if np.isnan(a[i]) or np.isnan(ma[i]):
            continue
        cnt[i] = int((np.abs(c[i - L + 1:i + 1] - ma[i]) > a[i]).sum())
    top = bot = np.nan
    right = -1
    os_ = 0
    osa = np.zeros(n, int)
    for i in range(n):
        if cnt[i] == 0 and i > 0 and cnt[i - 1] > 0:
            if i - L <= right and not np.isnan(top):
                top = max(ma[i] + a[i], top); bot = min(ma[i] - a[i], bot)
            else:
                top = ma[i] + a[i]; bot = ma[i] - a[i]; os_ = 0
            right = i
        elif cnt[i] == 0:
            right = i
        if not np.isnan(top):
            if c[i] > top:
                os_ = 1
            elif c[i] < bot:
                os_ = -1
        osa[i] = os_
    po = np.r_[0, osa[:-1]]
    return (osa == 1) & (po != 1), (osa == -1) & (po != -1)


_cache = {}


def signals(df, p):
    key = (id(df), len(df), p["length"], p["mult"])
    if key not in _cache:
        _cache[key] = range_det(df, p["length"], p["mult"])
    up, dn = _cache[key]
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "trail": p["k"] * a}
