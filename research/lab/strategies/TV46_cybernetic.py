"""TASC 2025.06 Cybernetic Oscillator (John F. Ehlers), script PineCodersTASC no TradingView."""
import numpy as np

import indicators as ind

META = {
    "id": "TV46_cybernetic",
    "name": "Cybernetic Oscillator de Ehlers: lado da linha zero (modo Trend)",
    "family": "tendencia",
    "round": 4,
    "origin": "TradingView comunidade (PineCodersTASC; John F. Ehlers, TASC jun/2025)",
    "sources": [
        "https://www.tradingview.com/script/QwMaFZTL-TASC-2025-06-Cybernetic-Oscillator",
        "Código Pine traduzido: github.com/deepentropy/lightweight-charts-indicators src/community/tasc-2025-06-cybernetic-oscillator.ts",
    ],
    "sourceNote": "Fórmula do código traduzido. No estilo 'Trend' o script pinta verde acima de 0 e vermelho abaixo; a regra opera essa cor. "
                  "A divisão pelo RMS não muda o sinal, então rmsLength (100) fica fixo.",
    "rule": "hp = passa-alta de 2ª ordem (período HP) do fechamento; lp = SuperSmoother(hp, LP); osc = lp/RMS(lp, 100). "
            "Compra quando osc cruza acima de 0; vende quando cruza abaixo; sai no cruzamento oposto (inverte se 'both'). "
            "Sem stop no original: stop de proteção k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"lp": [10, 15, 20], "hp": [30, 45, 60, 90], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def coefs(period, is_hp):
    a0 = 1.414 * np.pi / period
    a1 = np.exp(-a0)
    c2 = 2.0 * a1 * np.cos(a0)
    c3 = -a1 * a1
    c1 = (1.0 + c2 - c3) * 0.25 if is_hp else 1.0 - c2 - c3
    return c1, c2, c3


def cyber(src, hpp, lpp, rms_len=100):
    n = len(src)
    h1, h2, h3 = coefs(hpp, True)
    hp = np.zeros(n)
    for i in range(4, n):
        hp[i] = h1 * (src[i] - 2.0 * src[i - 1] + src[i - 2]) + h2 * hp[i - 1] + h3 * hp[i - 2]
    s1, s2, s3 = coefs(lpp, False)
    lp = np.full(n, hp[0])
    for i in range(4, n):
        lp[i] = s1 * 0.5 * (hp[i] + hp[i - 1]) + s2 * lp[i - 1] + s3 * lp[i - 2]
    rms = np.sqrt(ind.sma(lp * lp, rms_len))
    with np.errstate(invalid="ignore", divide="ignore"):
        osc = np.where(rms > 0, lp / rms, np.nan)
    osc[: max(rms_len, 3 * hpp)] = np.nan
    return osc


def signals(df, p):
    o = cyber(df.close.values, p["hp"], p["lp"])
    z = np.zeros(len(o))
    up = ind.cross_above(o, z)
    dn = ind.cross_below(o, z)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
