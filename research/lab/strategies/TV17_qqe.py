"""QQE (Quantitative Qualitative Estimation), versão Pine da comunidade TradingView (porta do MT4 de Roman Ignatov / Glaz)."""
import numpy as np

import indicators as ind

META = {
    "id": "TV17_qqe",
    "name": "QQE: RSI suavizado cruzando a linha de rastreio",
    "family": "momento",
    "round": 2,
    "origin": "TradingView comunidade (Roman Ignatov, porta do QQE MT4)",
    "sources": [
        "https://www.tradingview.com/script/IYfA9R2k-QQE-MT4",
        "https://www.luxalgo.com/library/concept/qqe/",
        "https://help.tradestation.com/10_00/eng/tradestationhelp/elanalysis/indicator/qqe_indicator_.htm",
    ],
    "sourceNote": "TradingView inacessível pelo WebFetch; regra tirada dos resumos do WebSearch (script QQE MT4, LuxAlgo, TradeStation).",
    "rule": "RsiMa = EMA(RSI(n), SF). AtrRsi = |RsiMa - RsiMa anterior|; dar = EMA(EMA(AtrRsi, 2n-1), 2n-1) * fator (lenta 4,236; rápida 2,618). "
            "Linha de rastreio: banda de baixo RsiMa-dar só sobe enquanto RsiMa fica acima dela; banda de cima RsiMa+dar só desce enquanto RsiMa fica abaixo; "
            "a tendência vira quando RsiMa cruza a banda oposta e a linha passa a ser a banda da tendência. Compra quando RsiMa cruza acima da linha; "
            "vende no cruzamento abaixo; sai no cruzamento oposto. Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [10, 14, 21], "sf": [3, 5, 8], "fac": [2.618, 4.236], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def qqe_line(rsima, dar):
    n = len(rsima)
    lb = np.full(n, np.nan)
    sb = np.full(n, np.nan)
    tr = np.zeros(n)
    line = np.full(n, np.nan)
    for i in range(1, n):
        r, rp, d = rsima[i], rsima[i - 1], dar[i]
        if np.isnan(r) or np.isnan(rp) or np.isnan(d):
            continue
        nl, ns = r - d, r + d
        plb, psb = lb[i - 1], sb[i - 1]
        if np.isnan(plb):
            lb[i], sb[i], tr[i] = nl, ns, 1
            line[i] = nl
            continue
        lb[i] = max(plb, nl) if (rp > plb and r > plb) else nl
        sb[i] = min(psb, ns) if (rp < psb and r < psb) else ns
        if rp <= psb and r > psb:  # cruzou a banda de cima anterior
            tr[i] = 1
        elif rp >= plb and r < plb:
            tr[i] = -1
        else:
            tr[i] = tr[i - 1] if tr[i - 1] != 0 else 1
        line[i] = lb[i] if tr[i] == 1 else sb[i]
    return line


def signals(df, p):
    c = df.close.values
    n = p["n"]
    rsima = np.array(ind.ema(np.nan_to_num(ind.rsi(c, n), nan=50.0), p["sf"]), dtype=float)
    rsima[: n + p["sf"]] = np.nan
    atr_rsi = np.abs(np.r_[np.nan, np.diff(rsima)])
    w = 2 * n - 1
    s1 = np.full(len(c), np.nan)
    f = np.argmax(~np.isnan(atr_rsi))
    s1[f:] = ind.ema(atr_rsi[f:], w)
    s2 = np.full(len(c), np.nan)
    f2 = np.argmax(~np.isnan(s1))
    s2[f2:] = ind.ema(s1[f2:], w)
    dar = s2 * p["fac"]
    line = qqe_line(rsima, dar)
    up = ind.cross_above(rsima, line)
    dn = ind.cross_below(rsima, line)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
