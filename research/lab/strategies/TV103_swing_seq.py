"""Swing Breakout Sequence [LuxAlgo], traduzido do port DE (swing-breakout-sequence.ts), com regra de rompimento de A."""
import numpy as np

import indicators as ind

META = {
    "id": "TV103_swing_seq",
    "name": "Swing Breakout Sequence (LuxAlgo): rompimento de A depois da sequência de 5 pontos",
    "family": "rompimento",
    "round": 7,
    "origin": "TradingView comunidade (LuxAlgo)",
    "sources": [
        "https://www.tradingview.com/script/LZIqzxDq-Swing-Breakout-Sequence-LuxAlgo",
        "https://www.luxalgo.com/library/indicator/Swing-Breakout-Sequence",
        "https://github.com/deepentropy/lightweight-charts-indicators/blob/main/src/community/swing-breakout-sequence.ts",
    ],
    "sourceNote": "Lógica dos swings e das sequências portada do port DE (fiel ao Pine, MPL-2.0). Os swings só existem quando a perna muda "
                  "(nova máxima/mínima de 'length' candles na direção oposta), então cada ponto é confirmado com atraso e nunca repinta. "
                  "O indicador não define entrada/stop; a página da LuxAlgo diz que a sequência 'antecipa a terceira tentativa' de sair da "
                  "zona. Regra de entrada da FILA: fechamento rompe A depois da sequência.",
    "rule": "Swings (perna de alta quando a máxima é a maior de 'length' candles, de baixa quando a mínima é a menor; ao mudar a perna, "
            "o extremo da perna anterior vira ponto) e pontos internos (comprimento 2). Sequência de alta: swing de alta A e de baixa B, "
            "ponto 1 (topo) acima de A, ponto 2 dentro de A-B, ponto 3 acima do 1, ponto 4 dentro de A-B e ponto 5 (fundo) a até "
            "thr*ATR200 do ponto 4 (fundo duplo). Depois da sequência, compra quando o fechamento passa acima de A em até 'window' candles; "
            "cancela se fechar abaixo de B. Venda espelhada (side=both). Stop: k*ATR14 ('atr') ou abaixo do ponto 5 menos 0,25*ATR14 "
            "('p5', no mínimo 0,5*ATR14). Alvo target_r em R; saída por tempo 3*window candles.",
    "timeframes": ["M15", "H1", "H4"],
    "grid": {"length": [3, 5, 8], "thr": [0.5, 1.0], "window": [10, 30], "stop": ["atr", "p5"], "k": [2.5],
             "target_r": [2.0, 3.0], "side": ["long", "both"]},
}

HIGH, LOW = 1, 0


def sequences(df, plen, ilen=2, thr=0.5):
    """Devolve lista de (i_detectado, bullish, A, B, p5) com i_detectado = candle em que a sequência fica conhecida."""
    h, l = df.high.values, df.low.values
    n = len(h)
    sh, sl = ind.highest(h, plen), ind.lowest(l, plen)
    ih, il = ind.highest(h, ilen), ind.lowest(l, ilen)
    atr200 = ind.atr(df, 200)
    sp, ip, out = [], [], []
    last_a = [-1]

    def inside(p, top, bot):
        return bot[0] <= p[0] <= top[0]

    def inside_lv(p, top, bot):
        return bot <= p[0] <= top

    def add(seq_pts, i, bull):
        a = seq_pts[0]
        if a[1] > last_a[0]:
            last_a[0] = a[1]
            out.append((i, bull, a[0], seq_pts[1][0], seq_pts[-1][0]))

    def gather_internal(i, st):
        if len(sp) < 6:
            return
        a, b, p1, p2, p3, p4 = sp[-6:]

        def dbl(top, bot):
            for e in ip:
                if e[1] > p4[1] and e[2] == p4[2] and inside_lv(e, p4[0] + st, p4[0] - st):
                    return e
            return None
        dt, db = dbl(b, a), dbl(a, b)
        bear = p1[2] == LOW and inside(p1, a, p3) and inside(p2, b, a) and inside(p4, b, a) and dt is not None
        bull = p1[2] == HIGH and inside(p1, p3, a) and inside(p2, a, b) and inside(p4, a, b) and db is not None
        if bull or bear:
            add([a, b, p1, p2, p3, p4, db if bull else dt], i, bull)

    def gather_swing(i, st):
        if len(sp) < 8:
            return
        a, b, p1, p2, p3, p4, _, p6 = sp[-8:]
        near = inside_lv(p6, p4[0] + st, p4[0] - st)
        bear = p1[2] == LOW and inside(p1, a, p3) and inside(p2, b, a) and inside(p4, b, a) and near
        bull = p1[2] == HIGH and inside(p1, p3, a) and inside(p2, a, b) and inside(p4, a, b) and near
        if bull or bear:
            add([a, b, p1, p2, p3, p4, p6], i, bull)

    sleg = ileg = 0
    psleg = pileg = None
    leg_i, leg_h, leg_l = 0, h[0], l[0]
    ileg_i, ileg_h, ileg_l = 0, h[0], l[0]
    for i in range(n):
        st = thr * atr200[i]
        if h[i] == sh[i]:
            sleg = 1
        elif l[i] == sl[i]:
            sleg = 0
        sch = None if psleg is None else sleg - psleg
        psleg = sleg
        if h[i] == ih[i]:
            ileg = 1
        elif l[i] == il[i]:
            ileg = 0
        ich = None if pileg is None else ileg - pileg
        pileg = ileg
        i_low, i_high = ich == 1, ich == -1
        if ich:
            pt = (ileg_l if i_low else ileg_h, ileg_i, LOW if i_low else HIGH)
            if len(ip) >= plen:
                ip.pop(0)
            ip.append(pt)
            if not np.isnan(st):
                gather_internal(i, st)
        ileg_h = h[i] if i_low else max(h[i], ileg_h)
        ileg_l = l[i] if i_high else min(l[i], ileg_l)
        if (ileg == 1 and ileg_h == h[i]) or (ileg == 0 and ileg_l == l[i]):
            ileg_i = i
        p_low, p_high = sch == 1, sch == -1
        if sch:
            pt = (leg_l if p_low else leg_h, leg_i, LOW if p_low else HIGH)
            if len(sp) >= 8:
                sp.pop(0)
            sp.append(pt)
            if not np.isnan(st):
                gather_swing(i, st)
        leg_h = h[i] if p_low else max(h[i], leg_h)
        leg_l = l[i] if p_high else min(l[i], leg_l)
        if (sleg == 1 and leg_h == h[i]) or (sleg == 0 and leg_l == l[i]):
            leg_i = i
    return out


def signals(df, p):
    c = df.close.values
    n = len(c)
    a14 = ind.atr(df, 14)
    seqs = sequences(df, p["length"], 2, p["thr"])
    by_i = {}
    for s in seqs:
        by_i.setdefault(s[0], []).append(s)
    entry = np.zeros(n, dtype=np.int8)
    stop = p["k"] * a14
    stop = stop.copy()
    W = p["window"]
    act = {True: None, False: None}  # bullish -> (i0, A, B, p5)
    for i in range(n):
        for s in by_i.get(i, []):
            act[s[1]] = (i, s[2], s[3], s[4])
        for bull in (True, False):
            s = act[bull]
            if s is None:
                continue
            i0, A, B, p5 = s
            if i - i0 > W or (bull and c[i] < B) or (not bull and c[i] > B):
                act[bull] = None
                continue
            if (bull and c[i] > A) or (not bull and c[i] < A):
                if entry[i] == 0:
                    entry[i] = 1 if bull else -1
                    if p["stop"] == "p5" and not np.isnan(a14[i]):
                        d = (c[i] - p5) if bull else (p5 - c[i])
                        stop[i] = max(d + 0.25 * a14[i], 0.5 * a14[i])
                act[bull] = None
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": stop, "target_r": p["target_r"], "max_hold": 3 * W}
