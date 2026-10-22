"""TV57 - Elder Force Index: pullback na tendência (Alexander Elder)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV57_force_pullback",
    "name": "Elder Force Index(2): pullback na tendência da EMA(22)",
    "family": "tendencia",
    "round": 5,
    "origin": "TradingView embutida (Elder Force Index; regra de Alexander Elder, Trading for a Living, 1993)",
    "sources": [
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/force-index",
        "https://github.com/deepentropy/lightweight-charts-indicators/blob/main/src/standard/elder-force.ts",
        "https://ta-lib.org/functions/efi.html",
    ],
    "sourceNote": "Fórmula do port do indicador embutido (EMA de (fech - fech anterior) * volume). Regra da ChartSchool: tendência pela "
                  "EMA(22) subindo; no pullback, comprar quando o FI(2) fica negativo (agressivo) ou esperar ele voltar a positivo. "
                  "A venda (FI(2) positivo com EMA caindo) é o espelho, a ChartSchool não a escreve explicitamente.",
    "rule": ("FI = EMA(2) de (fech - fech anterior) * volume. Tendência: EMA(t) subindo/caindo. mode='neg': compra no candle em que o FI cruza "
             "abaixo de 0 com a EMA subindo (venda: FI cruza acima de 0 com a EMA caindo). mode='turn': compra quando o FI volta acima de 0 "
             "depois de ter ficado negativo (cruzamento) com a EMA subindo; venda espelhada. Saída exit='fi': no modo neg sai quando o FI fica "
             "positivo (venda: negativo); no modo turn sai quando o FI volta a ficar negativo (venda: positivo). exit='ema': sai quando a EMA "
             "vira contra. Sem stop no original: stop de proteção k*ATR14."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"t": [13, 22, 34], "mode": ["neg", "turn"], "exit": ["fi", "ema"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    c, v = df.close.values, df.volume.values
    raw = np.r_[np.nan, np.diff(c)] * v
    raw[0] = 0.0
    fi = ind.ema(raw, 2)
    e = ind.ema(c, p["t"])
    pe = ind.prev(e)
    up, dn = e > pe, e < pe
    z = np.zeros(len(c))
    fneg, fpos = ind.cross_below(fi, z), ind.cross_above(fi, z)
    if p["mode"] == "neg":
        buy, sell = up & fneg, dn & fpos
        exl, exs = fi > 0, fi < 0
    else:
        buy, sell = up & fpos, dn & fneg
        exl, exs = fi < 0, fi > 0
    if p["exit"] == "ema":
        exl, exs = dn, up
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
