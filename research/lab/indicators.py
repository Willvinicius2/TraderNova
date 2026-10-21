"""Indicadores causais (o valor em i usa só dados até i)."""
import numpy as np
import pandas as pd

from engine import atr  # noqa: F401  (Wilder)


def sma(x, n):
    return pd.Series(x).rolling(n).mean().values


def ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False, min_periods=n).mean().values


def rsi(x, n=14):
    d = pd.Series(x).diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return (100 - 100 / (1 + up / dn)).values


def stdev(x, n):
    return pd.Series(x).rolling(n).std(ddof=0).values


def highest(x, n):
    return pd.Series(x).rolling(n).max().values


def lowest(x, n):
    return pd.Series(x).rolling(n).min().values


def prev(x, k=1):
    out = np.full(len(x), np.nan)
    out[k:] = np.asarray(x, dtype=float)[:-k]
    return out


def cross_above(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return (a > b) & (prev(a) <= prev(b))


def cross_below(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return (a < b) & (prev(a) >= prev(b))
