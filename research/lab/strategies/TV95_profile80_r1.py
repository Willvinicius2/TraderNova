"""TV95 refinamento 1 - regra dos 80% só em mercado em rotação (eficiência de Kaufman baixa)."""
import numpy as np

import indicators as ind
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("tv95_base", Path(__file__).with_name("TV95_profile80.py"))
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)

META = dict(_base.META)
META.update({
    "id": "TV95_profile80_r1",
    "name": "Regra dos 80% do Market Profile com filtro de mercado em rotação",
    "refines": "TV95_profile80",
    "refinement": "No desenvolvimento a regra pura ficou perto de zero (PF 0,94-1,02) em todas as combinações. Dalton descreve a regra dos 80% para "
                  "mercado em equilíbrio (rotação); em tendência a volta à value area falha. Filtro: só entra se a razão de eficiência de "
                  "Kaufman das últimas 48 horas (|fech - fech 48h antes| / soma das variações absolutas) for <= er. Saída fixa no fim do dia.",
    "rule": _base.META["rule"] + " Filtro r1: eficiência de Kaufman de 48 candles H1 <= er (mercado sem tendência).",
    "grid": {"va": [65, 70, 75], "conf": [1, 2, 3], "b": [0.5, 1.0], "er": [0.15, 0.25, 0.35], "side": ["long", "both"]},
})


def signals(df, p):
    q = dict(p)
    q["saida"] = "dia"
    sig = _base.signals(df, q)
    c = df.close.values
    n = 48
    net = np.abs(c - ind.prev(c, n))
    path = __import__("pandas").Series(np.abs(np.r_[np.nan, np.diff(c)])).rolling(n).sum().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        er = net / path
    ok = er <= p["er"]
    sig["entry"] = np.where(ok, sig["entry"], 0)
    return sig
