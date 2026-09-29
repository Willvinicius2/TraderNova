import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from goal_onchain_count_signals import DAY, HOUR, generate_signals


def fixture(count='100', receipts=False):
    return [dict(time=i * DAY, count=str(i + 1) if i < 90 else count,
                 **({'received_at': (i + 1) * DAY + HOUR} if receipts else {}))
            for i in range(91)]


class OnchainSignals(unittest.TestCase):
    def test_prior_only_rank_strict_threshold_and_timing(self):
        # ceil(.70*90)=63: current value is excluded from the percentile.
        self.assertEqual(generate_signals({'BTCUSDT': fixture('63')},
                                         historical_assumption=True)['N12'], {})
        result = generate_signals({'BTCUSDT': fixture('64')}, historical_assumption=True)['N12']
        self.assertEqual(list(result), [93 * DAY])
        signal = result[93 * DAY]
        self.assertEqual(signal['feature_end'], 91 * DAY)
        self.assertEqual(signal['signal_close_time'], 93 * DAY + HOUR)
        self.assertEqual((signal['direction'], signal['hold_hours'], signal['stop_pct']), (1, 12, .02))

    def test_missing_or_nonconsecutive_day_blocks_window(self):
        rows = fixture()
        del rows[35]
        self.assertEqual(generate_signals({'BTCUSDT': rows}, historical_assumption=True)['N12'], {})
        self.assertEqual(generate_signals({'BTCUSDT': fixture()[1:]},
                                         historical_assumption=True)['N12'], {})

    def test_priority_and_no_future_values(self):
        rows = fixture()
        original = generate_signals({'BTCUSDT': rows, 'ETHUSDT': rows}, historical_assumption=True)
        self.assertEqual(original['N12'][93 * DAY]['symbol'], 'BTCUSDT')
        extended = generate_signals({'BTCUSDT': rows + [dict(time=91 * DAY, count='100000')]},
                                    historical_assumption=True)
        self.assertEqual(original['N12'][93 * DAY], extended['N12'][93 * DAY])

    def test_receipts_are_required_for_every_observation(self):
        self.assertEqual(generate_signals({'BTCUSDT': fixture()})['N12'], {})
        rows = fixture(receipts=True)
        self.assertEqual(len(generate_signals({'BTCUSDT': rows})['N12']), 1)
        for bad in (None, float('nan'), float('inf'), True, -1, 93 * DAY + .001):
            candidate = [dict(row) for row in rows]
            candidate[0]['received_at'] = bad
            self.assertEqual(generate_signals({'BTCUSDT': candidate})['N12'], {})
        rows[-1]['received_at'] = 93 * DAY
        self.assertEqual(len(generate_signals({'BTCUSDT': rows})['N12']), 1)

    def test_invalid_inputs_and_duplicates_fail_explicitly(self):
        for bad in ('NaN', 'Infinity', '0', '-1', '1.2', 'oops'):
            with self.assertRaises(ValueError):
                generate_signals({'BTCUSDT': fixture(bad)}, historical_assumption=True)
        with self.assertRaises(ValueError):
            generate_signals({'BTCUSDT': fixture() + [fixture()[0]]}, historical_assumption=True)
        with self.assertRaises(ValueError):
            generate_signals({'BTCUSDT': [dict(time=1, count='1')]}, historical_assumption=True)
        with self.assertRaises(ValueError):
            generate_signals({'BTCUSDT': [dict(time=0, count=True)]}, historical_assumption=True)

    def test_unreceived_priority_asset_does_not_block_received_second(self):
        signals = generate_signals({'BTCUSDT': fixture(), 'ETHUSDT': fixture(receipts=True)})['N12']
        self.assertEqual(signals[93 * DAY]['symbol'], 'ETHUSDT')


if __name__ == '__main__':
    unittest.main()
