"""H02: momentum de série temporal em ensemble (7, 14 e 28 dias) com alvo de volatilidade e banda sem trade.

Fonte: Liu e Tsyvinski (2021), "Risks and Returns of Cryptocurrency" (NBER w24877): o retorno passado de 1 a 4
semanas prevê o retorno seguinte em cripto. Hipótese 2 do relatório de pesquisa GitHub do projeto.

Regra (D1, decisão no fechamento, execução na abertura seguinte):
- sinal = média de sign(retorno dos últimos n dias) para n em JANELAS (vai de -1 a +1).
- modo "so_long": sinais negativos viram 0. "simetrico": usa o sinal inteiro. "mm200": compra só acima da média
  de 200 dias e vende só abaixo.
- posição = sinal × alvo_vol / vol realizada de 30 dias, teto 2×. Alvo fixo em 15% (o Sharpe não depende dele).
- banda: só muda a posição quando a nova difere da atual em mais que `banda` (reduz giro e custo).
Grade fixada antes de rodar: modo × banda = 6 variantes.
"""
import numpy as np
import pandas as pd

ID = "H02_tsmom_ensemble"
NOME = "Momentum de série temporal (7/14/28 dias) com alvo de volatilidade, comprado e vendido"
FONTE = "Liu e Tsyvinski, Risks and Returns of Cryptocurrency (NBER w24877); hipótese 2 do relatório GitHub do projeto"
FREQ = "1D"
ATIVOS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
JANELAS = [7, 14, 28]
GRADE = {"modo": ["so_long", "simetrico", "mm200"], "banda": [0.0, 0.25]}
ALVO, TETO, VOL_JANELA = 0.15, 2.0, 30


def sinal_bruto(df: pd.DataFrame, modo: str) -> np.ndarray:
    c = df.close
    s = np.mean([np.sign(c.pct_change(n)).fillna(0).to_numpy() for n in JANELAS], axis=0)
    if modo == "so_long":
        s = np.clip(s, 0, None)
    elif modo == "mm200":
        mm = c.rolling(200).mean().to_numpy()
        s = np.where(c.to_numpy() > mm, np.clip(s, 0, None), np.where(c.to_numpy() < mm, np.clip(s, None, 0), 0))
    return s


def alavancagem(df: pd.DataFrame) -> np.ndarray:
    vol = df.close.pct_change().rolling(VOL_JANELA, min_periods=VOL_JANELA // 2).std().to_numpy() * np.sqrt(365)
    return np.clip(np.where(vol > 0, ALVO / np.where(vol > 0, vol, 1), 0), 0, TETO)


def com_banda(alvo: np.ndarray, banda: float) -> np.ndarray:
    if banda <= 0:
        return alvo
    out = np.zeros_like(alvo)
    atual = 0.0
    for i, a in enumerate(alvo):
        if abs(a - atual) > banda or (a == 0 and atual != 0 and np.sign(a) != np.sign(atual)):
            atual = a
        out[i] = atual
    return out


def posicao(df: pd.DataFrame, modo: str, banda: float) -> np.ndarray:
    return com_banda(np.nan_to_num(sinal_bruto(df, modo) * alavancagem(df)), banda)
