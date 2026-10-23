"""Z-score do fechamento contra a média móvel, entrada no extremo e saída na média."""
import numpy as np

import indicators as ind

META = {
    "id": "L32_zscore_revert",
    "name": "Z-score contra a média: entra no extremo, sai na média",
    "family": "reversao",
    "round": 8,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://it.tradingview.com/script/ymvBzYSw-Z-Score-Mean-Reversion-Strategy",
        "https://doc.stocksharp.com/en/api-examples/0218_ZScore_Reversal",
        "Definição clássica: z = (preço - média)/desvio-padrão (reversão à média; ver Ernest Chan, Algorithmic Trading, Wiley 2013, cap. 2)",
    ],
    "rule": ("z = (fech - SMA(fech,n))/desvio-padrão(fech,n). Compra quando z cruza abaixo de -zin (entra no extremo, sem esperar "
             "voltar para dentro da banda, diferente do G3); vende (side=both) quando z cruza acima de +zin. Sai na média: a compra sai "
             "quando z >= 0 e a venda quando z <= 0. Stop de proteção k*ATR14 (a fonte usa stop percentual fixo; aqui ATR para "
             "servir a vários tempos gráficos)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [20, 50, 100], "zin": [1.5, 2.0, 2.5], "k": [2.0, 3.0, 4.0], "side": ["long", "both"]},
}

_cache = {}


def signals(df, p):
    key = (id(df), len(df), p["n"])
    c = df.close.values
    if key not in _cache:
        m, s = ind.sma(c, p["n"]), ind.stdev(c, p["n"])
        with np.errstate(invalid="ignore", divide="ignore"):
            _cache[key] = ((c - m) / s, ind.atr(df, 14))
    z, a = _cache[key]
    N = len(z)
    el = ind.cross_below(z, np.full(N, -p["zin"]))
    es = ind.cross_above(z, np.full(N, p["zin"]))
    entry = np.where(el, 1, np.where(es, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": z >= 0, "exit_short": z <= 0}
