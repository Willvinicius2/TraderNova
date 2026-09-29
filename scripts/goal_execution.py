"""Causal, long-only USD-M research executor. No network or trading API calls.

Decisions use completed spot bars; fills use subsequent perpetual bars. Quantities
are continuous research quantities, not certified exchange lot sizes. Fees and
slippage are fixed conservative scenarios. Funding is realized historical data;
missing settlement marks use the adverse bound of that hour's mark OHLC. For a
stop whose intrahour time is unknown, debit all possibly owed funding and do not
credit possibly missed funding. This is a conservative screen, not a fill claim.
"""
from __future__ import annotations

import math
from typing import Any

HOUR = 3600
CAPITAL = 100_000.0
COSTS = {'base': (0.0005, 0.0002), 'stress': (0.001, 0.0005)}


def _valid_bar(bar: dict) -> bool:
    values = [bar.get(k) for k in ('open', 'high', 'low', 'close')]
    return (all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0 for v in values)
            and bar['low'] <= min(bar['open'], bar['close'])
            and bar['high'] >= max(bar['open'], bar['close']))


def simulate(perp: dict[str, list[dict]], marks: dict[str, list[dict]],
             funding: dict[str, list[dict]], signals: dict[int, dict],
             start: int, end: int, scenario: str = 'base') -> dict[str, Any]:
    if start >= end or start % HOUR or end % HOUR:
        raise ValueError('Window must be positive and H1-aligned')
    fee, slip = COSTS[scenario]
    symbols = sorted(perp)
    candles, mark_index, events = {}, {}, {}
    for symbol in symbols:
        for series in (perp[symbol], marks[symbol]):
            previous = None
            for b in series:
                if not _valid_bar(b) or b['time'] % HOUR or (previous is not None and b['time'] <= previous):
                    raise ValueError(f'Invalid or unordered {symbol} bar')
                previous = b['time']
        candles[symbol] = {b['time']: b for b in perp[symbol]}
        mark_index[symbol] = {b['time']: b for b in marks[symbol]}
        events[symbol] = {}
        previous = None
        for f in funding[symbol]:
            stamp, rate = f['time_ms'], f['rate']
            if not isinstance(stamp, int) or not math.isfinite(rate) or (previous is not None and stamp <= previous):
                raise ValueError('Invalid/duplicate/out-of-order funding')
            if f.get('mark_price') is not None and (not math.isfinite(f['mark_price']) or f['mark_price'] <= 0):
                raise ValueError('Invalid settlement mark')
            previous = stamp
            bucket = (stamp // (HOUR * 1000)) * HOUR
            events[symbol].setdefault(bucket, []).append(f)

    balance = peak = previous_close = CAPITAL
    position = None
    trades, daily = [], []
    max_dd = max_daily = 0.0
    current_day = None
    daily_reference = CAPITAL
    account_breach = False
    funding_bounds = ambiguous_funding = 0
    skipped = 0
    data_quality_flags = []

    def settle(f: dict, symbol: str, t: int, uncertain_exit: bool = False):
        nonlocal balance, funding_bounds, ambiguous_funding
        mark = f.get('mark_price')
        if mark is None:
            if t not in mark_index[symbol]:
                data_quality_flags.append({'time': t, 'symbol': symbol, 'issue': 'unpriced_funding'})
                return
            mark = mark_index[symbol][t]['high' if f['rate'] >= 0 else 'low']
            funding_bounds += 1
        payment = -position['qty'] * mark * f['rate']
        if uncertain_exit:
            ambiguous_funding += 1
            payment = min(0, payment)
        balance += payment
        position['funding_pnl'] += payment

    def liquidation_value(price: float) -> float:
        if position is None:
            return balance
        filled = price * (1 - slip)
        return balance + position['qty'] * (filled - position['entry']) - position['qty'] * filled * fee

    def observe(low_equity: float, high_equity: float | None = None):
        nonlocal peak, max_dd, max_daily, account_breach
        # An envelope: a favorable mark may precede an adverse mark. No claim
        # about the actual intrabar ordering or an executable risk-floor fill.
        peak = max(peak, low_equity if high_equity is None else high_equity)
        max_dd = max(max_dd, 100 * (peak - low_equity) / peak)
        daily_loss = max(0, 100 * (daily_reference - low_equity) / daily_reference)
        max_daily = max(max_daily, daily_loss)
        if low_equity <= CAPITAL * .9 or daily_loss >= 3:
            account_breach = True

    def close(price: float, time: int, reason: str):
        nonlocal balance, position
        p = position
        filled = price * (1 - slip)
        exit_fee = p['qty'] * filled * fee
        realized = p['qty'] * (filled - p['entry']) - exit_fee
        balance += realized
        pnl = realized - p['entry_fee'] + p['funding_pnl']
        trades.append({**p, 'exit': filled, 'exit_time': time, 'reason': reason,
                       'exit_fee': exit_fee, 'pnl': pnl})
        position = None
        observe(balance)

    for t in range(start, end, HOUR):
        day = t // 86400
        if day != current_day:
            if current_day is not None:
                daily.append({'day': current_day, 'equity': previous_close})
            current_day = day
            daily_reference = max(balance, previous_close)
        exited = False
        if position:
            symbol = position['symbol']
            b, m = candles[symbol].get(t), mark_index[symbol].get(t)
            if b is None or m is None:
                data_quality_flags.append({'time': t, 'symbol': symbol,
                                           'issue': 'missing_active_trade' if b is None else 'missing_active_mark'})
                # Never suppress yesterday's entry because tomorrow has a gap.
                # If a trade open exists we can exit now; otherwise wait for the
                # first actual open. The uncertain window is never screen-eligible.
                for f in events[symbol].get(t, []):
                    if b is None or f['time_ms'] == t * 1000:
                        settle(f, symbol, t, uncertain_exit=True)
                if b is not None:
                    close(b['open'], t, 'data_gap')
                    previous_close = balance
                else:
                    position['data_gap_exit_pending'] = True
                    if m is not None:
                        observe(liquidation_value(m['low']), liquidation_value(m['high']))
                        previous_close = liquidation_value(m['close'])
                continue
        # Settlement exactly at the open belongs to a pre-existing position.
        if position:
            symbol = position['symbol']
            b = candles[symbol][t]
            exiting_at_open = (position.get('data_gap_exit_pending', False)
                               or b['open'] <= position['stop'] or t >= position['exit_due'])
            for f in events[symbol].get(t, []):
                if f['time_ms'] == t * 1000:
                    settle(f, symbol, t, uncertain_exit=exiting_at_open)
            observe(liquidation_value(mark_index[symbol][t]['open']))
            if position.get('data_gap_exit_pending'):
                close(b['open'], t, 'data_gap')
                exited = True
            elif b['open'] <= position['stop']:
                close(b['open'], t, 'gap_stop')
                exited = True
            elif t >= position['exit_due']:
                close(b['open'], t, 'time')
                exited = True

        decision = signals.get(t - HOUR)
        if not position and not exited and not account_breach and decision:
            if (decision['signal_close_time'] != t or decision['direction'] != 1
                    or not 0 < decision['stop_pct'] < 1 or decision['hold_hours'] < 1):
                raise ValueError('Noncausal or invalid signal')
            symbol = decision['symbol']
            if (t + decision['hold_hours'] * HOUR >= end
                    or t not in candles[symbol] or t not in mark_index[symbol]):
                skipped += 1
            else:
                entry = candles[symbol][t]['open'] * (1 + slip)
                stop = entry * (1 - decision['stop_pct'])
                stop_fill = stop * (1 - slip)
                unit_risk = entry - stop_fill + fee * (entry + stop_fill)
                risk_budget = .0025 * balance
                qty = min(risk_budget / unit_risk, balance / (entry * (1 + fee)))
                entry_fee = qty * entry * fee
                position = {'symbol': symbol, 'entry_time': t, 'signal_time': t - HOUR,
                            'entry': entry, 'entry_fee': entry_fee, 'qty': qty,
                            'stop': stop, 'exit_due': t + decision['hold_hours'] * HOUR,
                            'risk_budget': risk_budget, 'funding_pnl': 0.0,
                            'evidence': decision.get('reason')}
                balance -= entry_fee
                # Same-timestamp entry/settlement ordering is not in H1 data.
                # Debit a possible charge; do not invent an incoming payment.
                for f in events[symbol].get(t, []):
                    if f['time_ms'] == t * 1000:
                        settle(f, symbol, t, uncertain_exit=True)

        if position:
            symbol = position['symbol']
            b, m = candles[symbol][t], mark_index[symbol][t]
            stop_hit = b['low'] <= position['stop']
            debits = credits = 0.0
            for f in events[symbol].get(t, []):
                if f['time_ms'] <= t * 1000:
                    continue
                mark = f.get('mark_price')
                if mark is None:
                    mark = m['high' if f['rate'] >= 0 else 'low']
                    funding_bounds += 1
                payment = -position['qty'] * mark * f['rate']
                if stop_hit:
                    ambiguous_funding += 1
                if payment < 0:
                    debits += payment
                elif not stop_hit:
                    credits += payment
            # Debit first; do not use a later credit to conceal intrabar risk.
            high_equity = liquidation_value(m['high'])
            balance += debits
            position['funding_pnl'] += debits
            observe(liquidation_value(m['low']), high_equity)
            balance += credits
            position['funding_pnl'] += credits
            if stop_hit:
                close(min(b['open'], position['stop']), t, 'intrabar_stop_time_unknown')
            elif t == end - HOUR:
                close(b['close'], end, 'window_end')

        previous_close = liquidation_value(mark_index[position['symbol']][t]['close']) if position else balance
        observe(previous_close)
    if current_day is not None:
        daily.append({'day': current_day, 'equity': previous_close})
    if position:
        raise AssertionError('Position left open')
    gross_profit = sum(x['pnl'] for x in trades if x['pnl'] > 0)
    gross_loss = -sum(x['pnl'] for x in trades if x['pnl'] < 0)
    if not math.isclose(balance - CAPITAL, sum(x['pnl'] for x in trades), abs_tol=1e-6):
        raise AssertionError('Trade PnL does not reconcile with equity')
    return {'scenario': scenario, 'start': start, 'end': end, 'trade_count': len(trades),
            'net_pct': 100 * (balance / CAPITAL - 1), 'net_cash': balance - CAPITAL,
            'profit_factor': gross_profit / gross_loss if gross_loss else None,
            'max_drawdown_pct': max_dd, 'max_daily_loss_pct': max_daily,
            'account_breach': account_breach, 'funding_mark_bounds': funding_bounds,
            'ambiguous_intrabar_funding': ambiguous_funding, 'boundary_skips': skipped,
            'data_quality_flags': data_quality_flags,
            'trades': trades, 'daily': daily, 'validated': False}
