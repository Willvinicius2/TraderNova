"""Deterministic regression tests for the independent research executor."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from goal_execution import simulate

H = 3600
def bars():
    return [{'time': i * H, 'open': 100., 'high': 100., 'low': 100., 'close': 100.} for i in range(7)]

def signal():
    return {0: {'symbol': 'TEST', 'direction': 1, 'stop_pct': .01,
                'hold_hours': 2, 'signal_close_time': H}}

def run(b=None, m=None, f=None, s=None, scenario='base'):
    b = bars() if b is None else b
    return simulate({'TEST': b}, {'TEST': bars() if m is None else m},
                    {'TEST': [] if f is None else f}, signal() if s is None else s,
                    0, 7 * H, scenario)

r = run()
assert r['trade_count'] == 1 and r['net_cash'] < 0
p = r['trades'][0]
assert p['entry_time'] == H and p['exit_time'] == 3 * H
assert abs(p['pnl'] - r['net_cash']) < 1e-7
assert p['qty'] * p['entry'] <= 100000
assert run(scenario='stress')['net_cash'] < r['net_cash']

# Known settlement after entry: debit the actual mark/rate exactly once.
f = [{'time_ms': H * 1000 + 6, 'rate': .001, 'mark_price': 101.}]
r2 = run(f=f)
assert abs(r2['trades'][0]['funding_pnl'] + p['qty'] * .001 * 101) < 1e-7
assert r2['funding_mark_bounds'] == 0
# Funding at the exact entry timestamp is ambiguous: possible debit, no credit.
assert run(f=[{'time_ms': H * 1000, 'rate': .001, 'mark_price': 101.}])['trades'][0]['funding_pnl'] < 0
assert run(f=[{'time_ms': H * 1000, 'rate': -.001, 'mark_price': 101.}])['trades'][0]['funding_pnl'] == 0
# Position held before a time exit still owes funding exactly at that open.
assert run(f=[{'time_ms': 3 * H * 1000, 'rate': .001, 'mark_price': 101.}])['trades'][0]['funding_pnl'] < 0
assert run(f=[{'time_ms': 3 * H * 1000, 'rate': -.001, 'mark_price': 101.}])['trades'][0]['funding_pnl'] == 0

# Missing mark is a labeled adverse bound, never silently the trade close.
m = bars(); m[1]['high'] = 105.; m[1]['low'] = 95.
r3 = run(m=m, f=[{'time_ms': H * 1000 + 6, 'rate': .001, 'mark_price': None}])
assert abs(r3['trades'][0]['funding_pnl'] + p['qty'] * .001 * 105) < 1e-7
assert r3['funding_mark_bounds'] == 1 and r3['max_drawdown_pct'] > r['max_drawdown_pct']

# Stop/settlement ordering unknown: debit included, possible credit excluded.
b = bars(); b[1]['low'] = 98.
stopped = run(b=b, f=[{'time_ms': H * 1000 + 6, 'rate': -.001, 'mark_price': 101.}])
assert stopped['trades'][0]['funding_pnl'] == 0 and stopped['ambiguous_intrabar_funding'] == 1
assert stopped['trades'][0]['reason'] == 'intrabar_stop_time_unknown'
assert abs(stopped['trades'][0]['pnl'] + stopped['trades'][0]['risk_budget']) < 1e-6
# Gap must use the observed adverse open; no fictional stop-price fill.
b = bars(); b[2].update(open=95., high=95., low=95., close=95.)
gapped = run(b=b)
assert gapped['trades'][0]['reason'] == 'gap_stop'
assert gapped['trades'][0]['pnl'] < -gapped['trades'][0]['risk_budget']
assert run(b=b, f=[{'time_ms': 2 * H * 1000, 'rate': -.001, 'mark_price': 100.}])['trades'][0]['funding_pnl'] == 0

for bad in ([bars()[0]] + bars(),):
    try: run(b=bad)
    except ValueError: pass
    else: raise AssertionError('Missing/duplicate data accepted')
# A future source gap may not retroactively cancel an otherwise valid entry.
b = bars(); b.pop(2)
lost = run(b=b)
assert lost['trades'][0]['entry_time'] == H
assert lost['trades'][0]['exit_time'] == 3 * H
assert lost['trades'][0]['reason'] == 'data_gap' and lost['data_quality_flags']
# A missing entry observation creates no fabricated fill.
b = bars(); b.pop(1)
assert run(b=b)['trade_count'] == 0
wrong = signal(); wrong[0]['signal_close_time'] = 0
try: run(s=wrong)
except ValueError: pass
else: raise AssertionError('Retroactive decision accepted')
print('goal-execution: causal fills, costs, funding, risk, gaps and reconciliation passed')
