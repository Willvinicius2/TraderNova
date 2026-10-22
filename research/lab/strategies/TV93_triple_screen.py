"""TV93 - Elder Triple Screen (Alexander Elder, 1986; Trading for a Living, 1993)."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV93_triple_screen",
    "name": "Elder Triple Screen: MACD do tempo maior + Force Index(2) + rompimento da máxima anterior",
    "family": "tendencia",
    "round": 7,
    "origin": "TradingView comunidade (scripts 'Triple Screen' / 'Elder's Complete Trading System'; regra de Alexander Elder)",
    "sources": [
        "https://www.tradingview.com/scripts/triplescreen/",
        "https://vn.tradingview.com/script/v5aXloyy-Elder-s-Complete-Trading-System",
        "https://www.investopedia.com/terms/t/triplescreen.asp",
    ],
    "sourceNote": "TradingView inacessível pelo WebFetch e sem Pine nos repositórios clonados; regra clássica de Elder (Trading for a Living / "
                  "Come Into My Trading Room). Tela 1 (maré): inclinação do histograma MACD(12,26,9) no tempo gráfico maior, só com candle "
                  "maior FECHADO (o valor do candle maior entra no gráfico menor só depois do fim do período). Tela 2 (onda): EMA(2) do Force "
                  "Index < 0 para comprar (> 0 para vender). Tela 3: ordem stop de compra 1 tick acima da máxima do candle anterior; aqui "
                  "aproximada por fechamento acima da máxima do candle de preparação (FI<0) e entrada na abertura seguinte. Stop de Elder: "
                  "abaixo da menor mínima dos 2 últimos candles (mínimo de 0,5*ATR14 para não ter stop zero).",
    "rule": "Maré de alta: histograma MACD(12,26,9) do tempo maior fechado subiu no último candle maior (maré de baixa: caiu). "
            "Compra: maré de alta, FI2 = EMA(fi) de (fech-fech ant.)*volume < 0 no candle anterior e o fechamento atual passa da máxima do candle anterior. "
            "Venda: espelho (maré de baixa, FI2>0 no anterior, fechamento abaixo da mínima anterior). Stop: menor mínima (maior máxima) dos 2 "
            "últimos candles, mínimo 0,5*ATR. Saída saida='mare': quando a maré vira contra; 'r2'/'r3': alvo 2R/3R (e também sai se a maré virar). "
            "Tempo maior: H1->H4 (htf=1) ou D1 (htf=2); H4->D1 ou semana; D1->semana ou mês.",
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"htf": [1, 2], "fi": [2, 3], "saida": ["mare", "r2", "r3"], "side": ["long", "both"]},
}

_HTF = {"H1": {1: "4h", 2: "1D"}, "H4": {1: "1D", 2: "W"}, "D1": {1: "W", 2: "M"}}
_TFD = {"H1": pd.Timedelta(hours=1), "H4": pd.Timedelta(hours=4), "D1": pd.Timedelta(days=1)}


def _tf_of(df):
    d = pd.Series(df.index[1:200] - df.index[:199]).median()
    return min(_TFD, key=lambda k: abs(_TFD[k] - d))


def htf_tide(df, rule):
    """Inclinação do histograma MACD do tempo maior, alinhada ao candle menor só depois do fechamento do candle maior."""
    t = df.index
    if rule == "W":
        start = (t.normalize() - pd.to_timedelta(t.dayofweek, unit="D"))
        end = start + pd.Timedelta(days=7)
    elif rule == "M":
        start = t.tz_localize(None).to_period("M").start_time.tz_localize("UTC")
        end = (t.tz_localize(None).to_period("M") + 1).start_time.tz_localize("UTC")
    else:
        start = t.floor(rule)
        end = start + pd.Timedelta(rule)
    g = pd.DataFrame({"c": df.close.values, "s": start, "e": end})
    h = g.groupby("s").agg(c=("c", "last"), e=("e", "first"))
    c = h.c.values
    m = ind.ema(c, 12) - ind.ema(c, 26)
    hist = m - ind.ema(m, 9)
    slope = np.sign(hist - ind.prev(hist))
    slope = np.nan_to_num(slope, nan=0.0)
    avail = pd.Series(slope, index=pd.DatetimeIndex(h.e.values).tz_localize(None))
    close_t = (t + _TFD[_tf_of(df)]).tz_localize(None)
    pos = avail.index.searchsorted(close_t, side="right") - 1
    out = np.where(pos >= 0, avail.values[np.clip(pos, 0, None)], 0.0)
    return out


def signals(df, p):
    tf = _tf_of(df)
    tide = htf_tide(df, _HTF[tf][p["htf"]])
    o, h, l, c, v = (df[k].values for k in ("open", "high", "low", "close", "volume"))
    raw = np.r_[0.0, np.diff(c)] * v
    fi = ind.ema(raw, p["fi"])
    pfi, ph, pl = ind.prev(fi), ind.prev(h), ind.prev(l)
    buy = (tide > 0) & (pfi < 0) & (c > ph)
    sell = (tide < 0) & (pfi > 0) & (c < pl)
    a = ind.atr(df, 14)
    lo2 = np.minimum(l, pl)
    hi2 = np.maximum(h, ph)
    sd_long = np.maximum(c - lo2, 0.5 * a)
    sd_short = np.maximum(hi2 - c, 0.5 * a)
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    stop = np.where(entry < 0, sd_short, sd_long)
    sig = {"entry": entry, "stop": stop, "exit_long": tide < 0, "exit_short": tide > 0}
    if p["saida"] == "r2":
        sig["target_r"] = 2.0
    elif p["saida"] == "r3":
        sig["target_r"] = 3.0
    return sig
