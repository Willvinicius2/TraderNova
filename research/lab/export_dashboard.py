"""Exporta os resultados do laboratório para o painel (3 arquivos JSON em research/lab/dashboard/).
Uso: python research/lab/export_dashboard.py"""
import json
import re
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent
OUT = LAB / "dashboard"

# Quem testou o quê: prefixos de ID por agente.
AGENTS = [
    {"agente": "tendencia", "rodada": 1, "foco": "Tendência", "ids": ["L01", "L02", "L03", "L04"]},
    {"agente": "reversao", "rodada": 1, "foco": "Reversão à média", "ids": ["L05", "L06", "L07", "L08"]},
    {"agente": "volatilidade", "rodada": 1, "foco": "Volatilidade e rompimento", "ids": ["L09", "L10", "L11", "L12"]},
    {"agente": "padroes", "rodada": 1, "foco": "Padrões de preço", "ids": ["L13", "L14", "L15", "L16"]},
    {"agente": "tempo-volume", "rodada": 1, "foco": "Horário e volume", "ids": ["L17", "L18", "L19", "L20"]},
    {"agente": "tv-embutidas-a", "rodada": 2, "foco": "TradingView embutidas", "ids": ["TV01", "TV02", "TV03", "TV04"]},
    {"agente": "tv-embutidas-b", "rodada": 2, "foco": "TradingView embutidas", "ids": ["TV05", "TV06", "TV07", "TV08"]},
    {"agente": "tv-embutidas-c", "rodada": 2, "foco": "TradingView embutidas", "ids": ["TV09", "TV10", "TV11"]},
    {"agente": "tv-comunidade-d", "rodada": 2, "foco": "TradingView comunidade", "ids": ["TV12", "TV13", "TV14", "TV15"]},
    {"agente": "tv-comunidade-e", "rodada": 2, "foco": "TradingView comunidade", "ids": ["TV16", "TV17", "TV18", "TV19"]},
    {"agente": "tv-comunidade-f", "rodada": 2, "foco": "TradingView comunidade", "ids": ["TV20", "TV21", "TV22", "TV23"]},
]
# Rodadas automáticas: research/lab/agents.json acrescenta agentes novos sem editar este arquivo.
_extra = Path(__file__).resolve().parent / "agents.json"
if _extra.exists():
    AGENTS += json.loads(_extra.read_text())
VERDICT = {"CANDIDATA": "Candidata", "REPROVADA_RESERVA": "Reprovada na reserva",
           "REPROVADA_VALIDACAO": "Reprovada na validação", "REPROVADA_DESENVOLVIMENTO": "Reprovada no desenvolvimento"}


def agent_of(sid):
    for a in AGENTS:
        if sid.split("_")[0] in a["ids"]:
            return a
    return None


def main():
    results = [json.loads(p.read_text()) for p in sorted((LAB / "results").glob("*.json")) if not p.name.startswith("_")]
    # O veredito de uma estratégia é o da última tentativa (original ou refinamento).
    by_base = {}
    for r in results:
        m = re.fullmatch(r"(.+)_r(\d+)", r["strategy"])
        base = m.group(1) if m else r["strategy"]
        r["_base"] = base
        r["_try"] = int(m.group(2)) if m else 0
        if base not in by_base or r["_try"] > by_base[base]["_try"]:
            by_base[base] = r

    rows, curves = [], []
    for r in by_base.values():
        s = r.get("selected") or {}
        dev = s.get("development") or (r["topDevelopment"][0]["dev"] if r.get("topDevelopment") else {})
        val = (s.get("validation") or {}).get("base") or {}
        res = (s.get("reserve") or {}).get("base") or {}
        ag = agent_of(r["strategy"])
        tries = sum(1 for x in results if x["_base"] == r["_base"])
        rows.append({
            "id": r["_base"], "nome": r["name"], "rodada": ag["rodada"] if ag else None,
            "agente": ag["agente"] if ag else "", "familia": r["family"],
            "veredito": VERDICT[r["verdict"]], "tempo": s.get("tf") or (r["topDevelopment"][0]["tf"] if r.get("topDevelopment") else ""),
            "tentativas": tries, "combinacoes": sum(x["combinationsTested"] for x in results if x["_base"] == r["_base"]),
            "fonte": (r.get("sources") or [""])[0], "protocolo": r["protocol"],
            "dev_trades": dev.get("trades"), "dev_r": dev.get("netR"), "dev_pf": dev.get("pf"),
            "val_trades": val.get("trades"), "val_r": val.get("netR"), "val_pf": val.get("pf"),
            "res_trades": res.get("trades"), "res_r": res.get("netR"), "res_pf": res.get("pf"),
            "res_dd_pct": res.get("maxDDPct"),
        })
        for fase, pts in (r.get("curves") or {}).items():
            for d, v in pts:
                curves.append({"id": r["_base"], "fase": fase, "data": d, "r": v})

    status_dir = LAB / "status"
    agents = []
    for a in AGENTS:
        done = [x for x in rows if x["agente"] == a["agente"]]
        st = {}
        p = status_dir / f"{a['agente']}.json"
        if p.exists():
            st = json.loads(p.read_text())
        total = len(a["ids"])
        situacao = "Concluído" if len(done) >= total else ("Rodando" if (a["rodada"] == 2 or done or st) else "Na fila")
        agents.append({
            "agente": a["agente"], "rodada": a["rodada"], "foco": a["foco"], "estrategias": total,
            "concluidas": min(len(done), total), "candidatas": sum(1 for x in done if x["veredito"] == "Candidata"),
            "situacao": situacao, "atualizado": st.get("updated", ""),
        })

    OUT.mkdir(exist_ok=True)
    rows.sort(key=lambda x: (x["rodada"] or 9, x["id"]))
    (OUT / "estrategias.json").write_text(json.dumps(rows, ensure_ascii=False))
    (OUT / "curvas.json").write_text(json.dumps(curves, ensure_ascii=False))
    (OUT / "agentes.json").write_text(json.dumps(agents, ensure_ascii=False))
    print(len(rows), "estratégias,", len(curves), "pontos,", time.strftime("%H:%M:%S"))


if __name__ == "__main__":
    main()
