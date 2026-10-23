"""L51 - Rompimento de canal ATR depois de contração da Bollinger BandWidth (percentil)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L51_atr_squeeze_breakout",
    "name": "Rompimento de canal ATR após BandWidth em contração (percentil)",
    "family": "volatilidade",
    "round": 9,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/bollinger-bandwidth",
        "https://www.luxalgo.com/library/concept/atr-bands.md",
        "John Bollinger, Bollinger on Bollinger Bands (2001), 'The Squeeze' (BandWidth na mínima de ~6 meses)",
    ],
    "rule": ("BandWidth = (BB superior - inferior)/SMA20*100 (Bollinger 20, 2 desvios). Contração: o percentil do BandWidth "
             "dentro dos últimos 'lb' candles (lb = ~6 meses no tempo gráfico: H1 4380, H4 1095, D1 180; janela causal) ficou "
             "<= pct em algum dos últimos 5 candles até i-1. Gatilho: fechamento cruza acima de SMA20 + k*ATR20 (canal ATR) -> "
             "compra; abaixo de SMA20 - k*ATR20 -> venda (side=both). Saída: exit=mid fechamento volta para o outro lado da SMA20; "
             "exit=trail stop móvel 3*ATR20 a partir do fechamento. Stop inicial stop_k*ATR20. Diferente do L09 TTM (BB dentro do "
             "Keltner + momentum) e do L12 Keltner (EMA±ATR sem filtro de contração): aqui o filtro é o percentil histórico do "
             "BandWidth e o gatilho é o canal ATR sobre SMA."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"pct": [10, 20, 30], "k": [1.0, 1.5, 2.0], "stop_k": [2.0, 3.0], "exit": ["mid", "trail"],
             "side": ["long", "both"]},
}

N = 20
RECENT = 5


def _lb(df):
    dt = (df.index[-1] - df.index[0]) / max(len(df) - 1, 1)
    hours = dt.total_seconds() / 3600
    return int(round(4380 / max(hours, 1e-9))) if hours < 20 else 180


def signals(df, p):
    c = df.close.values
    m = ind.sma(c, N)
    sd = ind.stdev(c, N)
    bw = 4 * sd / m * 100
    lb = _lb(df)
    # percentil causal do valor atual dentro da janela (0..100)
    pr = pd.Series(bw).rolling(lb, min_periods=lb).rank(pct=True).to_numpy() * 100
    tight = pd.Series(pr <= p["pct"]).rolling(RECENT, min_periods=1).max().to_numpy().astype(bool)
    tight_prev = np.r_[False, tight[:-1]]
    a = ind.atr(df, N)
    up, dn = m + p["k"] * a, m - p["k"] * a
    lo = ind.cross_above(c, up) & tight_prev
    sh = ind.cross_below(c, dn) & tight_prev
    entry = np.where(lo, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    out = {"entry": entry, "stop": p["stop_k"] * a}
    if p["exit"] == "mid":
        out["exit_long"], out["exit_short"] = c < m, c > m
    else:
        out["trail"] = 3.0 * a
    return out
