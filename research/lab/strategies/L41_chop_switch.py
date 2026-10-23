"""L41 - Choppiness Index (E.W. Dreiss) como interruptor tendência/lateral.

Diferença do L36_hurst_switch: lá o regime vem do expoente de Hurst (R/S) e as regras são rompimento de Donchian /
z-score. Aqui o regime vem do CHOP de Dreiss e o sinal de tendência é o próprio CHOP saindo da congestão
(cruzar abaixo do limiar de tendência), com direção dada pelo deslocamento líquido da janela; no regime lateral a
regra é a volta do RSI(14) das zonas 30/70 com alvo na média.
"""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L41_chop_switch",
    "name": "Choppiness Index (Dreiss) como interruptor tendência/lateral",
    "family": "regime",
    "round": 9,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://www.luxalgo.com/library/concept/choppiness-index/ (fórmula de Dreiss: 100*log10(soma TR n / (máx n - mín n))/log10(n), n=14; >61,8 congestão, <38,2 tendência; o CHOP não dá direção, que vem da estrutura)",
        "https://www.tradingview.com/support/solutions/43000501980/ (Choppiness Index no Help Center do TradingView, mesmos limiares 61,8/38,2)",
        "https://www.incrediblecharts.com/indicators/choppiness-index.php",
        "E.W. Dreiss (anos 1990), definição clássica do autor",
    ],
    "rule": ("CHOP(n) = 100*log10(soma dos TR de n candles / (maior máxima n - menor mínima n))/log10(n). "
             "Regime de tendência: o CHOP cruza abaixo de lo (fim da congestão, uso de Dreiss); a direção é o sinal de "
             "fech - fech[n] (deslocamento líquido da janela): compra se positivo, vende se negativo. Sai quando o CHOP "
             "cruza acima de hi (volta à congestão) ou no stop móvel k*ATR14. Regime lateral (só em mode=switch): com "
             "CHOP > hi, compra quando o RSI(14) cruza de volta acima de 30 e vende quando cruza abaixo de 70; alvo na "
             "SMA(20) (mínimo 0,5 ATR), stop k*ATR14 (também móvel). Stop inicial k*ATR14 em tudo. side=long só compra."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [14, 28], "lo": [38.2, 45.0], "hi": [55.0, 61.8], "k": [2.0, 3.0],
             "side": ["long", "both"], "mode": ["trend", "switch"]},
}


def chop(df, n):
    h, l, c = df.high.values, df.low.values, df.close.values
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    s = pd.Series(tr).rolling(n).sum().to_numpy()
    rng = ind.highest(h, n) - ind.lowest(l, n)
    with np.errstate(divide="ignore", invalid="ignore"):
        return 100 * np.log10(s / rng) / np.log10(n)


def signals(df, p):
    c = df.close.values
    n = p["n"]
    ch = chop(df, n)
    a = ind.atr(df, 14)
    mom = c - ind.prev(c, n)
    trend_go = ind.cross_below(ch, np.full(len(c), p["lo"]))
    t_long = trend_go & (mom > 0)
    t_short = trend_go & (mom < 0)
    entry = np.where(t_long, 1, np.where(t_short, -1, 0))
    target = np.zeros(len(c))
    if p["mode"] == "switch":
        r = ind.rsi(c, 14)
        rng = ch > p["hi"]
        r_long = rng & ind.cross_above(r, np.full(len(c), 30.0))
        r_short = rng & ind.cross_below(r, np.full(len(c), 70.0))
        m = ind.sma(c, 20)
        entry = np.where(entry != 0, entry, np.where(r_long, 1, np.where(r_short, -1, 0)))
        dist = np.maximum(np.abs(m - c), 0.5 * a)
        target = np.where(r_long | r_short, dist, 0.0)
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    back = ind.cross_above(ch, np.full(len(c), p["hi"]))
    return {"entry": entry, "stop": p["k"] * a, "target": np.nan_to_num(target),
            "exit_long": back, "exit_short": back, "trail": p["k"] * a}
