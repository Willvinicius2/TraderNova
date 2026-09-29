"""Pure N13 daily trade-IV skew and causal short signals; no network or PnL."""
from __future__ import annotations

import json
import math
from decimal import Decimal, InvalidOperation

DAY, HOUR = 86400, 3600
SYMBOLS = ('BTCUSDT', 'ETHUSDT')


def number(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = Decimal(str(value))
        return result if result.is_finite() else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def received_by(row, deadline, earliest):
    value = row.get('received_at')
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and earliest <= value <= deadline)


def median(values):
    ordered = sorted(values)
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2


def daily_skew(trades, instruments, currency, start, *, coverage_complete,
               coverage_received_at=None, historical_assumption=False):
    if currency not in ('BTC', 'ETH') or type(start) is not int or start % DAY:
        raise ValueError('Expected BTC/ETH and a UTC day start')
    end = start + DAY
    output = {'time': end, 'skew': None, 'put_count': 0, 'call_count': 0,
              'coverage_complete': bool(coverage_complete), 'received_at': None}
    if coverage_complete is not True:
        return output
    puts, calls, seen, unique, receipt_times = [], [], {}, {}, []
    valid_receipts = historical_assumption or received_by(
        {'received_at': coverage_received_at}, end + HOUR, end)
    if not historical_assumption and valid_receipts:
        receipt_times.append(coverage_received_at)
    for trade in trades:
        stamp, identity, name = trade.get('timestamp'), trade.get('trade_id'), trade.get('instrument_name')
        if (type(stamp) is not int or not start * 1000 <= stamp < end * 1000
                or not isinstance(identity, str) or not identity or not isinstance(name, str)):
            raise ValueError('Invalid identity or trade outside day')
        # Transport receipt timing is separate from the immutable market payload.
        payload = json.dumps({k: v for k, v in trade.items() if k != 'received_at'},
                             sort_keys=True, separators=(',', ':'), default=str, allow_nan=False)
        if identity in seen:
            if seen[identity] != payload:
                raise ValueError('Conflicting duplicate trade identity')
            if received_by(trade, end + HOUR, stamp / 1000):
                prior = unique[identity]
                if (not received_by(prior, end + HOUR, stamp / 1000)
                        or trade['received_at'] < prior['received_at']):
                    unique[identity] = trade
            continue
        seen[identity] = payload
        unique[identity] = trade
    for trade in unique.values():
        stamp, name = trade['timestamp'], trade['instrument_name']
        descriptor = instruments.get(name)
        if descriptor is None:
            raise ValueError('Missing official instrument descriptor')
        created, expiry = descriptor.get('creation_timestamp'), descriptor.get('expiration_timestamp')
        strike = number(descriptor.get('strike'))
        if (descriptor.get('kind') != 'option' or descriptor.get('base_currency') != currency
                or descriptor.get('price_index') != currency.lower() + '_usd'
                or descriptor.get('option_type') not in ('put', 'call')
                or type(created) is not int or type(expiry) is not int or created >= expiry
                or not created <= stamp < expiry or strike is None or strike <= 0):
            raise ValueError('Invalid or historically inactive option descriptor')
        if not historical_assumption:
            if (not received_by(trade, end + HOUR, stamp / 1000)
                    or not received_by(descriptor, end + HOUR, created / 1000)):
                valid_receipts = False
            else:
                receipt_times.extend((trade['received_at'], descriptor['received_at']))
        iv, index = number(trade.get('iv')), number(trade.get('index_price'))
        if iv is None or index is None or iv <= 0 or index <= 0:
            continue
        duration = expiry - stamp
        if not 7 * DAY * 1000 <= duration <= 35 * DAY * 1000:
            continue
        ratio = strike / index
        if descriptor['option_type'] == 'put' and Decimal('.85') <= ratio <= Decimal('.95'):
            puts.append(iv)
        elif descriptor['option_type'] == 'call' and Decimal('1.05') <= ratio <= Decimal('1.15'):
            calls.append(iv)
    output.update(put_count=len(puts), call_count=len(calls))
    if not historical_assumption and not valid_receipts:
        output['receipt_evidence_complete'] = False
        return output
    if len(puts) >= 5 and len(calls) >= 5:
        output['skew'] = str(median(puts) - median(calls))
        output['received_at'] = max(receipt_times) if receipt_times else None
    return output


def generate_signals(series, *, historical_assumption=False):
    indexed = {}
    for symbol in SYMBOLS:
        indexed[symbol] = {}
        for row in series.get(symbol, []):
            stamp = row.get('time')
            if type(stamp) is not int or stamp % DAY or stamp in indexed[symbol]:
                raise ValueError('Invalid or duplicate daily skew time')
            indexed[symbol][stamp] = row
    signals = {}
    times = sorted(set().union(*(set(rows) for rows in indexed.values())))
    for time in times:
        decision, entry = time + HOUR, time + 2 * HOUR
        required = [time - offset * DAY for offset in range(90, -1, -1)]
        for symbol in SYMBOLS:
            rows = indexed[symbol]
            if any(t not in rows for t in required):
                continue
            observations = [rows[t] for t in required]
            values = [number(row.get('skew')) for row in observations]
            if any(v is None for v in values) or any(
                    row.get('coverage_complete') is not True
                    or type(row.get('put_count')) is not int or row['put_count'] < 5
                    or type(row.get('call_count')) is not int or row['call_count'] < 5
                    for row in observations):
                continue
            if not historical_assumption and not all(
                    received_by(row, min(decision, row['time'] + HOUR), row['time'])
                    for row in observations):
                continue
            threshold = sorted(values[:-1])[53]
            if values[-1] <= 0 or values[-1] <= threshold:
                continue
            signals[decision] = {'symbol': symbol, 'direction': -1, 'stop_pct': .02,
                                 'hold_hours': 12, 'signal_close_time': entry,
                                 'feature_end': time, 'decision_time': decision,
                                 'reason': 'option_trade_put_minus_call_iv_above_prior_90_day_percentile_60'}
            break
    return {'N13': signals}
