"""WaveTrend Oscillator (LazyBear, TradingView comunidade): cruzamento WT1/WT2 nas zonas extremas."""
import numpy as np

import indicators as ind

META = {
    "id": "TV16_wavetrend",
    "name": "WaveTrend Oscillator (LazyBear): cruzamento nas zonas",
    "family": "reversao",
    "round": 2,
    "origin": "TradingView comunidade (LazyBear)",
    "sources": [
        "https://www.tradingview.com/script/2KE8wTuF-Indicator-WaveTrend-Oscillator-WT/",
        "https://www.prorealcode.com/prorealtime-indicators/wave-trend-oscillator/",
        "https://community.tradovate.com/t/wavetrend-anything-similar/762",
    ],
    "sourceNote": "TradingView inacessível pelo WebFetch; código Pine de LazyBear conferido em espelhos (ProRealCode, fórum Tradovate) via WebSearch.",
    "rule": "Pine de LazyBear: ap=hlc3, esa=EMA(ap,n1), d=EMA(|ap-esa|,n1), ci=(ap-esa)/(0,015*d), WT1=EMA(ci,n2), WT2=SMA(WT1,4). "
            "Compra quando WT1 cruza acima de WT2 com WT1 abaixo de -nível (sobrevenda; padrão -53/-60); vende quando cruza abaixo com WT1 acima de +nível. "
            "Sai no cruzamento oposto WT1/WT2. O script original é só indicador e não tem stop: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n1": [8, 10, 13], "n2": [16, 21], "lvl": [40, 53, 60], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    ap = (df.high.values + df.low.values + df.close.values) / 3
    esa = ind.ema(ap, p["n1"])
    d = ind.ema(np.abs(ap - esa), p["n1"])
    with np.errstate(invalid="ignore", divide="ignore"):
        ci = np.where(d > 0, (ap - esa) / (0.015 * d), np.nan)
    # EMA de série com NaN no começo: preenche com 0 só até o primeiro valor válido
    first = np.argmax(~np.isnan(ci))
    ci2 = ci.copy()
    ci2[:first] = np.nan
    wt1 = np.full(len(ci), np.nan)
    wt1[first:] = ind.ema(np.nan_to_num(ci2[first:]), p["n2"])
    wt2 = ind.sma(wt1, 4)
    up = ind.cross_above(wt1, wt2)
    dn = ind.cross_below(wt1, wt2)
    with np.errstate(invalid="ignore"):
        lg = up & (wt1 < -p["lvl"])
        sh = dn & (wt1 > p["lvl"])
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
