"""TASC 2025.09 The Continuation Index (John F. Ehlers), script PineCodersTASC no TradingView."""
import numpy as np

import indicators as ind

META = {
    "id": "TV47_continuation_index",
    "name": "Continuation Index de Ehlers: comprado acima de +0,5, vendido abaixo de -0,5",
    "family": "tendencia",
    "round": 4,
    "origin": "TradingView comunidade (PineCodersTASC; John F. Ehlers, TASC set/2025)",
    "sources": [
        "https://www.tradingview.com/script/5ZrOut79-TASC-2025-09-The-Continuation-Index/",
        "https://traders.com/Documentation/FEEDbk_docs/2025/09/TradersTips.html",
        "Código Pine traduzido: github.com/deepentropy/lightweight-charts-indicators src/community/tasc-2025-09-the-continuation-index.ts",
    ],
    "sourceNote": "Fórmula do código traduzido. O script pinta as barras de alta acima de +0,5 e de baixa abaixo de -0,5 (cinza no meio); "
                  "a regra opera essas cores e sai quando a cor volta ao cinza.",
    "rule": "us = UltimateSmoother(fech, L/2); lg = média dos 'ordem' termos de Laguerre (gamma) cujo 1º termo é UltimateSmoother(fech, L); "
            "ref = 2*(us-lg)/SMA(|us-lg|, L); CI = Fisher inversa de ref = tanh(ref). "
            "Compra quando CI cruza acima de +0,5 e sai quando volta abaixo de +0,5; vende quando cruza abaixo de -0,5 e sai quando volta acima de -0,5. "
            "Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"L": [20, 30, 40, 60, 80], "gamma": [0.6, 0.8], "order": [4, 8], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def ultimate(src, period):
    a1 = np.exp(-1.414 * np.pi / period)
    c2 = 2.0 * a1 * np.cos(1.414 * np.pi / period)
    c3 = -a1 * a1
    c1 = (1.0 + c2 - c3) / 4.0
    us = src.astype(float).copy()
    for i in range(4, len(src)):
        us[i] = ((1.0 - c1) * src[i] + (2.0 * c1 - c2) * src[i - 1] - (c1 + c3) * src[i - 2]
                 + c2 * us[i - 1] + c3 * us[i - 2])
    return us


def cont_index(src, L, gamma, order):
    us = ultimate(src, int(L / 2))
    first = ultimate(src, L)
    n = len(src)
    cur = np.zeros(order)
    prv = np.zeros(order)
    lg = np.zeros(n)
    for i in range(n):
        prv[0] = cur[0]
        cur[0] = first[i]
        fir = cur[0]
        for k in range(1, order):
            prv[k] = cur[k]
            cur[k] = gamma * (prv[k] - prv[k - 1]) + prv[k - 1]
            fir += cur[k]
        lg[i] = fir / order
    diff = us - lg
    avg = ind.sma(np.abs(diff), L)
    with np.errstate(invalid="ignore", divide="ignore"):
        ref = 2.0 * diff / avg
    ci = np.tanh(np.nan_to_num(ref, nan=0.0, posinf=0.0, neginf=0.0))
    ci[: 4 * L] = np.nan
    return ci


def signals(df, p):
    ci = cont_index(df.close.values, p["L"], p["gamma"], p["order"])
    hi = np.full(len(ci), 0.5)
    up = ind.cross_above(ci, hi)
    dn = ind.cross_below(ci, -hi)
    with np.errstate(invalid="ignore"):
        exl = ci < 0.5
        exs = ci > -0.5
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": exl, "exit_short": exs}
