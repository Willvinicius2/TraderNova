"""Teste cruzado: roda cada CANDIDATA do BTCUSD em outro ativo com a MESMA estratégia, os MESMOS parâmetros e o MESMO
tempo gráfico, sem recalibrar, em desenvolvimento, validação e reserva do ativo novo (períodos e custos de protocol.json).

Critérios (lab-v2, os mesmos de calibrate.py, sem a robustez de vizinhos porque não há grade aqui):
  desenvolvimento: trades >= 60 (D1: 30), netR > 0, PF >= 1.15, sem a maior operação > 0, DD <= 10% (0,5% por operação);
  validação:       trades >= 20 (D1: 10), netR > 0, PF >= 1.15, stress netR > 0, sem a maior > 0, DD <= 10%;
  reserva:         trades >= 20 (D1: 10), netR > 0, PF >= 1.10, stress netR > 0, sem a maior > 0, DD <= 10%.
Resultado informativo: não muda o veredito do BTCUSD e não autoriza reajuste.

Uso:  python research/lab/crossasset.py [--asset EURUSD] [--from BTCUSD]
Grava research/lab/results/_cross_<ATIVO>.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))
import calibrate as C  # noqa: E402

STAGES = (("development", 1.15), ("validation", 1.15), ("reserve", 1.10))


def check(m_base, m_stress, tf, stage, pf_min):
    fails = []
    if m_base["trades"] < C.min_trades(tf, stage):
        fails.append("poucas operações")
    if m_base["netR"] <= 0:
        fails.append("netR<=0")
    if (m_base["pf"] or 0) < pf_min:
        fails.append(f"PF<{pf_min}")
    if stage != "development" and m_stress["netR"] <= 0:
        fails.append("stress<=0")
    if m_base["semMaiorR"] <= 0:
        fails.append("sem maior<=0")
    if m_base["maxDDPct"] > C.MAX_DD_PCT:
        fails.append("DD>10%")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asset", default="EURUSD")
    ap.add_argument("--from", dest="src", default="BTCUSD")
    a = ap.parse_args()
    cfg = C.PROTOCOL["assets"][a.asset]
    per = cfg["periods"]
    cb, cs = cfg["costSide"]["base"], cfg["costSide"]["stress"]
    bars = {}
    out = {"asset": a.asset, "fromAsset": a.src, "protocol": C.PROTOCOL["id"], "runAt": dt.date.today().isoformat(),
           "source": cfg["source"], "costs": cfg["costSide"], "periods": per,
           "rule": "Mesma estratégia, parâmetros e tempo gráfico escolhidos no " + a.src + "; nenhuma recalibração.",
           "strategies": {}}
    rows = []
    for p in sorted((LAB / "results").glob(f"*__{a.src}.json")):
        r = json.loads(p.read_text())
        if r.get("verdict") != "CANDIDATA":
            continue
        mod, sha = C.load_strategy(r["strategy"])
        s = r["selected"]
        tf, params = s["tf"], s["params"]
        if tf not in bars:
            df = C.load_bars(a.asset, tf)
            bars[tf] = df[df.index >= pd.Timestamp(per["warmup"][0], tz="UTC")]
        df = bars[tf]
        d = {"tf": tf, "params": params, "btcProtocol": r["protocol"], "strategySha256": sha,
             "shaMatchesBTCResult": sha == r["strategySha256"], "stages": {}}
        all_ok = True
        for stage, pf_min in STAGES:
            s0, s1 = per[stage]
            trb, mb = C.evaluate(mod, df, params, cb, s0, s1)
            _, ms = C.evaluate(mod, df, params, cs, s0, s1)
            seg = df[(df.index >= pd.Timestamp(s0, tz="UTC")) & (df.index < pd.Timestamp(s1, tz="UTC"))]
            fails = check(mb, ms, tf, stage, pf_min)
            all_ok &= not fails
            d["stages"][stage] = {"base": mb, "stress": ms, "passed": not fails, "fails": fails,
                                  "buyHoldPct": round((seg.close.iloc[-1] / seg.open.iloc[0] - 1) * 100, 1),
                                  "curve": C.engine.curve(trb)}
        d["passedAll"] = bool(all_ok)
        out["strategies"][r["strategy"]] = d
        rows.append((r["strategy"], d))
    (LAB / "results" / f"_cross_{a.asset}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))

    print(f"Teste cruzado {a.src} -> {a.asset} (custo base {cb}, stress {cs} por lado)")
    hdr = f"{'estratégia':22} {'tf':3} {'fase':5} {'trades':>6} {'netR':>8} {'PF':>6} {'semMaior':>8} {'DD%':>5} {'stressR':>8} {'B&H%':>6}  ok"
    print(hdr)
    print("-" * len(hdr))
    for sid, d in rows:
        for stage, _ in STAGES:
            x = d["stages"][stage]
            b, st = x["base"], x["stress"]
            pf = f"{b['pf']:.2f}" if b["pf"] is not None else "-"
            print(f"{sid:22} {d['tf']:3} {stage[:5]:5} {b['trades']:6d} {b['netR']:8.2f} {pf:>6} {b['semMaiorR']:8.2f} "
                  f"{b['maxDDPct']:5.2f} {st['netR']:8.2f} {x['buyHoldPct']:6.1f}  {'sim' if x['passed'] else 'não: ' + ', '.join(x['fails'])}")
        print(f"{'':22} => {'PASSA nas 3 fases' if d['passedAll'] else 'reprova'}"
              + ("" if d["shaMatchesBTCResult"] else "  (AVISO: arquivo da estratégia mudou desde o resultado BTC)"))


if __name__ == "__main__":
    main()
