"""L20 r1 - Reversão ao VWAP só com recuperação da banda e a favor da tendência."""
import numpy as np

import indicators as ind
from importlib import util as _u
from pathlib import Path as _P

_spec = _u.spec_from_file_location("_l20base", _P(__file__).with_name("L20_vwap_reversion.py"))
_base = _u.module_from_spec(_spec)
_spec.loader.exec_module(_base)

META = {
    "id": "L20_vwap_reversion_r1",
    "refines": "L20_vwap_reversion",
    "refinement": ("No desenvolvimento a versão simples perdia até sem custo: o BTC continua andando além da banda do VWAP "
                   "(tendência intradiária). Duas mudanças: entrada só quando o preço fecha de volta para dentro da banda "
                   "(regra de 'reclaim' do script Institutional VWAP Bands) e só a favor da tendência (compra acima da "
                   "EMA200, venda abaixo)."),
    "name": "Reversão ao VWAP com recuperação da banda e tendência",
    "family": "tempo_volume",
    "sources": _base.META["sources"],
    "rule": ("Banda = VWAP (dia UTC ou rolante 24h) +- d*ATR14. Compra quando o candle anterior fechou abaixo da banda "
             "inferior e o atual fecha de volta acima dela, com fechamento acima da EMA200; venda no espelho abaixo da "
             "EMA200. Alvo: VWAP; stop k*ATR14; saída por tempo em 24h. Volume só do Bitstamp."),
    "timeframes": ["M15", "H1"],
    "grid": _base.META["grid"],
}


def signals(df, p):
    c = df.close.values
    vw, per_day = _base.vwap(df, p["anchor"])
    a = ind.atr(df, 14)
    lo = vw - p["d"] * a
    hi = vw + p["d"] * a
    up = (ind.prev(c) < ind.prev(lo)) & (c > lo) & (c < vw)
    dn = (ind.prev(c) > ind.prev(hi)) & (c < hi) & (c > vw)
    t = ind.ema(c, 200)
    up &= c > t
    dn &= c < t
    entry = np.where(up, 1, np.where(dn, -1, 0))
    if p["side"] == "long":
        entry = np.where(entry > 0, 1, 0)
    return {"entry": entry, "stop": p["k"] * a, "exit_long": c >= vw, "exit_short": c <= vw, "max_hold": per_day}
