"""H01: ensemble de rompimentos de Donchian com alvo de volatilidade, comprado e vendido.

Fonte: Zarattini, Pagani e Barbon (2025), "Catching Crypto Trends: A Tactical Approach for Bitcoin and Altcoins"
(Concretum Group). O artigo é só comprado; aqui o lado vendido é a extensão que queremos testar.

Regra (D1, decisão no fechamento, execução na abertura seguinte via backtest com lag=1):
- Para cada janela n em JANELAS: entra comprado quando o fechamento iguala ou supera a máxima das n barras
  anteriores; sai quando o fechamento cai abaixo do stop móvel = meio do canal (que só sobe enquanto comprado).
  Vendido é o espelho (mínima de n barras, stop no meio do canal que só desce).
- Modo "so_long": sem vendido. "simetrico": os dois lados. "mm200": comprado só acima da média de 200 dias e
  vendido só abaixo.
- Posição final = média dos sinais das janelas × alvo_vol / vol realizada (janela vol_janela), teto 2×.
Grade fixada antes de rodar: alvo_vol × modo × vol_janela = 18 variantes.
"""
import numpy as np
import pandas as pd

ID = "H01_donchian_ensemble"
NOME = "Ensemble de Donchian (5 a 360 dias) com alvo de volatilidade, comprado e vendido"
FONTE = "Zarattini, Pagani e Barbon (2025), Catching Crypto Trends; extensão long/short do relatório GitHub do projeto"
FREQ = "1D"
ATIVOS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
JANELAS = [5, 10, 20, 30, 60, 90, 150, 250, 360]
GRADE = {"alvo_vol": [0.15, 0.20, 0.25], "modo": ["so_long", "simetrico", "mm200"], "vol_janela": [30, 90]}
TETO = 2.0


def _sinal_janela(h: np.ndarray, l: np.ndarray, c: np.ndarray, n: int, pode_long: np.ndarray, pode_short: np.ndarray) -> np.ndarray:
    hi = pd.Series(h).rolling(n).max().shift(1).to_numpy()
    lo = pd.Series(l).rolling(n).min().shift(1).to_numpy()
    meio = (pd.Series(h).rolling(n).max() + pd.Series(l).rolling(n).min()).to_numpy() / 2
    out = np.zeros(len(c))
    pos, stop = 0, np.nan
    for i in range(len(c)):
        if np.isnan(hi[i]):
            continue
        if pos == 1:
            stop = max(stop, meio[i])
            if c[i] < stop:
                pos = 0
        elif pos == -1:
            stop = min(stop, meio[i])
            if c[i] > stop:
                pos = 0
        if pos == 0:
            if c[i] >= hi[i] and pode_long[i]:
                pos, stop = 1, meio[i]
            elif c[i] <= lo[i] and pode_short[i]:
                pos, stop = -1, meio[i]
        out[i] = pos
    return out


_CACHE: dict = {}


def _ensemble(df: pd.DataFrame, modo: str) -> np.ndarray:
    chave = (hash(df.close.to_numpy(dtype=float).tobytes()), hash(df.high.to_numpy(dtype=float).tobytes()), modo)
    if chave in _CACHE:
        return _CACHE[chave]
    h, l, c = (df[k].to_numpy(dtype=float) for k in ("high", "low", "close"))
    n = len(c)
    if modo == "so_long":
        pl, ps = np.ones(n, bool), np.zeros(n, bool)
    elif modo == "simetrico":
        pl, ps = np.ones(n, bool), np.ones(n, bool)
    else:
        mm = pd.Series(c).rolling(200).mean().to_numpy()
        pl, ps = c > mm, c < mm
    s = np.mean([_sinal_janela(h, l, c, j, pl, ps) for j in JANELAS], axis=0)
    if len(_CACHE) > 64:
        _CACHE.clear()
    _CACHE[chave] = s
    return s


def posicao(df: pd.DataFrame, alvo_vol: float, modo: str, vol_janela: int) -> np.ndarray:
    s = _ensemble(df, modo)
    r = df.close.pct_change()
    vol = r.rolling(vol_janela, min_periods=vol_janela // 2).std().to_numpy() * np.sqrt(365)
    alav = np.clip(np.where(vol > 0, alvo_vol / np.where(vol > 0, vol, 1), 0), 0, TETO)
    return np.nan_to_num(s * alav)
