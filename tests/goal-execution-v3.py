"""Synthetic regressions for v3 entry gaps and v2-compatible funding; no historical PnL."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from goal_execution_v3 import FUNDING_POLICY, simulate

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
assert r['funding_policy'] == FUNDING_POLICY == 'boundary_hour_conservative_v3'
p = r['trades'][0]
assert p['entry_time'] == H and p['exit_time'] == 3 * H
assert abs(p['pnl'] - r['net_cash']) < 1e-7
assert p['qty'] * p['entry'] <= 100000
assert run(scenario='stress')['net_cash'] < r['net_cash']

# An event six ms into the entry hour may precede its first trade: debit once.
f = [{'time_ms': H * 1000 + 6, 'rate': .001, 'mark_price': 101.}]
r2 = run(f=f)
assert abs(r2['trades'][0]['funding_pnl'] + p['qty'] * .001 * 101) < 1e-7
assert r2['funding_mark_bounds'] == 0
assert r2['ambiguous_intrabar_funding'] == 1
assert run(f=[{'time_ms': H * 1000 + 6, 'rate': -.001,
               'mark_price': 101.}])['trades'][0]['funding_pnl'] == 0
# Funding at the exact entry timestamp is ambiguous: possible debit, no credit.
assert run(f=[{'time_ms': H * 1000, 'rate': .001, 'mark_price': 101.}])['trades'][0]['funding_pnl'] < 0
assert run(f=[{'time_ms': H * 1000, 'rate': -.001, 'mark_price': 101.}])['trades'][0]['funding_pnl'] == 0
# Six ms before entry belongs to the previous hour, when no position exists.
assert run(f=[{'time_ms': H * 1000 - 6, 'rate': .001, 'mark_price': 101.}])['trades'][0]['funding_pnl'] == 0
assert run(f=[{'time_ms': H * 1000 - 6, 'rate': -.001, 'mark_price': 101.}])['trades'][0]['funding_pnl'] == 0
# Open exit, exact or +6ms: a debit may precede the first-trade fill; no credit.
assert run(f=[{'time_ms': 3 * H * 1000, 'rate': .001, 'mark_price': 101.}])['trades'][0]['funding_pnl'] < 0
assert run(f=[{'time_ms': 3 * H * 1000, 'rate': -.001, 'mark_price': 101.}])['trades'][0]['funding_pnl'] == 0
assert run(f=[{'time_ms': 3 * H * 1000 + 6, 'rate': .001,
               'mark_price': 101.}])['trades'][0]['funding_pnl'] < 0
assert run(f=[{'time_ms': 3 * H * 1000 + 6, 'rate': -.001,
               'mark_price': 101.}])['trades'][0]['funding_pnl'] == 0
# Six ms before exit belongs to the fully held preceding hour.
assert run(f=[{'time_ms': 3 * H * 1000 - 6, 'rate': .001,
               'mark_price': 101.}])['trades'][0]['funding_pnl'] < 0
assert run(f=[{'time_ms': 3 * H * 1000 - 6, 'rate': -.001,
               'mark_price': 101.}])['trades'][0]['funding_pnl'] > 0
# In a fully held middle hour, settled funding retains both signs.
assert run(f=[{'time_ms': 2 * H * 1000 + 6, 'rate': .001,
               'mark_price': 101.}])['trades'][0]['funding_pnl'] < 0
assert run(f=[{'time_ms': 2 * H * 1000 + 6, 'rate': -.001,
               'mark_price': 101.}])['trades'][0]['funding_pnl'] > 0
# Exact-open and +6ms events each settle once, at their real timestamps.
twice = run(f=[{'time_ms': H * 1000, 'rate': .001, 'mark_price': 101.},
               {'time_ms': H * 1000 + 6, 'rate': .002, 'mark_price': 101.}])
assert abs(twice['trades'][0]['funding_pnl'] + p['qty'] * .003 * 101.) < 1e-7
assert twice['ambiguous_intrabar_funding'] == 2
assert abs(twice['net_cash'] - sum(x['pnl'] for x in twice['trades'])) < 1e-7
exit_twice = run(f=[{'time_ms': 3 * H * 1000, 'rate': .001, 'mark_price': 101.},
                    {'time_ms': 3 * H * 1000 + 6, 'rate': .002, 'mark_price': 101.}])
assert abs(exit_twice['trades'][0]['funding_pnl'] + p['qty'] * .003 * 101.) < 1e-7
assert exit_twice['ambiguous_intrabar_funding'] == 2

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
assert run(b=b, f=[{'time_ms': 2 * H * 1000 + 6, 'rate': .001,
                     'mark_price': 100.}])['trades'][0]['funding_pnl'] < 0
assert run(b=b, f=[{'time_ms': 2 * H * 1000 + 6, 'rate': -.001,
                     'mark_price': 100.}])['trades'][0]['funding_pnl'] == 0

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
assert run(b=b, f=[{'time_ms': 2 * H * 1000 + 6, 'rate': .001,
                     'mark_price': 100.}])['trades'][0]['funding_pnl'] < 0
# A mark gap with a trade open still makes the whole exit hour ambiguous.
m = bars(); m.pop(2)
mark_gap = run(m=m, f=[{'time_ms': 2 * H * 1000 + 6, 'rate': .001,
                         'mark_price': 100.}])
assert mark_gap['trades'][0]['reason'] == 'data_gap' and mark_gap['data_quality_flags']
assert mark_gap['trades'][0]['funding_pnl'] < 0
# A missing entry observation creates no fabricated fill.
b = bars(); b.pop(1)
missing_trade = run(b=b)
assert missing_trade['trade_count'] == 0
assert any(x['issue'] == 'missing_entry_trade' and x['time'] == H
           for x in missing_trade['data_quality_flags'])
assert missing_trade['boundary_skips'] == 1
b = bars(); b[1]['open'] = None
missing_open = run(b=b)
assert missing_open['trade_count'] == 0
assert any(x['issue'] == 'missing_entry_trade' and x['time'] == H
           for x in missing_open['data_quality_flags'])

# Missing contemporary mark never cancels a known trade open. The position
# exits for source unavailability only at the next observed trade open.
m = bars(); m.pop(1)
entry_mark_gap = run(m=m, f=[{'time_ms': H * 1000 + 6, 'rate': .001,
                              'mark_price': 101.}])
assert entry_mark_gap['trade_count'] == 1
assert entry_mark_gap['trades'][0]['entry_time'] == H
assert entry_mark_gap['trades'][0]['exit_time'] == 2 * H
assert entry_mark_gap['trades'][0]['reason'] == 'data_gap'
assert any(x['issue'] == 'missing_entry_mark' and x['time'] == H
           for x in entry_mark_gap['data_quality_flags'])
assert entry_mark_gap['trades'][0]['funding_pnl'] < 0
assert abs(entry_mark_gap['net_cash'] - sum(x['pnl'] for x in entry_mark_gap['trades'])) < 1e-7
no_uncertain_credit = run(m=m, f=[{'time_ms': H * 1000 + 6, 'rate': -.001,
                                    'mark_price': 101.}])
assert no_uncertain_credit['trades'][0]['funding_pnl'] == 0
unpriced = run(m=m, f=[{'time_ms': H * 1000 + 6, 'rate': .001,
                         'mark_price': None}])
assert any(x['issue'] == 'unpriced_funding' for x in unpriced['data_quality_flags'])

# The missing mark is still flagged if the following trade open is also absent;
# no exit is invented in the missing hour.
b = bars(); b.pop(2)
later_gap = run(b=b, m=m)
assert later_gap['trades'][0]['entry_time'] == H
assert later_gap['trades'][0]['exit_time'] == 3 * H
assert later_gap['trades'][0]['reason'] == 'data_gap'
assert any(x['issue'] == 'missing_entry_mark' for x in later_gap['data_quality_flags'])
assert any(x['issue'] == 'missing_active_trade' for x in later_gap['data_quality_flags'])

# Future/current OHLC can change risk outcome, not whether the trade-open
# already observed at H was entered. Preflight validates structural OHLC only.
variants = []
for low, high, close in [(100., 100., 100.), (98., 103., 102.)]:
    b = bars(); b[1].update(low=low, high=high, close=close)
    variants.append(run(b=b, m=m))
assert all(v['trade_count'] == 1 and v['trades'][0]['entry_time'] == H for v in variants)
assert all(any(x['issue'] == 'missing_entry_mark' for x in v['data_quality_flags']) for v in variants)
assert variants[1]['trades'][0]['reason'] == 'intrabar_stop_time_unknown_missing_mark'
wrong = signal(); wrong[0]['signal_close_time'] = 0
try: run(s=wrong)
except ValueError: pass
else: raise AssertionError('Retroactive decision accepted')
print('goal-execution-v3: entry gaps, boundary funding, costs and reconciliation passed')
