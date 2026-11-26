#!/usr/bin/env python3
"""Chapter 17: reference intervals under declared scalar Gaussian assumptions.

Reuses SciPy's public distribution APIs (BSD-3-Clause), verified with 1.18.1.
These are fixed-window teaching calculations, not a real-data fault detector.
Install: python -m pip install -r bms-book/requirements.txt
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
import statistics

from scipy.stats import binom, chi2, norm


@dataclass(frozen=True)
class WindowReference:
    threshold: float
    count_interval: tuple[int, int]
    count_coverage: float
    mean_interval: tuple[float, float]


def _positive_count(n: int) -> None:
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("n must be a positive integer")


def window_reference(n: int = 512) -> WindowReference:
    """Separate 95% reference regions, NOT a joint 95% acceptance rule.

    Requires independent u=e/sqrt(S) ~ N(0,1), a predetermined equal-weight
    window, and no mean/variance fitting on that window. The discrete count
    interval includes both endpoints; its coverage can exceed 95%.
    """
    _positive_count(n)
    lower, upper = (int(v) for v in binom.ppf([0.025, 0.975], n, 0.05))
    mean_interval = tuple(float(v) / n for v in chi2.ppf([0.025, 0.975], n))
    return WindowReference(
        threshold=float(chi2.ppf(0.95, 1)),
        count_interval=(lower, upper),
        count_coverage=float(binom.cdf(upper, n, 0.05) - binom.cdf(lower - 1, n, 0.05)),
        mean_interval=mean_interval,
    )


def lag_screen(n: int) -> float:
    """Large-sample, single-lag screening approximation, not a whiteness test."""
    _positive_count(n)
    return float(norm.ppf(0.975)) / math.sqrt(n)


def ar1_effective_count(n: int, rho: float, *, squared: bool = False) -> float:
    """Variance-equivalent count for a stationary AR(1) model, 0 <= rho < 1.

    rho is a model parameter, not an inferred model from sorted residuals.
    squared=True additionally assumes jointly zero-mean Gaussian variables:
    Corr(u_i**2, u_j**2) = rho**(2*abs(i-j)). This variance equivalence does
    not turn the average of correlated squares into an exact chi2 variable.
    """
    _positive_count(n)
    if not math.isfinite(rho) or not 0 <= rho < 1:
        raise ValueError("this example requires finite 0 <= rho < 1")
    correlation = rho * rho if squared else rho
    inflation = 1 + 2 * math.fsum(
        (1 - lag / n) * correlation ** lag for lag in range(1, n)
    )
    return n / inflation


def gaussian_window(n: int = 512, seed: int = 5720) -> list[float]:
    """Seeded N(0,1) draws, with known scale; no within-window rescaling."""
    _positive_count(n)
    rng = random.Random(seed)
    return [rng.gauss(0.0, 1.0) for _ in range(n)]


def summarize(values: list[float], threshold: float) -> tuple[float, int]:
    """Mean squared standardized innovation and count strictly above threshold."""
    if not values or not all(math.isfinite(v) for v in values):
        raise ValueError("values must be a nonempty finite sequence")
    if not math.isfinite(threshold) or threshold <= 0:
        raise ValueError("threshold must be finite and positive")
    return statistics.fmean(v * v for v in values), sum(v * v > threshold for v in values)


def main() -> None:
    from estimator_evidence import residual_sequences

    ref = window_reference()
    print("Reference only: scalar iid N(0,1); fixed N=512; equal weights; S not fitted here")
    print(f"single upper threshold={ref.threshold:.6f}")
    print(f"count interval inclusive={ref.count_interval}; actual coverage={ref.count_coverage:.6%}")
    print(f"mean NIS interval=[{ref.mean_interval[0]:.6f}, {ref.mean_interval[1]:.6f}]")
    for n in (512, 64):
        print(f"N={n}: single-lag approximate screen +/-{lag_screen(n):.3f}")
    for rho in (0.0324, 0.9992):
        mean_count = ar1_effective_count(512, rho)
        square_count = ar1_effective_count(512, rho, squared=True)
        print(f"stationary Gaussian AR(1) rho={rho}: mean N_eff={mean_count:.3f}; squares N_eff={square_count:.3f}")
    normalized, ordered = residual_sequences()
    for label, values in (("known-scale Gaussian", gaussian_window()),
                          ("same-window normalized", normalized), ("sorted normalized", ordered)):
        mean, count = summarize(values, ref.threshold)
        print(f"{label}: mean square={mean:.6f}; above threshold={count}")
    print("Normalization fixes mean square at 1; sorting preserves counts, not independence.")


if __name__ == "__main__":
    main()
