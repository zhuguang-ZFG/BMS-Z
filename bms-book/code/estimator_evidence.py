#!/usr/bin/env python3
"""Synthetic estimator evidence: slope, residual ordering and capacity uncertainty.

Only standard library dependencies. Outputs are local teaching calculations,
not measured battery accuracy or a Gaussian statistical certification.
"""
from __future__ import annotations

import math
import random
import statistics


def scalar_update(slope: float, prior_var: float, measurement_var: float) -> tuple[float, float]:
    """Return K and K*H for a scalar SOC-only linearized observation."""
    if prior_var < 0 or measurement_var <= 0:
        raise ValueError("variances must be nonnegative; measurement variance must be positive")
    gain = prior_var * slope / (slope * slope * prior_var + measurement_var)
    return gain, gain * slope


def lag_one(values: list[float]) -> float:
    if len(values) < 3:
        raise ValueError("at least three values are required")
    a, b = values[:-1], values[1:]
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    numerator = sum((x - ma) * (y - mb) for x, y in zip(a, b, strict=True))
    denominator = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    if denominator == 0:
        raise ValueError("correlation is undefined for a constant series")
    return numerator / denominator


def residual_sequences() -> tuple[list[float], list[float]]:
    rng = random.Random(5720)
    samples = [rng.gauss(0.0, 1.0) for _ in range(512)]
    mean = statistics.fmean(samples)
    rms = math.sqrt(statistics.fmean((sample - mean) ** 2 for sample in samples))
    shuffled = [(sample - mean) / rms for sample in samples]
    ordered = sorted(shuffled)
    return shuffled, ordered


def capacity_sigma(charge_ah: float, delta_soc: float, sigma_charge_ah: float,
                   sigma_start: float, sigma_end: float, correlation: float = 0.0) -> tuple[float, float]:
    """First-order propagation, assuming charge error is independent of SOC endpoints."""
    if delta_soc <= 0 or any(sigma < 0 for sigma in (sigma_charge_ah, sigma_start, sigma_end)):
        raise ValueError("positive SOC span and nonnegative standard deviations are required")
    if not -1 <= correlation <= 1:
        raise ValueError("correlation must be in [-1, 1]")
    span_var = sigma_start ** 2 + sigma_end ** 2 - 2 * correlation * sigma_start * sigma_end
    capacity = charge_ah / delta_soc
    variance = (sigma_charge_ah / delta_soc) ** 2 + (charge_ah / delta_soc ** 2) ** 2 * span_var
    return capacity, math.sqrt(max(variance, 0.0))


def random_walk_noise_budget(noise_intensity: float, dt_s: float,
                             steps: int) -> tuple[float, float]:
    """Return per-step Q and total variance for a continuous-noise random walk.

    ``noise_intensity`` has units state^2/s. Independent increments over one
    sample interval have covariance ``noise_intensity * dt_s``. The caller
    must still derive a different model when noise is correlated or when the
    state transition/input matrix is nontrivial.
    """
    if not math.isfinite(noise_intensity) or noise_intensity < 0:
        raise ValueError("noise intensity must be finite and nonnegative")
    if not math.isfinite(dt_s) or dt_s <= 0:
        raise ValueError("dt_s must be finite and positive")
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
        raise ValueError("steps must be a positive integer")
    q_step = noise_intensity * dt_s
    return q_step, q_step * steps


def main() -> None:
    prior_var, measurement_var = 0.05 ** 2, 0.005 ** 2
    for slope in (0.8, 0.075, 0.01):
        gain, weight = scalar_update(slope, prior_var, measurement_var)
        print(f"slope {slope:.3f} V/SOC: K={gain:.4f} SOC/V; K*H={weight:.4f}; 15 mV correction={gain * 0.015 * 100:.3f} pp")
    steep_gain, steep_weight = scalar_update(0.8, prior_var, measurement_var)
    flat_gain, flat_weight = scalar_update(0.075, prior_var, measurement_var)
    assert flat_gain > steep_gain and flat_weight < steep_weight
    assert scalar_update(0.0, prior_var, measurement_var) == (0.0, 0.0)

    shuffled, ordered = residual_sequences()
    for label, values in (("shuffled", shuffled), ("ordered", ordered)):
        rms = math.sqrt(statistics.fmean(value ** 2 for value in values))
        print(f"{label}: mean={statistics.fmean(values):.6f}; RMS={rms:.6f}; mean NIS={rms ** 2:.6f}; lag1={lag_one(values):.4f}")
    assert sorted(shuffled) == ordered
    assert abs(lag_one(shuffled)) < 0.15 and lag_one(ordered) > 0.95
    # NIS divides squared residual by S: doubling S alone halves NIS.
    nis = statistics.fmean(value ** 2 for value in shuffled)
    assert math.isclose(nis, 1.0)
    print(f"same residuals, assumed S doubled: mean NIS={nis / 2:.6f}")

    capacity, sigma = capacity_sigma(0.72, 0.40, 0.02, 0.01, 0.01)
    _, sigma_correlated = capacity_sigma(0.72, 0.40, 0.02, 0.01, 0.01, correlation=0.8)
    print(f"window capacity: {capacity:.3f} Ah; sigma including SOC endpoints={sigma:.4f} Ah; SOH sigma={sigma / 2 * 100:.3f} pp")
    print(f"endpoint correlation +0.8: capacity sigma={sigma_correlated:.4f} Ah")
    assert math.isclose(capacity, 1.8)
    assert math.isclose(sigma ** 2, 0.00655)
    assert sigma_correlated < sigma

    noise_intensity = 2e-6
    coarse_step, coarse_total = random_walk_noise_budget(noise_intensity, 1.0, 3600)
    fine_step, fine_total = random_walk_noise_budget(noise_intensity, 0.5, 7200)
    _, reused_total = random_walk_noise_budget(noise_intensity, 1.0, 7200)
    print(f"random walk dt=1.0 s steps=3600: Q={coarse_step:.6e} SOC^2; added={coarse_total:.6f} SOC^2")
    print(f"random walk dt=0.5 s steps=7200: Q={fine_step:.6e} SOC^2; added={fine_total:.6f} SOC^2")
    print(f"wrong fixed Q at dt=0.5 s: added={reused_total:.6f} SOC^2; ratio={reused_total / fine_total:.1f}x")
    assert math.isclose(coarse_total, fine_total)
    assert math.isclose(reused_total / fine_total, 2.0)
    print("checks passed: slope weight, residual ordering, NIS scale, capacity propagation and sampling budget")


if __name__ == "__main__":
    main()
