"""Converte os candles H1/H4/D1 do repositório público github.com/ejtraderLabs/historical-data (MT5, 2012–2022)
para research/cache/lab/EJ_<PAR>_<TF>.csv.gz, no formato do laboratório.

  git clone --depth 1 --filter=blob:none --no-checkout https://github.com/ejtraderLabs/historical-data <dir>
  git -C <dir> checkout HEAD -- XAUUSD EURUSD GBPUSD USDJPY AUDUSD USDCAD
  python research/validacao/dados_fx.py <dir>

Atenção: são candles de corretora MT5 com fuso do servidor (UTC+2/+3), não UTC. Servem para teste de robustez em H4/D1,
não para o protocolo oficial do laboratório. Preços vêm em inteiros (pontos); a escala não muda resultado em R nem custo
proporcional ao preço, mas é corrigida mesmo assim.
"""
import sys
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "cache" / "lab"
PAIRS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
SCALE = {"XAUUSD": 100, "USDJPY": 1000}


def main(folder):
    OUT.mkdir(parents=True, exist_ok=True)
    for p in PAIRS:
        for tf in ("h1", "h4", "d1"):
            df = pd.read_csv(Path(folder) / p / f"{p}{tf}.csv")
            df.index = pd.to_datetime(df.Date).dt.tz_localize("UTC")
            df.index.name = "time"
            df = df.rename(columns={"tick_volume": "volume"})[["open", "high", "low", "close", "volume"]].astype(float)
            df[["open", "high", "low", "close"]] /= SCALE.get(p, 100000)
            df = df[~df.index.duplicated()].sort_index()
            df.to_csv(OUT / f"EJ_{p}_{tf.upper()}.csv.gz")
            print(p, tf, len(df), df.index.min(), df.index.max(), round(df.close.iloc[-1], 4))


if __name__ == "__main__":
    main(sys.argv[1])
