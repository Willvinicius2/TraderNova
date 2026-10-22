"""Acompanhamento em papel das 3 aproveitáveis no BTC (TV85, TV39, TV74), sem corretora e sem ordens.

Processo:
- Recalibração anual: em janeiro, cada estratégia escolhe parâmetros e tempo gráfico nos 3 anos anteriores, com a mesma
  regra do walk-forward de validar.py. Os parâmetros ficam congelados em papel/parametros_<ANO>.json o ano todo.
- Operação em papel: a partir de INICIO, o motor do laboratório roda com os parâmetros do ano, usando só candles fechados.
  Na virada do ano a posição aberta é fechada na primeira abertura e os parâmetros novos entram.
- Risco: 0,5% da conta por operação dividido igualmente entre as 3 (≈0,167% cada), custo base do laboratório (0,10% por lado).
- Cada execução reconstrói tudo desde INICIO (causal, então não depende de ter rodado todos os dias), grava papel/estado.json,
  papel/PAINEL.md e acrescenta um resumo em papel/diario.jsonl.

Uso:
  python research/lab/data.py --bitstamp <clone atualizado>     # candles novos
  python research/validacao/papel.py                            # atualiza o papel (recalibra sozinho se faltar o ano)
  python research/validacao/papel.py --recalibrar 2027          # força a recalibração de um ano
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validar as V  # noqa: E402

PAPEL = HERE / "papel"
ASSET = "BTCUSD"
INICIO = "2026-10-22"
MEMBROS = ["TV85_ai_trend_nav", "TV39_smoothed_ha", "TV74_rvi"]
RISCO_TOTAL = 0.5  # % da conta por operação, dividido entre os membros
TF_HORAS = {"H1": 1, "H4": 4, "D1": 24}


def recalibrar(ano: int) -> dict:
    """Escolhe, para cada membro, tempo gráfico e parâmetros nos 3 anos anteriores a `ano` (mesmo critério do walk-forward)."""
    ac = dict(V.CFG["assets"][ASSET])
    ac["wfFirstTest"] = ac["wfLastTest"] = ano
    V.CFG["assets"][ASSET] = ac
    out = {"ano": ano, "treino": [f"{ano - V.CFG['trainYears']}-01-01", f"{ano}-01-01"],
           "calculadoEm": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "membros": {}}
    for sid in MEMBROS:
        mod, sha = V.load_strategy(sid)
        trs, grids = {}, {}
        for tf in mod.META["timeframes"]:
            df = V.load(ASSET, tf)
            df = df[df.index < pd.Timestamp(f"{ano}-01-01", tz="UTC")]  # nada do ano operado entra na escolha
            g, combos = V.variant_grid(mod.META, "orig")
            grids[tf] = g
            trs[tf] = {V.key(c): V.run_trades(mod, df, c, "orig") for c in combos}
        f = V.walk_forward(trs, grids, ASSET, V.CFG["trainYears"], V.CFG["minTradesPerYear"])["folds"][0]
        out["membros"][sid] = {"escolha": f["chosen"], "treino": f.get("train"), "strategySha256": sha}
        print(ano, sid, f["chosen"])
    PAPEL.mkdir(exist_ok=True)
    (PAPEL / f"parametros_{ano}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    return out


def candles_fechados(tf: str) -> pd.DataFrame:
    df = V.load(ASSET, tf)
    fim_dados = pd.read_csv(V.C.ROOT / "research" / "cache" / "lab" / f"{ASSET}_M15.csv.gz", usecols=[0]).iloc[-1, 0]
    fim_dados = pd.Timestamp(fim_dados) + pd.Timedelta(minutes=15)
    return df[df.index + pd.Timedelta(hours=TF_HORAS[tf]) <= fim_dados], fim_dados


def operar(sid: str, escolha: dict, a: str, b: str) -> tuple[list, dict | None, pd.Timestamp]:
    mod, _ = V.load_strategy(sid)
    df, fim_dados = candles_fechados(escolha["tf"])
    sig = V.variant_signals(mod, df, escolha["params"], "orig")
    cb = V.CFG["assets"][ASSET]["costSide"]["base"]
    trades = V.engine.run(df, sig, cb, a, b)
    fechadas, aberta = [], None
    for t in trades:
        d = {"lado": "compra" if t.side > 0 else "venda", "entrada": t.entry_time, "precoEntrada": round(t.entry, 2),
             "stop": round(t.stop, 2), "saida": t.exit_time, "precoSaida": round(t.exit, 2), "R": round(t.r, 3), "motivo": t.reason}
        if t.reason == "fim":  # ainda aberta: marcada a mercado no último fechamento
            aberta = {k: d[k] for k in ("lado", "entrada", "precoEntrada", "stop")}
            aberta.update({"ultimoPreco": d["precoSaida"], "Rmarcado": d["R"]})
        else:
            fechadas.append(d)
    proximo = None
    if aberta is None and len(df) and sig["entry"][-1] != 0 and df.index[-1] >= pd.Timestamp(a, tz="UTC"):
        proximo = "compra" if sig["entry"][-1] > 0 else "venda"
    return fechadas, aberta, {"ultimoCandle": str(df.index[-1]), "fimDados": str(fim_dados), "sinalNaProximaAbertura": proximo}


def atualizar():
    hoje = dt.datetime.now(dt.timezone.utc)
    anos = range(int(INICIO[:4]), hoje.year + 1)
    params = {}
    for ano in anos:
        p = PAPEL / f"parametros_{ano}.json"
        params[ano] = json.loads(p.read_text()) if p.exists() else recalibrar(ano)
    estado = {"inicio": INICIO, "atualizadoEm": hoje.isoformat(timespec="seconds"), "riscoPorMembroPct": round(RISCO_TOTAL / 3, 4),
              "membros": {}}
    total_R = 0.0
    for sid in MEMBROS:
        todas, aberta, info = [], None, None
        for ano in anos:
            a = max(INICIO, f"{ano}-01-01")
            b = f"{ano + 1}-01-01"
            esc = params[ano]["membros"][sid]["escolha"]
            if not esc:
                continue
            f, ab, info = operar(sid, esc, a, b)
            todas += [dict(x, ano=ano) for x in f]
            aberta = ab if ano == anos[-1] else aberta
        r = sum(x["R"] for x in todas)
        total_R += r + (aberta["Rmarcado"] if aberta else 0.0)
        estado["membros"][sid] = {"escolha": params[anos[-1]]["membros"][sid]["escolha"], "fechadas": todas, "aberta": aberta,
                                  "Rfechado": round(r, 2), **(info or {})}
    estado["Rtotal"] = round(total_R, 2)
    estado["contaPct"] = round(total_R * RISCO_TOTAL / 3, 2)
    PAPEL.mkdir(exist_ok=True)
    (PAPEL / "estado.json").write_text(json.dumps(estado, indent=1, ensure_ascii=False))
    with open(PAPEL / "diario.jsonl", "a") as fh:
        fh.write(json.dumps({"em": estado["atualizadoEm"], "Rtotal": estado["Rtotal"], "contaPct": estado["contaPct"],
                             "abertas": {s: (m["aberta"] or {}).get("lado") for s, m in estado["membros"].items()},
                             "fechadas": {s: len(m["fechadas"]) for s, m in estado["membros"].items()}}, ensure_ascii=False) + "\n")
    painel(estado)
    print(json.dumps({k: estado[k] for k in ("atualizadoEm", "Rtotal", "contaPct")}))


def painel(e):
    L = ["# Papel: carteira das 3 aproveitáveis no BTC", "",
         f"Início {e['inicio']} · atualizado {e['atualizadoEm']} · risco {e['riscoPorMembroPct']}% da conta por operação de cada estratégia.", "",
         f"**Resultado até agora: {e['Rtotal']:+.2f}R ≈ {e['contaPct']:+.2f}% da conta** (fechadas + abertas marcadas a mercado).", "",
         "| Estratégia | Tempo gráfico e parâmetros do ano | Posição aberta | Fechadas | R fechado | Último candle |",
         "|---|---|---|---|---|---|"]
    for s, m in e["membros"].items():
        esc = m["escolha"] or {}
        ab = m["aberta"]
        pos = (f"{ab['lado']} desde {ab['entrada'][:16]} a {ab['precoEntrada']}, stop {ab['stop']}, {ab['Rmarcado']:+.2f}R"
               if ab else ("sem posição" + (f"; {m['sinalNaProximaAbertura']} na próxima abertura" if m.get("sinalNaProximaAbertura") else "")))
        L.append(f"| {s} | {esc.get('tf')} {json.dumps(esc.get('params'), ensure_ascii=False)} | {pos} | {len(m['fechadas'])} | "
                 f"{m['Rfechado']:+.2f} | {m.get('ultimoCandle', '-')[:16]} |")
    L += ["", "Operações fechadas:", "", "| Estratégia | Lado | Entrada | Saída | R | Motivo |", "|---|---|---|---|---|---|"]
    for s, m in e["membros"].items():
        for t in m["fechadas"]:
            L.append(f"| {s} | {t['lado']} | {t['entrada'][:16]} @ {t['precoEntrada']} | {t['saida'][:16]} @ {t['precoSaida']} | {t['R']:+.2f} | {t['motivo']} |")
    (PAPEL / "PAINEL.md").write_text("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recalibrar", type=int, default=None)
    a = ap.parse_args()
    if a.recalibrar:
        recalibrar(a.recalibrar)
    else:
        atualizar()


if __name__ == "__main__":
    main()
