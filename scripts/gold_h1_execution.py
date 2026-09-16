"""Offline H1 CFD execution research. No terminal/network calls or file writes.

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
Daily reference is max(balance, Bid/Ask marked equity) at the last processed close
before the new exported calendar day. The daily loss ceiling is min(USD3,000, 3%
of that reference); total equity floor USD90,000. Any estimated breach permanently
blocks new entries, including on following days. These are research assumptions,
not certification of the firm's rules. Entry needs full USD250 risk headroom.
An intrabar adverse-equity envelope is capped at an executable stop; adverse
opening gaps are not capped. No high/low ordering is claimed. The envelope can
precede a target under an adverse path; it is not an observed account drawdown.
Risk checks include remaining liquidation costs, but daily reference marked
equity excludes unincurred exit slippage and exit commission. A breach flag never
creates a fictional fill at the account limit: normal stop/time/gap exits remain.

Cutoff is 20:00 in the exported clock. Missing bars force an exit at the next
observed open. Crossing an exported calendar date flags unpriced overnight cost.
No swap is invented. Times are broker labels, not asserted true UTC.
"""
from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import numpy as np

BAR_SECONDS = 3600
INITIAL_CAPITAL = 100_000.0
RISK_PER_TRADE = 250.0
DAILY_LOSS_LIMIT = 3_000.0
DAILY_LOSS_FRACTION = 0.03
TOTAL_EQUITY_FLOOR = 90_000.0
CONTRACT_OZ = 100.0
LOT_STEP = 0.01
TICK_SIZE = 0.01
MIN_STOP_DISTANCE = 0.10
MAX_LOTS = 100.0
MAX_LEVERAGE = 10.0
CUTOFF_SECONDS = 20 * 3600
COSTS = {
    'base': {'spread': 0.60, 'slippage': 0.10, 'commissionPerLotRT': 10.0},
    'stress': {'spread': 1.20, 'slippage': 0.25, 'commissionPerLotRT': 20.0},
}


def _epoch(value: Any, name: str) -> int:
    result = int(value)
    if result != value or result % BAR_SECONDS:
        raise ValueError(f'{name} must be integer epoch seconds aligned to H1')
    return result


def _date(day: int) -> str:
    return datetime.fromtimestamp(day * 86400, timezone.utc).strftime('%Y-%m-%d')


def daily_risk_reference(balance: float, marked_equity: float) -> dict[str, float]:
    """Snapshot only: marked equity is balance plus currently floating Bid/Ask PnL."""
    balance, marked_equity = float(balance), float(marked_equity)
    if not math.isfinite(balance) or not math.isfinite(marked_equity):
        raise ValueError('daily reference needs finite balance and marked equity')
    reference = max(balance, marked_equity)
    loss_limit = min(DAILY_LOSS_LIMIT, max(0.0, DAILY_LOSS_FRACTION * reference))
    return {'balance': balance, 'markedEquity': marked_equity,
            'referenceEquity': reference, 'lossLimit': loss_limit,
            'equityFloor': reference - loss_limit}


def execution_parameters(scenario: str = 'base') -> dict[str, Any]:
    if scenario not in COSTS:
        raise ValueError("scenario must be 'base' or 'stress'")
    return {'barSeconds': BAR_SECONDS, 'timeframe': 'H1', 'initialCapital': INITIAL_CAPITAL,
            'plannedRisk': RISK_PER_TRADE, 'dailyLossCap': DAILY_LOSS_LIMIT,
            'dailyLossFraction': DAILY_LOSS_FRACTION, 'totalEquityFloor': TOTAL_EQUITY_FLOOR,
            'contractOz': CONTRACT_OZ, 'lotStep': LOT_STEP, 'maxLots': MAX_LOTS,
            'maxLeverage': MAX_LEVERAGE, 'tickSize': TICK_SIZE,
            'minStopDistance': MIN_STOP_DISTANCE, 'entryHours': '[08:00,20:00)',
            'cutoff': '20:00', 'costs': dict(COSTS[scenario]),
            'riskReference': 'max(balance, Bid/Ask marked equity) at preceding available close',
            'permanentBreach': True}


def simulate(bars: np.ndarray, signals: Any, start: int, end: int,
             scenario: str = 'base') -> dict[str, Any]:
    """Return serializable trades, liquidation-value close curve and metrics.

    Intrabar exitTime is the candle OPEN label, not an observed execution time;
    exitTimeKind makes this explicit. Curve time is the candle close boundary,
    while dayLabel denotes the day of that candle's open. A 23:00 close is the
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
        raise ValueError('timestamps must be unique, ordered H1 epoch seconds')
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
    day_loss_limit = DAILY_LOSS_LIMIT
    day_floor = INITIAL_CAPITAL - DAILY_LOSS_LIMIT
    prior_close_balance = INITIAL_CAPITAL
    prior_close_marked_equity = INITIAL_CAPITAL
    account_breached = False
    daily_breached = False
    total_paused = False
    breaches: list[dict[str, Any]] = []
    peak_equity = INITIAL_CAPITAL
    max_drawdown = 0.0
    max_drawdown_pct = 0.0
    max_daily_loss = 0.0
    conservative_peak = INITIAL_CAPITAL
    conservative_drawdown = 0.0
    conservative_drawdown_pct = 0.0
    max_daily_conservative_loss = 0.0
    gap_count = 0
    eps = 1e-8

    def liquidation_equity(bid: float) -> float:
        if position is None:
            return balance
        fill = bid - slip if position['direction'] == 1 else bid + spread + slip
        return (balance + position['direction'] * (fill - position['entry'])
                * position['quantityOz'] - position['exitCommission'])

    def marked_equity(bid: float) -> float:
        if position is None:
            return balance
        quote = bid if position['direction'] == 1 else bid + spread
        return balance + position['direction'] * (quote - position['entry']) * position['quantityOz']

    def observe_limits(equity: float, stamp: int, source: str) -> None:
        nonlocal account_breached, daily_breached, total_paused, max_daily_conservative_loss
        loss = max(0.0, day_reference - equity)
        max_daily_conservative_loss = max(max_daily_conservative_loss, loss)
        daily[current_day]['minConservativeEquity'] = min(daily[current_day]['minConservativeEquity'], equity)
        daily[current_day]['maxConservativeEquityLoss'] = max(daily[current_day]['maxConservativeEquityLoss'], loss)
        for kind, floor, already in [('daily_loss', day_floor, daily_breached),
                                     ('total_floor', TOTAL_EQUITY_FLOOR, total_paused)]:
            if equity <= floor + eps:
                account_breached = True
                if not already:
                    breaches.append({'kind': kind, 'time': stamp, 'dayLabel': _date(current_day),
                                     'source': source, 'equityEstimate': float(equity),
                                     'referenceEquity': float(day_reference),
                                     'dailyLossLimit': float(day_loss_limit), 'floor': float(floor),
                                     'intrabarSequenceUnknown': source == 'intrabar_adverse_bound'})
                if kind == 'daily_loss':
                    daily_breached = True
                else:
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
            'signalTime': p['signalTime'], 'signalCloseTime': p['signalTime'] + BAR_SECONDS,
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
            current_day = day
            snapshot = daily_risk_reference(prior_close_balance, prior_close_marked_equity)
            day_reference, day_loss_limit, day_floor = (snapshot[key] for key in
                                                       ('referenceEquity', 'lossLimit', 'equityFloor'))
            daily[day] = {'dayLabel': _date(day), 'referenceEquity': day_reference,
                          'referenceBalance': snapshot['balance'],
                          'referenceMarkedEquity': snapshot['markedEquity'],
                          'lossLimit': day_loss_limit, 'equityFloor': day_floor,
                          'minCloseEquity': day_reference, 'maxClosedEquityLoss': 0.0,
                          'minConservativeEquity': day_reference,
                          'maxConservativeEquityLoss': 0.0,
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
        opening_equity = float(liquidation_equity(bid))
        conservative_peak = max(conservative_peak, opening_equity)
        bar_conservative_min = opening_equity
        observe_limits(opening_equity, t, 'opening_liquidation')

        signal = signals[i - 1] if i > 0 and int(times[i - 1]) >= start else None
        if signal is not None and position is None:
            if t - int(times[i - 1]) != BAR_SECONDS or int(times[i - 1]) // 86400 != day:
                skipped['discontinuous_or_cross_day_entry'] += 1
            elif not 8 * 3600 <= seconds < 20 * 3600:
                skipped['entry_hours'] += 1
            elif account_breached:
                skipped['risk_pause'] += 1
            elif min(balance - day_floor,
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
            # Only adverse excursion is used; no favorable high/low is allowed
            # to raise the peak or size a position. A reached stop ends exposure.
            adverse_bid = max(float(l[i]), p['stop']) if p['direction'] == 1 else min(float(h[i]), p['stop'])
            adverse_equity = float(liquidation_equity(adverse_bid))
            bar_conservative_min = min(bar_conservative_min, adverse_equity)
            observe_limits(adverse_equity, t, 'intrabar_adverse_bound')
            if stop_hit:
                fill = stop_quote - slip if p['direction'] == 1 else stop_quote + slip
                close_position(fill, t, t, 'stop', 'intrabar_unknown', p['stop'])
            elif target_hit:
                fill = target_quote - slip if p['direction'] == 1 else target_quote + slip
                close_position(fill, t, t, 'target', 'intrabar_unknown', p['target'])

        if ordinal == len(indices) - 1 and position is not None:
            at_market(float(c[i]), t + BAR_SECONDS, t, 'window_end', 'bar_close')
        equity = float(liquidation_equity(float(c[i])))
        marked = float(marked_equity(float(c[i])))
        observe_limits(equity, t + BAR_SECONDS, 'close_liquidation')
        bar_conservative_min = min(bar_conservative_min, equity)
        conservative_drawdown = max(conservative_drawdown, conservative_peak - bar_conservative_min)
        conservative_drawdown_pct = max(conservative_drawdown_pct, 100.0 * (conservative_peak - bar_conservative_min) / conservative_peak)
        conservative_peak = max(conservative_peak, equity)
        peak_equity = max(peak_equity, equity)
        max_drawdown = max(max_drawdown, peak_equity - equity)
        max_drawdown_pct = max(max_drawdown_pct, 100.0 * (peak_equity - equity) / peak_equity)
        loss = max(0.0, day_reference - equity)
        max_daily_loss = max(max_daily_loss, loss)
        daily[day]['minCloseEquity'] = min(daily[day]['minCloseEquity'], equity)
        daily[day]['maxClosedEquityLoss'] = max(daily[day]['maxClosedEquityLoss'], loss)
        daily[day]['endingEquity'] = equity
        daily[day]['endingBalance'] = float(balance)
        daily[day]['endingMarkedEquity'] = marked
        curve.append({'time': t + BAR_SECONDS, 'candleTime': t, 'dayLabel': _date(day),
                      'balance': float(balance), 'equity': equity,
                      'markedEquity': marked, 'liquidationEquity': equity,
                      'conservativeAdverseEquity': float(bar_conservative_min),
                      'dayReferenceEquity': float(day_reference),
                      'dayLossLimit': float(day_loss_limit), 'dayEquityFloor': float(day_floor),
                      'accountBreached': bool(account_breached)})
        prior_close_balance, prior_close_marked_equity = float(balance), marked

    profits = sum(trade['net'] for trade in trades if trade['net'] > 0)
    losses = -sum(trade['net'] for trade in trades if trade['net'] < 0)
    net = float(balance - INITIAL_CAPITAL)
    if not math.isclose(net, sum(trade['net'] for trade in trades), abs_tol=1e-6):
        raise AssertionError('cash/trade PnL reconciliation failed')
    return {
        'scenario': scenario, 'costs': cost, 'start': start, 'end': end,
        'parameters': execution_parameters(scenario), 'barSeconds': BAR_SECONDS,
        'riskReference': execution_parameters(scenario)['riskReference'],
        'initialCapital': INITIAL_CAPITAL, 'endingBalance': float(balance),
        'trades': trades, 'curve': curve, 'net': net,
        'returnPct': 100.0 * net / INITIAL_CAPITAL,
        'profitFactor': float(profits / losses) if losses > 0 else None,
        'maxDrawdown': float(max_drawdown), 'maxDrawdownPct': float(max_drawdown_pct),
        'observedClosedDrawdown': float(max_drawdown),
        'observedClosedDrawdownPct': float(max_drawdown_pct),
        'conservativeDrawdown': float(conservative_drawdown),
        'conservativeDrawdownPct': float(conservative_drawdown_pct),
        'maxDailyClosedEquityLoss': float(max_daily_loss),
        'maxDailyConservativeEquityLoss': float(max_daily_conservative_loss),
        'overnightUnpriced': sum(trade['overnightUnknownCost'] for trade in trades),
        'daily': list(daily.values()), 'skipped': dict(skipped), 'observedGaps': gap_count,
        'accountBreached': bool(account_breached), 'permanentRiskBlock': bool(account_breached),
        'dailyLossBreached': bool(daily_breached), 'totalLossBreached': bool(total_paused),
        'breaches': breaches, 'rejectedForRiskBreach': bool(account_breached),
        'totalRiskPaused': bool(total_paused), 'valid': False,
        'assumptions': {
            'clock': 'native exported broker labels; UTC/session offset unverified',
            'dailyReference': execution_parameters(scenario)['riskReference'],
            'dailyLossLimit': 'min(3000, 0.03 * referenceEquity)',
            'totalEquityFloor': TOTAL_EQUITY_FLOOR, 'breachAction': 'permanent entry block, never reset by day',
            'plannedRiskPerTrade': RISK_PER_TRADE,
            'entryHours': '[08:00,20:00)', 'sessionCutoff': '20:00',
            'drawdown': 'observed H1 close liquidation values plus separate adverse intrabar envelope',
            'intrabarEnvelope': 'adverse low/high capped at executable stop; opening gap uncapped; no favorable extreme peak',
            'limitFills': 'no fictional execution at equity floors; ordinary bracket/time/gap exits remain',
            'riskCertification': 'conservative OHLC screen only; intrabar paths, fills and broker rules not certified',
            'costs': 'fixed research assumptions, not historical broker costs; swap absent',
        },
    }
