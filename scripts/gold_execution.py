"""Offline M15 CFD execution research. No terminal/network calls or file writes.

simulate(bars, signals, start, end, scenario='base')
  bars: chronological structured numpy array with time (epoch seconds), OHLC Bid.
  signals[i]: None or a decision made after bar i CLOSED. Required keys: id,
    direction (+1/-1), stop (absolute Bid), target (absolute Bid).
    Optional: holdBars=32, maxTradesPerDay=2, atr, minRewardR=1, reward.
    When reward is present, replace target with entry Bid +/- reward * stop
    distance. Otherwise retain the absolute target. With atr, entry stop distance
    must be between 1 and 3 ATR. Reward/R checks use Bid distances; sizing includes
    spread, both slippages and round-trip commission.
  start/end: aligned epoch seconds, start inclusive/end exclusive, whole bars.

One contract lot is 100 oz. Fixed planned risk ceiling USD250, 0.01 lot steps,
USD100,000 starting balance, maximum 10x current equity notional. No notional is
deducted from CFD cash: cash changes only through commissions and realized PnL.
Daily USD3,000 loss reference is the last processed close before the new exported
calendar day; total equity floor USD90,000. These are research assumptions, not
certification of the firm's rules. Entry needs the full USD250 risk headroom.
Open positions are not liquidated using future OHLC just to enforce these floors.

Cutoff is 20:45 in the exported clock. Missing bars force an exit at the next
observed open. Crossing an exported calendar date flags unpriced overnight cost.
No swap is invented. Times are broker labels, not asserted true UTC.
"""
from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import numpy as np

BAR_SECONDS = 900
INITIAL_CAPITAL = 100_000.0
RISK_PER_TRADE = 250.0
DAILY_LOSS_LIMIT = 3_000.0
TOTAL_EQUITY_FLOOR = 90_000.0
CONTRACT_OZ = 100.0
LOT_STEP = 0.01
TICK_SIZE = 0.01
MIN_STOP_DISTANCE = 0.10
MAX_LOTS = 100.0
MAX_LEVERAGE = 10.0
CUTOFF_SECONDS = 20 * 3600 + 45 * 60
COSTS = {
    'base': {'spread': 0.60, 'slippage': 0.10, 'commissionPerLotRT': 10.0},
    'stress': {'spread': 1.20, 'slippage': 0.25, 'commissionPerLotRT': 20.0},
}


def _epoch(value: Any, name: str) -> int:
    result = int(value)
    if result != value or result % BAR_SECONDS:
        raise ValueError(f'{name} must be integer epoch seconds aligned to M15')
    return result


def _date(day: int) -> str:
    return datetime.fromtimestamp(day * 86400, timezone.utc).strftime('%Y-%m-%d')


def simulate(bars: np.ndarray, signals: Any, start: int, end: int,
             scenario: str = 'base') -> dict[str, Any]:
    """Return serializable trades, liquidation-value close curve and metrics.

    Intrabar exitTime is the candle OPEN label, not an observed execution time;
    exitTimeKind makes this explicit. Curve time is the candle close boundary,
    while dayLabel denotes the day of that candle's open. A 23:45 close is the
    preceding day's final observation and the next day's equity reference.
    """
    start, end = _epoch(start, 'start'), _epoch(end, 'end')
    if end <= start:
        raise ValueError('end must be after start')
    if scenario not in COSTS:
        raise ValueError("scenario must be 'base' or 'stress'")
    data = np.asarray(bars)
    if data.ndim != 1 or not data.dtype.names:
        raise ValueError('bars must be a one-dimensional structured numpy array')
    if not {'time', 'open', 'high', 'low', 'close'} <= set(data.dtype.names):
        raise ValueError('bars require time/open/high/low/close fields')
    if len(signals) != len(data):
        raise ValueError('signals must have one entry per candle')
    raw_times = np.asarray(data['time'], dtype=float)
    if not np.all(np.isfinite(raw_times)):
        raise ValueError('non-finite timestamps')
    times = raw_times.astype(np.int64)
    if (np.any(times != raw_times) or np.any(times % BAR_SECONDS)
            or np.any(np.diff(times) <= 0)):
        raise ValueError('timestamps must be unique, ordered M15 epoch seconds')
    o, h, l, c = (np.asarray(data[key], dtype=float)
                  for key in ('open', 'high', 'low', 'close'))
    if (not all(np.all(np.isfinite(a)) for a in (o, h, l, c))
            or np.any(l <= 0) or np.any(h < np.maximum(o, c))
            or np.any(l > np.minimum(o, c))):
        raise ValueError('invalid OHLC')

    cost = dict(COSTS[scenario])
    spread, slip, commission = (cost[key] for key in
                                ('spread', 'slippage', 'commissionPerLotRT'))
    indices = np.flatnonzero((times >= start) & (times < end))
    trades: list[dict[str, Any]] = []
    curve: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    trade_counts: Counter[tuple[int, str]] = Counter()
    daily: dict[int, dict[str, Any]] = {}
    balance = INITIAL_CAPITAL
    position: dict[str, Any] | None = None
    current_day: int | None = None
    day_reference = INITIAL_CAPITAL
    prior_close_equity = INITIAL_CAPITAL
    day_paused = False
    total_paused = False
    peak_equity = INITIAL_CAPITAL
    max_drawdown = 0.0
    max_drawdown_pct = 0.0
    max_daily_loss = 0.0
    gap_count = 0
    eps = 1e-8

    def liquidation_equity(bid: float) -> float:
        if position is None:
            return balance
        fill = bid - slip if position['direction'] == 1 else bid + spread + slip
        return (balance + position['direction'] * (fill - position['entry'])
                * position['quantityOz'] - position['exitCommission'])

    def observe_limits(equity: float) -> None:
        nonlocal day_paused, total_paused
        if equity <= day_reference - DAILY_LOSS_LIMIT + eps:
            day_paused = True
        if equity <= TOTAL_EQUITY_FLOOR + eps:
            total_paused = True

    def close_position(fill: float, stamp: int, candle_time: int,
                       reason: str, kind: str, exit_bid: float) -> None:
        nonlocal position, balance
        assert position is not None
        p = position
        gross = p['direction'] * (fill - p['entry']) * p['quantityOz']
        net = gross - p['entryCommission'] - p['exitCommission']
        balance += gross - p['exitCommission']
        overnight = candle_time // 86400 != p['entryTime'] // 86400
        trades.append({
            'id': p['id'], 'direction': p['direction'],
            'signalTime': p['signalTime'], 'signalCloseTime': p['signalTime'] + 900,
            'entryTime': p['entryTime'], 'exitTime': stamp,
            'exitCandleTime': candle_time, 'exitTimeKind': kind,
            'entryBid': p['entryBid'], 'entry': p['entry'],
            'exitBidReference': exit_bid, 'exit': fill,
            'stop': p['stop'], 'target': p['target'],
            'lots': p['lots'], 'quantityOz': p['quantityOz'],
            'plannedRisk': p['plannedRisk'], 'barsHeld': p['barsHeld'],
            'grossPnl': gross, 'commission': p['entryCommission'] + p['exitCommission'],
            'net': net, 'balanceAfter': balance, 'reason': reason,
            'overnightUnknownCost': overnight,
        })
        position = None

    def at_market(bid: float, stamp: int, candle_time: int,
                  reason: str, kind: str = 'bar_open') -> None:
        assert position is not None
        fill = bid - slip if position['direction'] == 1 else bid + spread + slip
        close_position(fill, stamp, candle_time, reason, kind, bid)

    for ordinal, raw_i in enumerate(indices):
        i = int(raw_i)
        t, bid = int(times[i]), float(o[i])
        day, seconds = t // 86400, t % 86400
        if day != current_day:
            current_day, day_reference, day_paused = day, prior_close_equity, False
            daily[day] = {'dayLabel': _date(day), 'referenceEquity': day_reference,
                          'minCloseEquity': day_reference, 'maxClosedEquityLoss': 0.0,
                          'endingEquity': day_reference, 'entries': 0}
        gap = ordinal > 0 and t - int(times[int(indices[ordinal - 1])]) != BAR_SECONDS
        if gap:
            gap_count += 1

        # All opening decisions precede access to this candle's high/low/close.
        if position is not None:
            p = position
            quote_open = bid if p['direction'] == 1 else bid + spread
            stop_quote = p['stop'] if p['direction'] == 1 else p['stop'] + spread
            target_quote = p['target'] if p['direction'] == 1 else p['target'] + spread
            stop_gap = quote_open <= stop_quote if p['direction'] == 1 else quote_open >= stop_quote
            target_gap = quote_open >= target_quote if p['direction'] == 1 else quote_open <= target_quote
            if stop_gap:
                at_market(bid, t, t, 'stop_gap')
            elif target_gap:
                fill = target_quote - slip if p['direction'] == 1 else target_quote + slip
                close_position(fill, t, t, 'target_gap_capped', 'bar_open', p['target'])
            elif gap:
                at_market(bid, t, t, 'data_gap')
            elif day != p['entryTime'] // 86400 or seconds >= CUTOFF_SECONDS:
                at_market(bid, t, t, 'session_cutoff')
            elif p['barsHeld'] >= p['holdBars']:
                at_market(bid, t, t, 'max_hold')
        observe_limits(liquidation_equity(bid))

        signal = signals[i - 1] if i > 0 and int(times[i - 1]) >= start else None
        if signal is not None and position is None:
            if t - int(times[i - 1]) != BAR_SECONDS or int(times[i - 1]) // 86400 != day:
                skipped['discontinuous_or_cross_day_entry'] += 1
            elif not 8 * 3600 <= seconds < 20 * 3600:
                skipped['entry_hours'] += 1
            elif total_paused or day_paused:
                skipped['risk_pause'] += 1
            elif min(balance - (day_reference - DAILY_LOSS_LIMIT),
                     balance - TOTAL_EQUITY_FLOOR) + eps < RISK_PER_TRADE:
                skipped['insufficient_full_risk_budget'] += 1
            else:
                if not isinstance(signal, dict):
                    raise ValueError('non-empty signals must be dictionaries')
                sid = signal.get('id')
                direction = signal.get('direction')
                if not isinstance(sid, str) or not sid or direction not in (-1, 1):
                    raise ValueError('signals require a nonempty id and direction +/-1')
                hold = int(signal.get('holdBars', 32))
                max_trades = int(signal.get('maxTradesPerDay', 2))
                if (hold <= 0 or hold != signal.get('holdBars', 32)
                        or max_trades <= 0 or max_trades != signal.get('maxTradesPerDay', 2)):
                    raise ValueError('holdBars and maxTradesPerDay must be positive integers')
                stop = float(signal['stop'])
                target = float(signal['target'])
                min_reward = float(signal.get('minRewardR', 1.0))
                if not all(math.isfinite(v) for v in (stop, target, min_reward)) or min_reward < 0:
                    raise ValueError('non-finite levels or invalid minRewardR')
                stop = round((math.floor(stop / TICK_SIZE + 1e-9) if direction == 1 else math.ceil(stop / TICK_SIZE - 1e-9)) * TICK_SIZE, 2)
                distance = direction * (bid - stop)
                if signal.get('reward') is not None:
                    reward = float(signal['reward'])
                    if not math.isfinite(reward) or reward <= 0:
                        raise ValueError('reward must be positive and finite')
                    target = bid + direction * reward * distance
                target = round((math.ceil(target / TICK_SIZE - 1e-9) if direction == 1 else math.floor(target / TICK_SIZE + 1e-9)) * TICK_SIZE, 2)
                target_distance = direction * (target - bid)
                atr_ok = True
                if signal.get('atr') is not None:
                    atr_value = float(signal['atr'])
                    if not math.isfinite(atr_value) or atr_value <= 0:
                        raise ValueError('atr must be positive and finite')
                    atr_ok = 1.0 - 1e-12 <= distance / atr_value <= 3.0 + 1e-12
                if stop <= 0 or target <= 0 or distance < MIN_STOP_DISTANCE-eps or target_distance < MIN_STOP_DISTANCE-eps:
                    skipped['invalid_entry_bracket'] += 1
                elif not atr_ok:
                    skipped['entry_stop_atr_range'] += 1
                elif target_distance + eps < min_reward * distance:
                    skipped['entry_reward_r'] += 1
                elif trade_counts[(day, sid)] >= max_trades:
                    skipped['family_daily_trade_cap'] += 1
                else:
                    entry = bid + spread + slip if direction == 1 else bid - slip
                    stop_fill = stop - slip if direction == 1 else stop + spread + slip
                    risk_per_lot = direction * (entry - stop_fill) * CONTRACT_OZ + commission
                    lot_ceiling = min(MAX_LOTS, RISK_PER_TRADE / risk_per_lot,
                                      MAX_LEVERAGE * balance / (entry * CONTRACT_OZ))
                    lots = round(math.floor(lot_ceiling / LOT_STEP + 1e-12) * LOT_STEP, 2)
                    if lots < LOT_STEP:
                        skipped['below_minimum_lot'] += 1
                    else:
                        fee_half = lots * commission / 2.0
                        balance -= fee_half
                        position = {
                            'id': sid, 'direction': direction, 'signalTime': int(times[i - 1]),
                            'entryTime': t, 'entryBid': bid, 'entry': entry,
                            'stop': stop, 'target': target, 'holdBars': hold, 'barsHeld': 0,
                            'lots': lots, 'quantityOz': lots * CONTRACT_OZ,
                            'entryCommission': fee_half, 'exitCommission': fee_half,
                            'plannedRisk': lots * risk_per_lot,
                        }
                        trade_counts[(day, sid)] += 1
                        daily[day]['entries'] += 1

        if position is not None:
            p = position
            p['barsHeld'] += 1
            quote_low = float(l[i]) if p['direction'] == 1 else float(l[i]) + spread
            quote_high = float(h[i]) if p['direction'] == 1 else float(h[i]) + spread
            stop_quote = p['stop'] if p['direction'] == 1 else p['stop'] + spread
            target_quote = p['target'] if p['direction'] == 1 else p['target'] + spread
            stop_hit = quote_low <= stop_quote if p['direction'] == 1 else quote_high >= stop_quote
            target_hit = quote_high >= target_quote if p['direction'] == 1 else quote_low <= target_quote
            if stop_hit:
                fill = stop_quote - slip if p['direction'] == 1 else stop_quote + slip
                close_position(fill, t, t, 'stop', 'intrabar_unknown', p['stop'])
            elif target_hit:
                fill = target_quote - slip if p['direction'] == 1 else target_quote + slip
                close_position(fill, t, t, 'target', 'intrabar_unknown', p['target'])

        if ordinal == len(indices) - 1 and position is not None:
            at_market(float(c[i]), t + BAR_SECONDS, t, 'window_end', 'bar_close')
        equity = float(liquidation_equity(float(c[i])))
        observe_limits(equity)
        peak_equity = max(peak_equity, equity)
        max_drawdown = max(max_drawdown, peak_equity - equity)
        max_drawdown_pct = max(max_drawdown_pct, 100.0 * (peak_equity - equity) / peak_equity)
        loss = max(0.0, day_reference - equity)
        max_daily_loss = max(max_daily_loss, loss)
        daily[day]['minCloseEquity'] = min(daily[day]['minCloseEquity'], equity)
        daily[day]['maxClosedEquityLoss'] = max(daily[day]['maxClosedEquityLoss'], loss)
        daily[day]['endingEquity'] = equity
        curve.append({'time': t + BAR_SECONDS, 'candleTime': t, 'dayLabel': _date(day),
                      'balance': float(balance), 'equity': equity,
                      'dayReferenceEquity': float(day_reference)})
        prior_close_equity = equity

    profits = sum(trade['net'] for trade in trades if trade['net'] > 0)
    losses = -sum(trade['net'] for trade in trades if trade['net'] < 0)
    net = float(balance - INITIAL_CAPITAL)
    if not math.isclose(net, sum(trade['net'] for trade in trades), abs_tol=1e-6):
        raise AssertionError('cash/trade PnL reconciliation failed')
    return {
        'scenario': scenario, 'costs': cost, 'start': start, 'end': end,
        'initialCapital': INITIAL_CAPITAL, 'endingBalance': float(balance),
        'trades': trades, 'curve': curve, 'net': net,
        'returnPct': 100.0 * net / INITIAL_CAPITAL,
        'profitFactor': float(profits / losses) if losses > 0 else None,
        'maxDrawdown': float(max_drawdown), 'maxDrawdownPct': float(max_drawdown_pct),
        'maxDailyClosedEquityLoss': float(max_daily_loss),
        'overnightUnpriced': sum(trade['overnightUnknownCost'] for trade in trades),
        'daily': list(daily.values()), 'skipped': dict(skipped), 'observedGaps': gap_count,
        'totalRiskPaused': bool(total_paused), 'valid': False,
        'assumptions': {
            'clock': 'native exported broker labels; UTC/session offset unverified',
            'dailyReference': 'last processed close before new exported calendar day',
            'dailyLossLimit': DAILY_LOSS_LIMIT, 'totalEquityFloor': TOTAL_EQUITY_FLOOR,
            'plannedRiskPerTrade': RISK_PER_TRADE,
            'entryHours': '[08:00,20:00)', 'sessionCutoff': '20:45',
            'drawdown': 'liquidation-value M15 closes; intrabar limits not certified',
            'costs': 'fixed research assumptions, not historical broker costs; swap absent',
        },
    }
