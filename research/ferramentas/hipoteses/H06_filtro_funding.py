"""H06: filtro de funding sobre o momentum H02. Funding alto = comprados alavancados demais = risco de queda.

Fonte: Schmeling, Schrimpf e Todorov (2023), "Crypto Carry" (BIS Working Paper 1087): funding/carry alto prevê
quedas e liquidações. Hipótese 6 do relatório GitHub do projeto.

Regra (D1): parte da posição do H02 em modo "so_long", sem banda. Mede o funding médio de 7 dias (soma diária das
cobranças, média de 7 dias). Quando ele está acima do percentil `pct` do próprio histórico até aquele dia (janela
expansível, mínimo 180 dias):
- acao "zerar": não fica comprado;
- acao "vender": fica vendido com o mesmo tamanho que o momentum daria (ou 0,5 do alvo se o momentum estiver zerado).
Grade fixada antes de rodar: acao × pct = 4 variantes. Só faz sentido no perpétuo (precisa de funding_rate).
"""
import numpy as np
import pandas as pd

from importlib import util as _u
from pathlib import Path as _P

_s = _u.spec_from_file_location("H02", _P(__file__).with_name("H02_tsmom_ensemble.py"))
H02 = _u.module_from_spec(_s)
_s.loader.exec_module(H02)

ID = "H06_filtro_funding"
NOME = "Momentum comprado com filtro de funding alto (zera ou vende)"
FONTE = "Schmeling, Schrimpf e Todorov, Crypto Carry (BIS WP 1087); hipótese 6 do relatório GitHub do projeto"
FREQ = "1D"
ATIVOS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
GRADE = {"acao": ["zerar", "vender"], "pct": [0.8, 0.9]}


def funding_alto(df: pd.DataFrame, pct: float) -> np.ndarray:
    f7 = df.funding_rate.rolling(7).mean()
    limite = f7.expanding(min_periods=180).quantile(pct)
    return (f7 > limite).to_numpy()


def posicao(df: pd.DataFrame, acao: str, pct: float) -> np.ndarray:
    alav = H02.alavancagem(df)
    base = np.nan_to_num(H02.sinal_bruto(df, "so_long") * alav)
    alto = funding_alto(df, pct)
    if acao == "zerar":
        return np.where(alto, 0.0, base)
    return np.where(alto, -np.maximum(base, 0.5 * alav), base)
