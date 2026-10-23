#!/usr/bin/env python3
"""Deterministic error and timing budgets, using synthetic values only."""
from __future__ import annotations

import math


def worst_case_mv(bounds_mv: list[float]) -> float:
    """Sum absolute bounds; no independence assumption is required."""
    return sum(abs(bound) for bound in bounds_mv)


def random_rss_mv(sigmas_mv: list[float]) -> float:
    """Standard deviation for uncorrelated zero-mean terms, not a safety bound."""
    return math.sqrt(sum(sigma ** 2 for sigma in sigmas_mv))


def drift_percent(bias_a: float, duration_h: float, capacity_ah: float) -> float:
    if duration_h < 0 or capacity_ah <= 0:
        raise ValueError("duration must be nonnegative and capacity must be positive")
    return bias_a * duration_h / capacity_ah * 100


def main() -> None:
    bound = worst_case_mv([2.0, 1.2, 0.8, 0.5])
    sigma = random_rss_mv([0.6, 0.8])
    slope_mv_per_percent = 0.75
    offset = drift_percent(0.05, 7 * 24, 100.0)
    missing_charge_ah = 20.0 * 0.2 / 3600
    skew_error_mv = 50.0 * 0.002 * 1000
    adc12_mv, adc16_mv = 5000.0 / 2 ** 12, 5000.0 / 2 ** 16
    limit_mv, rise_mv_per_s, latency_s = 3650.0, 10.0, 0.2
    trip_mv = limit_mv - bound - rise_mv_per_s * latency_s
    shared_mv, per_channel_mv = 2.0 + 0.8 + 0.5, 1.2
    relative_mv = 2 * per_channel_mv
    gap_true_mv, a_base_mv, b_base_mv = 8.0, 3640.0, 3632.0
    observed_gaps_mv = {
        "shared only": (a_base_mv + shared_mv) - (b_base_mv + shared_mv),
        "residuals +1.2/-1.2": (a_base_mv + shared_mv + per_channel_mv) - (b_base_mv + shared_mv - per_channel_mv),
        "residuals -1.2/+1.2": (a_base_mv + shared_mv - per_channel_mv) - (b_base_mv + shared_mv + per_channel_mv),
    }
    threshold_mv, action_mv = 10.0, 10.0 + relative_mv

    print(f"ADC 5 V span: 12 bit {adc12_mv:.4f} mV/LSB; 16 bit {adc16_mv:.4f} mV/LSB")
    print(f"worst-case voltage bound: {bound:.2f} mV")
    print(f"uncorrelated random noise only: RSS sigma {sigma:.2f} mV (not a bound)")
    print(f"LFP local slope {slope_mv_per_percent:.2f} mV/%: SOC bound {bound / slope_mv_per_percent:.2f} percentage points")
    print(f"current offset +0.05 A, 7 days, 100 Ah: {offset:.2f} percentage points")
    print(f"missed 20 A / 200 ms pulse: {missing_charge_ah:.6f} Ah")
    print(f"V/I timestamp mismatch, 50 A step / 2 mOhm: {skew_error_mv:.1f} mV")
    print(f"synthetic OVP trip: {trip_mv:.2f} mV (3650 - 4.50 - 2.00)")
    print(f"difference-channel bound: {relative_mv:.1f} mV (2 x {per_channel_mv:.1f}); absolute bound stays {bound:.2f} mV")
    print(f"true gap {gap_true_mv:.1f} mV, observed gaps: " + ", ".join(f"{name} {value:.1f}" for name, value in observed_gaps_mv.items()))
    print(f"balance intent {threshold_mv:.1f} mV -> action line {action_mv:.1f} mV guarantees true gap >= {threshold_mv:.1f} mV")

    assert math.isclose(bound, 4.5)
    assert math.isclose(sigma, 1.0)
    assert math.isclose(bound / slope_mv_per_percent, 6.0)
    assert math.isclose(offset, 8.4)
    assert math.isclose(drift_percent(-0.05, 7 * 24, 100.0), -8.4)
    assert math.isclose(missing_charge_ah * 3600, 4.0)
    assert math.isclose(skew_error_mv, 100.0)
    assert math.isclose(trip_mv + bound + rise_mv_per_s * latency_s, limit_mv)
    assert adc16_mv < adc12_mv
    assert math.isclose(shared_mv + per_channel_mv, bound)
    assert math.isclose(relative_mv, 2.4)
    assert math.isclose(observed_gaps_mv["shared only"], gap_true_mv)
    assert math.isclose(observed_gaps_mv["residuals +1.2/-1.2"], 10.4)
    assert math.isclose(observed_gaps_mv["residuals -1.2/+1.2"], 5.6)
    assert observed_gaps_mv["residuals +1.2/-1.2"] >= threshold_mv > gap_true_mv
    assert math.isclose(action_mv - relative_mv, threshold_mv)
    print("checks passed: bounds, noise, drift, missed charge, timing, OVP margin and difference channel")


if __name__ == "__main__":
    main()
