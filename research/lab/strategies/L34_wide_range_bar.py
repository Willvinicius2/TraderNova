"""L34 - Reversão após Wide Range Bar (candle de range anormal)."""
import numpy as np

import indicators as ind

META = {
    "id": "L34_wide_range_bar",
    "name": "Reversão após Wide Range Bar (exaustão)",
    "family": "reversao",
    "round": 8,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://www.luxalgo.com/library/concept/wide-range-bar/",
        "https://dotnettutorials.net/lesson/wrb-trading-strategy/",
    ],
    "rule": ("Wide Range Bar (definição da LuxAlgo): range (máx-mín) > k x média do range dos 20 candles anteriores; a direção vem "
             "da posição do fechamento (CLV = ((fech-mín)-(máx-fech))/range): WRB de baixa fecha no terço de baixo (CLV <= -0,5) e "
             "abaixo da abertura; WRB de alta no espelho. Uso de reversão descrito pela fonte: WRB no fim de um movimento estendido "
             "sinaliza exaustão. Compra após WRB de baixa (venda após WRB de alta, side=both). ctx='ext' exige que o WRB vá a favor "
             "de um movimento já estendido (fechamento abaixo da SMA50 para WRB de baixa, acima para de alta); ctx='none' não "
             "filtra. confirm='imediato' entra na abertura seguinte ao WRB; 'confirmado' espera o candle seguinte fechar no sentido "
             "da reversão (fech > abert e > fechamento do WRB na compra) e entra na abertura depois dele (versão fechada da "
             "sugestão 'esperar o candle seguinte segurar'). Stop além do extremo do WRB (e do candle de confirmação) + 0,25*ATR14, "
             "mínimo 0,5*ATR14; alvo target_r em R; saída por tempo em 10 candles. Diferente de TV06 outside bar, TV66 pin bar e "
             "TV64 three bar: o gatilho é só o tamanho anormal do range e o fechamento no extremo, sem padrão de dois/três candles."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"k": [1.75, 2.0, 2.5, 3.0], "ctx": ["none", "ext"], "confirm": ["imediato", "confirmado"],
             "target_r": [1.0, 1.5, 2.0], "side": ["long", "both"]},
}


def signals(df, p):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    rng = h - l
    avg = ind.prev(ind.sma(rng, 20))
    with np.errstate(invalid="ignore", divide="ignore"):
        clv = np.where(rng > 0, ((c - l) - (h - c)) / rng, 0.0)
        wrb = rng > p["k"] * avg
    s50 = ind.sma(c, 50)
    bear = wrb & (clv <= -0.5) & (c < o)
    bull = wrb & (clv >= 0.5) & (c > o)
    if p["ctx"] == "ext":
        with np.errstate(invalid="ignore"):
            bear &= c < s50
            bull &= c > s50
    a = ind.atr(df, 14)
    if p["confirm"] == "imediato":
        long_ = bear
        short_ = bull
        lo_ext, hi_ext = l, h
    else:
        pb, pu = ind.prev(bear.astype(float)) == 1, ind.prev(bull.astype(float)) == 1
        pc = ind.prev(c)
        long_ = pb & (c > o) & (c > pc)
        short_ = pu & (c < o) & (c < pc)
        lo_ext = np.fmin(l, ind.prev(l))
        hi_ext = np.fmax(h, ind.prev(h))
    entry = np.where(long_, 1, np.where(short_, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    dist = np.where(entry > 0, c - lo_ext, hi_ext - c) + 0.25 * a
    stop = np.maximum(dist, 0.5 * a)
    return {"entry": entry, "stop": stop, "target_r": p["target_r"], "max_hold": 10}
