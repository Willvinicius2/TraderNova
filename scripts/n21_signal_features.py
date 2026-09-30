"""Pure, fail-closed N21 feature gate. It emits a hypothesis only, never a trade."""
from datetime import datetime
import re
from decimal import Decimal, DecimalException, InvalidOperation, localcontext

BAND = Decimal("0.999")
MIN_DROP = Decimal("0.0005")  # 5 bp
RECOVERY = Decimal("1.25")
MAX_DECIMAL_CHARS = 64
MAX_LEVELS = 10000


class FeatureError(ValueError):
    pass


def _dec(value, name):
    if isinstance(value, bool):
        raise FeatureError(f"invalid_{name}")
    text = str(value)
    if len(text) > MAX_DECIMAL_CHARS:
        raise FeatureError(f"oversize_{name}")
    try:
        number = Decimal(text)
    except (InvalidOperation, ValueError):
        raise FeatureError(f"invalid_{name}")
    if not number.is_finite():
        raise FeatureError(f"nonfinite_{name}")
    if not re.fullmatch(r'-?\d+(?:\.\d+)?', text):
        raise FeatureError(f'invalid_representation_{name}')
    return number


def _time(value):
    if not isinstance(value, str) or len(value) > 64:
        raise FeatureError("invalid_timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise FeatureError("invalid_timestamp")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise FeatureError("naive_timestamp")
    return parsed


def _seconds(later, earlier):
    delta = later - earlier
    return Decimal(delta.days * 86400 + delta.seconds) + Decimal(delta.microseconds) / Decimal(1000000)


def _sequence(state):
    value = state.get("sequence_marker")
    if value is None:
        seq = state.get("sequence")
        value = seq.get("u") if isinstance(seq, dict) else None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise FeatureError("invalid_sequence")
    return value


def _levels(state):
    rows = state.get("bid_levels")
    if not isinstance(rows, list) or not rows or len(rows) > MAX_LEVELS:
        raise FeatureError("missing_or_oversize_bid_levels")
    parsed, seen = [], set()
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) != 2:
            raise FeatureError("invalid_bid_level")
        price, qty = _dec(row[0], "price"), _dec(row[1], "quantity")
        if price <= 0 or qty < 0 or price in seen:
            raise FeatureError("invalid_or_duplicate_bid_level")
        seen.add(price)
        parsed.append((price, qty))
    return parsed


def _state(state):
    if not isinstance(state, dict):
        raise FeatureError("missing_bookstate")
    if state.get("utc_verified") is not True:
        raise FeatureError("utc_unverified")
    age = _dec(state.get("event_age_s"), "event_age")
    if age < 0 or age > 1:
        raise FeatureError("event_stale_or_future")
    source, connection = state.get("source"), state.get("connection_id")
    if not isinstance(source, str) or not source or not isinstance(connection, str) or not connection:
        raise FeatureError("source_or_connection_missing")
    if source != 'binance_spot_l2':
        raise FeatureError('unsupported_auxiliary_source')
    ts = _time(state.get("timestamp"))
    mid, bid, ask = (_dec(state.get(k), k) for k in ("mid", "bid", "ask"))
    if mid <= 0 or bid <= 0 or ask <= 0 or bid >= ask or not (bid < mid < ask):
        raise FeatureError("crossed_or_invalid_quote")
    if mid != (bid + ask) / 2:
        raise FeatureError('mid_quote_mismatch')
    lower = _dec(state.get("known_bid_lower_bound"), "known_bid_lower_bound")
    if lower <= 0:
        raise FeatureError("invalid_known_bid_lower_bound")
    levels = _levels(state)
    if max(p for p, _ in levels) != bid:
        raise FeatureError("top_bid_mismatch")
    return {"timestamp": ts, "mid": mid, "bid": bid, "ask": ask, "lower": lower,
            "levels": levels, "source": source, "connection": connection,
            "sequence": _sequence(state)}


def _depth(state, lo, hi):
    if state["lower"] > lo:
        raise FeatureError("band_not_fully_covered")
    return sum((qty for price, qty in state["levels"] if lo <= price <= hi), Decimal(0))


def _blocked(reason):
    return {"status": "blocked", "blocked_reason": reason,
            "source": "Binance_aux", "validated": False, "execution": False,
            "externally_attested": False, "requires_verified_adapter": True, "cooldown_not_enforced": True}


def _evaluate_n21(before, current, confirm, *, continuity_verified=False):
    try:
        states = [_state(before), _state(current), _state(confirm)]
        a, b, c = states
        if len({x["source"] for x in states}) != 1 or len({x["connection"] for x in states}) != 1:
            raise FeatureError("source_or_connection_mismatch")
        if not (a["sequence"] < b["sequence"] < c["sequence"]):
            raise FeatureError("sequence_gap_or_nonmonotonic")
        if _seconds(b["timestamp"], a["timestamp"]) != Decimal("1.0"):
            raise FeatureError("shock_interval_not_exactly_1s")
        if _seconds(c["timestamp"], b["timestamp"]) != Decimal("5.0"):
            raise FeatureError("confirmation_interval_not_exactly_5s")
        if continuity_verified is not True:
            raise FeatureError("continuity_not_verified_by_caller")
        if not isinstance(confirm, dict) or "min_mid_between" not in confirm:
            raise FeatureError("causal_min_mid_missing")
        min_mid = _dec(confirm["min_mid_between"], "min_mid_between")
        if min_mid < b["mid"]:
            raise FeatureError("new_low_during_confirmation")
        if min_mid > min(b['mid'],c['mid']):
            raise FeatureError('inconsistent_interval_minimum')
        if b["mid"] > a["mid"] * (Decimal(1) - MIN_DROP):
            raise FeatureError("drop_below_5bp")
        if b["bid"] >= a["bid"]:
            raise FeatureError("best_bid_did_not_recede")
        if c["mid"] < b["mid"]:
            raise FeatureError("confirmation_mid_below_current")
        lo, hi = a["mid"] * BAND, a["mid"]
        d0, d5 = _depth(a, lo, hi), _depth(c, lo, hi)
        if d0 <= 0:
            raise FeatureError("baseline_depth_not_positive")
        if d5 < RECOVERY * d0:
            raise FeatureError("fixed_band_recovery_below_1_25x")
        return {"status": "hypothesis_signal", "decision_at": confirm["timestamp"],
                "source": "Binance_aux", "evidence_source": a["source"],
                "validated": False, "execution": False,
                "externally_attested": False, "requires_verified_adapter": True, "cooldown_not_enforced": True}
    except FeatureError as exc:
        return _blocked(str(exc))
    except (TypeError, KeyError, OverflowError, DecimalException):
        return _blocked("malformed_input")


def evaluate_n21(before, current, confirm, *, continuity_verified=False):
    """Evaluate exactly three caller-prepared causal states; never reads future arrays."""
    with localcontext() as context:
        context.prec = 256
        return _evaluate_n21(before, current, confirm, continuity_verified=continuity_verified)
