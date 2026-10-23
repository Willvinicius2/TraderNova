"""Teste de vizinhos de uma regra da triagem: muda cada parâmetro numérico padrão em -20% e +20% (um por vez, inteiros
arredondados, mínimo 1) e roda as três fases em BTCUSD, ETHUSD e SOLUSD com as mesmas regras de operação da triagem.
Uma regra robusta continua passando (ou quase) quando o parâmetro muda um pouco. Variante cujo sinal sai idêntico ao do
padrão (largura de linha, cor, plot só desenhado) fica fora da contagem. Parâmetros fixos no código não são variados:
para esses, edite uma cópia do bundle (revisão de 23/10 em notes/triagem-revisao-*.md).

Uso: python research/lab/triagem/vizinhos.py <id> <TF> "<nome da regra>" [--ativos BTCUSD,ETHUSD,SOLUSD]
Grava research/lab/results/triagem/vizinhos/<id>_<TF>.json.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import triagem as T  # noqa: E402

C = T.C


def defaults(i):
    js = "import(process.argv[1]).then(m=>console.log(JSON.stringify(m.indicatorRegistry.find(e=>e.id===process.argv[2]).defaultInputs)))"
    return json.loads(subprocess.check_output(["node", "-e", js, str(T.TRI / "lci.mjs"), i], text=True))


def variants(d):
    out = [("padrão", {})]
    for k, v in d.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:  # negativos (limites de zona) ficam fixos
            continue
        for f in (0.8, 1.2):
            nv = max(1, round(v * f)) if isinstance(v, int) else round(v * f, 6)
            if nv != v:
                out.append((f"{k}={nv}", {k: nv}))
    return out


def signals(i, tf, asset, ovr):
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "LCI_INPUTS": json.dumps(ovr), "LCI_SEM_REPINTURA": "1"}
        subprocess.run(["node", "--max-old-space-size=3000", str(HERE / "sinais.mjs"), str(T.TRI / "lci.mjs"), str(T.TRI), asset, tf, tmp, i],
                       env=env, check=True, capture_output=True, timeout=1800)
        return json.loads((Path(tmp) / asset / tf / f"{i}.json").read_text())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id"); ap.add_argument("tf"); ap.add_argument("regra")
    ap.add_argument("--ativos", default="BTCUSD,ETHUSD,SOLUSD")
    a = ap.parse_args()
    linhas, padrao = [], {}
    for nome, ovr in variants(defaults(a.id)):
        lin = {"variante": nome, "ativos": {}}
        for asset in a.ativos.split(","):
            df = C.load_bars(asset, a.tf)
            d = signals(a.id, a.tf, asset, ovr)
            ru = next((x for x in d["regras"] if x["nome"] == a.regra), None)
            if ru is None:
                lin["ativos"][asset] = {"passou": False, "motivo": d.get("erro") or "regra sumiu"}; continue
            chave = (tuple(ru["long"]), tuple(ru["short"]))
            if nome == "padrão":
                padrao[asset] = chave
            elif padrao.get(asset) == chave:
                lin["ativos"][asset] = {"passou": None, "motivo": "sinal igual ao padrão"}; continue
            ph = T.run_phases(df, T.build_sig(df, ru), C.PROTOCOL["assets"][asset], a.tf, stop_at_fail=False)
            lin["ativos"][asset] = {"passou": all(not ph[s]["falhas"] for s, _ in T.STAGES),
                                    **{s: {"netR": ph[s]["base"]["netR"], "pf": ph[s]["base"]["pf"], "trades": ph[s]["base"]["trades"], "falhas": ph[s]["falhas"]} for s, _ in T.STAGES}}
        linhas.append(lin)
        print(nome, " ".join(f"{k}:{'=' if v['passou'] is None else 'ok' if v['passou'] else 'x'}({v.get('development', {}).get('netR')}/{v.get('validation', {}).get('netR')}/{v.get('reserve', {}).get('netR')})" for k, v in lin["ativos"].items()), flush=True)
    viz = [l for l in linhas if l["variante"] != "padrão"]
    resumo = {}
    for asset in a.ativos.split(","):
        conta = [l["ativos"][asset]["passou"] for l in viz if l["ativos"][asset]["passou"] is not None]
        resumo[asset] = f"{sum(conta)}/{len(conta)}" if conta else "nenhum parâmetro muda o sinal"
    print("vizinhos que passam:", resumo)
    dst = T.RES / "vizinhos"; dst.mkdir(parents=True, exist_ok=True)
    (dst / f"{a.id}_{a.tf}.json").write_text(json.dumps({"id": a.id, "tf": a.tf, "regra": a.regra, "resumo": resumo, "linhas": linhas}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
