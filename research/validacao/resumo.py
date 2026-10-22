"""Gera research/validacao/RESUMO.md a partir de research/validacao/results/*.json (rodar depois de validar.py)."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OTHER = ("EJ_XAUUSD", "EJ_EURUSD", "EJ_GBPUSD", "EJ_USDJPY", "EJ_AUDUSD", "EJ_USDCAD")


def wf_ok(w):
    o = w["oos"]
    return (o["netR"] > 0 and (o["pf"] or 0) >= 1.15 and o["semMaiorR"] > 0 and w["oosStressNetR"] > 0
            and o["maxDDPct"] <= 10 and w["yearsTraded"] >= 3 and w["yearsPositive"] >= 0.6 * w["yearsTraded"])


def wf_weak_ok(w):
    o = w["oos"]
    return o["trades"] >= 10 and o["netR"] > 0 and (o["pf"] or 0) >= 1.10 and w["oosStressNetR"] > 0


def fmt_wf(w):
    o = w["oos"]
    pf = f"{o['pf']:.2f}" if o["pf"] else "-"
    return f"{o['netR']:+.1f}R PF {pf} DD {o['maxDDPct']:.1f}% ({w['yearsPositive']}/{w['yearsTraded']} anos)"


def stable(W, v):
    """Positivo com PF >= 1.10 no walk-forward com 2, 3 e 4 anos de calibração."""
    ws = [W[v], W[f"{v}_treino2"], W[f"{v}_treino4"]]
    return all(w["oos"]["netR"] > 0 and (w["oos"]["pf"] or 0) >= 1.10 and w["oosStressNetR"] > 0 for w in ws)


def ratio(w):
    return w["oos"]["netR"] / max(w["oos"]["maxDDPct"] * 2, 5.0)


def verdict(rep, ref_ratio):
    """APROVEITÁVEL: passa no walk-forward do BTC (3 anos), é estável com 2 e 4 anos e rende por drawdown pelo menos o mesmo
    que a melhor referência ingênua. SÓ BTC (≈ referência): passa, mas não rende mais por risco que uma média móvel.
    Outros ativos: onde é estável no walk-forward recalibrado."""
    btc = rep["assets"]["BTCUSD"]["walkForward"]
    ok = [v for v in ("orig", "regime") if wf_ok(btc[v]) and stable(btc, v)]
    cross = [a.replace("EJ_", "") for a in OTHER if a in rep["assets"]
             and any(stable(rep["assets"][a]["walkForward"], v) for v in ("orig", "regime"))]
    if not ok:
        return "DESCARTAR", None, cross
    best = max(ok, key=lambda v: ratio(btc[v]))
    if ratio(btc[best]) >= ref_ratio:
        return "APROVEITÁVEL", best, cross
    return "≈ REFERÊNCIA", best, cross


def main():
    reps = [json.loads(p.read_text()) for p in sorted((HERE / "results").glob("*.json")) if not p.name.startswith("_")]
    ref_ratio = max(ratio(r["assets"]["BTCUSD"]["walkForward"]["orig"]) for r in reps if r["strategy"].startswith("BM"))
    L = ["# Resumo da validação das candidatas", "",
         "Gerado por `resumo.py`. Walk-forward: calibra em 3 anos, opera o ano seguinte, rola. "
         "Variante *regime* = compra só acima da média de 200 dias e vende só abaixo.", "",
         "| Estratégia | Lab (tf, lado) | Fixos: valid. / reserva | Fixos regime: valid. / reserva | Grade positiva na valid. | WF BTC orig | WF BTC regime | Outros ativos estáveis no WF | Veredito |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(reps, key=lambda x: x["strategy"]):
        B = r["assets"]["BTCUSD"]
        fo, fr = B["fixed"]["orig"]["phases"], B["fixed"]["regime"]["phases"]
        s = B["sensitivity"]["orig"]["validation"]
        v, bv, cross = verdict(r, ref_ratio) if not r['strategy'].startswith('BM') else ('REFERÊNCIA', None, [])
        side = r["labParams"].get("side", "-")
        v = v + (f" ({bv})" if bv else "")
        L.append(f"| {r['strategy']} | {r['labTf']} {side} | {fo['validation']['netR']:+.1f} / {fo['reserve']['netR']:+.1f} | "
                 f"{fr['validation']['netR']:+.1f} / {fr['reserve']['netR']:+.1f} | {s['positivas']}/{s['combos']} | "
                 f"{fmt_wf(B['walkForward']['orig'])} | {fmt_wf(B['walkForward']['regime'])} | {', '.join(cross) or '-'} | {v} |")
    L.append("")
    for r in sorted(reps, key=lambda x: x["strategy"]):
        L += [f"## {r['strategy']} — {r['name']}", ""]
        B = r["assets"]["BTCUSD"]
        yrs = sorted(B["fixed"]["orig"]["byYear"])
        L.append("| Ano | B&H BTC % | " + " | ".join(f"{v} R" for v in ("orig", "both", "short", "regime")) + " |")
        L.append("|---|---|---|---|---|---|")
        for y in yrs:
            L.append(f"| {y} | {B['buyHoldPctByYear'].get(y, B['buyHoldPctByYear'].get(str(y), '-'))} | "
                     + " | ".join(f"{B['fixed'][v]['byYear'][y]['netR']:+.1f}" for v in ("orig", "both", "short", "regime")) + " |")
        L.append("")
        L.append("| Ativo | WF orig (3 anos) | WF orig 2 / 4 anos | WF regime | Fixos do BTC (orig), período todo |")
        L.append("|---|---|---|---|---|")
        for a, A in r["assets"].items():
            fa = A["fixed"]["orig"]["all"]
            W = A["walkForward"]
            L.append(f"| {a} | {fmt_wf(W['orig'])} | {W['orig_treino2']['oos']['netR']:+.1f}R / {W['orig_treino4']['oos']['netR']:+.1f}R | {fmt_wf(W['regime'])} | "
                     f"{fa['netR']:+.1f}R em {fa['trades']} operações |")
        L.append("")
    (HERE / "RESUMO.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:20]))


if __name__ == "__main__":
    main()
