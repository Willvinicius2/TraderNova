"""Prepara os candles do laboratório em research/cache/lab (não versionado).

BTCUSD: Bitstamp 1 minuto do repositório público github.com/ff137/bitstamp-btcusd-minute-data.
  git clone --depth 1 --filter=blob:none --no-checkout https://github.com/ff137/bitstamp-btcusd-minute-data <dir>
  git -C <dir> checkout HEAD -- data/historical data/updates
  python research/lab/data.py --bitstamp <dir>

EURUSD: ticks Dukascopy publicados em github.com/FX-Data/FX-Data-EURUSD-DS (um ramo por ano, EURUSD-<ano>,
  um CSV de ticks por hora em UTC: hora, bid, ask, volume bid, volume ask). O script busca cada ramo com
  --depth 1 --filter=blob:none, faz checkout mês a mês, reduz para M1 (preço médio bid/ask, contagem de ticks
  e spread médio) e apaga os ticks. Cada ano leva alguns minutos e ~300 MB de rede; os M1 ficam em <work>.
  python research/lab/data.py --fxdata EURUSD --work <pasta> [--years 2009-2022]
  Os commits usados ficam em <work>/EURUSD_<ano>.commit e em <work>/EURUSD_sources.json.

Fins de semana no FX: o mercado abre domingo ~21/22h UTC. No D1 as horas de domingo entram no candle de segunda,
para não criar um "dia" de 2 horas. M15/H1/H4 são reamostrados direto em UTC (sem candles vazios).
"""
import argparse
import glob
import io
import json
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "cache" / "lab"
RULES = {"M15": "15min", "H1": "1h", "H4": "4h", "D1": "1D"}
AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}


def bitstamp(folder: str):
    d = Path(folder) / "data"
    parts = [pd.read_csv(p) for p in sorted((d / "historical").glob("*.csv.gz")) + sorted((d / "updates").glob("*.csv"))]
    m = pd.concat(parts).drop_duplicates("timestamp").sort_values("timestamp")
    m.index = pd.to_datetime(m.timestamp, unit="s", utc=True)
    m = m[m.index >= "2014-01-01"]
    OUT.mkdir(parents=True, exist_ok=True)
    for tf, rule in RULES.items():
        r = m.resample(rule).agg(AGG).dropna()
        r.to_csv(OUT / f"BTCUSD_{tf}.csv.gz")
        print(tf, len(r), r.index.min(), r.index.max())


def _git(repo: Path, *a) -> str:
    return subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True).stdout


def fx_year(pair: str, year: int, work: Path) -> Path:
    """Baixa o ramo <pair>-<year> do FX-Data/FX-Data-<pair>-DS e grava <work>/<pair>_M1_<year>.csv.gz (mid)."""
    out = work / f"{pair}_M1_{year}.csv.gz"
    if out.exists():
        return out
    repo = work / f"git_{pair}_{year}"
    if not repo.exists():
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        _git(repo, "config", "gc.auto", "0")
        _git(repo, "remote", "add", "origin", f"https://github.com/FX-Data/FX-Data-{pair}-DS")
    _git(repo, "fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", f"{pair}-{year}")
    (work / f"{pair}_{year}.commit").write_text(_git(repo, "rev-parse", "FETCH_HEAD").strip() + "\n")
    files = [f for f in _git(repo, "ls-tree", "-r", "--name-only", "FETCH_HEAD").split() if f.endswith("_ticks.csv")]
    parts = []
    for m in sorted({"/".join(f.split("/")[:3]) for f in files}):
        for attempt in range(3):
            try:
                _git(repo, "-c", "checkout.workers=4", "checkout", "-q", "FETCH_HEAD", "--", m)
                break
            except subprocess.CalledProcessError:
                if attempt == 2:
                    raise
        buf = io.BytesIO()
        for f in sorted(glob.glob(str(repo / m / "*_ticks.csv"))):
            b = Path(f).read_bytes()
            buf.write(b if (not b or b.endswith(b"\n")) else b + b"\n")
        buf.seek(0)
        t = pd.read_csv(buf, header=None, names=["t", "bid", "ask", "vb", "va"])
        t["t"] = pd.to_datetime(t["t"], format="%Y.%m.%d %H:%M:%S.%f", utc=True)
        t = t.set_index("t").sort_index()
        mid = (t.bid + t.ask) / 2
        r = mid.resample("1min").ohlc()
        r["volume"] = mid.resample("1min").count()
        r["spread"] = (t.ask - t.bid).resample("1min").mean()
        parts.append(r[r.volume > 0])
        print(pair, year, m, len(t), "ticks", flush=True)
        shutil.rmtree(repo / m.split("/")[0], ignore_errors=True)
    df = pd.concat(parts)
    df.index.name = "time"
    df.to_csv(out, float_format="%.6g")
    shutil.rmtree(repo)
    return out


def fxdata(pair: str, work: str, years: str):
    w = Path(work)
    w.mkdir(parents=True, exist_ok=True)
    y0, y1 = (int(x) for x in years.split("-"))
    ys = list(range(y0, y1 + 1))
    with ThreadPoolExecutor(4) as ex:
        paths = list(ex.map(lambda y: fx_year(pair, y, w), ys))
    (w / f"{pair}_sources.json").write_text(json.dumps(
        {str(y): (w / f"{pair}_{y}.commit").read_text().strip() for y in ys if (w / f"{pair}_{y}.commit").exists()}, indent=1))
    m = pd.concat(pd.read_csv(p, index_col=0, parse_dates=True) for p in paths).sort_index()
    m = m[~m.index.duplicated()]
    OUT.mkdir(parents=True, exist_ok=True)
    for tf, rule in RULES.items():
        if tf == "D1":
            # domingo (abertura ~22h UTC) entra no candle de segunda
            key = m.index.normalize() + pd.to_timedelta((m.index.dayofweek == 6).astype(int), unit="D")
            r = m.groupby(key).agg(AGG)
            r.index.name = "time"
        else:
            r = m.resample(rule).agg(AGG).dropna()
        r = r[r.volume > 0]
        r.to_csv(OUT / f"{pair}_{tf}.csv.gz")
        print(tf, len(r), r.index.min(), r.index.max())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bitstamp", help="clone do ff137/bitstamp-btcusd-minute-data (gera BTCUSD)")
    ap.add_argument("--fxdata", help="par do FX-Data/FX-Data-<PAR>-DS, ex.: EURUSD")
    ap.add_argument("--work", help="pasta de trabalho para os M1 anuais do --fxdata")
    ap.add_argument("--years", default="2009-2022", help="anos do --fxdata, ex.: 2009-2022")
    a = ap.parse_args()
    if not (a.bitstamp or a.fxdata):
        ap.error("informe --bitstamp e/ou --fxdata")
    if a.bitstamp:
        bitstamp(a.bitstamp)
    if a.fxdata:
        if not a.work:
            ap.error("--fxdata exige --work")
        fxdata(a.fxdata.upper(), a.work, a.years)


if __name__ == "__main__":
    main()
