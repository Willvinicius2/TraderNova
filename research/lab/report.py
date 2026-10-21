"""Junta research/lab/results/*.json em research/lab/RELATORIO.md e atualiza registry.json.

Uso: python research/lab/report.py --round 1
"""
import argparse
import json
from pathlib import Path

LAB = Path(__file__).resolve().parent


def fmt(m):
    if not m:
        return "-"
    return f"{m['trades']} op · {m['netR']:+.1f}R · PF {m['pf'] if m['pf'] is not None else '-'} · DD {m['maxDDR']}R"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    a = ap.parse_args()
    results = [json.loads(p.read_text()) for p in sorted((LAB / "results").glob("*.json")) if not p.name.startswith("_")]
    reg_path = LAB / "registry.json"
    reg = json.loads(reg_path.read_text())
    known = {s["id"] for s in reg["strategies"]}
    order = {"CANDIDATA": 0, "REPROVADA_RESERVA": 1, "REPROVADA_VALIDACAO": 2, "REPROVADA_DESENVOLVIMENTO": 3}
    results.sort(key=lambda r: (order[r["verdict"]], r["strategy"]))

    lines = [
        f"# Laboratório de estratégias: resultados até a rodada {a.round}",
        "",
        "Gerado por `python research/lab/report.py`. Rodada 1 usou o protocolo lab-v1 e a rodada 2 o lab-v2 (mais rígido); ver `protocol.json`. Calibração só no desenvolvimento (BTC 2016–2020), "
        "validação 2021–2022 e reserva 2023–out/2026 sem reajuste, custo base 0,10% por lado e stress 0,20%. "
        "CANDIDATA passou no histórico, mas ainda precisa de acompanhamento prospectivo, custos reais da conta e risco conjunto. Não é promessa de lucro.",
        "",
        "| Estratégia | Família | Veredito | Tempo | Parâmetros | Desenvolvimento | Validação | Reserva | Combinações | DSR |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        s = r.get("selected") or {}
        val = (s.get("validation") or {}).get("base")
        res = (s.get("reserve") or {}).get("base")
        dev = s.get("development") or (r["topDevelopment"][0]["dev"] if r["topDevelopment"] else None)
        params = json.dumps(s.get("params"), ensure_ascii=False) if s else "(melhor reprovada)"
        lines.append(
            f"| {r['strategy']} {r['name']} | {r['family']} | **{r['verdict']}** | {s.get('tf', r['topDevelopment'][0]['tf'] if r['topDevelopment'] else '-')} | "
            f"{params} | {fmt(dev)} | {fmt(val)} | {fmt(res)} | {r['combinationsTested']} | {s.get('deflatedSharpe', '-')} |"
        )
        base_id = r["strategy"]
        if base_id not in known:
            reg["strategies"].append({
                "id": base_id, "name": r["name"], "family": r["family"], "coreRule": r["rule"],
                "testedOn": f"{r['asset']} lab-v1", "status": r["verdict"], "origin": f"laboratório rodada {a.round}",
                "sources": r["sources"],
            })
            known.add(base_id)
        else:
            for x in reg["strategies"]:
                if x["id"] == base_id:
                    x["status"] = r["verdict"]
    diag_p = LAB / "results" / "_diagnostico_candidatas.json"
    if diag_p.exists():
        diag = json.loads(diag_p.read_text())
        lines += ["", "## Fragilidade das candidatas (`diagnose.py`)", "",
                  "Resultado sem a maior operação e em % do capital com 0,5% de risco por operação, ao lado de comprar e segurar BTC no mesmo período.", "",
                  "| Estratégia | Período | Op. | netR | Sem a maior | Retorno % | DD % | Comprar e segurar % |", "|---|---|---|---|---|---|---|---|"]
        for sid, d in diag.items():
            for st in ("development", "validation", "reserve"):
                v = d[st]
                lines.append(f"| {sid} | {st} | {v['trades']} | {v['netR']:+.1f} | {v['semMaiorR']:+.1f} | {v['retPct05']:+.1f} | {v['ddPct05']} | {v['buyHoldPct']:+.1f} |")
    lines += ["", "Fontes e regras completas em `strategies/` e `results/`. Notas de cada agente em `notes/`."]
    (LAB / "RELATORIO.md").write_text("\n".join(lines) + "\n")
    reg_path.write_text(json.dumps(reg, indent=1, ensure_ascii=False))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
