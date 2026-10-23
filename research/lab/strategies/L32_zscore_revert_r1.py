"""Z-score do fechamento contra a média móvel, entrada no extremo e saída na média."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "L32_zscore_revert_r1",
    "refines": "L32_zscore_revert",
    "refinement": "No desenvolvimento a entrada no extremo perdeu em H1/H4 (PF < 1): no BTC o z alto costuma ser começo de tendência. Filtro de regime lateral: só entra quando a eficiência de Kaufman (ER) dos últimos n candles está abaixo de er (mercado sem direção).",
    "name": "Z-score contra a média em regime lateral (ER de Kaufman)",
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
             "servir a vários tempos gráficos). Refinamento r1: só entra se ER(n) = |fech - fech[n]| / soma(|fech - fech[1]|, n) < er."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [20, 50, 100], "zin": [1.5, 2.0, 2.5], "er": [0.2, 0.3, 0.4], "k": [2.0, 3.0], "side": ["long", "both"]},
}

_cache = {}


def signals(df, p):
    key = (id(df), len(df), p["n"])
    c = df.close.values
    if key not in _cache:
        m, s = ind.sma(c, p["n"]), ind.stdev(c, p["n"])
        with np.errstate(invalid="ignore", divide="ignore"):
            d = np.abs(np.diff(c, prepend=np.nan))
            er = np.abs(c - ind.prev(c, p["n"])) / pd.Series(d).rolling(p["n"]).sum().to_numpy()
            _cache[key] = ((c - m) / s, ind.atr(df, 14), er)
    z, a, er = _cache[key]
    N = len(z)
    el = ind.cross_below(z, np.full(N, -p["zin"]))
    es = ind.cross_above(z, np.full(N, p["zin"]))
    calm = er < p["er"]
    entry = np.where(el & calm, 1, np.where(es & calm, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": z >= 0, "exit_short": z <= 0}
