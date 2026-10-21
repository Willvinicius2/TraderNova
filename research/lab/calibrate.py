"""Calibra e avalia uma estratégia do laboratório seguindo research/lab/protocol.json.

Uso:  python research/lab/calibrate.py <id_da_estrategia> [--asset BTCUSD] [--refine "motivo"]
Grava research/lab/results/<id>__<ativo>.json. Não abre validação/reserva se o desenvolvimento reprovar.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import math
import statistics
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent
ROOT = LAB.parents[1]
sys.path.insert(0, str(LAB))
import engine  # noqa: E402

PROTOCOL = json.loads((LAB / "protocol.json").read_text())
MAX_COMBOS = 400
MAX_DD_PCT = 10.0  # perda total da conta (10%) com 0,5% de risco por operação


def load_bars(asset: str, tf: str) -> pd.DataFrame:
    p = ROOT / "research" / "cache" / "lab" / f"{asset}_{tf}.csv.gz"
    if not p.exists():
        raise SystemExit(f"Sem dados em {p}. Rode research/lab/data.py primeiro.")
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    return df[["open", "high", "low", "close", "volume"]].astype(float)


def load_strategy(sid: str):
    path = LAB / "strategies" / f"{sid}.py"
    spec = importlib.util.spec_from_file_location(f"strat_{sid}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, hashlib.sha256(path.read_bytes()).hexdigest()


def years(a, b):
    return (pd.Timestamp(b) - pd.Timestamp(a)).days / 365.25


def grid(meta) -> list[dict]:
    keys = list(meta["grid"])
    return [dict(zip(keys, v)) for v in itertools.product(*(meta["grid"][k] for k in keys))]


def neighbors(meta, combo) -> list[dict]:
    out = []
    for k, vals in meta["grid"].items():
        if len(vals) < 2:
            continue
        j = vals.index(combo[k])
        for d in (-1, 1):
            if 0 <= j + d < len(vals):
                nb = dict(combo)
                nb[k] = vals[j + d]
                out.append(nb)
    return out


def deflated_sharpe(sr: float, n_obs: int, srs: list[float], skew: float, kurt: float) -> float | None:
    """DSR de Bailey & López de Prado (2014), por operação."""
    srs = [s for s in srs if s is not None and math.isfinite(s)]
    if n_obs < 3 or len(srs) < 2 or sr is None:
        return None
    from statistics import NormalDist

    nd = NormalDist()
    var = statistics.pvariance(srs)
    N = len(srs)
    g = 0.5772156649
    sr0 = math.sqrt(var) * ((1 - g) * nd.inv_cdf(1 - 1 / N) + g * nd.inv_cdf(1 - 1 / (N * math.e)))
    den = 1 - skew * sr + (kurt - 1) / 4 * sr * sr
    if den <= 0:
        return None
    z = (sr - sr0) * math.sqrt(n_obs - 1) / math.sqrt(den)
    return round(nd.cdf(z), 3)


def evaluate(mod, df, params, cost, start, end):
    sig = mod.signals(df, dict(params))
    tr = engine.run(df, sig, cost, start, end)
    return tr, engine.metrics(tr, years(start, end))


def min_trades(tf, stage):
    if stage == "development":
        return 30 if tf == "D1" else 60
    return 10 if tf == "D1" else 20


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sid")
    ap.add_argument("--asset", default="BTCUSD")
    ap.add_argument("--refine", default=None, help="motivo do refinamento (conta como tentativa extra)")
    a = ap.parse_args()

    mod, sha = load_strategy(a.sid)
    meta = mod.META
    cfg = PROTOCOL["assets"][a.asset]
    per = cfg["periods"]
    cb, cs = cfg["costSide"]["base"], cfg["costSide"]["stress"]
    combos = grid(meta)
    tfs = meta["timeframes"]
    if len(combos) * len(tfs) > MAX_COMBOS:
        raise SystemExit(f"Grade grande demais: {len(combos) * len(tfs)} > {MAX_COMBOS}")

    dev_a, dev_b = per["development"]
    rows = []
    best = None
    for tf in tfs:
        df = load_bars(a.asset, tf)
        df = df[df.index >= pd.Timestamp(per["warmup"][0], tz="UTC")]
        cache = {}
        for c in combos:
            trs, m = evaluate(mod, df, c, cb, dev_a, dev_b)
            by_year = {}
            for t in trs:
                by_year[t.exit_time[:4]] = by_year.get(t.exit_time[:4], 0.0) + t.r
            m["anosPositivos"] = sum(1 for v in by_year.values() if v > 0)
            m["anosTotal"] = int(round(years(dev_a, dev_b)))
            cache[json.dumps(c, sort_keys=True)] = m
            rows.append({"tf": tf, "params": c, "dev": m})
        for row in [r for r in rows if r["tf"] == tf]:
            m = row["dev"]
            ok = (m["trades"] >= min_trades(tf, "development") and m["netR"] > 0 and (m["pf"] or 0) >= 1.15
                  and m["semMaiorR"] > 0 and m["maxDDPct"] <= MAX_DD_PCT
                  and (PROTOCOL["id"] < "lab-v3" or m["anosPositivos"] >= m["anosTotal"] - 1))
            nbs = [cache[json.dumps(nb, sort_keys=True)] for nb in neighbors(meta, row["params"])]
            nb_pf = statistics.median([(x["pf"] or 0) for x in nbs]) if nbs else None
            row["neighborMedianPF"] = round(nb_pf, 3) if nb_pf is not None else None
            row["robust"] = nb_pf is None or nb_pf >= 1.05
            row["eligible"] = bool(ok and row["robust"])
            row["score"] = m["netR"] / max(m["maxDDR"], 5.0)
            if row["eligible"] and (best is None or row["score"] > best["score"]):
                best = row

    def same_tf_srs(tf):
        return [r["dev"]["sharpeTrade"] for r in rows if r["tf"] == tf]
    top = sorted(rows, key=lambda r: r["score"], reverse=True)[:5]
    out = {
        "strategy": a.sid,
        "name": meta["name"],
        "family": meta["family"],
        "sources": meta["sources"],
        "rule": meta["rule"],
        "asset": a.asset,
        "protocol": PROTOCOL["id"],
        "strategySha256": sha,
        "refinement": a.refine,
        "combinationsTested": len(rows),
        "costs": cfg["costSide"],
        "periods": per,
        "topDevelopment": [{k: r[k] for k in ("tf", "params", "dev", "neighborMedianPF", "robust", "eligible")} for r in top],
    }
    if best is None:
        out["verdict"] = "REPROVADA_DESENVOLVIMENTO"
        out["selected"] = None
        # curva da melhor combinação no desenvolvimento, só para visualização
        if top:
            t0 = top[0]
            df0 = load_bars(a.asset, t0["tf"])
            df0 = df0[df0.index >= pd.Timestamp(per["warmup"][0], tz="UTC")]
            trd0, _ = evaluate(mod, df0, t0["params"], cb, dev_a, dev_b)
            out["curves"] = {"development": engine.curve(trd0)}
    else:
        tf = best["tf"]
        df = load_bars(a.asset, tf)
        df = df[df.index >= pd.Timestamp(per["warmup"][0], tz="UTC")]
        trd, _ = evaluate(mod, df, best["params"], cb, dev_a, dev_b)
        r = np.array([t.r for t in trd])
        sk = float(pd.Series(r).skew()) if len(r) > 2 else 0.0
        ku = float(pd.Series(r).kurt() + 3) if len(r) > 3 else 3.0
        dsr = deflated_sharpe(best["dev"]["sharpeTrade"], len(r), same_tf_srs(tf), sk, ku)
        curves = {"development": engine.curve(trd)}
        sel = {"tf": tf, "params": best["params"], "development": best["dev"],
               "neighborMedianPF": best["neighborMedianPF"], "deflatedSharpe": dsr}
        verdict = "CANDIDATA"
        for stage, pf_min, fail in (("validation", 1.15, "REPROVADA_VALIDACAO"), ("reserve", 1.10, "REPROVADA_RESERVA")):
            s, e = per[stage]
            trb, mb = evaluate(mod, df, best["params"], cb, s, e)
            _, ms = evaluate(mod, df, best["params"], cs, s, e)
            curves[stage] = engine.curve(trb)
            ok = (mb["trades"] >= min_trades(tf, stage) and mb["netR"] > 0 and (mb["pf"] or 0) >= pf_min and ms["netR"] > 0
                  and mb["semMaiorR"] > 0 and mb["maxDDPct"] <= MAX_DD_PCT)
            sel[stage] = {"base": mb, "stress": ms, "passed": bool(ok)}
            if not ok:
                verdict = fail
                break
        if dsr is not None and dsr < 0.5:
            sel["warning"] = "Deflated Sharpe < 0.5: a escolha no desenvolvimento pode ser sorte entre muitas combinações."
        out["selected"] = sel
        out["curves"] = curves
        out["verdict"] = verdict

    res = LAB / "results"
    res.mkdir(exist_ok=True)
    name = f"{a.sid}__{a.asset}.json"
    (res / name).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    s = out["selected"]
    print(f"{a.sid} {a.asset}: {out['verdict']} | combinações {len(rows)}")
    if s:
        print(f"  escolhido {s['tf']} {s['params']} DSR={s['deflatedSharpe']}")
        for k in ("development", "validation", "reserve"):
            if k in s:
                m = s[k] if k == "development" else s[k]["base"]
                print(f"  {k}: trades={m['trades']} netR={m['netR']} PF={m['pf']} DD={m['maxDDR']}R")
    else:
        t = out["topDevelopment"][0]["dev"] if out["topDevelopment"] else {}
        print(f"  melhor no desenvolvimento: {out['topDevelopment'][0]['tf'] if out['topDevelopment'] else '-'} trades={t.get('trades')} netR={t.get('netR')} PF={t.get('pf')}")


if __name__ == "__main__":
    main()
