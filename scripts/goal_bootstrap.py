"""Advisory weekly block-bootstrap arithmetic. No provenance authentication or approval."""
import argparse
import hashlib
import json
import math
from datetime import date, timedelta
from pathlib import Path

import numpy as np

METHOD = 'weekly-basic-bootstrap-v1'
MIN_DAYS = 182  # Proposed numerical-method floor; not an amendment to global protocol.
MAX_REPLICATES = 500_000  # Local computation cap; never relax alpha to fit this cap.


def binomial_logcdf_below_mean(m, n, p):
    """Stable exact binomial sum in log space, only needed below its mean."""
    if not 0 <= m < n * p or not 0 < p < 1:
        raise ValueError('Expected 0 <= m < n*p and 0 < p < 1')
    term = math.lgamma(n + 1) - math.lgamma(m + 1) - math.lgamma(n - m + 1)
    term += m * math.log(p) + (n - m) * math.log1p(-p)
    # Scale every earlier term by the largest term (at m in this range).
    scaled = total = 1.0
    for j in range(m, 0, -1):
        scaled *= j / (n - j + 1) * (1 - p) / p
        total += scaled
        if scaled < total * 1e-16:
            break
    return min(0., term + math.log(total))


def evaluate(payload):
    k, seed, b = payload['trialNumber'], payload['seed'], payload['replicates']
    if any(type(v) is not int for v in (k, seed, b)) or k < 1 or not 0 <= seed < 2**64 or b < 1:
        raise ValueError('Invalid global trial number, seed or replicate count')
    rows = payload['days']
    values = []
    previous = None
    for row in rows:
        when = date.fromisoformat(row['date'])
        if previous is not None and when != previous + timedelta(days=1):
            raise ValueError('Days must be ordered and consecutive; missing is not inactive')
        value = row['netReturn']
        if type(value) not in (int, float) or not math.isfinite(value) or value <= -1:
            raise ValueError('Invalid simple daily net marked return')
        values.append(value)
        previous = when
    alpha = .05 / (k * (k + 1))
    if not math.isfinite(alpha) or alpha <= 0:
        raise ValueError('Trial allocation outside supported numeric range')
    tail, mc_error = .9 * alpha, .1 * alpha
    required = max(10000, math.ceil(100 / tail))
    out = {'method': METHOD, 'validated': False, 'operationalApproval': False,
           'trialNumberProvidedNotAuthenticated': k, 'seed': seed,
           'rng': 'numpy.PCG64', 'numpyVersion': np.__version__,
           'replicatesRequested': b, 'replicatesMinimum': required,
           'alpha': alpha, 'bootstrapTailAllocation': tail, 'monteCarloErrorAllocation': mc_error,
           'calendarDays': len(values), 'zeroReturnDays': values.count(0),
           'minimumDaysProposedMethod': MIN_DAYS, 'replicatesComputed': 0,
           'numericalSupport': False, 'state': 'inconclusive',
           'limitations': ['No authentication of trial registry, data, rule freeze or prospective independence.',
                           'No check of trade count, risk, contract, costs or independent review.',
                           'Block-bootstrap coverage is approximate; weekly dependence/stationarity assumptions may fail.']}
    if len(values) < MIN_DAYS:
        return {**out, 'reason': 'short_sample'}
    if b < required or b > MAX_REPLICATES:
        return {**out, 'reason': 'insufficient_resolution_or_local_resource_cap'}
    a = np.asarray(values, dtype=np.float64)
    if not np.isfinite(a.sum()):
        raise ValueError('Return aggregate is not finite')
    if np.ptp(a) == 0:
        return {**out, 'reason': 'degenerate_sample'}
    n = len(a)
    rng = np.random.Generator(np.random.PCG64(seed))
    means = np.empty(b)
    full, remainder = divmod(n, 7)
    # Precompute circular block sums; each replicate independently samples starts.
    starts = np.arange(n)
    block_sum = sum(a[(starts + shift) % n] for shift in range(7))
    partial_sum = sum((a[(starts + shift) % n] for shift in range(remainder)), np.zeros(n))
    for offset in range(0, b, 1024):
        count = min(1024, b - offset)
        indices = rng.integers(0, n, size=(count, full + bool(remainder)))
        total = block_sum[indices[:, :full]].sum(axis=1)
        if remainder:
            total += partial_sum[indices[:, -1]]
        means[offset:offset + count] = total / n
    theta = float(a.mean())
    tolerance = 32 * np.finfo(float).eps * max(float(np.max(np.abs(means))), np.finfo(float).tiny)
    if np.ptp(means) <= tolerance:
        return {**out, 'replicatesComputed': b, 'reason': 'degenerate_bootstrap_distribution'}
    upper_quantile = float(np.quantile(means, 1 - tail, method='higher'))
    lower = 2 * theta - upper_quantile
    m = int(np.count_nonzero(means >= 2 * theta))
    logcdf = binomial_logcdf_below_mean(m, b, tail) if m < b * tail else None
    mc_pass = logcdf is not None and logcdf < math.log(mc_error) - 1e-10
    bound_tolerance = 32 * np.finfo(float).eps * max(abs(theta), abs(upper_quantile), np.finfo(float).tiny)
    support = theta > bound_tolerance and lower > bound_tolerance and mc_pass
    return {**out, 'replicatesComputed': b, 'meanDailyNetReturn': theta,
            'basicLowerBound': lower, 'tailReplicates': m,
            'positiveBoundNumericalTolerance': float(bound_tolerance),
            'smoothedTailEstimateNotCalibratedPValue': (m + 1) / (b + 1),
            'monteCarloBoundaryLogCdf': logcdf, 'monteCarloGuardSatisfied': mc_pass,
            'numericalSupport': support,
            'state': 'conditional_numerical_support' if support else 'inconclusive',
            'reason': 'arithmetic_only_requires_full_review' if support else 'positive_bound_or_mc_guard_not_established'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    result = evaluate(json.loads(raw))
    result['inputSha256'] = hashlib.sha256(raw).hexdigest()
    result['scriptSha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    print(json.dumps(result, indent=2, allow_nan=False))
