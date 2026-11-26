"""Check statistical meaning, finite covariance sums and the normalization trap."""
import importlib.util
import math
from pathlib import Path
import statistics
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1] / "code"


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


evidence = load("nis_window_evidence")


def test_discrete_interval_has_declared_tail_coverage_without_normal_approximation():
    ref = evidence.window_reference()
    assert ref.count_interval == (16, 36)
    # Independently sum binomial masses with Python integers, no SciPy CDF.
    # Use exact p=1/20 to avoid accumulating binary rounding across 512 powers.
    pmf = [math.comb(512, k) * 19 ** (512 - k) / 20 ** 512 for k in range(513)]
    lo, hi = ref.count_interval
    assert sum(pmf[:lo]) <= .025 < sum(pmf[:lo + 1])
    assert sum(pmf[hi + 1:]) <= .025 < sum(pmf[hi:])
    assert sum(pmf[lo:hi + 1]) == pytest.approx(ref.count_coverage, abs=2e-14)
    assert ref.count_coverage == pytest.approx(.9676392522781697)


def test_mean_interval_matches_independent_integer_gamma_tail():
    ref = evidence.window_reference()
    # chi2(512)/2 is Gamma(256,1); survival is a finite Poisson sum.
    for endpoint, survival in zip(ref.mean_interval, (.975, .025), strict=True):
        x = endpoint * 512 / 2
        tail = math.fsum(math.exp(-x + k * math.log(x) - math.lgamma(k + 1))
                         for k in range(256))
        assert tail == pytest.approx(survival, abs=2e-13)
    assert ref.mean_interval == pytest.approx((.8812429765, 1.1261545747))
    assert math.erfc(math.sqrt(ref.threshold / 2)) == pytest.approx(.05)


@pytest.mark.parametrize("n,rho", [(1, .9992), (64, 0.0), (64, .8), (512, .9992)])
def test_finite_effective_count_matches_full_covariance_matrix(n, rho):
    lag = np.abs(np.subtract.outer(np.arange(n), np.arange(n)))
    covariance = rho ** lag
    mean_variance = covariance.sum() / n ** 2
    square_variance = (2 * covariance ** 2).sum() / n ** 2
    assert evidence.ar1_effective_count(n, rho) == pytest.approx(1 / mean_variance)
    assert evidence.ar1_effective_count(n, rho, squared=True) == pytest.approx(2 / square_variance)
    assert 1 <= evidence.ar1_effective_count(n, rho) <= n


def test_strong_correlation_finite_window_does_not_have_less_than_one_sample():
    assert evidence.ar1_effective_count(512, .9992) == pytest.approx(1.1411200874)
    assert evidence.ar1_effective_count(512, .9992, squared=True) == pytest.approx(1.2907552424)
    assert evidence.ar1_effective_count(512, 1 - 1e-12) == pytest.approx(1, abs=1e-8)
    assert evidence.lag_screen(64) > evidence.lag_screen(512)


def test_same_window_normalization_fixes_mean_square_but_not_count():
    original = evidence.gaussian_window()
    normalized, ordered = load("estimator_evidence").residual_sequences()
    threshold = evidence.window_reference().threshold
    mean, count = evidence.summarize(original, threshold)
    assert mean == pytest.approx(.9280189248472158)
    assert count == 21
    assert evidence.summarize(normalized, threshold) == pytest.approx((1, 24))
    assert evidence.summarize(ordered, threshold) == pytest.approx((1, 24))
    assert statistics.fmean(normalized) == pytest.approx(0, abs=1e-15)
    # Demonstrate the constraint for another scale/offset, without new random draws.
    transformed = [3 * x + 7 for x in original]
    center = statistics.fmean(transformed)
    scale = math.sqrt(statistics.fmean((x - center) ** 2 for x in transformed))
    assert [(x - center) / scale for x in transformed] == pytest.approx(normalized)


@pytest.mark.parametrize("n", [0, -1, 2.5, True])
def test_invalid_windows_fail(n):
    with pytest.raises(ValueError):
        evidence.window_reference(n)


@pytest.mark.parametrize("rho", [-.1, 1, math.nan, math.inf])
def test_ar1_example_rejects_out_of_scope_parameters(rho):
    with pytest.raises(ValueError):
        evidence.ar1_effective_count(512, rho)
