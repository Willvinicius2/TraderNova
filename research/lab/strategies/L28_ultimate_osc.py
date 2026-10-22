"""L28 - Ultimate Oscillator (Larry Williams, 1985): regra original de divergência + rompimento."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L28_ultimate_osc",
    "name": "Ultimate Oscillator (Williams): divergência confirmada + rompimento, saídas 70/45 e 30/65",
    "family": "reversao",
    "round": 8,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/ultimate-oscillator",
        "https://www.incrediblecharts.com/indicators/ultimate-oscillator.php",
        "https://en.wikipedia.org/wiki/Ultimate_oscillator",
        "Larry Williams, 'The Ultimate Oscillator', Technical Analysis of Stocks & Commodities, 1985",
    ],
    "rule": ("UO = 100*(4*A7 + 2*A14 + A28)/7, A_n = soma_n(BP)/soma_n(TR), BP = F - min(m, F[1]), TR = max(M, F[1]) - min(m, F[1]) "
             "(períodos x 'scale'). Compra (Williams): divergência de alta entre dois fundos de preço consecutivos (pivô de "
             "mínima com r candles de cada lado, só conhecido r candles depois): mínima do 2º fundo < do 1º, mínimo do UO "
             "em volta do 2º fundo > em volta do 1º, UO abaixo de 30 no 1º fundo, fundos separados por no máximo 'gap' candles; "
             "a partir da confirmação, compra quando o UO passa acima da máxima do UO entre os dois fundos (cancela se o preço "
             "perder a mínima do 2º fundo ou após 'gap' candles). Venda espelhada (topos, UO acima de 70 no 1º topo, UO cai "
             "abaixo da mínima entre os topos). Saídas de Williams: compra fecha com UO > 70 ou, depois de passar de 50, UO < 45; "
             "venda fecha com UO < 30 ou UO > 65; sinal oposto inverte. O '50 depois da entrada' é contado desde o último "
             "sinal de compra. Stop de proteção k*ATR14 (o original não tem). Entrada na abertura seguinte."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"scale": [1, 2], "r": [2, 3, 5], "gap": [30, 60], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def uo(df, s):
    h, l, c = (df[k].values.astype(float) for k in ("high", "low", "close"))
    pc = ind.prev(c, 1)
    lo = np.fmin(l, pc)
    bp = c - lo
    tr = np.fmax(h, pc) - lo
    bp, tr = pd.Series(bp), pd.Series(tr)
    a = [bp.rolling(n * s).sum() / tr.rolling(n * s).sum() for n in (7, 14, 28)]
    return (100.0 * (4 * a[0] + 2 * a[1] + a[2]) / 7.0).to_numpy(copy=True)


def _div_signals(price, osc, r, gap, bull):
    """Sinais de divergência + rompimento sem olhar o futuro. bull=True usa mínimas; False usa máximas (sinal invertido)."""
    x = price if bull else -price
    o = osc if bull else 100.0 - osc
    n = len(x)
    out = np.zeros(n, dtype=bool)
    last = None  # (índice do pivô, x no pivô, mínimo do osc em volta)
    armed = None  # (nível, x do 2º fundo, prazo)
    for i in range(2 * r, n):
        j = i - r  # candidato a pivô, confirmado agora
        win = x[j - r:i + 1]
        if not np.isnan(x[j]) and x[j] == np.nanmin(win) and np.argmin(win) == r:
            ow = o[j - r:i + 1]
            if not np.all(np.isnan(ow)):
                om = np.nanmin(ow)
                if last is not None:
                    pj, px, pom = last
                    if j - pj <= gap and x[j] < px and om > pom and pom < 30:
                        armed = (np.nanmax(o[pj:j + 1]), x[j], i + gap)
                last = (j, x[j], om)
        if armed is not None:
            lvl, x2, dl = armed
            if x[i] < x2 or i > dl:
                armed = None
            elif o[i] > lvl:
                out[i] = True
                armed = None
    return out


def signals(df, p):
    s, r, gap = p["scale"], p["r"], p["gap"]
    u = uo(df, s)
    lo, hi = df.low.values.astype(float), df.high.values.astype(float)
    buy = _div_signals(lo, u, r, gap, True)
    sell = _div_signals(hi, u, r, gap, False)
    # saídas de Williams
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
