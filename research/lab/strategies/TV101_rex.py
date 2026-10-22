"""Rex Oscillator (comunidade NNFX / MT4): TVB = 3*fech - (mín+abert+máx), suavizado, contra a linha de sinal."""
import numpy as np

import indicators as ind

META = {
    "id": "TV101_rex",
    "name": "Rex Oscillator: Rex (média do TVB) cruza a linha de sinal",
    "family": "momento",
    "round": 7,
    "origin": "TradingView comunidade (REX Oscillator; indicador MT4 de origem NNFX)",
    "sources": [
        "https://www.tradingview.com/script/AUi1mgFZ-REX-Oscillator",
        "https://www.prorealcode.com/topic/rex-indicator/",
        "https://www.mql5.com/en/code/21247",
    ],
    "sourceNote": "TradingView não abre no WebFetch; fórmula e padrões (média 14, sinal 14, SMA/EMA/SMMA/LWMA) do tópico ProRealCode, "
                  "que traz o código MQL. A regra de cruzamento Rex x sinal é a da linha da FILA (uso NNFX como confirmação).",
    "rule": "TVB = 3*fech - (mín + abert + máx); Rex = média(TVB, smooth); Sinal = média(Rex, signal) (SMA ou EMA). "
            "Compra quando Rex cruza acima do sinal; vende (side=both) quando cruza abaixo; inverte/sai no cruzamento oposto. "
            "trend>0: compra só com fechamento acima da EMA(trend) e venda só abaixo. Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"smooth": [8, 14, 21], "signal": [8, 14], "ma": ["sma", "ema"], "trend": [0, 200],
             "k": [2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    tvb = 3 * c - (l + o + h)
    f = ind.sma if p["ma"] == "sma" else ind.ema
    rex = f(tvb, p["smooth"])
    sig = f(rex, p["signal"])
    up = ind.cross_above(rex, sig)
    dn = ind.cross_below(rex, sig)
    lg, sh = up.copy(), dn.copy()
    if p["trend"]:
        e = ind.ema(c, p["trend"])
        with np.errstate(invalid="ignore"):
            lg &= c > e
            sh &= c < e
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
