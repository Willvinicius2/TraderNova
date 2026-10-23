"""L33 - Chandelier Exit (Chuck LeBeau) como sistema de parar-e-inverter / stop móvel."""
import numpy as np

import indicators as ind

META = {
    "id": "L33_chandelier",
    "name": "Chandelier Exit (LeBeau) como sistema",
    "family": "tendencia",
    "round": 8,
    "origin": "FILA.md (autor)",
    "sources": [
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/chandelier-exit",
        "https://www.tradingview.com/script/AqXxNS7j-Chandelier-Exit/ (everget; Pine em /home/user/labdata/pine/everget_tradingview-pinescript-indicators e porte em deepentropy .../community/chandelier-exit.ts)",
        "https://corporatefinanceinstitute.com/resources/equities/chandelier-exit/",
    ],
    "rule": ("Chandelier Exit de LeBeau (StockCharts): linha de compra = maior máxima (ou maior fechamento, 'Use Close' do script everget) "
             "de n candles - mult*ATR(n); linha de venda = menor mínima (ou fechamento) de n + mult*ATR(n). Como no Pine everget, as "
             "linhas só apertam enquanto o fechamento anterior está do lado certo, e a direção vira para alta quando o fechamento "
             "passa acima da linha de venda anterior e para baixa quando fecha abaixo da linha de compra anterior. Compra na virada "
             "para alta, vende (side=both) na virada para baixa. exit='flip': sai/inverte só na virada (stop inicial = distância até "
             "a linha do candle de sinal, mínimo 0,5*ATR14); exit='trail': a própria linha Chandelier é o stop móvel (uso original "
             "de LeBeau, stop tocado no intradiário) e não há reentrada até a próxima virada. Diferença do L01 Supertrend: a âncora é "
             "o extremo de n candles (máxima mais alta / mínima mais baixa), não o meio (máx+mín)/2 do candle atual, e a virada "
             "exige cruzar a linha OPOSTA; no modo trail sai pela linha do mesmo lado sem inverter. Diferença do TV10 SAR: distância "
             "fixa em ATR do extremo, sem fator de aceleração que aperta com o tempo."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"n": [11, 22, 44], "mult": [2.0, 3.0, 4.0, 5.0], "src": ["hl", "close"], "exit": ["flip", "trail"],
             "side": ["long", "both"]},
}


def chandelier(df, n, mult, src):
    h, l, c = df.high.values, df.low.values, df.close.values
    a = ind.atr(df, n) * mult
    hi = ind.highest(c if src == "close" else h, n)
    lo = ind.lowest(c if src == "close" else l, n)
    N = len(c)
    ls = np.full(N, np.nan)
    ss = np.full(N, np.nan)
    d = np.zeros(N, dtype=int)
    dirc = 1
    lprev = sprev = np.nan
    for i in range(N):
        lstop = hi[i] - a[i]
        sstop = lo[i] + a[i]
        if np.isnan(lstop):
            d[i] = 0
            continue
        lp = lstop if np.isnan(lprev) else lprev
        sp = sstop if np.isnan(sprev) else sprev
        if i > 0 and c[i - 1] > lp:
            lstop = max(lstop, lp)
        if i > 0 and c[i - 1] < sp:
            sstop = min(sstop, sp)
        if c[i] > sp:
            dirc = 1
        elif c[i] < lp:
            dirc = -1
        d[i] = dirc
        ls[i], ss[i] = lstop, sstop
        lprev, sprev = lstop, sstop
    return ls, ss, d


def signals(df, p):
    c = df.close.values
    ls, ss, d = chandelier(df, p["n"], p["mult"], p["src"])
    pd_ = ind.prev(d.astype(float))
    up = (d == 1) & (pd_ == -1)
    dn = (d == -1) & (pd_ == 1)
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    a14 = ind.atr(df, 14)
    dist = np.where(up, c - ls, np.where(dn, ss - c, np.nan))
    stop = np.maximum(dist, 0.5 * a14)
    out = {"entry": entry, "stop": stop, "exit_long": dn, "exit_short": up}
    if p["exit"] == "trail":
        tr = np.where(d == 1, c - ls, np.where(d == -1, ss - c, np.nan))
        tr[up | dn] = np.nan  # no candle da virada a posição antiga sai na abertura seguinte
        out["trail"] = tr
        # sem inversão automática no trail: a saída é a linha; virada oposta ainda fecha (exit_*) e abre o novo lado
    return out
