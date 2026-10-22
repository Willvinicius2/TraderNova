"""L35 - Market Structure: entrada no fundo mais alto (HL) confirmado dentro de estrutura HH/HL, saída na quebra do fundo."""
import numpy as np

import indicators as ind

META = {
    "id": "L35_market_structure",
    "name": "Market Structure (Higher High / Higher Low, quebra de estrutura)",
    "family": "tendencia",
    "round": 8,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://daytradingtoolkit.com/strategies/higher-high-higher-low-market-structure-strategy",
        "https://crosstrade.io/learn/price-action/market-structure",
        "Dow (teoria de Dow: tendência de alta = topos e fundos ascendentes); pivôs de swing como ta.pivothigh/ta.pivotlow do Pine",
    ],
    "rule": ("Pivôs de swing confirmados com atraso: topo em j se a máxima de j é maior que as p anteriores e >= que as p "
             "seguintes, só conhecido em j+p (fundo no espelho); sem repintura. Estrutura de alta: o último topo confirmado é "
             "maior que o anterior (HH) e o fundo recém-confirmado é maior que o anterior (HL); cycles=2 exige também o par "
             "anterior ascendente (dois ciclos HH/HL, como a fonte). Entrada (daytradingtoolkit): mode='confirm' compra na abertura "
             "após o candle que confirma o HL, se o fechamento ainda está acima dele; mode='trigger' arma uma compra acima da "
             "máxima do candle de confirmação (aproximada por fechamento acima dela, entrada na abertura seguinte) por até p "
             "candles, cancelada se fechar abaixo do HL. Stop logo abaixo do HL (- 0,25*ATR14, mínimo 0,5*ATR14). Saída: quebra "
             "de estrutura = fechamento abaixo do último fundo confirmado (que sobe a cada novo HL, servindo de stop móvel); alvo "
             "opcional target_r=2 (mínimo 2:1 da fonte; 0 = sem alvo). Venda (side=both) no espelho com LH/LL. Diferente do TV33 "
             "SMC BOS: lá a entrada é o rompimento (cruzamento) de um topo de swing; aqui a entrada é no recuo, quando o fundo mais "
             "alto se confirma dentro de uma sequência HH/HL já formada, e a saída é a perda do fundo."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"p": [2, 3, 5, 8], "cycles": [1, 2], "mode": ["confirm", "trigger"], "target_r": [0.0, 2.0],
             "side": ["long", "both"]},
}


def pivots(h, l, p):
    hs, ls = ind.prev(h, p), ind.prev(l, p)
    hl_left = ind.prev(ind.highest(h, p), p + 1)
    ll_left = ind.prev(ind.lowest(l, p), p + 1)
    with np.errstate(invalid="ignore"):
        ph = (hs > hl_left) & (hs >= ind.highest(h, p))
        pl = (ls < ll_left) & (ls <= ind.lowest(l, p))
    return ph, pl, hs, ls


def signals(df, p):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    n = len(c)
    P = p["p"]
    ph, pl, hs, ls = pivots(h, l, P)
    a = ind.atr(df, 14)
    entry = np.zeros(n, dtype=int)
    stop = np.full(n, np.nan)
    exl = np.zeros(n, dtype=bool)
    exs = np.zeros(n, dtype=bool)
    SH, SL = [], []
    lastSH = lastSL = np.nan
    armL = armS = None  # (nível, fundo/topo, expira)
    cyc = p["cycles"]

    def up_struct(lows):
        if len(SH) < cyc + 1 or len(lows) < cyc + 1:
            return False
        return all(SH[-k] > SH[-k - 1] for k in range(1, cyc + 1)) and all(lows[-k] > lows[-k - 1] for k in range(1, cyc + 1))

    def dn_struct(highs):
        if len(SL) < cyc + 1 or len(highs) < cyc + 1:
            return False
        return all(SL[-k] < SL[-k - 1] for k in range(1, cyc + 1)) and all(highs[-k] < highs[-k - 1] for k in range(1, cyc + 1))

    for i in range(n):
        # saídas pela quebra do último swing conhecido antes deste candle
        if not np.isnan(lastSL) and c[i] < lastSL:
            exl[i] = True
        if not np.isnan(lastSH) and c[i] > lastSH:
            exs[i] = True
        newL = bool(pl[i])
        newH = bool(ph[i])
        if newH:
            SH.append(hs[i]); lastSH = hs[i]
        if newL:
            SL.append(ls[i]); lastSL = ls[i]
        if np.isnan(a[i]):
            continue
        sig = 0
        if newL and up_struct(SL) and c[i] > ls[i]:
            if p["mode"] == "confirm":
                sig, ref = 1, ls[i]
            else:
                armL = (h[i], ls[i], i + P)
        if newH and dn_struct(SH) and c[i] < hs[i]:
            if p["mode"] == "confirm":
                sig, ref = (0, None) if sig else (-1, hs[i])
            else:
                armS = (l[i], hs[i], i + P)
        if p["mode"] == "trigger" and sig == 0:
            if armL is not None and not (newL and armL[2] == i + P):
                if i > armL[2] or c[i] < armL[1]:
                    armL = None
                elif c[i] > armL[0]:
                    sig, ref = 1, armL[1]
                    armL = None
            if sig == 0 and armS is not None and not (newH and armS[2] == i + P):
                if i > armS[2] or c[i] > armS[1]:
                    armS = None
                elif c[i] < armS[0]:
                    sig, ref = -1, armS[1]
                    armS = None
        if sig == 1:
            entry[i] = 1
            stop[i] = max(c[i] - ref + 0.25 * a[i], 0.5 * a[i])
        elif sig == -1:
            entry[i] = -1
            stop[i] = max(ref - c[i] + 0.25 * a[i], 0.5 * a[i])
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    out = {"entry": entry, "stop": np.nan_to_num(stop, nan=0.0), "exit_long": exl, "exit_short": exs}
    if p["target_r"] > 0:
        out["target_r"] = p["target_r"]
    return out
