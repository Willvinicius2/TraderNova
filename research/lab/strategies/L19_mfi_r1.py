"""L19 r1 - MFI com filtro de tendência (SMA200)."""
import numpy as np

import indicators as ind
from importlib import util as _u
from pathlib import Path as _P

_spec = _u.spec_from_file_location("_l19base", _P(__file__).with_name("L19_mfi.py"))
_base = _u.module_from_spec(_spec)
_spec.loader.exec_module(_base)

META = {
    "id": "L19_mfi_r1",
    "refines": "L19_mfi",
    "refinement": ("No desenvolvimento as compras na volta da sobrevenda perdiam em H1 e só funcionavam em poucas combinações "
                   "isoladas: a StockCharts avisa que em tendência forte o MFI fica preso no extremo. Filtro de tendência: "
                   "só compra com preço acima da SMA(200) e só vende abaixo dela."),
    "name": "Money Flow Index com filtro de tendência SMA200",
    "family": "tempo_volume",
    "sources": _base.META["sources"],
    "rule": ("Igual a L19_mfi (MFI(n) cruza de volta acima de lo para comprar / abaixo de 100-lo para vender; saída em 50 "
             "ou no nível oposto; stop k*ATR14), mas compras só com fechamento acima da SMA200 e vendas só abaixo. "
             "Volume só do Bitstamp."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": _base.META["grid"],
}


def signals(df, p):
    s = _base.signals(df, p)
    c = df.close.values
    t = ind.sma(c, 200)
    e = s["entry"]
    s["entry"] = np.where((e > 0) & (c > t), 1, np.where((e < 0) & (c < t), -1, 0))
    return s
