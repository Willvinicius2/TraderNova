"""Acompanhamento simulado (papel) das regras da triagem que passaram em BTCUSD, ETHUSD e SOLUSD (item 3 da meta em FILA.md).

Nada é executado: a cada rodada o script baixa os candles novos da Binance spot (arquivos diários públicos de 1h,
conferidos pelo CHECKSUM), refaz os sinais com os parâmetros padrão e registra as operações abertas desde o início do
acompanhamento (INICIO). O teste é "ao vivo" porque os candles depois de INICIO não existiam quando as regras foram
escolhidas. Cada rodada grava uma foto em papel/diario/<data>.json; se uma operação já fechada numa foto anterior
mudar depois, a regra é marcada como "mudou" (sinal que repinta ao vivo).

BTCUSD: o histórico do laboratório é Bitstamp até 30/09/2026; daí em diante entra BTCUSDT da Binance (diferença de
preço pequena, dita no relatório). ETHUSD e SOLUSD já são Binance spot.

Uso: python research/lab/papel/papel.py            # baixa, recalcula, grava foto, PAPEL.md e dashboard/papel.json
     python research/lab/papel/papel.py --sem-baixar
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
sys.path.insert(0, str(LAB / "triagem"))
import triagem as T  # noqa: E402

C = T.C
engine = T.engine
INICIO = "2026-10-23"  # dia seguinte ao aviso ao Will; 30 dias até 2026-11-22
DIAS = 30
PRE = "2026-10-01"  # 01–22/10: candles também nunca vistos, mostrados à parte (antes do início oficial)
ATIVOS = {"BTCUSD": "BTCUSDT", "ETHUSD": "ETHUSDT", "SOLUSD": "SOLUSDT"}
EXTRA = C.ROOT / "research" / "cache" / "lab" / "papel"
BASES = ("https://s3-ap-northeast-1.amazonaws.com/data.binance.vision", "https://data.binance.vision")
AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
REGRAS = json.loads((HERE / "regras.json").read_text())


def get(path):
    err = None
    for b in BASES * 3:
        try:
            with urllib.request.urlopen(f"{b}/{path}", timeout=60) as r:
                return r.read()
        except Exception as e:  # 404 (dia ainda não publicado) ou espelho fora
            err = e
    raise err


def baixar(asset):
    sym = ATIVOS[asset]
    EXTRA.mkdir(parents=True, exist_ok=True)
    p = EXTRA / f"{asset}_H1.csv"
    have = pd.read_csv(p, index_col=0, parse_dates=True) if p.exists() else None
    last = have.index.max() if have is not None and len(have) else C.load_bars(asset, "H1").index.max()
    dia, novos = (last + pd.Timedelta(hours=1)).date(), []
    while dia < dt.datetime.now(dt.timezone.utc).date():
        key = f"data/spot/daily/klines/{sym}/1h/{sym}-1h-{dia}.zip"
        try:
            blob, soma = get(key), get(key + ".CHECKSUM").decode().split()[0]
        except Exception:
            break  # o arquivo do dia sai no dia seguinte; tenta de novo na próxima rodada
        if hashlib.sha256(blob).hexdigest() != soma:
            raise SystemExit(f"checksum não confere: {key}")
        d = pd.read_csv(io.BytesIO(zipfile.ZipFile(io.BytesIO(blob)).read(zipfile.ZipFile(io.BytesIO(blob)).namelist()[0])), header=None)
        ot = d[0].astype("int64")
        unit = "us" if ot.iloc[0] > 10**14 else "ms"
        d.index = pd.to_datetime(ot, unit=unit, utc=True)
        d = d[[1, 2, 3, 4, 5]].astype(float); d.columns = ["open", "high", "low", "close", "volume"]
        novos.append(d)
        dia += dt.timedelta(days=1)
    if novos:
        allx = pd.concat(([have] if have is not None else []) + novos).sort_index()
        allx = allx[~allx.index.duplicated()]
        allx.index.name = "time"
        allx.to_csv(p)
        print(asset, "candles novos até", allx.index.max(), flush=True)


def barras(asset, tf):
    base = C.load_bars(asset, "H1")[["open", "high", "low", "close", "volume"]]
    p = EXTRA / f"{asset}_H1.csv"
    if p.exists():
        x = pd.read_csv(p, index_col=0, parse_dates=True)
        base = pd.concat([base, x[x.index > base.index.max()]])
    base = base[base.index < (base.index.max() + pd.Timedelta(hours=1)).floor("1D")]  # só dias completos
    return base.resample({"H4": "4h", "D1": "1D"}[tf]).agg(AGG).dropna()


def sinais(i, tf, asset, df, tmp):
    t = ((df.index - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta("1s")).astype(int).tolist()
    (Path(tmp) / f"{asset}_{tf}.json").write_text(json.dumps({"time": t, **{k: df[k].fillna(0).tolist() for k in AGG}}))
    env = {**os.environ, "LCI_SEM_REPINTURA": "1"}
    subprocess.run(["node", "--max-old-space-size=3000", str(LAB / "triagem" / "sinais.mjs"), str(T.TRI / "lci.mjs"), tmp, asset, tf, tmp, i],
                   env=env, check=True, capture_output=True, timeout=1800)
    return json.loads((Path(tmp) / asset / tf / f"{i}.json").read_text())


def ops(df, sig, cost, a):
    out = []
    for tr in engine.run(df, sig, cost, a, "2100-01-01"):
        x = tr.__dict__.copy()
        x["aberta"] = tr.reason == "fim"
        x["r"] = round(tr.r, 3)
        out.append(x)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--sem-baixar", action="store_true")
    a = ap.parse_args()
    if not a.sem_baixar:
        for asset in ATIVOS:
            baixar(asset)
    hoje = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    foto = {"data": hoje, "inicio": INICIO, "regras": []}
    with tempfile.TemporaryDirectory() as tmp:
        dfs = {(asset, tf): barras(asset, tf) for asset in ATIVOS for tf in ("H4", "D1")}
        for r in REGRAS:
            item = {k: r.get(k) for k in ("id", "tf", "regra", "revisao")}
            item["ativos"] = {}
            for asset in ATIVOS:
                df = dfs[(asset, r["tf"])]
                d = sinais(r["id"], r["tf"], asset, df, tmp)
                ru = next((x for x in d["regras"] if x["nome"] == r["regra"]), None)
                if ru is None:
                    item["ativos"][asset] = {"erro": d.get("erro") or "regra sumiu"}; continue
                sig = T.build_sig(df, ru)
                cost = C.PROTOCOL["assets"][asset]["costSide"]["base"]
                item["ativos"][asset] = {"ate": str(df.index.max()), "ops": ops(df, sig, cost, INICIO), "pre": ops(df, sig, cost, PRE)}
            foto["regras"].append(item)
    dd = HERE / "diario"; dd.mkdir(exist_ok=True)
    antes = sorted(p for p in dd.glob("*.json") if p.stem < hoje)
    prev = json.loads(antes[-1].read_text()) if antes else None
    for item in foto["regras"]:
        for asset, v in item["ativos"].items():
            if "ops" not in v or not prev:
                continue
            pv = next((x for x in prev["regras"] if x["id"] == item["id"] and x["tf"] == item["tf"]), None)
            fech = [o for o in ((pv or {}).get("ativos", {}).get(asset, {}).get("ops") or []) if not o["aberta"]]
            atual = {(o["entry_time"], o["side"]): o for o in v["ops"]}
            v["mudou"] = sum(1 for o in fech if (o["entry_time"], o["side"]) not in atual or atual[(o["entry_time"], o["side"])]["exit_time"] != o["exit_time"])
    (dd / f"{hoje}.json").write_text(json.dumps(foto, ensure_ascii=False))
    resumo(foto)


def soma(os_):
    fech = [o for o in os_ if not o["aberta"]]
    eq, pico, dd = 0.0, 0.0, 0.0
    for o in fech:  # queda em % do capital com 0,5% de risco por operação, como no laboratório
        eq += o["r"]; pico = max(pico, eq); dd = max(dd, (pico - eq) * 0.5)
    return {"fechadas": len(fech), "abertas": len(os_) - len(fech), "netR": round(sum(o["r"] for o in fech), 2), "ddPct": round(dd, 2),
            "aberto": round(sum(o["r"] for o in os_ if o["aberta"]), 2), "ganhos": sum(o["r"] > 0 for o in fech)}


def resumo(foto):
    dia = (pd.Timestamp(foto["data"]) - pd.Timestamp(INICIO)).days
    linhas, tab = [], []
    for item in foto["regras"]:
        for asset, v in item["ativos"].items():
            if "ops" not in v:
                tab.append({"id": item["id"], "tf": item["tf"], "revisao": item.get("revisao"), "ativo": asset, "erro": v["erro"]}); continue
            s, p = soma(v["ops"]), soma(v["pre"])
            tab.append({"id": item["id"], "tf": item["tf"], "revisao": item.get("revisao"), "ativo": asset, "ate": v["ate"], **s, "preNetR": p["netR"], "preFechadas": p["fechadas"],
                        "mudou": v.get("mudou", 0), "ultima": v["ops"][-1] if v["ops"] else None})
            linhas.append(f"| {item['id']} | {item.get('revisao') or '–'} | {item['tf']} | {asset} | {s['fechadas']} | {s['ganhos']} | {s['netR']:+.2f} | {s['ddPct']:.1f} | {s['abertas']} ({s['aberto']:+.2f}) | {p['fechadas']} / {p['netR']:+.2f} | {v.get('mudou', 0)} |")
    md = [f"# Acompanhamento simulado (papel)", "",
          f"Dia {max(0, dia)} de {DIAS} (início {INICIO}, foto de {foto['data']}). Regras da triagem que passaram em BTCUSD, ETHUSD e SOLUSD, parâmetros padrão, stop 2×ATR14, saída e inversão no sinal oposto, custo base. Nada é executado.",
          "", "Resultado em R (1R = risco da operação). \"Antes do início\" é 01–22/10/2026, também fora dos dados usados na escolha. \"Mudou\" conta operações fechadas que mudaram depois (sinal que repinta ao vivo).", "",
          "| Regra | Revisão | TF | Ativo | Fechadas | Ganhos | R fechado | Queda % | Abertas (R aberto) | Antes do início: ops / R | Mudou |", "|---|---|---|---|---|---|---|---|---|---|---|", *linhas]
    (LAB / "PAPEL.md").write_text("\n".join(md) + "\n")
    for x in tab:
        x.update({"chave": f"{x['id']}|{x['tf']}|{x['ativo']}", "foto": foto["data"], "inicio": INICIO, "dia": max(0, dia), "dias": DIAS})
        u = x.pop("ultima", None)
        x["ultima"] = None if not u else f"{'compra' if u['side'] > 0 else 'venda'} {u['entry_time'][:10]}" + (" (aberta)" if u["aberta"] else f" → {u['exit_time'][:10]} {u['r']:+.2f}R")
    (LAB / "dashboard" / "papel.json").write_text(json.dumps(tab, ensure_ascii=False))
    print("\n".join(md[-len(linhas) - 2:]))


if __name__ == "__main__":
    main()
