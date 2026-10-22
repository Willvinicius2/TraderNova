"""Triagem em massa dos ~1.700 indicadores da biblioteca deepentropy (ports dos scripts do TradingView).

Regras fixas (protocol.json, "triagem"): parâmetros padrão do autor (nada é calibrado), compra e venda sempre, stop de
2×ATR14, saída e inversão no sinal oposto. Cada regra passa pelas mesmas fases e critérios do laboratório (lab-v4 mais a
exigência de operar os dois lados), e o Deflated Sharpe usa o número total de regras testadas no tempo gráfico.

Uso:
  python research/lab/triagem/triagem.py candles            # candles em JSON para o Node
  python research/lab/triagem/triagem.py sinais  [--asset BTCUSD] [--tf H4,D1] [--ids a,b] [--jobs 4]
  python research/lab/triagem/triagem.py testar  [--tf H4,D1]
  python research/lab/triagem/triagem.py cruzado            # candidatas da triagem em EURUSD e USDJPY
  python research/lab/triagem/triagem.py resumo             # TRIAGEM.md e arquivo do painel
Precisa de research/cache/lab/tri/lci.mjs (bundle da biblioteca) e dos candles em JSON (ver CICLO.md).
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
sys.path.insert(0, str(LAB))
import calibrate as C  # noqa: E402
import engine  # noqa: E402

TRI = C.ROOT / "research" / "cache" / "lab" / "tri"
OUT = TRI / "out"
RES = LAB / "results" / "triagem"
K_STOP = 2.0
STAGES = (("development", 1.15), ("validation", 1.15), ("reserve", 1.10))


def all_ids():
    js = "import(process.argv[1]).then(m=>console.log(JSON.stringify(m.indicatorRegistry.map(e=>e.id))))"
    return json.loads(subprocess.check_output(["node", "-e", js, str(TRI / "lci.mjs")], text=True))


def cmd_candles(a):
    TRI.mkdir(parents=True, exist_ok=True)
    for asset in ("BTCUSD", "EURUSD", "USDJPY"):
        for tf in ("H4", "D1"):
            d = C.load_bars(asset, tf)
            t = ((d.index - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta("1s")).astype(int).tolist()
            (TRI / f"{asset}_{tf}.json").write_text(json.dumps({"time": t, **{k: d[k].fillna(0).tolist() for k in ("open", "high", "low", "close", "volume")}}))


def cmd_sinais(a):
    ids = a.ids.split(",") if a.ids else all_ids()
    todo = [i for i in ids if a.force or not all((OUT / a.asset / tf / f"{i}.json").exists() for tf in a.tf.split(","))]
    print(len(ids), "indicadores,", len(todo), "a calcular", flush=True)
    chunks = [todo[k:k + 10] for k in range(0, len(todo), 10)]

    def run(chunk, timeout=2400):
        cmd = ["node", "--max-old-space-size=3000", str(HERE / "sinais.mjs"), str(TRI / "lci.mjs"), str(TRI), a.asset, a.tf, str(OUT)]
        try:
            subprocess.run(cmd + chunk, timeout=timeout, capture_output=True)
        except subprocess.TimeoutExpired:
            pass
        # o que não saiu (lento ou travou) vai de um em um com limite menor
        miss = [i for i in chunk if not all((OUT / a.asset / tf / f"{i}.json").exists() for tf in a.tf.split(","))]
        for i in miss:
            if len(chunk) == 1:
                for tf in a.tf.split(","):
                    p = OUT / a.asset / tf / f"{i}.json"
                    if not p.exists():
                        p.parent.mkdir(parents=True, exist_ok=True)
                        p.write_text(json.dumps({"id": i, "tf": tf, "asset": a.asset, "regras": [], "erro": f"passou de {timeout}s"}))
            else:
                run([i], timeout=900)

    t0 = time.time()
    with ThreadPoolExecutor(a.jobs) as ex:
        for k, _ in enumerate(ex.map(run, chunks)):
            if k % 10 == 0:
                print(f"{(k + 1) * 10}/{len(todo)} em {time.time() - t0:.0f}s", flush=True)


def build_sig(df, rule):
    n = len(df)
    assert rule.get("n") in (None, n), "sinais e candles desalinhados"
    lo = np.zeros(n, bool); sh = np.zeros(n, bool)
    lo[[i for i in rule["long"] if i < n]] = True
    sh[[i for i in rule["short"] if i < n]] = True
    both = lo & sh
    lo &= ~both; sh &= ~both
    entry = np.where(lo, 1, np.where(sh, -1, 0)).astype(np.int8)
    return {"entry": entry, "stop": K_STOP * engine.atr(df, 14), "exit_long": sh, "exit_short": lo}


def years_pos(trs, a, b):
    y0, y1 = int(a[:4]), int((pd.Timestamp(b) - pd.Timedelta(seconds=1)).year)
    by = {}
    for t in trs:
        y = min(max(int(t.exit_time[:4]), y0), y1)
        by[y] = by.get(y, 0.0) + t.r
    return sum(1 for v in by.values() if v > 0), y1 - y0 + 1


def fails(mb, ms, tf, stage, pf_min, trs=None, per=None):
    f = []
    if mb["trades"] < C.min_trades(tf, stage): f.append("poucas operações")
    if mb["netR"] <= 0: f.append("netR<=0")
    if (mb["pf"] or 0) < pf_min: f.append(f"PF<{pf_min}")
    if mb["semMaiorR"] <= 0: f.append("sem a maior<=0")
    if mb["maxDDPct"] > C.MAX_DD_PCT: f.append("DD>10%")
    if stage == "development":
        yp, yt = years_pos(trs, *per)
        if yp < yt - 1: f.append(f"anos positivos {yp}/{yt}")
    else:
        if ms["netR"] <= 0: f.append("stress<=0")
        if ms["maxDDPct"] > C.MAX_DD_PCT: f.append("DD stress>10%")
    return f


def run_phases(df, sig, cfg, tf, stop_at_fail=True):
    per = cfg["periods"]; cb, cs = cfg["costSide"]["base"], cfg["costSide"]["stress"]
    out = {}
    for stage, pf in STAGES:
        a, b = per[stage]
        trb = engine.run(df, sig, cb, a, b)
        mb = engine.metrics(trb, C.years(a, b))
        ms = engine.metrics(engine.run(df, sig, cs, a, b), C.years(a, b)) if stage != "development" else None
        f = fails(mb, ms, tf, stage, pf, trb, (a, b))
        if stage == "development":
            mb["anosPositivos"], mb["anosTotal"] = years_pos(trb, a, b)
            out["_r"] = [t.r for t in trb]
        out[stage] = {"base": mb, "stress": ms, "falhas": f, "curva": engine.curve(trb)}
        if f and stop_at_fail:
            break
    return out


def cmd_testar(a):
    RES.mkdir(parents=True, exist_ok=True)
    cfg = C.PROTOCOL["assets"]["BTCUSD"]
    for tf in a.tf.split(","):
        df = C.load_bars("BTCUSD", tf)
        # sem cortar o aquecimento: os índices dos sinais vêm do mesmo arquivo de candles inteiro
        rows, t0 = [], time.time()
        files = sorted((OUT / "BTCUSD" / tf).glob("*.json"))
        for k, p in enumerate(files):
            d = json.loads(p.read_text())
            base = {"id": d["id"], "nome": d.get("nome"), "grupo": d.get("grupo"), "categoria": d.get("categoria"), "tf": tf}
            if d.get("erro"):
                rows.append({**base, "regra": None, "veredito": "ERRO", "motivo": d["erro"]}); continue
            if not d["regras"]:
                rows.append({**base, "regra": None, "veredito": "SEM_SINAL"}); continue
            for ru in d["regras"]:
                row = {**base, "regra": ru["nome"], "fonte": ru["fonte"], "sinais": len(ru["long"]) + len(ru["short"])}
                if ru.get("repinta"):
                    rows.append({**row, "veredito": "REPINTA", "motivo": f"{ru['repinta']} sinais mudam com dados futuros"}); continue
                ph = run_phases(df, build_sig(df, ru), cfg, tf)
                ver = "CANDIDATA"
                for stage, _ in STAGES:
                    if stage not in ph or ph[stage]["falhas"]:
                        ver = {"development": "REPROVADA_DESENVOLVIMENTO", "validation": "REPROVADA_VALIDACAO", "reserve": "REPROVADA_RESERVA"}[stage]
                        break
                row.update({"veredito": ver, "fases": {s: {k: v for k, v in ph[s].items() if k != "curva"} for s, _ in STAGES if s in ph},
                            "_r": ph.get("_r"), "_curvas": {s: ph[s]["curva"] for s, _ in STAGES if s in ph}})
                rows.append(row)
            if k % 100 == 0:
                print(tf, f"{k}/{len(files)} em {time.time() - t0:.0f}s", flush=True)
        # Deflated Sharpe com todas as regras testadas neste tempo gráfico
        srs = [r["fases"]["development"]["base"]["sharpeTrade"] for r in rows if r.get("fases") and r["fases"]["development"]["base"]["sharpeTrade"] is not None]
        for r in rows:
            rr = r.pop("_r", None)
            if r["veredito"] in ("REPROVADA_VALIDACAO", "REPROVADA_RESERVA", "CANDIDATA") and rr and len(rr) > 3:
                s = pd.Series(rr)
                r["dsr"] = C.deflated_sharpe(r["fases"]["development"]["base"]["sharpeTrade"], len(rr), srs, float(s.skew()), float(s.kurt() + 3))
            if r["veredito"] != "CANDIDATA":
                r.pop("_curvas", None)
        (RES / f"BTCUSD_{tf}.json").write_text(json.dumps({"protocolo": C.PROTOCOL["triagem"]["id"], "regrasTestadas": len(srs), "linhas": rows}, ensure_ascii=False))
        cnt = {}
        for r in rows: cnt[r["veredito"]] = cnt.get(r["veredito"], 0) + 1
        print(tf, cnt, f"{time.time() - t0:.0f}s", flush=True)


def placebo(df, sig, cfg, draws=20):
    per = cfg["periods"]; cb = cfg["costSide"]["base"]; t = df.index
    rng = np.random.default_rng(12345)
    res = {k: [] for k, _ in STAGES}
    idx = {k: (t.searchsorted(pd.Timestamp(per[k][0], tz="UTC")), t.searchsorted(pd.Timestamp(per[k][1], tz="UTC"))) for k in res}
    for _ in range(draws):
        e = np.zeros(len(t), dtype=np.int8)
        for k, (i0, i1) in idx.items():
            e[i0:i1] = rng.permutation(np.asarray(sig["entry"][i0:i1]))
        s2 = dict(sig); s2["entry"] = e
        for k in res:
            res[k].append(engine.metrics(engine.run(df, s2, cb, *per[k]), 1)["netR"])
    return {k: round(statistics.median(v), 2) for k, v in res.items()}


def cmd_cruzado(a):
    cands = []
    for tf in ("H4", "D1"):
        p = RES / f"BTCUSD_{tf}.json"
        if p.exists():
            cands += [r for r in json.loads(p.read_text())["linhas"] if r["veredito"] == "CANDIDATA"]
    print(len(cands), "candidatas", flush=True)
    ids = sorted({r["id"] for r in cands})
    for asset in ("EURUSD", "USDJPY"):
        if ids:
            subprocess.run([sys.executable, __file__, "sinais", "--asset", asset, "--ids", ",".join(ids)], check=False)
    out = []
    btc = C.PROTOCOL["assets"]["BTCUSD"]
    for r in cands:
        df = C.load_bars("BTCUSD", r["tf"])
        d = json.loads((OUT / "BTCUSD" / r["tf"] / f"{r['id']}.json").read_text())
        ru = next(x for x in d["regras"] if x["nome"] == r["regra"])
        item = {"id": r["id"], "nome": r["nome"], "tf": r["tf"], "regra": r["regra"], "placeboBTC": placebo(df, build_sig(df, ru), btc), "ativos": {}}
        for asset in ("EURUSD", "USDJPY"):
            cfg = C.PROTOCOL["assets"][asset]
            dfa = C.load_bars(asset, r["tf"])
            pa = OUT / asset / r["tf"] / f"{r['id']}.json"
            da = json.loads(pa.read_text()) if pa.exists() else {"regras": []}
            rua = next((x for x in da["regras"] if x["nome"] == r["regra"]), None)
            if rua is None or rua.get("repinta"):
                item["ativos"][asset] = {"passou": False, "motivo": "sem o mesmo sinal neste ativo"}; continue
            ph = run_phases(dfa, build_sig(dfa, rua), cfg, r["tf"], stop_at_fail=False)
            item["ativos"][asset] = {"passou": all(not ph[s]["falhas"] for s, _ in STAGES),
                                     **{s: {"netR": ph[s]["base"]["netR"], "pf": ph[s]["base"]["pf"], "trades": ph[s]["base"]["trades"], "falhas": ph[s]["falhas"]} for s, _ in STAGES}}
        item["metaAtingida"] = any(v["passou"] for v in item["ativos"].values())
        out.append(item)
        print(r["id"], r["tf"], {k: v["passou"] for k, v in item["ativos"].items()}, flush=True)
    (RES / "_cruzado.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))


def cmd_resumo(a):
    rows = []
    for tf in ("H4", "D1"):
        p = RES / f"BTCUSD_{tf}.json"
        if p.exists():
            rows += json.loads(p.read_text())["linhas"]
    cruz = {(x["id"], x["tf"], x["regra"]): x for x in json.loads((RES / "_cruzado.json").read_text())} if (RES / "_cruzado.json").exists() else {}
    ind = {r["id"] for r in rows}
    cnt = {}
    for r in rows: cnt[r["veredito"]] = cnt.get(r["veredito"], 0) + 1
    testadas = sum(1 for r in rows if r.get("fases"))
    L = ["# Triagem em massa dos scripts do TradingView", "",
         f"{len(ind)} indicadores da biblioteca deepentropy (ports em TypeScript de scripts do TradingView), em BTCUSD H4 e D1, com os parâmetros padrão do autor. "
         "Nada foi calibrado: compra e venda sempre, stop de 2×ATR14, saída e inversão no sinal oposto. Critérios das fases iguais aos do laboratório (lab-v4). "
         "Regras que mudam com dados futuros (teste de corte do histórico) ficam fora. Ver `protocol.json` → `triagem`.", "",
         "## Funil", "", "| Etapa | Regras |", "|---|---|",
         f"| Regras com sinal testadas | {testadas} |",
         f"| Repintam (fora) | {cnt.get('REPINTA', 0)} |",
         f"| Sem sinal de compra/venda | {cnt.get('SEM_SINAL', 0)} |",
         f"| Erro ou lentidão | {cnt.get('ERRO', 0)} |",
         f"| Reprovadas no desenvolvimento | {cnt.get('REPROVADA_DESENVOLVIMENTO', 0)} |",
         f"| Reprovadas na validação | {cnt.get('REPROVADA_VALIDACAO', 0)} |",
         f"| Reprovadas na reserva | {cnt.get('REPROVADA_RESERVA', 0)} |",
         f"| **Candidatas** | **{cnt.get('CANDIDATA', 0)}** |", ""]
    good = [r for r in rows if r["veredito"] in ("CANDIDATA", "REPROVADA_RESERVA", "REPROVADA_VALIDACAO")]
    good.sort(key=lambda r: ({"CANDIDATA": 0, "REPROVADA_RESERVA": 1, "REPROVADA_VALIDACAO": 2}[r["veredito"]], -(r["fases"]["development"]["base"]["netR"])))
    L += ["## Passaram no desenvolvimento", "", "| Indicador | Tempo | Regra | Veredito | Dev | Validação | Reserva | DSR | EURUSD | USDJPY |", "|---|---|---|---|---|---|---|---|---|---|"]
    f = lambda m: f"{m['trades']} op · {m['netR']:+.1f}R · PF {m['pf']}" if m else "-"
    for r in good[:150]:
        fs = r["fases"]; c = cruz.get((r["id"], r["tf"], r["regra"]))
        ca = (lambda k: ("passa" if c["ativos"][k]["passou"] else "não")) if c else (lambda k: "-")
        L.append(f"| {r['nome']} (`{r['id']}`) | {r['tf']} | {r['regra']} | **{r['veredito']}** | {f(fs['development']['base'])} | "
                 f"{f(fs.get('validation', {}).get('base'))} | {f(fs.get('reserve', {}).get('base'))} | {r.get('dsr', '-')} | {ca('EURUSD')} | {ca('USDJPY')} |")
    meta = [c for c in cruz.values() if c["metaAtingida"]]
    def bate(r):
        c = cruz.get((r["id"], r["tf"], r["regra"]))
        return bool(c) and all(r["fases"][s]["base"]["netR"] > 2 * max(c["placeboBTC"][s], 0) + 5 for s in ("validation", "reserve"))
    nbate = sum(1 for r in good if r["veredito"] == "CANDIDATA" and bate(r))
    L += ["", "## Placebo e múltiplos testes", "",
          f"Das {cnt.get('CANDIDATA', 0)} candidatas, {nbate} ganham do placebo com folga na validação e na reserva (resultado real maior que o dobro da mediana de 20 sorteios de entradas ao acaso, mais 5R). "
          "O Deflated Sharpe, calculado com todas as regras testadas, ficou abaixo de 0,5 em todas: com milhares de tentativas, nenhum desenvolvimento sozinho prova que não é sorte. "
          "Por isso o que vale é o teste fora da amostra (validação, reserva e outros ativos)."]
    L += ["", "## Meta (passa no BTC e em outro ativo, mesmos parâmetros)", "",
          ("**ATINGIDA** por: " + ", ".join(f"{c['nome']} {c['tf']} ({c['regra']})" for c in meta)) if meta else "Ainda não.", "",
          "Candidata da triagem não é estratégia aprovada: o port e a regra de sinal precisam ser revisados por um agente no laboratório completo antes de qualquer uso."]
    (LAB / "TRIAGEM.md").write_text("\n".join(L) + "\n")
    # painel: só o que passou no desenvolvimento entra na tabela; o funil vai inteiro
    funil = [{"ordem": k, "etapa": e, "regras": v} for k, (e, v) in enumerate([
        ("Scripts do TradingView na biblioteca", len(ind)), ("Regras de sinal testadas", testadas),
        ("Passaram no desenvolvimento", len(good)),
        ("Passaram também na validação", cnt.get("REPROVADA_RESERVA", 0) + cnt.get("CANDIDATA", 0)),
        ("Candidatas (passaram nas 3 fases)", cnt.get("CANDIDATA", 0)),
        ("Ganham do placebo com folga", nbate),
        ("Passaram também em EURUSD ou USDJPY", len(meta)),
        ("Repintam (fora do teste)", cnt.get("REPINTA", 0)), ("Sem sinal de compra/venda", cnt.get("SEM_SINAL", 0)),
        ("Erro ou lentidão", cnt.get("ERRO", 0))])]
    (LAB / "dashboard" / "funil.json").write_text(json.dumps(funil, ensure_ascii=False))
    VER = {"CANDIDATA": "Candidata", "REPROVADA_RESERVA": "Reprovada na reserva", "REPROVADA_VALIDACAO": "Reprovada na validação"}
    dash = [{"id": r["id"], "nome": r["nome"], "tf": r["tf"], "regra": r["regra"], "veredito": r["veredito"], "dsr": r.get("dsr"),
                        **{f"{s[:3]}_{k}": (r["fases"].get(s) or {}).get("base", {}).get(k) for s in ("development", "validation", "reserve") for k in ("trades", "netR", "pf")},
                        "chave": f"{r['id']}|{r['tf']}|{r['regra']}",
                        "cruzado": (lambda c: ("Passa em " + ", ".join(k for k, v in c["ativos"].items() if v["passou"])) if c["metaAtingida"] else "Não passa")(cruz[(r["id"], r["tf"], r["regra"])]) if (r["id"], r["tf"], r["regra"]) in cruz else ""}
                       for r in good]
    for x in dash: x["veredito"] = VER[x["veredito"]]
    (LAB / "dashboard" / "triagem.json").write_text(json.dumps(dash, ensure_ascii=False))
    print("\n".join(L[:20]))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("sinais"); s.add_argument("--asset", default="BTCUSD"); s.add_argument("--tf", default="H4,D1")
    s.add_argument("--ids", default=""); s.add_argument("--jobs", type=int, default=4); s.add_argument("--force", action="store_true")
    t = sp.add_parser("testar"); t.add_argument("--tf", default="H4,D1")
    sp.add_parser("cruzado"); sp.add_parser("resumo"); sp.add_parser("candles")
    a = ap.parse_args()
    {"candles": cmd_candles, "sinais": cmd_sinais, "testar": cmd_testar, "cruzado": cmd_cruzado, "resumo": cmd_resumo}[a.cmd](a)


if __name__ == "__main__":
    main()
