"""Check one registered research condition from a supplied feature JSON. No fills/PnL."""
import argparse
import json
from pathlib import Path
from goal_five_signals import (n16_liquidation_reclaim, n17_etf_flow,
                               n18_exchange_deposit, n19_cross_venue, n20_cpi_surprise)
from continuous_signals import n21_liquidity_resilience, n22_aave_credit_stress

RULES = dict(zip(['N16', 'N17', 'N18', 'N19', 'N20'],
                [n16_liquidation_reclaim, n17_etf_flow, n18_exchange_deposit,
                 n19_cross_venue, n20_cpi_surprise]))
RULES.update(N21=n21_liquidity_resilience,N22=n22_aave_credit_stress)

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', choices=RULES, required=True)
    p.add_argument('--input', type=Path, required=True)
    args = p.parse_args()
    if args.input.stat().st_size > 2_000_000:
        p.error('Feature file exceeds the 2 MB limit.')
    data = json.loads(args.input.read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict):
        p.error('Expected a feature object.')
    signal = RULES[args.candidate](data)
    print(json.dumps({'candidate': args.candidate, 'signal': signal,
                      'status': 'research_condition_only' if signal else 'no_signal_or_invalid_features',
                      'validated': False, 'ordersSent': 0,
                      'limitation': 'Supplied metadata is not independently verified. No execution, PnL or financial approval.'},
                     indent=2, ensure_ascii=False, allow_nan=False))
