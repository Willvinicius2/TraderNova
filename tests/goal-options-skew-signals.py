import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from goal_options_skew_signals import DAY, HOUR, daily_skew, generate_signals
from goal_execution_v4 import simulate


def market():
    start = DAY
    stamp = (start + HOUR) * 1000
    instruments = {}
    trades = []
    for kind, strike, level in [('put', '90', 40), ('call', '110', 20)]:
        name = 'BTC-' + kind
        instruments[name] = dict(kind='option', base_currency='BTC', price_index='btc_usd',
                                 quote_currency='BTC', option_type=kind, strike=strike,
                                 creation_timestamp=0, expiration_timestamp=stamp + 14 * DAY * 1000,
                                 is_active=False, received_at=HOUR)
        for i in range(5):
            trades.append(dict(timestamp=stamp, instrument_name=name, trade_id=kind + str(i),
                               iv=level + i, index_price=100, received_at=2 * DAY + 1))
    return start, trades, instruments


def features(current='55', receipts=True):
    return [dict(time=(i + 1) * DAY, skew=str(i + 1) if i < 90 else current,
                 put_count=5, call_count=5, coverage_complete=True,
                 received_at=(i + 1) * DAY + 1 if receipts else None) for i in range(91)]


class OptionsSignals(unittest.TestCase):
    def test_contract_time_median_duplicate_and_native_unit(self):
        start, trades, metadata = market()
        duplicate = dict(trades[0])
        result = daily_skew(trades + [duplicate], metadata, 'BTC', start,
                            coverage_complete=True, historical_assumption=True)
        self.assertEqual((result['time'], result['put_count'], result['call_count'], result['skew']),
                         (2 * DAY, 5, 5, '20'))
        # Current is_active=False for an expired instrument must not erase history.
        extra = dict(trades[-1], trade_id='extra', iv=30)
        self.assertEqual(daily_skew(trades + [extra], metadata, 'BTC', start,
                                   coverage_complete=True, historical_assumption=True)['skew'], '19.5')
        duplicate['iv'] += 1
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            daily_skew(trades + [duplicate], metadata, 'BTC', start,
                       coverage_complete=True, historical_assumption=True)
        missing = dict(metadata); del missing['BTC-put']
        with self.assertRaisesRegex(ValueError, 'Missing'):
            daily_skew(trades, missing, 'BTC', start, coverage_complete=True, historical_assumption=True)

    def test_inclusive_contract_and_moneyness_boundaries(self):
        start, trades, original = market()
        for duration in (7, 35):
            for put_strike, call_strike in (('85', '105'), ('95', '115')):
                metadata = copy.deepcopy(original)
                metadata['BTC-put']['strike'] = put_strike
                metadata['BTC-call']['strike'] = call_strike
                for row in metadata.values():
                    row['expiration_timestamp'] = trades[0]['timestamp'] + duration * DAY * 1000
                result = daily_skew(trades, metadata, 'BTC', start,
                                    coverage_complete=True, historical_assumption=True)
                self.assertEqual(result['skew'], '20')
        metadata['BTC-put']['expiration_timestamp'] += 1
        self.assertIsNone(daily_skew(trades, metadata, 'BTC', start,
                                    coverage_complete=True, historical_assumption=True)['skew'])
        metadata = copy.deepcopy(original); metadata['BTC-put']['creation_timestamp'] = trades[0]['timestamp'] + 1
        with self.assertRaisesRegex(ValueError, 'inactive'):
            daily_skew(trades, metadata, 'BTC', start, coverage_complete=True, historical_assumption=True)

    def test_receipt_coverage_and_order_invariance(self):
        start, trades, metadata = market()
        kwargs = dict(coverage_complete=True, coverage_received_at=2 * DAY + 10)
        self.assertIsNone(daily_skew(trades, metadata, 'BTC', start, coverage_complete=True)['skew'])
        self.assertEqual(daily_skew(trades, metadata, 'BTC', start, **kwargs)['skew'], '20')
        late = dict(trades[0], received_at=2 * DAY + HOUR + 1)
        a = daily_skew([late] + trades, metadata, 'BTC', start, **kwargs)
        b = daily_skew(trades + [late], metadata, 'BTC', start, **kwargs)
        self.assertEqual(a, b)
        self.assertEqual(a['skew'], '20')
        for receipt in (2 * DAY - 1, 2 * DAY + HOUR + 1, None, float('nan')):
            self.assertIsNone(daily_skew(trades, metadata, 'BTC', start, coverage_complete=True,
                                        coverage_received_at=receipt)['skew'])
        metadata['BTC-put']['received_at'] = 2 * DAY + HOUR + 1
        self.assertIsNone(daily_skew(trades, metadata, 'BTC', start, **kwargs)['skew'])

    def test_missing_invalid_or_fewer_than_five_no_feature(self):
        start, trades, metadata = market()
        self.assertIsNone(daily_skew(trades, metadata, 'BTC', start,
                                    coverage_complete=False, historical_assumption=True)['skew'])
        for field, invalid in [('iv', None), ('iv', 'NaN'), ('iv', 0), ('index_price', -1)]:
            rows = copy.deepcopy(trades); rows[0][field] = invalid
            self.assertIsNone(daily_skew(rows, metadata, 'BTC', start,
                                        coverage_complete=True, historical_assumption=True)['skew'])
        rows = copy.deepcopy(trades); rows[0]['timestamp'] = 2 * DAY * 1000
        with self.assertRaisesRegex(ValueError, 'outside'):
            daily_skew(rows, metadata, 'BTC', start, coverage_complete=True, historical_assumption=True)

    def test_prior_only_rank_strictness_timing_and_priority(self):
        self.assertEqual(generate_signals({'BTCUSDT': features('54')})['N13'], {})
        self.assertEqual(generate_signals({'BTCUSDT': features('0')})['N13'], {})
        result = generate_signals({'BTCUSDT': features(), 'ETHUSDT': features()})['N13']
        decision = 91 * DAY + HOUR
        self.assertEqual(list(result), [decision])
        signal = result[decision]
        self.assertEqual((signal['symbol'], signal['direction'], signal['feature_end'],
                          signal['signal_close_time']), ('BTCUSDT', -1, 91 * DAY, 91 * DAY + 2 * HOUR))
        scaled = features()
        for row in scaled:
            row['skew'] = str(float(row['skew']) * 100)
        self.assertEqual(generate_signals({'BTCUSDT': scaled})['N13'], result)
        later = dict(features()[-1], time=92 * DAY, skew='100000', received_at=92 * DAY + 1)
        self.assertEqual(generate_signals({'BTCUSDT': features() + [later]})['N13'][decision], signal)

    def test_missing_days_invalid_receipts_and_synthetic_short_fill(self):
        broken = features(); broken[10]['skew'] = None
        self.assertEqual(generate_signals({'BTCUSDT': broken})['N13'], {})
        self.assertEqual(generate_signals({'BTCUSDT': features()[1:]})['N13'], {})
        self.assertEqual(generate_signals({'BTCUSDT': features(receipts=False)})['N13'], {})
        rows = features(); rows[0]['received_at'] = rows[0]['time'] + HOUR + 1
        result = generate_signals({'BTCUSDT': rows, 'ETHUSDT': features()})['N13']
        self.assertEqual(next(iter(result.values()))['symbol'], 'ETHUSDT')
        signals = generate_signals({'BTCUSDT': features()})['N13']
        entry = 91 * DAY + 2 * HOUR
        start, end = entry - HOUR, entry + 14 * HOUR
        bars = [dict(time=t, open=100., high=100., low=100., close=100.) for t in range(start, end, HOUR)]
        result = simulate({'BTCUSDT': bars}, {'BTCUSDT': bars}, {'BTCUSDT': []}, signals, start, end)
        trade = result['trades'][0]
        self.assertEqual((trade['entry_time'], trade['exit_time'], trade['direction']),
                         (entry, entry + 12 * HOUR, -1))
        self.assertLess(trade['entry'], 100)
        self.assertGreater(trade['exit'], 100)
        self.assertAlmostEqual(trade['pnl'], result['net_cash'])


if __name__ == '__main__':
    unittest.main()
