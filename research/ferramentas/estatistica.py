"""Camada estatística da validação: corrige o "melhor de muitas tentativas" e mede a robustez.

Cada função é pequena e testada em research/ferramentas/testes/. Fontes:
- PSR, DSR, MinTRL: Bailey e López de Prado (2012, 2014), "The Sharpe Ratio Efficient Frontier" e
  "The Deflated Sharpe Ratio". Implementação própria (pypbo é AGPL e não está no PyPI).
- PBO por CSCV: Bailey, Borwein, López de Prado e Zhu (2015), "The Probability of Backtest Overfitting".
- SPA: Hansen (2005), via arch.bootstrap.SPA (licença NCSA).
- MCPT com permutação de barras: ideia e algoritmo de github.com/neurotrader888/mcpt (MIT), reescrito aqui.
- CPCV: López de Prado (2018), "Advances in Financial Machine Learning", cap. 12.

Convenções: retornos são frações por barra (0,01 = 1%). Sharpe "por barra" (sem anualizar) nas fórmulas
de PSR/DSR, como nos artigos; `sharpe_anual` só para relatório.
"""
from __future__ import annotations

import itertools
import math
from typing import Callable, Iterable

import numpy as np
import pandas as pd
from scipy import stats

EULER = 0.5772156649015329


# --------------------------------------------------------------------------- métricas básicas

def sharpe(r: np.ndarray) -> float:
    r = np.asarray(r, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) < 2:
        return float("nan")
    sd = r.std(ddof=1)
    return float(r.mean() / sd) if sd > 0 else float("nan")


def sharpe_anual(r: np.ndarray, barras_por_ano: float) -> float:
    return sharpe(r) * math.sqrt(barras_por_ano)


def drawdown_max(r: np.ndarray, composto: bool = True) -> float:
    """Maior queda do patrimônio (fração positiva). composto=False usa soma simples (como o laboratório em R)."""
    r = np.nan_to_num(np.asarray(r, dtype=float))
    eq = np.cumprod(1 + r) if composto else 1 + np.cumsum(r)
    pico = np.maximum.accumulate(np.r_[1.0, eq])[1:]
    return float(np.max(1 - eq / pico)) if len(eq) else 0.0


def profit_factor(trades: np.ndarray) -> float:
    t = np.asarray(trades, dtype=float)
    ganho, perda = t[t > 0].sum(), -t[t < 0].sum()
    return float(ganho / perda) if perda > 0 else float("inf")


# --------------------------------------------------------------------------- PSR, DSR, MinTRL

def _momentos(r: np.ndarray) -> tuple[float, int, float, float]:
    r = np.asarray(r, dtype=float)
    r = r[~np.isnan(r)]
    return sharpe(r), len(r), float(stats.skew(r)), float(stats.kurtosis(r, fisher=False))


def psr(r: np.ndarray, sr_ref: float = 0.0) -> float:
    """Probabilidade de o Sharpe verdadeiro ser maior que sr_ref (por barra), dada assimetria e curtose."""
    sr, n, g3, g4 = _momentos(r)
    den = 1 - g3 * sr + (g4 - 1) / 4 * sr**2
    if n < 3 or den <= 0 or not np.isfinite(sr):
        return float("nan")
    return float(stats.norm.cdf((sr - sr_ref) * math.sqrt(n - 1) / math.sqrt(den)))


def sharpe_maximo_esperado(n_tentativas: int, var_sharpes: float) -> float:
    """E[max SR] de n tentativas sem habilidade nenhuma (Sharpe verdadeiro zero), por barra."""
    if n_tentativas < 2:
        return 0.0
    n = n_tentativas
    return math.sqrt(var_sharpes) * ((1 - EULER) * stats.norm.ppf(1 - 1 / n) + EULER * stats.norm.ppf(1 - 1 / (n * math.e)))


def dsr(r: np.ndarray, n_tentativas: int, var_sharpes: float | None = None) -> dict:
    """Deflated Sharpe: PSR contra o Sharpe que o melhor de n tentativas teria por sorte.

    var_sharpes: variância dos Sharpes (por barra) das tentativas. Sem ela, usa a variância do estimador
    sob a hipótese nula, 1/(T-1), que é o mínimo razoável (a real costuma ser maior, então isto é otimista)."""
    sr, n, _, _ = _momentos(r)
    v = var_sharpes if var_sharpes and var_sharpes > 0 else 1 / (n - 1)
    ref = sharpe_maximo_esperado(n_tentativas, v)
    return {"dsr": psr(r, ref), "srEsperadoPorSorte": ref, "sr": sr, "nTentativas": n_tentativas,
            "varSharpes": v, "varEstimadaDaNula": not (var_sharpes and var_sharpes > 0)}


def min_trl(r: np.ndarray, sr_ref: float = 0.0, confianca: float = 0.95) -> float:
    """Número mínimo de barras para o Sharpe observado ser significativo contra sr_ref."""
    sr, _, g3, g4 = _momentos(r)
    if not sr > sr_ref:
        return float("inf")
    z = stats.norm.ppf(confianca)
    return float(1 + (1 - g3 * sr + (g4 - 1) / 4 * sr**2) * (z / (sr - sr_ref)) ** 2)


# --------------------------------------------------------------------------- PBO por CSCV

def pbo(matriz: np.ndarray, s: int = 16, metrica: Callable[[np.ndarray], np.ndarray] | None = None) -> dict:
    """Probabilidade de overfitting do backtest (CSCV).

    matriz: T x N, retornos por barra de N variantes testadas (todas, inclusive as descartadas).
    Divide as linhas em s blocos; para cada metade escolhida como dentro da amostra, pega a melhor variante
    e vê a posição dela fora da amostra. PBO = fração das combinações em que a melhor ficou abaixo da mediana."""
    m = np.nan_to_num(np.asarray(matriz, dtype=float))
    t, n = m.shape
    if n < 2:
        raise ValueError("PBO precisa de pelo menos 2 variantes")
    s = s - s % 2
    blocos = np.array_split(np.arange(t - t % s), s)
    if metrica is None:
        def metrica(x):
            sd = x.std(axis=0, ddof=1)
            return np.where(sd > 0, x.mean(axis=0) / np.where(sd > 0, sd, 1), -np.inf)
    lambdas, degradacao = [], []
    for combo in itertools.combinations(range(s), s // 2):
        dentro = np.concatenate([blocos[i] for i in combo])
        fora = np.concatenate([blocos[i] for i in range(s) if i not in combo])
        md, mf = metrica(m[dentro]), metrica(m[fora])
        melhor = int(np.argmax(md))
        rank = (stats.rankdata(mf)[melhor]) / (n + 1)
        lambdas.append(math.log(rank / (1 - rank)))
        degradacao.append((md[melhor], mf[melhor]))
    lam = np.array(lambdas)
    d = np.array(degradacao)
    return {"pbo": float(np.mean(lam <= 0)), "combinacoes": len(lam), "variantes": n, "blocos": s,
            "logitMediano": float(np.median(lam)),
            "sharpeDentroMedio": float(np.mean(d[:, 0])), "sharpeForaMedio": float(np.mean(d[:, 1]))}


# --------------------------------------------------------------------------- Hansen SPA (arch)

def spa(retornos_variantes: np.ndarray, referencia: np.ndarray | None = None, reps: int = 10000,
        bloco: int | None = None, semente: int = 7) -> dict:
    """Teste SPA de Hansen: alguma variante bate a referência (padrão: ficar fora do mercado) além do acaso?

    Usa bootstrap estacionário do arch. p < 0,05 → existe ao menos uma variante melhor que a referência,
    já levando em conta que todas foram testadas."""
    from arch.bootstrap import SPA

    m = np.nan_to_num(np.asarray(retornos_variantes, dtype=float))
    if m.ndim == 1:
        m = m[:, None]
    ref = np.zeros(len(m)) if referencia is None else np.nan_to_num(np.asarray(referencia, dtype=float))
    bloco = bloco or max(1, int(round(len(m) ** (1 / 3))))
    teste = SPA(-ref, -m, reps=reps, block_size=bloco, bootstrap="stationary", seed=semente)
    teste.compute()
    p = teste.pvalues
    return {"pConsistente": float(p["consistent"]), "pInferior": float(p["lower"]), "pSuperior": float(p["upper"]),
            "variantes": m.shape[1], "reps": reps, "bloco": bloco}


# --------------------------------------------------------------------------- bootstrap dos trades

def bootstrap_trades(trades: np.ndarray, reps: int = 10000, semente: int = 7, composto: bool = False) -> dict:
    """Reamostra a sequência de trades (com reposição) e devolve a distribuição de queda e PF.

    trades em fração da conta (ex.: 0,005 = +0,5%). composto=False soma (como o laboratório)."""
    t = np.asarray(trades, dtype=float)
    if len(t) < 5:
        return {"trades": len(t), "erro": "poucos trades"}
    rng = np.random.default_rng(semente)
    amostras = t[rng.integers(0, len(t), size=(reps, len(t)))]
    eq = np.cumprod(1 + amostras, axis=1) if composto else 1 + np.cumsum(amostras, axis=1)
    pico = np.maximum.accumulate(np.concatenate([np.ones((reps, 1)), eq], axis=1), axis=1)[:, 1:]
    dd = np.max(1 - eq / pico, axis=1)
    ganho = np.where(amostras > 0, amostras, 0).sum(axis=1)
    perda = -np.where(amostras < 0, amostras, 0).sum(axis=1)
    pf = np.where(perda > 0, ganho / np.where(perda > 0, perda, 1), np.inf)
    return {"trades": len(t), "reps": reps, "ddP50": float(np.percentile(dd, 50)), "ddP95": float(np.percentile(dd, 95)),
            "pfP5": float(np.percentile(pf, 5)), "pfP50": float(np.percentile(pf, 50)),
            "probPrejuizo": float(np.mean(amostras.sum(axis=1) <= 0))}


# --------------------------------------------------------------------------- MCPT (permutação de barras)

def permutar_barras(df: pd.DataFrame, inicio: int = 0, semente: int | None = None) -> pd.DataFrame:
    """Embaralha as barras a partir de `inicio`, preservando a distribuição de cada barra mas destruindo a ordem.

    Separa o salto de abertura (abertura vs. fechamento anterior) do movimento dentro da barra (máxima, mínima e
    fechamento vs. abertura) e embaralha os dois de forma independente, como o bar_permute do neurotrader888.
    O preço inicial e o final ficam iguais aos originais. As barras antes de `inicio` não mudam."""
    rng = np.random.default_rng(semente)
    lo = np.log(df[["open", "high", "low", "close"]].to_numpy(dtype=float))
    n = len(lo)
    o, h, l, c = lo.T
    gap = o[1:] - c[:-1]
    rh, rl, rc = h - o, l - o, c - o
    idx = np.arange(inicio + 1, n) if inicio < n - 1 else np.array([], dtype=int)
    p1 = rng.permutation(len(idx))
    p2 = rng.permutation(len(idx))
    novo = lo.copy()
    for k, i in enumerate(idx):
        j_intra = idx[p1[k]]
        j_gap = idx[p2[k]]
        abertura = novo[i - 1, 3] + gap[j_gap - 1]
        novo[i] = [abertura, abertura + rh[j_intra], abertura + rl[j_intra], abertura + rc[j_intra]]
    out = df.copy()
    out[["open", "high", "low", "close"]] = np.exp(novo)
    return out


def mcpt(df: pd.DataFrame, pontuar: Callable[[pd.DataFrame], float], n: int = 200, inicio: int = 0,
         semente: int = 7) -> dict:
    """Teste de permutação Monte Carlo.

    pontuar(df) → número (ex.: PF ou Sharpe da MELHOR variante depois de otimizar em df). Repete em n séries
    embaralhadas. p = (1 + nº de permutações com pontuação ≥ real) / (1 + n). Para testar o processo inteiro
    (inclusive a escolha de parâmetros), `pontuar` deve reotimizar dentro de cada série."""
    real = pontuar(df)
    pts = [pontuar(permutar_barras(df, inicio, semente + k)) for k in range(n)]
    acima = int(np.sum(np.array(pts) >= real))
    return {"real": float(real), "p": (1 + acima) / (1 + n), "n": n, "mediaPermutada": float(np.nanmean(pts))}


# --------------------------------------------------------------------------- divisões no tempo

def walk_forward(indice: pd.DatetimeIndex, treino: str = "365D", teste: str = "90D", ancorado: bool = False,
                 inicio: pd.Timestamp | None = None) -> list[tuple[np.ndarray, np.ndarray]]:
    """Janelas (treino, teste) em posições inteiras. Teste começa logo após o treino; nada se sobrepõe."""
    tr, te = pd.Timedelta(treino), pd.Timedelta(teste)
    t0 = indice[0] if inicio is None else inicio
    cursor = t0 + tr
    out = []
    while cursor < indice[-1]:
        a = t0 if ancorado else cursor - tr
        i_tr = np.flatnonzero((indice >= a) & (indice < cursor))
        i_te = np.flatnonzero((indice >= cursor) & (indice < cursor + te))
        if len(i_te):
            out.append((i_tr, i_te))
        cursor += te
    return out


def cpcv(n_barras: int, grupos: int = 10, k: int = 2, embargo: int = 0) -> tuple[list, list]:
    """Combinatorial Purged CV. Devolve (divisões, caminhos).

    divisões: lista de (treino, teste) em posições; o treino exclui `embargo` barras depois de cada bloco de teste
    (e a barra imediatamente antes, para rótulos que olham 1 barra à frente).
    caminhos: lista de caminhos; cada caminho é uma lista de (índice da divisão, grupo) que cobre todos os grupos
    uma vez. Com grupos=10 e k=2 são 45 divisões e 9 caminhos."""
    bl = np.array_split(np.arange(n_barras), grupos)
    combos = list(itertools.combinations(range(grupos), k))
    divisoes = []
    for combo in combos:
        teste = np.concatenate([bl[g] for g in combo])
        proibido = np.zeros(n_barras, bool)
        for g in combo:
            a, b = bl[g][0], bl[g][-1]
            proibido[max(0, a - 1): min(n_barras, b + 1 + embargo)] = True
        divisoes.append((np.flatnonzero(~proibido), teste))
    n_caminhos = math.comb(grupos - 1, k - 1)
    uso = {g: [i for i, c in enumerate(combos) if g in c] for g in range(grupos)}
    caminhos = [[(uso[g][p], g) for g in range(grupos)] for p in range(n_caminhos)]
    return divisoes, caminhos


def cpcv_sharpes(n_barras: int, ajustar_e_testar: Callable[[np.ndarray, np.ndarray], np.ndarray], grupos: int = 10,
                 k: int = 2, embargo: int = 0) -> dict:
    """Roda CPCV: ajustar_e_testar(treino, teste) → retornos por barra no teste (mesma ordem de `teste`).
    Devolve o Sharpe de cada caminho fora da amostra."""
    divisoes, caminhos = cpcv(n_barras, grupos, k, embargo)
    bl = np.array_split(np.arange(n_barras), grupos)
    res = []
    for treino, teste in divisoes:
        r = np.asarray(ajustar_e_testar(treino, teste), dtype=float)
        res.append(dict(zip(teste.tolist(), r.tolist())))
    srs = []
    for cam in caminhos:
        r = np.array([res[d][i] for d, g in cam for i in bl[g]])
        srs.append(sharpe(r))
    srs = np.array(srs)
    return {"sharpesPorCaminho": srs.tolist(), "mediano": float(np.nanmedian(srs)),
            "fracaoPositivos": float(np.mean(srs > 0)), "caminhos": len(srs), "divisoes": len(divisoes)}


# --------------------------------------------------------------------------- lookahead

def checar_lookahead(sinal: Callable[[pd.DataFrame], Iterable], df: pd.DataFrame, pontos: int = 40,
                     minimo: int = 400, semente: int = 7) -> dict:
    """Recalcula o sinal só com os dados até cada ponto sorteado e compara com o sinal calculado na série toda.

    Qualquer diferença indica uso de dado futuro (ou dependência do tamanho da série, que também é problema).
    Inspirado no lookahead-analysis do freqtrade."""
    completo = np.asarray(sinal(df), dtype=float)
    rng = np.random.default_rng(semente)
    idx = np.sort(rng.choice(np.arange(minimo, len(df)), size=min(pontos, len(df) - minimo), replace=False))
    divergencias = []
    for i in idx:
        parcial = np.asarray(sinal(df.iloc[: i + 1]), dtype=float)
        a, b = parcial[-1], completo[i]
        if not (np.isclose(a, b, equal_nan=True)):
            divergencias.append({"barra": str(df.index[i]), "parcial": float(a), "completo": float(b)})
    return {"ok": not divergencias, "pontos": len(idx), "divergencias": divergencias[:10]}
