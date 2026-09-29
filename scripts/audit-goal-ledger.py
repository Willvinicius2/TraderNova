"""Read-only decimal reconciliation of frozen research ledgers; never approves strategies."""
import hashlib
import json
import sys
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 40
ROOT = Path(__file__).resolve().parents[1]
D = Decimal
COSTS = {'base': (D('.0005'), D('.0002')),
         'stress': (D('.001'), D('.0005'))}
TOL = D('.000001')


def require_close(actual, expected, label):
    if abs(actual - expected) > TOL:
        raise AssertionError(f'{label}: {actual} != {expected}')


def audit(path):
    raw = path.read_bytes()
    result = json.loads(raw, parse_float=D)
    runs = []
    for scenario, summary in result['development'].items():
        detail_path = (ROOT / summary['detailPath']).resolve()
        if not detail_path.is_relative_to(ROOT):
            raise ValueError('Ledger outside repository')
        detail_raw = detail_path.read_bytes()
        if hashlib.sha256(detail_raw).hexdigest() != summary['detailSha256']:
            raise AssertionError('Ledger hash mismatch')
        ledger = json.loads(detail_raw, parse_float=D)
        fee, slip = COSTS[scenario]
        balance = peak = D(100000)
        profit = loss = closed_dd = D(0)
        previous_exit = None
        for trade in ledger['trades']:
            qty, entry, exit_price = trade['qty'], trade['entry'], trade['exit']
            direction = trade['direction']
            assert direction in (-1, 1) and qty > 0
            assert ledger['start'] <= trade['entry_time'] <= trade['exit_time'] <= ledger['end']
            assert trade['signal_time'] < trade['entry_time']
            assert previous_exit is None or trade['entry_time'] > previous_exit
            previous_exit = trade['exit_time']
            require_close(trade['entry_fee'], qty * entry * fee, 'entry fee')
            require_close(trade['exit_fee'], qty * exit_price * fee, 'exit fee')
            require_close(trade['risk_budget'], balance / D(400), 'risk budget')
            assert qty * entry * (1 + fee) <= balance + TOL
            stop_fill = trade['stop'] * (1 - direction * slip)
            planned_loss = qty * (direction * (entry - stop_fill) + fee * (entry + stop_fill))
            assert D(0) < planned_loss <= trade['risk_budget'] + TOL
            cash = (direction * qty * (exit_price - entry)
                    - qty * (entry + exit_price) * fee + trade['funding_pnl'])
            require_close(trade['pnl'], cash, 'trade net cash')
            balance += cash
            peak = max(peak, balance)
            closed_dd = max(closed_dd, 100 * (peak - balance) / peak)
            profit += max(D(0), cash)
            loss += max(D(0), -cash)
        count = len(ledger['trades'])
        assert count == ledger['trade_count'] == summary['trade_count']
        for target in (ledger, summary):
            require_close(target['net_cash'], balance - 100000, 'total net cash')
            require_close(target['net_pct'], (balance - 100000) / 1000, 'net percent')
            if loss:
                require_close(target['profit_factor'], profit / loss, 'profit factor')
            else:
                assert target['profit_factor'] is None
            assert target['max_drawdown_pct'] + TOL >= closed_dd
            assert target['validated'] is False
        runs.append({'scenario': scenario, 'tradesChecked': count,
                     'detailSha256': summary['detailSha256'],
                     'netCashDecimal': str(balance - 100000),
                     'closedBalanceDrawdownLowerBoundPct': str(closed_dd),
                     'arithmeticPassed': True})
    return {'family': result['family'], 'resultPath': path.relative_to(ROOT).as_posix(),
            'resultSha256': hashlib.sha256(raw).hexdigest(), 'runs': runs}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python scripts/audit-goal-ledger.py RESULT_JSON [...]')
    output = {'audit': 'decimal-ledger-reconciliation-v1',
              'scriptSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'toleranceCash': str(TOL), 'validated': False,
              'limitations': ['Recorded funding is reconciled, not independently replayed from events.',
                              'Drawdown check is a closed-balance lower bound, not intrabar reconstruction.',
                              'No proof of fills, market availability, broker contract equivalence or strategy validity.'],
              'results': [audit((ROOT / arg).resolve()) for arg in sys.argv[1:]]}
    print(json.dumps(output, indent=2))
