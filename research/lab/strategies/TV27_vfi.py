"""Volume Flow Indicator (LazyBear, TradingView comunidade; Markos Katsanos 2004)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV27_vfi",
    "name": "Volume Flow Indicator (LazyBear / Katsanos)",
    "family": "volume",
    "round": 3,
    "origin": "TradingView comunidade (LazyBear)",
    "sources": [
        "https://www.tradingview.com/script/MhlDpfdS-Volume-Flow-Indicator-LazyBear/",
        "https://traders.com/Documentation/FEEDbk_docs/2004/06/TradersTips/TradersTips.html",
        "https://prorealcode.com/prorealtime-indicators/volume-flow-indicator",
    ],
    "sourceNote": "TradingView inacessível; fórmula conferida nos Traders' Tips da TASC (jun/2004, Katsanos) e no porte ProRealCode, que batem com o Pine de LazyBear (coef 0,2, vcoef 2,5, sinal EMA 5).",
    "rule": "typical=hlc3; inter=log(typ)-log(typ[1]); cutoff=coef*desvio(inter,30)*fech; vave=SMA(volume,n)[1]; vc=min(volume, 2,5*vave); "
            "vcp=+vc se typ-typ[1]>cutoff, -vc se < -cutoff, senão 0; VFI=soma(vcp,n)/vave; sinal=EMA(VFI,5). "
            "Gatilho 'zero' (Katsanos): compra quando VFI cruza acima de 0, vende quando cruza abaixo; sai no cruzamento oposto. "
            "Gatilho 'signal': cruzamento VFI x sinal. Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [65, 130, 200], "trigger": ["zero", "signal"], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    n = p["n"]
    c, v = df.close.values, df.volume.values
    typ = (df.high.values + df.low.values + c) / 3
    with np.errstate(divide="ignore", invalid="ignore"):
        inter = np.log(typ) - np.log(ind.prev(typ))
    cutoff = 0.2 * pd.Series(inter).rolling(30).std(ddof=0).to_numpy() * c
    vave = ind.prev(ind.sma(v, n))
    vc = np.minimum(v, 2.5 * vave)
    mf = typ - ind.prev(typ)
    with np.errstate(invalid="ignore"):
        vcp = np.where(mf > cutoff, vc, np.where(mf < -cutoff, -vc, 0.0))
    vcp = np.where(np.isnan(cutoff) | np.isnan(vave), np.nan, vcp)
    with np.errstate(divide="ignore", invalid="ignore"):
        vfi = pd.Series(vcp).rolling(n).sum().to_numpy() / vave
    vfi = np.where(np.isfinite(vfi), vfi, np.nan)
    if p["trigger"] == "zero":
        ref = np.zeros(len(c))
    else:
        ref = pd.Series(vfi).ewm(span=5, adjust=False, min_periods=5).mean().to_numpy()
    up, dn = ind.cross_above(vfi, ref), ind.cross_below(vfi, ref)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
