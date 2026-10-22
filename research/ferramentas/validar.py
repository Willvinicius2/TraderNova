"""Pipeline de validação: roda uma hipótese por todos os portões e grava um veredito em JSON.

Uma hipótese é um arquivo em research/ferramentas/hipoteses/<ID>.py com:
  ID, NOME, FONTE (de onde veio a ideia), FREQ ("1h", "4h" ou "1D"), ATIVOS (símbolos da Binance),
  GRADE (dict parâmetro → lista de valores, fixada ANTES de rodar), e
  posicao(df, **params) → array com a posição decidida no fechamento de cada barra (só dados até ela).

Passos (todos rodam; o veredito é a primeira reprovação, na ordem):
  0. pré-registro: hash do arquivo e da grade entra em tentativas.jsonl antes de qualquer número
  1. lookahead: sinal recalculado com dados truncados tem de bater com o da série toda
  2. grade inteira no desenvolvimento (antes de reservaInicio), carteira com peso igual entre ativos
  3. walk-forward: escolhe a melhor variante no treino, opera a janela seguinte; fora da amostra unido
  4. CPCV (escolha da melhor variante no treino de cada divisão), PBO por CSCV
  5. PSR e Deflated Sharpe com N = nHistorico + hipóteses registradas + tamanho da grade
  6. Hansen SPA de todas as variantes contra ficar fora do mercado
  7. MCPT: o processo inteiro (otimizar a grade) em séries embaralhadas
  8. bootstrap dos trades fora da amostra
  9. estresse: custo 2× e 3×, atraso de 1 barra, fração de vizinhos positivos
 10. reserva (de reservaInicio em diante): só com --abrir-reserva, uma vez por hash, e fica registrado

Uso:
  python research/ferramentas/validar.py H01_donchian_ensemble [--rapido] [--abrir-reserva]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))

from ferramentas import backtest as bt  # noqa: E402
from ferramentas import dados_binance as dados  # noqa: E402
from ferramentas import estatistica as est  # noqa: E402

CFG = json.loads((AQUI / "portoes.json").read_text())
REGISTRO = AQUI / "tentativas.jsonl"
SAIDA = AQUI / "resultados"


def carregar_hipotese(nome: str):
    p = AQUI / "hipoteses" / f"{nome}.py"
    spec = importlib.util.spec_from_file_location(nome, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, hashlib.sha256(p.read_bytes()).hexdigest()


def registro() -> list[dict]:
    if not REGISTRO.exists():
        return []
    return [json.loads(x) for x in REGISTRO.read_text().splitlines() if x.strip()]


def registrar(linha: dict):
    with REGISTRO.open("a") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")


def serie(sym: str, freq: str) -> pd.DataFrame:
    df = dados.carregar(sym)
    if freq == "1h":
        return df
    if freq == "1D":
        return dados.diario(df)
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum", "funding_rate": "sum"}
    return df.resample(freq).agg(agg).dropna(subset=["close"])


def variantes(grade: dict) -> list[dict]:
    chaves = list(grade)
    return [dict(zip(chaves, v)) for v in itertools.product(*(grade[k] for k in chaves))]


def carteira(h, series: dict, params: dict, custos: bt.Custos, lag: int = 1) -> tuple[pd.Series, pd.DataFrame]:
    """Peso igual entre ativos disponíveis em cada barra. Trades de todos os ativos juntos (retorno já ponderado)."""
    rets, trades = {}, []
    for sym, df in series.items():
        res = bt.rodar(df, h.posicao(df, **params), custos, lag, h.FREQ)
        rets[sym] = res.retornos
        t = res.trades.copy()
        t["ativo"] = sym
        trades.append(t)
    m = pd.DataFrame(rets)
    vivos = pd.DataFrame({s: series[s].index.to_series().reindex(m.index).notna() for s in series})
    r = m.fillna(0).sum(axis=1) / vivos.sum(axis=1).clip(lower=1)
    tr = pd.concat(trades, ignore_index=True)
    if len(tr):
        n_vivos = vivos.sum(axis=1).clip(lower=1)
        tr["retorno"] = tr.retorno / n_vivos.reindex(pd.DatetimeIndex(tr.inicio)).to_numpy()
    return r, tr


def resumo_trades(r: pd.Series, tr: pd.DataFrame, freq: str) -> dict:
    pos_fake = pd.Series(1.0, index=r.index)
    s = bt.resumir(r, pos_fake, tr, freq)
    s.pop("exposicaoMedia", None)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hipotese")
    ap.add_argument("--rapido", action="store_true", help="menos repetições (só para testar o código)")
    ap.add_argument("--abrir-reserva", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    h, sha = carregar_hipotese(a.hipotese)
    exe = dict(CFG["execucao"])
    if a.rapido:
        exe.update(spaReps=500, mcptN=20, bootstrapReps=1000)
    P = CFG["portoes"]
    vs = variantes(h.GRADE)
    anteriores = registro()

    # 0. pré-registro
    ja = [x for x in anteriores if x.get("sha256") == sha and x.get("tipo") == "pre-registro"]
    if not ja:
        registrar({"tipo": "pre-registro", "id": h.ID, "sha256": sha, "grade": h.GRADE, "variantes": len(vs),
                   "freq": h.FREQ, "ativos": h.ATIVOS, "em": pd.Timestamp.now(tz="UTC").isoformat()})
    hipoteses_previas = len({x["id"] for x in anteriores if x.get("tipo") == "pre-registro" and x["id"] != h.ID})
    n_tent = CFG["nHistorico"] + hipoteses_previas + len(vs)

    reserva = pd.Timestamp(CFG["reservaInicio"], tz="UTC")
    completas = {s: serie(s, h.FREQ) for s in h.ATIVOS}
    dev = {s: d[d.index < reserva] for s, d in completas.items()}
    custos = bt.Custos()
    out = {"id": h.ID, "nome": h.NOME, "fonte": h.FONTE, "sha256": sha, "freq": h.FREQ, "ativos": h.ATIVOS,
           "grade": h.GRADE, "variantes": len(vs), "portoes": CFG["versao"], "custos": vars(custos),
           "desenvolvimento": [str(min(d.index[0] for d in dev.values())), str(reserva)], "etapas": {}}
    E = out["etapas"]

    # 1. lookahead
    la = {s: est.checar_lookahead(lambda d: h.posicao(d, **vs[0]), df, pontos=25, minimo=min(400, len(df) // 3))
          for s, df in dev.items()}
    E["lookahead"] = {"ok": all(x["ok"] for x in la.values()), "porAtivo": la}

    # 2. grade inteira
    mat, trades_var = {}, {}
    for i, p in enumerate(vs):
        mat[i], trades_var[i] = carteira(h, dev, p, custos)
    M = pd.DataFrame(mat).fillna(0)
    bpa = bt.BARRAS_ANO[h.FREQ]
    sh = M.apply(lambda c: est.sharpe_anual(c.to_numpy(), bpa))
    E["grade"] = {"sharpeAnualPorVariante": [{"params": vs[i], "sharpe": round(float(sh[i]), 3)} for i in M.columns],
                  "fracaoPositivas": float((sh > 0).mean())}

    # 3. walk-forward
    wf = CFG["walkForward"][h.FREQ]
    janelas = est.walk_forward(M.index, wf["treino"], wf["teste"])
    oos, escolhas, efic, jpos = [], [], [], []
    for tr_i, te_i in janelas:
        s_tr = M.iloc[tr_i].apply(lambda c: est.sharpe(c.to_numpy()))
        k = int(s_tr.idxmax())
        r_te = M.iloc[te_i][k]
        oos.append(r_te)
        escolhas.append({"teste": str(M.index[te_i[0]].date()), "params": vs[k]})
        jpos.append(float(r_te.sum()) > 0)
        efic.append((est.sharpe(r_te.to_numpy()), float(s_tr.max())))
    r_oos = pd.concat(oos)
    ini_oos = r_oos.index[0]
    tr_oos = []
    for (tr_i, te_i), e in zip(janelas, escolhas):
        k = vs.index(e["params"])
        t = trades_var[k]
        a0, a1 = M.index[te_i[0]], M.index[te_i[-1]]
        tr_oos.append(t[(pd.DatetimeIndex(t.inicio) >= a0) & (pd.DatetimeIndex(t.inicio) <= a1)])
    tr_oos = pd.concat(tr_oos, ignore_index=True)
    s_in = np.nanmean([x[1] for x in efic])
    s_out = est.sharpe(r_oos.to_numpy())
    E["walkForward"] = {**resumo_trades(r_oos, tr_oos, h.FREQ), "janelas": len(janelas),
                        "janelasPositivas": float(np.mean(jpos)), "eficiencia": float(s_out / s_in) if s_in > 0 else float("nan"),
                        "inicioForaDaAmostra": str(ini_oos), "escolhas": escolhas}

    # 4. CPCV e PBO
    def ajustar_e_testar(treino, teste):
        k = int(M.iloc[treino].apply(lambda c: est.sharpe(c.to_numpy())).idxmax())
        return M.iloc[teste][k].to_numpy()
    embargo = {"1D": 5, "4h": 30, "1h": 120}[h.FREQ]
    E["cpcv"] = est.cpcv_sharpes(len(M), ajustar_e_testar, exe["cpcvGrupos"], exe["cpcvK"], embargo)
    E["pbo"] = est.pbo(M.to_numpy(), exe["pboBlocos"]) if len(vs) > 1 else {"pbo": float("nan"), "nota": "grade de 1"}

    # 5. PSR, DSR
    var_sr = float(np.var([est.sharpe(M[c].to_numpy()) for c in M.columns], ddof=1)) if len(vs) > 2 else None
    E["psr"] = est.psr(r_oos.to_numpy())
    E["dsr"] = est.dsr(r_oos.to_numpy(), n_tent, var_sr)
    E["minTRL"] = {"barras": est.min_trl(r_oos.to_numpy()), "temos": len(r_oos)}

    # 6. SPA
    E["spa"] = est.spa(M.to_numpy(), reps=exe["spaReps"])

    # 7. MCPT (processo inteiro: otimizar a grade em séries embaralhadas)
    def pontuar(series_perm):
        melhores = []
        for p in vs:
            r, _ = carteira(h, series_perm, p, custos)
            melhores.append(est.sharpe(r.to_numpy()))
        return float(np.nanmax(melhores))
    real = pontuar(dev)
    pts = []
    for k in range(exe["mcptN"]):
        perm = {s: est.permutar_barras(df, 0, 1000 * k + j) .assign(funding_rate=df.funding_rate.to_numpy())
                for j, (s, df) in enumerate(dev.items())}
        pts.append(pontuar(perm))
    E["mcpt"] = {"real": real, "p": (1 + int(np.sum(np.array(pts) >= real))) / (1 + len(pts)), "n": len(pts),
                 "mediaPermutada": float(np.nanmean(pts))}

    # 8. bootstrap
    E["bootstrap"] = est.bootstrap_trades(tr_oos.retorno.to_numpy(), exe["bootstrapReps"])

    # 9. estresse (sobre as mesmas escolhas do walk-forward)
    def wf_com(custo, lag):
        partes, tps = [], []
        for (tr_i, te_i), e in zip(janelas, escolhas):
            r, t = carteira(h, dev, e["params"], custo, lag)
            a0, a1 = M.index[te_i[0]], M.index[te_i[-1]]
            partes.append(r[(r.index >= a0) & (r.index <= a1)])
            tps.append(t[(pd.DatetimeIndex(t.inicio) >= a0) & (pd.DatetimeIndex(t.inicio) <= a1)])
        rr, tt = pd.concat(partes), pd.concat(tps, ignore_index=True)
        return {"sharpeAnual": est.sharpe_anual(rr.to_numpy(), bpa), "pf": est.profit_factor(tt.retorno.to_numpy()),
                "retornoTotal": float(np.prod(1 + rr) - 1), "ddMax": est.drawdown_max(rr.to_numpy())}
    E["estresse"] = {"custo2x": wf_com(custos.vezes(2), 1), "custo3x": wf_com(custos.vezes(3), 1),
                     "atraso1barra": wf_com(custos, 2), "vizinhosPositivos": E["grade"]["fracaoPositivas"],
                     "semFunding": wf_com(bt.Custos(custos.taxa, custos.slippage, False), 1)}

    # veredito
    W = E["walkForward"]
    checks = [
        ("lookahead", E["lookahead"]["ok"]),
        ("trades", W["trades"] >= P["tradesMin"]),
        ("pf", W["pf"] >= P["pfMin"]),
        ("dd", W["ddMax"] <= P["ddMax"]),
        ("janelasPositivas", W["janelasPositivas"] >= P["janelasPositivasMin"]),
        ("eficiencia", W["eficiencia"] >= P["eficienciaMin"]),
        ("cpcv", E["cpcv"]["mediano"] > P["cpcvSharpeMedianoMin"] and E["cpcv"]["fracaoPositivos"] >= P["cpcvFracaoPositivosMin"]),
        ("pbo", not (E["pbo"]["pbo"] > P["pboMax"])),
        ("psr", E["psr"] >= P["psrMin"]),
        ("dsr", E["dsr"]["dsr"] >= P["dsrMin"]),
        ("spa", E["spa"]["pConsistente"] <= P["spaPMax"]),
        ("mcpt", E["mcpt"]["p"] <= P["mcptPMax"]),
        ("bootstrap", E["bootstrap"].get("ddP95", 1) <= P["bootstrapDdP95Max"] and E["bootstrap"].get("pfP5", 0) > P["bootstrapPfP5Min"]),
        ("custo2x", E["estresse"]["custo2x"]["pf"] >= P["estresseCusto2xPfMin"]),
        ("atraso", E["estresse"]["atraso1barra"]["sharpeAnual"] > P["estresseAtrasoSharpeMin"]),
        ("vizinhos", E["estresse"]["vizinhosPositivos"] >= P["vizinhosPositivosMin"]),
    ]
    out["portoesResultado"] = {k: bool(v) for k, v in checks}
    falhas = [k for k, v in checks if not v]
    out["veredito"] = "PASSOU_DESENVOLVIMENTO" if not falhas else f"REPROVADA_{falhas[0].upper()}"
    out["falhas"] = falhas
    out["nTentativasUsadoNoDSR"] = n_tent

    # 10. reserva
    if a.abrir_reserva:
        abertas = [x for x in anteriores if x.get("tipo") == "reserva" and x.get("sha256") == sha]
        if abertas:
            out["reserva"] = {"erro": f"reserva já aberta em {abertas[0]['em']} para este hash; não reabre"}
        elif falhas:
            out["reserva"] = {"erro": "só abre a reserva quem passou no desenvolvimento"}
        else:
            k = vs.index(escolhas[-1]["params"])
            res = {s: d[d.index >= reserva - pd.Timedelta("400D")] for s, d in completas.items()}
            r_res, t_res = carteira(h, res, vs[k], custos)
            r_res, t_res = r_res[r_res.index >= reserva], t_res[pd.DatetimeIndex(t_res.inicio) >= reserva]
            out["reserva"] = {"params": vs[k], **resumo_trades(r_res, t_res, h.FREQ)}
            registrar({"tipo": "reserva", "id": h.ID, "sha256": sha, "em": pd.Timestamp.now(tz="UTC").isoformat(),
                       "resultado": out["reserva"]})

    out["segundos"] = round(time.time() - t0, 1)
    SAIDA.mkdir(exist_ok=True)
    (SAIDA / f"{h.ID}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float))
    registrar({"tipo": "resultado", "id": h.ID, "sha256": sha, "veredito": out["veredito"], "falhas": falhas,
               "sharpeOOS": E["walkForward"]["sharpeAnual"], "em": pd.Timestamp.now(tz="UTC").isoformat(),
               "rapido": a.rapido})
    print(json.dumps({"veredito": out["veredito"], "falhas": falhas, "walkForward": {k: W[k] for k in
                      ("retornoTotal", "sharpeAnual", "ddMax", "trades", "pf", "janelasPositivas", "eficiencia")},
                      "pbo": E["pbo"].get("pbo"), "dsr": E["dsr"]["dsr"], "spa": E["spa"]["pConsistente"],
                      "mcpt": E["mcpt"]["p"], "cpcv": E["cpcv"]["mediano"], "segundos": out["segundos"]}, indent=1, default=float))


if __name__ == "__main__":
    main()
