"""TV32 - Machine Learning: Lorentzian Classification (jdehorty), versão causal sem olhar o futuro."""
import numpy as np
import pandas as pd

import indicators as ind

META = {
    "id": "TV32_lorentzian",
    "name": "Machine Learning: Lorentzian Classification (jdehorty), kNN causal",
    "family": "aprendizado",
    "round": 3,
    "origin": "TradingView comunidade (jdehorty)",
    "sources": [
        "https://www.tradingview.com/script/WhBzgfDu-Machine-Learning-Lorentzian-Classification/",
        "https://pypi.org/project/advanced-ta/0.1.7/ (porte Python do Pine; código lido no pacote baixado)",
    ],
    "rule": ("Atributos do Pine (padrões): RSI(14), WaveTrend(hlc3,10,11), CCI(fech,20), ADX(20), RSI(9); RSI/ADX reescalados "
             "para 0-1 e WT/CCI normalizados pelo mínimo/máximo histórico ACUMULADO (como o Pine; o porte Python usa o mínimo/máximo "
             "da amostra inteira, que olha o futuro, e não foi copiado). Distância Lorentziana d=Σ log(1+|f_t-f_j|). "
             "Para cada candle t procura os k vizinhos mais próximos entre candles passados j da janela de L candles, espaçados de 4 "
             "em 4 (o Pine também espaça os vizinhos 4 candles). Rótulo 'futuro' (pedido: versão causal do propósito do autor): "
             "sinal de fech[j+4]-fech[j], usado só quando j+4<=t (já fechado). Rótulo 'pine': reprodução literal do pareamento do "
             "script (y = curto se fech[j-4]<fech[j], longo se maior), que também é causal mas na prática é reversão dos últimos 4 "
             "candles. Previsão = soma dos rótulos dos k vizinhos (kNN exato em vez da busca aproximada do Pine). Filtros padrão: "
             "volatilidade ATR(1)>ATR(10) e regime (inclinação do filtro de Kalman KLMF >= -0,1 da média de 200); sinal = +1 se "
             "previsão>0 e filtros, -1 se <0 e filtros, senão mantém. Compra quando o sinal vira +1 e o kernel de regressão "
             "racional-quadrático (h=8, r=8, x=25, só candles passados, sem repintura) está subindo; venda no espelho (side=both). "
             "Saída 'fixo4' = padrão do Pine: 4 candles ou sinal oposto novo antes disso; 'dinamico' = virada do kernel. "
             "Stop de proteção k*ATR14 (o script não tem stop)."),
    "timeframes": ["H1", "H4", "D1"],
    "grid": {"nn": [4, 8, 12], "L": [1000, 2000], "label": ["futuro", "pine"], "exit": ["fixo4", "dinamico"],
             "k": [2.0, 3.0], "side": ["long", "both"]},
}


def _norm_hist(x):
    """normalize() do MLExtensions: (x - mín histórico) / (máx - mín) usando só o passado."""
    x = np.asarray(x, float)
    lo = np.fmin.accumulate(np.where(np.isnan(x), np.inf, x))
    hi = np.fmax.accumulate(np.where(np.isnan(x), -np.inf, x))
    with np.errstate(invalid="ignore", divide="ignore"):
        return (x - lo) / np.maximum(hi - lo, 1e-9)


def _cci(x, n):
    s = pd.Series(x)
    ma = s.rolling(n).mean()
    md = s.rolling(n).apply(lambda v: np.mean(np.abs(v - v.mean())), raw=True)
    return ((s - ma) / (0.015 * md)).values


def _rma(x, n):
    return pd.Series(x).ewm(alpha=1 / n, adjust=False, min_periods=n).mean().to_numpy()


def _n_adx(h, l, c, n):
    ph, pl, pc = np.r_[h[0], h[:-1]], np.r_[l[0], l[:-1]], np.r_[c[0], c[:-1]]
    tr = np.maximum(np.maximum(h - l, np.abs(h - pc)), np.abs(l - pc))
    up, dn = h - ph, pl - l
    dmp = np.where(up > dn, np.maximum(up, 0), 0.0)
    dmm = np.where(dn > up, np.maximum(dn, 0), 0.0)
    trs, sp, sm = np.zeros(len(c)), np.zeros(len(c)), np.zeros(len(c))
    a = b = d = 0.0
    for i in range(len(c)):
        a = a - a / n + tr[i]
        b = b - b / n + dmp[i]
        d = d - d / n + dmm[i]
        trs[i], sp[i], sm[i] = a, b, d
    with np.errstate(invalid="ignore", divide="ignore"):
        dip, dim = sp / trs * 100, sm / trs * 100
        dx = np.abs(dip - dim) / (dip + dim) * 100
    return _rma(np.nan_to_num(dx), n) / 100.0


def features(df):
    h, l, c = df.high.values, df.low.values, df.close.values
    hlc3 = (h + l + c) / 3
    e1 = ind.ema(hlc3, 10)
    e2 = ind.ema(np.abs(hlc3 - e1), 10)
    with np.errstate(invalid="ignore", divide="ignore"):
        ci = (hlc3 - e1) / (0.015 * e2)
    wt1 = ind.ema(ci, 11)
    wt2 = ind.sma(wt1, 4)
    f = np.c_[ind.rsi(c, 14) / 100, _norm_hist(wt1 - wt2), _norm_hist(_cci(c, 20)), _n_adx(h, l, c, 20), ind.rsi(c, 9) / 100]
    return f


def knn_pred(F, c, L, label, nns):
    n = len(c)
    out = {k: np.zeros(n) for k in nns}
    kmax = max(nns)
    ok = ~np.isnan(F).any(axis=1)
    if label == "futuro":
        y = np.zeros(n)
        y[:-4] = np.sign(c[4:] - c[:-4])  # y[j] só é usado quando j+4 <= t
        lag0 = 4
    else:
        y = np.zeros(n)
        y[4:] = np.sign(c[4:] - c[:-4]) * -1  # Pine: curto se fech[j-4] < fech[j]
        lag0 = 1
    first = np.argmax(ok) + 50
    for t in range(first, n):
        if not ok[t]:
            continue
        js = np.arange(t - lag0, max(first - 50, t - L) - 1, -4)
        js = js[ok[js]] if len(js) else js
        if len(js) < kmax:
            continue
        d = np.log1p(np.abs(F[js] - F[t])).sum(axis=1)
        part = np.argpartition(d, kmax - 1)[:kmax]
        order = part[np.argsort(d[part], kind="stable")]
        yy = y[js[order]]
        cs = np.cumsum(yy)
        for k in nns:
            out[k][t] = cs[k - 1]
    return out


def filters(df):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    vol = _rma(tr, 1) > _rma(tr, 10)
    src = (o + h + l + c) / 4
    v1 = v2 = kl = 0.0
    klmf = np.zeros(len(c))
    for i in range(len(c)):
        v1 = 0.2 * (src[i] - (src[i - 1] if i else src[i])) + 0.8 * v1
        v2 = 0.1 * (h[i] - l[i]) + 0.8 * v2
        om = abs(v1 / v2) if v2 else 0.0
        al = (-om ** 2 + np.sqrt(om ** 4 + 16 * om ** 2)) / 8
        kl = al * src[i] + (1 - al) * kl
        klmf[i] = kl
    slope = np.abs(np.diff(klmf, prepend=klmf[0]))
    ea = ind.ema(slope, 200)
    with np.errstate(invalid="ignore", divide="ignore"):
        reg = (slope - ea) / ea >= -0.1
    return vol & reg


def kernel_rq(c, h=8, r=8.0, x=25):
    out = np.zeros(len(c))
    tot = 0.0
    for i in range(x + 2):
        w = (1 + i ** 2 / (h ** 2 * 2 * r)) ** -r
        out += ind.prev(c, i) * w if i else c * w
        tot += w
    return out / tot


_cache = {}


def signals(df, p):
    base = (id(df), len(df))
    if base not in _cache:
        _cache[base] = {"F": features(df), "flt": filters(df), "yhat": kernel_rq(df.close.values)}
    C = _cache[base]
    kk = (p["L"], p["label"])
    if kk not in C:
        C[kk] = knn_pred(C["F"], df.close.values, p["L"], p["label"], META["grid"]["nn"])
    pred = C[kk][p["nn"]]
    flt = C["flt"]
    n = len(pred)
    sig = np.zeros(n)
    s = 0.0
    for i in range(n):
        if pred[i] > 0 and flt[i]:
            s = 1.0
        elif pred[i] < 0 and flt[i]:
            s = -1.0
        sig[i] = s
    chg = sig != np.r_[0.0, sig[:-1]]
    new_buy, new_sell = (sig == 1) & chg, (sig == -1) & chg
    yh = C["yhat"]
    yp = ind.prev(yh)
    bull, bear = yh > yp, yh < yp
    lg, sh = new_buy & bull, new_sell & bear
    entry = np.where(lg, 1, np.where(sh, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    out = {"entry": entry, "stop": p["k"] * ind.atr(df, 14)}
    if p["exit"] == "fixo4":
        out["max_hold"] = 4
        out["exit_long"], out["exit_short"] = new_sell, new_buy
    else:
        ypp = ind.prev(yh, 2)
        was_bull, was_bear = yp > ypp, yp < ypp
        out["exit_long"], out["exit_short"] = bear & was_bull, bull & was_bear
    return out
