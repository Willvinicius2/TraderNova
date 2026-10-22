"""Validação das candidatas do laboratório (research/lab), em pasta separada: não altera nada do laboratório.

Para cada CANDIDATA do BTCUSD em research/lab/results:
  1. Ano a ano com os parâmetros escolhidos pelo laboratório, em 4 variantes:
       orig    = regra e lado escolhidos no laboratório;
       both    = mesma regra operando comprado e vendido;
       short   = só o lado vendido;
       regime  = comprado e vendido, mas compra só acima da média de 200 dias e vende só abaixo (sai quando cruza a média).
  2. Sensibilidade: a grade inteira do laboratório no BTC, quantas combinações ficam positivas na validação e na reserva.
  3. Walk-forward: calibra em 3 anos, opera o ano seguinte sem olhar, rola um ano e repete. Junta só os anos "fora da amostra".
     Feito no BTC e, recalibrando, em EURUSD, USDJPY e XAUUSD.
  4. Teste cruzado com os parâmetros fixos do BTC nos outros ativos, ano a ano.

O motor, as estratégias e os dados são os do laboratório (research/lab). Cada combinação roda uma vez no histórico inteiro;
as janelas usam as operações abertas dentro delas, e o custo é recalculado por operação (o caminho do stop não depende do custo).

Uso:  python research/validacao/validar.py [--only TV21_aroon] [--assets BTCUSD,EURUSD] [--workers 4]
Grava research/validacao/results/<id>.json.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
LAB = HERE.parent / "lab"
sys.path.insert(0, str(LAB))
import calibrate as C  # noqa: E402
import engine  # noqa: E402
import indicators as ind  # noqa: E402

CFG = json.loads((HERE / "config.json").read_text())
VARIANTS = ("orig", "both", "short", "regime")
MAX_DD_PCT = 10.0
RISK_PCT = 0.5


# ---------- sinais ----------

def bars_per_day(df):
    step = (df.index[1:] - df.index[:-1]).to_series().median()
    return max(1, int(round(86400 / step.total_seconds())))


def variant_signals(mod, df, params, variant, regime_days=200):
    p = dict(params)
    if variant in ("both", "short", "regime") and "side" in p:
        p["side"] = "both"
    sig = dict(mod.signals(df, p))
    e = np.asarray(sig["entry"]).astype(int).copy()
    if variant == "short":
        e = np.where(e < 0, -1, 0)
    elif variant == "regime":
        c = df.close.values
        ma = ind.sma(c, regime_days * bars_per_day(df))
        ok = ~np.isnan(ma)
        up = ok & (c > ma)
        dn = ok & (c < ma)
        e = np.where((e > 0) & up, 1, np.where((e < 0) & dn, -1, 0))
        exl = sig.get("exit_long")
        exs = sig.get("exit_short")
        sig["exit_long"] = dn if exl is None else (np.asarray(exl, bool) | dn)
        sig["exit_short"] = up if exs is None else (np.asarray(exs, bool) | up)
    sig["entry"] = e
    return sig


def run_trades(mod, df, params, variant):
    """Roda uma vez no histórico todo; devolve arrays por operação para recalcular custo e janela sem rodar de novo."""
    sig = variant_signals(mod, df, params, variant)
    tr = engine.run(df, sig, 0.0)
    if not tr:
        return {k: np.zeros(0) for k in ("t", "tx", "gross", "turn", "side")}
    ep = np.array([t.entry for t in tr])
    xp = np.array([t.exit for t in tr])
    sp = np.array([t.stop for t in tr])
    risk = np.abs(ep - sp)
    side = np.array([t.side for t in tr], dtype=float)
    return {
        "t": pd.to_datetime([t.entry_time for t in tr], utc=True).values.astype("datetime64[s]").astype(np.int64),
        "tx": pd.to_datetime([t.exit_time for t in tr], utc=True).values.astype("datetime64[s]").astype(np.int64),
        "gross": (xp - ep) * side / risk,
        "turn": (ep + xp) / risk,
        "side": side,
    }


def ts(s):
    return int(pd.Timestamp(s, tz="UTC").timestamp())


def window_r(tr, a, b, cost):
    m = (tr["t"] >= ts(a)) & (tr["t"] < ts(b))
    return tr["gross"][m] - tr["turn"][m] * cost, tr["side"][m]


def metrics(r):
    r = np.asarray(r, float)
    if len(r) == 0:
        return {"trades": 0, "netR": 0.0, "pf": None, "maxDDPct": 0.0, "semMaiorR": 0.0, "winRate": None}
    gp, gl = r[r > 0].sum(), -r[r < 0].sum()
    eq = np.cumsum(r)
    dd = float(np.max(np.maximum.accumulate(np.r_[0, eq])[1:] - eq))
    return {
        "trades": int(len(r)),
        "netR": round(float(r.sum()), 2),
        "pf": round(float(gp / gl), 3) if gl > 0 else None,
        "maxDDR": round(max(dd, 0.0), 2),
        "maxDDPct": round(max(dd, 0.0) * RISK_PCT, 2),
        "semMaiorR": round(float(r.sum() - r.max()), 2),
        "winRate": round(float((r > 0).mean()), 3),
    }


# ---------- grade ----------

def variant_grid(meta, variant):
    g = dict(meta["grid"])
    if variant != "orig" and "side" in g:
        g["side"] = ["both"]
    keys = list(g)
    return g, [dict(zip(keys, v)) for v in itertools.product(*(g[k] for k in keys))]


def neighbors(g, combo):
    out = []
    for k, vals in g.items():
        if len(vals) < 2:
            continue
        j = vals.index(combo[k])
        for d in (-1, 1):
            if 0 <= j + d < len(vals):
                nb = dict(combo)
                nb[k] = vals[j + d]
                out.append(nb)
    return out


def key(c):
    return json.dumps(c, sort_keys=True)


# ---------- tarefas ----------

def load(asset, tf):
    df = C.load_bars(asset, tf)
    return df[df.index >= pd.Timestamp(CFG["assets"][asset]["start"], tz="UTC")]


def task_grid(args):
    """Todas as combinações da grade de uma variante num ativo/tempo gráfico."""
    sid, asset, tf, variant = args
    mod, _ = load_strategy(sid)
    df = load(asset, tf)
    g, combos = variant_grid(mod.META, variant)
    out = {}
    for c in combos:
        out[key(c)] = run_trades(mod, df, c, variant)
    return (sid, asset, tf, variant), out


def walk_forward(trs_by_tf, grids, asset, train_years, min_per_year):
    """trs_by_tf: {tf: {combo_key: trades}}; escolhe a cada ano a melhor combinação nos train_years anteriores."""
    a = CFG["assets"][asset]
    cb, cs = a["costSide"]["base"], a["costSide"]["stress"]
    out_base, out_stress, folds = [], [], []
    for y in range(a["wfFirstTest"], a["wfLastTest"] + 1):
        tr0, tr1 = f"{y - train_years}-01-01", f"{y}-01-01"
        te0, te1 = f"{y}-01-01", min(f"{y + 1}-01-01", a["end"])
        best = None
        for tf, trs in trs_by_tf.items():
            g = grids[tf]
            cache = {k: metrics(window_r(v, tr0, tr1, cb)[0]) for k, v in trs.items()}
            mt = min_per_year * train_years * (0.5 if tf == "D1" else 1)
            for k, m in cache.items():
                ok = (m["trades"] >= mt and m["netR"] > 0 and (m["pf"] or 0) >= 1.15
                      and m["semMaiorR"] > 0 and m["maxDDPct"] <= MAX_DD_PCT)
                if not ok:
                    continue
                nbs = [cache[key(nb)] for nb in neighbors(g, json.loads(k))]
                if nbs and statistics.median([(x["pf"] or 0) for x in nbs]) < 1.05:
                    continue
                score = m["netR"] / max(m["maxDDR"], 5.0)
                if best is None or score > best[0]:
                    best = (score, tf, k)
        if best is None:
            folds.append({"testYear": y, "chosen": None, "test": metrics([])})
            continue
        _, tf, k = best
        rb, side = window_r(trs_by_tf[tf][k], te0, te1, cb)
        rs, _ = window_r(trs_by_tf[tf][k], te0, te1, cs)
        out_base.append(rb)
        out_stress.append(rs)
        folds.append({"testYear": y, "chosen": {"tf": tf, "params": json.loads(k)},
                      "train": metrics(window_r(trs_by_tf[tf][k], tr0, tr1, cb)[0]),
                      "test": metrics(rb), "testStressNetR": round(float(rs.sum()), 2),
                      "shortShare": round(float((side < 0).mean()), 2) if len(side) else None})
    rb = np.concatenate(out_base) if out_base else np.zeros(0)
    rs = np.concatenate(out_stress) if out_stress else np.zeros(0)
    years = [f for f in folds if f["chosen"]]
    return {"trainYears": train_years, "folds": folds, "oos": metrics(rb), "oosStressNetR": round(float(rs.sum()), 2),
            "oosStressDDPct": metrics(rs)["maxDDPct"],
            "yearsTraded": len(years), "yearsPositive": sum(1 for f in years if f["test"]["netR"] > 0)}


def yearly(tr, asset, cost):
    a = CFG["assets"][asset]
    out = {}
    for y in range(int(a["start"][:4]) + 1, int(a["end"][:4]) + 1):
        r, s = window_r(tr, f"{y}-01-01", min(f"{y + 1}-01-01", a["end"]), cost)
        out[y] = {"netR": round(float(r.sum()), 2), "trades": int(len(r)), "shorts": int((s < 0).sum())}
    return out


def buy_hold(asset):
    df = load(asset, "D1")
    a = CFG["assets"][asset]
    out = {}
    for y in range(int(a["start"][:4]) + 1, int(a["end"][:4]) + 1):
        s = df[(df.index >= pd.Timestamp(f"{y}-01-01", tz="UTC")) & (df.index < pd.Timestamp(f"{y + 1}-01-01", tz="UTC"))]
        if len(s):
            out[y] = round((s.close.iloc[-1] / s.open.iloc[0] - 1) * 100, 1)
    return out


def phase_metrics(tr, asset, cost_key="base"):
    a = CFG["assets"][asset]
    return {ph: metrics(window_r(tr, *a["phases"][ph], a["costSide"][cost_key])[0]) for ph in a["phases"]}


# ---------- principal ----------

def load_strategy(sid):
    if sid.startswith("BM"):
        import hashlib
        import importlib.util
        path = HERE / "benchmarks" / f"{sid}.py"
        spec = importlib.util.spec_from_file_location(f"bm_{sid}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, hashlib.sha256(path.read_bytes()).hexdigest()
    return C.load_strategy(sid)


def candidates(benchmarks=False):
    """CANDIDATAS do laboratório; com benchmarks=True, as referências ingênuas (parâmetros 'fixos' = meio da grade, lado both)."""
    out = []
    if benchmarks:
        for p in sorted((HERE / "benchmarks").glob("BM*.py")):
            mod, sha = load_strategy(p.stem)
            g = mod.META["grid"]
            params = {k: v[len(v) // 2] for k, v in g.items()}
            params["side"] = "both"
            out.append({"strategy": p.stem, "name": mod.META["name"], "protocol": "-", "strategySha256": sha,
                        "selected": {"tf": "H4", "params": params}})
    for p in sorted((LAB / "results").glob("*__BTCUSD.json")):
        r = json.loads(p.read_text())
        if r.get("verdict") == "CANDIDATA":
            out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--assets", default=",".join(CFG["assets"]))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--benchmarks", action="store_true", help="inclui as referências ingênuas de benchmarks/")
    a = ap.parse_args()
    assets = [x for x in a.assets.split(",") if x]
    cands = [c for c in candidates(a.benchmarks) if a.only is None or c["strategy"] in a.only.split(",")]
    tasks = []
    for c in cands:
        mod, _ = load_strategy(c["strategy"])
        for asset in assets:
            for tf in mod.META["timeframes"]:
                for v in ("orig", "regime"):
                    tasks.append((c["strategy"], asset, tf, v))
            # variantes both/short só no tempo gráfico escolhido (ano a ano com os parâmetros fixos)
            for v in ("both", "short"):
                tasks.append((c["strategy"], asset, c["selected"]["tf"], v))
    # tarefas pesadas (H1) primeiro
    tasks.sort(key=lambda t: {"H1": 0, "H4": 1, "D1": 2}.get(t[2], 3))
    res = {}
    with ProcessPoolExecutor(a.workers) as ex:
        for k, v in ex.map(task_grid, tasks):
            res[k] = v
            print("ok", *k, len(v), flush=True)

    outdir = HERE / "results"
    outdir.mkdir(exist_ok=True)
    bh = {asset: buy_hold(asset) for asset in assets}
    for c in cands:
        sid = c["strategy"]
        mod, sha = load_strategy(sid)
        meta = mod.META
        sel_tf, sel_p = c["selected"]["tf"], c["selected"]["params"]
        rep = {"strategy": sid, "name": c["name"], "labProtocol": c["protocol"], "labTf": sel_tf, "labParams": sel_p,
               "strategySha256": sha, "shaMatchesLab": sha == c["strategySha256"], "assets": {}}
        for asset in assets:
            ac = CFG["assets"][asset]
            cb = ac["costSide"]["base"]
            A = {"buyHoldPctByYear": bh[asset], "fixed": {}, "sensitivity": {}, "walkForward": {}}
            # 1 e 4: parâmetros fixos do laboratório, por variante
            for v in VARIANTS:
                g, _ = variant_grid(meta, v)
                pv = dict(sel_p)
                if v != "orig" and "side" in pv:
                    pv["side"] = "both"
                tr = res[(sid, asset, sel_tf, v)][key(pv)]
                A["fixed"][v] = {"params": pv, "byYear": yearly(tr, asset, cb),
                                 "phases": phase_metrics(tr, asset), "phasesStress": phase_metrics(tr, asset, "stress"),
                                 "all": metrics(window_r(tr, ac["phases"]["development"][0], ac["end"], cb)[0])}
            # 2: sensibilidade da grade (variante orig, todos os tempos gráficos)
            for v in ("orig", "regime"):
                rows = []
                for tf in meta["timeframes"]:
                    for k, tr in res[(sid, asset, tf, v)].items():
                        ph = phase_metrics(tr, asset)
                        rows.append((tf, k, ph))
                s = {}
                for ph in ac["phases"]:
                    vals = [r[2][ph] for r in rows]
                    s[ph] = {"combos": len(vals),
                             "positivas": sum(1 for m in vals if m["netR"] > 0),
                             "pfMediano": round(statistics.median([(m["pf"] or 0) for m in vals]), 3) if vals else None}
                s["todasAsFasesPositivas"] = sum(1 for r in rows if all(r[2][ph]["netR"] > 0 for ph in ac["phases"]))
                A["sensitivity"][v] = s
            # 3: walk-forward recalibrando no próprio ativo
            for v in ("orig", "regime"):
                trs = {tf: res[(sid, asset, tf, v)] for tf in meta["timeframes"]}
                grids = {tf: variant_grid(meta, v)[0] for tf in meta["timeframes"]}
                A["walkForward"][v] = walk_forward(trs, grids, asset, CFG["trainYears"], CFG["minTradesPerYear"])
                # mesmo walk-forward travado no tempo gráfico do laboratório
                A["walkForward"][v + "_" + sel_tf] = walk_forward({sel_tf: trs[sel_tf]}, {sel_tf: grids[sel_tf]}, asset,
                                                                  CFG["trainYears"], CFG["minTradesPerYear"])
                # sensibilidade ao tamanho da janela de calibração (2 e 4 anos), só o resumo
                for ty in (2, 4):
                    w = walk_forward(trs, grids, asset, ty, CFG["minTradesPerYear"])
                    A["walkForward"][f"{v}_treino{ty}"] = {k: w[k] for k in w if k != "folds"}
            rep["assets"][asset] = A
        (outdir / f"{sid}.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str))
        print("gravado", sid)


if __name__ == "__main__":
    main()
