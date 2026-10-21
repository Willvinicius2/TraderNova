"""SSL Channel (ErwinBeckers): virada do canal de médias de máximas/mínimas."""
import numpy as np

import indicators as ind

META = {
    "id": "TV15_ssl_channel",
    "name": "SSL Channel (ErwinBeckers)",
    "family": "tendencia",
    "round": 2,
    "origin": "TradingView comunidade (ErwinBeckers)",
    "sources": [
        "https://tradingview.com/script/sm4zbLHp-SSL-Channel-w-alert",
        "https://www.tradingview.com/script/wC5DA3Wo-SSL-Channel-MTF",
        "https://community.tradovate.com/t/ssl-channel-chart-indicator/1173",
    ],
    "rule": ("smaHigh = SMA(máximas, len), smaLow = SMA(mínimas, len). Hlv = 1 quando o fechamento passa acima de smaHigh, -1 quando "
             "passa abaixo de smaLow, senão mantém. sslUp/sslDown trocam de lugar quando Hlv vira (as linhas se cruzam). Compra quando "
             "Hlv vira para 1; vende (side=both) quando vira para -1; sai na virada oposta. Script sem stop: stop de proteção k*ATR14. "
             "Página original no TradingView inacessível ao WebFetch; código v3 citado no fórum da Tradovate (resumo de busca)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"len": [5, 8, 10, 13, 20, 30], "k": [1.5, 2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    h, l, c = df.high.values, df.low.values, df.close.values
    sh, sl = ind.sma(h, p["len"]), ind.sma(l, p["len"])
    n = len(c)
    hlv = np.zeros(n, dtype=int)
    for i in range(n):
        hlv[i] = 1 if c[i] > sh[i] else (-1 if c[i] < sl[i] else (hlv[i - 1] if i else 0))
    ph = np.r_[0, hlv[:-1]]
    up = (hlv == 1) & (ph == -1)
    dn = (hlv == -1) & (ph == 1)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
