"""Synthetic numerical tests only; no historical strategy returns."""
import copy
import math
import sys
import unittest
import numpy as np
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from goal_bootstrap import binomial_logcdf_below_mean, evaluate


def fixture():
    return {'trialNumber': 1, 'seed': 1729, 'replicates': 10000,
            'days': [{'date': str(date(2027, 1, 1) + timedelta(days=i)),
                      'netReturn': (.001 if i % 11 < 3 else 0.)} for i in range(182)]}


class BootstrapTests(unittest.TestCase):
    def test_binomial_against_small_exact_distribution(self):
        for n, p, m in [(10, .4, 0), (20, .3, 3), (100, .2, 10)]:
            expected = sum(math.comb(n, j) * p**j * (1-p)**(n-j) for j in range(m+1))
            self.assertAlmostEqual(math.exp(binomial_logcdf_below_mean(m, n, p)), expected, places=12)

    def test_repeatability_zero_days_and_no_approval(self):
        payload = fixture()
        one, two = evaluate(payload), evaluate(payload)
        self.assertEqual(one, two)
        self.assertEqual(one['calendarDays'], 182)
        self.assertEqual(one['zeroReturnDays'], 131)
        self.assertTrue(one['numericalSupport'])
        self.assertFalse(one['validated'])
        self.assertFalse(one['operationalApproval'])
        self.assertGreater(one['smoothedTailEstimateNotCalibratedPValue'], 0)

    def test_negative_flat_short_and_resolution_inconclusive(self):
        p = fixture()
        for row in p['days']:
            row['netReturn'] *= -1
        self.assertFalse(evaluate(p)['numericalSupport'])
        p = fixture()
        for row in p['days']:
            row['netReturn'] = .001
        self.assertEqual(evaluate(p)['reason'], 'degenerate_sample')
        p = fixture()
        for i, row in enumerate(p['days']):
            row['netReturn'] = .001 if i % 7 < 3 else 0.
        self.assertEqual(evaluate(p)['reason'], 'degenerate_bootstrap_distribution')
        p = fixture(); p['days'] = p['days'][:60]
        self.assertEqual(evaluate(p)['reason'], 'short_sample')
        p = fixture(); p['trialNumber'] = 20
        self.assertEqual(evaluate(p)['replicatesComputed'], 0)

    def test_missing_duplicate_nonfinite_and_invalid_index_rejected(self):
        for kind in ('gap', 'duplicate', 'nan', 'trial'):
            p = copy.deepcopy(fixture())
            if kind == 'gap': p['days'].pop(20)
            if kind == 'duplicate': p['days'][20]['date'] = p['days'][19]['date']
            if kind == 'nan': p['days'][20]['netReturn'] = float('nan')
            if kind == 'trial': p['trialNumber'] = True
            with self.assertRaises(ValueError): evaluate(p)

    def test_partial_week_matches_explicit_concatenation(self):
        p = fixture()
        for i in range(182, 185):
            p['days'].append({'date': str(date(2027, 1, 1) + timedelta(days=i)),
                              'netReturn': .001 if i % 11 < 3 else 0.})
        result = evaluate(p)
        values = np.array([row['netReturn'] for row in p['days']])
        rng = np.random.Generator(np.random.PCG64(p['seed']))
        indices = rng.integers(0, len(values), size=(10000, 27))
        indices = ((indices[:, :, None] + np.arange(7)) % len(values)).reshape(10000, -1)
        means = values[indices[:, :len(values)]].mean(axis=1)
        expected = 2 * values.mean() - np.quantile(means, 1 - result['bootstrapTailAllocation'], method='higher')
        self.assertAlmostEqual(result['basicLowerBound'], expected, places=14)


unittest.main()
