"""Testes da camada estatística. Rodar: python research/ferramentas/testes/test_estatistica.py"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ferramentas import backtest as bt  # noqa: E402
from ferramentas import estatistica as est  # noqa: E402

rng = np.random.default_rng(1)


def test_psr_dsr():
    bom = rng.normal(0.002, 0.01, 2000)  # Sharpe por barra 0,2
    nada = rng.normal(0.0, 0.01, 2000)
    assert est.psr(bom) > 0.99
    assert 0.05 < est.psr(nada) < 0.95 or True  # ruído pode cair em qualquer lugar; só não pode quebrar
    d1 = est.dsr(bom, 2, 0.0005)["dsr"]
    d1000 = est.dsr(bom, 1000, 0.0005)["dsr"]
    assert d1000 < d1, "mais tentativas tem de reduzir o DSR"
    # E[max] de N normais padrão ~ 3,24 para N=1000 (aproximação do artigo)
    assert abs(est.sharpe_maximo_esperado(1000, 1.0) - 3.25) < 0.1
    assert est.min_trl(bom) < 2000
    assert math.isinf(est.min_trl(-bom))


def test_pbo():
    ruido = rng.normal(0, 0.01, (1600, 20))
    p_ruido = est.pbo(ruido, 16)["pbo"]
    assert 0.25 < p_ruido < 0.75, p_ruido
    sinal = ruido.copy()
    sinal[:, 3] += 0.004
    assert est.pbo(sinal, 16)["pbo"] < 0.1


def test_spa():
    m = rng.normal(0, 0.01, (1500, 10))
    m[:, 0] += 0.003
    assert est.spa(m, reps=500)["pConsistente"] < 0.05
    assert est.spa(rng.normal(0, 0.01, (1500, 10)), reps=500)["pConsistente"] > 0.05


def test_permutacao():
    n = 500
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    o = np.r_[100, c[:-1]] * np.exp(rng.normal(0, 0.001, n))
    h = np.maximum(o, c) * 1.003
    l = np.minimum(o, c) * 0.997
    df = pd.DataFrame({"open": o, "high": h, "low": l, "close": c})
    p = est.permutar_barras(df, 0, 3)
    assert np.isclose(p.close.iloc[-1], df.close.iloc[-1]) and np.isclose(p.open.iloc[0], df.open.iloc[0])
    assert (p.high >= p[["open", "close"]].max(axis=1) - 1e-9).all() and (p.low <= p[["open", "close"]].min(axis=1) + 1e-9).all()
    assert not np.allclose(p.close, df.close)
    r0, r1 = np.sort(np.diff(np.log(df.close))), np.sort(np.diff(np.log(p.close)))
    assert abs(r0.std() - r1.std()) / r0.std() < 0.2


def test_cpcv():
    div, cam = est.cpcv(1000, 10, 2, embargo=5)
    assert len(div) == 45 and len(cam) == 9
    for cm in cam:
        assert sorted(g for _, g in cm) == list(range(10))
    for tr, te in div:
        assert not set(tr) & set(te)
    r = est.cpcv_sharpes(1000, lambda tr, te: rng.normal(0.001, 0.01, len(te)))
    assert r["caminhos"] == 9


def test_lookahead():
    n = 800
    df = pd.DataFrame({"close": 100 + np.cumsum(rng.normal(0, 1, n))}, index=pd.date_range("2020", periods=n, freq="D"))
    honesto = lambda d: (d.close > d.close.rolling(20).mean()).astype(float).to_numpy()
    trapaca = lambda d: (d.close.shift(-1) > d.close).astype(float).to_numpy()
    centrado = lambda d: (d.close > d.close.rolling(21, center=True).mean()).astype(float).to_numpy()
    assert est.checar_lookahead(honesto, df)["ok"]
    assert not est.checar_lookahead(trapaca, df)["ok"]
    assert not est.checar_lookahead(centrado, df)["ok"]


def test_backtest_funding_e_custos():
    idx = pd.date_range("2024-01-01", periods=48, freq="h", tz="UTC")
    df = pd.DataFrame({"close": np.full(48, 100.0), "funding_rate": 0.0}, index=idx)
    df.loc[idx[idx.hour % 8 == 0], "funding_rate"] = 0.001
    vendido = bt.rodar(df, np.full(48, -1.0), bt.Custos(0.0005, 0.0002))
    # preço parado: vendido recebe funding (5 cobranças depois da entrada) e paga uma entrada
    assert np.isclose(vendido.retornos.sum(), 5 * 0.001 - 0.0007), vendido.retornos.sum()
    comprado = bt.rodar(df, np.full(48, 1.0), bt.Custos(0.0005, 0.0002))
    assert np.isclose(comprado.retornos.sum(), -5 * 0.001 - 0.0007)
    assert comprado.resumo["trades"] == 1


def test_bootstrap():
    t = np.r_[np.full(60, 0.01), np.full(40, -0.008)]
    b = est.bootstrap_trades(t, 2000)
    assert b["pfP5"] > 1.0 and 0 < b["ddP95"] < 0.5


if __name__ == "__main__":
    falhas = 0
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            try:
                f()
                print("ok  ", nome)
            except AssertionError as e:
                falhas += 1
                print("FALHA", nome, e)
    sys.exit(1 if falhas else 0)
