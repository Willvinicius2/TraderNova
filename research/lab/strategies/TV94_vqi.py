"""TV94 - Volatility Quality Index (Thomas Stridsman), versão Volatility Quality [Alpha Extract]."""
import numpy as np

import indicators as ind

META = {
    "id": "TV94_vqi",
    "name": "Volatility Quality [Alpha Extract]: VQI vira e cruza a própria média",
    "family": "tendencia",
    "round": 7,
    "origin": "TradingView comunidade (AlphaExtract; ideia de Thomas Stridsman, Trading Systems That Work, 2000)",
    "sources": [
        "https://github.com/deepentropy/lightweight-charts-indicators/blob/main/src/community/volatility-quality.ts",
        "https://www.tradingview.com/script/MbAO4zo0-Indicator-Volatility-Quality-Index-VQI",
        "https://docs.gehtsoftusa.com/fxcodebase-backup/backup/custom-indicators/v/volatility-quality-index-vqi/",
    ],
    "sourceNote": "Fórmula do port fiel (MPL 2.0) do Pine 'Volatility Quality [Alpha Extract]' em deepentropy/lightweight-charts-indicators: "
                  "true range com o sinal da vela (+1 alta, -1 baixa, 0 doji), EMA(len), EMA(suav), normalizado para -100..100 pela máxima e "
                  "mínima de 200 candles; a linha fica verde >= 0 e vermelha < 0. O script é só indicador. Regra da fila: compra quando o VQI "
                  "vira para cima e cruza a própria média (média = SMA(9), como no VQI clássico de Stridsman com média curta). Modo 'zero' usa "
                  "a troca de cor do original (cruzar 0). Sem stop no original: stop de proteção k*ATR14.",
    "rule": "VQI = normalização(-100..100, 200 candles) de EMA(suav) de EMA(len) de TR*sinal(fech-abert). Modo 'media': compra quando o VQI sobe "
            "(VQI > VQI anterior) e cruza acima da SMA(9) do VQI; venda espelhada; sai no cruzamento oposto. Modo 'zero': compra quando o VQI cruza "
            "acima de 0, vende abaixo de 0; sai no cruzamento oposto. Stop k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"len": [9, 14, 21], "suav": [3, 5, 8], "modo": ["media", "zero"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def vqi(df, n, s, norm=200):
    h, l, c, o = df.high.values, df.low.values, df.close.values, df.open.values
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    tr[0] = h[0] - l[0]
    d = np.where(c - o > 1e-10, 1.0, np.where(o - c > 1e-10, -1.0, 0.0))
    sm = ind.ema(ind.ema(tr * d, n), s)
    hi, lo = ind.highest(sm, norm), ind.lowest(sm, norm)
    rng = hi - lo
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.where(rng > 1e-10, ((sm - lo) / rng - 0.5) * 200, sm)
    return out


def signals(df, p):
    v = vqi(df, p["len"], p["suav"])
    if p["modo"] == "media":
        m = ind.sma(v, 9)
        rising, falling = v > ind.prev(v), v < ind.prev(v)
        up = ind.cross_above(v, m) & rising
        dn = ind.cross_below(v, m) & falling
        exl, exs = ind.cross_below(v, m), ind.cross_above(v, m)
    else:
        z = np.zeros(len(v))
        up, dn = ind.cross_above(v, z), ind.cross_below(v, z)
        exl, exs = dn, up
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
