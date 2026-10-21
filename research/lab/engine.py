"""Motor de backtest do laboratório. Sem corretora, sem ordens: só candles fechados.

Regras fixas para todas as estratégias:
- decisão no fechamento do candle i, entrada na abertura do candle i+1;
- stop e alvo observados de forma conservadora (se os dois forem tocados no mesmo candle, conta o stop);
- gap além do stop/alvo sai no preço de abertura (pior caso realista);
- saída por sinal ou por tempo acontece na abertura do candle seguinte;
- uma posição por vez; sinal oposto fecha e inverte na mesma abertura;
- custo por lado em fração do preço (taxa + slippage), cobrado na entrada e na saída.
Resultado de cada operação em R (múltiplos do risco inicial = distância do stop).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class Trade:
    entry_time: str
    exit_time: str
    side: int
    entry: float
    exit: float
    stop: float
    r: float
    bars: int
    reason: str


def atr(df: pd.DataFrame, n: int = 14) -> np.ndarray:
    h, l, c = df.high.values, df.low.values, df.close.values
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    out = np.full(len(c), np.nan)
    if len(c) <= n:
        return out
    out[n] = np.nanmean(tr[1 : n + 1])
    for i in range(n + 1, len(c)):  # Wilder
        out[i] = (out[i - 1] * (n - 1) + tr[i]) / n
    return out


def run(df: pd.DataFrame, sig: dict, cost_side: float, start=None, end=None) -> list[Trade]:
    """sig: entry (int8 +1/-1/0), stop (distância de preço >0), opcionais:
    target_r (float), target (array de distância), exit_long/exit_short (bool), max_hold (int), trail (array de distância para stop móvel).
    start/end limitam o período: entradas só dentro dele e posição aberta é fechada na abertura do primeiro candle após o fim."""
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    t = df.index
    n = len(c)
    entry = np.asarray(sig["entry"], dtype=np.int8)
    stopd = np.asarray(sig["stop"], dtype=float)
    tgt = sig.get("target")
    tgt = None if tgt is None else np.asarray(tgt, dtype=float)
    target_r = sig.get("target_r")
    exl = sig.get("exit_long")
    exs = sig.get("exit_short")
    trail = sig.get("trail")
    max_hold = sig.get("max_hold")
    i0 = 0 if start is None else int(t.searchsorted(pd.Timestamp(start, tz=t.tz)))
    i1 = n if end is None else int(t.searchsorted(pd.Timestamp(end, tz=t.tz)))

    trades: list[Trade] = []
    pos = 0
    i = max(i0, 1)
    pending = 0  # direção a abrir na abertura do candle i
    pend_stop = pend_tgt = 0.0
    ep = sp = tp = risk = 0.0
    ei = 0

    def close_at(j, price, reason):
        nonlocal pos
        gross = (price - ep) * pos
        cost = (ep + price) * cost_side
        trades.append(Trade(str(t[ei]), str(t[j]), pos, ep, price, sp, (gross - cost) / risk, j - ei, reason))
        pos = 0

    while i < n:
        # 0) fim do período: fecha na abertura, sem usar preços do período seguinte
        if i >= i1:
            if pos:
                close_at(i, o[i], "fim_periodo")
            break
        # 1) abre posição pendente na abertura
        if pending and pos == 0:
            if i - 1 < i1:
                pos = pending
                ep = o[i]
                risk = pend_stop
                sp = ep - pos * risk
                tp = ep + pos * pend_tgt if pend_tgt > 0 else math.nan
                ei = i
            pending = 0
        # 2) gerencia posição dentro do candle i
        if pos:
            hit = None
            if pos > 0:
                if o[i] <= sp:
                    hit = (o[i], "stop")
                elif l[i] <= sp:
                    hit = (sp, "stop")
                elif not math.isnan(tp) and o[i] >= tp and i > ei:
                    hit = (o[i], "alvo")
                elif not math.isnan(tp) and h[i] >= tp:
                    hit = (tp, "alvo")
            else:
                if o[i] >= sp:
                    hit = (o[i], "stop")
                elif h[i] >= sp:
                    hit = (sp, "stop")
                elif not math.isnan(tp) and o[i] <= tp and i > ei:
                    hit = (o[i], "alvo")
                elif not math.isnan(tp) and l[i] <= tp:
                    hit = (tp, "alvo")
            if hit:
                close_at(i, hit[0], hit[1])
            elif trail is not None and not math.isnan(trail[i]):
                ns = c[i] - pos * trail[i]
                sp = max(sp, ns) if pos > 0 else min(sp, ns)
        # 3) decisões no fechamento do candle i (valem para a abertura de i+1)
        if i + 1 >= n:
            break
        if pos:
            want_exit = (pos > 0 and exl is not None and exl[i]) or (pos < 0 and exs is not None and exs[i])
            timed = max_hold is not None and (i + 1 - ei) >= max_hold
            flip = entry[i] == -pos and i < i1
            if want_exit or timed or flip:
                pos_before = pos
                close_at(i + 1, o[i + 1], "sinal" if want_exit else ("tempo" if timed else "inversao"))
                if flip and stopd[i] > 0 and not math.isnan(stopd[i]):
                    pending = -pos_before
                    pend_stop = stopd[i]
                    pend_tgt = (tgt[i] if tgt is not None else (target_r * stopd[i] if target_r else 0.0))
                i += 1
                continue
        elif entry[i] and i0 <= i < i1 and stopd[i] > 0 and not math.isnan(stopd[i]):
            pending = int(entry[i])
            pend_stop = stopd[i]
            pend_tgt = (tgt[i] if tgt is not None else (target_r * stopd[i] if target_r else 0.0))
            if math.isnan(pend_tgt):
                pend_tgt = 0.0
        i += 1
    if pos:  # fecha no último preço disponível
        close_at(n - 1, c[n - 1], "fim")
    return trades


def metrics(trades: list[Trade], years: float, risk_pct: float = 0.5) -> dict:
    r = np.array([x.r for x in trades], dtype=float)
    if len(r) == 0:
        return {"trades": 0, "netR": 0.0, "pf": None, "winRate": None, "expR": None, "maxDDR": 0.0,
                "sharpeTrade": None, "tStat": None, "tradesPerYear": 0.0, "retPct": 0.0, "maxDDPct": 0.0, "avgBars": None, "semMaiorR": 0.0}
    gp, gl = r[r > 0].sum(), -r[r < 0].sum()
    eq = np.cumsum(r)
    dd = float(np.max(np.maximum.accumulate(np.r_[0, eq])[1:] - eq)) if len(eq) else 0.0
    dd = max(dd, 0.0)
    sd = r.std(ddof=1) if len(r) > 1 else 0.0
    return {
        "trades": int(len(r)),
        "netR": round(float(r.sum()), 2),
        "pf": round(float(gp / gl), 3) if gl > 0 else None,
        "winRate": round(float((r > 0).mean()), 3),
        "expR": round(float(r.mean()), 4),
        "maxDDR": round(dd, 2),
        "sharpeTrade": round(float(r.mean() / sd), 4) if sd > 0 else None,
        "tStat": round(float(r.mean() / sd * math.sqrt(len(r))), 2) if sd > 0 else None,
        "tradesPerYear": round(len(r) / years, 1) if years > 0 else None,
        "retPct": round(float(r.sum() * risk_pct), 2),
        "maxDDPct": round(dd * risk_pct, 2),
        "avgBars": round(float(np.mean([x.bars for x in trades])), 1),
        "semMaiorR": round(float(r.sum() - r.max()), 2),
    }


def curve(trades: list[Trade], points: int = 150) -> list[list]:
    """Curva acumulada em R (data de saída, R acumulado), reduzida para no máximo `points` pontos."""
    if not trades:
        return []
    eq = np.cumsum([t.r for t in trades])
    idx = np.unique(np.linspace(0, len(trades) - 1, min(points, len(trades))).astype(int))
    return [[trades[i].exit_time[:10], round(float(eq[i]), 2)] for i in idx]
