"""Pure preregistered N5/N6 signals; no fills, costs, PnL, or future reads."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from statistics import median


HOUR = 3600
ASSETS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
N5_MIN_IMBALANCE = Decimal("0.20")
N5_MAX_ABS_RETURN = Decimal("0.0025")
N6_MIN_BTC_RETURN = Decimal("0.0075")
N6_MAX_ABS_FOLLOWER_RETURN = Decimal("0.002")


def _number(value: object) -> Decimal | None:
    if isinstance(value, bool):
        return None
    try:
        out = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return out if out.is_finite() else None


def _clean_bar(row: dict) -> dict | None:
    if not isinstance(row, dict):
        return None
    when = row.get("time")
    if isinstance(when, bool) or not isinstance(when, int) or when % HOUR:
        return None
    fields = {key: _number(row.get(key)) for key in (
        "open", "high", "low", "close", "quote_volume", "taker_buy_quote_volume"
    )}
    if any(value is None for value in fields.values()):
        return None
    op, hi, lo, cl = (fields[key] for key in ("open", "high", "low", "close"))
    volume = fields["quote_volume"]
    taker = fields["taker_buy_quote_volume"]
    if (op <= 0 or lo <= 0 or cl <= 0 or hi < max(op, cl) or
            lo > min(op, cl) or volume <= 0 or taker < 0 or taker > volume):
        return None
    return {"time": when, **fields}


def _indexed(rows: list[dict]) -> dict[int, dict]:
    result: dict[int, dict] = {}
    duplicates: set[int] = set()
    seen: set[int] = set()
    for row in rows:
        when = row.get("time") if isinstance(row, dict) else None
        if isinstance(when, int) and not isinstance(when, bool) and when % HOUR == 0:
            if when in seen:
                duplicates.add(when)
            seen.add(when)
        clean = _clean_bar(row)
        if clean is None:
            continue
        if when not in duplicates:
            result[when] = clean
    for when in duplicates:
        result.pop(when)
    return result


def _return(bar: dict) -> Decimal:
    return bar["close"] / bar["open"] - 1


def _signal(symbol: str, stop_pct: float, time: int, reason: str) -> dict:
    return {
        "symbol": symbol,
        "direction": 1,
        "stop_pct": stop_pct,
        "hold_hours": 2,
        "signal_close_time": time + HOUR,
        "reason": reason,
    }


def generate_signals(spot: dict[str, list[dict]]) -> dict[str, dict[int, dict]]:
    """Return signal maps keyed by the completed spot H1 candle's open epoch second.

    The executor, not this function, enforces one open position per family and
    validates the following perpetual-futures entry/exit observations.
    """
    bars = {asset: _indexed(spot.get(asset, [])) for asset in ASSETS}
    result: dict[str, dict[int, dict]] = {"N5": {}, "N6": {}}
    times = sorted(set().union(*(set(one) for one in bars.values())))
    for when in times:
        for asset in ASSETS:
            current = bars[asset].get(when)
            if current is None or not -N5_MAX_ABS_RETURN <= _return(current) <= N5_MAX_ABS_RETURN:
                continue
            previous = [bars[asset].get(when - offset * HOUR) for offset in range(1, 25)]
            if any(prior is None for prior in previous):
                continue
            if current["quote_volume"] < median(prior["quote_volume"] for prior in previous):
                continue
            imbalance = 2 * current["taker_buy_quote_volume"] / current["quote_volume"] - 1
            if imbalance >= N5_MIN_IMBALANCE:
                result["N5"][when] = _signal(asset, 0.01, when, "taker_buy_pressure_continuation")
                break
        leader = bars["BTCUSDT"].get(when)
        if leader is None or _return(leader) < N6_MIN_BTC_RETURN:
            continue
        for asset in ("ETHUSDT", "SOLUSDT"):
            follower = bars[asset].get(when)
            if follower is not None and -N6_MAX_ABS_FOLLOWER_RETURN <= _return(follower) <= N6_MAX_ABS_FOLLOWER_RETURN:
                result["N6"][when] = _signal(asset, 0.015, when, "btc_leads_altcoin")
                break
    return result
