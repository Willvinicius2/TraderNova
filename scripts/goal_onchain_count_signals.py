"""N12 transfer-count signals. Pure functions; no prices, network, or execution."""
from __future__ import annotations

import math
from decimal import Decimal, InvalidOperation

DAY = 86400
HOUR = 3600
PRIORITY = ('BTCUSDT', 'ETHUSDT')


def _index(rows):
    indexed = {}
    for row in rows:
        stamp = row.get('time')
        if not isinstance(stamp, int) or isinstance(stamp, bool) or stamp % DAY:
            raise ValueError('Daily UTC grid required')
        if stamp in indexed:
            raise ValueError('Duplicate daily source timestamp')
        if not isinstance(row.get('count'), str):
            raise ValueError('Source count must be a decimal string')
        try:
            count = Decimal(row['count'])
        except (KeyError, InvalidOperation, ValueError, TypeError):
            raise ValueError('Invalid native-transfer count')
        if not count.is_finite() or count <= 0 or count != count.to_integral_value():
            raise ValueError('Positive finite integer native-transfer count required')
        indexed[stamp] = {**row, 'count': count}
    return indexed


def _received_by(row, deadline):
    value = row.get('received_at')
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and row['time'] + DAY <= value <= deadline)


def generate_signals(series, *, historical_assumption=False):
    """Use 90 *prior* consecutive days; source label D ends at D+1 day.

    All 91 receipts are required in the default prospective mode. Historical
    mode cannot establish first publication or certify revised source values.
    """
    indexed = {symbol: _index(series.get(symbol, [])) for symbol in PRIORITY}
    timestamps = sorted(set().union(*(set(rows) for rows in indexed.values())))
    decisions = {}
    for stamp in timestamps:
        feature_end = stamp + DAY
        decision_time = feature_end + 2 * DAY
        entry_time = decision_time + HOUR
        for symbol in PRIORITY:
            rows = indexed[symbol]
            required = [stamp - offset * DAY for offset in range(90, -1, -1)]
            if any(time not in rows for time in required):
                continue
            observations = [rows[time] for time in required]
            if not historical_assumption and not all(
                    _received_by(row, decision_time) for row in observations):
                continue
            threshold = sorted(row['count'] for row in observations[:-1])[62]
            if observations[-1]['count'] <= threshold:
                continue
            decisions[decision_time] = {
                'symbol': symbol, 'direction': 1, 'stop_pct': .02,
                'hold_hours': 12, 'signal_close_time': entry_time,
                'feature_end': feature_end, 'source_label': stamp,
                'decision_time': decision_time,
                'reason': 'native_transfer_count_above_prior_90_day_percentile_70',
            }
            break
    return {'N12': decisions}
