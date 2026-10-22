"""TV65 - N Bar Reversal Detector (LuxAlgo): padrão de reversão de N barras confirmado por fechamento."""
import importlib.util
from pathlib import Path

import numpy as np

import indicators as ind

# reutiliza Supertrend/Donchian/máquina de estados do TV64 (mesmo autor, mesma lógica de confirmação)
_spec = importlib.util.spec_from_file_location("_tv64_helpers", Path(__file__).with_name("TV64_three_bar.py"))
_tv64 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tv64)

META = {
    "id": "TV65_nbar_reversal",
    "name": "N Bar Reversal Detector (LuxAlgo): rompimento da máxima da 1ª barra do padrão",
    "family": "padroes",
    "round": 5,
    "origin": "TradingView comunidade (LuxAlgo)",
    "sources": [
        "https://www.tradingview.com/script/efR5fu0R-N-Bar-Reversal-Detector-LuxAlgo/",
        "https://www.luxalgo.com/library/indicator/n-bar-reversal-detector/",
        "https://github.com/deepentropy/lightweight-charts-indicators (src/community/n-bar-reversal-detector.ts, port fiel do Pine, commit f8e1b0e)",
    ],
    "rule": ("Pine LuxAlgo (minBars 50%, tipo 'All'): no candle i, a barra de referência é i-N; percorre as barras i-1..i-N+1 enquanto "
             "nenhuma tiver máxima acima da máxima de i-N, contando as de baixa; padrão de alta se (barras de baixa)/(N-1) >= 50% e "
             "a máxima de i passa a máxima de i-N (e não havia padrão no candle anterior); linha de falha = menor mínima do trecho "
             "(com i). Espelho para baixa. Filtro opcional 'Aligned' do script: Supertrend(10, 3) ou Donchian(13). O padrão fica aberto "
             "até um fechamento acima da máxima de i-N (confirmação = compra) ou abaixo da linha de falha, ou padrão oposto. "
             "Decisão no fechamento que confirma (o indicador marca 1 candle depois com close[1]), entrada na abertura seguinte. "
             "Sem saída no indicador: stop na linha de falha (mínimo 0,25*ATR14), alvo tr*R, confirmação oposta fecha/inverte."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"nbars": [4, 7, 10], "trend": ["none", "st", "dc"], "tr": [1.0, 1.5, 2.0, 3.0], "side": ["long", "both"]},
}


def detect(o, h, l, c, N, upok, dnok):
    m = len(c)
    bull = np.zeros(m, bool)
    bear = np.zeros(m, bool)
    bl = np.full(m, np.nan)
    bh = np.full(m, np.nan)
    for i in range(N, m):
        hN, lN = h[i - N], l[i - N]
        low_, cnt = lN, 0
        for k in range(1, N):
            if h[i - k] > hN:
                break
            low_ = min(low_, l[i - k])
            if o[i - k] > c[i - k]:
                cnt += 1
        bl[i] = min(low_, l[i])
        bull[i] = cnt / (N - 1) >= 0.5 and h[i] > hN and upok[i]
        high_, cnt = hN, 0
        for k in range(1, N):
            if l[i - k] < lN:
                break
            high_ = max(high_, h[i - k])
            if o[i - k] < c[i - k]:
                cnt += 1
        bh[i] = max(high_, h[i])
        bear[i] = cnt / (N - 1) >= 0.5 and l[i] < lN and dnok[i]
    newbull = bull & ~np.r_[False, bull[:-1]]
    newbear = bear & ~np.r_[False, bear[:-1]]
    return bull, bear, newbull, newbear, bl, bh


def signals(df, p):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    N = p["nbars"]
    upok, dnok = _tv64.trend_ok(df, p["trend"])
    bull, bear, nb, ns, bl, bh = detect(o, h, l, c, N, upok, dnok)
    hN, lN = ind.prev(h, N), ind.prev(l, N)
    # padrão oposto (bruto) cancela; padrão novo (sem padrão no candle anterior) abre
    m = len(c)
    buy = np.zeros(m, bool)
    sell = np.zeros(m, bool)
    slv = np.full(m, np.nan)
    ba = sa = False
    blv = bex = slv_ = sex = np.nan
    for i in range(m):
        if nb[i]:
            ba, blv, bex = True, hN[i], bl[i]
        if ns[i]:
            sa, slv_, sex = True, lN[i], bh[i]
        if bear[i]:
            ba = False
        if bull[i]:
            sa = False
        if ba:
            if c[i] > blv:
                buy[i], slv[i], ba = True, bex, False
            elif c[i] < bex:
                ba = False
        if sa:
            if c[i] < slv_:
                sell[i], slv[i], sa = True, sex, False
            elif c[i] > sex:
                sa = False
    a = ind.atr(df, 14)
    dist = np.where(buy, c - slv, np.where(sell, slv - c, np.nan))
    stop = np.fmax(dist, 0.25 * a)
    entry = np.where(buy, 1, np.where(sell, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": stop, "target_r": p["tr"], "exit_long": sell, "exit_short": buy}
