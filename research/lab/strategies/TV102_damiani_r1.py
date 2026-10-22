"""Damiani Volatmeter (Luis Damiani; Pine de xinolia/loxx) como filtro do cruzamento do Fisher Transform."""
import numpy as np

import indicators as ind

META = {
    "id": "TV102_damiani_r1",
    "refines": "TV102_damiani",
    "refinement": "Desenvolvimento: no H1/H4 o Fisher de reversão contra a tendência perde em todos os anos (2018 pior) e no D1 só 3 de 5 anos positivos. Filtro de tendência: só aceita o sinal do Fisher a favor da EMA(trend) (compra acima, venda abaixo), nível fixo 0,5.",
    "name": "Damiani Volatmeter como filtro + tendência EMA: Fisher cruza o Trigger a favor da tendência com volatilidade 'acordada'",
    "family": "volatilidade",
    "round": 7,
    "origin": "TradingView comunidade (Damiani Volatmeter, xinolia / loxx; indicador MT4 de Luis Damiani)",
    "sources": [
        "https://www.tradingview.com/script/z95IdM4a-Damiani-Volatmeter-loxx",
        "https://docs.gehtsoftusa.com/fxcodebase-backup/backup/mt4-expert-advisors/d/damiani-volameter/",
        "https://www.tradingview.com/support/solutions/43000589141-fisher-transform/",
    ],
    "sourceNote": "Fórmula do fxcodebase (Line1 = ATR_vis/ATR_sed + (Line1[1]-Line1[3])/2 com supressor de atraso; "
                  "Line2 = limiar - DP_vis/DP_sed). Padrões clássicos vis_atr=13, sed_atr=40, vis_std=20, sed_std=100, limiar 1,4; "
                  "a FILA cita ATR(7)/ATR(50), também testado. Gatilho direcional: a página do loxx diz que a volatilidade não tem direção "
                  "e cita o Fisher Transform como indicador direcional para combinar; usado o cruzamento Fisher/Trigger em extremo "
                  "(mesma lógica do TV19_fisher). Aqui a regra nova é o filtro, não o gatilho.",
    "rule": "Volatmeter ligado quando Line1 > Line2 (ATR curto/ATR longo, com supressor de atraso, acima de limiar - DP curto/DP longo). "
            "Gatilho: Fisher(n) cruza acima do Trigger (Fisher anterior) estando abaixo de -lvl = compra; cruza abaixo estando acima "
            "de +lvl = venda (side=both). Entra só se o Volatmeter está ligado no candle do sinal. Sai no cruzamento oposto do Fisher "
            "(sem filtro). Refino r1: compra só com fechamento acima da EMA(trend) e venda só abaixo. Stop de proteção k*ATR14 (o original não tem stop).",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"cfg": ["7/50", "13/40"], "thr": [1.2, 1.4, 1.6], "n": [9, 13], "lvl": [0.5], "trend": [100, 200],
             "k": [2.0, 3.0], "side": ["long", "both"]},
}


def fisher(df, n):
    hl2 = (df.high.values + df.low.values) / 2
    hh, ll = ind.highest(hl2, n), ind.lowest(hl2, n)
    N = len(hl2)
    fi = np.full(N, np.nan)
    pv, pfi = 0.0, 0.0
    for i in range(N):
        if np.isnan(hh[i]):
            continue
        rng = hh[i] - ll[i]
        x = 0.66 * (((hl2[i] - ll[i]) / rng if rng > 0 else 0.5) - 0.5) + 0.67 * pv
        x = min(max(x, -0.999), 0.999)
        f = 0.5 * np.log((1 + x) / (1 - x)) + 0.5 * pfi
        fi[i] = f
        pv, pfi = x, f
    return fi


def volatmeter(df, vis_atr, sed_atr, vis_std=20, sed_std=100, thr=1.4):
    c = df.close.values
    ratio = ind.atr(df, vis_atr) / ind.atr(df, sed_atr)
    n = len(c)
    vol = np.full(n, np.nan)
    for i in range(n):
        if np.isnan(ratio[i]):
            continue
        v1 = vol[i - 1] if i >= 1 and not np.isnan(vol[i - 1]) else 0.0
        v3 = vol[i - 3] if i >= 3 and not np.isnan(vol[i - 3]) else 0.0
        vol[i] = ratio[i] + 0.5 * (v1 - v3)
    with np.errstate(divide="ignore", invalid="ignore"):
        anti = ind.stdev(c, vis_std) / ind.stdev(c, sed_std)
    line2 = thr - anti
    with np.errstate(invalid="ignore"):
        return vol > line2


def signals(df, p):
    va, sa = (int(x) for x in p["cfg"].split("/"))
    on = volatmeter(df, va, sa, thr=p["thr"])
    f = fisher(df, p["n"])
    t = ind.prev(f)
    up = ind.cross_above(f, t)
    dn = ind.cross_below(f, t)
    with np.errstate(invalid="ignore"):
        lg = up & (f < -p["lvl"]) & on
        sh = dn & (f > p["lvl"]) & on
        e = ind.ema(df.close.values, p["trend"])
        lg &= df.close.values > e
        sh &= df.close.values < e
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
