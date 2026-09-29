"""Pure N11 signal generation; no downloads, fills, PnL, or future features.

Inputs use UTC epoch *seconds*. ``perp[symbol]`` contains H1 bars with ``time``
(bar open), ``open``, ``high``, ``low`` and ``close``. ``oi[symbol]`` contains
point snapshots with hourly-aligned ``observation_end`` and ``sum_open_interest``
(quantity, not quote value); prospectively each row must also have
``received_at`` in UTC epoch seconds; prospectively H1 bars also require
``received_at`` after the bar ends. A loader must first confirm the timezone
and period semantics of the source's textual create_time, align the statistical
endpoint (archive slot start +300s in the audited sample), and retain hashes.
Missing, duplicate, nonfinite or nonpositive required observations fail closed.

``historical_assumption=True`` permits missing received_at solely for an
exploratory historical screen; it assumes availability by decision time and
does not establish point-in-time validity. An explicitly late/invalid receipt
never passes. The executor handles one open position and entry-bar availability.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation


HOUR = 3600
DECISION_DELAY = 3300
ASSETS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
THRESHOLD = Decimal("-0.005")


def _number(value: object) -> Decimal | None:
    if isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return number if number.is_finite() else None


def _timestamp(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _bar(row: dict, historical_assumption: bool) -> dict | None:
    when = _timestamp(row.get("time"))
    if when is None or when % HOUR:
        return None
    prices = {field: _number(row.get(field)) for field in ("open", "high", "low", "close")}
    if any(price is None or price <= 0 for price in prices.values()):
        return None
    if prices["low"] > min(prices["open"], prices["close"]) or prices["high"] < max(prices["open"], prices["close"]):
        return None
    received = row.get("received_at")
    if received is None:
        if not historical_assumption:
            return None
    else:
        received = _timestamp(received)
        if received is None or received < when + HOUR:
            return None
    return {"time": when, **prices, "received_at": received}


def _snapshot(row: dict, historical_assumption: bool) -> dict | None:
    when = _timestamp(row.get("observation_end"))
    quantity = _number(row.get("sum_open_interest"))
    if when is None or when % HOUR or quantity is None or quantity <= 0:
        return None
    received = row.get("received_at")
    if received is None:
        if not historical_assumption:
            return None
    else:
        received = _timestamp(received)
        if received is None or received < when:
            return None
    return {"observation_end": when, "quantity": quantity, "received_at": received}


def _index(rows: object, timestamp: str, cleaner, *cleaner_args) -> dict[int, dict]:
    if not isinstance(rows, list):
        return {}
    indexed: dict[int, dict] = {}
    seen: set[int] = set()
    duplicates: set[int] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        when = _timestamp(row.get(timestamp))
        if when is not None:
            if when in seen:
                duplicates.add(when)
            seen.add(when)
        clean = cleaner(row, *cleaner_args)
        if clean is not None and when not in duplicates:
            indexed[when] = clean
    for when in duplicates:
        indexed.pop(when, None)
    return indexed


def _available(snapshot: dict, decision_time: int) -> bool:
    received = snapshot["received_at"]
    return received is None or received <= decision_time


def generate_signals(
    perp: dict[str, list[dict]], oi: dict[str, list[dict]], historical_assumption: bool = False
) -> dict[str, dict[int, dict]]:
    """Map feature-end T to a candidate entered at T+3600, after T+3300 decision.

    Keys are UTC epoch seconds. The required feature bar has ``time=T-3600``;
    OI points have exactly ``observation_end=T-3600`` and ``observation_end=T``. Signal
    ``signal_close_time=T+3600`` matches the frozen executor's next-open key
    convention. No entry price or next-hour return is read here.
    """
    if not isinstance(perp, dict) or not isinstance(oi, dict):
        return {"N11": {}}
    bars = {asset: _index(perp.get(asset), "time", _bar, historical_assumption) for asset in ASSETS}
    points = {asset: _index(oi.get(asset), "observation_end", _snapshot, historical_assumption)
              for asset in ASSETS}
    result: dict[int, dict] = {}
    feature_ends = sorted({bar_open + HOUR for asset in ASSETS for bar_open in bars[asset]})
    for end in feature_ends:
        decision_time = end + DECISION_DELAY
        for asset in ASSETS:
            bar = bars[asset].get(end - HOUR)
            previous = points[asset].get(end - HOUR)
            current = points[asset].get(end)
            if bar is None or previous is None or current is None:
                continue
            if (not _available(bar, decision_time) or not _available(previous, decision_time)
                    or not _available(current, decision_time)):
                continue
            oi_change = current["quantity"] / previous["quantity"] - 1
            price_change = bar["close"] / bar["open"] - 1
            if oi_change <= THRESHOLD and price_change <= THRESHOLD:
                result[end] = {
                    "symbol": asset,
                    "direction": 1,
                    "stop_pct": 0.015,
                    "hold_hours": 4,
                    "signal_close_time": end + HOUR,
                    "feature_end": end,
                    "decision_time": decision_time,
                    "availability_mode": "assumed_historical" if historical_assumption else "observed_receipt",
                    "reason": "oi_quantity_contraction_price_shock_recovery",
                }
                break
    return {"N11": result}
