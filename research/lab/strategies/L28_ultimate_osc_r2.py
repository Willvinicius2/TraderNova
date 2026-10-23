"""L28 r2 - Ultimate Oscillator: regra de Twiggs com nível de mergulho ajustável (BTC quase nunca fica abaixo de 30)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L28_ultimate_osc_r2",
    "name": "Ultimate Oscillator: fundo/topo mais alto após nível lv + cruzamento de 50 (Twiggs), saídas de Williams",
    "family": "reversao",
    "round": 8,
    "origin": "FILA.md (autor)",
    "refines": "L28_ultimate_osc",
    "refinement": ("Na r1 (regra de Twiggs) o melhor do desenvolvimento teve só 21 operações: no BTC o UO(7,14,28) fica "
                   "abaixo de 30 em apenas 0,2-0,5% dos candles (a distribuição é deslocada para cima), então o mergulho exigido "
                   "quase nunca acontece. O nível do mergulho vira parâmetro lv (compra após UO < lv, venda após UO > 100-lv); "
                   "o resto da regra e as saídas de Williams ficam iguais."),
    "sources": [
        "https://www.incrediblecharts.com/indicators/ultimate-oscillator.php",
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/ultimate-oscillator",
    ],
    "rule": ("UO de Williams (7/14/28 x 'scale'). Compra (Twiggs): depois de o UO cair abaixo de lv (30 no original) (guarda o menor valor desse "
             "mergulho), um novo fundo do UO (pivô com 2 candles de cada lado, conhecido 2 candles depois) mais alto que esse "
             "menor valor arma o sinal; compra quando o UO cruza acima de 50 depois desse fundo; se o 2º fundo já estiver acima "
             "de 50, compra quando o UO sobe 10 pontos a partir dele. Se o UO voltar abaixo do 1º fundo, o mergulho recomeça. "
             "Venda espelhada (acima de 100-lv, topo mais baixo, cruza abaixo de 50). Saídas de Williams: compra fecha com UO > 70 "
             "ou, depois de passar de 50, UO < 45; venda fecha com UO < 30 ou UO > 65; sinal oposto inverte. Filtro de regime "
             "opcional: compra só com fechamento > EMA(trend), venda só abaixo. Stop k*ATR14. Entrada na abertura seguinte."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"lv": [30, 35, 40], "scale": [1, 2], "trend": [0, 200], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def uo(df, s):
    h, l, c = (df[k].values.astype(float) for k in ("high", "low", "close"))
    pc = ind.prev(c, 1)
    lo = np.fmin(l, pc)
    bp, tr = pd.Series(c - lo), pd.Series(np.fmax(h, pc) - lo)
    a = [bp.rolling(n * s).sum() / tr.rolling(n * s).sum() for n in (7, 14, 28)]
    return (100.0 * (4 * a[0] + 2 * a[1] + a[2]) / 7.0).to_numpy(copy=True)


def _twiggs(o, r, lv=30):
    """o já orientado para compra (para venda, passe 100-UO)."""
    n = len(o)
    out = np.zeros(n, dtype=bool)
    t1 = None      # menor valor do mergulho abaixo de 30
    t2 = None      # valor do 2º fundo (armado)
    for i in range(1, n):
        v = o[i]
        if np.isnan(v):
            continue
        if v < lv and (t1 is None or v < t1):
            t1, t2 = v, None
        if t1 is None:
            continue
        j = i - r
        if t2 is None and j - r >= 0:
            w = o[j - r:i + 1]
            if not np.any(np.isnan(w)) and np.argmin(w) == r and o[j] > t1:
                t2 = o[j]
        if t2 is not None:
            trig = (v > 50 and o[i - 1] <= 50) if t2 < 50 else (v >= t2 + 10)
            if trig:
                out[i] = True
                t1 = t2 = None
    return out


def signals(df, p):
    u = uo(df, p["scale"])
    c = df.close.values.astype(float)
    buy = _twiggs(u, 2, p["lv"])
    sell = _twiggs(100.0 - u, 2, p["lv"])
    if p["trend"]:
        e = ind.ema(c, p["trend"])
        buy &= c > e
        sell &= c < e
    n = len(u)
    ex_l = np.zeros(n, dtype=bool)
    above50 = False
    for i in range(n):
        if buy[i]:
            above50 = False
        if u[i] > 50:
            above50 = True
        ex_l[i] = (u[i] > 70) or (above50 and u[i] < 45)
    ex_s = (u < 30) | (u > 65)
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": ex_l, "exit_short": ex_s}
