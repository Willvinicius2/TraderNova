"""Backtest por posição, com taxa, slippage e funding do perpétuo. Feito para gerar a série de retornos que a
camada estatística precisa (uma coluna por variante).

Regras:
- `posicao[i]` é decidida no FECHAMENTO da barra i (só com dados até i) e vale durante a barra i+1
  (com lag=1). lag=2 é o teste de atraso: a mesma regra executada uma barra depois.
- Posição em múltiplos do capital: +1 = comprado 100%, -0,5 = vendido 50%. Alvo de volatilidade pode passar de 1
  até o teto definido pela estratégia.
- Custo = |variação da posição| × (taxa + slippage) por lado.
- Funding: em cada barra com cobrança, a posição em aberto paga posicao × taxa (comprado paga quando a taxa é
  positiva, vendido recebe). Sem coluna funding_rate (spot), não há funding e o vendido é hipotético.
- Retorno da barra = posição × variação do fechamento − custo − funding.
- Trade = trecho contínuo com o mesmo sinal de posição; o resultado do trade é a soma dos retornos do trecho.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import estatistica as est

BARRAS_ANO = {"1h": 24 * 365, "4h": 6 * 365, "1D": 365}


@dataclass
class Custos:
    taxa: float = 0.0005       # 0,05% por lado (taker USDT-M sem desconto de BNB)
    slippage: float = 0.0002   # 0,02% por lado em BTC/ETH; aumente para altcoins
    funding: bool = True

    def vezes(self, k: float) -> "Custos":
        return Custos(self.taxa * k, self.slippage * k, self.funding)


@dataclass
class Resultado:
    retornos: pd.Series
    posicao: pd.Series
    trades: pd.DataFrame
    resumo: dict = field(default_factory=dict)


def rodar(df: pd.DataFrame, posicao, custos: Custos = Custos(), lag: int = 1, freq: str = "1h") -> Resultado:
    pos_decidida = pd.Series(np.nan_to_num(np.asarray(posicao, dtype=float)), index=df.index)
    pos = pos_decidida.shift(lag).fillna(0.0)
    var = df["close"].pct_change().fillna(0.0)
    giro = pos.diff().abs().fillna(pos.abs())
    custo = giro * (custos.taxa + custos.slippage)
    fund = pos * df["funding_rate"] if (custos.funding and "funding_rate" in df) else 0.0
    r = pos * var - custo - fund
    trades = _trades(pos, r)
    return Resultado(r, pos, trades, resumir(r, pos, trades, freq))


def _trades(pos: pd.Series, r: pd.Series) -> pd.DataFrame:
    sinal = np.sign(pos.to_numpy())
    mudou = np.r_[True, sinal[1:] != sinal[:-1]]
    grupo = np.cumsum(mudou)
    d = pd.DataFrame({"g": grupo, "lado": sinal, "r": r.to_numpy(), "t": pos.index})
    d = d[d.lado != 0]
    if d.empty:
        return pd.DataFrame(columns=["inicio", "fim", "lado", "retorno", "barras"])
    t = d.groupby("g").agg(inicio=("t", "first"), fim=("t", "last"), lado=("lado", "first"), retorno=("r", "sum"),
                           barras=("r", "size"))
    return t.reset_index(drop=True)


def resumir(r: pd.Series, pos: pd.Series, trades: pd.DataFrame, freq: str = "1h") -> dict:
    tr = trades.retorno.to_numpy() if len(trades) else np.array([])
    lados = {}
    for nome, s in (("comprado", 1), ("vendido", -1)):
        sub = trades[trades.lado == s] if len(trades) else trades
        lados[nome] = {"trades": int(len(sub)), "retorno": float(sub.retorno.sum()) if len(sub) else 0.0,
                       "pf": est.profit_factor(sub.retorno.to_numpy()) if len(sub) else float("nan")}
    anos = r.groupby(r.index.year).apply(lambda x: float(np.prod(1 + x) - 1))
    return {
        "retornoTotal": float(np.prod(1 + r) - 1),
        "sharpeAnual": est.sharpe_anual(r.to_numpy(), BARRAS_ANO.get(freq, 24 * 365)),
        "ddMax": est.drawdown_max(r.to_numpy()),
        "trades": int(len(tr)),
        "pf": est.profit_factor(tr) if len(tr) else float("nan"),
        "exposicaoMedia": float(pos.abs().mean()),
        "porLado": lados,
        "porAno": {int(k): round(v, 4) for k, v in anos.items()},
        "anosPositivos": f"{int((anos > 0).sum())}/{len(anos)}",
    }


def alvo_vol(retornos_ativo: pd.Series, alvo_anual: float, janela: int, barras_ano: int, teto: float = 2.0) -> pd.Series:
    """Fator de alavancagem para mirar `alvo_anual` de volatilidade, com dados até a própria barra."""
    vol = retornos_ativo.rolling(janela, min_periods=janela // 2).std() * np.sqrt(barras_ano)
    return (alvo_anual / vol).clip(upper=teto).fillna(0.0)


def freio_drawdown(r_bruto: pd.Series, limite: float = 0.10, corte: float = 0.5) -> pd.Series:
    """Multiplicador de exposição: corta para `corte` quando a curva (do próprio sistema, até a barra anterior)
    está mais de `limite` abaixo do pico. Aplique sobre a posição, não sobre os retornos."""
    eq = (1 + r_bruto.fillna(0)).cumprod()
    dd = 1 - eq / eq.cummax()
    return pd.Series(np.where(dd.shift(1).fillna(0) > limite, corte, 1.0), index=r_bruto.index)
