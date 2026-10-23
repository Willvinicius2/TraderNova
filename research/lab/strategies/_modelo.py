"""Modelo de estratégia do laboratório (não é testada; arquivos com _ são ignorados).

Copie para strategies/<id>.py. Regras:
- signals() só pode usar dados até o fechamento do candle i para decidir o valor em i (nada de shift(-1)).
- entry[i] = +1 compra / -1 venda / 0 nada, executado na abertura de i+1 pelo motor.
- stop[i] = distância do stop em preço (>0). Sem stop não há operação.
- Opcionais: target_r (alvo em R), target (array), exit_long/exit_short (bool por candle),
  max_hold (candles), trail (distância de stop móvel por candle).
"""
import numpy as np

import indicators as ind

META = {
    "id": "_modelo",
    "name": "Cruzamento de médias (modelo)",
    "family": "tendencia",
    "sources": ["https://exemplo"],
    "rule": "Compra quando SMA rápida cruza acima da lenta; vende no inverso; stop k*ATR; sai no cruzamento oposto.",
    "timeframes": ["H4", "D1"],
    "grid": {"fast": [10, 20], "slow": [50, 100], "k": [2.0, 3.0], "side": ["long", "both"]},
}


def signals(df, p):
    c = df.close.values
    f, s = ind.sma(c, p["fast"]), ind.sma(c, p["slow"])
    up = ind.cross_above(f, s)
    dn = ind.cross_below(f, s)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a = ind.atr(df, 14)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": dn, "exit_short": up}
