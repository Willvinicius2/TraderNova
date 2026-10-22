"""Dados públicos da Binance (spot e perpétuo USDT-M), conferidos por SHA-256. Sem chave, sem ordens.

Fonte: arquivo público data.binance.vision (github.com/binance/binance-public-data). Quando o domínio é
bloqueado pela rede (caso deste ambiente), usa o espelho S3 oficial do mesmo bucket, que serve os mesmos
arquivos e os mesmos .CHECKSUM. O endereço usado fica no manifesto.

O que baixa por símbolo (futuros USDT-M):
  klines 1h, fundingRate (a cada 8h; 4h em alguns períodos), premiumIndexKlines 1h e, com --metrics,
  metrics diários (open interest e razões long/short a cada 5 min, desde 2020-09).
Spot (--spot) baixa klines 1h, útil para comparar com o histórico antigo do laboratório.

Saída em research/cache/binance/ (não versionado):
  <SYM>_um_H1.csv.gz   open/high/low/close/volume do perpétuo, funding_rate na hora em que é cobrado,
                       premium (fechamento do premium index) e, se houver, colunas de metrics agregadas por hora.
  manifest_<SYM>.json  URL, sha256 e tamanho de cada arquivo mensal/diário.
Uma cópia do manifesto vai para research/ferramentas/dados/ (versionado) para rastrear qualquer resultado.

Uso:
  python research/ferramentas/dados_binance.py BTCUSDT ETHUSDT SOLUSDT [--metrics] [--spot]
  from ferramentas.dados_binance import carregar; df = carregar("BTCUSDT")
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import io
import json
import re
import time
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "research" / "cache" / "binance"
MANIFESTOS = Path(__file__).resolve().parent / "dados"
BASES = [
    "https://data.binance.vision",
    "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision",
]
UA = {"User-Agent": "TraderNova-research/1.0"}


def _get(url: str, timeout: int = 60) -> bytes:
    for tentativa in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except Exception:
            if tentativa == 3:
                raise
            time.sleep(2 ** (tentativa + 1))
    raise RuntimeError(url)


_BASE: str | None = None


def base() -> str:
    """Primeiro endereço que responde. O domínio principal vem primeiro; o S3 é o espelho do mesmo bucket."""
    global _BASE
    if _BASE is None:
        for b in BASES:
            try:
                urllib.request.urlopen(urllib.request.Request(b + "/data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2020-01.zip.CHECKSUM", headers=UA), timeout=15).read()
                _BASE = b
                break
            except Exception:
                continue
        if _BASE is None:
            raise RuntimeError("Nenhum endereço do arquivo da Binance respondeu (rede bloqueada?)")
    return _BASE


def listar(prefixo: str) -> list[str]:
    """Lista as chaves .zip de um prefixo pelo índice S3 (paginado)."""
    s3 = BASES[1]
    chaves, marcador = [], ""
    while True:
        xml = _get(f"{s3}?delimiter=/&prefix={prefixo}&marker={marcador}").decode()
        novas = re.findall(r"<Key>([^<]+)</Key>", xml)
        chaves += [k for k in novas if k.endswith(".zip")]
        if "<IsTruncated>true</IsTruncated>" not in xml or not novas:
            return chaves
        marcador = novas[-1]


def baixar(chave: str) -> dict:
    """Baixa um .zip e confere com o .CHECKSUM publicado. Arquivos já em cache são reconferidos."""
    destino = CACHE / "raw" / chave.split("data/", 1)[1]
    destino.parent.mkdir(parents=True, exist_ok=True)
    soma_path = destino.with_name(destino.name + ".CHECKSUM")
    url = f"{base()}/{chave}"
    esperado = soma_path.read_bytes() if soma_path.exists() else _get(url + ".CHECKSUM")
    blob = destino.read_bytes() if destino.exists() else _get(url)
    digest = hashlib.sha256(blob).hexdigest()
    if digest != esperado.decode().split()[0]:
        destino.unlink(missing_ok=True)
        raise ValueError(f"Checksum não confere: {chave}")
    destino.write_bytes(blob)
    soma_path.write_bytes(esperado)
    return {"url": url, "sha256": digest, "bytes": len(blob), "path": str(destino.relative_to(CACHE))}


def _csv(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as z:
        nome = z.namelist()[0]
        raw = z.read(nome)
    primeira = raw.split(b"\n", 1)[0]
    tem_cabecalho = not primeira[:1].isdigit()
    return pd.read_csv(io.BytesIO(raw), header=0 if tem_cabecalho else None)


def _tempo(col: pd.Series) -> pd.DatetimeIndex:
    v = col.astype("int64")
    v = v.where(v < 10**14, v // 1000)  # alguns arquivos recentes usam microssegundos
    return pd.DatetimeIndex(pd.to_datetime(v, unit="ms", utc=True))


KCOLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "count",
         "taker_buy_volume", "taker_buy_quote_volume", "ignore"]


def _klines(entradas: list[dict]) -> pd.DataFrame:
    partes = []
    for e in entradas:
        d = _csv(CACHE / e["path"])
        d.columns = KCOLS[: len(d.columns)]
        d.index = _tempo(d.open_time)
        partes.append(d[["open", "high", "low", "close", "volume", "taker_buy_volume"]].astype(float))
    out = pd.concat(partes).sort_index()
    return out[~out.index.duplicated()]


def montar(sym: str, metrics: bool = False, spot: bool = False) -> pd.DataFrame:
    jobs = {
        "klines": f"data/futures/um/monthly/klines/{sym}/1h/",
        "funding": f"data/futures/um/monthly/fundingRate/{sym}/",
        "premium": f"data/futures/um/monthly/premiumIndexKlines/{sym}/1h/",
    }
    if metrics:
        jobs["metrics"] = f"data/futures/um/daily/metrics/{sym}/"
    if spot:
        jobs["spot"] = f"data/spot/monthly/klines/{sym}/1h/"
    manifesto = {"fonte": "Binance public data (binance-public-data)", "base": base(),
                 "geradoEm": pd.Timestamp.now(tz="UTC").isoformat(), "simbolo": sym, "arquivos": {}}
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        for nome, prefixo in jobs.items():
            chaves = listar(prefixo)
            manifesto["arquivos"][nome] = list(ex.map(baixar, chaves))
            print(sym, nome, len(chaves), "arquivos", flush=True)

    df = _klines(manifesto["arquivos"]["klines"])
    fr = pd.concat(_csv(CACHE / e["path"]) for e in manifesto["arquivos"]["funding"])
    fr.index = _tempo(fr.calc_time).floor("1h")
    fr = fr[~fr.index.duplicated()]
    # funding cobrado sobre a posição aberta no instante calc_time; fica na barra que começa nessa hora
    df["funding_rate"] = fr.last_funding_rate.astype(float).reindex(df.index).fillna(0.0)
    pr = _klines(manifesto["arquivos"]["premium"])
    df["premium"] = pr.close.reindex(df.index)
    if metrics and manifesto["arquivos"].get("metrics"):
        m = pd.concat(_csv(CACHE / e["path"]) for e in manifesto["arquivos"]["metrics"])
        m.index = pd.to_datetime(m.create_time, utc=True)
        num = m.drop(columns=[c for c in ("create_time", "symbol") if c in m]).apply(pd.to_numeric, errors="coerce")
        df = df.join(num.resample("1h", label="left", closed="left").last(), how="left")
    if spot and manifesto["arquivos"].get("spot"):
        sp = _klines(manifesto["arquivos"]["spot"])
        df["spot_close"] = sp.close.reindex(df.index)

    falhas = df.index.to_series().diff().dt.total_seconds().div(3600).sub(1)
    manifesto["barras"] = len(df)
    manifesto["inicio"], manifesto["fim"] = str(df.index[0]), str(df.index[-1])
    manifesto["lacunas"] = [{"depois": str(i), "horasFaltando": int(h)} for i, h in falhas[falhas > 0].items()]
    df.index.name = "time"
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_csv(CACHE / f"{sym}_um_H1.csv.gz")
    manifesto["sha256Saida"] = hashlib.sha256((CACHE / f"{sym}_um_H1.csv.gz").read_bytes()).hexdigest()
    texto = json.dumps(manifesto, indent=1, ensure_ascii=False)
    (CACHE / f"manifest_{sym}.json").write_text(texto)
    MANIFESTOS.mkdir(exist_ok=True)
    resumo = {k: v for k, v in manifesto.items() if k != "arquivos"}
    resumo["arquivos"] = {k: [{"url": a["url"], "sha256": a["sha256"]} for a in v] for k, v in manifesto["arquivos"].items()}
    (MANIFESTOS / f"manifest_{sym}.json").write_text(json.dumps(resumo, indent=1, ensure_ascii=False))
    print(sym, len(df), "barras H1", df.index[0], "→", df.index[-1], f"{len(manifesto['lacunas'])} lacunas", flush=True)
    return df


def carregar(sym: str) -> pd.DataFrame:
    """Lê o H1 já montado. Rode o script antes (python research/ferramentas/dados_binance.py SYM)."""
    p = CACHE / f"{sym}_um_H1.csv.gz"
    if not p.exists():
        raise FileNotFoundError(f"{p} não existe: rode python research/ferramentas/dados_binance.py {sym}")
    return pd.read_csv(p, index_col=0, parse_dates=True)


def diario(df: pd.DataFrame) -> pd.DataFrame:
    """D1 em UTC a partir do H1. funding_rate do dia = soma das cobranças do dia."""
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum", "funding_rate": "sum"}
    return df.resample("1D").agg({k: v for k, v in agg.items() if k in df}).dropna(subset=["close"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("simbolos", nargs="+")
    ap.add_argument("--metrics", action="store_true", help="open interest e long/short diários (muitos arquivos)")
    ap.add_argument("--spot", action="store_true")
    a = ap.parse_args()
    for s in a.simbolos:
        montar(s.upper(), metrics=a.metrics, spot=a.spot)
