"""TV92 - Ehlers Sinewave (Sine x LeadSine), modo ciclo. John F. Ehlers, Cybernetic Analysis (2004) / Rocket Science for Traders (2001)."""
import math

import numpy as np

import indicators as ind

META = {
    "id": "TV92_sinewave",
    "name": "Ehlers Sinewave: cruzamento LeadSine/Sine com ciclo válido",
    "family": "ciclos",
    "round": 7,
    "origin": "TradingView comunidade (LazyBear, blackcat e outros; John F. Ehlers, Cybernetic Analysis for Stocks and Futures, 2004)",
    "sources": [
        "https://www.prorealcode.com/reply/11887/",
        "https://kr.tradingview.com/script/5n0y69Aq-blackcat-L2-Ehlers-Sine-Wave-Indicator",
        "https://id.tradingview.com/script/a1AeExr4-Ehlers-Even-Better-Sinewave-Indicator-CC",
    ],
    "sourceNote": "TradingView inacessível; não há Pine do Sinewave nos repositórios clonados. Fórmula da listagem EasyLanguage de Ehlers "
                  "(Cybernetic Analysis, cap. 9) reproduzida no fórum ProRealCode: Smooth 1-2-2-1, Cyber Cycle (alpha), I/Q, delta fase "
                  "limitada a 0,1-1,1 e mediana de 5, período dominante suavizado, fase dominante pela DFT do ciclo em DCPeriod candles; "
                  "Sine = sin(DCPhase), LeadSine = sin(DCPhase+45). Regra de Ehlers: compra quando a LeadSine cruza acima da Sine (fundo do ciclo) e "
                  "vende no cruzamento para baixo. A linha da fila diz 'Sine cruza acima da LeadSine'; seguimos Ehlers (a LeadSine adianta 45 graus "
                  "e cruza para cima perto do fundo). 'Ciclo válido' (Rocket Science): a fase avança entre 0,67 e 1,5 vez 360/DCPeriod por candle; "
                  "fora disso o mercado está em modo tendência e o sinal é ignorado. Sem stop no original: stop de proteção k*ATR14.",
    "rule": "Preço (H+L)/2. Calcula Sine e LeadSine de Ehlers. Compra quando LeadSine cruza acima da Sine; vende quando cruza abaixo; "
            "a posição sai/inverte no cruzamento oposto. filtro='ciclo': só entra se a fase avançou entre 0,67 e 1,5 x 360/DCPeriod no candle. "
            "Stop k*ATR14.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"alpha": [0.05, 0.07, 0.1], "filtro": ["nenhum", "ciclo"], "k": [2.0, 3.0], "side": ["long", "both"]},
}

_CACHE = {}


def sinewave(price, alpha):
    p = np.asarray(price, float)
    n = len(p)
    sm = p.copy()
    sm[3:] = (p[3:] + 2 * p[2:-1] + 2 * p[1:-2] + p[:-3]) / 6
    cyc = np.zeros(n)
    q1 = np.zeros(n)
    i1 = np.zeros(n)
    dp = np.zeros(n)
    inst = np.zeros(n)
    per = np.zeros(n)
    phase = np.zeros(n)
    dcp = np.zeros(n)
    a1, a2, a3 = (1 - 0.5 * alpha) ** 2, 2 * (1 - alpha), (1 - alpha) ** 2
    for i in range(n):
        if i < 7:
            cyc[i] = (p[i] - 2 * p[i - 1] + p[i - 2]) / 4 if i >= 2 else 0.0
            continue
        cyc[i] = a1 * (sm[i] - 2 * sm[i - 1] + sm[i - 2]) + a2 * cyc[i - 1] - a3 * cyc[i - 2]
        q1[i] = (0.0962 * cyc[i] + 0.5769 * cyc[i - 2] - 0.5769 * cyc[i - 4] - 0.0962 * cyc[i - 6]) * (0.5 + 0.08 * inst[i - 1])
        i1[i] = cyc[i - 3]
        d = dp[i - 1]
        if q1[i] != 0 and q1[i - 1] != 0:
            den = 1 + i1[i] * i1[i - 1] / (q1[i] * q1[i - 1])
            if den != 0:
                d = (i1[i] / q1[i] - i1[i - 1] / q1[i - 1]) / den
        d = min(max(d, 0.1), 1.1)
        dp[i] = d
        md = float(np.median(dp[i - 4 : i + 1]))
        dc = 15.0 if md == 0 else 6.28318 / md + 0.5
        inst[i] = 0.33 * dc + 0.67 * inst[i - 1]
        per[i] = 0.15 * inst[i] + 0.85 * per[i - 1]
        L = int(per[i])
        dcp[i] = L
        if L < 1 or i - L + 1 < 0:
            phase[i] = phase[i - 1]
            continue
        ang = 2 * math.pi * np.arange(L) / L
        seg = cyc[i - np.arange(L)]
        re = float(np.dot(np.sin(ang), seg))
        im = float(np.dot(np.cos(ang), seg))
        if abs(im) > 0.001:
            ph = math.degrees(math.atan(re / im))
        else:
            ph = 90.0 * (1 if re > 0 else (-1 if re < 0 else 0))
        ph += 90
        if im < 0:
            ph += 180
        if ph > 315:
            ph -= 360
        phase[i] = ph
    sine = np.sin(np.radians(phase))
    lead = np.sin(np.radians(phase + 45))
    return sine, lead, phase, dcp


def signals(df, p):
    key = (len(df), str(df.index[0]), str(df.index[-1]), p["alpha"])
    if key not in _CACHE:
        price = (df.high.values + df.low.values) / 2
        _CACHE[key] = sinewave(price, p["alpha"])
    sine, lead, phase, dcp = _CACHE[key]
    up, dn = ind.cross_above(lead, sine), ind.cross_below(lead, sine)
    warm = np.arange(len(sine)) < 60
    up &= ~warm
    dn &= ~warm
    if p["filtro"] == "ciclo":
        adv = np.r_[np.nan, np.diff(phase)]
        adv = np.where(adv < -180, adv + 360, adv)
        rate = 360.0 / np.maximum(dcp, 1)
        ok = (adv > 0.67 * rate) & (adv < 1.5 * rate)
        eu, ed = up & ok, dn & ok
    else:
        eu, ed = up, dn
    entry = np.where(eu, 1, np.where(ed, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * ind.atr(df, 14), "exit_long": dn, "exit_short": up}
